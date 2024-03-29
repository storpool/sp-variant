/*
 * SPDX-FileCopyrightText: 2021 - 2023  StorPool <support@storpool.com>
 * SPDX-License-Identifier: BSD-2-Clause
 */
//! Yet another INI-like file parser.
//!
//! This one is specifically written for the somewhat simplified format of
//! the os-release file as found in recent Linux distributions.

use std::collections::HashMap;
use std::fs;
use std::io::Error as IoError;
use std::path::Path;

use once_cell::sync::Lazy;
use regex::{Error as RegexError, Regex};
use thiserror::Error;

/// An error that occurred during parsing.
#[derive(Debug, Error)]
#[non_exhaustive]
pub enum YAIError {
    /// A backslash at the end of the line.
    #[error("Backslash at the end of the {0:?} os-release line")]
    BackslashAtEnd(String),

    /// An invalid line in the /etc/os-release file.
    #[error("Unexpected os-release line {0:?}")]
    BadLine(String),

    /// A quoted value contains the quote character.
    #[error("The value in the {0:?} os-release line contains the quote character")]
    QuoteInQuoted(String),

    /// Mismatched open/close quotes.
    #[error("Mismatched open/close quotes in the {0:?} os-release line")]
    MismatchedQuotes(String),

    /// Could not read the /etc/os-release file.
    #[error("Could not read the /etc/os-release file")]
    FileRead(#[source] IoError),

    /// An internal error occurred
    #[error("YAI parser internal error: {0}")]
    Internal(String),
}

const RE_LINE: &str = "(?x)
    ^ (?:
        (?P<comment> \\s* (?: \\# .* )? )
        |
        (?:
            (?P<varname> [A-Za-z0-9_]+ )
            =
            (?P<full>
                (?P<q_open> [\"'] )?
                (?P<quoted> .*? )
                (?P<q_close> [\"'] )?
            )
        )
    ) $
";

fn parse_line(line: &str) -> Result<Option<(String, String)>, YAIError> {
    static RE: Lazy<Result<Regex, RegexError>> = Lazy::new(|| Regex::new(RE_LINE));
    match RE
        .as_ref()
        .map_err(|err| YAIError::Internal(format!("Could not parse '{RE_LINE}': {err}")))?
        .captures(line)
    {
        Some(caps) => {
            let cap = |name: &str| -> Result<&str, YAIError> {
                Ok(caps
                    .name(name)
                    .ok_or_else(|| YAIError::Internal(format!("No '{name}' in {caps:?}")))?
                    .as_str())
            };

            if caps.name("comment").is_some() {
                return Ok(None);
            }
            let q_open = caps.name("q_open").map(|value| value.as_str());
            let q_close = caps.name("q_close").map(|value| value.as_str());
            let varname = cap("varname")?;
            let quoted_top = cap("quoted")?;

            if q_open == Some("'") {
                if quoted_top.contains('\'') {
                    return Err(YAIError::QuoteInQuoted(line.to_owned()));
                }
                if q_close != q_open {
                    return Err(YAIError::MismatchedQuotes(line.to_owned()));
                }
                return Ok(Some((varname.to_owned(), quoted_top.to_owned())));
            }

            let quoted = match q_open {
                Some("\"") => {
                    if q_close != q_open {
                        return Err(YAIError::MismatchedQuotes(line.to_owned()));
                    }
                    quoted_top
                }
                Some(other) => {
                    return Err(YAIError::Internal(format!(
                        "YAI parse_line: {line:?}: q_open {other:?}"
                    )))
                }
                None => cap("full")?,
            }
            .to_owned();
            match quoted
                .chars()
                .fold((false, String::new()), |(escaped, mut acc), chr| {
                    if escaped || chr != '\\' {
                        acc.push(chr);
                        (false, acc)
                    } else {
                        (true, acc)
                    }
                }) {
                (false, res) => Ok(Some((varname.to_owned(), res))),
                (true, _) => Err(YAIError::BackslashAtEnd(line.to_owned())),
            }
        }
        None => Err(YAIError::BadLine(line.to_owned())),
    }
}

/// Parse a file, return a name: value mapping.
///
/// # Errors
/// - I/O or text decoding errors from reading the file
/// - [`YAIError`] parse errors from examining the INI-file structure
#[allow(clippy::missing_inline_in_public_items)]
pub fn parse<P: AsRef<Path>>(path: P) -> Result<HashMap<String, String>, YAIError> {
    fs::read_to_string(path)
        .map_err(YAIError::FileRead)?
        .lines()
        .filter_map(|line| parse_line(line).transpose())
        .collect()
}

#[cfg(test)]
mod tests {
    #![allow(clippy::print_stdout)]
    #![allow(clippy::use_debug)]

    use std::error::Error;
    use std::fs;

    const LINES_BAD: [&str; 5] = [
        "NAME='",
        "NAME=\"foo'",
        "FOO BAR=baz",
        "FOO=bar\\",
        "FOO=\"meow\\\"",
    ];

    const LINES_COMMENTS: [&str; 4] = ["", "   \t  ", "  \t  # something", "#"];

    const LINES_OK: [(&str, (&str, &str)); 5] = [
        ("ID=centos", ("ID", "centos")),
        ("ID='centos'", ("ID", "centos")),
        (
            "NAME='something long \"and weird'",
            ("NAME", "something long \"and weird"),
        ),
        (
            "NAME=\"something long \'and \\\\weird\\\"\\`\"",
            ("NAME", "something long 'and \\weird\"`"),
        ),
        (
            "NAME=unquoted\\\"and\\\\-escaped\\'",
            ("NAME", "unquoted\"and\\-escaped'"),
        ),
    ];

    const CFG_TEXT: &str = "PRETTY_NAME=\"Debian GNU/Linux 11 (bullseye)\"
NAME=\"Debian GNU/Linux\"
VERSION_ID=\"11\"
VERSION=\"11 (bullseye)\"
VERSION_CODENAME=bullseye
ID=debian
HOME_URL=\"https://www.debian.org/\"
SUPPORT_URL=\"https://www.debian.org/support\"
BUG_REPORT_URL=\"https://bugs.debian.org/\"";

    const CFG_EXPECTED: [(&str, Option<&str>); 4] = [
        ("ID", Some("debian")),
        ("VERSION_ID", Some("11")),
        ("VERSION", Some("11 (bullseye)")),
        ("FOO", None),
    ];

    #[test]
    fn parse_bad() {
        println!("\nMaking sure malformed lines are rejected");
        for line in &LINES_BAD {
            println!("- {line:?}");
            super::parse_line(line).unwrap_err();
        }
    }

    #[test]
    fn parse_comments() {
        println!("\nMaking sure comments and empty lines are ignored");
        for line in &LINES_COMMENTS {
            println!("- {line:?}");
            let res = super::parse_line(line).unwrap();
            println!("  - {res:?}");
            assert_eq!(res, None);
        }
    }

    #[test]
    fn parse_good() {
        println!("\nMaking sure well-formed lines are parsed correctly");
        for (line, (varname, value)) in &LINES_OK {
            println!("- {line:?}");
            let (p_varname, p_value) = super::parse_line(line).unwrap().unwrap();
            println!("  - name {p_varname:?} value {p_value:?}");
            assert_eq!(varname, &p_varname);
            assert_eq!(value, &p_value);
        }
    }

    #[test]
    fn parse() -> Result<(), Box<dyn Error>> {
        let dir = tempfile::tempdir()?;
        let path = dir.path().join("os-release");
        println!(
            "\nWriting and parsing {path}",
            path = path.to_string_lossy()
        );
        fs::write(&path, CFG_TEXT.as_bytes())?;
        let res = super::parse(&path)?;
        assert_eq!(res.len(), 9);
        for (name, value) in &CFG_EXPECTED {
            let pvalue = res.get(&name.to_string());
            println!("- {name:?}: expected {value:?}, got {pvalue:?}");
            match value {
                Some(value) => match pvalue {
                    Some(pvalue) => assert_eq!(value, pvalue),
                    None => panic!("{name}: expected {value:?} got {pvalue:?}"),
                },
                None => assert_eq!(pvalue, None),
            }
        }
        Ok(())
    }
}
