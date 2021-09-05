"""Routines for creating temporary files and directories."""

import contextlib
import subprocess
import tempfile

from typing import Iterator, Optional, Text, Union

from sp.util.backports import pathlib


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
