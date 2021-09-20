# Change log for the sp-variant library

## 1.4.0 (not yet)

- all:
  - Add a "descr" field to the variant containing a brief
    human-readable name/description.
- sh:
  - Install ourselves as `/usr/sbin/sp_variant` in `repo add` so that
    other programs may use this helper.
- rust:
  - Autogenerate the VariantKind enum.
  - Use the new Variant.descr field in the documentation.
- build-repo:
  - Use trivver to sort DEBIAN9 before DEBIAN10.

## 1.3.0 (2021-09-15)

- First public release.
