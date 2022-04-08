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
"""Build variant definitions and commands."""

import errno
import io
import subprocess

from typing import Dict, Iterable, List, Optional, Text  # noqa: H301

from . import defs
from . import vbuild
from . import yaiparser

from .defs import (
    Config,  # noqa: H301
    Variant,
    VariantError,
    VERSION,
)

from .vbuild import update_namedtuple


class VariantKeyError(VariantError):
    """A variant with an unknown name was requested."""


class VariantFileError(VariantError):
    """A filesystem-related error occurred."""


class VariantRemoteError(VariantError):
    """An error occurred while communicating with a remote host."""

    def __init__(self, hostname, msg):
        # type: (VariantRemoteError, Text, Text) -> None
        """Store the hostname and the error message."""
        super(VariantRemoteError, self).__init__()
        self.hostname = hostname
        self.msg = msg

    def __str__(self):
        # type: () -> str
        """Return a human-readable representation of the error."""
        return "{host}: {err}".format(host=self.hostname, err=self.msg)


class VariantDetectError(VariantError):
    """An error that occurred during the detection of a variant."""


_DEFAULT_CONFIG = Config()

SAFEENC = "Latin-1"


def detect_variant(cfg=_DEFAULT_CONFIG):
    # type: (Config) -> Variant
    """Detect the build variant for the current host."""
    vbuild.build_variants(cfg)
    cfg.diag("Trying to detect the current hosts's build variant")

    try:
        data = yaiparser.YAIParser("/etc/os-release").parse()
        os_id, os_version = data.get("ID"), data.get("VERSION_ID")
    except (IOError, OSError) as err:
        if err.errno != errno.ENOENT:
            raise
        os_id, os_version = None, None

    if os_id is not None and os_version is not None:
        cfg.diag(
            "Matching os-release id {os_id!r} version {os_version!r}".format(
                os_id=os_id, os_version=os_version
            )
        )
        for var in vbuild.DETECT_ORDER:
            cfg.diag("- trying {name}".format(name=var.name))
            if var.detect.os_id == os_id and var.detect.os_version_regex.match(os_version):
                cfg.diag("  - found it!")
                return var

    cfg.diag("Trying non-os-release-based heuristics")
    for var in vbuild.DETECT_ORDER:
        cfg.diag("- trying {name}".format(name=var.name))
        try:
            with io.open(var.detect.filename, mode="r", encoding=SAFEENC) as osf:
                cfg.diag("  - {fname}".format(fname=var.detect.filename))
                for line in (line.rstrip("\r\n") for line in osf.readlines()):
                    if var.detect.regex.match(line):
                        cfg.diag("  - found it: {line}".format(line=line))
                        return var
        except (IOError, OSError) as err:
            if err.errno != errno.ENOENT:
                raise VariantDetectError(
                    "Could not read the {fname} file: {err}".format(
                        fname=var.detect.filename, err=err
                    )
                )
            cfg.diag("  - no {fname}".format(fname=var.detect.filename))

    raise VariantDetectError("Could not detect the current host's build variant")


def get_all_variants(cfg=_DEFAULT_CONFIG):
    # type: (Config) -> Dict[Text, Variant]
    """Return information about all the supported variants."""
    vbuild.build_variants(cfg)
    return dict(vbuild.VARIANTS)


def get_all_variants_in_order(cfg=_DEFAULT_CONFIG):
    # type: (Config) -> List[Variant]
    """Return information about all supported variants in detect order."""
    vbuild.build_variants(cfg)
    return list(vbuild.DETECT_ORDER)


def get_by_alias(alias, cfg=_DEFAULT_CONFIG):
    # type: (Text, Config) -> Variant
    """Return the variant with the specified name."""
    vbuild.build_variants(cfg)
    for var in vbuild.VARIANTS.values():
        if var.builder.alias == alias:
            return var
    raise VariantKeyError("No variant with alias {alias}".format(alias=alias))


def get_variant(name, cfg=_DEFAULT_CONFIG):
    # type: (Text, Config) -> Variant
    """Return the variant with the specified name."""
    vbuild.build_variants(cfg)
    try:
        return vbuild.VARIANTS[name]
    except KeyError:
        raise VariantKeyError("No variant named {name}".format(name=name))


def list_all_packages(var, patterns=None):
    # type: (Variant, Optional[Iterable[str]]) -> List[defs.OSPackage]
    """Parse the output of the "list installed packages" command."""
    cmd = list(var.commands.package.list_all)
    if patterns is not None:
        cmd.extend(patterns)

    res = []
    for line in subprocess.check_output(cmd, shell=False).decode("UTF-8").splitlines():
        fields = line.split("\t")
        if len(fields) != 4:
            raise VariantFileError(
                "Unexpected line in the '{cmd}' output: {line}".format(
                    cmd=" ".join(cmd), line=repr(line)
                )
            )
        # This may need updating at some point, but it'll work for now
        if not fields[3].startswith("ii"):
            continue

        res.append(
            defs.OSPackage(
                name=fields[0],
                version=fields[1],
                arch=fields[2],
                status="installed",
            )
        )

    return res


__all__ = (
    "Config",
    "Variant",
    "VariantError",
    "VERSION",
    "detect_variant",
    "get_all_variants",
    "get_all_variants_in_order",
    "get_by_alias",
    "get_variant",
    "list_all_packages",
    "update_namedtuple",
)
