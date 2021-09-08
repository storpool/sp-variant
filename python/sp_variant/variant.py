"""Build variant definitions and commands."""

from .__main__ import (
    Config,  # noqa: H301
    Variant,
    VERSION,
    detect_variant,
    get_by_alias,
    get_variant,
    list_all_packages,
    update_namedtuple,
)

__all__ = (
    "Config",
    "Variant",
    "VERSION",
    "detect_variant",
    "get_by_alias",
    "get_variant",
    "list_all_packages",
    "update_namedtuple",
)
