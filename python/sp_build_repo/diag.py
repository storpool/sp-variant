# SPDX-FileCopyrightText: 2023, 2024  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause
"""Provide a class that outputs diagnostic messages if configured to."""

from __future__ import annotations

import functools
import logging
import sys
import typing


if typing.TYPE_CHECKING:
    from typing import Final


@functools.lru_cache
def _build_logger(name: str | None = None) -> logging.Logger:
    """Set the logger up, adding a standard error stream handler."""
    logger: Final = logging.getLogger(name)

    handler: Final = logging.StreamHandler(stream=sys.stderr)
    # The log level is configured at the top-level logger
    handler.setLevel(logging.DEBUG)

    logger.addHandler(handler)
    return logger


def setup_logger(
    name: str | None = None,
    *,
    verbose: bool,
    propagate: bool = False,
) -> logging.Logger:
    """Set up a logger that sends messages to the standard error stream.

    If the `verbose` parameter is false, debug-level messages are ignored.

    Note that the logger will NOT propagate messages to parent loggers unless
    the `propagate` parameter is true.
    """
    logger = _build_logger(name)
    logger.propagate = propagate
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    return logger
