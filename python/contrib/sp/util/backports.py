"""Various Python modules varying between Python versions."""

import sys


if sys.version_info[0] < 3:
    import pathlib2 as pathlib
else:
    import pathlib


__all__ = ["pathlib"]
