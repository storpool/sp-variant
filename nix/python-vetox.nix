# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause

{ pkgs ? import <nixpkgs> { }
, py-ver ? 311
}:
let
  python-name = "python${toString py-ver}";
  python = builtins.getAttr python-name pkgs;
in
pkgs.mkShell {
  buildInputs = [
    pkgs.dpkg
    pkgs.gitMinimal
    pkgs.uv
    python
  ];
  shellHook = ''
    set -e
    if [ -z "$VETOX_CERT_FILE" ]; then
      VETOX_CERT_FILE='/etc/ssl/certs/ca-certificates.crt'
    fi
    env SSL_CERT_FILE="$VETOX_CERT_FILE" python3 python/tests/vetox.py run-parallel --tox-uv --uv
    exit
  '';
}
