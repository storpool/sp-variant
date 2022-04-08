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
"""Yet Another INI-style-file Parser."""

import io
import re

from typing import Dict, Optional, Text, Tuple, Union  # noqa: H301

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


class YAIParser(object):
    """Yet another INI-like file parser, this time for /etc/os-release."""

    def __init__(self, filename):
        # type: (YAIParser, Text) -> None
        """Initialize a YAIParser object: store the filename."""
        self.filename = filename
        self.data = {}  # type: Dict[defs.TextType, defs.TextType]

    def parse_line(
        self,  # type: YAIParser
        line,  # type: Union[defs.TextType, defs.BytesType]
    ):  # type: (...) -> Optional[Tuple[defs.TextType, defs.TextType]]
        """Parse a single var=value line."""
        if isinstance(line, defs.BytesType):
            try:
                line = line.decode("UTF-8")
            except UnicodeDecodeError as err:
                raise VariantYAIError(
                    "Invalid {fname} line, not a valid UTF-8 string: {line!r}: {err}".format(
                        fname=self.filename, line=line, err=err
                    )
                )
        assert isinstance(line, defs.TextType)

        mline = _RE_YAIP_LINE.match(line)
        if not mline:
            raise VariantYAIError(
                "Unexpected {fname} line: {line!r}".format(fname=self.filename, line=line)
            )
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
                        "Weird {fname} line, the quoted content "
                        "contains the quote character: {line!r}"
                    ).format(fname=self.filename, line=line)
                )
            if cquot != oquot:
                raise VariantYAIError(
                    "Weird {fname} line, open/close quote mismatch: {line!r}".format(
                        fname=self.filename, line=line
                    )
                )

            return (varname, quoted)

        if oquot is None:
            quoted = full
        elif cquot != oquot:
            raise VariantYAIError(
                "Weird {fname} line, open/close quote mismatch: {line!r}".format(
                    fname=self.filename, line=line
                )
            )

        res = defs.TextType("")
        while quoted:
            try:
                idx = quoted.index("\\")
            except ValueError:
                res += quoted
                break

            if idx == len(quoted) - 1:
                raise VariantYAIError(
                    (
                        "Weird {fname} line, backslash at the end of the quoted string: {line!r}"
                    ).format(fname=self.filename, line=line)
                )
            res += quoted[:idx] + quoted[idx + 1]
            quoted = quoted[idx + 2 :]

        return (varname, res)

    def parse(self):
        # type: (YAIParser) -> Dict[defs.TextType, defs.TextType]
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

    def get(self, key):
        # type: (YAIParser, Union[defs.TextType, defs.BytesType]) -> Optional[defs.TextType]
        """Get a value parsed from the configuration file."""
        if isinstance(key, defs.BytesType):
            key = key.decode("UTF-8")
        assert isinstance(key, defs.TextType)
        return self.data.get(key)
