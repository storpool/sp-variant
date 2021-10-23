#![warn(missing_docs)]
//! Detect the OS distribution and version.

/*
 * Copyright (c) 2021  StorPool.
 * All rights reserved.
 */

use std::collections::HashMap;
use std::error;
use std::fs;
use std::io;

use expect_exit::ExpectedResult;
use serde::{Deserialize, Serialize};

#[macro_use]
extern crate quick_error;

#[macro_use]
extern crate lazy_static;

pub mod data;
pub mod yai;

#[cfg(test)]
pub mod tests;

pub use data::VariantKind;

quick_error! {
    /// An error that occurred while determining the Linux variant.
    #[derive(Debug)]
    pub enum VariantError {
        /// An invalid variant name was specified.
        BadVariant(name: String) {
            display("Unknown variant '{}'", name)
        }
        /// A file to be examined could not be read.
        FileRead(variant: String, filename: String, err: io::Error) {
            display("Checking for {}: could not read {}: {}", variant, filename, err)
        }
        /// Unexpected error parsing the /etc/os-release file.
        OsRelease(err: Box<dyn error::Error>) {
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
pub struct VariantFormatVersion {
    /// The version major number.
    pub major: u32,
    /// The version minor number.
    pub minor: u32,
}

/// The internal format of the variant definition format data.
#[derive(Debug, Clone, Serialize, Deserialize)]
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
pub struct YumRepo {
    /// The *.repo file to copy to /etc/yum.repos.d/.
    pub yumdef: String,
    /// The keyring file to copy to /etc/pki/rpm-gpg/.
    pub keyring: String,
}

/// OS package repository data.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum Repo {
    /// Debian/Ubuntu repository data.
    Deb(DebRepo),
    /// CentOS/Oracle repository data.
    Yum(YumRepo),
}

/// StorPool builder data.
#[derive(Debug, Clone, Serialize, Deserialize)]
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

/// Build the list of StorPool variants from the JSON description
/// in the [`crate::data`] module.
pub fn build_variants() -> &'static VariantDefTop {
    lazy_static! {
        static ref JSON_BYTES: Vec<u8> = data::get_json_def();
        static ref FMT_TOP: VariantFormatTop = serde_json::from_slice(&JSON_BYTES).unwrap();
    }
    if FMT_TOP.format.version.major != 1 {
        panic!(
            "Internal error: JSON variant definition: version {:?}",
            FMT_TOP.format.version
        );
    }
    lazy_static! {
        static ref DEF_TOP: VariantDefTop = serde_json::from_slice(&JSON_BYTES).unwrap();
    }
    &DEF_TOP
}

/// Detect the variant that this host is currently running.
pub fn detect() -> Result<Variant, Box<dyn error::Error>> {
    detect_from(build_variants()).map(|var| var.clone())
}

/// Detect the current host's variant from the supplied data.
pub fn detect_from(variants: &VariantDefTop) -> Result<&Variant, Box<dyn error::Error>> {
    match yai::parse("/etc/os-release") {
        Ok(data) => {
            if let Some(os_id) = data.get("ID") {
                if let Some(version_id) = data.get("VERSION_ID") {
                    for kind in &variants.order {
                        let var = &variants.variants[kind];
                        if var.detect.os_id != *os_id {
                            continue;
                        }
                        let re_ver = regex::RegexBuilder::new(&var.detect.os_version_regex)
                            .ignore_whitespace(true)
                            .build()
                            .unwrap();
                        if re_ver.is_match(version_id) {
                            return Ok(var);
                        }
                    }
                }
            }
            // Fall through to the PRETTY_NAME processing.
        }
        Err(err) => {
            let ignore = match err.downcast_ref::<io::Error>() {
                Some(io_err) => io_err.kind() == io::ErrorKind::NotFound,
                None => false,
            };
            if !ignore {
                return Err(Box::new(VariantError::OsRelease(err)));
            }
        }
    }

    for kind in &variants.order {
        let var = &variants.variants[kind];
        let re_line = regex::RegexBuilder::new(&var.detect.regex)
            .ignore_whitespace(true)
            .build()
            .unwrap();
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
                if err.kind() != io::ErrorKind::NotFound {
                    return Err(Box::new(VariantError::FileRead(
                        var.kind.as_ref().to_string(),
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
pub fn get_from<'a>(
    variants: &'a VariantDefTop,
    name: &str,
) -> Result<&'a Variant, Box<dyn error::Error>> {
    let kind: VariantKind = name.parse()?;
    variants
        .variants
        .get(&kind)
        .expect_result(|| format!("No data for the {} variant", name))
}

/// Get the variant with the specified builder alias from the supplied data.
pub fn get_by_alias_from<'a>(
    variants: &'a VariantDefTop,
    alias: &str,
) -> Result<&'a Variant, Box<dyn error::Error>> {
    variants
        .variants
        .values()
        .find(|var| var.builder.alias == alias)
        .expect_result(|| format!("No variant with the {} alias", alias))
}

/// Get the metadata format version of the variant data.
pub fn get_format_version() -> (u32, u32) {
    get_format_version_from(build_variants())
}

/// Get the metadata format version of the supplied variant data structure.
pub fn get_format_version_from(variants: &VariantDefTop) -> (u32, u32) {
    (variants.format.version.major, variants.format.version.minor)
}

/// Get the program version from the variant data.
pub fn get_program_version() -> String {
    get_program_version_from(build_variants()).clone()
}

/// Get the program version from the supplied variant data structure.
pub fn get_program_version_from(variants: &VariantDefTop) -> &String {
    &variants.version
}
