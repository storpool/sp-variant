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
"""Test the variant data template rendering tool."""

from sp_build_repo import subst

from unit_tests import util
from unit_tests.util import pathlib


def test_subst():
    # type: () -> None
    """Test the substitution tool."""
    with util.TemporaryDirectory() as tempd_obj:
        tempd = pathlib.Path(tempd_obj)
        cfg = subst.Config(
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
""",  # noqa: E501  pylint: disable=line-too-long
            encoding="UTF-8",
        )

        subst.substitute(cfg)

        assert cfg.output.is_file()
        assert (cfg.output.stat().st_mode & 0o7777) == 0o612
        lines = cfg.output.read_text(encoding="UTF-8").splitlines()
        assert "- variant: ALMA8" in lines
        assert "- variant: ORACLE7" in lines

        c7_lines = [line for line in lines if line.startswith("Variant: CENTOS7 ")]
        assert len(c7_lines) == 1
        assert c7_lines[0].startswith("Variant: CENTOS7 alias: centos7 family: redhat update: ")


def test_subst_re():
    # type: () -> None
    """Test the substitution tool."""
    with util.TemporaryDirectory() as tempd_obj:
        tempd = pathlib.Path(tempd_obj)
        cfg = subst.Config(
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
        lines = cfg.output.read_text(encoding="UTF-8").splitlines()
        assert lines

        for line in lines:
            assert " " not in line
            assert "\t" not in line
            assert "(?:" not in line
