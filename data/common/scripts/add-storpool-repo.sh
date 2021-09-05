#!/bin/sh

set -e

thisdir="$(dirname -- "$(readlink -f -- "$0")")"
exec "$thisdir/storpool_variant.sh" repo add -d "$thisdir" "$@"
