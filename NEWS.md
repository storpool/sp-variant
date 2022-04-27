# Change log for the sp-variant library

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
    the sp_variant crate are now marked as non-exhaustive
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
    that invoke storpool_variant may use its output!
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
