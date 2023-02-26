#!/bin/sh
#
# SPDX-FileCopyrightText: 2021  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause

set -e

thisdir="$(dirname -- "$(readlink -f -- "$0")")"
exec "$thisdir/storpool_variant" "$@"
