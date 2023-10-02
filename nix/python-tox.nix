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
    pkgs.dpkg
    pkgs.gitMinimal
    python-with-tox
  ];

  shellHook = ''
    set -e
    tox run-parallel
    exit
  '';
}
