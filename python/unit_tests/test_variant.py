# SPDX-FileCopyrightText: 2021 - 2024  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause
"""Test the functions in the sp.variant module."""

from __future__ import annotations

import collections
import dataclasses
import pathlib
import re
import sys
import typing
from unittest import mock

import pytest

from sp_variant import defs
from sp_variant import variant
from sp_variant import vbuild


if typing.TYPE_CHECKING:
    from typing import IO, Final


_MSG_NOT_SEEN = "This should not be seen"
_MSG_SEEN = "This should be seen"
_RE_CENTOS_VER = re.compile(r"^ .*? (?P<ver> \d+ ) $", re.X)


def test_get() -> None:
    """Test the operation of get_variant()."""
    assert variant.get_variant("CENTOS9").name == "CENTOS9"
    assert variant.get_variant("CENTOS8").name == "CENTOS8"

    repo = variant.get_variant("UBUNTU1804").repo
    assert isinstance(repo, defs.DebRepo)
    assert repo.vendor == "ubuntu"
    assert repo.codename == "bionic"

    repo = variant.get_variant("DEBIAN12").repo
    assert isinstance(repo, defs.DebRepo)
    assert repo.vendor == "debian"
    assert repo.codename == "bookworm"

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
    assert pathlib.Path(var.detect.filename).is_file()


def test_list_all() -> None:
    """Make sure that the package.list_all command does not go amok."""
    print()

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


def test_config_diag() -> None:
    """Test the `cfg_diag`-like functionality of the `Config` class."""
    output: list[tuple[str, IO[str]]] = []

    def check(*, seen: bool) -> None:
        """Make sure the output is exactly as expected."""
        if not seen:
            assert not output
            return

        assert output == [(_MSG_SEEN, sys.stderr)]
        output.clear()

    def init_cfg(*, verbose: bool, diag_to_stderr: bool = True) -> defs.Config:
        """Initialize a defs.Config object in the specified way."""
        cfg = defs.Config(verbose=verbose)
        assert cfg._diag_to_stderr  # noqa: SLF001

        if not diag_to_stderr:
            cfg._diag_to_stderr = False  # noqa: SLF001
            # It... did not change... right?
            assert cfg._diag_to_stderr  # noqa: SLF001

        # We cannot just set random properties, can we?
        with pytest.raises(dataclasses.FrozenInstanceError):
            cfg.random_property = 616  # type: ignore[attr-defined]
        assert not hasattr(cfg, "random_property")

        return cfg

    def mock_print(msg: str, *, file: IO[str]) -> None:
        """Mock a print() invocation."""
        output.append((msg, file))

    check(seen=False)

    cfg = init_cfg(verbose=False)
    with mock.patch("builtins.print", new=mock_print):
        cfg.diag(_MSG_NOT_SEEN)

    check(seen=False)

    cfg = init_cfg(verbose=True)
    with mock.patch("builtins.print", new=mock_print):
        cfg.diag(_MSG_SEEN)

    check(seen=True)

    # OK, can we do stdout now? No, right?
    cfg = init_cfg(verbose=True, diag_to_stderr=False)
    with mock.patch("builtins.print", new=mock_print):
        cfg.diag(_MSG_SEEN)

    check(seen=True)

    # Just for kicks...
    cfg = init_cfg(verbose=False, diag_to_stderr=False)
    with mock.patch("builtins.print", new=mock_print):
        cfg.diag(_MSG_NOT_SEEN)

    check(seen=False)


def test_builder_branches() -> None:
    """Make sure the builder branch assignments are sane."""
    all_variants: Final = variant.get_all_variants_in_order()

    # All supported Debian/Ubuntu branches should define a builder.
    missing: Final = [
        var
        for var in all_variants
        if var.family == "debian" and var.supported.repo and not var.builder.branch
    ]
    assert not missing

    # There should be a builder for all supported CentOS/Alma/Rocky numbered variants.
    def extract_version(var: variant.Variant) -> str:
        """Extract the version from a single CentOS-like variant."""
        vdata: Final = _RE_CENTOS_VER.match(var.name)
        assert vdata
        ver: Final = vdata.group("ver")
        assert ver
        return ver

    versions: Final = sorted(
        {extract_version(var) for var in all_variants if var.family == "redhat"},
    )
    assert versions
    missing_branches: Final = [
        branch
        for branch in (f"centos/{ver}" for ver in versions)
        if all(var.builder.branch != branch for var in all_variants)
    ]
    assert not missing_branches

    # And finally, there should only be one variant to declare a given builder branch.
    dup_branches: Final = sorted(
        item
        for item in collections.Counter(
            var.builder.branch for var in all_variants if var.builder.branch
        ).items()
        if item[1] != 1
    )
    assert not dup_branches
