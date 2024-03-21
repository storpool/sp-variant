#!/bin/sh
#
# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause

set -e

: "${PY_MINVER_MIN:=9}"
: "${PY_MINVER_MAX:=13}"

for minor in $(seq -- "$PY_MINVER_MIN" "$PY_MINVER_MAX"); do
	pyver="3$minor"
	nix/cleanpy.sh
	printf -- '\n===== Running tests for %s\n\n\n' "$pyver"
	nix-shell --pure --keep VETOX_CERT_FILE --arg py-ver "$pyver" nix/python-vetox.nix
	printf -- '\n===== Done with %s\n\n' "$pyver"
done
