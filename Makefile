#!/usr/bin/make -f

RUST_SRC=	$(wildcard rust/*.rs)
RUST_RELEASE=	${CURDIR}/target/x86_64-unknown-linux-musl/release
RUST_BIN=	${RUST_RELEASE}/storpool_variant
RUST_VARIANT_JSON=	${CURDIR}/rust/variants-all.json

SP_CARGO?=	sp-cargo

SP_PYTHON3?=	/opt/storpool/python3/bin/python3
SP_PY3_ENV?=	env PYTHONPATH='${CURDIR}/python' ${SP_PYTHON3} -B -u
SP_PY3_INVOKE?=	${SP_PY3_ENV} -m sp_variant

PYTHON_MAIN=	${CURDIR}/python/sp_variant/__main__.py

REPO_TMPDIR?=	${CURDIR}/repo-build
REPO_BUILT=	${REPO_TMPDIR}/add-storpool-repo.tar.gz

all:		${RUST_BIN}
		${RUST_BIN} features
		${RUST_BIN} detect
		${RUST_BIN} command list
		${SP_PY3_INVOKE} features
		${SP_PY3_INVOKE} detect
		${SP_PY3_INVOKE} command list
		${SP_PY3_INVOKE} show all | diff -u '${CURDIR}/rust/variants-all.json' -

${REPO_BUILT}:	all
		rm -rf -- '${REPO_TMPDIR}'
		[ ! -f '${REPO_BUILT}' ]
		mkdir -- '${REPO_TMPDIR}'
		${SP_PY3_ENV} -m sp_variant.repo build -d '${CURDIR}/data' -D '${REPO_TMPDIR}' -r '${RUST_BIN}' --no-date
		[ -f '${REPO_BUILT}' ]

repo:		${REPO_BUILT}

${RUST_VARIANT_JSON}:	${PYTHON_MAIN}
		${SP_PY3_INVOKE} show all > '${RUST_VARIANT_JSON}' || { rm -f -- '${RUST_VARIANT_JSON}'; false; }

${RUST_BIN}:	Cargo.toml .cargo/config.toml ${RUST_SRC} ${RUST_VARIANT_JSON}
		${SP_CARGO} sp-freeze
		${SP_CARGO} clean
		rm -f -- Cargo.lock
		${SP_CARGO} fmt -- --check
		${SP_CARGO} build --release --offline
		${SP_CARGO} test --release --offline

test-docker:	repo
		${SP_PY3_ENV} -m test_docker -r '${REPO_BUILT}' -v

clean:		clean-repo clean-rust

clean-repo:
		rm -rf -- '${REPO_TMPDIR}'

clean-rust:
		${SP_CARGO} clean
		rm -f -- Cargo.lock

.PHONY:		all repo test-docker clean clean-repo clean-rust
