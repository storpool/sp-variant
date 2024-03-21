# SPDX-FileCopyrightText: 2023, 2024  StorPool <support@storpool.com>
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
    pkgs.dpkg
    pkgs.gitMinimal
    python-with-tox
  ];

  shellHook = ''
    set -e
    set -x

    tox run-parallel

    "$(pwd)/nix/run-basic-tests.sh" "$(pwd)/.tox/unit-tests-pytest-8/bin/sp_variant"

    set +x
    exit
  '';
}
