# SPDX-FileCopyrightText: 2021 - 2024  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause
"""Substitute variant data using Jinja2 templates."""

from __future__ import annotations

import dataclasses
import functools
import json
import logging
import pathlib
import typing

import click
import jinja2
import trivver

from sp_build_repo import diag
from sp_variant import defs
from sp_variant import variant


if typing.TYPE_CHECKING:
    from typing import Final


@dataclasses.dataclass(frozen=True)
class Config:
    """Runtime configuration for the variant substitution tool."""

    output: pathlib.Path
    output_mode: int
    template: pathlib.Path
    verbose: bool


def regex_un_x(value: str) -> str:
    """Un-re.X a regular expression... somewhat."""
    return (
        value.replace(" ", "")
        .replace("\t", "")
        .replace("\n", "")
        .replace("\\s", "[[:space:]]")
        .replace("(?:", "(")
    )


def rust_bool(value: bool) -> str:  # noqa: FBT001  # this is a conversion routine
    """Format a boolean value as a Rust bool one."""
    return "true" if value else "false"


def dictvsort(data: dict[str, variant.Variant]) -> list[tuple[str, variant.Variant]]:
    """Sort a dict of variants by name, preserving some numerical order."""

    def compare(left: tuple[str, variant.Variant], right: tuple[str, variant.Variant]) -> int:
        """Compare two variants by name."""
        res: Final = trivver.compare(left[0], right[0])
        assert res  # noqa: S101  # just to be absolutely sure
        return res

    return sorted(data.items(), key=functools.cmp_to_key(compare))


def vsort(names: list[str]) -> list[str]:
    """Sort a list of variant names, preserving some numerical order."""
    return sorted(names, key=trivver.key_compare)


def build_json(var: variant.Variant) -> str:
    """Represent the variant data as a JSON string."""
    return json.dumps(defs.jsonify(var), sort_keys=True, indent=2)


def substitute(cfg: Config) -> None:
    """Perform the substitutions."""
    logging.debug("Building the variants data")
    variants: Final = variant.get_all_variants_in_order()

    logging.debug("Preparing the Jinja substitution environment")
    jenv: Final = jinja2.Environment(
        autoescape=False,  # noqa: S701
        loader=jinja2.FileSystemLoader(cfg.template.parent),
        undefined=jinja2.StrictUndefined,
    )
    jenv.filters["dictvsort"] = dictvsort
    jenv.filters["regexunx"] = regex_un_x
    jenv.filters["rust_bool"] = rust_bool
    jenv.filters["vsort"] = vsort
    jvars: Final = {
        "format_version": defs.FORMAT_VERSION,
        "order": [var.name for var in variants],
        "repotypes": {repo.name: repo for repo in defs.REPO_TYPES},
        "variants": {var.name: var for var in variants},
        "variants_json": {var.name: build_json(var) for var in variants},
        "version": defs.VERSION,
    }

    logging.debug("Rendering the template")
    result: Final = jenv.get_template(cfg.template.name).render(**jvars)
    logging.debug("Got %(count)d characters", {"count": len(result)})

    logging.debug("Generating the %(filename)s output file", {"filename": cfg.output})
    cfg.output.write_text(result, encoding="UTF-8")
    cfg.output.chmod(cfg.output_mode)

    logging.debug(
        "Rendered %(template)s into %(filename)s",
        {"template": cfg.template, "filename": cfg.output},
    )


class OctalInteger(click.ParamType):
    """Convert a string value to an integer using base 8."""

    name = "octal"

    def convert(
        self,
        value: str | int,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> int:
        """Convert a string to an integer using base 8."""
        if isinstance(value, int):
            return value

        try:
            return int(value, 8)
        except ValueError as err:
            self.fail(f"{value!r} is not a valid integer: {err}", param, ctx)


OCTAL_INTEGER: Final = OctalInteger()


@click.command(name="subst")
@click.option(
    "-m",
    "--mode",
    type=OCTAL_INTEGER,
    default=0o644,
    help="the octal permissions mode of the output file",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(
        dir_okay=False,
        file_okay=True,
        writable=True,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    required=True,
    help="the output file to generate",
)
@click.option(
    "-t",
    "--template",
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        readable=True,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    required=True,
    help="the template to render",
)
@click.option(
    "-v",
    "--verbose",
    type=bool,
    is_flag=True,
    help="verbose operation; display diagnostic messages",
)
def main(*, mode: int, output: pathlib.Path, template: pathlib.Path, verbose: bool) -> None:
    """Parse command-line arguments, substitute data."""
    diag.setup_logger(verbose=verbose)
    cfg: Final = Config(
        output=output,
        output_mode=mode,
        template=template,
        verbose=verbose,
    )
    substitute(cfg)


if __name__ == "__main__":
    main()
