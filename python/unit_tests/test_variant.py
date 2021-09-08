"""Test the functions in the sp.variant module."""

from __future__ import print_function

import os

import pytest

from sp_variant import __main__ as spvar


def test_get():
    # type: () -> None
    """Test the operation of get_variant()."""
    assert spvar.get_variant("CENTOS7").name == "CENTOS7"
    assert spvar.get_variant("CENTOS6").name == "CENTOS6"

    repo = spvar.get_variant("UBUNTU1804").repo
    assert isinstance(repo, spvar.DebRepo)
    assert repo.vendor == "ubuntu"
    assert repo.codename == "bionic"

    repo = spvar.get_variant("DEBIAN9").repo
    assert isinstance(repo, spvar.DebRepo)
    assert repo.vendor == "debian"
    assert repo.codename == "stretch"

    with pytest.raises(spvar.VariantKeyError):
        spvar.get_variant("whee")


def test_roundtrip():
    # type: () -> None
    """Run through the variants with some minimal sanity checks."""
    spvar.build_variants(spvar.Config(verbose=False))
    assert spvar.VARIANTS
    for name in spvar.VARIANTS:
        var = spvar.get_variant(name)
        assert var.name == name
        avar = spvar.get_by_alias(var.builder.alias)
        assert avar == var


def test_detect():
    # type: () -> None
    """Make sure that detect_variant() returns a reasonably valid result."""
    var = spvar.detect_variant()
    assert var is not None
    assert os.path.isfile(var.detect.filename)
