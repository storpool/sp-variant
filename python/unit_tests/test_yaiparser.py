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
"""Test the os-release parser class."""

from __future__ import annotations

import pathlib
import tempfile

from typing import Final

import pytest

from sp_variant import defs
from sp_variant import yaiparser


_LINES_BAD: Final = [
    "NAME='",
    "NAME=\"foo'",
    "FOO BAR=baz",
    "FOO=bar\\",
    'FOO="meow\\"',
]

_LINES_COMMENTS: Final = ["", "   \t  ", "  \t  # something", "#"]

_LINES_OK: Final = [
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

_CFG_TEXT: Final = """
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

_CFG_EXPECTED: Final = [
    ("ID", "debian"),
    ("VERSION_ID", "11"),
    ("VERSION", "11 (bullseye)"),
    ("FOO", None),
]


@pytest.mark.parametrize("line", _LINES_COMMENTS)
def test_parse_comments(line: str) -> None:
    """Parse empty lines and comments."""
    yai: Final = yaiparser.YAIParser("/dev/null")
    assert yai.parse_line(line) is None


@pytest.mark.parametrize("line", _LINES_BAD)
def test_bad(line: str) -> None:
    """Make sure parse_line() raises exceptions on errors."""
    yai: Final = yaiparser.YAIParser("/dev/null")
    with pytest.raises(defs.VariantError):
        assert yai.parse_line(line) == ("not reached", "we hope")


@pytest.mark.parametrize("line,res", _LINES_OK)
def test_parse_line_ok(line: str, res: tuple[str, str]) -> None:
    """Make sure parse_line() works on valid text.

    So we silently assume that `==` works between str and unicode on
    Python 2.x... let's go with that for now.
    """
    yai: Final = yaiparser.YAIParser("/dev/null")
    assert yai.parse_line(line) == res


def test_parse() -> None:
    """Test the functionality of _YAIParser.parse() and .get()."""
    with tempfile.TemporaryDirectory() as tempd_obj:
        tempd: Final = pathlib.Path(tempd_obj)
        cfile: Final = tempd / "os-release"
        cfile.write_text(_CFG_TEXT, encoding="UTF-8")

        yai: Final = yaiparser.YAIParser(str(cfile))  # pylint: disable=W0212
        data: Final = yai.parse()

        for name, value in _CFG_EXPECTED:
            res_raw = data.get(name)
            assert res_raw == value, repr((name, value, res_raw))

            res_ret = yai.get(name)
            assert res_ret == value, repr((name, value, res_ret))
