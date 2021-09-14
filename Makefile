#!/usr/bin/make -f

RUST_SRC=	$(wildcard rust/*.rs)
RUST_RELEASE=	${CURDIR}/target/x86_64-unknown-linux-musl/release
RUST_BIN=	${RUST_RELEASE}/storpool_variant
RUST_VARIANT_JSON=	${CURDIR}/rust/variants-all.json

SH_SRC=		sp_variant.sh.j2
SH_BIN=		sp_variant.sh

SP_CARGO?=	sp-cargo

SP_PYTHON3?=	/opt/storpool/python3/bin/python3
SP_PY3_ENV?=	env PYTHONPATH='${CURDIR}/python' ${SP_PYTHON3} -B -u
SP_PY3_INVOKE?=	${SP_PY3_ENV} -m sp_variant
SP_PY3_NORMALIZE=	${SP_PY3_ENV} -c 'import json; import sys; print(json.dumps(json.loads(sys.stdin.read()), sort_keys=True, indent=2))'

PYTHON_MAIN=	${CURDIR}/python/sp_variant/__main__.py

REPO_TMPDIR?=	${CURDIR}/repo-build
REPO_BUILT=	${REPO_TMPDIR}/add-storpool-repo.tar.gz

TEMP_CURRENT_JSON?=	${CURDIR}/current-variant.json

all:		${RUST_BIN} ${SH_BIN}
		${SP_PY3_INVOKE} show current > '${TEMP_CURRENT_JSON}'
		${RUST_BIN} features
		${RUST_BIN} detect
		${RUST_BIN} command list
		${RUST_BIN} show current | ${SP_PY3_NORMALIZE} | diff -u '${TEMP_CURRENT_JSON}' -
		${CURDIR}/${SH_BIN} detect
		${CURDIR}/${SH_BIN} show all | ${SP_PY3_NORMALIZE} | diff -u '${CURDIR}/rust/variants-all.json' -
		${CURDIR}/${SH_BIN} show current | ${SP_PY3_NORMALIZE} | diff -u '${TEMP_CURRENT_JSON}' -
		${SP_PY3_INVOKE} features
		${SP_PY3_INVOKE} detect
		${SP_PY3_INVOKE} command list
		${SP_PY3_INVOKE} show all | diff -u '${CURDIR}/rust/variants-all.json' -

${REPO_BUILT}:	all
		rm -rf -- '${REPO_TMPDIR}'
		[ ! -f '${REPO_BUILT}' ]
		mkdir -- '${REPO_TMPDIR}'
		${SP_PY3_ENV} -m sp_build_repo build -d '${CURDIR}/data' -D '${REPO_TMPDIR}' -r '${SH_BIN}' --no-date
		[ -f '${REPO_BUILT}' ]

repo:		${REPO_BUILT}

${RUST_VARIANT_JSON}:	${PYTHON_MAIN}
		${SP_PY3_INVOKE} show all > '${RUST_VARIANT_JSON}' || { rm -f -- '${RUST_VARIANT_JSON}'; false; }

${RUST_BIN}:	Cargo.toml .cargo/config.toml ${RUST_SRC} ${RUST_VARIANT_JSON}
		${SP_CARGO} sp-freeze
		[ -n '${NO_CARGO_CLEAN}' ] || ${SP_CARGO} clean
		rm -f -- Cargo.lock
		${SP_CARGO} fmt -- --check
		${SP_CARGO} build --release --offline
		${SP_CARGO} test --release --offline

${SH_BIN}:	${SH_SRC} python/sp_build_repo/subst.py ${PYTHON_MAIN}
		${SP_PY3_ENV} -m sp_build_repo.subst -m 755 -t '${SH_SRC}' -o '${SH_BIN}' -v || { rm -f -- '${SH_BIN}'; false; }

test-docker:	repo
		${SP_PY3_ENV} -m test_docker -r '${REPO_BUILT}' -v

clean:		clean-py clean-repo clean-rust clean-sh

clean-py:
		find -- '${CURDIR}/python' -type d \( -name __pycache__ -or -name '*.egg-info' \) -exec rm -rf -- '{}' +
		find -- '${CURDIR}/python' -type f -name '*.pyc' -exec rm -- '{}' +
		rm -f -- '${TEMP_CURRENT_JSON}'

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
		[ ! -f MANIFEST.in ]
		[ -f setup-build-repo.cfg ]
		[ -f MANIFEST-build-repo.in ]
		mv -fv setup.cfg setup-variant.cfg
		cp -fv setup-build-repo.cfg setup.cfg
		cp -fv MANIFEST-build-repo.in MANIFEST.in
		${SP_PYTHON3} -m build --sdist || { mv -fv setup-variant.cfg setup.cfg; rm -f MANIFEST.in; false; }
		mv -fv setup-variant.cfg setup.cfg
		rm -f MANIFEST.in

.PHONY:		all repo test-docker clean clean-py clean-repo clean-rust clean-sh pydist pydist-build-repo
