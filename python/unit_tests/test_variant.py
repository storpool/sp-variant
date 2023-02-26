# SPDX-FileCopyrightText: 2021 - 2023  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause
"""Test the functions in the sp.variant module."""

import os

from typing import Final

import pytest

from sp_variant import defs
from sp_variant import variant
from sp_variant import vbuild


def test_get() -> None:
    """Test the operation of get_variant()."""
    assert variant.get_variant("CENTOS7").name == "CENTOS7"
    assert variant.get_variant("CENTOS6").name == "CENTOS6"

    repo = variant.get_variant("UBUNTU1804").repo
    assert isinstance(repo, defs.DebRepo)
    assert repo.vendor == "ubuntu"
    assert repo.codename == "bionic"

    repo = variant.get_variant("DEBIAN9").repo
    assert isinstance(repo, defs.DebRepo)
    assert repo.vendor == "debian"
    assert repo.codename == "stretch"

    with pytest.raises(variant.VariantKeyError):
        variant.get_variant("whee")


def test_roundtrip() -> None:
    """Run through the variants with some minimal sanity checks."""
    vbuild.build_variants(variant.Config(verbose=False))
    assert vbuild.VARIANTS
    for name in vbuild.VARIANTS:
        var = variant.get_variant(name)
        assert var.name == name
        avar = variant.get_by_alias(var.builder.alias)
        assert avar == var


def test_detect() -> None:
    """Make sure that detect_variant() returns a reasonably valid result."""
    var: Final = variant.detect_variant()
    assert var is not None
    assert os.path.isfile(var.detect.filename)


def test_list_all() -> None:
    """Make sure that the package.list_all command does not go amok."""
    print("")

    var: Final = variant.detect_variant()
    assert var is not None
    det_cmd: Final = list(var.commands.package.list_all)
    print(f"list_all command: {det_cmd!r}")

    pkgs_a: Final = variant.list_all_packages(var, patterns=["a*"])
    print(f"{len(pkgs_a)} packages with names starting with 'a'")
    assert det_cmd == var.commands.package.list_all

    pkgs_b: Final = variant.list_all_packages(var, patterns=["b*"])
    print(f"{len(pkgs_b)} packages with names starting with 'b'")
    assert det_cmd == var.commands.package.list_all

    pkgs_a_again: Final = variant.list_all_packages(var, patterns=["a*"])
    print(f"now {len(pkgs_a_again)} packages with names starting with 'a'")
    assert det_cmd == var.commands.package.list_all
    assert set(pkgs_a) == set(pkgs_a_again)

    # There should be at least one package installed on the system... right?
    pkgs_all: Final = variant.list_all_packages(var, patterns=["*"])
    print(f"{len(pkgs_all)} total packages on the system")
    assert pkgs_all
