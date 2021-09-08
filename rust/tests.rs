use std::collections::HashSet;
use std::error;

#[test]
fn test_detect() -> Result<(), Box<dyn error::Error>> {
    let variant = crate::detect()?;
    println!("Detected {}", variant.kind.as_ref());
    Ok(())
}

#[test]
fn test_roundtrip() -> Result<(), Box<dyn error::Error>> {
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
