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
"""Build the hierarchical structure of variant definitions."""

import re

from typing import Any, Dict, List, Text, Type, TypeVar, Tuple, Union  # noqa: H301

from . import defs

CMD_NOOP = ["true"]  # type: List[Text]

T = TypeVar("T")  # pylint: disable=invalid-name

_VARIANT_DEF = [
    defs.Variant(
        name="DEBIAN12",
        descr="Debian 12.x (bookworm/unstable)",
        parent="",
        family="debian",
        detect=defs.Detect(
            filename="/etc/os-release",
            regex=re.compile(
                r"""^
                    PRETTY_NAME= .*
                    Debian \s+ GNU/Linux \s+
                    (?: bookworm | 12 ) (?: \s | / )
                """,
                re.X,
            ),
            os_id="debian",
            os_version_regex=re.compile(r"^12$"),
        ),
        commands=defs.Commands(
            package=defs.CommandsPackage(
                update_db=["apt-get", "-q", "-y", "update"],
                install=[
                    "env",
                    "DEBIAN_FRONTEND=noninteractive",
                    "apt-get",
                    "-q",
                    "-y",
                    "--no-install-recommends",
                    "install",
                    "--",
                ],
                list_all=[
                    "dpkg-query",
                    "-W",
                    "-f",
                    r"${Package}\t${Version}\t${Architecture}\t${db:Status-Abbrev}\n",
                    "--",
                ],
                purge=[
                    "env",
                    "DEBIAN_FRONTEND=noninteractive",
                    "apt-get",
                    "-q",
                    "-y",
                    "purge",
                    "--",
                ],
                remove=[
                    "env",
                    "DEBIAN_FRONTEND=noninteractive",
                    "apt-get",
                    "-q",
                    "-y",
                    "remove",
                    "--",
                ],
                remove_impl=[
                    "env",
                    "DEBIAN_FRONTEND=noninteractive",
                    "dpkg",
                    "-r",
                    "--",
                ],
            ),
            pkgfile=defs.CommandsPkgFile(
                dep_query=[
                    "sh",
                    "-c",
                    "dpkg-deb -f -- \"$pkg\" 'Depends' | sed -e 's/ *, */,/g' | tr ',' \"\\n\"",
                ],
                install=[
                    "sh",
                    "-c",
                    "env DEBIAN_FRONTEND=noninteractive apt-get install "
                    "--no-install-recommends --reinstall -y "
                    "-o DPkg::Options::=--force-confnew "
                    "-- $packages",
                ],
            ),
        ),
        min_sys_python="3.9",
        repo=defs.DebRepo(
            vendor="debian",
            codename="unstable",
            sources="debian/repo/storpool.sources",
            keyring="debian/repo/storpool-keyring.gpg",
            req_packages=["ca-certificates"],
        ),
        package={
            "BINDINGS_PYTHON": "python3",
            "BINDINGS_PYTHON_CONFGET": "python3-confget",
            "BINDINGS_PYTHON_SIMPLEJSON": "python3-simplejson",
            "CGROUP": "cgroup-tools",
            "CPUPOWER": "linux-cpupower",
            "LIBSSL": "libssl1.1",
            "MCELOG": "mcelog",
        },
        systemd_lib="lib/systemd/system",
        file_ext="deb",
        initramfs_flavor="update-initramfs",
        builder=defs.Builder(
            alias="debian12",
            base_image="debian:unstable",
            branch="debian/unstable",
            kernel_package="linux-headers",
            utf8_locale="C.UTF-8",
        ),
    ),
    defs.VariantUpdate(
        name="DEBIAN11",
        descr="Debian 11.x (bullseye)",
        parent="DEBIAN12",
        detect=defs.Detect(
            filename="/etc/os-release",
            regex=re.compile(
                r"""^
                    PRETTY_NAME= .*
                    Debian \s+ GNU/Linux \s+
                    (?: bullseye | 11 ) (?: \s | / )
                """,
                re.X,
            ),
            os_id="debian",
            os_version_regex=re.compile(r"^11$"),
        ),
        updates={
            "repo": {"codename": "bullseye"},
            "builder": {
                "alias": "debian11",
                "base_image": "debian:bullseye",
                "branch": "debian/bullseye",
            },
        },
    ),
    defs.VariantUpdate(
        name="DEBIAN10",
        descr="Debian 10.x (buster)",
        parent="DEBIAN11",
        detect=defs.Detect(
            filename="/etc/os-release",
            regex=re.compile(
                r"""^
                    PRETTY_NAME= .*
                    Debian \s+ GNU/Linux \s+
                    (?: buster | 10 ) (?: \s | / )
                """,
                re.X,
            ),
            os_id="debian",
            os_version_regex=re.compile(r"^10$"),
        ),
        updates={
            "repo": {
                "codename": "buster",
            },
            "min_sys_python": "2.7",
            "package": {
                "BINDINGS_PYTHON": "python",
                "BINDINGS_PYTHON_CONFGET": "python-confget",
                "BINDINGS_PYTHON_SIMPLEJSON": "python-simplejson",
            },
            "builder": {
                "alias": "debian10",
                "base_image": "debian:buster",
                "branch": "debian/buster",
            },
        },
    ),
    defs.VariantUpdate(
        name="DEBIAN9",
        descr="Debian 9.x (stretch)",
        parent="DEBIAN10",
        detect=defs.Detect(
            filename="/etc/os-release",
            regex=re.compile(
                r"""^
                    PRETTY_NAME= .*
                    Debian \s+ GNU/Linux \s+
                    (?: stretch | 9 ) (?: \s | / )
                """,
                re.X,
            ),
            os_id="debian",
            os_version_regex=re.compile(r"^9$"),
        ),
        updates={
            "repo": {
                "codename": "stretch",
                "req_packages": ["apt-transport-https", "ca-certificates"],
            },
            "builder": {
                "alias": "debian9",
                "base_image": "debian:stretch",
                "branch": "debian/stretch",
            },
        },
    ),
    defs.VariantUpdate(
        name="UBUNTU2204",
        descr="Ubuntu 22.04 LTS (Jammy Jellyfish)",
        parent="DEBIAN12",
        detect=defs.Detect(
            filename="/etc/os-release",
            regex=re.compile(
                r"^ PRETTY_NAME= .* (?: Ubuntu \s+ 22 \. 04 | Mint \s+ 22 ) ",
                re.X,
            ),
            os_id="ubuntu",
            os_version_regex=re.compile(r"^22\.04$"),
        ),
        updates={
            "repo": {
                "vendor": "ubuntu",
                "codename": "jammy",
            },
            "package": {
                "CPUPOWER": "linux-tools-generic",
                "MCELOG": "bash",
            },
            "builder": {
                "alias": "ubuntu-22.04",
                "base_image": "ubuntu:jammy",
                "branch": "ubuntu/jammy",
            },
        },
    ),
    defs.VariantUpdate(
        name="UBUNTU2110",
        descr="Ubuntu 21.10 LTS (Impish Indri)",
        parent="UBUNTU2204",
        detect=defs.Detect(
            filename="/etc/os-release",
            regex=re.compile(
                r"^ PRETTY_NAME= .* (?: Ubuntu \s+ 21 \. 10 | Mint \s+ 21 ) ",
                re.X,
            ),
            os_id="ubuntu",
            os_version_regex=re.compile(r"^21\.10$"),
        ),
        updates={
            "repo": {
                "vendor": "ubuntu",
                "codename": "impish",
            },
            "builder": {
                "alias": "ubuntu-21.10",
                "base_image": "ubuntu:impish",
                "branch": "ubuntu/impish",
            },
        },
    ),
    defs.VariantUpdate(
        name="UBUNTU2004",
        descr="Ubuntu 20.04 LTS (Focal Fossa)",
        parent="UBUNTU2110",
        detect=defs.Detect(
            filename="/etc/os-release",
            regex=re.compile(
                r"^ PRETTY_NAME= .* (?: Ubuntu \s+ 20 \. 04 | Mint \s+ 20 ) ",
                re.X,
            ),
            os_id="ubuntu",
            os_version_regex=re.compile(r"^20\.04$"),
        ),
        updates={
            "repo": {
                "vendor": "ubuntu",
                "codename": "focal",
            },
            "min_sys_python": "3.8",
            "builder": {
                "alias": "ubuntu-20.04",
                "base_image": "ubuntu:focal",
                "branch": "ubuntu/focal",
            },
        },
    ),
    defs.VariantUpdate(
        name="UBUNTU1804",
        descr="Ubuntu 18.04 LTS (Bionic Beaver)",
        parent="UBUNTU2004",
        detect=defs.Detect(
            filename="/etc/os-release",
            regex=re.compile(
                r"^ PRETTY_NAME= .* Ubuntu \s+ 18 \. 04 ",
                re.X,
            ),
            os_id="ubuntu",
            os_version_regex=re.compile(r"^18\.04$"),
        ),
        updates={
            "repo": {
                "codename": "bionic",
            },
            "min_sys_python": "2.7",
            "package": {
                "BINDINGS_PYTHON": "python",
                "BINDINGS_PYTHON_CONFGET": "python-confget",
                "BINDINGS_PYTHON_SIMPLEJSON": "python-simplejson",
            },
            "builder": {
                "alias": "ubuntu-18.04",
                "base_image": "ubuntu:bionic",
                "branch": "ubuntu/bionic",
            },
        },
    ),
    defs.VariantUpdate(
        name="UBUNTU1604",
        descr="Ubuntu 16.04 LTS (Xenial Xerus)",
        parent="UBUNTU1804",
        detect=defs.Detect(
            filename="/etc/os-release",
            regex=re.compile(
                r"^ PRETTY_NAME= .* Ubuntu \s+ 16 \. 04 ",
                re.X,
            ),
            os_id="ubuntu",
            os_version_regex=re.compile(r"^16\.04$"),
        ),
        updates={
            "repo": {
                "codename": "xenial",
                "req_packages": ["apt-transport-https", "ca-certificates"],
            },
            "package": {
                "LIBSSL": "libssl1.0.0",
                "mcelog": "mcelog",
            },
            "builder": {
                "alias": "ubuntu-16.04",
                "base_image": "ubuntu:xenial",
                "branch": "ubuntu/xenial",
            },
        },
    ),
    defs.Variant(
        name="CENTOS8",
        descr="CentOS 8.x",
        parent="",
        family="redhat",
        detect=defs.Detect(
            filename="/etc/redhat-release",
            regex=re.compile(r"^ CentOS \s .* \s 8 \. (?: [3-9] | (?: [12][0-9] ) )", re.X),
            os_id="centos",
            os_version_regex=re.compile(r"^8(?:$|\.[4-9]|\.[1-9][0-9])"),
        ),
        commands=defs.Commands(
            package=defs.CommandsPackage(
                update_db=CMD_NOOP,
                install=[
                    "dnf",
                    "--enablerepo=storpool-contrib",
                    "--enablerepo=powertools",
                    "install",
                    "-q",
                    "-y",
                    "--",
                ],
                list_all=[
                    "rpm",
                    "-qa",
                    "--qf",
                    r"%{Name}\t%{EVR}\t%{Arch}\tii\n",
                    "--",
                ],
                purge=[
                    "yum",
                    "remove",
                    "-q",
                    "-y",
                    "--",
                ],
                remove=[
                    "yum",
                    "remove",
                    "-q",
                    "-y",
                    "--",
                ],
                remove_impl=[
                    "rpm",
                    "-e",
                    "--",
                ],
            ),
            pkgfile=defs.CommandsPkgFile(
                dep_query=[
                    "sh",
                    "-c",
                    'rpm -qpR -- "$pkg"',
                ],
                install=[
                    "sh",
                    "-c",
                    """
unset to_install to_reinstall
for f in $packages; do
    package="$(rpm -qp "$f")"
    if rpm -q -- "$package"; then
        to_reinstall="$to_reinstall ./$f"
    else
        to_install="$to_install ./$f"
    fi
done

if [ -n "$to_install" ]; then
    dnf install -y --enablerepo=storpool-contrib,powertools --setopt=localpkg_gpgcheck=0 -- $to_install
fi
if [ -n "$to_reinstall" ]; then
    dnf reinstall -y --enablerepo=storpool-contrib,powertools --setopt=localpkg_gpgcheck=0 -- $to_reinstall
fi
""",  # noqa: E501  pylint: disable=line-too-long
                ],
            ),
        ),
        min_sys_python="2.7",
        repo=defs.YumRepo(
            yumdef="redhat/repo/storpool-centos.repo",
            keyring="redhat/repo/RPM-GPG-KEY-StorPool",
        ),
        package={
            "KMOD": "kmod",
            "LIBCGROUP": "libcgroup-tools",
            "LIBUDEV": "systemd-libs",
            "OPENSSL": "openssl-libs",
            "PERL_AUTODIE": "perl-autodie",
            "PERL_FILE_PATH": "perl-File-Path",
            "PERL_LWP_PROTO_HTTPS": "perl-LWP-Protocol-https",
            "PERL_SYS_SYSLOG": "perl-Sys-Syslog",
            "PYTHON_SIMPLEJSON": "python2-simplejson",
            "PROCPS": "procps-ng",
            "UDEV": "systemd",
        },
        systemd_lib="usr/lib/systemd/system",
        file_ext="rpm",
        initramfs_flavor="mkinitrd",
        builder=defs.Builder(
            alias="centos8",
            base_image="centos:8",
            branch="centos/8",
            kernel_package="kernel-core",
            utf8_locale="C.utf8",
        ),
    ),
    defs.VariantUpdate(
        name="CENTOS7",
        descr="CentOS 7.x",
        parent="CENTOS8",
        detect=defs.Detect(
            filename="/etc/redhat-release",
            regex=re.compile(r"^ (?: CentOS | Virtuozzo ) \s .* \s 7 \.", re.X),
            os_id="centos",
            os_version_regex=re.compile(r"^7(?:$|\.[0-9])"),
        ),
        updates={
            "commands": {
                "package": {
                    "install": [
                        "yum",
                        "--enablerepo=storpool-contrib",
                        "install",
                        "-q",
                        "-y",
                    ],
                },
                "pkgfile": {
                    "install": [
                        """
unset to_install to_reinstall
for f in $packages; do
    package="$(rpm -qp "$f")"
    if rpm -q -- "$package"; then
        to_reinstall="$to_reinstall ./$f"
    else
        to_install="$to_install ./$f"
    fi
done

if [ -n "$to_install" ]; then
    yum install -y --enablerepo=storpool-contrib --setopt=localpkg_gpgcheck=0 -- $to_install
fi
if [ -n "$to_reinstall" ]; then
    yum reinstall -y --enablerepo=storpool-contrib --setopt=localpkg_gpgcheck=0 -- $to_reinstall
fi
""",  # noqa: E501  pylint: disable=line-too-long
                    ],
                },
            },
            "builder": {
                "alias": "centos7",
                "base_image": "centos:7",
                "branch": "centos/7",
                "kernel_package": "kernel",
                "utf8_locale": "C",
            },
        },
    ),
    defs.VariantUpdate(
        name="CENTOS6",
        descr="CentOS 6.x",
        parent="CENTOS7",
        detect=defs.Detect(
            filename="/etc/redhat-release",
            regex=re.compile(r"^ CentOS \s .* \s 6 \.", re.X),
            os_id="centos",
            os_version_regex=re.compile(r"^6(?:$|\.[0-9])"),
        ),
        updates={
            "min_sys_python": "2.6",
            "package": {
                "KMOD": "module-init-tools",
                "LIBCGROUP": "libcgroup",
                "LIBUDEV": "libudev",
                "OPENSSL": "openssl",
                "PERL_AUTODIE": "perl",
                "PERL_FILE_PATH": "perl",
                "PERL_LWP_PROTO_HTTPS": "perl",
                "PERL_SYS_SYSLOG": "perl",
                "PYTHON_SIMPLEJSON": "python-simplejson",
                "PROCPS": "procps",
                "UDEV": "udev",
            },
            "builder": {
                "alias": "centos6",
                "base_image": "centos:6",
                "branch": "centos/6",
            },
        },
    ),
    defs.VariantUpdate(
        name="ORACLE7",
        descr="Oracle Linux 7.x",
        parent="CENTOS7",
        detect=defs.Detect(
            filename="/etc/oracle-release",
            regex=re.compile(r"^ Oracle \s+ Linux \s .* \s 7 \.", re.X),
            os_id="ol",
            os_version_regex=re.compile(r"^7(?:$|\.[0-9])"),
        ),
        updates={
            "builder": {
                "alias": "oracle7",
                "base_image": "IGNORE",
                "branch": "",
            },
        },
    ),
    defs.VariantUpdate(
        name="RHEL8",
        descr="RedHat Enterprise Linux 8.x",
        parent="CENTOS8",
        detect=defs.Detect(
            filename="/etc/redhat-release",
            regex=re.compile(
                r"^ Red \s+ Hat \s+ Enterprise \s+ Linux \s .* "
                r"\s 8 \. (?: [4-9] | [1-9][0-9] )",
                re.X,
            ),
            os_id="rhel",
            os_version_regex=re.compile(r"^8(?:$|\.[4-9]|\.[1-9][0-9])"),
        ),
        updates={
            "commands": {
                "package": {
                    "install": [
                        "dnf",
                        "--enablerepo=storpool-contrib",
                        "--enablerepo=codeready-builder-for-rhel-8-x86_64-rpms",
                        "install",
                        "-q",
                        "-y",
                        "--",
                    ]
                },
                "pkgfile": {
                    "install": [
                        "sh",
                        "-c",
                        """
unset to_install to_reinstall
for f in $packages; do
    package="$(rpm -qp "$f")"
    if rpm -q -- "$package"; then
        to_reinstall="$to_reinstall ./$f"
    else
        to_install="$to_install ./$f"
    fi
done

if [ -n "$to_install" ]; then
    dnf install -y --enablerepo=storpool-contrib,codeready-builder-for-rhel-8-x86_64-rpms --setopt=localpkg_gpgcheck=0 -- $to_install
fi
if [ -n "$to_reinstall" ]; then
    dnf reinstall -y --enablerepo=storpool-contrib,codeready-builder-for-rhel-8-x86_64-rpms --setopt=localpkg_gpgcheck=0 -- $to_reinstall
fi
""",  # noqa: E501  pylint: disable=line-too-long
                    ]
                },
            },
            "builder": {
                "alias": "rhel8",
                "base_image": "redhat/ubi8:reg",
                "branch": "",
            },
        },
    ),
    defs.VariantUpdate(
        name="ROCKY8",
        descr="Rocky Linux 8.x",
        parent="CENTOS8",
        detect=defs.Detect(
            filename="/etc/redhat-release",
            regex=re.compile(
                r"^ Rocky \s+ Linux \s .* \s 8 \. (?: [4-9] | [1-9][0-9] )",
                re.X,
            ),
            os_id="rocky",
            os_version_regex=re.compile(r"^8(?:$|\.[4-9]|\.[1-9][0-9])"),
        ),
        updates={
            "builder": {
                "alias": "rocky8",
                "base_image": "rockylinux/rockylinux:8",
                "branch": "",
            },
        },
    ),
    defs.VariantUpdate(
        name="ALMA8",
        descr="AlmaLinux 8.x",
        parent="CENTOS8",
        detect=defs.Detect(
            filename="/etc/redhat-release",
            regex=re.compile(r"^ AlmaLinux \s .* \s 8 \. (?: [4-9] | [1-9][0-9] )", re.X),
            os_id="alma",
            os_version_regex=re.compile(r"^8(?:$|\.[4-9]|\.[1-9][0-9])"),
        ),
        updates={
            "builder": {
                "alias": "alma8",
                "base_image": "almalinux/almalinux:8",
                "branch": "",
            },
        },
    ),
]  # type: (List[Union[defs.Variant, defs.VariantUpdate]])

VARIANTS = {}  # type: Dict[Text, defs.Variant]

DETECT_ORDER = []  # type: List[defs.Variant]


def update_namedtuple(data, updates):
    # type: (T, Dict[str, Any]) -> T
    """Create a new named tuple with some updated values."""
    if not updates:
        return data
    fields = getattr(data, "_fields")  # type: List[str]

    newv = dict((name, getattr(data, name)) for name in fields)
    prefix = "Internal error: could not update {newv} with {updates}".format(
        newv=newv, updates=updates
    )

    for name, value in updates.items():
        if name not in newv:
            raise defs.VariantConfigError(
                "{prefix}: unexpected field {name}".format(prefix=prefix, name=name)
            )
        orig = newv[name]

        def check_type(
            name,  # type: str
            orig,  # type: Any
            expected,  # type: Union[Type[Any], Tuple[Type[Any], ...]]
            tname,  # type: str
        ):  # type: (...) -> None
            """Make sure the `orig` value is of the expected type."""
            if not isinstance(orig, expected):
                raise defs.VariantConfigError(
                    "{prefix}: {name} is not a {tname}".format(
                        prefix=prefix, name=name, tname=tname
                    )
                )

        if isinstance(value, dict):
            if isinstance(orig, tuple):
                newv[name] = update_namedtuple(orig, value)
            elif isinstance(orig, dict):
                newv[name].update(value)
            else:
                raise defs.VariantConfigError(
                    "{prefix}: {name} is not a tuple".format(prefix=prefix, name=name)
                )
        elif isinstance(
            value,
            (
                str,
                defs.TextType,
            ),
        ):
            check_type(name, orig, (str, defs.TextType), "string")
            newv[name] = value
        elif type(value).__name__ == "PosixPath":
            if orig is not None:
                check_type(name, orig, type(value), "path")
            newv[name] = value
        elif isinstance(value, list):
            check_type(name, orig, list, "list")
            newv[name] = value
        else:
            raise defs.VariantConfigError(
                "{prefix}: weird {tname} update for {name}".format(
                    prefix=prefix,
                    tname=type(value).__name__,
                    name=name,
                )
            )

    updated = type(data)(**newv)
    return updated


def merge_into_parent(cfg, parent, child):
    # type: (defs.Config, defs.Variant, defs.VariantUpdate) -> defs.Variant
    """Merge a child's definitions into the parent."""
    cfg.diag("- merging {child} into {parent}".format(child=child.name, parent=parent.name))
    return update_namedtuple(
        defs.Variant(
            name=child.name,
            descr=child.descr,
            parent=parent.name,
            family=parent.family,
            detect=child.detect,
            commands=parent.commands,
            repo=parent.repo,
            package=dict(parent.package),
            min_sys_python=parent.min_sys_python,
            systemd_lib=parent.systemd_lib,
            file_ext=parent.file_ext,
            initramfs_flavor=parent.initramfs_flavor,
            builder=parent.builder,
        ),
        child.updates,
    )


def build_variants(cfg):
    # type: (defs.Config) -> None
    """Build the variant definitions from the parent/child relations."""
    if VARIANTS:
        assert len(VARIANTS) == len(_VARIANT_DEF)
        assert DETECT_ORDER
        assert len(DETECT_ORDER) == len(_VARIANT_DEF)
        return
    assert not DETECT_ORDER

    cfg.diag("Building the list of variants")
    order = []  # type: List[Text]
    for var in _VARIANT_DEF:
        if isinstance(var, defs.VariantUpdate):
            current = merge_into_parent(cfg, VARIANTS[var.parent], var)
        else:
            current = var

        VARIANTS[var.name] = current
        order.append(var.name)

    order.reverse()
    DETECT_ORDER.extend([VARIANTS[name] for name in order])
    cfg.diag("Detect order: {names}".format(names=" ".join(var.name for var in DETECT_ORDER)))
