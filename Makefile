#!/usr/bin/make -f
#
# Copyright (c) 2021, 2022  StorPool <support@storpool.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.


RUST_DATA=	rust/data.rs
RUST_SRC=	rust/bin.rs rust/lib.rs rust/tests.rs rust/yai.rs ${RUST_DATA}
RUST_RELEASE=	${CURDIR}/target/x86_64-unknown-linux-musl/release
RUST_BIN=	${RUST_RELEASE}/storpool_variant

SH_SRC=		sp_variant.sh.j2
SH_BIN=		sp_variant.sh

SP_CARGO?=	sp-cargo

SP_PYTHON3?=	/opt/storpool/python3/bin/python3
SP_PY3_ENV?=	env PYTHONPATH='${CURDIR}/python' ${SP_PYTHON3} -B -u
SP_PY3_INVOKE?=	${SP_PY3_ENV} -m sp_variant
SP_PY3_NORMALIZE=	${SP_PY3_ENV} -c 'import json; import sys; print(json.dumps(json.loads(sys.stdin.read()), sort_keys=True, indent=2))'

PYTHON_VBUILD=	${CURDIR}/python/sp_variant/vbuild.py

REPO_TMPDIR?=	${CURDIR}/repo-build
REPO_BUILT=	${REPO_TMPDIR}/add-storpool-repo.tar.gz

TEMP_CURRENT_JSON?=	${CURDIR}/current-variant.json
TEMP_ALL_JSON?=		${CURDIR}/all-variants.json
TEMP_PACKAGE_LIST?=	${CURDIR}/package-list.txt

all:		${RUST_BIN} ${SH_BIN}

test:		test-trivial test-tox-delay

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

${REPO_BUILT}:	all test-trivial
		rm -rf -- '${REPO_TMPDIR}'
		[ ! -f '${REPO_BUILT}' ]
		mkdir -- '${REPO_TMPDIR}'
		${SP_PY3_ENV} -m sp_build_repo build -d '${CURDIR}/data' -D '${REPO_TMPDIR}' -r '${SH_BIN}' --no-date
		[ -f '${REPO_BUILT}' ]

repo:		${REPO_BUILT}

${RUST_DATA}:	${RUST_DATA}.j2 python/sp_build_repo/subst.py ${PYTHON_VBUILD}
		${SP_PY3_ENV} -m sp_build_repo.subst -m 644 -t '${RUST_DATA}.j2' -o '${RUST_DATA}' -v || { rm -f -- '${RUST_DATA}'; false; }
		${SP_CARGO} fmt -- '${RUST_DATA}'

${RUST_BIN}:	Cargo.toml .cargo/config.toml ${RUST_SRC}
		[ -n '${NO_CARGO_FREEZE}' ] || ${SP_CARGO} sp-freeze
		[ -n '${NO_CARGO_CLEAN}' ] || ${SP_CARGO} clean
		rm -f -- Cargo.lock
		${SP_CARGO} fmt -- --check
		${SP_CARGO} build --release --offline
		${SP_CARGO} test --release --offline

${SH_BIN}:	${SH_SRC} python/sp_build_repo/subst.py ${PYTHON_VBUILD}
		${SP_PY3_ENV} -m sp_build_repo.subst -m 755 -t '${SH_SRC}' -o '${SH_BIN}' -v || { rm -f -- '${SH_BIN}'; false; }

test-docker:	repo
		${SP_PY3_ENV} -m test_docker -r '${REPO_BUILT}' -v ${TEST_DOCKER_ARGS}

test-tox-delay:
		tox-delay -p all -e unit-tests-2,unit-tests-3 -- -p all

clean:		clean-py clean-repo clean-rust clean-sh

clean-py:
		find -- '${CURDIR}/python' -type d \( -name __pycache__ -or -name '*.egg-info' \) -exec rm -rf -- '{}' +
		find -- '${CURDIR}/python' -type f -name '*.pyc' -exec rm -- '{}' +
		rm -f -- '${TEMP_CURRENT_JSON}' '${TEMP_ALL_JSON}' '${TEMP_PACKAGE_LIST}'

clean-repo:
		rm -rf -- '${REPO_TMPDIR}'

clean-rust:
		${SP_CARGO} clean
		rm -f -- Cargo.lock

clean-sh:
		rm -f -- '${SH_BIN}'

pydist:
		rm -rf build
		[ ! -d dist ] || find dist -type f \( -name 'sp-variant*' -or -name 'sp_variant*' \) -delete
		${SP_PYTHON3} -m build --sdist --wheel

pydist-build-repo:
		rm -rf build
		[ ! -d dist ] || find dist -type f \( -name 'sp-build-repo*' -or -name 'sp_build_repo*' \) -delete
		[ ! -f setup-variant.cfg ]
		[ ! -f MANIFEST-variant.in ]
		[ -f setup-build-repo.cfg ]
		[ -f MANIFEST-build-repo.in ]
		mv -fv MANIFEST.in MANIFEST-variant.in
		mv -fv setup.cfg setup-variant.cfg
		cp -fv setup-build-repo.cfg setup.cfg
		cp -fv MANIFEST-build-repo.in MANIFEST.in
		${SP_PYTHON3} -m build --sdist || { mv -fv MANIFEST-variant.in MANIFEST.in; mv -fv setup-variant.cfg setup.cfg; false; }
		mv -fv MANIFEST-variant.in MANIFEST.in
		mv -fv setup-variant.cfg setup.cfg

.PHONY:		all repo test test-trivial test-docker test-tox-delay clean clean-py clean-repo clean-rust clean-sh pydist pydist-build-repo
