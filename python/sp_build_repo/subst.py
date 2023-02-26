# Copyright (c) 2021, 2022  StorPool <support@storpool.com>
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
"""Substitute variant data using Jinja2 templates."""

from __future__ import annotations

import argparse
import dataclasses
import functools
import json
import pathlib

from typing import Final

import cfg_diag
import jinja2
import trivver

from sp_variant import defs
from sp_variant import variant


@dataclasses.dataclass(frozen=True)
class Config(cfg_diag.Config):
    """Runtime configuration for the variant substitution tool."""

    output: pathlib.Path
    output_mode: int
    template: pathlib.Path


def parse_args() -> Config:
    """Parse the command-line arguments."""
    parser: Final = argparse.ArgumentParser(prog="sp_var_subst")
    parser.add_argument(
        "-m",
        "--mode",
        type=lambda value: int(value, 8),
        help="the octal permissions mode of the output file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        required=True,
        help="the output file to generate",
    )
    parser.add_argument(
        "-t",
        "--template",
        type=pathlib.Path,
        required=True,
        help="the template to render",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="verbose operation; display diagnostic messages",
    )

    args: Final = parser.parse_args()

    return Config(
        output=args.output,
        output_mode=args.mode,
        template=args.template,
        verbose=args.verbose,
    )


def regex_un_x(value: str) -> str:
    """Un-re.X a regular expression... somewhat."""
    return (
        value.replace(" ", "")
        .replace("\t", "")
        .replace("\n", "")
        .replace("\\s", "[[:space:]]")
        .replace("(?:", "(")
    )


def dictvsort(data: dict[str, variant.Variant]) -> list[tuple[str, variant.Variant]]:
    """Sort a dict of variants by name, preserving some numerical order."""

    def compare(left: tuple[str, variant.Variant], right: tuple[str, variant.Variant]) -> int:
        """Compare two variants by name."""
        res: Final = trivver.compare(left[0], right[0])
        assert res
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
    cfg.diag_("Building the variants data")
    variants: Final = variant.get_all_variants_in_order()

    cfg.diag_("Preparing the Jinja substitution environment")
    jenv: Final = jinja2.Environment(
        autoescape=False,
        loader=jinja2.FileSystemLoader(cfg.template.parent),
        undefined=jinja2.StrictUndefined,
    )
    jenv.filters["dictvsort"] = dictvsort
    jenv.filters["regexunx"] = regex_un_x
    jenv.filters["vsort"] = vsort
    jvars: Final = {
        "format_version": defs.FORMAT_VERSION,
        "order": [var.name for var in variants],
        "repotypes": {repo.name: repo for repo in defs.REPO_TYPES},
        "variants": {var.name: var for var in variants},
        "variants_json": {var.name: build_json(var) for var in variants},
        "version": defs.VERSION,
    }

    cfg.diag_("Rendering the template")
    result: Final = jenv.get_template(cfg.template.name).render(**jvars)
    cfg.diag(lambda: f"Got {len(result)} characters")

    cfg.diag(lambda: f"Generating the {cfg.output} output file")
    cfg.output.write_text(result, encoding="UTF-8")
    cfg.output.chmod(cfg.output_mode)

    cfg.diag(lambda: f"Rendered {cfg.template} into {cfg.output}")


def main() -> None:
    """Parse command-line arguments, substitute data."""
    cfg: Final = parse_args()
    substitute(cfg)


if __name__ == "__main__":
    main()
