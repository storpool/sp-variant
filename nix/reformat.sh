#!/bin/sh

set -e

script_path="$(readlink -f -- "$0")"
nix_dir="$(dirname -- "$script_path")"
nix-shell --pure -p nixpkgs-fmt --run "nixpkgs-fmt '$nix_dir'/*.nix"
