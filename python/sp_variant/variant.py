"""Build variant definitions and commands."""

from .__main__ import (
    Config,  # noqa: H301
    Variant,
    VariantError,
    VERSION,
    detect_variant,
    get_all_variants,
    get_all_variants_in_order,
    get_by_alias,
    get_variant,
    list_all_packages,
    update_namedtuple,
)

__all__ = (
    "Config",
    "Variant",
    "VariantError",
    "VERSION",
    "detect_variant",
    "get_all_variants",
    "get_all_variants_in_order",
    "get_by_alias",
    "get_variant",
    "list_all_packages",
    "update_namedtuple",
)
