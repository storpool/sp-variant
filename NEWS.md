# Change log for the sp-variant library

## 3.0.0 (2022-11-09)

- INCOMPATIBLE CHANGES:
    - Yum/DNF: when installing packages (both via the `package.install` and
      `pkgfile.install` commands), disable all the configured repositories,
      only enable some base system ones and the StorPool ones
    - python:
        - drop Python 2.6 support, use dict comprehensions
    - rust:
        - all the functions now return our own error enum instead of
          `Box<dyn error::Error>`
- all:
    - correctly treat Linux Mint 21.x as a Ubuntu 22.04 equivalent
    - allow repository definitions to be built using a different `storpool_variant`
      interpretation, mostly for testing the correctness of the Rust one
    - use the simpler container names for AlmaLinux and Rocky Linux
    - make AlmaLinux the principal RPM-based distribution instead of CentOS
    - add some initial support for AlmaLinux 9 and Rocky Linux 9
- python:
    - use the `cfg-diag` 0.4 `Config` class API
    - declare Python 3.10 and 3.11 as supported versions
    - drop the Rust and POSIX shell implementations from the sdist tarball
    - `sp_variant`:
        - now that `sp_build_repo` and `test_docker` use the `click` library,
          drop the `base_parser()` method
    - `sp_build_repo`:
        - mark the `-r` option as required, rename its long form to `--runtime`
        - allow repository URLs to be overridden using a TOML configuration file;
          provide a sample as `examples/build-repo-overrides.toml`
        - override a "duplicate code" warning from pylint
        - use the `typedload` library for validating and loading configuration data
        - use the `click` library for command-line argument parsing
        - use f-strings
        - use the Text type instead of str; long overdue
        - correctly use the `name` and `slug` fields when generating the repository
          definitions files
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
    - use a separate tool, `run-clippy.sh`, to invoke clippy;
      remove the `#![warn(...)]` directives from the individual source files
    - minor refactoring following some suggestions from clippy
    - override several clippy lints, mostly for good reasons
    - use the `clap` library for command-line parsing
    - use the `thiserror` library instead of the `quick-error` one, it is cleaner
    - use the `once_cell` library instead of the `lazy_static` one
    - use the `anyhow` library instead of `expect-exit` in the command-line tool
    - keep the `Cargo.lock` file under version control

## 2.3.3 (2022-04-28)

- all:
    - make the quoting style in the Debian/Ubuntu `pkgfile.dep_query` command
      consistent with that of the others
- sh:
    - fix the quoting for the Debian/Ubuntu `pkgfile.dep_query` command
    - complete the exiting-on-errors fix: two missed invocations
    - minor changes to implement some shellcheck suggestions
    - add a shellcheck test unless `NO_SHELLCHECK` is specified

## 2.3.2 (2022-04-27)

- sh:
    - fix exiting on errors in some situations; local variable declarations
      and error-checked assignments do not mix

## 2.3.1 (2022-04-27)

- sh:
    - fix matching the `VERSION_ID` variable in the `/etc/os-release` file:
      use a POSIX extended regular expression with `grep -E`, not
      a Perl-compatible one!

## 2.3.0 (2022-04-26)

- python:
    - now that there is a working POSIX shell implementation that is better
      suited for bootstrapping, split the Python library into several modules
    - always require the "typing" module to be installed
- rust:
    - possibly incompatible change: the structs and enums exported by
      the `sp_variant` crate are now marked as non-exhaustive
    - possibly incompatible change: some functions are now marked as
      "must use"
    - import struct names directory for a more idiomatic Rust style
    - many small improvements, mostly suggested by Clippy lints

## 2.2.0 (2022-02-05)
- all:
    - recognize Ubuntu 22.04 (Jammy Jellyfish)
- python:
    - fix two bugs in the `list_all_packages()` convenience function:
        - do not modify the variant structure's command list in place!
        - correctly recognize installed packages on Debian/Ubuntu systems
    - reformat with 100 characters per line
    - make the ArgumentParser-related type annotations a bit more precise to
      pass some checks in recent versions of Mypy
- rust:
    - change the dependency on nix to a >= relation, hoping they do not
      break backwards compatibility

## 2.1.1 (2021-12-18)
- all:
    - Add two-clause BSD licenses to all the source files.
    - Make sure all the implementations output the same thing for
      `command run package.list_all`.
- python:
    - Drop a "type: ignore" comment and bump the mypy version used for
      the test suite to 0.920.
- rust:
    - Fix a command.run bug: do not output the command to run, the tools
      that invoke `storpool_variant` may use its output!
    - Code clean-up:
        - drop an unused internal "url" field
        - simplify a double match
        - use `.find_map()` instead of reimplementing it
        - streamline `yai::parse()`

## 2.1.0 (2021-11-15)

- all:
    - On RedHat-derived distributions, the `package.list_all` command now
      displays the full epoch:version-release (EVR) string instead of
      only the version component.
    - Add support for Ubuntu 21.10 (Impish Indri).

## 2.0.0 (2021-10-24)

- all:
    - Add a "descr" field to the variant containing a brief
      human-readable name/description.
    - Install (or update as necessary) the ca-certificates package on
      RedHat-derived distributions, too, to take care of the Let's Encrypt
      certificate expiration debacle.
- sh:
    - Install ourselves as `/usr/sbin/sp_variant` in `repo add` so that
      other programs may use this helper.
- python:
    - Fix the program name in the usage message of the `sp_variant` and
      `sp_build_repo` tools.
- rust:
    - INCOMPATIBLE CHANGE: change the return type of `get_program_version()`
      and `get_program_version_from()` from `String` to `&str`.
    - Autogenerate the VariantKind enum.
    - Use the new Variant.descr field in the documentation.
    - Make the `sp_variant::data` module private.
    - Create the variants' data structure directly, do not decode a JSON
      document.
- build-repo:
    - Use trivver to sort DEBIAN9 before DEBIAN10.
- test-docker:
    - Add the "-i" option to limit the images to run on.
    - Run `apt-get update` if necessary.
    - Show the containers' output continually.

## 1.3.0 (2021-09-15)

- First public release.
