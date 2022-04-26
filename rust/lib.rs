/*
 * Copyright (c) 2021, 2022  StorPool <support@storpool.com>
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 */
//! Detect the OS distribution and version.

#![warn(missing_docs)]
// Turn on most of the clippy::restriction lints...
#![warn(clippy::exhaustive_enums)]
#![warn(clippy::exhaustive_structs)]
#![warn(clippy::integer_arithmetic)]
#![warn(clippy::missing_inline_in_public_items)]
#![warn(clippy::panic)]
#![warn(clippy::pattern_type_mismatch)]
#![warn(clippy::print_stdout)]
#![warn(clippy::shadow_reuse)]
#![warn(clippy::shadow_unrelated)]
#![warn(clippy::single_char_lifetime_names)]
#![warn(clippy::str_to_string)]
#![warn(clippy::string_slice)]
#![warn(clippy::string_to_string)]
#![warn(clippy::unwrap_used)]
#![warn(clippy::use_debug)]
#![warn(clippy::verbose_file_reads)]
// ...except for these ones.
#![allow(clippy::implicit_return)]
#![allow(clippy::indexing_slicing)]
#![allow(clippy::missing_docs_in_private_items)]
// Also turn on some of the clippy::pedantic lints.
#![warn(clippy::doc_markdown)]
#![warn(clippy::implicit_clone)]
#![warn(clippy::items_after_statements)]
#![warn(clippy::manual_assert)]
#![warn(clippy::match_bool)]
#![warn(clippy::missing_errors_doc)]
#![warn(clippy::must_use_candidate)]
#![warn(clippy::needless_pass_by_value)]
#![warn(clippy::redundant_closure_for_method_calls)]
#![warn(clippy::similar_names)]
#![warn(clippy::too_many_lines)]

use std::clone::Clone;
use std::collections::HashMap;
use std::error::Error;
use std::fs;
use std::io::{Error as IoError, ErrorKind};

use expect_exit::ExpectedResult;
use regex::RegexBuilder;
use serde::{Deserialize, Serialize};

#[macro_use]
extern crate quick_error;

#[macro_use]
extern crate lazy_static;

mod data;

pub mod yai;

#[cfg(test)]
pub mod tests;

pub use data::VariantKind;

quick_error! {
    /// An error that occurred while determining the Linux variant.
    #[derive(Debug)]
    #[non_exhaustive]
    pub enum VariantError {
        /// An invalid variant name was specified.
        BadVariant(name: String) {
            display("Unknown variant '{}'", name)
        }
        /// A file to be examined could not be read.
        FileRead(variant: String, filename: String, err: IoError) {
            display("Checking for {}: could not read {}: {}", variant, filename, err)
        }
        /// Unexpected error parsing the /etc/os-release file.
        OsRelease(err: Box<dyn Error>) {
            display("Could not parse the /etc/os-release file: {}", err)
        }
        /// None of the variants matched.
        UnknownVariant {
            display("Could not detect the current host's build variant")
        }
    }
}

/// The version of the variant definition format data.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct VariantFormatVersion {
    /// The version major number.
    pub major: u32,
    /// The version minor number.
    pub minor: u32,
}

/// The internal format of the variant definition format data.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct VariantFormat {
    /// The version of the metadata format.
    pub version: VariantFormatVersion,
}

#[derive(Debug, Serialize, Deserialize)]
struct VariantFormatTop {
    format: VariantFormat,
}

/// Check whether this host is running this particular OS variant.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Detect {
    /// The name of the file to read.
    pub filename: String,
    /// The regular expression pattern to look for in the file.
    pub regex: String,
    /// The "ID" field in the /etc/os-release file.
    pub os_id: String,
    /// The regular expression pattern for the "VERSION_ID" os-release field.
    pub os_version_regex: String,
}

/// Debian package repository data.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct DebRepo {
    /// The distribution codename (e.g. "buster").
    pub codename: String,
    /// The distribution vendor ("debian", "ubuntu", etc.).
    pub vendor: String,
    /// The APT sources list file to copy to /etc/apt/sources.list.d/.
    pub sources: String,
    /// The GnuPG keyring file to copy to /usr/share/keyrings/.
    pub keyring: String,
    /// OS packages that need to be installed before `apt-get update` is run.
    pub req_packages: Vec<String>,
}

/// Yum/DNF package repository data.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct YumRepo {
    /// The *.repo file to copy to /etc/yum.repos.d/.
    pub yumdef: String,
    /// The keyring file to copy to /etc/pki/rpm-gpg/.
    pub keyring: String,
}

/// OS package repository data.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
#[non_exhaustive]
pub enum Repo {
    /// Debian/Ubuntu repository data.
    Deb(DebRepo),
    /// CentOS/Oracle repository data.
    Yum(YumRepo),
}

/// StorPool builder data.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Builder {
    /// The builder name.
    pub alias: String,
    /// The base Docker image that the builder is generated from.
    pub base_image: String,
    /// The branch used by the sp-pkg tool to specify the variant.
    pub branch: String,
    /// The base kernel OS package.
    pub kernel_package: String,
    /// The name of the locale to use for clean UTF-8 output.
    pub utf8_locale: String,
}

/// A single StorPool build variant with all its options.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Variant {
    /// Which variant is that?
    #[serde(rename = "name")]
    pub kind: VariantKind,
    /// The human-readable description of the variant.
    pub descr: String,
    /// The OS "family" that this distribution belongs to.
    pub family: String,
    /// The name of the variant that this one is based on.
    pub parent: String,
    /// The ways to check whether we are running this variant.
    pub detect: Detect,
    /// The OS commands to execute for particular purposes.
    pub commands: HashMap<String, HashMap<String, Vec<String>>>,
    /// The minimum Python version that we can depend on.
    pub min_sys_python: String,
    /// The StorPool repository files to install.
    pub repo: Repo,
    /// The names of the packages to be used for this variant.
    pub package: HashMap<String, String>,
    /// The name of the directory to install systemd unit files to.
    pub systemd_lib: String,
    /// The filename extension of the OS packages ("deb", "rpm", etc.).
    pub file_ext: String,
    /// The type of initramfs-generating tools.
    pub initramfs_flavor: String,
    /// The data specific to the StorPool builder containers.
    pub builder: Builder,
}

/// The internal variant format data: all build variants, some more info.
#[derive(Debug, Serialize, Deserialize)]
pub struct VariantDefTop {
    format: VariantFormat,
    order: Vec<VariantKind>,
    variants: HashMap<VariantKind, Variant>,
    version: String,
}

/// Get the list of StorPool variants from the internal `data` module.
#[inline]
#[must_use]
pub fn build_variants() -> &'static VariantDefTop {
    data::get_variants()
}

/// Detect the variant that this host is currently running.
///
/// # Errors
/// Propagates any errors from [`detect_from()`].
#[inline]
pub fn detect() -> Result<Variant, Box<dyn Error>> {
    detect_from(build_variants()).map(Clone::clone)
}

/// Detect the current host's variant from the supplied data.
///
/// # Errors
/// May return a [`VariantError`], either "unknown variant" or a wrapper around
/// an underlying error condition:
/// - any `os-release` parse errors from [`crate::yai::parse()`] other than "file not found"
/// - I/O errors from reading the distribution-specific version files (e.g. `/etc/redhat-release`)
#[allow(clippy::missing_inline_in_public_items)]
pub fn detect_from(variants: &VariantDefTop) -> Result<&Variant, Box<dyn Error>> {
    match yai::parse("/etc/os-release") {
        Ok(data) => {
            if let Some(os_id) = data.get("ID") {
                if let Some(version_id) = data.get("VERSION_ID") {
                    for kind in &variants.order {
                        let var = &variants.variants[kind];
                        if var.detect.os_id != *os_id {
                            continue;
                        }
                        let re_ver = RegexBuilder::new(&var.detect.os_version_regex)
                            .ignore_whitespace(true)
                            .build()
                            .expect_result(|| {
                                format!(
                                    "Internal error: {}: could not parse '{}'",
                                    kind.as_ref(),
                                    var.detect.regex
                                )
                            })?;
                        if re_ver.is_match(version_id) {
                            return Ok(var);
                        }
                    }
                }
            }
            // Fall through to the PRETTY_NAME processing.
        }
        Err(err) => {
            let ignore = match err.downcast_ref::<IoError>() {
                Some(io_err) => io_err.kind() == ErrorKind::NotFound,
                None => false,
            };
            if !ignore {
                return Err(Box::new(VariantError::OsRelease(err)));
            }
        }
    }

    for kind in &variants.order {
        let var = &variants.variants[kind];
        let re_line = RegexBuilder::new(&var.detect.regex)
            .ignore_whitespace(true)
            .build()
            .expect_result(|| {
                format!(
                    "Internal error: {}: could not parse '{}'",
                    kind.as_ref(),
                    var.detect.regex
                )
            })?;
        match fs::read(&var.detect.filename) {
            Ok(file_bytes) => {
                if let Ok(contents) = String::from_utf8(file_bytes) {
                    {
                        if contents.lines().any(|line| re_line.is_match(line)) {
                            return Ok(var);
                        }
                    }
                }
            }
            Err(err) => {
                if err.kind() != ErrorKind::NotFound {
                    return Err(Box::new(VariantError::FileRead(
                        var.kind.as_ref().to_owned(),
                        var.detect.filename.clone(),
                        err,
                    )));
                }
            }
        };
    }
    Err(Box::new(VariantError::UnknownVariant))
}

/// Get the variant with the specified name from the supplied data.
///
/// # Errors
/// - [`VariantKind`] name parse errors, e.g. invalid name
/// - an internal error if there is no data about a recognized variant name
#[inline]
pub fn get_from<'defs>(
    variants: &'defs VariantDefTop,
    name: &str,
) -> Result<&'defs Variant, Box<dyn Error>> {
    let kind: VariantKind = name.parse()?;
    variants
        .variants
        .get(&kind)
        .expect_result(|| format!("No data for the {} variant", name))
}

/// Get the variant with the specified builder alias from the supplied data.
///
/// # Errors
/// May fail if the argument does not specify a recognized variant builder alias.
#[inline]
pub fn get_by_alias_from<'defs>(
    variants: &'defs VariantDefTop,
    alias: &str,
) -> Result<&'defs Variant, Box<dyn Error>> {
    variants
        .variants
        .values()
        .find(|var| var.builder.alias == alias)
        .expect_result(|| format!("No variant with the {} alias", alias))
}

/// Get the metadata format version of the variant data.
#[inline]
#[must_use]
pub fn get_format_version() -> (u32, u32) {
    get_format_version_from(build_variants())
}

/// Get the metadata format version of the supplied variant data structure.
#[inline]
#[must_use]
pub const fn get_format_version_from(variants: &VariantDefTop) -> (u32, u32) {
    (variants.format.version.major, variants.format.version.minor)
}

/// Get the program version from the variant data.
#[inline]
#[must_use]
pub fn get_program_version() -> &'static str {
    get_program_version_from(build_variants())
}

/// Get the program version from the supplied variant data structure.
#[inline]
#[must_use]
pub fn get_program_version_from(variants: &VariantDefTop) -> &str {
    &variants.version
}
