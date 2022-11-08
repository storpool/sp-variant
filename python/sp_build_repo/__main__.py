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

from typing import Dict, Optional

import cfg_diag
import click
import jinja2
import tomli
import typedload

from sp_variant import defs
from sp_variant import variant
from sp_variant import vbuild


@dataclasses.dataclass
class ConfigHolder:
    """Pass the context to the command-line subcommand handler."""

    verbose: bool = False


VERSION = "1.0.0"


OVERRIDES_SCHEMAS = {
    (0, 1): {
        "?repo": {
            "*": {
                "?slug": str,
                "?url": str,
                "?vendor": str,
                "?codename": str,
            }
        }
    }
}


@dataclasses.dataclass(frozen=True)
class DataFormatVersion:
    """The version of the data format specification."""

    major: int
    minor: int


@dataclasses.dataclass(frozen=True)
class DataFormat:
    """The format metadata, currently only the version."""

    version: DataFormatVersion


@dataclasses.dataclass(frozen=True)
class OverrideRepo:
    """Override a repository's URL, URL slug, or other attributes."""

    url: Optional[str] = None
    slug: Optional[str] = None
    vendor: Optional[str] = None
    codename: Optional[str] = None


@dataclasses.dataclass(frozen=True)
class Overrides:
    """Overrides for some settings, e.g. repo URLs."""

    repo: Dict[str, OverrideRepo]


@dataclasses.dataclass(frozen=True)
class Config(cfg_diag.Config):
    """Configuration for the repository setup."""

    datadir: pathlib.Path
    destdir: pathlib.Path
    no_date: bool
    overrides: Overrides
    runtime: pathlib.Path


class Singles:
    """Keep some singleton objects in a controlled way."""

    _jinja2_env: Dict[str, jinja2.Environment] = {}
    _jinja2_loaders: Dict[str, jinja2.BaseLoader] = {}

    @classmethod
    def jinja2_env(cls, path: pathlib.Path) -> jinja2.Environment:
        """Instantiate a Jinja2 environment if necessary."""
        abspath = str(path.absolute())
        if abspath in cls._jinja2_env:
            return cls._jinja2_env[abspath]

        env = jinja2.Environment(autoescape=False, loader=cls.jinja2_loader(path))
        cls._jinja2_env[abspath] = env
        return env

    @classmethod
    def jinja2_loader(cls, path: pathlib.Path) -> jinja2.BaseLoader:
        """Instantiate a Jinja2 environment if necessary."""
        abspath = str(path.absolute())
        if abspath in cls._jinja2_loaders:
            return cls._jinja2_loaders[abspath]

        loader = jinja2.FileSystemLoader(abspath)
        cls._jinja2_loaders[abspath] = loader
        return loader


def ensure_none(cfg: Config, path: pathlib.Path) -> None:
    """Remove a file, directory, or other filesystem object altogether."""
    if not path.exists():
        return
    cfg.diag(lambda: f"Removing the existing {path}")
    try:
        subprocess.check_call(["rm", "-rf", "--", path])
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(f"Could not remove {path}: {err}")


def copy_file(
    cfg: Config,
    src: pathlib.Path,
    dstdir: pathlib.Path,
    dstname: Optional[str] = None,
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
        raise variant.VariantFileError(f"Could not copy {src} to {dst}: {err}")


def subst_debian_sources(
    cfg: Config,
    var: variant.Variant,
    src: pathlib.Path,
    dstdir: pathlib.Path,
    rtype: defs.RepoType,
) -> None:
    """Substitute the placeholder vars in a Debian sources list file."""
    assert isinstance(var.repo, defs.DebRepo)
    vendor = var.repo.vendor
    codename = var.repo.codename
    dst = dstdir / (src.stem + rtype.extension + src.suffix)
    cfg.diag(lambda: f"{src} -> {dst} [vendor {vendor}, codename {codename}]")

    ovr = cfg.overrides.repo.get(
        rtype.name, OverrideRepo(url=None, slug=None, vendor=None, codename=None)
    )
    try:
        result = (
            Singles.jinja2_env(src.parent)
            .get_template(src.name)
            .render(
                url=rtype.url if ovr.url is None else ovr.url,
                name=rtype.name,
                slug=rtype.name if ovr.slug is None else ovr.slug,
                vendor=vendor if ovr.vendor is None else ovr.vendor,
                codename=codename if ovr.codename is None else ovr.codename,
            )
        )
    except jinja2.TemplateError as err:
        raise variant.VariantFileError(f"Could not render the {src} template: {err}")

    try:
        dst.write_text(result + "\n", encoding="UTF-8")
    except (IOError, OSError) as err:
        raise variant.VariantFileError(f"Could not write out {dst}: {err}")


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
    cfg.diag(lambda: f"{src} -> {dst} []")

    ovr = cfg.overrides.repo.get(
        rtype.name, OverrideRepo(url=None, slug=None, vendor=None, codename=None)
    )
    try:
        result = (
            Singles.jinja2_env(src.parent)
            .get_template(src.name)
            .render(
                url=rtype.url if ovr.url is None else ovr.url,
                name=rtype.name,
                slug=rtype.name if ovr.slug is None else ovr.slug,
            )
        )
    except jinja2.TemplateError as err:
        raise variant.VariantFileError(f"Could not render the {src} template: {err}")

    try:
        dst.write_text(result + "\n", encoding="UTF-8")
    except (IOError, OSError) as err:
        raise variant.VariantFileError(f"Could not write out {dst}: {err}")


def build_repo(cfg: Config) -> pathlib.Path:
    """Build the StorPool repository archive."""
    distname = "add-storpool-repo"
    if not cfg.no_date:
        distdate = datetime.date.today().strftime("%Y%m%d")
        distname = f"{distname}-{distdate}"
    distdir = cfg.destdir / distname
    ensure_none(cfg, distdir)
    distdir.mkdir()

    copy_file(
        cfg,
        cfg.runtime,
        distdir,
        dstname="storpool_variant",
        executable=True,
    )

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
                f"No idea how to handle {type(var.repo).__name__} for {var.name}"
            )

    distfile = (cfg.destdir / distname).with_suffix(".tar.gz")
    ensure_none(cfg, distfile)
    cfg.diag(lambda: f"Creating {distfile}")
    try:
        subprocess.check_call(
            ["tar", "-caf", distfile, "-C", cfg.destdir, distname],
            shell=False,
        )
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(f"Could not package {distdir} up into {distfile}: {err}")
    return distfile


def parse_overrides(path: pathlib.Path) -> Overrides:
    """Parse the TOML overrides file."""
    if path is None:
        return Overrides(repo={})

    try:
        raw = tomli.loads(path.read_text(encoding="UTF-8"))
    except (OSError, ValueError) as err:
        sys.exit(f"Could not read or parse the {path} overrides file as valid TOML: {err}")

    try:
        raw_format = raw.pop("format")
    except (TypeError, AttributeError, KeyError):
        sys.exit(f"No 'format' section in the {path} override file")
    try:
        data_format = typedload.load(raw_format, DataFormat)
    except (TypeError, AttributeError, KeyError, ValueError) as err:
        sys.exit(f"Could not read the 'format' section of the {path} overrides file: {err}")
    if (data_format.version.major, data_format.version.minor) != (0, 1):
        sys.exit(
            f"Unsupported format version for the {path} override files, "
            f"only 0.1 supported so far"
        )

    try:
        return typedload.load(raw, Overrides, failonextra=True)
    except (TypeError, AttributeError, KeyError, ValueError) as err:
        sys.exit(f"Invalid format for the {path} overrides file: {err}")


@click.command(name="build")
@click.option(
    "-d",
    "--datadir",
    type=pathlib.Path,
    required=True,
    help="The directory to place the repo file in",
)
@click.option(
    "-D",
    "--destdir",
    type=pathlib.Path,
    required=True,
    help="The directory to place the repo file in",
)
@click.option(
    "-o",
    "--overrides",
    type=pathlib.Path,
    help="The path to a TOML configuration overrides file",
)
@click.option(
    "-r",
    "--runtime",
    type=pathlib.Path,
    required=True,
    help="The storpool_variant executable to use",
)
@click.option(
    "--no-date",
    is_flag=True,
    help="Do not include the current date in the directory name",
)
@click.pass_context
def cmd_build(
    ctx: click.Context,
    datadir: pathlib.Path,
    destdir: pathlib.Path,
    overrides: pathlib.Path,
    runtime: pathlib.Path,
    no_date: bool,
) -> None:
    """Build the StorPool repository archive and output its name."""
    # pylint: disable=too-many-arguments
    cfg_hold = ctx.find_object(ConfigHolder)
    assert isinstance(cfg_hold, ConfigHolder)
    cfg = Config(
        datadir=datadir,
        destdir=destdir,
        no_date=no_date,
        overrides=parse_overrides(overrides),
        runtime=runtime,
        verbose=cfg_hold.verbose,
    )

    try:
        print(build_repo(cfg=cfg))
    except variant.VariantError as err:
        print(str(err), file=sys.stderr)
        sys.exit(1)


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="verbose operation; display diagnostic output")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """Main routine: parse options, build the repository definitions."""
    ctx.ensure_object(ConfigHolder)
    ctx.obj.verbose = verbose


main.add_command(cmd_build)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
