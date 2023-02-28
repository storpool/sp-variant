# SPDX-FileCopyrightText: 2021 - 2023  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause
"""Common definitions for the OS/distribution variant detection library."""

from __future__ import annotations

import dataclasses
import sys

from typing import Any, Final, NamedTuple, Pattern, TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib


class Detect(NamedTuple):
    """Where (and what for) to look when figuring out which variant this is."""

    filename: str
    regex: Pattern[str]
    os_id: str
    os_version_regex: Pattern[str]


class CommandsPackage(NamedTuple):
    """Variant-specific commands related to OS packages."""

    update_db: list[str]
    install: list[str]
    list_all: list[str]
    purge: list[str]
    remove: list[str]
    remove_impl: list[str]


class CommandsPkgFile(NamedTuple):
    """Variant-specific commands related to OS package files."""

    dep_query: list[str]
    install: list[str]


class Commands(NamedTuple):
    """Variant-specific commands, mainly related to the packaging system."""

    package: CommandsPackage
    pkgfile: CommandsPkgFile


class DebRepo(NamedTuple):
    """The data to be stored in an Apt sources list file."""

    codename: str
    vendor: str
    sources: str
    keyring: str
    req_packages: list[str]


class YumRepo(NamedTuple):
    """The data to be stored in a Yum repository file."""

    yumdef: str
    keyring: str


class Builder(NamedTuple):
    """Information related to the StorPool internal autobuilders."""

    alias: str
    base_image: str
    branch: str
    kernel_package: str
    utf8_locale: str


class Supported(NamedTuple):
    """The aspects of the StorPool environment that are supported for this variant."""

    repo: bool


class Variant(NamedTuple):
    """The information about a Linux distribution version (build variant)."""

    name: str
    descr: str
    parent: str
    family: str
    detect: Detect
    supported: Supported
    commands: Commands
    min_sys_python: str
    repo: DebRepo | YumRepo
    package: dict[str, str]
    systemd_lib: str
    file_ext: str
    initramfs_flavor: str
    builder: Builder


class VariantUpdate(NamedTuple):
    """The changes to be applied to the parent variant definition."""

    name: str
    descr: str
    parent: str
    detect: Detect
    updates: dict[str, Any]


class OSPackage(NamedTuple):
    """The attributes of a currently-installed or known OS package."""

    name: str
    version: str
    arch: str
    status: str


class RepoType(NamedTuple):
    """Attributes common to a StorPool package repository."""

    name: str
    extension: str
    url: str


VERSION: Final = "3.1.1"
FORMAT_VERSION: Final = (1, 4)

REPO_TYPES: Final = [
    RepoType(name="contrib", extension="", url="https://repo.storpool.com/public/"),
    RepoType(
        name="staging",
        extension="-staging",
        url="https://repo.storpool.com/public/",
    ),
    RepoType(
        name="infra",
        extension="-infra",
        url="https://intrepo.storpool.com/repo/",
    ),
]


class VariantError(Exception):
    """Base class for errors that occurred during variant processing."""


class VariantConfigError(VariantError):
    """Invalid parameters passed to the variant routines."""


@dataclasses.dataclass(frozen=True)
class Config:
    """Runtime configuration for the sp-variant library functions."""

    args: list[str] | None = None
    command: str | None = None
    noop: bool = False
    repodir: pathlib.Path | None = None
    repotype: RepoType = REPO_TYPES[0]
    verbose: bool = False

    _diag_to_stderr: bool = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        """Log to the standard error stream by default."""
        object.__setattr__(self, "_diag_to_stderr", True)  # noqa: FBT003

    def diag(self, msg: str) -> None:
        """Output a diagnostic message in verbose mode."""
        if self.verbose:
            print(msg, file=sys.stderr if self._diag_to_stderr else sys.stdout)


def jsonify(obj: Any) -> Any:  # noqa: ANN401  # this needs to operate on, well, anything
    """Return a more readable representation of an object."""
    if type(obj).__name__.endswith("Pattern") and hasattr(obj, "pattern"):
        return jsonify(obj.pattern)

    if hasattr(obj, "_asdict"):
        return {name: jsonify(value) for name, value in obj._asdict().items()}
    if isinstance(obj, dict):
        return {name: jsonify(value) for name, value in obj.items()}

    if isinstance(obj, list):
        return [jsonify(item) for item in obj]

    return obj
