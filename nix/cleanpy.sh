#!/bin/sh
#
# SPDX-FileCopyrightText: 2023  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause

set -e

find . -mindepth 1 -maxdepth 1 -type d \( \
	-name '.tox' \
	-or -name '.mypy_cache' \
	-or -name '.pytest_cache' \
	-or -name '.nox' \
	-or -name '.ruff_cache' \
\) -exec rm -rf -- '{}' +
find . -type d -name '__pycache__' -exec rm -rfv -- '{}' +
find . -type f -name '*.pyc' -delete -print
find . -mindepth 1 -maxdepth 2 -type d -name '*.egg-info' -exec rm -rfv -- '{}' +
