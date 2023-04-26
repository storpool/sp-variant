#!/usr/bin/make -f
#
# SPDX-FileCopyrightText: 2021 - 2023  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause

RUST_DATA=	rust/data.rs
RUST_SRC=	\
		rust/bin/cli.rs rust/bin/main.rs \
		rust/lib.rs \
		rust/tests.rs \
		rust/yai.rs \
		${RUST_DATA}
RUST_RELEASE=	${CURDIR}/target/x86_64-unknown-linux-musl/release
RUST_BIN=	${RUST_RELEASE}/storpool_variant

SH_SRC=		sp_variant.sh.j2
SH_BIN=		sp_variant.sh

SP_CARGO?=	sp-cargo
ifeq (,${NO_CARGO_OFFLINE})
SP_CARGO_OFFLINE=	--offline
else
SP_CARGO_OFFLINE=
endif

SP_PYTHON3?=	/opt/storpool/python3/bin/python3
SP_PY3_ENV?=	env PYTHONPATH='${CURDIR}/python' ${SP_PYTHON3} -B -u
SP_PY3_INVOKE?=	${SP_PY3_ENV} -m sp_variant
SP_PY3_NORMALIZE=	${SP_PY3_ENV} -c 'import json; import sys; print(json.dumps(json.loads(sys.stdin.read()), sort_keys=True, indent=2))'

PYTHON_VBUILD=	${CURDIR}/python/sp_variant/vbuild.py

REPO_TMPDIR?=	${CURDIR}/repo-build
REPO_BUILT=	${REPO_TMPDIR}/add-storpool-repo.tar.gz
REPO_BIN?=	${SH_BIN}

TEMP_CURRENT_JSON?=	${CURDIR}/current-variant.json
TEMP_ALL_JSON?=		${CURDIR}/all-variants.json
TEMP_PACKAGE_LIST?=	${CURDIR}/package-list.txt

all:		${RUST_BIN} ${SH_BIN}

test:		test-trivial test-shellcheck test-tox-stages

test-trivial:	all
		${SP_PY3_INVOKE} features
		${SP_PY3_INVOKE} detect
		${SP_PY3_INVOKE} command list
		${SP_PY3_INVOKE} show current > '${TEMP_CURRENT_JSON}'
		${SP_PY3_INVOKE} show all > '${TEMP_ALL_JSON}'
		${SP_PY3_INVOKE} command run package.list_all > '${TEMP_PACKAGE_LIST}'
		${RUST_BIN} features
		${RUST_BIN} detect
		${RUST_BIN} command list
		${RUST_BIN} show current | ${SP_PY3_NORMALIZE} | diff -u '${TEMP_CURRENT_JSON}' -
		${RUST_BIN} command run package.list_all | diff -u '${TEMP_PACKAGE_LIST}' -
		! grep -Eqe 'grep -E.*[(][?]:' -- '${SH_BIN}'
		grep -Eqe 'grep -E.*[(][$$][|]' -- '${SH_BIN}'
		${CURDIR}/${SH_BIN} detect
		${CURDIR}/${SH_BIN} show all | ${SP_PY3_NORMALIZE} | diff -u '${TEMP_ALL_JSON}' -
		${CURDIR}/${SH_BIN} show current | ${SP_PY3_NORMALIZE} | diff -u '${TEMP_CURRENT_JSON}' -
		${CURDIR}/${SH_BIN} command run package.list_all | diff -u '${TEMP_PACKAGE_LIST}' -

${REPO_BUILT}:	all test-trivial ${REPO_BIN}
		rm -rf -- '${REPO_TMPDIR}'
		[ ! -f '${REPO_BUILT}' ]
		mkdir -- '${REPO_TMPDIR}'
		${SP_PY3_ENV} -m sp_build_repo build -d '${CURDIR}/data' -D '${REPO_TMPDIR}' -r '${REPO_BIN}' $${REPO_OVERRIDES:+-o "$$REPO_OVERRIDES"} --no-date
		[ -f '${REPO_BUILT}' ]

repo:		${REPO_BUILT}

${RUST_DATA}:	${RUST_DATA}.j2 python/sp_build_repo/subst.py ${PYTHON_VBUILD}
		${SP_PY3_ENV} -m sp_build_repo.subst -m 644 -t '${RUST_DATA}.j2' -o '${RUST_DATA}' -v || { rm -f -- '${RUST_DATA}'; false; }
		${SP_CARGO} fmt -- '${RUST_DATA}'

${RUST_BIN}:	Cargo.toml .cargo/config.toml ${RUST_SRC}
		[ -n '${NO_CARGO_FREEZE}' ] || ${SP_CARGO} sp-freeze
		[ -n '${NO_CARGO_CLEAN}' ] || ${SP_CARGO} clean
		${SP_CARGO} fmt -- --check
		${SP_CARGO} build --release ${SP_CARGO_OFFLINE}
		${SP_CARGO} test --release ${SP_CARGO_OFFLINE}

${SH_BIN}:	${SH_SRC} python/sp_build_repo/subst.py ${PYTHON_VBUILD}
		${SP_PY3_ENV} -m sp_build_repo.subst -m 755 -t '${SH_SRC}' -o '${SH_BIN}' -v || { rm -f -- '${SH_BIN}'; false; }

test-docker:	repo
		${SP_PY3_ENV} -m test_docker -r '${REPO_BUILT}' -v ${TEST_DOCKER_ARGS}

test-tox-stages:
		"$$(dirname -- '${SP_PYTHON3}')/tox-stages" run

test-shellcheck:	${SH_BIN}
		[ -n '${NO_SHELLCHECK}' ] || shellcheck -- '${SH_BIN}'

clean:		clean-py clean-repo clean-rust clean-sh clean-site

clean-py:
		find -- '${CURDIR}/python' -type d \( -name __pycache__ -or -name '*.egg-info' \) -exec rm -rf -- '{}' +
		find -- '${CURDIR}/python' -type f -name '*.pyc' -delete
		find . -mindepth 1 -maxdepth 1 -type d \( -name '.tox' -or -name '.mypy_cache' -or -name '.pytest_cache' -or -name '.nox' -or -name '.ruff_cache' \) -exec rm -rf -- '{}' +
		rm -f -- '${TEMP_CURRENT_JSON}' '${TEMP_ALL_JSON}' '${TEMP_PACKAGE_LIST}'

clean-repo:
		rm -rf -- '${REPO_TMPDIR}'

clean-rust:
		${SP_CARGO} clean

clean-sh:
		rm -f -- '${SH_BIN}'

clean-site:
		rm -rf -- site/docs
		rmdir site || true

pydist:
		rm -rf build
		[ ! -d dist ] || find dist -type f \( -name 'sp-variant*' -or -name 'sp_variant*' \) -delete
		${SP_PYTHON3} -m build --sdist --wheel

.PHONY:		all repo test test-trivial test-docker test-tox-stages clean clean-py clean-repo clean-rust clean-sh pydist pydist-build-repo
