"""Substitute variant data using Jinja2 templates."""

import argparse
import dataclasses
import json
import pathlib

import cfg_diag
import jinja2

from sp_variant import __main__ as variant


@dataclasses.dataclass(frozen=True)
class Config(cfg_diag.ConfigDiag):
    """Runtime configuration for the variant substitution tool."""

    output: pathlib.Path
    output_mode: int
    template: pathlib.Path


def parse_args() -> Config:
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(prog="sp_var_subst")
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

    args = parser.parse_args()

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


def build_json(var: variant.Variant) -> str:
    """Represent the variant data as a JSON string."""
    return json.dumps(variant.jsonify(var), sort_keys=True, indent=2)


def substitute(cfg: Config) -> None:
    """Perform the substitutions."""
    cfg.diag("Building the variants data")
    variants = variant.get_all_variants_in_order()

    cfg.diag("Preparing the Jinja substitution environment")
    jenv = jinja2.Environment(
        autoescape=False,
        loader=jinja2.FileSystemLoader(cfg.template.parent),
        undefined=jinja2.StrictUndefined,
    )
    jenv.filters["regexunx"] = regex_un_x
    jvars = {
        "format_version": variant.FORMAT_VERSION,
        "order": [var.name for var in variants],
        "repotypes": {repo.name: repo for repo in variant.REPO_TYPES},
        "variants": {var.name: var for var in variants},
        "variants_json": {var.name: build_json(var) for var in variants},
        "version": variant.VERSION,
    }

    cfg.diag("Rendering the template")
    result = jenv.get_template(cfg.template.name).render(**jvars)
    cfg.diag(f"Got {len(result)} characters")

    cfg.diag(f"Generating the {cfg.output} output file")
    cfg.output.write_text(result, encoding="UTF-8")
    cfg.output.chmod(cfg.output_mode)

    cfg.diag(f"Rendered {cfg.template} into {cfg.output}")


def main() -> None:
    """Parse command-line arguments, substitute data."""
    cfg = parse_args()
    substitute(cfg)


if __name__ == "__main__":
    main()
