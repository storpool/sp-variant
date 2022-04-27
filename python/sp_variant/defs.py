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
"""Common definitions for the OS/distribution variant detection library."""

from __future__ import print_function

import sys

from typing import (
    Any,  # noqa: H301
    Dict,
    List,
    NamedTuple,
    Optional,
    Pattern,
    Text,
    Union,
)


Detect = NamedTuple(  # pylint: disable=invalid-name
    "Detect",
    [
        ("filename", Text),
        ("regex", Pattern[Text]),
        ("os_id", Text),
        ("os_version_regex", Pattern[Text]),
    ],
)

CommandsPackage = NamedTuple(  # pylint: disable=invalid-name
    "CommandsPackage",
    [
        ("update_db", List[Text]),
        ("install", List[Text]),
        ("list_all", List[Text]),
        ("purge", List[Text]),
        ("remove", List[Text]),
        ("remove_impl", List[Text]),
    ],
)

CommandsPkgFile = NamedTuple(  # pylint: disable=invalid-name
    "CommandsPkgFile",
    [
        ("dep_query", List[Text]),
        ("install", List[Text]),
    ],
)

Commands = NamedTuple(  # pylint: disable=invalid-name
    "Commands",
    [
        ("package", CommandsPackage),
        ("pkgfile", CommandsPkgFile),
    ],
)

DebRepo = NamedTuple(  # pylint: disable=invalid-name
    "DebRepo",
    [
        ("codename", Text),
        ("vendor", Text),
        ("sources", Text),
        ("keyring", Text),
        ("req_packages", List[Text]),
    ],
)

YumRepo = NamedTuple(  # pylint: disable=invalid-name
    "YumRepo",
    [
        ("yumdef", Text),
        ("keyring", Text),
    ],
)

Builder = NamedTuple(  # pylint: disable=invalid-name
    "Builder",
    [
        ("alias", Text),
        ("base_image", Text),
        ("branch", Text),
        ("kernel_package", Text),
        ("utf8_locale", Text),
    ],
)

Variant = NamedTuple(  # pylint: disable=invalid-name
    "Variant",
    [
        ("name", Text),
        ("descr", Text),
        ("parent", Text),
        ("family", Text),
        ("detect", Detect),
        ("commands", Commands),
        ("min_sys_python", Text),
        ("repo", Union[DebRepo, YumRepo]),
        ("package", Dict[str, str]),
        ("systemd_lib", Text),
        ("file_ext", Text),
        ("initramfs_flavor", Text),
        ("builder", Builder),
    ],
)

VariantUpdate = NamedTuple(  # pylint: disable=invalid-name
    "VariantUpdate",
    [
        ("name", Text),
        ("descr", Text),
        ("parent", Text),
        ("detect", Detect),
        ("updates", Dict[str, Any]),
    ],
)

OSPackage = NamedTuple(  # pylint: disable=invalid-name
    "OSPackage",
    [
        ("name", Text),
        ("version", Text),
        ("arch", Text),
        ("status", Text),
    ],
)

RepoType = NamedTuple("RepoType", [("name", str), ("extension", str), ("url", str)])

if sys.version_info[0] >= 3:
    TextType = str
    BytesType = bytes
else:
    TextType = unicode  # noqa: F821  # pylint: disable=undefined-variable
    BytesType = str


VERSION = "2.3.1"
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


class Config(object):  # pylint: disable=too-few-public-methods
    """Basic configuration: a "verbose" field and a diag() method."""

    def __init__(
        self,  # type: Config
        args=None,  # type: Optional[List[Text]]
        command=None,  # type: Optional[Text]
        noop=False,  # type: bool
        repodir=None,  # type: Optional[Text]
        repotype=REPO_TYPES[0],  # type: RepoType
        verbose=False,  # type: bool
    ):  # type: (...) -> None
        """Store the verbosity setting."""
        # pylint: disable=too-many-arguments
        self.args = args
        self.command = command
        self.noop = noop
        self.repodir = repodir
        self.repotype = repotype
        self.verbose = verbose
        self._diag_to_stderr = True

    def diag(self, msg):
        # type: (Config, Text) -> None
        """Output a diagnostic message in verbose mode."""
        if self.verbose:
            print(msg, file=sys.stderr if self._diag_to_stderr else sys.stdout)


def jsonify(obj):
    # type: (Any) -> Any
    """Return a more readable representation of an object."""
    if type(obj).__name__.endswith("Pattern") and hasattr(obj, "pattern"):
        return jsonify(obj.pattern)

    if hasattr(obj, "_asdict"):
        return dict((name, jsonify(value)) for name, value in obj._asdict().items())
    if isinstance(obj, dict):
        return dict((name, jsonify(value)) for name, value in obj.items())

    if isinstance(obj, list):
        return [jsonify(item) for item in obj]

    return obj
