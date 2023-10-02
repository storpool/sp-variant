#!/bin/sh
#
# SPDX-FileCopyrightText: 2023  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause

set -e
set -x

if [ "$#" -ne 1 ]; then
	echo 'Usage: run-basic-tests path/to/storpool_variant' 1>&2
	exit 1
fi
spvar="$1"

"$spvar" show all

"$spvar" detect

current="$("$spvar" detect)"
"$spvar" show "$current"
