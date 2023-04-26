/*
 * SPDX-FileCopyrightText: 2021 - 2023  StorPool <support@storpool.com>
 * SPDX-License-Identifier: BSD-2-Clause
 */
use std::collections::HashSet;

use enum_iterator::{all, cardinality};

use super::{VariantError, VariantKind};

#[test]
fn test_detect() -> Result<(), VariantError> {
    let variant = crate::detect()?;
    println!("Detected {kind}", kind = variant.kind.as_ref());
    Ok(())
}

#[test]
fn test_roundtrip() {
    println!("");
    let all = crate::build_variants();
    assert_eq!(all.order.len(), all.variants.len());

    let mut seen: HashSet<String> = HashSet::new();

    for kind in &all.order {
        println!("Checking {kind}", kind = kind.as_ref());
        let var = &all.variants[&kind];

        let name = var.kind.as_ref().to_string();
        let alias = &var.builder.alias;
        println!("- name {name} alias {alias}");
        assert_eq!(var.kind, *kind);
        assert!(!seen.contains(&name));
        seen.insert(name);

        let avar = crate::get_by_alias_from(&all, alias).unwrap();
        assert_eq!(avar.kind, *kind);
    }

    let mut seen_vec: Vec<String> = seen.drain().collect();
    print!(
        "Expected: {count_seen}, seen: {count_all}:",
        count_seen = seen_vec.len(),
        count_all = all.order.len()
    );
    seen_vec.sort_unstable();
    for name in &seen_vec {
        print!(" {name}");
    }
    println!("");
    assert_eq!(seen_vec.len(), all.order.len());
}

#[test]
fn test_get_all() -> Result<(), VariantError> {
    let count = cardinality::<VariantKind>();

    let built = crate::build_variants();
    assert_eq!(
        built.order.iter().copied().collect::<HashSet<_>>(),
        all::<VariantKind>().collect::<HashSet<_>>()
    );

    let all_hash_from_built = crate::get_all_variants_from(&built);
    assert_eq!(all_hash_from_built.len(), count);
    for (key, value) in all_hash_from_built.iter() {
        assert_eq!(*key, value.kind);
    }

    let all_hash = crate::get_all_variants();
    assert_eq!(*all_hash, *all_hash_from_built);

    let in_order_from_built: Vec<_> = crate::get_all_variants_in_order_from(&built).collect();
    assert_eq!(
        in_order_from_built
            .iter()
            .map(|var| var.kind)
            .collect::<Vec<_>>(),
        built.order
    );

    let in_order: Vec<_> = crate::get_all_variants_in_order().collect();
    assert_eq!(in_order, in_order_from_built);
    Ok(())
}
