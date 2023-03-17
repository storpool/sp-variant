<!--
SPDX-FileCopyrightText: 2021 - 2023  StorPool <support@storpool.com>
SPDX-License-Identifier: BSD-2-Clause
-->

# Changelog

All notable changes to the sp-variant project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.1.2] - 2023-03-17

### Semi-incompatible changes

- python:
    - deprecate the `defs.Config._diag_to_stderr` member variable;
      replace it with a read-only property that always returns true and
      a `__setattr__()` override that detects and ignores attempts to
      modify it. Both will be removed in a future version of sp-variant.

### Additions

- python:
    - add some more PyPI trove classifiers to the setuptools metadata
    - break out the Tox environments' dependencies into separate files so
      that they may be reused by external tools
    - `test_docker`: allow multiple `-i imagepattern` options to be
      specified so that several unrelated Docker images may be tested in
      a single run
- Start some MkDocs-based documentation with a copy of the README file and
  the changelog moved there

### Other changes

- python:
    - move the setuptools metadata to the `pyproject.toml` file
    - test with ruff 0.0.256, drop a couple of overrides for false
      positives emitted by earlier versions of Ruff
    - invoke the `tox-stages` tool from the directory where the Python 3.x
      interpreter lives, so that it is virtually certain that `tox-stages`
      (and consequenty Tox) will use the same Python interpreter
    - drop the `types-dataclasses` dependency for the `mypy` Tox test
      environment; dataclasses are included with Python 3.8
    - clean up some more Python-related files in the `clean` Makefile target

## [3.1.1] - 2023-02-28

### Fixes

- python:
    - do not build a universal wheel

### Other changes

- python:
    - test with ruff 0.0.253 with no changes

## [3.1.0] - 2023-02-28

### Semi-incompatible changes

- python:
    - drop Python 2.x compatibility
    - drop Python 3.6 and 3.7 compatibility; 3.8 and 3.9 will probably also be
      dropped in an upcoming release
- rust:
    - use named arguments for `format!()`, `println!()`, etc, and declare
      a minimum Rust supported version of 1.58

### Fixes

- use the `en_US.UTF-8` locale for CentOS 7.x and the related variants;
  we should really specify a UTF-8-capable locale, and `en_US.UTF-8` is
  installed by default on most minimal container setups
- use the `C.UTF-8` locale for CentOS 8.x/9.x and the related variants;
  this is the preferred POSIX name of the locale, `C.utf8` is merely
  an implementation detail
- use the `appstream` DNF/Yum repository for CentOS 8.x/9.x and the related
  variants; it should be enabled by default at this point in time, and some of
  the software that the various StorPool packages need has moved there
- python:
    - fix the way the `_fields` member of various named tuples is accessed
    - fix the format of several module and function docstrings
    - `sp_build_repo`: obtain the current date in a better timezone-aware way
    - mark the `setup.py` file as executable

### Additions

- all:
    - add the `supported` variant member with a single boolean field, `repo`,
      that declares whether StorPool provides a third-party OS packages
      repository for that variant
    - bump the variant description format version to 1.4 for the added
      `supported` member

### Other changes

- use the "Keep a Changelog" format for the changelog file
- python:
    - use the StorPool Python 2.x interpreter for the Tox tests
    - use the `tox-stages` utility instead of the `tox-delay` one
    - drop the Python 2.x, 3.6, and 3.7 compatibility, use some Python 3.x
      language features and modules that are in the standard library now
    - use black 23.x and flake8 6.x with no changes
    - use pylint 2.16.x, fix some of the issues it reported
    - start using ruff, fix some of the issues it reported
- rust:
    - bump the minor versions of the `anyhow`, `once_cell`, and `thiserror`
      dependencies to sync them with the StorPool `sp-rust-crates-io` package
    - let clippy know that we do mean to request a blanket `clippy::restriction`
      set of checks
- test-docker: test the `builder.utf8_locale` setting

## [3.0.0] - 2022-11-09

### Incompatible changes

- all:
    - Yum/DNF: when installing packages (both via the `package.install` and
      `pkgfile.install` commands), disable all the configured repositories,
      only enable some base system ones and the StorPool ones
- python:
    - drop Python 2.6 support, use dict comprehensions
- rust:
    - all the functions now return our own error enum instead of
      `Box<dyn error::Error>`

### Fixes

- all:
    - correctly treat Linux Mint 21.x as a Ubuntu 22.04 equivalent
    - make AlmaLinux the principal RPM-based distribution instead of CentOS
- python:
    - `sp_build_repo`:
        - correctly use the `name` and `slug` fields when generating the repository
          definitions files

### Additions

- all:
    - add some initial support for AlmaLinux 9 and Rocky Linux 9
- python:
    - `sp_build_repo`:
        - allow repository URLs to be overridden using a TOML configuration file;
          provide a sample as `examples/build-repo-overrides.toml`
- rust:
    - use a separate tool, `run-clippy.sh`, to invoke clippy;
      remove the `#![warn(...)]` directives from the individual source files
    - keep the `Cargo.lock` file under version control

### Other changes

- all:
    - allow repository definitions to be built using a different `storpool_variant`
      interpretation, mostly for testing the correctness of the Rust one
    - use the simpler container names for AlmaLinux and Rocky Linux
- python:
    - use the `cfg-diag` 0.4 `Config` class API
    - declare Python 3.10 and 3.11 as supported versions
    - drop the Rust and POSIX shell implementations from the sdist tarball
    - `sp_variant`:
        - now that `sp_build_repo` and `test_docker` use the `click` library,
          drop the `base_parser()` method
    - `sp_build_repo`:
        - mark the `-r` option as required, rename its long form to `--runtime`
        - override a "duplicate code" warning from pylint
        - use the `typedload` library for validating and loading configuration data
        - use the `click` library for command-line argument parsing
        - use f-strings
        - use the Text type instead of str; long overdue
    - `test_docker`:
        - install the StorPool Python packages to make sure the repository is
          indeed accessible and configured correctly
        - only use `asyncio.run()` for the parts that need to run asynchronously
          (e.g. not for command-line parsing or trivial queries)
        - use the `click` library for command-line argument parsing
        - run `docker swap` for the CentOS 8 container to switch to the CentOS Stream
          repositories; maybe we need to start using the quay.io containers instead
    - test suite:
        - specify version constraints for the library dependencies
        - use `pytest.mark.parametrize()` instead of the `ddt` library
        - drop the Python 2.x mypy and the `flake8` + `hacking` test environments,
          they do not provide much value nowadays
        - drop the outdated `pytest.pyi` typing stub
        - move the configuration for the check tools out of the `tox.ini` file,
          mostly into `pyproject.toml`, but still `setup.cfg` for `flake8`
- rust:
    - minor refactoring following some suggestions from clippy
    - override several clippy lints, mostly for good reasons
    - use the `clap` library for command-line parsing
    - use the `thiserror` library instead of the `quick-error` one, it is cleaner
    - use the `once_cell` library instead of the `lazy_static` one
    - use the `anyhow` library instead of `expect-exit` in the command-line tool

## [2.3.3] - 2022-04-28

### Fixes

- all:
    - make the quoting style in the Debian/Ubuntu `pkgfile.dep_query` command
      consistent with that of the others
- sh:
    - fix the quoting for the Debian/Ubuntu `pkgfile.dep_query` command
    - complete the exiting-on-errors fix: two missed invocations

### Other changes

- sh:
    - minor changes to implement some shellcheck suggestions
    - add a shellcheck test unless `NO_SHELLCHECK` is specified

## [2.3.2] - 2022-04-27

### Fixes

- sh:
    - fix exiting on errors in some situations; local variable declarations
      and error-checked assignments do not mix

## [2.3.1] - 2022-04-27

### Fixes

- sh:
    - fix matching the `VERSION_ID` variable in the `/etc/os-release` file:
      use a POSIX extended regular expression with `grep -E`, not
      a Perl-compatible one!

## [2.3.0] - 2022-04-26

### Incompatible changes

- rust:
    - the structs and enums exported by the `sp_variant` crate are now
      marked as non-exhaustive
    - some functions are now marked as "must use"

### Other changes

- python:
    - now that there is a working POSIX shell implementation that is better
      suited for bootstrapping, split the Python library into several modules
    - always require the "typing" module to be installed
- rust:
    - import struct names directory for a more idiomatic Rust style
    - many small improvements, mostly suggested by Clippy lints

## [2.2.0] - 2022-02-05

### Fixes

- python:
    - fix two bugs in the `list_all_packages()` convenience function:
        - do not modify the variant structure's command list in place!
        - correctly recognize installed packages on Debian/Ubuntu systems

### Additions

- all:
    - recognize Ubuntu 22.04 (Jammy Jellyfish)

### Other changes

- python:
    - reformat with 100 characters per line
    - make the ArgumentParser-related type annotations a bit more precise to
      pass some checks in recent versions of Mypy
- rust:
    - change the dependency on nix to a >= relation, hoping they do not
      break backwards compatibility

## [2.1.1] - 2021-12-18

### Fixes

- all:
    - Make sure all the implementations output the same thing for
      `command run package.list_all`.
- rust:
    - Fix a command.run bug: do not output the command to run, the tools
      that invoke `storpool_variant` may use its output!

### Other changes

- all:
    - Add two-clause BSD licenses to all the source files.
- python:
    - Drop a "type: ignore" comment and bump the mypy version used for
      the test suite to 0.920.
- rust:
    - Code clean-up:
        - drop an unused internal "url" field
        - simplify a double match
        - use `.find_map()` instead of reimplementing it
        - streamline `yai::parse()`

## [2.1.0] - 2021-11-15

### Fixes

- all:
    - On RedHat-derived distributions, the `package.list_all` command now
      displays the full epoch:version-release (EVR) string instead of
      only the version component.

### Additions

- all:
    - Add support for Ubuntu 21.10 (Impish Indri).

## [2.0.0] - 2021-10-24

### Incompatible changes

- rust:
    - change the return type of `get_program_version()` and
      `get_program_version_from()` from `String` to `&str`.

### Fixes

- all:
    - Install (or update as necessary) the ca-certificates package on
      RedHat-derived distributions, too, to take care of the Let's Encrypt
      certificate expiration debacle.
- python:
    - Fix the program name in the usage message of the `sp_variant` and
      `sp_build_repo` tools.
- build-repo:
    - Use trivver to sort DEBIAN9 before DEBIAN10.
- test-docker:
    - Run `apt-get update` if necessary.

### Additions

- all:
    - Add a "descr" field to the variant containing a brief
      human-readable name/description.
- sh:
    - Install ourselves as `/usr/sbin/sp_variant` in `repo add` so that
      other programs may use this helper.
- rust:
    - Use the new Variant.descr field in the documentation.

### Other changes

- rust:
    - Autogenerate the VariantKind enum.
    - Make the `sp_variant::data` module private.
    - Create the variants' data structure directly, do not decode a JSON
      document.
- test-docker:
    - Add the "-i" option to limit the images to run on.
    - Show the containers' output continually.

## [1.3.0] - 2021-09-15

### Started

- First public release.

[Unreleased]: https://github.com/storpool/sp-variant/compare/release/3.1.2...main
[3.1.2]: https://github.com/storpool/sp-variant/compare/release/3.1.1...release/3.1.2
[3.1.1]: https://github.com/storpool/sp-variant/compare/release/3.1.0...release/3.1.1
[3.1.0]: https://github.com/storpool/sp-variant/compare/release/3.0.0...release/3.1.0
[3.0.0]: https://github.com/storpool/sp-variant/compare/release/2.3.3...release/3.0.0
[2.3.3]: https://github.com/storpool/sp-variant/compare/release/2.3.2...release/2.3.3
[2.3.2]: https://github.com/storpool/sp-variant/compare/release/2.3.1...release/2.3.2
[2.3.1]: https://github.com/storpool/sp-variant/compare/release/2.3.0...release/2.3.1
[2.3.0]: https://github.com/storpool/sp-variant/compare/release/2.2.0...release/2.3.0
[2.2.0]: https://github.com/storpool/sp-variant/compare/release/2.1.1...release/2.2.0
[2.1.1]: https://github.com/storpool/sp-variant/compare/release/2.1.0...release/2.1.1
[2.1.0]: https://github.com/storpool/sp-variant/compare/release/2.0.0...release/2.1.0
[2.0.0]: https://github.com/storpool/sp-variant/compare/release/1.3.0...release/2.0.0
[1.3.0]: https://github.com/storpool/sp-variant/releases/tag/release%2F1.3.0
