#!/bin/sh
#
# SPDX-FileCopyrightText: 2023, 2024  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause

set -e

: "${PY_MINVER_MIN:=9}"

# cffi is broken for 3.12 in nixpkgs-unstable
: "${PY_MINVER_MAX:=11}"

for minor in $(seq -- "$PY_MINVER_MIN" "$PY_MINVER_MAX"); do
	pyver="3$minor"
	nix/cleanpy.sh
	printf -- '\n===== Running tests for %s\n\n\n' "$pyver"
	nix-shell --pure --arg py-ver "$pyver" nix/python-tox.nix
	printf -- '\n===== Done with %s\n\n' "$pyver"
done
