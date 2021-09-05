"""Utility functions for the sp_variant tests."""

import contextlib
import subprocess
import sys
import tempfile

from typing import Iterator, Optional, Text, Union  # noqa: H301


if sys.version_info[0] < 3:
    import pathlib2 as pathlib
else:
    import pathlib


@contextlib.contextmanager
def TemporaryDirectory(  # pylint: disable=invalid-name
    path=None,  # type: Optional[Union[pathlib.Path, Text, str]]
):  # type: (...) -> Iterator[pathlib.Path]
    """Create a temporary directory and eventually remove it."""
    temp = None
    try:
        temp = tempfile.mkdtemp(
            dir=Text(path) if isinstance(path, pathlib.Path) else path
        )
        yield pathlib.Path(temp)
    finally:
        if temp is not None:
            subprocess.call(["rm", "-rf", "--", temp])


__all__ = ["pathlib", "TemporaryDirectory"]
