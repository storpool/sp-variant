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
"""Build the "add StorPool repository" archive."""

import dataclasses
import datetime
import pathlib
import shutil
import subprocess
import sys

from typing import Callable, Dict, Optional, Text, Tuple  # noqa: H301

import cfg_diag
import jinja2

from sp_variant import __main__ as vmain
from sp_variant import defs
from sp_variant import variant
from sp_variant import vbuild


VERSION = "0.1.1"


@dataclasses.dataclass(frozen=True)
class Config(cfg_diag.ConfigDiag):
    """Configuration for the repository setup."""

    datadir: pathlib.Path
    destdir: pathlib.Path
    no_date: bool
    rustbin: Optional[pathlib.Path]


class Singles:
    """Keep some singleton objects in a controlled way."""

    _jinja2_env: Dict[Text, jinja2.Environment] = {}
    _jinja2_loaders: Dict[Text, jinja2.BaseLoader] = {}

    @classmethod
    def jinja2_env(cls, path: pathlib.Path) -> jinja2.Environment:
        """Instantiate a Jinja2 environment if necessary."""
        abspath = Text(path.absolute())
        if abspath in cls._jinja2_env:
            return cls._jinja2_env[abspath]

        env = jinja2.Environment(autoescape=False, loader=cls.jinja2_loader(path))
        cls._jinja2_env[abspath] = env
        return env

    @classmethod
    def jinja2_loader(cls, path: pathlib.Path) -> jinja2.BaseLoader:
        """Instantiate a Jinja2 environment if necessary."""
        abspath = Text(path.absolute())
        if abspath in cls._jinja2_loaders:
            return cls._jinja2_loaders[abspath]

        loader = jinja2.FileSystemLoader(abspath)
        cls._jinja2_loaders[abspath] = loader
        return loader


def ensure_none(cfg: Config, path: pathlib.Path) -> None:
    """Remove a file, directory, or other filesystem object altogether."""
    if not path.exists():
        return
    cfg.diag("Removing the existing {path}".format(path=path))
    try:
        subprocess.check_call(["rm", "-rf", "--", path])
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError("Could not remove {path}: {err}".format(path=path, err=err))


def copy_file(
    cfg: Config,
    src: pathlib.Path,
    dstdir: pathlib.Path,
    dstname: Optional[Text] = None,
    executable: bool = False,
) -> None:
    """Copy a file with the appropriate access permissions."""
    if dstname is None:
        dst = dstdir / src.name
    else:
        dst = dstdir / dstname
    ensure_none(cfg, dst)
    try:
        shutil.copy2(src, dst)
        dst.chmod(0o755 if executable else 0o644)
    except (OSError, subprocess.CalledProcessError) as err:
        raise variant.VariantFileError(
            "Could not copy {src} to {dst}: {err}".format(src=src, dst=dst, err=err)
        )


def subst_debian_sources(
    cfg: Config,
    var: variant.Variant,
    src: pathlib.Path,
    dstdir: pathlib.Path,
    rtype: defs.RepoType,
) -> None:
    """Substitute the placeholder vars in a Debian sources list file."""
    assert isinstance(var.repo, defs.DebRepo)
    dst = dstdir / (src.stem + rtype.extension + src.suffix)
    cfg.diag(
        "{src} -> {dst} [vendor {vendor}, codename {codename}]".format(
            src=src,
            dst=dst,
            vendor=var.repo.vendor,
            codename=var.repo.codename,
        )
    )

    try:
        result = (
            Singles.jinja2_env(src.parent)
            .get_template(src.name)
            .render(
                url=rtype.url,
                name=rtype.name,
                vendor=var.repo.vendor,
                codename=var.repo.codename,
            )
        )
    except jinja2.TemplateError as err:
        raise variant.VariantFileError(
            "Could not render the {src} template: {err}".format(src=src, err=err)
        )

    try:
        dst.write_text(result + "\n", encoding="UTF-8")
    except (IOError, OSError) as err:
        raise variant.VariantFileError("Could not write out {dst}: {err}".format(dst=dst, err=err))


def subst_yum_repo(
    cfg: Config,
    var: variant.Variant,
    src: pathlib.Path,
    dstdir: pathlib.Path,
    rtype: defs.RepoType,
) -> None:
    """Substitute the placeholder vars in a Debian sources list file."""
    assert isinstance(var.repo, defs.YumRepo)
    dst = dstdir / (src.stem + rtype.extension + src.suffix)
    cfg.diag(
        "{src} -> {dst} []".format(
            src=src,
            dst=dst,
        )
    )

    try:
        result = (
            Singles.jinja2_env(src.parent)
            .get_template(src.name)
            .render(
                url=rtype.url,
                name=rtype.name,
            )
        )
    except jinja2.TemplateError as err:
        raise variant.VariantFileError(
            "Could not render the {src} template: {err}".format(src=src, err=err)
        )

    try:
        dst.write_text(result + "\n", encoding="UTF-8")
    except (IOError, OSError) as err:
        raise variant.VariantFileError("Could not write out {dst}: {err}".format(dst=dst, err=err))


def build_repo(cfg: Config) -> pathlib.Path:
    """Build the StorPool repository archive."""
    distname = "add-storpool-repo"
    if not cfg.no_date:
        distname = "{name}-{date}".format(
            name=distname, date=datetime.date.today().strftime("%Y%m%d")
        )
    distdir = cfg.destdir / distname
    ensure_none(cfg, distdir)
    distdir.mkdir()

    if cfg.rustbin is not None:
        copy_file(
            cfg,
            cfg.rustbin,
            distdir,
            dstname="storpool_variant",
            executable=True,
        )
    else:
        mainfile = pathlib.Path(__file__).absolute().with_name("__main__.py")
        copy_file(cfg, mainfile, distdir, dstname="storpool_variant", executable=True)

    copy_file(
        cfg,
        cfg.datadir / "common/scripts/storpool_variant.sh",
        distdir,
        executable=True,
    )
    copy_file(
        cfg,
        cfg.datadir / "common/scripts/add-storpool-repo.sh",
        distdir,
        executable=True,
    )

    vbuild.build_variants(variant.Config(verbose=cfg.verbose))
    for var in vbuild.VARIANTS.values():
        vardir = distdir / var.name
        vardir.mkdir()

        if isinstance(var.repo, defs.DebRepo):
            for rtype in defs.REPO_TYPES:
                subst_debian_sources(cfg, var, cfg.datadir / var.repo.sources, vardir, rtype)
            copy_file(
                cfg,
                cfg.datadir / var.repo.keyring,
                vardir,
            )
        elif isinstance(var.repo, defs.YumRepo):
            for rtype in defs.REPO_TYPES:
                subst_yum_repo(cfg, var, cfg.datadir / var.repo.yumdef, vardir, rtype)
            copy_file(
                cfg,
                cfg.datadir / var.repo.keyring,
                vardir,
            )
        else:
            raise NotImplementedError(
                "No idea how to handle {tname} for {var}".format(
                    tname=type(var.repo).__name__, var=var.name
                )
            )

    distfile = (cfg.destdir / distname).with_suffix(".tar.gz")
    ensure_none(cfg, distfile)
    cfg.diag("Creating {distfile}".format(distfile=distfile))
    try:
        subprocess.check_call(
            ["tar", "-caf", distfile, "-C", cfg.destdir, distname],
            shell=False,
        )
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(
            "Could not package {distdir} up into {distfile}: {err}".format(
                distdir=distdir, distfile=distfile, err=err
            )
        )
    return distfile


def cmd_build(cfg: Config) -> None:
    """Build the StorPool repository archive and output its name."""
    try:
        print(build_repo(cfg=cfg))
    except variant.VariantError as err:
        print(str(err), file=sys.stderr)
        sys.exit(1)


def parse_arguments() -> Tuple[Config, Callable[[Config], None]]:
    """Parse the command-line arguments."""
    parser, subp = vmain.base_parser(prog="sp_build_repo")

    p_build = subp.add_parser("build", help="Detect the build variant for a remote host")
    p_build.add_argument(
        "-d",
        "--datadir",
        type=pathlib.Path,
        required=True,
        help="The directory to place the repo file in",
    )
    p_build.add_argument(
        "-D",
        "--destdir",
        type=pathlib.Path,
        required=True,
        help="The directory to place the repo file in",
    )
    p_build.add_argument(
        "-r",
        "--rust-bin",
        type=pathlib.Path,
        required=True,
        help="The Rust storpool_variant executable to use",
    )
    p_build.add_argument(
        "--no-date",
        action="store_true",
        default=False,
        help="Do not include the current date in the directory name",
    )
    p_build.set_defaults(func=cmd_build)

    args = parser.parse_args()
    return (
        Config(
            datadir=args.datadir,
            destdir=args.destdir,
            no_date=args.no_date,
            rustbin=args.rust_bin,
            verbose=args.verbose,
        ),
        args.func,
    )


def main() -> None:
    """Main routine: parse options, detect the variant."""
    cfg, func = parse_arguments()
    func(cfg)


if __name__ == "__main__":
    main()
