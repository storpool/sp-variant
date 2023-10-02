# SPDX-FileCopyrightText: 2023  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause

{ pkgs ? import <nixpkgs> { }
, py-ver ? 311
}:
let
  python-name = "python${toString py-ver}";
  python = builtins.getAttr python-name pkgs;
  python-with-tox = python.withPackages (p: with p; [ tox ]);
in
pkgs.mkShell {
  buildInputs = [
    pkgs.cargo
    pkgs.rustc
  ];

  shellHook = ''
    set -e
    set -x

    target="$(rustc --version -v | awk '$1 == "host:" { print $2 }')"
    env NIX_ENFORCE_PURITY=0 cargo build --target "$target"
    env NIX_ENFORCE_PURITY=0 cargo test --target "$target"

    "$(pwd)/nix/run-basic-tests.sh" "$(pwd)/target/$target/debug/storpool_variant"

    set +x
    exit
  '';
}
