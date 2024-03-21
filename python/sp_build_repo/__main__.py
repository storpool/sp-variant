# SPDX-FileCopyrightText: 2021 - 2024  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause
"""Build the "add StorPool repository" archive."""

from __future__ import annotations

import dataclasses
import datetime
import functools
import logging
import pathlib
import shutil
import subprocess
import sys
from typing import TYPE_CHECKING, Dict, Optional

import click
import jinja2
import typedload.dataloader

from sp_build_repo import diag
from sp_variant import defs
from sp_variant import variant
from sp_variant import vbuild


if TYPE_CHECKING:
    from typing import ClassVar, Final


if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclasses.dataclass
class ConfigHolder:
    """Pass the context to the command-line subcommand handler."""

    verbose: bool = False


VERSION: Final = "1.0.0"


OVERRIDES_SCHEMAS: Final = {
    (0, 1): {
        "?repo": {
            "*": {
                "?slug": str,
                "?url": str,
                "?vendor": str,
                "?codename": str,
            },
        },
    },
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
class Config:
    """Configuration for the repository setup."""

    datadir: pathlib.Path
    destdir: pathlib.Path
    no_date: bool
    overrides: Overrides
    runtime: pathlib.Path
    verbose: bool


class Singles:
    """Keep some singleton objects in a controlled way."""

    _jinja2_env: ClassVar[dict[str, jinja2.Environment]] = {}
    _jinja2_loaders: ClassVar[dict[str, jinja2.BaseLoader]] = {}

    @classmethod
    def jinja2_env(cls, path: pathlib.Path) -> jinja2.Environment:
        """Instantiate a Jinja2 environment if necessary."""
        if (abspath := str(path.absolute())) in cls._jinja2_env:
            return cls._jinja2_env[abspath]

        env: Final = jinja2.Environment(
            autoescape=False,  # noqa: S701
            loader=cls.jinja2_loader(path),
        )
        cls._jinja2_env[abspath] = env
        return env

    @classmethod
    def jinja2_loader(cls, path: pathlib.Path) -> jinja2.BaseLoader:
        """Instantiate a Jinja2 environment if necessary."""
        if (abspath := str(path.absolute())) in cls._jinja2_loaders:
            return cls._jinja2_loaders[abspath]

        loader: Final = jinja2.FileSystemLoader(abspath)
        cls._jinja2_loaders[abspath] = loader
        return loader


def ensure_none(path: pathlib.Path) -> None:
    """Remove a file, directory, or other filesystem object altogether."""
    if not path.exists():
        return
    logging.debug("Removing the existing %(path)s", {"path": path})
    try:
        subprocess.check_call(["rm", "-rf", "--", path])
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(f"Could not remove {path}: {err}") from err


def copy_file(
    src: pathlib.Path,
    dstdir: pathlib.Path,
    *,
    dstname: str | None = None,
    executable: bool = False,
) -> None:
    """Copy a file with the appropriate access permissions."""
    dst: Final = dstdir / (src.name if dstname is None else dstname)
    ensure_none(dst)
    try:
        shutil.copy2(src, dst)
    except (OSError, subprocess.CalledProcessError) as err:
        raise variant.VariantFileError(f"Could not copy {src} to {dst}: {err}") from err
    try:
        dst.chmod(0o755 if executable else 0o644)
    except OSError as err:
        raise variant.VariantFileError(
            f"Could not set the permissions mode on {dst}: {err}",
        ) from err


def subst_debian_sources(
    cfg: Config,
    var: variant.Variant,
    src: pathlib.Path,
    dstdir: pathlib.Path,
    rtype: defs.RepoType,
) -> None:
    """Substitute the placeholder vars in a Debian sources list file."""
    assert isinstance(var.repo, defs.DebRepo)  # noqa: S101  # mypy needs this
    vendor: Final = var.repo.vendor
    codename: Final = var.repo.codename
    dst: Final = dstdir / (src.stem + rtype.extension + src.suffix)
    logging.debug(
        "%(src)s -> %(dst)s [vendor %(vendor)s, codename %(codename)s]",
        {"src": src, "dst": dst, "vendor": vendor, "codename": codename},
    )

    ovr: Final = cfg.overrides.repo.get(
        rtype.name,
        OverrideRepo(url=None, slug=None, vendor=None, codename=None),
    )
    try:
        result: Final = (
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
        raise variant.VariantFileError(f"Could not render the {src} template: {err}") from err

    try:
        dst.write_text(result + "\n", encoding="UTF-8")
    except OSError as err:
        raise variant.VariantFileError(f"Could not write out {dst}: {err}") from err


def subst_yum_repo(
    cfg: Config,
    var: variant.Variant,
    src: pathlib.Path,
    dstdir: pathlib.Path,
    rtype: defs.RepoType,
) -> None:
    """Substitute the placeholder vars in a Debian sources list file."""
    assert isinstance(var.repo, defs.YumRepo)  # noqa: S101  # mypy needs this
    dst: Final = dstdir / (src.stem + rtype.extension + src.suffix)
    logging.debug("%(src)s -> %(dst)s []", {"src": src, "dst": dst})

    ovr: Final = cfg.overrides.repo.get(
        rtype.name,
        OverrideRepo(url=None, slug=None, vendor=None, codename=None),
    )
    try:
        result: Final = (
            Singles.jinja2_env(src.parent)
            .get_template(src.name)
            .render(
                url=rtype.url if ovr.url is None else ovr.url,
                name=rtype.name,
                slug=rtype.name if ovr.slug is None else ovr.slug,
            )
        )
    except jinja2.TemplateError as err:
        raise variant.VariantFileError(f"Could not render the {src} template: {err}") from err

    try:
        dst.write_text(result + "\n", encoding="UTF-8")
    except OSError as err:
        raise variant.VariantFileError(f"Could not write out {dst}: {err}") from err


def build_repo(cfg: Config) -> pathlib.Path:
    """Build the StorPool repository archive."""

    def get_distname() -> str:
        """Build the distribution directory name."""
        base = "add-storpool-repo"
        if cfg.no_date:
            return base

        distdate: Final = datetime.datetime.now(tz=datetime.timezone.utc).date().strftime("%Y%m%d")
        return f"{base}-{distdate}"

    distname: Final = get_distname()
    distdir: Final = cfg.destdir / distname
    ensure_none(distdir)
    distdir.mkdir()

    copy_file(
        cfg.runtime,
        distdir,
        dstname="storpool_variant",
        executable=True,
    )

    copy_file(
        cfg.datadir / "common/scripts/storpool_variant.sh",
        distdir,
        executable=True,
    )
    copy_file(
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
            copy_file(cfg.datadir / var.repo.keyring, vardir)
        elif isinstance(var.repo, defs.YumRepo):
            for rtype in defs.REPO_TYPES:
                subst_yum_repo(cfg, var, cfg.datadir / var.repo.yumdef, vardir, rtype)
            copy_file(cfg.datadir / var.repo.keyring, vardir)
        else:
            raise NotImplementedError(
                f"No idea how to handle {type(var.repo).__name__} for {var.name}",
            )

    distfile: Final = (cfg.destdir / distname).with_suffix(".tar.gz")
    ensure_none(distfile)
    logging.debug("Creating %(distfile)s", {"distfile": distfile})
    try:
        subprocess.check_call(
            ["tar", "-caf", distfile, "-C", cfg.destdir, distname],
            shell=False,
        )
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(
            f"Could not package {distdir} up into {distfile}: {err}",
        ) from err
    return distfile


@functools.lru_cache(maxsize=2)
def typed_loader(*, failonextra: bool = False) -> typedload.dataloader.Loader:
    """Prepare a loader that can parse annotated types."""
    return typedload.dataloader.Loader(pep563=True, failonextra=failonextra)


def parse_overrides(path: pathlib.Path) -> Overrides:
    """Parse the TOML overrides file."""
    if path is None:
        return Overrides(repo={})

    try:
        raw: Final = tomllib.loads(path.read_text(encoding="UTF-8"))
    except (OSError, ValueError) as err:
        sys.exit(f"Could not read or parse the {path} overrides file as valid TOML: {err}")

    try:
        raw_format: Final = raw.pop("format")
    except (TypeError, AttributeError, KeyError):
        sys.exit(f"No 'format' section in the {path} override file")
    try:
        data_format: Final = typed_loader().load(raw_format, DataFormat)
    except (TypeError, AttributeError, KeyError, ValueError) as err:
        sys.exit(f"Could not read the 'format' section of the {path} overrides file: {err}")
    if (data_format.version.major, data_format.version.minor) != (0, 1):
        sys.exit(
            f"Unsupported format version for the {path} override files, "
            f"only 0.1 supported so far",
        )

    try:
        return typed_loader(failonextra=True).load(raw, Overrides)
    except (TypeError, AttributeError, KeyError, ValueError) as err:
        sys.exit(f"Invalid format for the {path} overrides file: {err}")


@click.command(name="build")
@click.option(
    "-d",
    "--datadir",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    required=True,
    help="The directory to place the repo file in",
)
@click.option(
    "-D",
    "--destdir",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    required=True,
    help="The directory to place the repo file in",
)
@click.option(
    "-o",
    "--overrides",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    help="The path to a TOML configuration overrides file",
)
@click.option(
    "-r",
    "--runtime",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        executable=True,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    required=True,
    help="The storpool_variant executable to use",
)
@click.option(
    "--no-date",
    is_flag=True,
    help="Do not include the current date in the directory name",
)
@click.pass_context
def cmd_build(  # noqa: PLR0913
    ctx: click.Context,
    *,
    datadir: pathlib.Path,
    destdir: pathlib.Path,
    overrides: pathlib.Path,
    runtime: pathlib.Path,
    no_date: bool,
) -> None:
    """Build the StorPool repository archive and output its name."""
    cfg_hold: Final = ctx.find_object(ConfigHolder)
    assert isinstance(cfg_hold, ConfigHolder)  # noqa: S101  # mypy needs this
    diag.setup_logger(verbose=cfg_hold.verbose)
    cfg: Final = Config(
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
def main(ctx: click.Context, *, verbose: bool) -> None:
    """Parse options, build the repository definitions."""
    ctx.ensure_object(ConfigHolder)
    ctx.obj.verbose = verbose


main.add_command(cmd_build)


if __name__ == "__main__":
    main()
