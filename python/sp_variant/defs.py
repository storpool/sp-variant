# Copyright (c) 2021 - 2023  StorPool <support@storpool.com>
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
"""Common definitions for the OS/distribution variant detection library."""

import sys

from typing import Any, Dict, List, NamedTuple, Optional, Pattern, Union


class Detect(NamedTuple):
    """Where (and what for) to look when figuring out which variant this is."""

    filename: str
    regex: Pattern[str]
    os_id: str
    os_version_regex: Pattern[str]


class CommandsPackage(NamedTuple):
    """Variant-specific commands related to OS packages."""

    update_db: List[str]
    install: List[str]
    list_all: List[str]
    purge: List[str]
    remove: List[str]
    remove_impl: List[str]


class CommandsPkgFile(NamedTuple):
    """Variant-specific commands related to OS package files."""

    dep_query: List[str]
    install: List[str]


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
    req_packages: List[str]


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


class Variant(NamedTuple):
    """The information about a Linux distribution version (build variant)."""

    name: str
    descr: str
    parent: str
    family: str
    detect: Detect
    commands: Commands
    min_sys_python: str
    repo: Union[DebRepo, YumRepo]
    package: Dict[str, str]
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
    updates: Dict[str, Any]


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


VERSION = "3.0.1"
FORMAT_VERSION = (1, 3)

REPO_TYPES = [
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


class Config:  # pylint: disable=too-few-public-methods
    """Basic configuration: a "verbose" field and a diag() method."""

    args: Optional[List[str]]
    command: Optional[str]
    noop: bool
    repodir: Optional[str]
    repotype: RepoType
    verbose: bool

    def __init__(
        self,
        args: Optional[List[str]] = None,
        command: Optional[str] = None,
        noop: bool = False,
        repodir: Optional[str] = None,
        repotype: RepoType = REPO_TYPES[0],
        verbose: bool = False,
    ) -> None:
        """Store the verbosity setting."""
        # pylint: disable=too-many-arguments
        self.args = args
        self.command = command
        self.noop = noop
        self.repodir = repodir
        self.repotype = repotype
        self.verbose = verbose
        self._diag_to_stderr = True

    def diag(self, msg: str) -> None:
        """Output a diagnostic message in verbose mode."""
        if self.verbose:
            print(msg, file=sys.stderr if self._diag_to_stderr else sys.stdout)


def jsonify(obj: Any) -> Any:
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
