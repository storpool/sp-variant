"""Run some sp_variant tests using Docker containers."""

import argparse
import asyncio
import asyncio.subprocess as aprocess
import dataclasses
import json
import pathlib
import subprocess
import sys
import tempfile

from typing import Dict, List, NamedTuple, Optional, Tuple, Union  # noqa: H301

import cfg_diag
import utf8_locale


@dataclasses.dataclass(frozen=True)
class Config(cfg_diag.ConfigDiag):
    """Runtime configuration for the Docker test runner."""

    repo_file: pathlib.Path
    utf8_env: Dict[str, str]


class SimpleBuilder(NamedTuple):
    """A part of a variant's builder data."""

    alias: str
    base_image: str


class SimpleVariant(NamedTuple):
    """A part of the variants representation."""

    name: str
    builder: SimpleBuilder


def parse_args() -> Config:
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(prog="test_docker")
    parser.add_argument(
        "-r",
        "--repo-file",
        type=pathlib.Path,
        required=True,
        help="The add-storpool-repo archive to test",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose operation; display diagnostic output",
    )

    args = parser.parse_args()
    return Config(
        repo_file=args.repo_file,
        utf8_env=utf8_locale.get_utf8_env(),
        verbose=args.verbose,
    )


def extract_variants_data(
    cfg: Config, tempd: pathlib.Path
) -> Tuple[pathlib.Path, Dict[str, SimpleVariant]]:
    """Extract the variants data into the specified directory."""
    cfg.diag(f"Making sure the {tempd} directory is empty")
    found = list(tempd.iterdir())
    if found:
        sys.exit(f"Unexpected stuff found in {tempd}: {found!r}")

    cfg.diag(f"Extracting {cfg.repo_file} into {tempd}")
    subprocess.check_call(
        ["tar", "-xaf", cfg.repo_file, "-C", tempd], env=cfg.utf8_env
    )
    cfg.diag("Looking for a single directory")
    found = list(tempd.iterdir())
    if (
        len(found) != 1
        or not found[0].is_dir()
        or found[0].name != "add-storpool-repo"
    ):
        sys.exit(
            (
                f"Expected a single add-storpool-repo directory in "
                f"{tempd}: {found!r}"
            )
        )
    spdir = found[0]

    spvar = spdir / "storpool_variant"
    if not spvar.is_file() or (spvar.stat().st_mode & 0o555) != 0o555:
        sys.exit(f"Expected an executable {spvar} file")

    output = subprocess.check_output(
        [spvar, "show", "all"], encoding="UTF-8", env=cfg.utf8_env
    )
    try:
        data = json.loads(output)
    except ValueError as err:
        sys.exit(f"Failed to decode the output of `{spvar} show all`: {err}")

    if (
        not isinstance(data, dict)
        or not isinstance(data.get("format"), dict)
        or not isinstance(data["format"].get("version"), dict)
        or data["format"]["version"].get("major") != 1
        or data["format"]["version"]["minor"] < 2
    ):
        sys.exit(f"Missing or unsupported `{spvar} show all` format version")

    res = {}
    for var in data["variants"].values():
        res[var["name"]] = SimpleVariant(
            name=var["name"],
            builder=SimpleBuilder(
                alias=var["builder"]["alias"],
                base_image=var["builder"]["base_image"],
            ),
        )

    return spdir, res


def filter_docker_images(
    cfg: Config, var_data: Dict[str, SimpleVariant]
) -> Dict[str, str]:
    """Find the Docker images present on this system."""
    cfg.diag("Querying Docker for the available images")
    images = set(
        subprocess.check_output(
            ["docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}"],
            encoding="UTF-8",
            env=cfg.utf8_env,
        ).splitlines()
    )

    res = {}
    for var in var_data.values():
        for image in (var.builder.base_image, "builder:" + var.builder.alias):
            if image == "IGNORE":
                continue
            if image in images:
                res[image] = var.name

    return res


async def run_detect_for_image(
    cfg: Config, spdir: pathlib.Path, image: str
) -> Tuple[Optional[str], Optional[str]]:
    """Run `storpool_variant detect` in a single new Docker container."""
    cfg.diag(f"{image}: starting a container")
    proc = await aprocess.create_subprocess_exec(
        "docker",
        "run",
        "--rm",
        "-v",
        f"{spdir}:/sp:ro",
        "--",
        image,
        "/sp/storpool_variant",
        "detect",
        env=cfg.utf8_env,
        stdout=aprocess.PIPE,
    )
    cfg.diag(f"{image}: created process {proc.pid}")
    assert proc.stdout is not None

    first_line = None
    rest = b""
    errors = []
    try:
        try:
            first_line = await proc.stdout.readline()
        except Exception as err:  # pylint: disable=broad-except
            errors.append(f"Could not read the first line: {err}")
        cfg.diag(f"{image}: first line {first_line!r}")

        if first_line:
            first_line = first_line.rstrip(b"\n")
            while True:
                try:
                    more = await proc.stdout.readline()
                except Exception as err:  # pylint: disable=broad-except
                    errors.append(f"Could not read a further line: {err}")
                    break
                cfg.diag(f"{image}: more {more!r}")

                if not more:
                    break
                rest += b"\n" + more.rstrip(b"\n")

        if rest:
            assert first_line is not None
            errors.append(
                f"More than one line of output: {(first_line + rest)!r}"
            )
    finally:
        res = await proc.wait()
        cfg.diag(f"{image}: exit code {res!r}")
        if res != 0:
            errors.append(f"Non-zero exit code {res}")

    first_line_dec = (
        None if first_line is None else first_line.decode("ISO-8859-15")
    )
    cfg.diag(f"{image}: first_line_dec {first_line_dec!r} errors {errors!r}")
    if errors:
        return (first_line_dec, "\n".join(errors))
    return (first_line_dec, None)


def analyze_detect_single(
    cfg: Config,
    image: str,
    expected: str,
    received: Union[BaseException, Tuple[Optional[str], Optional[str]]],
) -> List[str]:
    """Analyze a single container result."""
    if isinstance(received, BaseException):
        return [f"{image}: {received}"]
    if not isinstance(received, tuple) or len(received) != 2:
        return [f"{image}: unexpected result {received!r}"]

    r_first, r_err = received
    if r_err is not None:
        return [f"{image}: first line {r_first!r} stderr output {r_err!r}"]

    if r_first != expected:
        return [f"{image}: expected {expected!r}, got {r_first!r}"]

    cfg.diag(f"{image}: OK: {r_first!r}")
    return []


async def test_detect(
    cfg: Config, spdir: pathlib.Path, ordered: List[Tuple[str, str]]
) -> List[str]:
    """Run `storpool_variant detect` for all the images."""
    cfg.diag("Spawning the detect containers")
    gathering = asyncio.gather(
        *(run_detect_for_image(cfg, spdir, image) for image, _ in ordered),
        return_exceptions=True,
    )
    cfg.diag("Waiting for the detect containers")
    res = await gathering

    cfg.diag(f"Analyzing {len(res)} detect results")
    errors = []
    for (image, expected), received in zip(ordered, res):
        errors.extend(analyze_detect_single(cfg, image, expected, received))

    if len(res) != len(ordered):
        errors.append(
            f"Internal error: expected {len(ordered)} detect results, "
            f"got {len(res)} ones"
        )

    return errors


async def main() -> None:
    """Parse command-line options, run tests."""
    cfg = parse_args()

    with tempfile.TemporaryDirectory() as tempd_path:
        tempd = pathlib.Path(tempd_path)
        cfg.diag(f"Using {tempd} as a temporary directory")
        spdir, var_data = extract_variants_data(cfg, tempd)

        images = filter_docker_images(cfg, var_data)
        cfg.diag(
            f"About to test {len(images)} containers: {sorted(images.keys())}"
        )
        ordered = sorted(images.items())

        errors = await test_detect(cfg, spdir, ordered)
        if errors:
            sys.exit("`storpool_variant detect` errors: " + "\n".join(errors))

        cfg.diag("Everything seems fine!")


if __name__ == "__main__":
    asyncio.run(main())
