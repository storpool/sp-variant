# Copyright (c) 2021, 2022  StorPool <support@storpool.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#
"""Test the functions in the sp.variant module."""

from __future__ import print_function

import os

import pytest

from sp_variant import defs
from sp_variant import variant
from sp_variant import vbuild


def test_get():
    # type: () -> None
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


def test_roundtrip():
    # type: () -> None
    """Run through the variants with some minimal sanity checks."""
    vbuild.build_variants(variant.Config(verbose=False))
    assert vbuild.VARIANTS
    for name in vbuild.VARIANTS:
        var = variant.get_variant(name)
        assert var.name == name
        avar = variant.get_by_alias(var.builder.alias)
        assert avar == var


def test_detect():
    # type: () -> None
    """Make sure that detect_variant() returns a reasonably valid result."""
    var = variant.detect_variant()
    assert var is not None
    assert os.path.isfile(var.detect.filename)


def test_list_all():
    # type: () -> None
    """Make sure that the package.list_all command does not go amok."""
    print("")

    var = variant.detect_variant()
    assert var is not None
    det_cmd = list(var.commands.package.list_all)
    print("list_all command: {det_cmd!r}".format(det_cmd=det_cmd))

    pkgs_a = variant.list_all_packages(var, patterns=["a*"])
    print("{count} packages with names starting with 'a'".format(count=len(pkgs_a)))
    assert det_cmd == var.commands.package.list_all

    pkgs_b = variant.list_all_packages(var, patterns=["b*"])
    print("{count} packages with names starting with 'b'".format(count=len(pkgs_b)))
    assert det_cmd == var.commands.package.list_all

    pkgs_a_again = variant.list_all_packages(var, patterns=["a*"])
    print("now {count} packages with names starting with 'a'".format(count=len(pkgs_a_again)))
    assert det_cmd == var.commands.package.list_all
    assert set(pkgs_a) == set(pkgs_a_again)

    # There should be at least one package installed on the system... right?
    pkgs_all = variant.list_all_packages(var, patterns=["*"])
    print("{count} total packages on the system".format(count=len(pkgs_all)))
    assert pkgs_all
