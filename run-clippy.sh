#!/bin/sh

set -e

usage()
{
	cat <<'EOUSAGE'
Usage:	run-clippy.sh [-c cargo] [-n]
	-c	specify the Cargo command to use
	-n	also warn about lints in the Clippy "nursery" category
EOUSAGE
}

unset run_nursery
cargo='sp-cargo'

while getopts 'c:n' o; do
	case "$o" in
		c)
			cargo="$OPTARG"
			;;

		n)
			run_nursery=1
			;;

		*)
			usage 1>&2
			exit 1
			;;
	esac
done

"$cargo" clippy -- \
	-W warnings \
	-W future-incompatible \
	-W nonstandard-style \
	-W rust-2018-compatibility \
	-W rust-2018-idioms \
	-W rust-2021-compatibility \
	-W unused \
	-W clippy::restriction \
		-A clippy::blanket_clippy_restriction_lints \
		-A clippy::implicit_return \
		-A clippy::missing_docs_in_private_items \
		-A clippy::std_instead_of_alloc \
		-A clippy::std_instead_of_core \
	-W clippy::pedantic \
	${run_nursery+-W clippy::nursery}
