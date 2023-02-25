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
"""Yet Another INI-style-file Parser."""

import io
import re

from typing import Dict, Optional, Tuple, Union

from . import defs


class VariantYAIError(defs.VariantError):
    """An error that occurred while parsing an INI-like file."""


_RE_YAIP_LINE = re.compile(
    r"""
    ^ (?:
        (?P<comment> \s* (?: \# .* )? )
        |
        (?:
            (?P<varname> [A-Za-z0-9_]+ )
            =
            (?P<full>
                (?P<oquot> ["'] )?
                (?P<quoted> .*? )
                (?P<cquot> ["'] )?
            )
        )
    ) $ """,
    re.X,
)


class YAIParser:
    """Yet another INI-like file parser, this time for /etc/os-release."""

    filename: str
    data: Dict[str, str]

    def __init__(self, filename: str) -> None:
        """Initialize a YAIParser object: store the filename."""
        self.filename = filename
        self.data = {}

    def parse_line(self, line: Union[str, bytes]) -> Optional[Tuple[str, str]]:
        """Parse a single var=value line."""
        if isinstance(line, bytes):
            try:
                line = line.decode("UTF-8")
            except UnicodeDecodeError as err:
                raise VariantYAIError(
                    f"Invalid {self.filename} line, not a valid UTF-8 string: {line!r}: {err}"
                ) from err
        assert isinstance(line, str)

        mline = _RE_YAIP_LINE.match(line)
        if not mline:
            raise VariantYAIError(f"Unexpected {self.filename} line: {line!r}")
        if mline.group("comment") is not None:
            return None

        varname, oquot, cquot, quoted, full = (
            mline.group("varname"),
            mline.group("oquot"),
            mline.group("cquot"),
            mline.group("quoted"),
            mline.group("full"),
        )

        if oquot == "'":
            if oquot in quoted:
                raise VariantYAIError(
                    (
                        f"Weird {self.filename} line, the quoted content "
                        f"contains the quote character: {line!r}"
                    )
                )
            if cquot != oquot:
                raise VariantYAIError(
                    f"Weird {self.filename} line, open/close quote mismatch: {line!r}"
                )

            return (varname, quoted)

        if oquot is None:
            quoted = full
        elif cquot != oquot:
            raise VariantYAIError(
                f"Weird {self.filename} line, open/close quote mismatch: {line!r}"
            )

        res = ""
        while quoted:
            try:
                idx = quoted.index("\\")
            except ValueError:
                res += quoted
                break

            if idx == len(quoted) - 1:
                raise VariantYAIError(
                    (
                        f"Weird {self.filename} line, backslash at "
                        f"the end of the quoted string: {line!r}"
                    )
                )
            res += quoted[:idx] + quoted[idx + 1]
            quoted = quoted[idx + 2 :]

        return (varname, res)

    def parse(self) -> Dict[str, str]:
        """Parse a file, store and return the result."""
        with io.open(self.filename, mode="r", encoding="UTF-8") as infile:
            contents = infile.read()
        data = {}
        for line in contents.splitlines():
            res = self.parse_line(line)
            if res is None:
                continue
            data[res[0]] = res[1]

        self.data = data
        return data

    def get(self, key: Union[str, bytes]) -> Optional[str]:
        """Get a value parsed from the configuration file."""
        if isinstance(key, bytes):
            key = key.decode("UTF-8")
        assert isinstance(key, str)
        return self.data.get(key)
