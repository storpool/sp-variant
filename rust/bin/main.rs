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
//! Perform tasks related to the OS distribution and version.
//!
//! The `storpool_variant` tool may be used to:
//! - detect the OS variant running on the current host
//! - install the StorPool repository definition files
//! - run distribution-specific commands (e.g. install a set of packages)
//! - display the OS variant data as a JSON object

#![warn(missing_docs)]

use std::borrow::ToOwned;
use std::collections::HashMap;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::os::unix::fs::PermissionsExt;
use std::os::unix::io::AsRawFd;
use std::os::unix::process::ExitStatusExt;
use std::path::Path;
use std::process::Command;

use expect_exit::{Expected, ExpectedResult, ExpectedWithError};
use nix::unistd::{self, Gid, Uid};
use serde_json::json;

use sp_variant::{self, DebRepo, Repo, Variant, VariantDefTop, YumRepo};

mod cli;

use cli::{CommandRunConfig, Mode, RepoAddConfig, ShowConfig};

fn detect_variant(varfull: &VariantDefTop) -> &Variant {
    sp_variant::detect_from(varfull).or_exit_e_("Could not detect the current build variant")
}

#[allow(clippy::print_stdout)]
fn cmd_features(varfull: &VariantDefTop) {
    let (major, minor) = sp_variant::get_format_version_from(varfull);
    let program_version = sp_variant::get_program_version_from(varfull);
    println!(
        "Features: format={}.{} variant={}",
        major, minor, program_version
    );
}

#[allow(clippy::print_stdout)]
fn cmd_detect(varfull: &VariantDefTop) {
    let var = detect_variant(varfull);
    println!("{}", var.kind.as_ref());
}

#[allow(clippy::print_stdout)]
fn run_command(cmdvec: &[String], action: &str, noop: bool) {
    let cmdstr = cmdvec.join(" ");
    if noop {
        println!("Would run `{}`", cmdstr);
        return;
    }

    let (name, args) = cmdvec
        .split_first()
        .or_exit(|| format!("Internal error: empty '{}' command", action));
    let status = Command::new(&name)
        .args(args)
        .spawn()
        .or_exit_e(|| format!("{}: {}", action, cmdstr))
        .wait()
        .or_exit_e(|| format!("{}: {}", action, cmdstr));

    if !status.success() {
        match status.signal() {
            None => match status.code() {
                Some(code) => {
                    expect_exit::exit(&format!("{}: {}: exit code {}", action, cmdstr, code))
                }
                None => {
                    expect_exit::exit(&format!("{}: {}: exit status {:?}", action, cmdstr, status))
                }
            },
            Some(sig) => {
                expect_exit::exit(&format!("{}: {}: killed by signal {}", action, cmdstr, sig))
            }
        }
    }
}

#[allow(clippy::print_stdout)]
fn copy_file(fname: &str, srcdir: &str, dstdir: &str, noop: bool) {
    let src = format!("{}/{}", srcdir, fname);
    let dst = format!("{}/{}", dstdir, fname);
    println!("Copying {} -> {}", src, dst);

    let read_source_file = || fs::read(&src).or_exit_e(|| format!("Could not read from {}", src));

    let write_destination_file = |contents: &Vec<u8>| {
        let mut outfile = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .open(&dst)
            .or_exit_e(|| format!("Could not open {} for writing", dst));
        let mut perms = outfile
            .metadata()
            .or_exit_e(|| format!("Could not examine the newly-created {}", dst))
            .permissions();
        perms.set_mode(0o644);
        outfile
            .set_permissions(perms)
            .or_exit_e(|| format!("Could not change the mode on {}", dst));
        unistd::fchown(
            outfile.as_raw_fd(),
            Some(Uid::from_raw(0)),
            Some(Gid::from_raw(0)),
        )
        .or_exit_e(|| format!("Could not set the ownership of {}", dst));
        outfile
            .write_all(contents)
            .or_exit_e(|| format!("Could not write to {}", dst));
    };

    let contents = read_source_file();

    if noop {
        println!("Would write {} bytes to {}", contents.len(), dst);
        return;
    }

    write_destination_file(&contents);
}

fn get_filename<'path>(path: &'path str, tag: &str) -> &'path str {
    path.rsplit('/')
        .next()
        .expect_result(|| format!("Could not obtain a filename from '{}'", path))
        .or_exit_e(|| format!("Internal error: could not parse a {}", tag))
}

fn get_filename_extension<'fname>(filename: &'fname str, tag: &str) -> (&'fname str, &'fname str) {
    filename
        .rsplit_once('.')
        .expect_result(|| {
            format!(
                "Could not split '{}' into a filename and extension",
                filename
            )
        })
        .or_exit_e(|| format!("Internal error: could not parse a {}", tag))
}

fn repo_add_deb(var: &Variant, config: &RepoAddConfig, vdir: &str, repo: &DebRepo) {
    let install_req_packages = || {
        // First, install the ca-certificates package if required...
        let mut cmdvec: Vec<String> = var
            .commands
            .get("package")
            .or_exit(|| {
                format!(
                    "Internal error: no 'package' command category for {}",
                    var.kind.as_ref()
                )
            })
            .get("install")
            .or_exit(|| {
                format!(
                    "Internal error: no 'package.install' command for {}",
                    var.kind.as_ref()
                )
            })
            .clone();
        cmdvec.extend(repo.req_packages.iter().cloned());
        run_command(
            &cmdvec,
            "Could not install the required packages",
            config.noop,
        );
    };

    let copy_sources_file = || {
        let sources_orig = get_filename(&repo.sources, "Apt sources list");
        let (sources_base, sources_ext) = get_filename_extension(sources_orig, "Apt sources list");
        let sources_fname = format!(
            "{}{}.{}",
            sources_base,
            config.repotype.extension(),
            sources_ext
        );
        copy_file(&sources_fname, vdir, "/etc/apt/sources.list.d", config.noop);
    };

    let copy_keyring_file = || {
        let keyring_fname = get_filename(&repo.keyring, "Apt keyring");
        copy_file(keyring_fname, vdir, "/usr/share/keyrings", config.noop);
    };

    let run_apt_update = || {
        run_command(
            &["apt-get".to_owned(), "update".to_owned()],
            "Could not update the package database",
            config.noop,
        );
    };

    if !repo.req_packages.is_empty() {
        run_apt_update();
        install_req_packages();
    }
    copy_sources_file();
    copy_keyring_file();
    run_apt_update();
}

fn repo_add_yum(config: &RepoAddConfig, vdir: &str, repo: &YumRepo) {
    let run_yum_install_certs = || {
        run_command(
            &[
                "yum".to_owned(),
                "--disablerepo=storpool-*".to_owned(),
                "install".to_owned(),
                "-q".to_owned(),
                "-y".to_owned(),
                "ca-certificates".to_owned(),
            ],
            "Could not update the package database",
            config.noop,
        );
    };

    let copy_yumdef_file = || {
        let yumdef_orig = get_filename(&repo.yumdef, "Yum repository definition");
        let (yumdef_base, yumdef_ext) =
            get_filename_extension(yumdef_orig, "Yum repository definition");
        let yumdef_fname = format!(
            "{}{}.{}",
            yumdef_base,
            config.repotype.extension(),
            yumdef_ext
        );
        copy_file(&yumdef_fname, vdir, "/etc/yum.repos.d", config.noop);
    };

    let keyring_fname = get_filename(&repo.keyring, "Yum keyring");
    let copy_keyring_file = || {
        copy_file(keyring_fname, vdir, "/etc/pki/rpm-gpg", config.noop);
    };

    let run_rpmkeys = || {
        if Path::new("/usr/bin/rpmkeys").exists() {
            run_command(
                &[
                    "rpmkeys".to_owned(),
                    "--import".to_owned(),
                    format!("/etc/pki/rpm-gpg/{}", keyring_fname),
                ],
                "Could not import the StorPool RPM OpenPGP keys",
                config.noop,
            );
        }
    };

    let run_yum_clean_metadata = || {
        run_command(
            &[
                "yum".to_owned(),
                "--disablerepo=*".to_owned(),
                format!("--enablerepo=storpool-{}", config.repotype.as_ref()),
                "clean".to_owned(),
                "metadata".to_owned(),
            ],
            "Could not update the package database",
            config.noop,
        );
    };

    run_yum_install_certs();
    copy_yumdef_file();
    copy_keyring_file();
    run_rpmkeys();
    run_yum_clean_metadata();
}

fn cmd_repo_add(varfull: &VariantDefTop, config: &RepoAddConfig) {
    let var = detect_variant(varfull);
    let vdir = format!("{}/{}", config.repodir, var.kind.as_ref());
    fs::metadata(&vdir)
        .or_exit_e(|| format!("Could not examine {:?}", vdir))
        .is_dir()
        .or_exit(|| format!("Not a directory: {:?}", vdir));
    match var.repo {
        Repo::Deb(ref deb) => repo_add_deb(var, config, &vdir, deb),
        Repo::Yum(ref yum) => repo_add_yum(config, &vdir, yum),
        _ => expect_exit::exit("Internal error: unhandled repo type"),
    }
}

#[allow(clippy::print_stdout)]
fn cmd_command_list(varfull: &VariantDefTop) {
    fn sorted_by_key<K, T>(map: &HashMap<K, T>) -> Vec<(&K, &T)>
    where
        K: Ord,
    {
        let mut res: Vec<_> = map.iter().collect();
        res.sort_by_key(|&(key, _)| key);
        res
    }

    let var = detect_variant(varfull);
    for (category, cmap) in sorted_by_key(&var.commands) {
        for (name, cmd) in sorted_by_key(cmap) {
            if category == "pkgfile" && name == "install" {
                println!("{}.{}: ...", category, name);
            } else {
                println!("{}.{}: {}", category, name, cmd.join(" "));
            }
        }
    }
}

fn cmd_command_run(varfull: &VariantDefTop, config: CommandRunConfig) {
    let var = detect_variant(varfull);
    let cmap = var
        .commands
        .get(&config.category)
        .or_exit_("Unknown command category identifier");
    let mut cmd_vec: Vec<String> = cmap
        .get(&config.name)
        .or_exit_("Unknown command identifier")
        .clone();
    cmd_vec.extend(config.args);
    run_command(&cmd_vec, "Command failed", config.noop);
}

#[allow(clippy::print_stdout)]
fn cmd_show(varfull: &VariantDefTop, config: &ShowConfig) {
    if config.name == "all" {
        print!(
            "{}",
            serde_json::to_string(varfull)
                .or_exit_e_("Internal error: could not serialize the variant data")
        );
    } else {
        let var = match &*config.name {
            "current" => {
                sp_variant::detect_from(varfull).or_exit_e_("Cannot detect the current variant")
            }
            other => sp_variant::get_from(varfull, other).or_exit_e_("Invalid variant name"),
        };
        let (major, minor) = sp_variant::get_format_version_from(varfull);
        let single = json!({
            "format": {
                "version": {
                    "major": major,
                    "minor": minor,
                },
            },
            "variant": var.clone(),
            "version": sp_variant::get_program_version().to_owned(),
        });
        println!(
            "{}",
            serde_json::to_string_pretty(&single)
                .or_exit_e_("Internal error: could not serialize the variant data")
        );
    }
}

fn main() {
    let varfull = sp_variant::build_variants();
    match cli::parse() {
        Mode::Features => cmd_features(varfull),
        Mode::CommandList => cmd_command_list(varfull),
        Mode::CommandRun(config) => cmd_command_run(varfull, config),
        Mode::Detect => cmd_detect(varfull),
        Mode::RepoAdd(config) => cmd_repo_add(varfull, &config),
        Mode::Show(config) => cmd_show(varfull, &config),
    }
}