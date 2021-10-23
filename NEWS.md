# Change log for the sp-variant library

## 2.0.0 (not yet)

- all:
  - Add a "descr" field to the variant containing a brief
    human-readable name/description.
  - Install (or update as necessary) the ca-certificates package on
    RedHat-derived distributions, too, to take care of the Let's Encrypt
    certificate expiration debacle.
- sh:
  - Install ourselves as `/usr/sbin/sp_variant` in `repo add` so that
    other programs may use this helper.
- rust:
  - Autogenerate the VariantKind enum.
  - Use the new Variant.descr field in the documentation.
- build-repo:
  - Use trivver to sort DEBIAN9 before DEBIAN10.
- test-docker:
  - Add the "-i" option to limit the images to run on.
  - Run `apt-get update` if necessary.
  - Show the containers' output continually.

## 1.3.0 (2021-09-15)

- First public release.
