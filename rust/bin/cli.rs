/*
 * SPDX-FileCopyrightText: 2022, 2024  StorPool <support@storpool.com>
 * SPDX-License-Identifier: BSD-2-Clause
 */

use std::str::FromStr;

use clap::Parser;
use clap_derive::{Parser, Subcommand};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum ParseError {
    #[error("The command identifier must consist of exactly two parts separated by a dot")]
    CommandIdNeedsTwo,

    #[error(
        "Unrecognized repository type, must be one of {}, {}, or {}",
        RepoType::CONTRIB,
        RepoType::STAGING,
        RepoType::INFRA
    )]
    RepoTypeUnknown,
}

#[derive(Debug, Clone)]
pub enum RepoType {
    Contrib,
    Staging,
    Infra,
}

impl RepoType {
    pub const CONTRIB: &'static str = "contrib";
    pub const STAGING: &'static str = "staging";
    pub const INFRA: &'static str = "infra";

    pub const EXT_CONTRIB: &'static str = "";
    pub const EXT_STAGING: &'static str = "-staging";
    pub const EXT_INFRA: &'static str = "-infra";

    pub const fn extension(&self) -> &str {
        match *self {
            Self::Contrib => Self::EXT_CONTRIB,
            Self::Staging => Self::EXT_STAGING,
            Self::Infra => Self::EXT_INFRA,
        }
    }
}

impl AsRef<str> for RepoType {
    fn as_ref(&self) -> &str {
        match *self {
            Self::Contrib => Self::CONTRIB,
            Self::Staging => Self::STAGING,
            Self::Infra => Self::INFRA,
        }
    }
}

impl FromStr for RepoType {
    type Err = ParseError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            Self::CONTRIB => Ok(Self::Contrib),
            Self::STAGING => Ok(Self::Staging),
            Self::INFRA => Ok(Self::Infra),
            _ => Err(ParseError::RepoTypeUnknown),
        }
    }
}

#[derive(Debug)]
pub struct RepoAddConfig {
    pub noop: bool,
    pub repodir: String,
    pub repotype: RepoType,
}

#[derive(Debug)]
pub struct CommandRunConfig {
    pub category: String,
    pub name: String,
    pub noop: bool,
    pub args: Vec<String>,
}

#[derive(Debug)]
pub struct ShowConfig {
    pub name: String,
}

#[derive(Debug)]
pub enum Mode {
    CommandList,
    CommandRun(CommandRunConfig),
    Detect,
    Features,
    RepoAdd(RepoAddConfig),
    Show(ShowConfig),
}

#[derive(Debug, Clone)]
struct CommandId {
    category: String,
    name: String,
}

impl FromStr for CommandId {
    type Err = ParseError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let fields: Vec<&str> = value.split('.').collect();
        match *fields {
            [category, name] => Ok(Self {
                category: (*category).to_owned(),
                name: (*name).to_owned(),
            }),
            _ => Err(ParseError::CommandIdNeedsTwo),
        }
    }
}

#[derive(Debug, Subcommand)]
enum CommandCommand {
    /// List the distribution-specific commands.
    List,

    /// Run a distribution-specific command.
    Run {
        /// No-operation mode; display what would be done.
        #[clap(short('N'), long)]
        noop: bool,

        /// The identifier of the command to run.
        command: CommandId,

        /// Arguments to pass to the command.
        args: Vec<String>,
    },
}

#[derive(Debug, Subcommand)]
enum RepoCommand {
    /// Install the StorPool repository configuration.
    Add {
        /// No-operation mode; display what would be done.
        #[clap(short('N'), long)]
        noop: bool,

        /// The path to the repo config directory.
        #[clap(short('d'), required(true))]
        repodir: String,

        /// The type of the repository to add (default: contrib).
        #[clap(short('t'), default_value("contrib"))]
        repotype: RepoType,
    },
}

#[derive(Debug, Subcommand)]
enum CliCommand {
    /// Distribution-specific commands.
    Command {
        #[clap(subcommand)]
        subc: CommandCommand,
    },

    /// Detect the build variant for the current host.
    Detect,

    /// Display the features supported by storpool_variant.
    Features,

    /// StorPool repository-related commands.
    Repo {
        #[clap(subcommand)]
        subc: RepoCommand,
    },

    /// Display information about a build variant.
    Show {
        /// The name of the build variant to query.
        name: String,
    },
}

#[derive(Debug, Parser)]
#[clap(
    about("storpool_variant: handle OS distribution- and version-specific tasks"),
    author("StorPool <support@storpool.com>"),
    name("storpool_variant"),
    version(sp_variant::get_program_version())
)]
pub struct Cli {
    #[clap(subcommand)]
    command: CliCommand,
}

pub fn parse() -> Mode {
    let opts = Cli::parse();

    match opts.command {
        CliCommand::Command { subc } => match subc {
            CommandCommand::List => Mode::CommandList,
            CommandCommand::Run {
                noop,
                command,
                args,
            } => Mode::CommandRun(CommandRunConfig {
                category: command.category,
                name: command.name,
                noop,
                args,
            }),
        },
        CliCommand::Detect => Mode::Detect,
        CliCommand::Features => Mode::Features,
        CliCommand::Show { name } => Mode::Show(ShowConfig { name }),
        CliCommand::Repo { subc } => match subc {
            RepoCommand::Add {
                noop,
                repodir,
                repotype,
            } => Mode::RepoAdd(RepoAddConfig {
                noop,
                repodir,
                repotype,
            }),
        },
    }
}
