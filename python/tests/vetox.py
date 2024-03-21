# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Create a virtual environment, install Tox, run it."""

from __future__ import annotations

import argparse
import configparser
import dataclasses
import functools
import logging
import os
import pathlib
import re
import shlex
import subprocess
import sys
import tempfile
import typing
import venv


if typing.TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Final


VERSION: Final = "0.1.3"
"""The vetox library version."""


TOX_MIN_VERSION: Final = "4.1"
"""The minimum version of Tox needed to run our tests."""

# Is this too strict? No, for our purposes it is not.
RE_FROZEN_LINE: Final = re.compile(
    r"^ (?P<name> [A-Za-z][A-Za-z0-9_.-]+ ) == (?P<version> [0-9A-Za-z_.-]+ ) $",
    re.X,
)
"""Match a line in the output of `pip freeze`."""


@dataclasses.dataclass(frozen=True)
class Config:
    """Runtime configuration for the venv-tox tool."""

    conf: pathlib.Path
    """The path to the `tox.ini` file to use."""

    env: dict[str, str]
    """The cleaned-up environment variables to pass to child processes."""

    log: logging.Logger
    """The logger to send diagnostic, informational, warning, and error messages to."""

    tempd: pathlib.Path
    """The temporary directory to operate in."""

    tox_req: str | None
    """The PEP508 version requirements for Tox itself if specified."""

    tox_uv: bool
    """Install `tox-uv` ito the virtual environment."""

    uv: bool
    """Use `uv` to create the ephemeral Tox environment."""


# Shamelessly stolen from the logging-std module
@functools.lru_cache
def build_logger() -> logging.Logger:
    """Build a logger object, send info messages to stdout, everything else to stderr."""
    logger: Final = logging.getLogger("vetox")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    h_out: Final = logging.StreamHandler(sys.stdout)
    h_out.setLevel(logging.INFO)
    h_out.addFilter(lambda rec: rec.levelno == logging.INFO)
    logger.addHandler(h_out)

    h_err: Final = logging.StreamHandler(sys.stderr)
    h_err.setLevel(logging.INFO)
    h_err.addFilter(lambda rec: rec.levelno != logging.INFO)
    logger.addHandler(h_err)

    return logger


def clean_env() -> dict[str, str]:
    """Clean up any variables related to the current virtual environment."""
    return {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("PYTEST", "PYTHON", "TOX", "VIRTUAL_ENV"))
    }


def parse_frozen(contents: str) -> dict[str, str]:
    """Parse the output of `pip freeze` into a name-to-version dict."""

    def parse_single(line: str) -> tuple[str, str]:
        """Parse a single line."""
        pkg: Final = RE_FROZEN_LINE.match(line)
        if not pkg:
            sys.exit(f"Unexpected `pip freeze` output line: {line!r}")
        return pkg.group("name"), pkg.group("version")

    return dict(parse_single(line) for line in contents.splitlines())


def create_and_update_uv_venv(cfg: Config, penv: pathlib.Path) -> pathlib.Path:
    """Use `uv` to create a virtual environment."""
    cfg.log.info("About to create the %(penv)s virtual environment using uv", {"penv": penv})
    subprocess.check_call(["uv", "venv", "-p", sys.executable, "--", penv], env=cfg.env)
    return penv


def create_and_update_venv(cfg: Config) -> pathlib.Path:
    """Create a virtual environment, update all the packages within."""
    penv: pathlib.Path = cfg.tempd / "venv"
    if cfg.uv:
        return create_and_update_uv_venv(cfg, penv)

    cfg.log.info("About to create the %(penv)s virtual environment", {"penv": penv})
    if sys.version_info >= (3, 9):
        cfg.log.info("- using venv.create(upgrade_deps) directly")
        venv.create(penv, with_pip=True, upgrade_deps=True)
        return penv

    cfg.log.info("- no venv.create(upgrade_deps)")
    venv.create(penv, with_pip=True)

    cfg.log.info("- obtaining the list of packages in the virtual environment")
    contents: Final = subprocess.check_output(
        [penv / "bin/python3", "-m", "pip", "freeze", "--all"],
        encoding="UTF-8",
        env=cfg.env,
    )
    names: Final = sorted(parse_frozen(contents))
    cfg.log.info(
        "- upgrading the %(names)s package%(plu)s in the virtual environment",
        {"names": ", ".join(names), "plu": "" if len(names) == 1 else "s"},
    )
    subprocess.check_call(
        [penv / "bin/python3", "-m", "pip", "install", "-U", "--", *names],
        env=cfg.env,
    )
    return penv


@functools.lru_cache
def get_tox_min_version(conf: pathlib.Path) -> str:
    """Look for a minimum Tox version in the tox.ini file, fall back to TOX_MIN_VERSION."""
    cfgp: Final = configparser.ConfigParser(interpolation=None)
    with conf.open(encoding="UTF-8") as tox_ini:
        cfgp.read_file(tox_ini)

    return cfgp["tox"].get("min_version", cfgp["tox"].get("minversion", TOX_MIN_VERSION))


def install_tox(cfg: Config, penv: pathlib.Path) -> None:
    """Install Tox into the virtual environment."""
    if cfg.tox_req is not None:
        tox_req = f"tox {cfg.tox_req}"
    else:
        minver: Final = get_tox_min_version(cfg.conf)
        tox_req = f"tox >= {minver}"

    tox_uv: Final = ["tox-uv"] if cfg.tox_uv else []

    cfg.log.info(
        "Installing Tox %(tox_req)s%(tox_uv)s",
        {"tox_req": tox_req, "tox_uv": " and tox-uv" if cfg.tox_uv else ""},
    )
    if cfg.uv:
        subprocess.check_call(
            ["env", f"VIRTUAL_ENV={penv}", "uv", "pip", "install", tox_req, *tox_uv],
            env=cfg.env,
        )
    else:
        subprocess.check_call(
            [penv / "bin/python3", "-m", "pip", "install", tox_req, *tox_uv],
            env=cfg.env,
        )


def get_tox_cmdline(
    cfg: Config,
    penv: pathlib.Path,
    *,
    parallel: bool = True,
    args: list[str],
) -> list[pathlib.Path | str]:
    """Get the Tox command with arguments."""
    penv_py3: Final = penv / "bin/python3"

    def get_run_command() -> list[str]:
        """Get the appropriate command to run Tox in parallel or not."""
        if not parallel:
            return ["run"]

        vers: Final = subprocess.check_output(
            [penv_py3, "-m", "tox", "--version"],
            encoding="UTF-8",
            env=cfg.env,
        )
        if vers.startswith("3"):
            return ["run", "-p", "all"]

        return ["run-parallel"]

    cfg.log.info(
        "Running Tox%(parallel)s with %(args)s",
        {
            "parallel": " in parallel" if parallel else "",
            "args": ("additional arguments: " + shlex.join(args))
            if args
            else "no additional arguments",
        },
    )
    run_cmd: Final = get_run_command()
    return [penv_py3, "-m", "tox", "-c", cfg.conf, *run_cmd, *args]


def run_tox(cfg: Config, penv: pathlib.Path, *, parallel: bool = True, args: list[str]) -> None:
    """Run Tox from the virtual environment."""
    subprocess.check_call(get_tox_cmdline(cfg, penv, parallel=parallel, args=args), env=cfg.env)


def run(cfg_no_tempd: Config, *, parallel: bool, args: list[str]) -> None:
    """Create the virtual environment, install Tox, run it."""
    with tempfile.TemporaryDirectory() as tempd_obj:
        cfg: Final = dataclasses.replace(cfg_no_tempd, tempd=pathlib.Path(tempd_obj))
        penv: Final = create_and_update_venv(cfg)
        install_tox(cfg, penv)
        run_tox(cfg, penv, parallel=parallel, args=args)


def cmd_run(cfg_no_tempd: Config, args: list[str]) -> None:
    """Run the Tox tests sequentially."""
    run(cfg_no_tempd, parallel=False, args=args)


def cmd_run_parallel(cfg_no_tempd: Config, args: list[str]) -> None:
    """Run the Tox tests in parallel."""
    run(cfg_no_tempd, parallel=True, args=args)


def cmd_features(_cfg_no_tempd: Config, _args: list[str]) -> None:
    """Display the list of features supported by the program."""
    print(f"Features: vetox={VERSION} tox=0.1 tox-parallel=0.1 tox-uv=0.1 uv=0.1")


def cmd_version(_cfg_no_tempd: Config, _args: list[str]) -> None:
    """Display the vetox version."""
    print(f"vetox {VERSION}")


def parse_args() -> tuple[Config, Callable[[Config, list[str]], None], list[str]]:
    """Parse the command-line arguments."""
    parser: Final = argparse.ArgumentParser(prog="vetox")
    parser.add_argument(
        "-c",
        "--conf",
        type=pathlib.Path,
        default=pathlib.Path.cwd() / "tox.ini",
        help="The path to the tox.ini file",
    )

    subp: Final = parser.add_subparsers()
    p_run: Final = subp.add_parser("run", help="Run tests sequentially")
    p_run.add_argument(
        "-t",
        "--tox-req",
        type=str,
        help="specify the PEP508 version requirement for Tox itself",
    )
    p_run.add_argument(
        "--tox-uv",
        action="store_true",
        help="Install `tox-uv` into the virtual environment",
    )
    p_run.add_argument(
        "--uv",
        action="store_true",
        help="Use `uv` to create the ephemeral virtual environment",
    )
    p_run.add_argument("args", type=str, nargs="*", help="Additional arguments to pass to Tox")
    p_run.set_defaults(func=cmd_run)

    p_run_p: Final = subp.add_parser("run-parallel", help="Run tests in parallel")
    p_run_p.add_argument(
        "-t",
        "--tox-req",
        type=str,
        help="specify the PEP508 version requirement for Tox itself",
    )
    p_run_p.add_argument(
        "--tox-uv",
        action="store_true",
        help="Install `tox-uv` into the virtual environment",
    )
    p_run_p.add_argument(
        "--uv",
        action="store_true",
        help="Use `uv` to create the ephemeral virtual environment",
    )
    p_run_p.add_argument("args", type=str, nargs="*", help="Additional arguments to pass to Tox")
    p_run_p.set_defaults(func=cmd_run_parallel)

    p_features: Final = subp.add_parser("features", help="Display the supported program features")
    p_features.set_defaults(func=cmd_features)

    p_version: Final = subp.add_parser("version", help="Display the vetox version")
    p_version.set_defaults(func=cmd_version)

    args: Final = parser.parse_args()

    func: Final[Callable[[Config, list[str]], None] | None] = getattr(args, "func", None)
    if func is None:
        sys.exit("No subcommand specified; use `--help` for a list")

    # Things would be a bit simpler with `click`, but we don't want any dependencies
    return (
        Config(
            conf=args.conf,
            env=clean_env(),
            log=build_logger(),
            tempd=pathlib.Path("/nonexistent"),
            tox_req=getattr(args, "tox_req", False),  # type: ignore[arg-type]
            tox_uv=getattr(args, "tox_uv", False),
            uv=getattr(args, "uv", False),
        ),
        func,
        getattr(args, "args", []),
    )


def main() -> None:
    """Parse command-line arguments, create a virtual environment, run Tox."""
    cfg_no_tempd, func, args = parse_args()
    func(cfg_no_tempd, args)


if __name__ == "__main__":
    main()
