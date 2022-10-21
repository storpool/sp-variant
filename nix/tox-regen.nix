{ pkgs ? import
    (fetchTarball "https://github.com/ppentchev/nixpkgs/archive/pp-cfg-diag.tar.gz")
    { }
, py-ver ? 311
}:
let
  python-name = "python${toString py-ver}";
  python = builtins.getAttr python-name pkgs;
  # tomli is needed for Python < 3.11 until https://github.com/NixOS/nixpkgs/pull/194020 goes in
  python-pkgs = python.withPackages (p: with p; [
    cfg_diag
    click
    jinja2
    tomli
    tox
    tox-delay
    trivver
    typedload
  ]);
  rust-pkgs = [
    pkgs.cargo
    pkgs.rustc
    pkgs.rustfmt
    pkgs.binutils
  ];
in
pkgs.mkShell {
  buildInputs = [
    python-pkgs
    rust-pkgs
    pkgs.dpkg
    pkgs.python2
    pkgs.rpm
    pkgs.shellcheck
  ];
  shellHook = ''
    set -e
    set -x
    
    echo 'Checking for the Rust build target'
    if python3 -c 'import tomli; import sys; sys.exit(int(tomli.load(open(".cargo/config.toml", mode="rb")).get("build", {}).get("target", "") != "x86_64-unknown-linux-musl"));'; then
      echo 'The .cargo/config.toml file defines a musl build target; please comment it out' 1>&2
      false
    fi

    echo 'Cleaning up Python-related files'
    find . -mindepth 1 -maxdepth 1 -type d \( \
      -name '.tox' -or \
      -name '.mypy_cache' -or \
      -name '.pytest_cache' -or \
      -name '.nox' \
    \) -print -exec rm -rf -- '{}' +

    echo 'Cleaning up any built artifacts'
    make clean SP_CARGO=cargo SP_PYTHON3=python3

    echo 'Cleaning up more built artifacts'
    rm -fv -- rust/data.rs

    echo 'Removing any previously-built add-storpool-repo package'
    rm -rf -- repo-build

    echo 'Running the upstream test suite'
    make test SP_CARGO=cargo SP_PYTHON3=python3 NO_CARGO_FREEZE=1 RUST_RELEASE="$(pwd)/target/release" NIX_ENFORCE_PURITY=0

    echo 'Making sure that there still is no built add-storpool-repo'
    [ ! -e repo-build ]
    [ ! -e repo-build/add-storpool-repo ]
    [ ! -e repo-build/add-storpool-repo.tar.gz ]

    echo 'Building the add-storpool-repo package'
    make repo SP_CARGO=cargo SP_PYTHON3=python3 NO_CARGO_FREEZE=1 RUST_RELEASE="$(pwd)/target/release" NIX_ENFORCE_PURITY=0

    echo 'Making sure that there is a built package now'
    [ -d repo-build ]
    [ -d repo-build/add-storpool-repo ]
    [ -f repo-build/add-storpool-repo.tar.gz ]

    echo 'Making sure the storpool_variant executable there works'
    repo-build/add-storpool-repo/storpool_variant detect

    echo 'Seems fine'
    set +x
    exit 0
  '';
}
