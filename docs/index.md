<!--
SPDX-FileCopyrightText: 2021 - 2023  StorPool <support@storpool.com>
SPDX-License-Identifier: BSD-2-Clause
-->

# sp-variant - detect the Linux distribution for the StorPool build system

The `sp-variant` library is mainly useful within the StorPool internal
build and QA environment, as well as the first step of installations on
end-user systems. It examines several files and tries to determine what
distribution and what version it is running on.

## Basic command-line usage

- `sp_variant detect` - identify the current Linux distribution
- `sp_variant show current` - show JSON data about the current distribution
- `sp_variant show all` - show JSON data about all supported distributions
- `sp_variant show NAME` - show JSON data about a specific distribution
- `sp_variant command list` - show a list of distribution-specific commands
- `sp_variant command run category.item [arg...]` - run
  a distribution-specific command
- `sp_variant repo add` - add the Apt or Yum repository definitions for
  the StorPool package repository

## Basic Python API

The `sp_variant.variant` module exports several constants and functions,
among them:

- `detect_variant()` - return an object describing the detected distribution
- `get_variant()` - get an object describing the specified distribution
- `get_by_alias()` - same, but specify the StorPool builder alias for
  the distribution
- `get_all_variants()` - get objects describing all supported distributions
- `command_run()` - run a distribution-specific command

## Basic Rust API

The `sp-variant` crate exports several constants and functions, among them:

- `build_variants()` - return information about all supported variants
- `detect()` - get an object describing the detected distribution
- `get_from()` - get an object describing the specified distribution
- `get_by_alias_from()` - same, but specify the StorPool builder alias for
  the distribution

For more information, as well as for suggestions and problem reports, please
contact [the StorPool support team](mailto:support@storpool.com).
