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
"""
Support for different OS distributions and StorPool build variants.

NB: This should be the only file in the StorPool source that cannot
really depend on sp-python2 and sp-python2-modules being installed.

NB: This is a looong file. It has to be, since it needs to be
completely self-contained so that it may be copied over to
a remote host and executed there.
"""

# pylint: disable=too-many-lines

from __future__ import print_function

import argparse
import json
import os
import subprocess
import sys

from typing import Callable, List, Optional, Text, Tuple, TYPE_CHECKING  # noqa: H301

from . import defs
from . import variant
from . import vbuild


if TYPE_CHECKING:
    if sys.version_info[0] >= 3:
        # pylint: disable-next=protected-access,unsubscriptable-object
        SubPAction = argparse._SubParsersAction[argparse.ArgumentParser]
    else:
        # pylint: disable-next=protected-access
        SubPAction = argparse._SubParsersAction


CMD_LIST_BRIEF = [
    ("pkgfile", "install"),
]


def cmd_detect(cfg):
    # type: (defs.Config) -> None
    """Detect and output the build variant for the current host."""
    try:
        print(variant.detect_variant(cfg=cfg).name)
    except variant.VariantError as err:
        print(str(err), file=sys.stderr)
        sys.exit(1)


def copy_file(cfg, src, dstdir):
    # type: (defs.Config, Text, Text) -> None
    """Use `install(8)` to install a configuration file."""
    dst = os.path.join(dstdir, os.path.basename(src))
    mode = "0644"
    cfg.diag("{src} -> {dst} [{mode}]".format(src=src, dst=dst, mode=mode))
    try:
        subprocess.check_call(
            [
                "install",
                "-o",
                "root",
                "-g",
                "root",
                "-m",
                mode,
                "--",
                src,
                dst,
            ],
            shell=False,
        )
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(
            "Could not copy {src} over to {dst}: {err}".format(src=src, dst=dst, err=err)
        )


def repo_add_extension(cfg, name):
    # type: (defs.Config, Text) -> Text
    """Add the extension for the specified repository type."""
    parts = name.rsplit(".")
    if len(parts) != 2:
        raise variant.VariantFileError(
            "Unexpected repository file name without an extension: {name}".format(name=name)
        )
    return "{stem}{extension}.{ext}".format(
        stem=parts[0], extension=cfg.repotype.extension, ext=parts[1]
    )


def repo_add_deb(cfg, var, vardir):
    # type: (defs.Config, defs.Variant, Text) -> None
    """Install the StorPool Debian-like repo configuration."""
    assert isinstance(var.repo, defs.DebRepo)

    try:
        subprocess.check_call(var.commands.package.install + var.repo.req_packages, shell=False)
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(
            "Could not install the required packages {req}: {err}".format(
                req=" ".join(var.repo.req_packages), err=err
            )
        )

    copy_file(
        cfg,
        os.path.join(vardir, repo_add_extension(cfg, os.path.basename(var.repo.sources))),
        "/etc/apt/sources.list.d",
    )
    copy_file(
        cfg,
        os.path.join(vardir, os.path.basename(var.repo.keyring)),
        "/usr/share/keyrings",
    )

    try:
        subprocess.check_call(["apt-get", "update"], shell=False)
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError("Could not update the APT database: {err}".format(err=err))


def repo_add_yum(cfg, var, vardir):
    # type: (defs.Config, defs.Variant, Text) -> None
    """Install the StorPool RedHat/CentOS-like repo configuration."""
    assert isinstance(var.repo, defs.YumRepo)

    try:
        subprocess.check_call(
            [
                "yum",
                "--disablerepo=storpool-*'",
                "install",
                "-q",
                "-y",
                "ca-certificates",
            ],
            shell=False,
        )
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(
            "Could not install the required ca-certificates package: {err}".format(err=err)
        )

    copy_file(
        cfg,
        os.path.join(vardir, repo_add_extension(cfg, os.path.basename(var.repo.yumdef))),
        "/etc/yum.repos.d",
    )
    copy_file(
        cfg,
        os.path.join(vardir, os.path.basename(var.repo.keyring)),
        "/etc/pki/rpm-gpg",
    )

    if os.path.isfile("/usr/bin/rpmkeys"):
        try:
            subprocess.check_call(
                [
                    "rpmkeys",
                    "--import",
                    os.path.join("/etc/pki/rpm-gpg", os.path.basename(var.repo.keyring)),
                ],
                shell=False,
            )
        except subprocess.CalledProcessError as err:
            raise variant.VariantFileError(
                "Could not import the RPM PGP keys: {err}".format(err=err)
            )

    try:
        subprocess.check_call(
            [
                "yum",
                "--disablerepo=*",
                "--enablerepo=storpool-{name}".format(name=cfg.repotype.name),
                "clean",
                "metadata",
            ],
            shell=False,
        )
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(
            "Could not clean the Yum repository metadata: {err}".format(err=err)
        )


def repo_add(cfg):
    # type: (defs.Config) -> None
    """Install the StorPool repository configuration."""
    assert cfg.repodir is not None
    var = variant.detect_variant(cfg)
    vardir = os.path.join(cfg.repodir, var.name)
    if not os.path.isdir(vardir):
        raise defs.VariantConfigError("No {vdir} directory".format(vdir=vardir))

    if isinstance(var.repo, defs.DebRepo):
        repo_add_deb(cfg, var, vardir)
    elif isinstance(var.repo, defs.YumRepo):
        repo_add_yum(cfg, var, vardir)


def cmd_repo_add(cfg):
    # type: (defs.Config) -> None
    """Install the StorPool repository configuration, display errors."""
    try:
        repo_add(cfg)
    except variant.VariantError as err:
        print(str(err), file=sys.stderr)
        sys.exit(1)


def command_find(cfg, var):
    # type: (defs.Config, defs.Variant) -> List[Text]
    """Get a distribution-specific command from the variant definition."""
    assert cfg.command is not None

    current = var.commands
    for comp in cfg.command.split("."):
        if not isinstance(current, tuple):
            raise defs.VariantConfigError("Too many command components")

        fields = getattr(current, "_fields")  # type: List[str]
        if comp not in fields:
            raise defs.VariantConfigError(
                "Invalid command component '{comp}', should be one of {fields}".format(
                    comp=comp, fields=" ".join(fields)
                )
            )
        current = getattr(current, comp)

    if not isinstance(current, list):
        fields = getattr(current, "_fields")
        raise defs.VariantConfigError(
            "Incomplete command specification, should continue with one of {fields}".format(
                fields=" ".join(fields)
            )
        )

    return current


def command_run(cfg):
    # type: (defs.Config) -> None
    """Run a distribution-specific command."""
    assert cfg.args is not None

    cmd = command_find(cfg, variant.detect_variant(cfg=cfg)) + cfg.args
    cfg.diag("About to run `{cmd}`".format(cmd=" ".join(cmd)))
    if cfg.noop:
        # Ahhh... we won't have shlex.quote() on Python 2.6, will we?
        print(" ".join(cmd))
        return

    try:
        subprocess.check_call(cmd, shell=False)
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(
            "Could not run `{cmd}`: {err}".format(cmd=" ".join(cmd), err=err)
        )


def cmd_command_list(cfg):
    # type: (defs.Config) -> None
    """List the distribution-specific commands."""
    var = variant.detect_variant(cfg=cfg)

    # We only have two levels, right?
    for cat_name, category in (
        (name, getattr(var.commands, name)) for name in sorted(var.commands._fields)
    ):
        for cmd_name, command in (
            (name, getattr(category, name)) for name in sorted(category._fields)
        ):
            if (cat_name, cmd_name) in CMD_LIST_BRIEF:
                command = ["..."]
            print("{cat}.{name}: {cmd}".format(cat=cat_name, name=cmd_name, cmd=" ".join(command)))


def cmd_command_run(cfg):
    # type: (defs.Config) -> None
    """Run a distribution-specific command."""
    try:
        command_run(cfg)
    except variant.VariantError as err:
        print(str(err), file=sys.stderr)
        sys.exit(1)


def cmd_features(_cfg):
    # type: (defs.Config) -> None
    """Display the features supported by storpool_variant."""
    print(
        "Features: repo=0.2 variant={ver} format={f_major}.{f_minor}".format(
            ver=defs.VERSION, f_major=defs.FORMAT_VERSION[0], f_minor=defs.FORMAT_VERSION[1]
        )
    )


def cmd_show(cfg):
    # type: (defs.Config) -> None
    """Display information about a single build variant."""
    assert cfg.command is not None
    vbuild.build_variants(cfg)
    if cfg.command == "all":
        data = defs.jsonify(
            {
                "format": {
                    "version": {
                        "major": defs.FORMAT_VERSION[0],
                        "minor": defs.FORMAT_VERSION[1],
                    }
                },
                "version": defs.VERSION,
                "variants": vbuild.VARIANTS,
                "order": [var.name for var in vbuild.DETECT_ORDER],
            }
        )
    else:
        if cfg.command == "current":
            var = variant.detect_variant(cfg)  # type: Optional[defs.Variant]
        else:
            var = vbuild.VARIANTS.get(cfg.command)

        if var is None:
            sys.exit("Invalid build variant '{name}'".format(name=cfg.command))
        data = defs.jsonify(
            {
                "format": {
                    "version": {
                        "major": defs.FORMAT_VERSION[0],
                        "minor": defs.FORMAT_VERSION[1],
                    }
                },
                "version": defs.VERSION,
                "variant": var,
            }
        )
    print(json.dumps(data, sort_keys=True, indent=2))


def base_parser(prog):
    # type: (str) -> Tuple[argparse.ArgumentParser, SubPAction]
    """Build a parser with the options used by all the sp.variant tools."""
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="verbose operation; display diagnostic output",
    )

    return parser, parser.add_subparsers()


def parse_arguments():
    # type: () -> Tuple[defs.Config, Callable[[defs.Config], None]]
    """Parse the command-line arguments."""
    parser, subp = base_parser(prog="storpool_variant")

    p_cmd = subp.add_parser("command", help="Distribition-specific commands")
    subp_cmd = p_cmd.add_subparsers()

    p_subcmd = subp_cmd.add_parser("list", help="List the distribution-specific commands")
    p_subcmd.set_defaults(func=cmd_command_list)

    p_subcmd = subp_cmd.add_parser("run", help="Run a distribution-specific command")
    p_subcmd.add_argument(
        "-N",
        "--noop",
        action="store_true",
        help="display the command instead of executing it",
    )
    p_subcmd.add_argument("command", type=str, help="The identifier of the command to run")
    p_subcmd.add_argument("args", type=str, nargs="*", help="Arguments to pass to the command")
    p_subcmd.set_defaults(func=cmd_command_run)

    p_cmd = subp.add_parser("detect", help="Detect the build variant for the current host")
    p_cmd.set_defaults(func=cmd_detect)

    p_cmd = subp.add_parser("features", help="Display the features supported by storpool_variant")
    p_cmd.set_defaults(func=cmd_features)

    p_cmd = subp.add_parser("repo", help="StorPool repository-related commands")
    subp_cmd = p_cmd.add_subparsers()

    p_subcmd = subp_cmd.add_parser("add", help="Install the StorPool repository configuration")
    p_subcmd.add_argument(
        "-d",
        "--repodir",
        type=str,
        required=True,
        help="The path to the directory with the repository configuration",
    )
    p_subcmd.add_argument(
        "-t",
        "--repotype",
        type=str,
        default=defs.REPO_TYPES[0].name,
        choices=[item.name for item in defs.REPO_TYPES],
        help="The type of repository to add (default: contrib)",
    )
    p_subcmd.set_defaults(func=cmd_repo_add)

    p_cmd = subp.add_parser("show", help="Display information about a build variant")
    p_cmd.add_argument(
        "name",
        type=str,
        help=(
            "the name of the build variant to query, 'all' for all, or "
            "'current' for the one detected"
        ),
    )
    p_cmd.set_defaults(func=cmd_show)

    args = parser.parse_args()
    if getattr(args, "func", None) is None:
        sys.exit("No command specified")

    return (
        defs.Config(
            args=getattr(args, "args", None),
            command=getattr(args, "command", getattr(args, "name", None)),
            noop=bool(getattr(args, "noop", False)),
            repodir=getattr(args, "repodir", None),
            repotype=next(rtype for rtype in defs.REPO_TYPES if rtype.name == args.repotype)
            if hasattr(args, "repotype")
            else defs.REPO_TYPES[0],
            verbose=args.verbose,
        ),
        args.func,
    )


def main():
    # type: () -> None
    """Main routine: parse options, detect the variant."""
    cfg, func = parse_arguments()
    func(cfg)


if __name__ == "__main__":
    main()
