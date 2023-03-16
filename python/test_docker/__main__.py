# SPDX-FileCopyrightText: 2021 - 2023  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause
"""Run some sp_variant tests using Docker containers."""

from __future__ import annotations

import asyncio
import asyncio.subprocess as aprocess
import dataclasses
import json
import pathlib
import subprocess
import sys
import tempfile

from typing import Final, NamedTuple

import cfg_diag
import click
import utf8_locale


@dataclasses.dataclass(frozen=True)
class Config(cfg_diag.Config):
    """Runtime configuration for the Docker test runner."""

    images_filter: tuple[str, ...]
    repo_file: pathlib.Path
    utf8_env: dict[str, str]


class SimpleBuilder(NamedTuple):
    """A part of a variant's builder data."""

    alias: str
    base_image: str
    utf8_locale: str


class SimpleVariant(NamedTuple):
    """A part of the variants representation."""

    name: str
    builder: SimpleBuilder


def extract_variants_data(
    cfg: Config, tempd: pathlib.Path
) -> tuple[pathlib.Path, dict[str, SimpleVariant]]:
    """Extract the variants data into the specified directory."""
    cfg.diag(lambda: f"Making sure the {tempd} directory is empty")
    if found := list(tempd.iterdir()):
        sys.exit(f"Unexpected stuff found in {tempd}: {found!r}")

    cfg.diag(lambda: f"Extracting {cfg.repo_file} into {tempd}")
    subprocess.check_call(["tar", "-xaf", cfg.repo_file, "-C", tempd], env=cfg.utf8_env)
    cfg.diag_("Looking for a single directory")
    found = list(tempd.iterdir())
    if len(found) != 1 or not found[0].is_dir() or found[0].name != "add-storpool-repo":
        sys.exit(f"Expected a single add-storpool-repo directory in {tempd}: {found!r}")
    spdir: Final = found[0]

    spvar: Final = spdir / "storpool_variant"
    if not spvar.is_file() or (spvar.stat().st_mode & 0o555) != 0o555:
        sys.exit(f"Expected an executable {spvar} file")

    output: Final = subprocess.check_output(
        [spvar, "show", "all"], encoding="UTF-8", env=cfg.utf8_env
    )
    try:
        data: Final = json.loads(output)
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

    res: Final = {}
    for var in data["variants"].values():
        res[var["name"]] = SimpleVariant(
            name=var["name"],
            builder=SimpleBuilder(
                alias=var["builder"]["alias"],
                base_image=var["builder"]["base_image"],
                utf8_locale=var["builder"]["utf8_locale"],
            ),
        )

    return spdir, res


def filter_docker_images(cfg: Config, var_data: dict[str, SimpleVariant]) -> dict[str, str]:
    """Find the Docker images present on this system."""
    cfg.diag_("Querying Docker for the available images")
    all_images: Final = set(
        subprocess.check_output(
            ["docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}"],
            encoding="UTF-8",
            env=cfg.utf8_env,
        ).splitlines()
    )
    images: Final = (
        all_images
        if not cfg.images_filter
        else {name for name in all_images if any(word in name for word in cfg.images_filter)}
    )

    res: Final = {}
    ignored: Final = {"IGNORE", "centos:6"}
    for var in var_data.values():
        for image in (var.builder.base_image, "builder:" + var.builder.alias):
            if image in ignored:
                continue
            if image in images:
                res[image] = var.name

    return res


async def process_detect_lines(
    cfg: Config, image: str, proc: aprocess.Process
) -> tuple[bytes | None, list[str]]:
    """Read the lines output by `storpool_variant detect`, see if they look okay."""
    assert proc.stdout is not None  # noqa: S101  # mypy needs this

    first_line = None
    rest = b""
    errors: Final = []
    try:  # pylint: disable=too-many-try-statements
        try:
            first_line = await proc.stdout.readline()
        except Exception as err:  # pylint: disable=broad-except  # noqa: BLE001
            errors.append(f"Could not read the first line: {err}")
        cfg.diag(lambda: f"{image}: first line {first_line!r}")

        if first_line:
            first_line = first_line.rstrip(b"\n")
            # pylint: disable-next=while-used
            while True:
                try:
                    more = await proc.stdout.readline()
                except Exception as err:  # pylint: disable=broad-except  # noqa: BLE001
                    errors.append(f"Could not read a further line: {err}")
                    break
                cfg.diag(lambda: f"{image}: more {more!r}")  # noqa: B023

                if not more:
                    break
                rest += b"\n" + more.rstrip(b"\n")

        if rest:
            assert first_line is not None  # noqa: S101  # mypy needs this
            errors.append(f"More than one line of output: {(first_line + rest)!r}")
    finally:
        res: Final = await proc.wait()
        cfg.diag(lambda: f"{image}: exit code {res!r}")
        if res:
            errors.append(f"Non-zero exit code {res}")

    return first_line, errors


async def run_detect_for_image(
    cfg: Config, spdir: pathlib.Path, image: str
) -> tuple[str | None, str | None]:
    """Run `storpool_variant detect` in a single new Docker container."""
    cfg.diag(lambda: f"{image}: starting a container")
    proc: Final = await aprocess.create_subprocess_exec(
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
    cfg.diag(lambda: f"{image}: created process {proc.pid}")

    first_line, errors = await process_detect_lines(cfg, image, proc)
    first_line_dec: Final = None if first_line is None else first_line.decode("ISO-8859-15")
    cfg.diag(lambda: f"{image}: first_line_dec {first_line_dec!r} errors {errors!r}")
    if errors:
        return (first_line_dec, "\n".join(errors))
    return (first_line_dec, None)


def analyze_detect_single(
    cfg: Config,
    image: str,
    expected: str,
    received: BaseException | tuple[str | None, str | None],
) -> list[str]:
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

    cfg.diag(lambda: f"{image}: OK: {r_first!r}")
    return []


async def test_detect(
    cfg: Config, spdir: pathlib.Path, ordered: list[tuple[str, str]]
) -> list[str]:
    """Run `storpool_variant detect` for all the images."""
    cfg.diag_("Spawning the detect containers")
    gathering: Final = asyncio.gather(
        *(run_detect_for_image(cfg, spdir, image) for image, _ in ordered),
        return_exceptions=True,
    )
    cfg.diag_("Waiting for the detect containers")
    res: Final = await gathering

    cfg.diag(lambda: f"Analyzing {len(res)} detect results")
    errors: Final = []
    for (image, expected), received in zip(ordered, res):
        errors.extend(analyze_detect_single(cfg, image, expected, received))

    if len(res) != len(ordered):
        errors.append(
            f"Internal error: expected {len(ordered)} detect results, got {len(res)} ones"
        )

    return errors


async def run_add_repo_for_image(
    cfg: Config,
    spdir: pathlib.Path,
    addsh: pathlib.Path,
    image: str,
    variant: SimpleVariant,
) -> tuple[bytes, bytes, int]:
    """Run `add-storpool-repo` in a single new Docker container."""
    cfg.diag(lambda: f"{image}: starting a container")
    proc: Final = await aprocess.create_subprocess_exec(
        "docker",
        "run",
        "--rm",
        "-v",
        f"{spdir}:/sp:ro",
        "--",
        image,
        "env",
        "LC_ALL=" + variant.builder.utf8_locale,
        "/sp/" + str(addsh.relative_to(spdir)),
        env=cfg.utf8_env,
        stdout=aprocess.PIPE,
        stderr=aprocess.PIPE,
    )
    cfg.diag(lambda: f"{image}: created process {proc.pid}")
    assert proc.stdout is not None  # noqa: S101  # mypy needs this
    assert proc.stderr is not None  # noqa: S101  # mypy needs this

    async def read_stream(stype: str, stream: asyncio.StreamReader) -> bytes:
        """Read lines from a stream, output them, gather them."""
        cfg.diag(lambda: f"{image}: waiting for {stype} lines")
        res = b""
        # pylint: disable-next=while-used
        while True:
            if not (line := await stream.readline()):
                cfg.diag(lambda: f"{image}: no more {stype}")
                break

            cfg.diag(lambda: f"{image}: read a {stype} line: {line!r}")
            res += line

        return res

    r_out, r_err = await asyncio.gather(
        read_stream("stdout", proc.stdout), read_stream("stderr", proc.stderr)
    )
    res: Final = await proc.wait()
    return (r_out, r_err, res)


def analyze_add_repo_single(
    cfg: Config,
    image: str,
    received: BaseException | tuple[bytes, bytes, int],
) -> list[str]:
    """Analyze a single add-storpool-repo result."""
    if isinstance(received, BaseException):
        return [f"{image}: {received}"]
    if not isinstance(received, tuple) or len(received) != 3:
        return [f"{image}: unexpected result {received!r}"]

    r_out, r_err, r_res = received
    if r_res:
        return [
            f"{image}: the script failed with exit code {r_res}; "
            f"stdout: {r_out!r} stderr {r_err!r}"
        ]

    cfg.diag(lambda: f"{image}: OK")
    return []


async def test_add_repo(
    cfg: Config,
    spdir: pathlib.Path,
    ordered: list[tuple[str, str]],
    var_data: dict[str, SimpleVariant],
) -> list[str]:
    """Run `storpool_variant detect` for all the images."""
    cfg.diag_("Preparing the add-repo script")
    addsh: Final = spdir / "run-add-repo.sh"
    if addsh.exists() or addsh.is_symlink():
        return [f"Did not expect {addsh} to exist"]
    try:
        addsh.write_text(
            """#!/bin/sh

set -e
set -x

check_locale()
{
    local var="$1" value="$2"

    if [ -z "$value" ]; then
        echo "$var is not set" 1>&2
        exit 1
    fi
    if [ -n "$(env LC_ALL="$value" locale -k -c LC_CTYPE 2>&1 > /dev/null)" ]; then
        echo "$var specifies a '$value' locale that is not configured" 1>&2
        exit 1
    fi
    if ! env LC_ALL="$value" locale -k -c LC_CTYPE | grep -Eqe '^charmap=.*UTF-8'; then
        echo "$var specifies a '$value' locale with a non-UTF-8 charmap" 1>&2
        exit 1
    fi
}

# Make sure LC_ALL is set to a valid UTF-8-capable locale
echo 'Checking whether LC_ALL specifies a valid UTF-8-capable locale'
check_locale 'The LC_ALL environment variable' "$LC_ALL"

# Parsing JSON without jq? Yeah, sure, why not...
echo 'Checking for a Debian-like variant'
unset is_debian
if /sp/storpool_variant show current | tr "\n" ' ' | grep -Eqe '"family"[[:space:]]*:[[:space:]]*"debian"'; then
    is_debian=1
    echo 'Running apt-get update'
    apt-get update
elif [ "$(/sp/storpool_variant detect)" = 'CENTOS8' ]; then
    echo 'Running dnf swap centos-linux-repos centos-stream-repos'
    dnf --disablerepo '*' --enablerepo extras -y swap centos-linux-repos centos-stream-repos
else
    echo 'No apt-get update or dnf swap necessary'
fi

echo 'Running add-storpool-repo'
/sp/add-storpool-repo.sh

echo 'Installing jq'
/sp/storpool_variant command run -- package.install jq

echo 'Checking whether builder.utf8_locale specifies a valid UTF-8-capable locale'
u8loc="$(/sp/storpool_variant show current | jq -r '.variant.builder.utf8_locale')"
check_locale 'The builder.utf8_locale setting' "$u8loc"

echo 'Checking whether StorPool has a package repository for this variant'
supp_repo="$(/sp/storpool_variant show current | jq -r '.variant.supported.repo')"
case "$supp_repo" in
    true)
        supp_repo='1'
        ;;

    false)
        supp_repo=''
        ;;

    *)
        echo "storpool_variant output an unexpected value for supported.repo: '$supp_repo'" 1>&2
        exit 1
        ;;
esac

echo 'Installing some programs'
if ! /sp/storpool_variant command run -- package.install sp-python3 sp-python3-modules; then
    if [ -z "$supp_repo" ]; then
        echo 'Ignoring the package.install failure for an unsupported repository'
    else
        echo 'Installing the StorPool packages failed' 1>&2
        exit 1
    fi
fi

echo 'Running add-storpool-repo -t staging'
/sp/add-storpool-repo.sh -t staging

echo 'Running the "update the repository metadata" command'
/sp/storpool_variant.sh command run package.update_db

echo 'Obtaining information about the sp-python3 package'
res=0
if [ -n "$is_debian" ]; then
    if ! apt-cache policy sp-python3; then
        res="$?"
    fi
else
    if ! yum info sp-python3; then
        res="$?"
    fi
fi
if [ "$res" -ne 0 ]; then
    if [ -z "$supp_repo" ]; then
        echo 'Ignoring the package query failure for an unsupported repository'
    else
        echo 'Querying for the sp-python3 package failed' 1>&2
        exit 1
    fi
fi

echo 'Done, it seems'
""",  # noqa: E501  pylint: disable=line-too-long
            encoding="UTF-8",
        )
    except Exception as err:  # pylint: disable=broad-except  # noqa: BLE001
        return [f"Could not create {addsh}: {err}"]
    try:
        addsh.chmod(0o755)
    except OSError as err:
        return [f"Could not set the permissions mode on {addsh}: {err}"]

    cfg.diag_("Spawning the add-repo containers")
    gathering: Final = asyncio.gather(
        *(
            run_add_repo_for_image(cfg, spdir, addsh, image, var_data[variant])
            for image, variant in ordered
        ),
        return_exceptions=True,
    )
    cfg.diag_("Waiting for the add-repo containers")
    res: Final = await gathering

    cfg.diag(lambda: f"Analyzing {len(res)} add-repo results")
    errors: Final = []
    for (image, _), received in zip(ordered, res):
        errors.extend(analyze_add_repo_single(cfg, image, received))

    if len(res) != len(ordered):
        errors.append(
            f"Internal error: expected {len(ordered)} add-repo results, got {len(res)} ones"
        )

    return errors


async def run_tests(
    cfg: Config,
    spdir: pathlib.Path,
    ordered: list[tuple[str, str]],
    var_data: dict[str, SimpleVariant],
) -> None:
    """Run the tests themselves."""
    if errors := await test_detect(cfg, spdir, ordered):
        sys.exit("`storpool_variant detect` errors: " + "\n".join(errors))

    if errors := await test_add_repo(cfg, spdir, ordered, var_data):
        sys.exit("`add-storpool-repo.sh` errors: " + "\n".join(errors))

    cfg.diag_("Everything seems fine!")


@click.command()
@click.option(
    "-i",
    "--images-filter",
    type=str,
    multiple=True,
    help="Only process images with names containing this string; may be specified multiple times",
)
@click.option(
    "-r",
    "--repo-file",
    type=pathlib.Path,
    required=True,
    help="The add-storpool-repo archive to test",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Verbose operation; display diagnostic output",
)
def main(*, images_filter: tuple[str, ...], repo_file: pathlib.Path, verbose: bool) -> None:
    """Parse command-line options, run tests."""
    cfg: Final = Config(
        images_filter=images_filter,
        repo_file=repo_file,
        utf8_env=utf8_locale.get_utf8_env(),
        verbose=verbose,
    )
    with tempfile.TemporaryDirectory() as tempd_path:
        tempd: Final = pathlib.Path(tempd_path)
        cfg.diag(lambda: f"Using {tempd} as a temporary directory")
        spdir, var_data = extract_variants_data(cfg, tempd)

        images: Final = filter_docker_images(cfg, var_data)
        cfg.diag(lambda: f"About to test {len(images)} containers: {sorted(images.keys())}")
        ordered: Final = sorted(images.items())

        asyncio.run(run_tests(cfg, spdir, ordered, var_data))


if __name__ == "__main__":
    main()  # pylint: disable=missing-kwoa
