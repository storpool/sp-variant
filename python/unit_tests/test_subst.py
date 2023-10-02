# SPDX-FileCopyrightText: 2021 - 2023  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause
"""Test the variant data template rendering tool."""

import pathlib
import tempfile
import typing

from sp_build_repo import diag
from sp_build_repo import subst


if typing.TYPE_CHECKING:
    from typing import Final


def test_subst() -> None:
    """Test the substitution tool."""
    with tempfile.TemporaryDirectory() as tempd_obj:
        tempd: Final = pathlib.Path(tempd_obj)
        diag.setup_logger(verbose=True)
        cfg: Final = subst.Config(
            output=tempd / "data.txt",
            output_mode=0o612,
            template=tempd / "template.j2",
            verbose=True,
        )
        cfg.template.write_text(
            """
Let's generate some data!

{% for name in order %}
- variant: {{ name }}
{% endfor %}

Let's examine some variants:

{% for name, var in variants|dictvsort %}
Variant: {{ var.name }} alias: {{ var.builder.alias }} family: {{ var.family }} update: {{ var.commands.package.update_db }}
{% endfor %}
""",  # noqa: E501
            encoding="UTF-8",
        )

        subst.substitute(cfg)

        assert cfg.output.is_file()
        assert (cfg.output.stat().st_mode & 0o7777) == 0o612
        lines: Final = cfg.output.read_text(encoding="UTF-8").splitlines()
        assert "- variant: ALMA8" in lines
        assert "- variant: ORACLE7" in lines

        c7_lines: Final = [line for line in lines if line.startswith("Variant: CENTOS7 ")]
        assert len(c7_lines) == 1
        assert c7_lines[0].startswith("Variant: CENTOS7 alias: centos7 family: redhat update: ")


def test_subst_re() -> None:
    """Test the substitution tool."""
    with tempfile.TemporaryDirectory() as tempd_obj:
        tempd: Final = pathlib.Path(tempd_obj)
        diag.setup_logger(verbose=True)
        cfg: Final = subst.Config(
            output=tempd / "data.txt",
            output_mode=0o747,
            template=tempd / "template.j2",
            verbose=True,
        )
        cfg.template.write_text(
            """{% for var in variants.values() %}
{{ var.detect.os_version_regex.pattern|regexunx }}
{{ var.detect.regex.pattern|regexunx }}
{% endfor %}
""",
            encoding="UTF-8",
        )

        subst.substitute(cfg)

        assert cfg.output.is_file()
        assert (cfg.output.stat().st_mode & 0o7777) == 0o747
        lines: Final = cfg.output.read_text(encoding="UTF-8").splitlines()
        assert lines

        for line in lines:
            assert " " not in line
            assert "\t" not in line
            assert "(?:" not in line
