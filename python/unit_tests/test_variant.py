# Copyright (c) 2021  StorPool <support@storpool.com>
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
