# Change log for the sp-variant library

## 2.1.0 (not yet)

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
