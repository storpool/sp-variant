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
use std::collections::HashSet;
use std::error::Error;

#[test]
fn test_detect() -> Result<(), Box<dyn Error>> {
    let variant = crate::detect()?;
    println!("Detected {}", variant.kind.as_ref());
    Ok(())
}

#[test]
fn test_roundtrip() -> Result<(), Box<dyn Error>> {
    println!("");
    let all = crate::build_variants();
    assert_eq!(all.order.len(), all.variants.len());

    let mut seen: HashSet<String> = HashSet::new();

    for kind in &all.order {
        println!("Checking {}", kind.as_ref());
        let var = &all.variants[&kind];

        let name = var.kind.as_ref().to_string();
        let alias = &var.builder.alias;
        println!("- name {} alias {}", name, alias);
        assert_eq!(var.kind, *kind);
        assert!(!seen.contains(&name));
        seen.insert(name);

        let avar = crate::get_by_alias_from(&all, alias).unwrap();
        assert_eq!(avar.kind, *kind);
    }

    let mut seen_vec: Vec<String> = seen.drain().collect();
    print!("Expected: {}, seen: {}:", seen_vec.len(), all.order.len());
    seen_vec.sort_unstable();
    for name in &seen_vec {
        print!(" {}", name);
    }
    println!("");
    assert_eq!(seen_vec.len(), all.order.len());

    Ok(())
}
