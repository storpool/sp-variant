#!/usr/bin/make -f

RUST_SRC=	$(wildcard rust/*.rs)
RUST_RELEASE=	${CURDIR}/target/x86_64-unknown-linux-musl/release
RUST_BIN=	${RUST_RELEASE}/storpool_variant

SP_CARGO?=	sp-cargo

SP_PYTHON3?=	/opt/storpool/python3/bin/python3
SP_PY3_INVOKE?=	env PYTHONPATH='${CURDIR}/python' ${SP_PYTHON3} -B -u -m sp_variant

all:		${RUST_BIN}
		${RUST_BIN} features
		${RUST_BIN} detect
		${RUST_BIN} command list
		${SP_PY3_INVOKE} features
		${SP_PY3_INVOKE} detect
		${SP_PY3_INVOKE} command list
		${SP_PY3_INVOKE} show all | diff -u '${CURDIR}/rust/variants-all.json' -

${RUST_BIN}:	Cargo.toml .cargo/config.toml ${RUST_SRC}
		${SP_CARGO} sp-freeze
		${SP_CARGO} clean
		rm -f -- Cargo.lock
		${SP_CARGO} fmt -- --check
		${SP_CARGO} build --release --offline
		${SP_CARGO} test --release --offline

clean:		clean-rust

clean-rust:
		${SP_CARGO} clean
		rm -f -- Cargo.lock

.PHONY:		all clean clean-rust
