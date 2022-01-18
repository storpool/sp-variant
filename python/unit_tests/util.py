# Copyright (c) 2021  StorPool <support@storpool.com>
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
        temp = tempfile.mkdtemp(dir=Text(path) if isinstance(path, pathlib.Path) else path)
        yield pathlib.Path(temp)
    finally:
        if temp is not None:
            subprocess.call(["rm", "-rf", "--", temp])


__all__ = ["pathlib", "TemporaryDirectory"]
