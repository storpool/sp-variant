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
//! Yet another INI-like file parser.
//!
//! This one is specifically written for the somewhat simplified format of
//! the os-release file as found in recent Linux distributions.

use std::collections::HashMap;
use std::error::Error;
use std::fs;
use std::path::Path;

use expect_exit::{ExpectedResult, ExpectedWithError};
use regex::Regex;

quick_error! {
    /// An error that occurred during parsing.
    #[derive(Debug)]
    #[non_exhaustive]
    pub enum YAIError {
        /// A backslash at the end of the line.
        BackslashAtEnd(line: String) {
            display("Backslash at the end of the {:?} os-release line", line)
        }
        /// An invalid line in the /etc/os-release file.
        BadLine(line: String) {
            display("Unexpected os-release line {:?}", line)
        }
        /// A quoted value contains the quote character.
        QuoteInQuoted(line: String) {
            display("The value in the {:?} os-release line contains the quote character", line)
        }
        /// Mismatched open/close quotes.
        MismatchedQuotes(line: String) {
            display("Mismatched open/close quotes in the {:?} os-release line", line)
        }
        /// An internal error occurred
        InternalError(message: String) {
            display("YAI parser internal error: {}", message)
        }
    }
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

fn parse_line(line: &str) -> Result<Option<(String, String)>, Box<dyn Error>> {
    lazy_static! {
        static ref RE: Regex = Regex::new(RE_LINE)
            .expect_result(|| format!("could not parse '{}'", RE_LINE))
            .or_exit_e_("YAI internal error");
    }
    match RE.captures(line) {
        Some(caps) => {
            if caps.name("comment").is_some() {
                return Ok(None);
            }
            let q_open = caps.name("q_open").map(|value| value.as_str());
            let q_close = caps.name("q_close").map(|value| value.as_str());
            let varname = &caps["varname"];
            let quoted_top = &caps["quoted"];

            if q_open == Some("'") {
                if quoted_top.contains('\'') {
                    return Err(Box::new(YAIError::QuoteInQuoted(line.to_owned())));
                }
                if q_close != q_open {
                    return Err(Box::new(YAIError::MismatchedQuotes(line.to_owned())));
                }
                return Ok(Some((varname.to_owned(), quoted_top.to_owned())));
            }

            let quoted = match q_open {
                Some("\"") => {
                    if q_close != q_open {
                        return Err(Box::new(YAIError::MismatchedQuotes(line.to_owned())));
                    }
                    quoted_top
                }
                Some(other) => {
                    return Err(Box::new(YAIError::InternalError(format!(
                        "YAI parse_line: {:?}: q_open {:?}",
                        line, other
                    ))))
                }
                None => &caps["full"],
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
                (true, _) => Err(Box::new(YAIError::BackslashAtEnd(line.to_owned()))),
            }
        }
        None => Err(Box::new(YAIError::BadLine(line.to_owned()))),
    }
}

/// Parse a file, return a name: value mapping.
///
/// # Errors
/// - I/O or text decoding errors from reading the file
/// - [`YAIError`] parse errors from examining the INI-file structure
#[allow(clippy::missing_inline_in_public_items)]
pub fn parse<P: AsRef<Path>>(path: P) -> Result<HashMap<String, String>, Box<dyn Error>> {
    fs::read_to_string(path)?
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

    use super::YAIError;

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
            println!("- {:?}", line);
            match super::parse_line(line) {
                Ok(data) => panic!("The {:?} malformed line was misparsed as {:?}", line, data),
                Err(err) => {
                    if !err.downcast_ref::<YAIError>().is_some() {
                        panic!("The {:?} malformed line raised an error: {}", line, err)
                    }
                }
            }
        }
    }

    #[test]
    fn parse_comments() {
        println!("\nMaking sure comments and empty lines are ignored");
        for line in &LINES_COMMENTS {
            println!("- {:?}", line);
            let res = super::parse_line(line).unwrap();
            println!("  - {:?}", res);
            assert_eq!(res, None);
        }
    }

    #[test]
    fn parse_good() {
        println!("\nMaking sure well-formed lines are parsed correctly");
        for (line, (varname, value)) in &LINES_OK {
            println!("- {:?}", line);
            let (p_varname, p_value) = super::parse_line(line).unwrap().unwrap();
            println!("  - name {:?} value {:?}", p_varname, p_value);
            assert_eq!(varname, &p_varname);
            assert_eq!(value, &p_value);
        }
    }

    #[test]
    fn parse() -> Result<(), Box<dyn Error>> {
        let dir = tempfile::tempdir()?;
        let path = dir.path().join("os-release");
        println!("\nWriting and parsing {}", path.to_string_lossy());
        fs::write(&path, CFG_TEXT.as_bytes())?;
        let res = super::parse(&path)?;
        assert_eq!(res.len(), 9);
        for (name, value) in &CFG_EXPECTED {
            let pvalue = res.get(&name.to_string());
            println!("- {:?}: expected {:?}, got {:?}", name, value, pvalue);
            match value {
                Some(value) => match pvalue {
                    Some(pvalue) => assert_eq!(value, pvalue),
                    None => panic!("{}: expected {:?} got {:?}", name, value, pvalue),
                },
                None => assert_eq!(pvalue, None),
            }
        }
        Ok(())
    }
}
