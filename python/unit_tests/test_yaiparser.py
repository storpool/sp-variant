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
"""Test the os-release parser class."""

import unittest

from typing import Tuple

import ddt  # type: ignore
import pytest

from sp_variant import defs
from sp_variant import yaiparser

from . import util


_LINES_BAD = [
    "NAME='",
    "NAME=\"foo'",
    "FOO BAR=baz",
    "FOO=bar\\",
    'FOO="meow\\"',
]

_LINES_COMMENTS = ["", "   \t  ", "  \t  # something", "#"]

_LINES_OK = [
    ("ID=centos", ("ID", "centos")),
    ("ID='centos'", ("ID", "centos")),
    (
        "NAME='something long \"and weird'",
        ("NAME", 'something long "and weird'),
    ),
    (
        'NAME="something long \'and \\\\weird\\"\\`"',
        (
            "NAME",
            "something long 'and \\weird\"`",
        ),
    ),
    (
        "NAME=unquoted\\\"and\\\\-escaped\\'",
        (
            "NAME",
            "unquoted\"and\\-escaped'",
        ),
    ),
]

_CFG_TEXT = """
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
"""

_CFG_EXPECTED = [
    ("ID", "debian"),
    ("VERSION_ID", "11"),
    ("VERSION", "11 (bullseye)"),
    ("FOO", None),
]


@ddt.ddt
class TestParseLine(unittest.TestCase):
    """Test various aspects of YAIParser.parse_line()."""

    def setUp(self):
        # type: (TestParseLine) -> None
        """Stash a YAIParser object."""
        self.yai = yaiparser.YAIParser("/dev/null")  # pylint: disable=W0212

    @ddt.data(*_LINES_COMMENTS)
    def test_parse_comments(self, line):
        # type: (TestParseLine, str) -> None
        """Parse empty lines and comments."""
        assert self.yai.parse_line(line) is None

    @ddt.data(*_LINES_BAD)
    def test_bad(self, line):
        # type: (TestParseLine, str) -> None
        """Make sure parse_line() raises exceptions on errors."""
        with pytest.raises(defs.VariantError):
            raise Exception(repr(self.yai.parse_line(line)))

    @ddt.data(*_LINES_OK)
    @ddt.unpack
    def test_parse_line_ok(self, line, res):
        # type: (TestParseLine, str, Tuple[str, str]) -> None
        """Make sure parse_line() works on valid text.

        So we silently assume that `==` works between str and unicode on
        Python 2.x... let's go with that for now.
        """
        assert self.yai.parse_line(line) == res


def test_parse():
    # type: () -> None
    """Test the functionality of _YAIParser.parse() and .get()."""
    with util.TemporaryDirectory() as tempd:
        cfile = tempd / "os-release"
        cfile.write_text(defs.TextType(_CFG_TEXT), encoding="UTF-8")

        yai = yaiparser.YAIParser(str(cfile))  # pylint: disable=W0212
        data = yai.parse()

        for name, value in _CFG_EXPECTED:
            res = data.get(name)
            assert res == value, repr((name, value, res))

            res = yai.get(name)
            assert res == value, repr((name, value, res))
