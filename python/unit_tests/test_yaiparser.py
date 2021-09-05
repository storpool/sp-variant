"""Test the os-release parser class."""

import unittest

from typing import Tuple

import ddt  # type: ignore
import pytest

from sp_variant import __main__ as spvar

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
    """Test various aspects of _YAIParser.parse_line()."""

    def setUp(self):
        # type: (TestParseLine) -> None
        """Stash a _YAIParser object."""
        self.yai = spvar._YAIParser("/dev/null")  # pylint: disable=W0212

    @ddt.data(*_LINES_COMMENTS)
    def test_parse_comments(self, line):
        # type: (TestParseLine, str) -> None
        """Parse empty lines and comments."""
        assert self.yai.parse_line(line) is None

    @ddt.data(*_LINES_BAD)
    def test_bad(self, line):
        # type: (TestParseLine, str) -> None
        """Make sure parse_line() raises exceptions on errors."""
        with pytest.raises(spvar.VariantError):
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
        cfile.write_text(spvar.TextType(_CFG_TEXT), encoding="UTF-8")

        yai = spvar._YAIParser(str(cfile))  # pylint: disable=W0212
        data = yai.parse()

        for name, value in _CFG_EXPECTED:
            res = data.get(name)
            assert res == value, repr((name, value, res))

            res = yai.get(name)
            assert res == value, repr((name, value, res))
