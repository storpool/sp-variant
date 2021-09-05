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

pub mod data;

#[cfg(test)]
pub mod tests;

pub use data::VariantKind;

/// The features supported by this module and the storpool_variant executable.
pub const FEATURES: [(&str, &str); 1] = [("variant", "1.2")];

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
        /// None of the variants matched.
        UnknownVariant {
            display("Could not detect the current host's build variant")
        }
    }
}

/// The version of the variant definition format data.
#[derive(Debug, Serialize, Deserialize)]
pub struct VariantFormatVersion {
    major: u32,
    minor: u32,
}

/// The internal format of the variant definition format data.
#[derive(Debug, Serialize, Deserialize)]
pub struct VariantFormat {
    version: VariantFormatVersion,
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

/// A single StorPool build variant with all its options.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Variant {
    /// Which variant is that?
    #[serde(rename = "name")]
    pub kind: VariantKind,
    /// The OS "family" that this distribution belongs to.
    pub family: String,
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
}

/// The internal variant format data: all build variants, some more info.
#[derive(Debug, Serialize, Deserialize)]
pub struct VariantDefTop {
    format: VariantFormat,
    order: Vec<VariantKind>,
    variants: HashMap<VariantKind, Variant>,
}

/// Build the list of StorPool variants from the JSON description
/// in the [`crate::data`] module.
pub fn build_variants() -> VariantDefTop {
    let json_bytes = data::get_json_def();
    let fmt_top: VariantFormatTop = serde_json::from_slice(&json_bytes).unwrap();
    if fmt_top.format.version.major != 1 {
        panic!(
            "Internal error: JSON variant definition: version {:?}",
            fmt_top.format.version
        );
    }
    serde_json::from_slice(&json_bytes).unwrap()
}

/// Detect the variant that this host is currently running.
pub fn detect() -> Result<Variant, Box<dyn error::Error>> {
    detect_from(&build_variants()).map(|var| var.clone())
}

/// Detect the current host's variant from the supplied data.
pub fn detect_from(variants: &VariantDefTop) -> Result<&Variant, Box<dyn error::Error>> {
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
