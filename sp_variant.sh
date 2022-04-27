#!/bin/sh
#
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

set -e

usage()
{
	cat <<'EOUSAGE'
Usage:  sp_variant command run [-N] category.command [arg...]
	sp_variant detect
	sp_variant features
	sp_variant repo add
	sp_variant show all
	sp_variant show current
	sp_variant show VARIANT
EOUSAGE
}

detect_from_os_release()
{
	if [ ! -r /etc/os-release ]; then
		return
	fi

	local output="$(unset ID VERSION_ID; . /etc/os-release; printf -- '%s::%s\n' "$ID" "$VERSION_ID")"
	local os_id="${output%%::*}" version_id="${output#*::}"
	if [ -z "$os_id" ] || [ -z "$version_id" ]; then
		return
	fi
	
	if [ "$os_id" = 'alma' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^8($|\.[4-9]|\.[1-9][0-9])'; then
		printf -- '%s\n' 'ALMA8'
		return
	fi
	
	if [ "$os_id" = 'centos' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^6($|\.[0-9])'; then
		printf -- '%s\n' 'CENTOS6'
		return
	fi
	
	if [ "$os_id" = 'centos' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^7($|\.[0-9])'; then
		printf -- '%s\n' 'CENTOS7'
		return
	fi
	
	if [ "$os_id" = 'centos' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^8($|\.[4-9]|\.[1-9][0-9])'; then
		printf -- '%s\n' 'CENTOS8'
		return
	fi
	
	if [ "$os_id" = 'debian' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^9$'; then
		printf -- '%s\n' 'DEBIAN9'
		return
	fi
	
	if [ "$os_id" = 'debian' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^10$'; then
		printf -- '%s\n' 'DEBIAN10'
		return
	fi
	
	if [ "$os_id" = 'debian' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^11$'; then
		printf -- '%s\n' 'DEBIAN11'
		return
	fi
	
	if [ "$os_id" = 'debian' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^12$'; then
		printf -- '%s\n' 'DEBIAN12'
		return
	fi
	
	if [ "$os_id" = 'ol' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^7($|\.[0-9])'; then
		printf -- '%s\n' 'ORACLE7'
		return
	fi
	
	if [ "$os_id" = 'rhel' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^8($|\.[4-9]|\.[1-9][0-9])'; then
		printf -- '%s\n' 'RHEL8'
		return
	fi
	
	if [ "$os_id" = 'rocky' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^8($|\.[4-9]|\.[1-9][0-9])'; then
		printf -- '%s\n' 'ROCKY8'
		return
	fi
	
	if [ "$os_id" = 'ubuntu' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^16\.04$'; then
		printf -- '%s\n' 'UBUNTU1604'
		return
	fi
	
	if [ "$os_id" = 'ubuntu' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^18\.04$'; then
		printf -- '%s\n' 'UBUNTU1804'
		return
	fi
	
	if [ "$os_id" = 'ubuntu' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^20\.04$'; then
		printf -- '%s\n' 'UBUNTU2004'
		return
	fi
	
	if [ "$os_id" = 'ubuntu' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^21\.10$'; then
		printf -- '%s\n' 'UBUNTU2110'
		return
	fi
	
	if [ "$os_id" = 'ubuntu' ] && printf -- '%s\n' "$version_id" | grep -Eqe '^22\.04$'; then
		printf -- '%s\n' 'UBUNTU2204'
		return
	fi
	
}

cmd_detect()
{
	local res

	if [ "$#" -ne 0 ]; then
		usage 1>&2
		exit 1
	fi

	res="$(detect_from_os_release)"
	if [ -n "$res" ]; then
		printf -- '%s\n' "$res"
		return
	fi

	
	if [ -r '/etc/redhat-release' ] && grep -Eqe '^AlmaLinux[[:space:]].*[[:space:]]8\.([4-9]|[1-9][0-9])' -- '/etc/redhat-release'; then
		printf -- '%s\n' 'ALMA8'
		return
	fi
	
	if [ -r '/etc/redhat-release' ] && grep -Eqe '^Rocky[[:space:]]+Linux[[:space:]].*[[:space:]]8\.([4-9]|[1-9][0-9])' -- '/etc/redhat-release'; then
		printf -- '%s\n' 'ROCKY8'
		return
	fi
	
	if [ -r '/etc/redhat-release' ] && grep -Eqe '^Red[[:space:]]+Hat[[:space:]]+Enterprise[[:space:]]+Linux[[:space:]].*[[:space:]]8\.([4-9]|[1-9][0-9])' -- '/etc/redhat-release'; then
		printf -- '%s\n' 'RHEL8'
		return
	fi
	
	if [ -r '/etc/oracle-release' ] && grep -Eqe '^Oracle[[:space:]]+Linux[[:space:]].*[[:space:]]7\.' -- '/etc/oracle-release'; then
		printf -- '%s\n' 'ORACLE7'
		return
	fi
	
	if [ -r '/etc/redhat-release' ] && grep -Eqe '^CentOS[[:space:]].*[[:space:]]6\.' -- '/etc/redhat-release'; then
		printf -- '%s\n' 'CENTOS6'
		return
	fi
	
	if [ -r '/etc/redhat-release' ] && grep -Eqe '^(CentOS|Virtuozzo)[[:space:]].*[[:space:]]7\.' -- '/etc/redhat-release'; then
		printf -- '%s\n' 'CENTOS7'
		return
	fi
	
	if [ -r '/etc/redhat-release' ] && grep -Eqe '^CentOS[[:space:]].*[[:space:]]8\.([3-9]|([12][0-9]))' -- '/etc/redhat-release'; then
		printf -- '%s\n' 'CENTOS8'
		return
	fi
	
	if [ -r '/etc/os-release' ] && grep -Eqe '^PRETTY_NAME=.*Ubuntu[[:space:]]+16\.04' -- '/etc/os-release'; then
		printf -- '%s\n' 'UBUNTU1604'
		return
	fi
	
	if [ -r '/etc/os-release' ] && grep -Eqe '^PRETTY_NAME=.*Ubuntu[[:space:]]+18\.04' -- '/etc/os-release'; then
		printf -- '%s\n' 'UBUNTU1804'
		return
	fi
	
	if [ -r '/etc/os-release' ] && grep -Eqe '^PRETTY_NAME=.*(Ubuntu[[:space:]]+20\.04|Mint[[:space:]]+20)' -- '/etc/os-release'; then
		printf -- '%s\n' 'UBUNTU2004'
		return
	fi
	
	if [ -r '/etc/os-release' ] && grep -Eqe '^PRETTY_NAME=.*(Ubuntu[[:space:]]+21\.10|Mint[[:space:]]+21)' -- '/etc/os-release'; then
		printf -- '%s\n' 'UBUNTU2110'
		return
	fi
	
	if [ -r '/etc/os-release' ] && grep -Eqe '^PRETTY_NAME=.*(Ubuntu[[:space:]]+22\.04|Mint[[:space:]]+22)' -- '/etc/os-release'; then
		printf -- '%s\n' 'UBUNTU2204'
		return
	fi
	
	if [ -r '/etc/os-release' ] && grep -Eqe '^PRETTY_NAME=.*Debian[[:space:]]+GNU/Linux[[:space:]]+(stretch|9)([[:space:]]|/)' -- '/etc/os-release'; then
		printf -- '%s\n' 'DEBIAN9'
		return
	fi
	
	if [ -r '/etc/os-release' ] && grep -Eqe '^PRETTY_NAME=.*Debian[[:space:]]+GNU/Linux[[:space:]]+(buster|10)([[:space:]]|/)' -- '/etc/os-release'; then
		printf -- '%s\n' 'DEBIAN10'
		return
	fi
	
	if [ -r '/etc/os-release' ] && grep -Eqe '^PRETTY_NAME=.*Debian[[:space:]]+GNU/Linux[[:space:]]+(bullseye|11)([[:space:]]|/)' -- '/etc/os-release'; then
		printf -- '%s\n' 'DEBIAN11'
		return
	fi
	
	if [ -r '/etc/os-release' ] && grep -Eqe '^PRETTY_NAME=.*Debian[[:space:]]+GNU/Linux[[:space:]]+(bookworm|12)([[:space:]]|/)' -- '/etc/os-release'; then
		printf -- '%s\n' 'DEBIAN12'
		return
	fi
	

	echo "Could not detect the current host's build variant" 1>&2
	exit 1
}


show_ALMA8()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "alma8",
    "base_image": "almalinux/almalinux:8",
    "branch": "",
    "kernel_package": "kernel-core",
    "utf8_locale": "C.utf8"
  },
  "commands": {
    "package": {
      "install": [
        "dnf",
        "--enablerepo=storpool-contrib",
        "--enablerepo=powertools",
        "install",
        "-q",
        "-y",
        "--"
      ],
      "list_all": [
        "rpm",
        "-qa",
        "--qf",
        "%{Name}\\t%{EVR}\\t%{Arch}\\tii\\n",
        "--"
      ],
      "purge": [
        "yum",
        "remove",
        "-q",
        "-y",
        "--"
      ],
      "remove": [
        "yum",
        "remove",
        "-q",
        "-y",
        "--"
      ],
      "remove_impl": [
        "rpm",
        "-e",
        "--"
      ],
      "update_db": [
        "true"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "rpm -qpR -- \"$pkg\""
      ],
      "install": [
        "sh",
        "-c",
        "\nunset to_install to_reinstall\nfor f in $packages; do\n    package=\"$(rpm -qp \"$f\")\"\n    if rpm -q -- \"$package\"; then\n        to_reinstall=\"$to_reinstall ./$f\"\n    else\n        to_install=\"$to_install ./$f\"\n    fi\ndone\n\nif [ -n \"$to_install\" ]; then\n    dnf install -y --enablerepo=storpool-contrib,powertools --setopt=localpkg_gpgcheck=0 -- $to_install\nfi\nif [ -n \"$to_reinstall\" ]; then\n    dnf reinstall -y --enablerepo=storpool-contrib,powertools --setopt=localpkg_gpgcheck=0 -- $to_reinstall\nfi\n"
      ]
    }
  },
  "descr": "AlmaLinux 8.x",
  "detect": {
    "filename": "/etc/redhat-release",
    "os_id": "alma",
    "os_version_regex": "^8(?:$|\\.[4-9]|\\.[1-9][0-9])",
    "regex": "^ AlmaLinux \\s .* \\s 8 \\. (?: [4-9] | [1-9][0-9] )"
  },
  "family": "redhat",
  "file_ext": "rpm",
  "initramfs_flavor": "mkinitrd",
  "min_sys_python": "2.7",
  "name": "ALMA8",
  "package": {
    "KMOD": "kmod",
    "LIBCGROUP": "libcgroup-tools",
    "LIBUDEV": "systemd-libs",
    "OPENSSL": "openssl-libs",
    "PERL_AUTODIE": "perl-autodie",
    "PERL_FILE_PATH": "perl-File-Path",
    "PERL_LWP_PROTO_HTTPS": "perl-LWP-Protocol-https",
    "PERL_SYS_SYSLOG": "perl-Sys-Syslog",
    "PROCPS": "procps-ng",
    "PYTHON_SIMPLEJSON": "python2-simplejson",
    "UDEV": "systemd"
  },
  "parent": "CENTOS8",
  "repo": {
    "keyring": "redhat/repo/RPM-GPG-KEY-StorPool",
    "yumdef": "redhat/repo/storpool-centos.repo"
  },
  "systemd_lib": "usr/lib/systemd/system"
}
EOVARIANT_JSON
}

show_CENTOS6()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "centos6",
    "base_image": "centos:6",
    "branch": "centos/6",
    "kernel_package": "kernel",
    "utf8_locale": "C"
  },
  "commands": {
    "package": {
      "install": [
        "yum",
        "--enablerepo=storpool-contrib",
        "install",
        "-q",
        "-y"
      ],
      "list_all": [
        "rpm",
        "-qa",
        "--qf",
        "%{Name}\\t%{EVR}\\t%{Arch}\\tii\\n",
        "--"
      ],
      "purge": [
        "yum",
        "remove",
        "-q",
        "-y",
        "--"
      ],
      "remove": [
        "yum",
        "remove",
        "-q",
        "-y",
        "--"
      ],
      "remove_impl": [
        "rpm",
        "-e",
        "--"
      ],
      "update_db": [
        "true"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "rpm -qpR -- \"$pkg\""
      ],
      "install": [
        "\nunset to_install to_reinstall\nfor f in $packages; do\n    package=\"$(rpm -qp \"$f\")\"\n    if rpm -q -- \"$package\"; then\n        to_reinstall=\"$to_reinstall ./$f\"\n    else\n        to_install=\"$to_install ./$f\"\n    fi\ndone\n\nif [ -n \"$to_install\" ]; then\n    yum install -y --enablerepo=storpool-contrib --setopt=localpkg_gpgcheck=0 -- $to_install\nfi\nif [ -n \"$to_reinstall\" ]; then\n    yum reinstall -y --enablerepo=storpool-contrib --setopt=localpkg_gpgcheck=0 -- $to_reinstall\nfi\n"
      ]
    }
  },
  "descr": "CentOS 6.x",
  "detect": {
    "filename": "/etc/redhat-release",
    "os_id": "centos",
    "os_version_regex": "^6(?:$|\\.[0-9])",
    "regex": "^ CentOS \\s .* \\s 6 \\."
  },
  "family": "redhat",
  "file_ext": "rpm",
  "initramfs_flavor": "mkinitrd",
  "min_sys_python": "2.6",
  "name": "CENTOS6",
  "package": {
    "KMOD": "module-init-tools",
    "LIBCGROUP": "libcgroup",
    "LIBUDEV": "libudev",
    "OPENSSL": "openssl",
    "PERL_AUTODIE": "perl",
    "PERL_FILE_PATH": "perl",
    "PERL_LWP_PROTO_HTTPS": "perl",
    "PERL_SYS_SYSLOG": "perl",
    "PROCPS": "procps",
    "PYTHON_SIMPLEJSON": "python-simplejson",
    "UDEV": "udev"
  },
  "parent": "CENTOS7",
  "repo": {
    "keyring": "redhat/repo/RPM-GPG-KEY-StorPool",
    "yumdef": "redhat/repo/storpool-centos.repo"
  },
  "systemd_lib": "usr/lib/systemd/system"
}
EOVARIANT_JSON
}

show_CENTOS7()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "centos7",
    "base_image": "centos:7",
    "branch": "centos/7",
    "kernel_package": "kernel",
    "utf8_locale": "C"
  },
  "commands": {
    "package": {
      "install": [
        "yum",
        "--enablerepo=storpool-contrib",
        "install",
        "-q",
        "-y"
      ],
      "list_all": [
        "rpm",
        "-qa",
        "--qf",
        "%{Name}\\t%{EVR}\\t%{Arch}\\tii\\n",
        "--"
      ],
      "purge": [
        "yum",
        "remove",
        "-q",
        "-y",
        "--"
      ],
      "remove": [
        "yum",
        "remove",
        "-q",
        "-y",
        "--"
      ],
      "remove_impl": [
        "rpm",
        "-e",
        "--"
      ],
      "update_db": [
        "true"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "rpm -qpR -- \"$pkg\""
      ],
      "install": [
        "\nunset to_install to_reinstall\nfor f in $packages; do\n    package=\"$(rpm -qp \"$f\")\"\n    if rpm -q -- \"$package\"; then\n        to_reinstall=\"$to_reinstall ./$f\"\n    else\n        to_install=\"$to_install ./$f\"\n    fi\ndone\n\nif [ -n \"$to_install\" ]; then\n    yum install -y --enablerepo=storpool-contrib --setopt=localpkg_gpgcheck=0 -- $to_install\nfi\nif [ -n \"$to_reinstall\" ]; then\n    yum reinstall -y --enablerepo=storpool-contrib --setopt=localpkg_gpgcheck=0 -- $to_reinstall\nfi\n"
      ]
    }
  },
  "descr": "CentOS 7.x",
  "detect": {
    "filename": "/etc/redhat-release",
    "os_id": "centos",
    "os_version_regex": "^7(?:$|\\.[0-9])",
    "regex": "^ (?: CentOS | Virtuozzo ) \\s .* \\s 7 \\."
  },
  "family": "redhat",
  "file_ext": "rpm",
  "initramfs_flavor": "mkinitrd",
  "min_sys_python": "2.7",
  "name": "CENTOS7",
  "package": {
    "KMOD": "kmod",
    "LIBCGROUP": "libcgroup-tools",
    "LIBUDEV": "systemd-libs",
    "OPENSSL": "openssl-libs",
    "PERL_AUTODIE": "perl-autodie",
    "PERL_FILE_PATH": "perl-File-Path",
    "PERL_LWP_PROTO_HTTPS": "perl-LWP-Protocol-https",
    "PERL_SYS_SYSLOG": "perl-Sys-Syslog",
    "PROCPS": "procps-ng",
    "PYTHON_SIMPLEJSON": "python2-simplejson",
    "UDEV": "systemd"
  },
  "parent": "CENTOS8",
  "repo": {
    "keyring": "redhat/repo/RPM-GPG-KEY-StorPool",
    "yumdef": "redhat/repo/storpool-centos.repo"
  },
  "systemd_lib": "usr/lib/systemd/system"
}
EOVARIANT_JSON
}

show_CENTOS8()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "centos8",
    "base_image": "centos:8",
    "branch": "centos/8",
    "kernel_package": "kernel-core",
    "utf8_locale": "C.utf8"
  },
  "commands": {
    "package": {
      "install": [
        "dnf",
        "--enablerepo=storpool-contrib",
        "--enablerepo=powertools",
        "install",
        "-q",
        "-y",
        "--"
      ],
      "list_all": [
        "rpm",
        "-qa",
        "--qf",
        "%{Name}\\t%{EVR}\\t%{Arch}\\tii\\n",
        "--"
      ],
      "purge": [
        "yum",
        "remove",
        "-q",
        "-y",
        "--"
      ],
      "remove": [
        "yum",
        "remove",
        "-q",
        "-y",
        "--"
      ],
      "remove_impl": [
        "rpm",
        "-e",
        "--"
      ],
      "update_db": [
        "true"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "rpm -qpR -- \"$pkg\""
      ],
      "install": [
        "sh",
        "-c",
        "\nunset to_install to_reinstall\nfor f in $packages; do\n    package=\"$(rpm -qp \"$f\")\"\n    if rpm -q -- \"$package\"; then\n        to_reinstall=\"$to_reinstall ./$f\"\n    else\n        to_install=\"$to_install ./$f\"\n    fi\ndone\n\nif [ -n \"$to_install\" ]; then\n    dnf install -y --enablerepo=storpool-contrib,powertools --setopt=localpkg_gpgcheck=0 -- $to_install\nfi\nif [ -n \"$to_reinstall\" ]; then\n    dnf reinstall -y --enablerepo=storpool-contrib,powertools --setopt=localpkg_gpgcheck=0 -- $to_reinstall\nfi\n"
      ]
    }
  },
  "descr": "CentOS 8.x",
  "detect": {
    "filename": "/etc/redhat-release",
    "os_id": "centos",
    "os_version_regex": "^8(?:$|\\.[4-9]|\\.[1-9][0-9])",
    "regex": "^ CentOS \\s .* \\s 8 \\. (?: [3-9] | (?: [12][0-9] ) )"
  },
  "family": "redhat",
  "file_ext": "rpm",
  "initramfs_flavor": "mkinitrd",
  "min_sys_python": "2.7",
  "name": "CENTOS8",
  "package": {
    "KMOD": "kmod",
    "LIBCGROUP": "libcgroup-tools",
    "LIBUDEV": "systemd-libs",
    "OPENSSL": "openssl-libs",
    "PERL_AUTODIE": "perl-autodie",
    "PERL_FILE_PATH": "perl-File-Path",
    "PERL_LWP_PROTO_HTTPS": "perl-LWP-Protocol-https",
    "PERL_SYS_SYSLOG": "perl-Sys-Syslog",
    "PROCPS": "procps-ng",
    "PYTHON_SIMPLEJSON": "python2-simplejson",
    "UDEV": "systemd"
  },
  "parent": "",
  "repo": {
    "keyring": "redhat/repo/RPM-GPG-KEY-StorPool",
    "yumdef": "redhat/repo/storpool-centos.repo"
  },
  "systemd_lib": "usr/lib/systemd/system"
}
EOVARIANT_JSON
}

show_DEBIAN9()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "debian9",
    "base_image": "debian:stretch",
    "branch": "debian/stretch",
    "kernel_package": "linux-headers",
    "utf8_locale": "C.UTF-8"
  },
  "commands": {
    "package": {
      "install": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "--no-install-recommends",
        "install",
        "--"
      ],
      "list_all": [
        "dpkg-query",
        "-W",
        "-f",
        "${Package}\\t${Version}\\t${Architecture}\\t${db:Status-Abbrev}\\n",
        "--"
      ],
      "purge": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "purge",
        "--"
      ],
      "remove": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "remove",
        "--"
      ],
      "remove_impl": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "dpkg",
        "-r",
        "--"
      ],
      "update_db": [
        "apt-get",
        "-q",
        "-y",
        "update"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "dpkg-deb -f -- \"$pkg\" 'Depends' | sed -e 's/ *, */,/g' | tr ',' \"\\n\""
      ],
      "install": [
        "sh",
        "-c",
        "env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages"
      ]
    }
  },
  "descr": "Debian 9.x (stretch)",
  "detect": {
    "filename": "/etc/os-release",
    "os_id": "debian",
    "os_version_regex": "^9$",
    "regex": "^\n                    PRETTY_NAME= .*\n                    Debian \\s+ GNU/Linux \\s+\n                    (?: stretch | 9 ) (?: \\s | / )\n                "
  },
  "family": "debian",
  "file_ext": "deb",
  "initramfs_flavor": "update-initramfs",
  "min_sys_python": "2.7",
  "name": "DEBIAN9",
  "package": {
    "BINDINGS_PYTHON": "python",
    "BINDINGS_PYTHON_CONFGET": "python-confget",
    "BINDINGS_PYTHON_SIMPLEJSON": "python-simplejson",
    "CGROUP": "cgroup-tools",
    "CPUPOWER": "linux-cpupower",
    "LIBSSL": "libssl1.1",
    "MCELOG": "mcelog"
  },
  "parent": "DEBIAN10",
  "repo": {
    "codename": "stretch",
    "keyring": "debian/repo/storpool-keyring.gpg",
    "req_packages": [
      "apt-transport-https",
      "ca-certificates"
    ],
    "sources": "debian/repo/storpool.sources",
    "vendor": "debian"
  },
  "systemd_lib": "lib/systemd/system"
}
EOVARIANT_JSON
}

show_DEBIAN10()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "debian10",
    "base_image": "debian:buster",
    "branch": "debian/buster",
    "kernel_package": "linux-headers",
    "utf8_locale": "C.UTF-8"
  },
  "commands": {
    "package": {
      "install": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "--no-install-recommends",
        "install",
        "--"
      ],
      "list_all": [
        "dpkg-query",
        "-W",
        "-f",
        "${Package}\\t${Version}\\t${Architecture}\\t${db:Status-Abbrev}\\n",
        "--"
      ],
      "purge": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "purge",
        "--"
      ],
      "remove": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "remove",
        "--"
      ],
      "remove_impl": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "dpkg",
        "-r",
        "--"
      ],
      "update_db": [
        "apt-get",
        "-q",
        "-y",
        "update"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "dpkg-deb -f -- \"$pkg\" 'Depends' | sed -e 's/ *, */,/g' | tr ',' \"\\n\""
      ],
      "install": [
        "sh",
        "-c",
        "env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages"
      ]
    }
  },
  "descr": "Debian 10.x (buster)",
  "detect": {
    "filename": "/etc/os-release",
    "os_id": "debian",
    "os_version_regex": "^10$",
    "regex": "^\n                    PRETTY_NAME= .*\n                    Debian \\s+ GNU/Linux \\s+\n                    (?: buster | 10 ) (?: \\s | / )\n                "
  },
  "family": "debian",
  "file_ext": "deb",
  "initramfs_flavor": "update-initramfs",
  "min_sys_python": "2.7",
  "name": "DEBIAN10",
  "package": {
    "BINDINGS_PYTHON": "python",
    "BINDINGS_PYTHON_CONFGET": "python-confget",
    "BINDINGS_PYTHON_SIMPLEJSON": "python-simplejson",
    "CGROUP": "cgroup-tools",
    "CPUPOWER": "linux-cpupower",
    "LIBSSL": "libssl1.1",
    "MCELOG": "mcelog"
  },
  "parent": "DEBIAN11",
  "repo": {
    "codename": "buster",
    "keyring": "debian/repo/storpool-keyring.gpg",
    "req_packages": [
      "ca-certificates"
    ],
    "sources": "debian/repo/storpool.sources",
    "vendor": "debian"
  },
  "systemd_lib": "lib/systemd/system"
}
EOVARIANT_JSON
}

show_DEBIAN11()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "debian11",
    "base_image": "debian:bullseye",
    "branch": "debian/bullseye",
    "kernel_package": "linux-headers",
    "utf8_locale": "C.UTF-8"
  },
  "commands": {
    "package": {
      "install": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "--no-install-recommends",
        "install",
        "--"
      ],
      "list_all": [
        "dpkg-query",
        "-W",
        "-f",
        "${Package}\\t${Version}\\t${Architecture}\\t${db:Status-Abbrev}\\n",
        "--"
      ],
      "purge": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "purge",
        "--"
      ],
      "remove": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "remove",
        "--"
      ],
      "remove_impl": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "dpkg",
        "-r",
        "--"
      ],
      "update_db": [
        "apt-get",
        "-q",
        "-y",
        "update"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "dpkg-deb -f -- \"$pkg\" 'Depends' | sed -e 's/ *, */,/g' | tr ',' \"\\n\""
      ],
      "install": [
        "sh",
        "-c",
        "env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages"
      ]
    }
  },
  "descr": "Debian 11.x (bullseye)",
  "detect": {
    "filename": "/etc/os-release",
    "os_id": "debian",
    "os_version_regex": "^11$",
    "regex": "^\n                    PRETTY_NAME= .*\n                    Debian \\s+ GNU/Linux \\s+\n                    (?: bullseye | 11 ) (?: \\s | / )\n                "
  },
  "family": "debian",
  "file_ext": "deb",
  "initramfs_flavor": "update-initramfs",
  "min_sys_python": "3.9",
  "name": "DEBIAN11",
  "package": {
    "BINDINGS_PYTHON": "python3",
    "BINDINGS_PYTHON_CONFGET": "python3-confget",
    "BINDINGS_PYTHON_SIMPLEJSON": "python3-simplejson",
    "CGROUP": "cgroup-tools",
    "CPUPOWER": "linux-cpupower",
    "LIBSSL": "libssl1.1",
    "MCELOG": "mcelog"
  },
  "parent": "DEBIAN12",
  "repo": {
    "codename": "bullseye",
    "keyring": "debian/repo/storpool-keyring.gpg",
    "req_packages": [
      "ca-certificates"
    ],
    "sources": "debian/repo/storpool.sources",
    "vendor": "debian"
  },
  "systemd_lib": "lib/systemd/system"
}
EOVARIANT_JSON
}

show_DEBIAN12()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "debian12",
    "base_image": "debian:unstable",
    "branch": "debian/unstable",
    "kernel_package": "linux-headers",
    "utf8_locale": "C.UTF-8"
  },
  "commands": {
    "package": {
      "install": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "--no-install-recommends",
        "install",
        "--"
      ],
      "list_all": [
        "dpkg-query",
        "-W",
        "-f",
        "${Package}\\t${Version}\\t${Architecture}\\t${db:Status-Abbrev}\\n",
        "--"
      ],
      "purge": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "purge",
        "--"
      ],
      "remove": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "remove",
        "--"
      ],
      "remove_impl": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "dpkg",
        "-r",
        "--"
      ],
      "update_db": [
        "apt-get",
        "-q",
        "-y",
        "update"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "dpkg-deb -f -- \"$pkg\" 'Depends' | sed -e 's/ *, */,/g' | tr ',' \"\\n\""
      ],
      "install": [
        "sh",
        "-c",
        "env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages"
      ]
    }
  },
  "descr": "Debian 12.x (bookworm/unstable)",
  "detect": {
    "filename": "/etc/os-release",
    "os_id": "debian",
    "os_version_regex": "^12$",
    "regex": "^\n                    PRETTY_NAME= .*\n                    Debian \\s+ GNU/Linux \\s+\n                    (?: bookworm | 12 ) (?: \\s | / )\n                "
  },
  "family": "debian",
  "file_ext": "deb",
  "initramfs_flavor": "update-initramfs",
  "min_sys_python": "3.9",
  "name": "DEBIAN12",
  "package": {
    "BINDINGS_PYTHON": "python3",
    "BINDINGS_PYTHON_CONFGET": "python3-confget",
    "BINDINGS_PYTHON_SIMPLEJSON": "python3-simplejson",
    "CGROUP": "cgroup-tools",
    "CPUPOWER": "linux-cpupower",
    "LIBSSL": "libssl1.1",
    "MCELOG": "mcelog"
  },
  "parent": "",
  "repo": {
    "codename": "unstable",
    "keyring": "debian/repo/storpool-keyring.gpg",
    "req_packages": [
      "ca-certificates"
    ],
    "sources": "debian/repo/storpool.sources",
    "vendor": "debian"
  },
  "systemd_lib": "lib/systemd/system"
}
EOVARIANT_JSON
}

show_ORACLE7()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "oracle7",
    "base_image": "IGNORE",
    "branch": "",
    "kernel_package": "kernel",
    "utf8_locale": "C"
  },
  "commands": {
    "package": {
      "install": [
        "yum",
        "--enablerepo=storpool-contrib",
        "install",
        "-q",
        "-y"
      ],
      "list_all": [
        "rpm",
        "-qa",
        "--qf",
        "%{Name}\\t%{EVR}\\t%{Arch}\\tii\\n",
        "--"
      ],
      "purge": [
        "yum",
        "remove",
        "-q",
        "-y",
        "--"
      ],
      "remove": [
        "yum",
        "remove",
        "-q",
        "-y",
        "--"
      ],
      "remove_impl": [
        "rpm",
        "-e",
        "--"
      ],
      "update_db": [
        "true"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "rpm -qpR -- \"$pkg\""
      ],
      "install": [
        "\nunset to_install to_reinstall\nfor f in $packages; do\n    package=\"$(rpm -qp \"$f\")\"\n    if rpm -q -- \"$package\"; then\n        to_reinstall=\"$to_reinstall ./$f\"\n    else\n        to_install=\"$to_install ./$f\"\n    fi\ndone\n\nif [ -n \"$to_install\" ]; then\n    yum install -y --enablerepo=storpool-contrib --setopt=localpkg_gpgcheck=0 -- $to_install\nfi\nif [ -n \"$to_reinstall\" ]; then\n    yum reinstall -y --enablerepo=storpool-contrib --setopt=localpkg_gpgcheck=0 -- $to_reinstall\nfi\n"
      ]
    }
  },
  "descr": "Oracle Linux 7.x",
  "detect": {
    "filename": "/etc/oracle-release",
    "os_id": "ol",
    "os_version_regex": "^7(?:$|\\.[0-9])",
    "regex": "^ Oracle \\s+ Linux \\s .* \\s 7 \\."
  },
  "family": "redhat",
  "file_ext": "rpm",
  "initramfs_flavor": "mkinitrd",
  "min_sys_python": "2.7",
  "name": "ORACLE7",
  "package": {
    "KMOD": "kmod",
    "LIBCGROUP": "libcgroup-tools",
    "LIBUDEV": "systemd-libs",
    "OPENSSL": "openssl-libs",
    "PERL_AUTODIE": "perl-autodie",
    "PERL_FILE_PATH": "perl-File-Path",
    "PERL_LWP_PROTO_HTTPS": "perl-LWP-Protocol-https",
    "PERL_SYS_SYSLOG": "perl-Sys-Syslog",
    "PROCPS": "procps-ng",
    "PYTHON_SIMPLEJSON": "python2-simplejson",
    "UDEV": "systemd"
  },
  "parent": "CENTOS7",
  "repo": {
    "keyring": "redhat/repo/RPM-GPG-KEY-StorPool",
    "yumdef": "redhat/repo/storpool-centos.repo"
  },
  "systemd_lib": "usr/lib/systemd/system"
}
EOVARIANT_JSON
}

show_RHEL8()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "rhel8",
    "base_image": "redhat/ubi8:reg",
    "branch": "",
    "kernel_package": "kernel-core",
    "utf8_locale": "C.utf8"
  },
  "commands": {
    "package": {
      "install": [
        "dnf",
        "--enablerepo=storpool-contrib",
        "--enablerepo=codeready-builder-for-rhel-8-x86_64-rpms",
        "install",
        "-q",
        "-y",
        "--"
      ],
      "list_all": [
        "rpm",
        "-qa",
        "--qf",
        "%{Name}\\t%{EVR}\\t%{Arch}\\tii\\n",
        "--"
      ],
      "purge": [
        "yum",
        "remove",
        "-q",
        "-y",
        "--"
      ],
      "remove": [
        "yum",
        "remove",
        "-q",
        "-y",
        "--"
      ],
      "remove_impl": [
        "rpm",
        "-e",
        "--"
      ],
      "update_db": [
        "true"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "rpm -qpR -- \"$pkg\""
      ],
      "install": [
        "sh",
        "-c",
        "\nunset to_install to_reinstall\nfor f in $packages; do\n    package=\"$(rpm -qp \"$f\")\"\n    if rpm -q -- \"$package\"; then\n        to_reinstall=\"$to_reinstall ./$f\"\n    else\n        to_install=\"$to_install ./$f\"\n    fi\ndone\n\nif [ -n \"$to_install\" ]; then\n    dnf install -y --enablerepo=storpool-contrib,codeready-builder-for-rhel-8-x86_64-rpms --setopt=localpkg_gpgcheck=0 -- $to_install\nfi\nif [ -n \"$to_reinstall\" ]; then\n    dnf reinstall -y --enablerepo=storpool-contrib,codeready-builder-for-rhel-8-x86_64-rpms --setopt=localpkg_gpgcheck=0 -- $to_reinstall\nfi\n"
      ]
    }
  },
  "descr": "RedHat Enterprise Linux 8.x",
  "detect": {
    "filename": "/etc/redhat-release",
    "os_id": "rhel",
    "os_version_regex": "^8(?:$|\\.[4-9]|\\.[1-9][0-9])",
    "regex": "^ Red \\s+ Hat \\s+ Enterprise \\s+ Linux \\s .* \\s 8 \\. (?: [4-9] | [1-9][0-9] )"
  },
  "family": "redhat",
  "file_ext": "rpm",
  "initramfs_flavor": "mkinitrd",
  "min_sys_python": "2.7",
  "name": "RHEL8",
  "package": {
    "KMOD": "kmod",
    "LIBCGROUP": "libcgroup-tools",
    "LIBUDEV": "systemd-libs",
    "OPENSSL": "openssl-libs",
    "PERL_AUTODIE": "perl-autodie",
    "PERL_FILE_PATH": "perl-File-Path",
    "PERL_LWP_PROTO_HTTPS": "perl-LWP-Protocol-https",
    "PERL_SYS_SYSLOG": "perl-Sys-Syslog",
    "PROCPS": "procps-ng",
    "PYTHON_SIMPLEJSON": "python2-simplejson",
    "UDEV": "systemd"
  },
  "parent": "CENTOS8",
  "repo": {
    "keyring": "redhat/repo/RPM-GPG-KEY-StorPool",
    "yumdef": "redhat/repo/storpool-centos.repo"
  },
  "systemd_lib": "usr/lib/systemd/system"
}
EOVARIANT_JSON
}

show_ROCKY8()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "rocky8",
    "base_image": "rockylinux/rockylinux:8",
    "branch": "",
    "kernel_package": "kernel-core",
    "utf8_locale": "C.utf8"
  },
  "commands": {
    "package": {
      "install": [
        "dnf",
        "--enablerepo=storpool-contrib",
        "--enablerepo=powertools",
        "install",
        "-q",
        "-y",
        "--"
      ],
      "list_all": [
        "rpm",
        "-qa",
        "--qf",
        "%{Name}\\t%{EVR}\\t%{Arch}\\tii\\n",
        "--"
      ],
      "purge": [
        "yum",
        "remove",
        "-q",
        "-y",
        "--"
      ],
      "remove": [
        "yum",
        "remove",
        "-q",
        "-y",
        "--"
      ],
      "remove_impl": [
        "rpm",
        "-e",
        "--"
      ],
      "update_db": [
        "true"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "rpm -qpR -- \"$pkg\""
      ],
      "install": [
        "sh",
        "-c",
        "\nunset to_install to_reinstall\nfor f in $packages; do\n    package=\"$(rpm -qp \"$f\")\"\n    if rpm -q -- \"$package\"; then\n        to_reinstall=\"$to_reinstall ./$f\"\n    else\n        to_install=\"$to_install ./$f\"\n    fi\ndone\n\nif [ -n \"$to_install\" ]; then\n    dnf install -y --enablerepo=storpool-contrib,powertools --setopt=localpkg_gpgcheck=0 -- $to_install\nfi\nif [ -n \"$to_reinstall\" ]; then\n    dnf reinstall -y --enablerepo=storpool-contrib,powertools --setopt=localpkg_gpgcheck=0 -- $to_reinstall\nfi\n"
      ]
    }
  },
  "descr": "Rocky Linux 8.x",
  "detect": {
    "filename": "/etc/redhat-release",
    "os_id": "rocky",
    "os_version_regex": "^8(?:$|\\.[4-9]|\\.[1-9][0-9])",
    "regex": "^ Rocky \\s+ Linux \\s .* \\s 8 \\. (?: [4-9] | [1-9][0-9] )"
  },
  "family": "redhat",
  "file_ext": "rpm",
  "initramfs_flavor": "mkinitrd",
  "min_sys_python": "2.7",
  "name": "ROCKY8",
  "package": {
    "KMOD": "kmod",
    "LIBCGROUP": "libcgroup-tools",
    "LIBUDEV": "systemd-libs",
    "OPENSSL": "openssl-libs",
    "PERL_AUTODIE": "perl-autodie",
    "PERL_FILE_PATH": "perl-File-Path",
    "PERL_LWP_PROTO_HTTPS": "perl-LWP-Protocol-https",
    "PERL_SYS_SYSLOG": "perl-Sys-Syslog",
    "PROCPS": "procps-ng",
    "PYTHON_SIMPLEJSON": "python2-simplejson",
    "UDEV": "systemd"
  },
  "parent": "CENTOS8",
  "repo": {
    "keyring": "redhat/repo/RPM-GPG-KEY-StorPool",
    "yumdef": "redhat/repo/storpool-centos.repo"
  },
  "systemd_lib": "usr/lib/systemd/system"
}
EOVARIANT_JSON
}

show_UBUNTU1604()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "ubuntu-16.04",
    "base_image": "ubuntu:xenial",
    "branch": "ubuntu/xenial",
    "kernel_package": "linux-headers",
    "utf8_locale": "C.UTF-8"
  },
  "commands": {
    "package": {
      "install": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "--no-install-recommends",
        "install",
        "--"
      ],
      "list_all": [
        "dpkg-query",
        "-W",
        "-f",
        "${Package}\\t${Version}\\t${Architecture}\\t${db:Status-Abbrev}\\n",
        "--"
      ],
      "purge": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "purge",
        "--"
      ],
      "remove": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "remove",
        "--"
      ],
      "remove_impl": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "dpkg",
        "-r",
        "--"
      ],
      "update_db": [
        "apt-get",
        "-q",
        "-y",
        "update"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "dpkg-deb -f -- \"$pkg\" 'Depends' | sed -e 's/ *, */,/g' | tr ',' \"\\n\""
      ],
      "install": [
        "sh",
        "-c",
        "env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages"
      ]
    }
  },
  "descr": "Ubuntu 16.04 LTS (Xenial Xerus)",
  "detect": {
    "filename": "/etc/os-release",
    "os_id": "ubuntu",
    "os_version_regex": "^16\\.04$",
    "regex": "^ PRETTY_NAME= .* Ubuntu \\s+ 16 \\. 04 "
  },
  "family": "debian",
  "file_ext": "deb",
  "initramfs_flavor": "update-initramfs",
  "min_sys_python": "2.7",
  "name": "UBUNTU1604",
  "package": {
    "BINDINGS_PYTHON": "python",
    "BINDINGS_PYTHON_CONFGET": "python-confget",
    "BINDINGS_PYTHON_SIMPLEJSON": "python-simplejson",
    "CGROUP": "cgroup-tools",
    "CPUPOWER": "linux-tools-generic",
    "LIBSSL": "libssl1.0.0",
    "MCELOG": "bash",
    "mcelog": "mcelog"
  },
  "parent": "UBUNTU1804",
  "repo": {
    "codename": "xenial",
    "keyring": "debian/repo/storpool-keyring.gpg",
    "req_packages": [
      "apt-transport-https",
      "ca-certificates"
    ],
    "sources": "debian/repo/storpool.sources",
    "vendor": "ubuntu"
  },
  "systemd_lib": "lib/systemd/system"
}
EOVARIANT_JSON
}

show_UBUNTU1804()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "ubuntu-18.04",
    "base_image": "ubuntu:bionic",
    "branch": "ubuntu/bionic",
    "kernel_package": "linux-headers",
    "utf8_locale": "C.UTF-8"
  },
  "commands": {
    "package": {
      "install": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "--no-install-recommends",
        "install",
        "--"
      ],
      "list_all": [
        "dpkg-query",
        "-W",
        "-f",
        "${Package}\\t${Version}\\t${Architecture}\\t${db:Status-Abbrev}\\n",
        "--"
      ],
      "purge": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "purge",
        "--"
      ],
      "remove": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "remove",
        "--"
      ],
      "remove_impl": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "dpkg",
        "-r",
        "--"
      ],
      "update_db": [
        "apt-get",
        "-q",
        "-y",
        "update"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "dpkg-deb -f -- \"$pkg\" 'Depends' | sed -e 's/ *, */,/g' | tr ',' \"\\n\""
      ],
      "install": [
        "sh",
        "-c",
        "env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages"
      ]
    }
  },
  "descr": "Ubuntu 18.04 LTS (Bionic Beaver)",
  "detect": {
    "filename": "/etc/os-release",
    "os_id": "ubuntu",
    "os_version_regex": "^18\\.04$",
    "regex": "^ PRETTY_NAME= .* Ubuntu \\s+ 18 \\. 04 "
  },
  "family": "debian",
  "file_ext": "deb",
  "initramfs_flavor": "update-initramfs",
  "min_sys_python": "2.7",
  "name": "UBUNTU1804",
  "package": {
    "BINDINGS_PYTHON": "python",
    "BINDINGS_PYTHON_CONFGET": "python-confget",
    "BINDINGS_PYTHON_SIMPLEJSON": "python-simplejson",
    "CGROUP": "cgroup-tools",
    "CPUPOWER": "linux-tools-generic",
    "LIBSSL": "libssl1.1",
    "MCELOG": "bash"
  },
  "parent": "UBUNTU2004",
  "repo": {
    "codename": "bionic",
    "keyring": "debian/repo/storpool-keyring.gpg",
    "req_packages": [
      "ca-certificates"
    ],
    "sources": "debian/repo/storpool.sources",
    "vendor": "ubuntu"
  },
  "systemd_lib": "lib/systemd/system"
}
EOVARIANT_JSON
}

show_UBUNTU2004()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "ubuntu-20.04",
    "base_image": "ubuntu:focal",
    "branch": "ubuntu/focal",
    "kernel_package": "linux-headers",
    "utf8_locale": "C.UTF-8"
  },
  "commands": {
    "package": {
      "install": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "--no-install-recommends",
        "install",
        "--"
      ],
      "list_all": [
        "dpkg-query",
        "-W",
        "-f",
        "${Package}\\t${Version}\\t${Architecture}\\t${db:Status-Abbrev}\\n",
        "--"
      ],
      "purge": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "purge",
        "--"
      ],
      "remove": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "remove",
        "--"
      ],
      "remove_impl": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "dpkg",
        "-r",
        "--"
      ],
      "update_db": [
        "apt-get",
        "-q",
        "-y",
        "update"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "dpkg-deb -f -- \"$pkg\" 'Depends' | sed -e 's/ *, */,/g' | tr ',' \"\\n\""
      ],
      "install": [
        "sh",
        "-c",
        "env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages"
      ]
    }
  },
  "descr": "Ubuntu 20.04 LTS (Focal Fossa)",
  "detect": {
    "filename": "/etc/os-release",
    "os_id": "ubuntu",
    "os_version_regex": "^20\\.04$",
    "regex": "^ PRETTY_NAME= .* (?: Ubuntu \\s+ 20 \\. 04 | Mint \\s+ 20 ) "
  },
  "family": "debian",
  "file_ext": "deb",
  "initramfs_flavor": "update-initramfs",
  "min_sys_python": "3.8",
  "name": "UBUNTU2004",
  "package": {
    "BINDINGS_PYTHON": "python3",
    "BINDINGS_PYTHON_CONFGET": "python3-confget",
    "BINDINGS_PYTHON_SIMPLEJSON": "python3-simplejson",
    "CGROUP": "cgroup-tools",
    "CPUPOWER": "linux-tools-generic",
    "LIBSSL": "libssl1.1",
    "MCELOG": "bash"
  },
  "parent": "UBUNTU2110",
  "repo": {
    "codename": "focal",
    "keyring": "debian/repo/storpool-keyring.gpg",
    "req_packages": [
      "ca-certificates"
    ],
    "sources": "debian/repo/storpool.sources",
    "vendor": "ubuntu"
  },
  "systemd_lib": "lib/systemd/system"
}
EOVARIANT_JSON
}

show_UBUNTU2110()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "ubuntu-21.10",
    "base_image": "ubuntu:impish",
    "branch": "ubuntu/impish",
    "kernel_package": "linux-headers",
    "utf8_locale": "C.UTF-8"
  },
  "commands": {
    "package": {
      "install": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "--no-install-recommends",
        "install",
        "--"
      ],
      "list_all": [
        "dpkg-query",
        "-W",
        "-f",
        "${Package}\\t${Version}\\t${Architecture}\\t${db:Status-Abbrev}\\n",
        "--"
      ],
      "purge": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "purge",
        "--"
      ],
      "remove": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "remove",
        "--"
      ],
      "remove_impl": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "dpkg",
        "-r",
        "--"
      ],
      "update_db": [
        "apt-get",
        "-q",
        "-y",
        "update"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "dpkg-deb -f -- \"$pkg\" 'Depends' | sed -e 's/ *, */,/g' | tr ',' \"\\n\""
      ],
      "install": [
        "sh",
        "-c",
        "env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages"
      ]
    }
  },
  "descr": "Ubuntu 21.10 LTS (Impish Indri)",
  "detect": {
    "filename": "/etc/os-release",
    "os_id": "ubuntu",
    "os_version_regex": "^21\\.10$",
    "regex": "^ PRETTY_NAME= .* (?: Ubuntu \\s+ 21 \\. 10 | Mint \\s+ 21 ) "
  },
  "family": "debian",
  "file_ext": "deb",
  "initramfs_flavor": "update-initramfs",
  "min_sys_python": "3.9",
  "name": "UBUNTU2110",
  "package": {
    "BINDINGS_PYTHON": "python3",
    "BINDINGS_PYTHON_CONFGET": "python3-confget",
    "BINDINGS_PYTHON_SIMPLEJSON": "python3-simplejson",
    "CGROUP": "cgroup-tools",
    "CPUPOWER": "linux-tools-generic",
    "LIBSSL": "libssl1.1",
    "MCELOG": "bash"
  },
  "parent": "UBUNTU2204",
  "repo": {
    "codename": "impish",
    "keyring": "debian/repo/storpool-keyring.gpg",
    "req_packages": [
      "ca-certificates"
    ],
    "sources": "debian/repo/storpool.sources",
    "vendor": "ubuntu"
  },
  "systemd_lib": "lib/systemd/system"
}
EOVARIANT_JSON
}

show_UBUNTU2204()
{
	cat <<'EOVARIANT_JSON'
  {
  "builder": {
    "alias": "ubuntu-22.04",
    "base_image": "ubuntu:jammy",
    "branch": "ubuntu/jammy",
    "kernel_package": "linux-headers",
    "utf8_locale": "C.UTF-8"
  },
  "commands": {
    "package": {
      "install": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "--no-install-recommends",
        "install",
        "--"
      ],
      "list_all": [
        "dpkg-query",
        "-W",
        "-f",
        "${Package}\\t${Version}\\t${Architecture}\\t${db:Status-Abbrev}\\n",
        "--"
      ],
      "purge": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "purge",
        "--"
      ],
      "remove": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "apt-get",
        "-q",
        "-y",
        "remove",
        "--"
      ],
      "remove_impl": [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "dpkg",
        "-r",
        "--"
      ],
      "update_db": [
        "apt-get",
        "-q",
        "-y",
        "update"
      ]
    },
    "pkgfile": {
      "dep_query": [
        "sh",
        "-c",
        "dpkg-deb -f -- \"$pkg\" 'Depends' | sed -e 's/ *, */,/g' | tr ',' \"\\n\""
      ],
      "install": [
        "sh",
        "-c",
        "env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages"
      ]
    }
  },
  "descr": "Ubuntu 22.04 LTS (Jammy Jellyfish)",
  "detect": {
    "filename": "/etc/os-release",
    "os_id": "ubuntu",
    "os_version_regex": "^22\\.04$",
    "regex": "^ PRETTY_NAME= .* (?: Ubuntu \\s+ 22 \\. 04 | Mint \\s+ 22 ) "
  },
  "family": "debian",
  "file_ext": "deb",
  "initramfs_flavor": "update-initramfs",
  "min_sys_python": "3.9",
  "name": "UBUNTU2204",
  "package": {
    "BINDINGS_PYTHON": "python3",
    "BINDINGS_PYTHON_CONFGET": "python3-confget",
    "BINDINGS_PYTHON_SIMPLEJSON": "python3-simplejson",
    "CGROUP": "cgroup-tools",
    "CPUPOWER": "linux-tools-generic",
    "LIBSSL": "libssl1.1",
    "MCELOG": "bash"
  },
  "parent": "DEBIAN12",
  "repo": {
    "codename": "jammy",
    "keyring": "debian/repo/storpool-keyring.gpg",
    "req_packages": [
      "ca-certificates"
    ],
    "sources": "debian/repo/storpool.sources",
    "vendor": "ubuntu"
  },
  "systemd_lib": "lib/systemd/system"
}
EOVARIANT_JSON
}


cmd_show_all()
{
	if [ "$#" -ne 0 ]; then
		usage 1>&2
		exit 1
	fi

	cat <<'EOPROLOGUE'
{
  "format": {
    "version": {
      "major": 1,
      "minor": 3
    }
  },
  "order": [
    "ALMA8",
    "ROCKY8",
    "RHEL8",
    "ORACLE7",
    "CENTOS6",
    "CENTOS7",
    "CENTOS8",
    "UBUNTU1604",
    "UBUNTU1804",
    "UBUNTU2004",
    "UBUNTU2110",
    "UBUNTU2204",
    "DEBIAN9",
    "DEBIAN10",
    "DEBIAN11",
    "DEBIAN12"
  ],
  "variants": {
EOPROLOGUE

  
  printf -- '    "%s": ' 'ALMA8'
  show_ALMA8
  echo ','
  printf -- '    "%s": ' 'CENTOS6'
  show_CENTOS6
  echo ','
  printf -- '    "%s": ' 'CENTOS7'
  show_CENTOS7
  echo ','
  printf -- '    "%s": ' 'CENTOS8'
  show_CENTOS8
  echo ','
  printf -- '    "%s": ' 'DEBIAN9'
  show_DEBIAN9
  echo ','
  printf -- '    "%s": ' 'DEBIAN10'
  show_DEBIAN10
  echo ','
  printf -- '    "%s": ' 'DEBIAN11'
  show_DEBIAN11
  echo ','
  printf -- '    "%s": ' 'DEBIAN12'
  show_DEBIAN12
  echo ','
  printf -- '    "%s": ' 'ORACLE7'
  show_ORACLE7
  echo ','
  printf -- '    "%s": ' 'RHEL8'
  show_RHEL8
  echo ','
  printf -- '    "%s": ' 'ROCKY8'
  show_ROCKY8
  echo ','
  printf -- '    "%s": ' 'UBUNTU1604'
  show_UBUNTU1604
  echo ','
  printf -- '    "%s": ' 'UBUNTU1804'
  show_UBUNTU1804
  echo ','
  printf -- '    "%s": ' 'UBUNTU2004'
  show_UBUNTU2004
  echo ','
  printf -- '    "%s": ' 'UBUNTU2110'
  show_UBUNTU2110
  echo ','
  printf -- '    "%s": ' 'UBUNTU2204'
  show_UBUNTU2204
  

	cat <<'EOEPILOGUE'
  },
  "version": "2.3.1"
}
EOEPILOGUE
}

show_variant()
{
	local variant="$1"

	cat <<'EOPROLOGUE'
{
  "format": {
    "version": {
      "major": 1,
      "minor": 3
    }
  },
  "variant":
EOPROLOGUE

	eval "'show_$variant'"

	cat <<'EOEPILOGUE'
  ,
  "version": "2.3.1"
}
EOEPILOGUE
}

cmd_show_current()
{
	if [ "$#" -ne 0 ]; then
		usage 1>&2
		exit 1
	fi

	local variant="$(cmd_detect)"
	[ -n "$variant" ]

	show_variant "$variant"
}

run_command()
{
	local name="$1" noop="$2" command="$3"
	shift 3

	local cmd_cat="${command%%.*}" cmd_item="${command#*.}"
	if [ "$command" = "$cmd_cat" ] || [ "$cmd_item" != "${cmd_item%.*}" ]; then
		echo "Invalid command specification '$command'" 1>&2
		exit 1
	fi

	case "$name" in
		
		ALMA8)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'dnf' '--enablerepo=storpool-contrib' '--enablerepo=powertools' 'install' '-q' '-y' '--'  "$@"
							;;
						
						list_all)
							$noop 'rpm' '-qa' '--qf' '%{Name}\t%{EVR}\t%{Arch}\tii\n' '--'  "$@"
							;;
						
						purge)
							$noop 'yum' 'remove' '-q' '-y' '--'  "$@"
							;;
						
						remove)
							$noop 'yum' 'remove' '-q' '-y' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'rpm' '-e' '--'  "$@"
							;;
						
						update_db)
							$noop 'true'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'rpm -qpR -- "$pkg"'  "$@"
							;;
						
						install)
							$noop 'sh' '-c' '
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
'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		CENTOS6)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'yum' '--enablerepo=storpool-contrib' 'install' '-q' '-y'  "$@"
							;;
						
						list_all)
							$noop 'rpm' '-qa' '--qf' '%{Name}\t%{EVR}\t%{Arch}\tii\n' '--'  "$@"
							;;
						
						purge)
							$noop 'yum' 'remove' '-q' '-y' '--'  "$@"
							;;
						
						remove)
							$noop 'yum' 'remove' '-q' '-y' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'rpm' '-e' '--'  "$@"
							;;
						
						update_db)
							$noop 'true'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'rpm -qpR -- "$pkg"'  "$@"
							;;
						
						install)
							$noop '
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
'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		CENTOS7)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'yum' '--enablerepo=storpool-contrib' 'install' '-q' '-y'  "$@"
							;;
						
						list_all)
							$noop 'rpm' '-qa' '--qf' '%{Name}\t%{EVR}\t%{Arch}\tii\n' '--'  "$@"
							;;
						
						purge)
							$noop 'yum' 'remove' '-q' '-y' '--'  "$@"
							;;
						
						remove)
							$noop 'yum' 'remove' '-q' '-y' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'rpm' '-e' '--'  "$@"
							;;
						
						update_db)
							$noop 'true'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'rpm -qpR -- "$pkg"'  "$@"
							;;
						
						install)
							$noop '
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
'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		CENTOS8)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'dnf' '--enablerepo=storpool-contrib' '--enablerepo=powertools' 'install' '-q' '-y' '--'  "$@"
							;;
						
						list_all)
							$noop 'rpm' '-qa' '--qf' '%{Name}\t%{EVR}\t%{Arch}\tii\n' '--'  "$@"
							;;
						
						purge)
							$noop 'yum' 'remove' '-q' '-y' '--'  "$@"
							;;
						
						remove)
							$noop 'yum' 'remove' '-q' '-y' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'rpm' '-e' '--'  "$@"
							;;
						
						update_db)
							$noop 'true'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'rpm -qpR -- "$pkg"'  "$@"
							;;
						
						install)
							$noop 'sh' '-c' '
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
'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		DEBIAN9)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' '--no-install-recommends' 'install' '--'  "$@"
							;;
						
						list_all)
							$noop 'dpkg-query' '-W' '-f' '${Package}\t${Version}\t${Architecture}\t${db:Status-Abbrev}\n' '--'  "$@"
							;;
						
						purge)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'purge' '--'  "$@"
							;;
						
						remove)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'remove' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'dpkg' '-r' '--'  "$@"
							;;
						
						update_db)
							$noop 'apt-get' '-q' '-y' 'update'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'dpkg-deb -f -- "$pkg" 'Depends' | sed -e 's/ *, */,/g' | tr ',' "\n"'  "$@"
							;;
						
						install)
							$noop 'sh' '-c' 'env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		DEBIAN10)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' '--no-install-recommends' 'install' '--'  "$@"
							;;
						
						list_all)
							$noop 'dpkg-query' '-W' '-f' '${Package}\t${Version}\t${Architecture}\t${db:Status-Abbrev}\n' '--'  "$@"
							;;
						
						purge)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'purge' '--'  "$@"
							;;
						
						remove)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'remove' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'dpkg' '-r' '--'  "$@"
							;;
						
						update_db)
							$noop 'apt-get' '-q' '-y' 'update'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'dpkg-deb -f -- "$pkg" 'Depends' | sed -e 's/ *, */,/g' | tr ',' "\n"'  "$@"
							;;
						
						install)
							$noop 'sh' '-c' 'env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		DEBIAN11)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' '--no-install-recommends' 'install' '--'  "$@"
							;;
						
						list_all)
							$noop 'dpkg-query' '-W' '-f' '${Package}\t${Version}\t${Architecture}\t${db:Status-Abbrev}\n' '--'  "$@"
							;;
						
						purge)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'purge' '--'  "$@"
							;;
						
						remove)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'remove' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'dpkg' '-r' '--'  "$@"
							;;
						
						update_db)
							$noop 'apt-get' '-q' '-y' 'update'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'dpkg-deb -f -- "$pkg" 'Depends' | sed -e 's/ *, */,/g' | tr ',' "\n"'  "$@"
							;;
						
						install)
							$noop 'sh' '-c' 'env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		DEBIAN12)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' '--no-install-recommends' 'install' '--'  "$@"
							;;
						
						list_all)
							$noop 'dpkg-query' '-W' '-f' '${Package}\t${Version}\t${Architecture}\t${db:Status-Abbrev}\n' '--'  "$@"
							;;
						
						purge)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'purge' '--'  "$@"
							;;
						
						remove)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'remove' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'dpkg' '-r' '--'  "$@"
							;;
						
						update_db)
							$noop 'apt-get' '-q' '-y' 'update'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'dpkg-deb -f -- "$pkg" 'Depends' | sed -e 's/ *, */,/g' | tr ',' "\n"'  "$@"
							;;
						
						install)
							$noop 'sh' '-c' 'env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		ORACLE7)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'yum' '--enablerepo=storpool-contrib' 'install' '-q' '-y'  "$@"
							;;
						
						list_all)
							$noop 'rpm' '-qa' '--qf' '%{Name}\t%{EVR}\t%{Arch}\tii\n' '--'  "$@"
							;;
						
						purge)
							$noop 'yum' 'remove' '-q' '-y' '--'  "$@"
							;;
						
						remove)
							$noop 'yum' 'remove' '-q' '-y' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'rpm' '-e' '--'  "$@"
							;;
						
						update_db)
							$noop 'true'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'rpm -qpR -- "$pkg"'  "$@"
							;;
						
						install)
							$noop '
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
'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		RHEL8)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'dnf' '--enablerepo=storpool-contrib' '--enablerepo=codeready-builder-for-rhel-8-x86_64-rpms' 'install' '-q' '-y' '--'  "$@"
							;;
						
						list_all)
							$noop 'rpm' '-qa' '--qf' '%{Name}\t%{EVR}\t%{Arch}\tii\n' '--'  "$@"
							;;
						
						purge)
							$noop 'yum' 'remove' '-q' '-y' '--'  "$@"
							;;
						
						remove)
							$noop 'yum' 'remove' '-q' '-y' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'rpm' '-e' '--'  "$@"
							;;
						
						update_db)
							$noop 'true'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'rpm -qpR -- "$pkg"'  "$@"
							;;
						
						install)
							$noop 'sh' '-c' '
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
'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		ROCKY8)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'dnf' '--enablerepo=storpool-contrib' '--enablerepo=powertools' 'install' '-q' '-y' '--'  "$@"
							;;
						
						list_all)
							$noop 'rpm' '-qa' '--qf' '%{Name}\t%{EVR}\t%{Arch}\tii\n' '--'  "$@"
							;;
						
						purge)
							$noop 'yum' 'remove' '-q' '-y' '--'  "$@"
							;;
						
						remove)
							$noop 'yum' 'remove' '-q' '-y' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'rpm' '-e' '--'  "$@"
							;;
						
						update_db)
							$noop 'true'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'rpm -qpR -- "$pkg"'  "$@"
							;;
						
						install)
							$noop 'sh' '-c' '
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
'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		UBUNTU1604)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' '--no-install-recommends' 'install' '--'  "$@"
							;;
						
						list_all)
							$noop 'dpkg-query' '-W' '-f' '${Package}\t${Version}\t${Architecture}\t${db:Status-Abbrev}\n' '--'  "$@"
							;;
						
						purge)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'purge' '--'  "$@"
							;;
						
						remove)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'remove' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'dpkg' '-r' '--'  "$@"
							;;
						
						update_db)
							$noop 'apt-get' '-q' '-y' 'update'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'dpkg-deb -f -- "$pkg" 'Depends' | sed -e 's/ *, */,/g' | tr ',' "\n"'  "$@"
							;;
						
						install)
							$noop 'sh' '-c' 'env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		UBUNTU1804)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' '--no-install-recommends' 'install' '--'  "$@"
							;;
						
						list_all)
							$noop 'dpkg-query' '-W' '-f' '${Package}\t${Version}\t${Architecture}\t${db:Status-Abbrev}\n' '--'  "$@"
							;;
						
						purge)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'purge' '--'  "$@"
							;;
						
						remove)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'remove' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'dpkg' '-r' '--'  "$@"
							;;
						
						update_db)
							$noop 'apt-get' '-q' '-y' 'update'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'dpkg-deb -f -- "$pkg" 'Depends' | sed -e 's/ *, */,/g' | tr ',' "\n"'  "$@"
							;;
						
						install)
							$noop 'sh' '-c' 'env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		UBUNTU2004)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' '--no-install-recommends' 'install' '--'  "$@"
							;;
						
						list_all)
							$noop 'dpkg-query' '-W' '-f' '${Package}\t${Version}\t${Architecture}\t${db:Status-Abbrev}\n' '--'  "$@"
							;;
						
						purge)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'purge' '--'  "$@"
							;;
						
						remove)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'remove' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'dpkg' '-r' '--'  "$@"
							;;
						
						update_db)
							$noop 'apt-get' '-q' '-y' 'update'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'dpkg-deb -f -- "$pkg" 'Depends' | sed -e 's/ *, */,/g' | tr ',' "\n"'  "$@"
							;;
						
						install)
							$noop 'sh' '-c' 'env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		UBUNTU2110)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' '--no-install-recommends' 'install' '--'  "$@"
							;;
						
						list_all)
							$noop 'dpkg-query' '-W' '-f' '${Package}\t${Version}\t${Architecture}\t${db:Status-Abbrev}\n' '--'  "$@"
							;;
						
						purge)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'purge' '--'  "$@"
							;;
						
						remove)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'remove' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'dpkg' '-r' '--'  "$@"
							;;
						
						update_db)
							$noop 'apt-get' '-q' '-y' 'update'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'dpkg-deb -f -- "$pkg" 'Depends' | sed -e 's/ *, */,/g' | tr ',' "\n"'  "$@"
							;;
						
						install)
							$noop 'sh' '-c' 'env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		
		UBUNTU2204)
			case "$cmd_cat" in
				
				package)
					case "$cmd_item" in
						
						install)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' '--no-install-recommends' 'install' '--'  "$@"
							;;
						
						list_all)
							$noop 'dpkg-query' '-W' '-f' '${Package}\t${Version}\t${Architecture}\t${db:Status-Abbrev}\n' '--'  "$@"
							;;
						
						purge)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'purge' '--'  "$@"
							;;
						
						remove)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'apt-get' '-q' '-y' 'remove' '--'  "$@"
							;;
						
						remove_impl)
							$noop 'env' 'DEBIAN_FRONTEND=noninteractive' 'dpkg' '-r' '--'  "$@"
							;;
						
						update_db)
							$noop 'apt-get' '-q' '-y' 'update'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				
				pkgfile)
					case "$cmd_item" in
						
						dep_query)
							$noop 'sh' '-c' 'dpkg-deb -f -- "$pkg" 'Depends' | sed -e 's/ *, */,/g' | tr ',' "\n"'  "$@"
							;;
						
						install)
							$noop 'sh' '-c' 'env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --reinstall -y -o DPkg::Options::=--force-confnew -- $packages'  "$@"
							;;
						

						*)
							echo "Invalid command '$cmd_item' in the '$cmd_cat' category" 1>&2
							exit 1
							;;
					esac
					;;
				

				*)
					echo "Invalid command category '$cmd_cat'" 1>&2
					exit 1
					;;
			esac
			;;
		

		*)
			echo "Internal error: invalid variant '$name'" 1>&2
			exit 1
			;;
	esac
}

copy_file()
{
	local src="$1" dstdir="$2"
	if [ ! -f "$src" ]; then
		echo "Internal error: no $src file to copy to $dstdir" 1>&2
		exit 1
	fi
	if [ -z "$dstdir" ]; then
		echo "Internal error: no destination specified for $src" 1>&2
		exit 1
	fi
	if [ ! -d "$dstdir" ]; then
		echo "Internal error: no $dstdir directory" 1>&2
		exit 1
	fi

	local dst="$dstdir/$(basename -- "$src")"
	install -o root -g root -m 644 -- "$src" "$dst"
}

repo_add_extension()
{
	local filename="$1" repotype="$2"
	local basename="${filename%.*}"
	local ext="${filename##*.}"

	local suffix='-invalid'
	case "$repotype" in
		
		contrib)
			suffix=''
			;;
		
		infra)
			suffix='-infra'
			;;
		
		staging)
			suffix='-staging'
			;;
		

		*)
			echo "Invalid repository type '$repotype'" 1>&2
			exit 1
			;;
	esac

	printf -- '%s%s.%s\n' "$basename" "$suffix" "$ext"
}

repo_add_yum()
{
	local name="$1" vdir="$2" repotype="$3" yumdef="$4" keyring="$5"

	yum --disablerepo='storpool-*' install -q -y ca-certificates

	local yumbase="$(basename -- "$yumdef")"
	local repofile="$(repo_add_extension "$yumbase" "$repotype")"
	[ -n "$repofile" ]
	copy_file "$vdir/$repofile" /etc/yum.repos.d

	local keybase="$(basename -- "$keyring")"
	copy_file "$vdir/$keybase" /etc/pki/rpm-gpg

	if [ -n "$(command -v rpmkeys)" ]; then
		rpmkeys --import "/etc/pki/rpm-gpg/$(basename -- "$keybase")"
	fi

	yum --disablerepo='*' --enablerepo="storpool-$repotype" clean metadata
}

repo_add_deb()
{
	local name="$1" vdir="$2" repotype="$3" srcdef="$4" keyring="$5" packages="$6"

	# $packages is unquoted on purpose: there may be more than one.
	run_command "$name" '' package.install $packages

	local srcbase="$(basename -- "$srcdef")"
	local repofile="$(repo_add_extension "$srcbase" "$repotype")"
	[ -n "$repofile" ]
	copy_file "$vdir/$repofile" /etc/apt/sources.list.d

	local keybase="$(basename -- "$keyring")"
	copy_file "$vdir/$keybase" /usr/share/keyrings

	apt-get update
}

cmd_repo_add()
{
	local repodir="$(dirname -- "$0")" repotype='contrib'
	local o
	while getopts 'd:t:' o; do
		case "$o" in
			d)
				repodir="$OPTARG"
				;;

			t)
				repotype="$OPTARG"
				;;

			*)
				usage 1>&2
				exit 1
				;;
		esac
	done
	shift "$((OPTIND - 1))"
	if [ "$#" -ne 0 ]; then
		usage 1>&2
		exit 1
	fi

	local variant="$(cmd_detect)"
	local vdir="$repodir/$variant"
	if [ ! -d "$vdir" ]; then
		echo "No $vdir directory" 1>&2
		exit 1
	fi

	case "$variant" in
		
		ALMA8)
			
			repo_add_yum 'ALMA8' "$vdir" "$repotype" 'redhat/repo/storpool-centos.repo' 'redhat/repo/RPM-GPG-KEY-StorPool'
			
			;;
		
		CENTOS6)
			
			repo_add_yum 'CENTOS6' "$vdir" "$repotype" 'redhat/repo/storpool-centos.repo' 'redhat/repo/RPM-GPG-KEY-StorPool'
			
			;;
		
		CENTOS7)
			
			repo_add_yum 'CENTOS7' "$vdir" "$repotype" 'redhat/repo/storpool-centos.repo' 'redhat/repo/RPM-GPG-KEY-StorPool'
			
			;;
		
		CENTOS8)
			
			repo_add_yum 'CENTOS8' "$vdir" "$repotype" 'redhat/repo/storpool-centos.repo' 'redhat/repo/RPM-GPG-KEY-StorPool'
			
			;;
		
		DEBIAN9)
			
			repo_add_deb 'DEBIAN9' "$vdir" "$repotype" 'debian/repo/storpool.sources' 'debian/repo/storpool-keyring.gpg' 'apt-transport-https ca-certificates'
			
			;;
		
		DEBIAN10)
			
			repo_add_deb 'DEBIAN10' "$vdir" "$repotype" 'debian/repo/storpool.sources' 'debian/repo/storpool-keyring.gpg' 'ca-certificates'
			
			;;
		
		DEBIAN11)
			
			repo_add_deb 'DEBIAN11' "$vdir" "$repotype" 'debian/repo/storpool.sources' 'debian/repo/storpool-keyring.gpg' 'ca-certificates'
			
			;;
		
		DEBIAN12)
			
			repo_add_deb 'DEBIAN12' "$vdir" "$repotype" 'debian/repo/storpool.sources' 'debian/repo/storpool-keyring.gpg' 'ca-certificates'
			
			;;
		
		ORACLE7)
			
			repo_add_yum 'ORACLE7' "$vdir" "$repotype" 'redhat/repo/storpool-centos.repo' 'redhat/repo/RPM-GPG-KEY-StorPool'
			
			;;
		
		RHEL8)
			
			repo_add_yum 'RHEL8' "$vdir" "$repotype" 'redhat/repo/storpool-centos.repo' 'redhat/repo/RPM-GPG-KEY-StorPool'
			
			;;
		
		ROCKY8)
			
			repo_add_yum 'ROCKY8' "$vdir" "$repotype" 'redhat/repo/storpool-centos.repo' 'redhat/repo/RPM-GPG-KEY-StorPool'
			
			;;
		
		UBUNTU1604)
			
			repo_add_deb 'UBUNTU1604' "$vdir" "$repotype" 'debian/repo/storpool.sources' 'debian/repo/storpool-keyring.gpg' 'apt-transport-https ca-certificates'
			
			;;
		
		UBUNTU1804)
			
			repo_add_deb 'UBUNTU1804' "$vdir" "$repotype" 'debian/repo/storpool.sources' 'debian/repo/storpool-keyring.gpg' 'ca-certificates'
			
			;;
		
		UBUNTU2004)
			
			repo_add_deb 'UBUNTU2004' "$vdir" "$repotype" 'debian/repo/storpool.sources' 'debian/repo/storpool-keyring.gpg' 'ca-certificates'
			
			;;
		
		UBUNTU2110)
			
			repo_add_deb 'UBUNTU2110' "$vdir" "$repotype" 'debian/repo/storpool.sources' 'debian/repo/storpool-keyring.gpg' 'ca-certificates'
			
			;;
		
		UBUNTU2204)
			
			repo_add_deb 'UBUNTU2204' "$vdir" "$repotype" 'debian/repo/storpool.sources' 'debian/repo/storpool-keyring.gpg' 'ca-certificates'
			
			;;
		
	esac

	install -o root -g root -m 755 -- "$0" /usr/sbin/sp_variant
}

cmd_command_run()
{
	local noop=''
	while getopts 'N' o; do
		case "$o" in
			N)
				noop='echo'
				;;

			*)
				usage 1>&2
				exit 1
				;;
		esac
	done
	shift "$((OPTIND - 1))"

	local variant="$(cmd_detect)"
	[ -n "$variant" ]

	run_command "$variant" "$noop" "$@"
}

cmd_command()
{
	case "$1" in
		run)
			shift
			cmd_command_run "$@"
			;;

		*)
			usage 1>&2
			exit 1
			;;
	esac
}

cmd_features()
{
	echo 'Features: format=1.3 version=2.3.1'
}

case "$1" in
	command)
		shift
		cmd_command "$@"
		;;

	detect)
		shift
		cmd_detect "$@"
		;;

	features)
		shift
		cmd_features "$@"
		;;

	repo)
		shift
		case "$1" in
			add)
				shift
				cmd_repo_add "$@"
				;;

			*)
				usage 1>&2
				exit 1
				;;
		esac
		;;

	show)
		shift
		case "$1" in
			all)
				shift
				cmd_show_all "$@"
				;;

			current)
				shift
				cmd_show_current "$@"
				;;

			
			ALMA8)
				show_variant 'ALMA8'
				;;
			
			CENTOS6)
				show_variant 'CENTOS6'
				;;
			
			CENTOS7)
				show_variant 'CENTOS7'
				;;
			
			CENTOS8)
				show_variant 'CENTOS8'
				;;
			
			DEBIAN9)
				show_variant 'DEBIAN9'
				;;
			
			DEBIAN10)
				show_variant 'DEBIAN10'
				;;
			
			DEBIAN11)
				show_variant 'DEBIAN11'
				;;
			
			DEBIAN12)
				show_variant 'DEBIAN12'
				;;
			
			ORACLE7)
				show_variant 'ORACLE7'
				;;
			
			RHEL8)
				show_variant 'RHEL8'
				;;
			
			ROCKY8)
				show_variant 'ROCKY8'
				;;
			
			UBUNTU1604)
				show_variant 'UBUNTU1604'
				;;
			
			UBUNTU1804)
				show_variant 'UBUNTU1804'
				;;
			
			UBUNTU2004)
				show_variant 'UBUNTU2004'
				;;
			
			UBUNTU2110)
				show_variant 'UBUNTU2110'
				;;
			
			UBUNTU2204)
				show_variant 'UBUNTU2204'
				;;
			

			*)
				usage 1>&2
				exit 1
				;;
		esac
		;;

	*)
		usage 1>&2
		exit 1
		;;
esac
