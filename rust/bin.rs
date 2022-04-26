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
// Turn on most of the clippy::restriction lints...
#![warn(clippy::exhaustive_enums)]
#![warn(clippy::exhaustive_structs)]
#![warn(clippy::integer_arithmetic)]
#![warn(clippy::missing_inline_in_public_items)]
#![warn(clippy::panic)]
#![warn(clippy::pattern_type_mismatch)]
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
#![allow(clippy::print_stdout)]
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

use std::borrow::ToOwned;
use std::collections::HashMap;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::os::unix::fs::PermissionsExt;
use std::os::unix::io::AsRawFd;
use std::os::unix::process::ExitStatusExt;
use std::path::Path;
use std::process::Command;

use clap::{App, Arg, ArgMatches, SubCommand};
use expect_exit::{ExpectedResult, ExpectedWithError};
use nix::unistd::{self, Gid, Uid};
use serde_json::json;

use sp_variant::{self, DebRepo, Repo, Variant, VariantDefTop, YumRepo};

#[derive(Debug)]
struct RepoType<'data> {
    name: &'data str,
    extension: &'data str,
}

#[derive(Debug)]
struct RepoAddConfig<'data> {
    noop: bool,
    repodir: String,
    repotype: &'data RepoType<'data>,
}

#[derive(Debug)]
struct CommandRunConfig {
    category: String,
    name: String,
    noop: bool,
    args: Vec<String>,
}

#[derive(Debug)]
struct ShowConfig {
    name: String,
}

#[derive(Debug)]
enum Mode<'data> {
    CommandList,
    CommandRun(CommandRunConfig),
    Detect,
    Features,
    RepoAdd(RepoAddConfig<'data>),
    Show(ShowConfig),
}

const REPO_TYPES: &[RepoType; 3] = &[
    RepoType {
        name: "contrib",
        extension: "",
    },
    RepoType {
        name: "staging",
        extension: "-staging",
    },
    RepoType {
        name: "infra",
        extension: "-infra",
    },
];

fn detect_variant(varfull: &VariantDefTop) -> &Variant {
    sp_variant::detect_from(varfull).or_exit_e_("Could not detect the current build variant")
}

fn cmd_features(varfull: &VariantDefTop) {
    let (major, minor) = sp_variant::get_format_version_from(varfull);
    let program_version = sp_variant::get_program_version_from(varfull);
    println!(
        "Features: format={}.{} variant={}",
        major, minor, program_version
    );
}

fn cmd_detect(varfull: &VariantDefTop) {
    let var = detect_variant(varfull);
    println!("{}", var.kind.as_ref());
}

fn run_command(cmdvec: &[String], action: &str, noop: bool) {
    let cmdstr = cmdvec.join(" ");
    if noop {
        println!("Would run `{}`", cmdstr);
        return;
    }

    let status = Command::new(&cmdvec[0])
        .args(&cmdvec[1..])
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
        let mut cmdvec: Vec<String> = var.commands["package"]["install"].clone();
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
            sources_base, config.repotype.extension, sources_ext
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
            yumdef_base, config.repotype.extension, yumdef_ext
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
                format!("--enablerepo=storpool-{}", config.repotype.name),
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
    if !fs::metadata(&vdir)
        .or_exit_e(|| format!("Could not examine {:?}", vdir))
        .is_dir()
    {
        expect_exit::die(&format!("Not a directory: {:?}", vdir));
    }
    match var.repo {
        Repo::Deb(ref deb) => repo_add_deb(var, config, &vdir, deb),
        Repo::Yum(ref yum) => repo_add_yum(config, &vdir, yum),
        _ => expect_exit::exit("Internal error: unhandled repo type"),
    }
}

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
    let mut cmd_vec: Vec<String> = match var.commands.get(&config.category) {
        Some(cmap) => match cmap.get(&config.name) {
            Some(cmd) => cmd.clone(),
            None => expect_exit::exit("Unknown command identifier"),
        },
        None => expect_exit::exit("Unknown command identifier"),
    };
    cmd_vec.extend(config.args);
    run_command(&cmd_vec, "Command failed", config.noop);
}

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

// This one could probably go away with a clap 3 refactoring... maybe.
#[allow(clippy::too_many_lines)]
fn main() {
    type Handler<'cmds> = &'cmds dyn Fn(&'cmds ArgMatches) -> Mode<'cmds>;

    fn get_subc_name<'cmds>(current: &'cmds SubCommand) -> (String, &'cmds ArgMatches<'cmds>) {
        match current.matches.subcommand {
            Some(ref next) => {
                let (next_name, matches) = get_subc_name(next);
                (format!("{}/{}", current.name, next_name), matches)
            }
            None => (current.name.clone(), &current.matches),
        }
    }

    let varfull = sp_variant::build_variants();
    let program_version = sp_variant::get_program_version_from(varfull);
    let app = {
        let valid_repo_types: Vec<&str> = REPO_TYPES.iter().map(|rtype| rtype.name).collect();
        App::new("storpool_variant")
            .version(program_version)
            .author("StorPool <support@storpool.com>")
            .about("storpool_variant: handle OS distribution- and version-specific tasks")
            .subcommand(
                SubCommand::with_name("command")
                    .about("Distribition-specific commands")
                    .subcommand(
                        SubCommand::with_name("list")
                            .about("List the distribution-specific commands"),
                    )
                    .subcommand(
                        SubCommand::with_name("run")
                            .about("Run a distribution-specific command")
                            .arg(
                                Arg::with_name("noop")
                                    .short("N")
                                    .long("noop")
                                    .help("No-operation mode; display what would be done"),
                            )
                            .arg(
                                Arg::with_name("command")
                                    .index(1)
                                    .required(true)
                                    .help("The identifier of the command to run"),
                            )
                            .arg(
                                Arg::with_name("args")
                                    .index(2)
                                    .multiple(true)
                                    .help("Arguments to pass to the command"),
                            ),
                    ),
            )
            .subcommand(
                SubCommand::with_name("detect")
                    .about("Detect the build variant for the current host"),
            )
            .subcommand(
                SubCommand::with_name("features")
                    .about("Display the features supported by storpool_variant"),
            )
            .subcommand(
                SubCommand::with_name("repo")
                    .about("StorPool repository-related commands")
                    .subcommand(
                        SubCommand::with_name("add")
                            .about("Install the StorPool repository configuration")
                            .arg(
                                Arg::with_name("noop")
                                    .short("N")
                                    .long("noop")
                                    .help("No-operation mode; display what would be done"),
                            )
                            .arg(
                                Arg::with_name("repodir")
                                    .short("d")
                                    .required(true)
                                    .takes_value(true)
                                    .value_name("REPODIR")
                                    .help("The path to the repo config directory"),
                            )
                            .arg(
                                Arg::with_name("repotype")
                                    .short("t")
                                    .takes_value(true)
                                    .value_name("REPOTYPE")
                                    .default_value("contrib")
                                    .possible_values(&valid_repo_types)
                                    .help("The type of the repository to add (default: contrib)"),
                            ),
                    ),
            )
            .subcommand(
                SubCommand::with_name("show")
                    .about("Display information about a build variant")
                    .arg(
                        Arg::with_name("name")
                            .index(1)
                            .required(true)
                            .help("the name of the build variant to query"),
                    ),
            )
    };
    let opt_matches = app.get_matches();

    #[allow(clippy::unwrap_used)]
    let cmds: Vec<(&str, Handler)> = vec![
        ("command/list", &|_matches| Mode::CommandList),
        ("command/run", &|matches| {
            let parts: Vec<&str> = matches.value_of("command").unwrap().split('.').collect();
            match parts.len() {
                2 => Mode::CommandRun(CommandRunConfig {
                    category: parts[0].to_owned(),
                    name: parts[1].to_owned(),
                    args: match matches.values_of("args") {
                        Some(args) => args.map(ToOwned::to_owned).collect(),
                        None => vec![],
                    },
                    noop: matches.is_present("noop"),
                }),
                _ => expect_exit::exit("Invalid command identifier, must be category.name"),
            }
        }),
        ("detect", &|_matches| Mode::Detect),
        ("features", &|_matches| Mode::Features),
        ("repo/add", &|matches| {
            Mode::RepoAdd(RepoAddConfig {
                noop: matches.is_present("noop"),
                repodir: matches.value_of("repodir").unwrap().to_owned(),
                repotype: {
                    let name = matches.value_of("repotype").unwrap();
                    REPO_TYPES.iter().find(|rtype| rtype.name == name).unwrap()
                },
            })
        }),
        ("show", &|matches| {
            Mode::Show(ShowConfig {
                name: matches.value_of("name").unwrap().to_owned(),
            })
        }),
    ];
    match opt_matches.subcommand {
        Some(ref subcommand) => {
            let (subc_name, subc_matches) = get_subc_name(subcommand);
            match cmds
                .iter()
                .find_map(|&(name, handler)| (*name == subc_name).then(|| handler))
            {
                Some(handler) => match handler(subc_matches) {
                    Mode::Features => cmd_features(varfull),
                    Mode::CommandList => cmd_command_list(varfull),
                    Mode::CommandRun(config) => cmd_command_run(varfull, config),
                    Mode::Detect => cmd_detect(varfull),
                    Mode::RepoAdd(config) => cmd_repo_add(varfull, &config),
                    Mode::Show(config) => cmd_show(varfull, &config),
                },
                None => expect_exit::exit(opt_matches.usage()),
            }
        }
        None => expect_exit::exit(opt_matches.usage()),
    }
}
