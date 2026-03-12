"""Rust/ownership/error-focused probe remediation practices."""

from __future__ import annotations

from typing import Any

RUST_PRACTICES: dict[str, dict[str, Any]] = {
    "stringly_typed_rust": {
        "title": "Replace string match arms with a proper enum",
        "explanation": (
            "Matching on string literals in Rust bypasses the compiler's "
            "exhaustiveness checking — the most powerful safety feature of Rust "
            "enums. A match on &str always needs a catch-all arm, meaning new "
            "variants can be silently missed. An enum gives you compile-time "
            "guarantees that every variant is handled."
        ),
        "fix_pattern": (
            "1. Define an enum with one variant per valid string.\n"
            "2. Implement FromStr (or use serde) for parsing at boundaries.\n"
            "3. Match on enum variants — compiler enforces exhaustiveness."
        ),
        "example_before": (
            "match action.as_str() {\n"
            '    "create" => do_create(),\n'
            '    "update" => do_update(),\n'
            '    "delete" => do_delete(),\n'
            "    _ => { /* new variants silently ignored */ }\n"
            "}"
        ),
        "example_after": (
            "enum Action { Create, Update, Delete }\n"
            "\n"
            "impl FromStr for Action { /* parse once at boundary */ }\n"
            "\n"
            "match action {\n"
            "    Action::Create => do_create(),\n"
            "    Action::Update => do_update(),\n"
            "    Action::Delete => do_delete(),\n"
            "    // Compiler error if new variant is added without handling!\n"
            "}"
        ),
        "references": [
            "Rust Book: Defining an Enum",
            "Rust Book: The match Control Flow Construct",
        ],
    },
    "boolean_params_rust": {
        "title": "Bundle boolean parameters into an options struct",
        "explanation": (
            "Functions with 3+ boolean parameters produce unreadable call sites "
            "like foo(true, false, true, false). Rust's named-field struct pattern "
            "makes every call site self-documenting, and the compiler catches "
            "field name typos."
        ),
        "fix_pattern": (
            "1. Create a struct with named boolean fields and Default.\n"
            "2. Replace positional bools with the struct parameter.\n"
            "3. Use struct update syntax for convenience: Options { force: true, ..Default::default() }."
        ),
        "example_before": (
            "fn deploy(verbose: bool, dry_run: bool, force: bool, skip_tests: bool) {\n"
            "    ...\n"
            "}\n"
            "\n"
            "deploy(true, false, true, false);  // What does each bool mean?"
        ),
        "example_after": (
            "#[derive(Default)]\n"
            "struct DeployOptions {\n"
            "    verbose: bool,\n"
            "    dry_run: bool,\n"
            "    force: bool,\n"
            "    skip_tests: bool,\n"
            "}\n"
            "\n"
            "fn deploy(opts: DeployOptions) { ... }\n"
            "\n"
            "deploy(DeployOptions { verbose: true, force: true, ..Default::default() });"
        ),
        "references": [
            "Rust API Guidelines: C-BUILDER pattern",
        ],
    },
    "unwrap_chains": {
        "title": "Replace .unwrap()/.expect() with the ? operator",
        "explanation": (
            "Each .unwrap() or .expect() is a potential panic — an unrecoverable "
            "crash in production. When a function has multiple unwrap calls, it "
            "means there are multiple crash points that will bring down the entire "
            "process. The ? operator propagates errors to the caller, where they "
            "can be handled gracefully (retry, log, show user-friendly message)."
        ),
        "fix_pattern": (
            "1. Change the function return type to Result<T, Error>.\n"
            "2. Replace .unwrap() with ? to propagate errors.\n"
            "3. For Option types, use .ok_or() or .ok_or_else() before ?.\n"
            "4. Use .unwrap_or_default() only when a silent default is correct."
        ),
        "example_before": (
            "fn load_config(path: &str) -> Config {\n"
            "    let text = fs::read_to_string(path).unwrap();\n"
            "    let parsed: Value = serde_json::from_str(&text).unwrap();\n"
            '    let name = parsed["name"].as_str().unwrap().to_string();\n'
            "    Config { name }\n"
            "}"
        ),
        "example_after": (
            "fn load_config(path: &str) -> anyhow::Result<Config> {\n"
            "    let text = fs::read_to_string(path)?;\n"
            "    let parsed: Value = serde_json::from_str(&text)?;\n"
            '    let name = parsed["name"]\n'
            "        .as_str()\n"
            "        .ok_or_else(|| anyhow!(\"missing 'name' field\"))?\n"
            "        .to_string();\n"
            "    Ok(Config { name })\n"
            "}"
        ),
        "references": [
            "Rust Book: Recoverable Errors with Result",
            "Rust Book: The ? Operator",
            "anyhow crate: Flexible error handling",
        ],
    },
    "type_conversions": {
        "title": "Eliminate redundant type conversion chains",
        "explanation": (
            "Patterns like .as_str().to_string() convert String -> &str -> String, "
            "allocating a new String that's identical to the original. This is a "
            "round-trip that wastes CPU and memory. It usually means the author "
            "doesn't understand when they have an owned vs borrowed value."
        ),
        "fix_pattern": (
            "1. If you need an owned String, use .clone() directly.\n"
            "2. If the callee only reads, pass &str (a reference) instead.\n"
            "3. If you're converting between types, do it once at the boundary."
        ),
        "example_before": (
            "let name = config.name.as_str().to_string();  // String→&str→String\n"
            "let path = entry.path().to_string().as_str();  // creates temp String"
        ),
        "example_after": (
            "let name = config.name.clone();  // already a String, just clone\n"
            "let path_str = entry.path();      // use the &str directly"
        ),
        "references": [
            "Rust Book: Understanding Ownership",
            "Rust Book: References and Borrowing",
        ],
    },
    "clone_density": {
        "title": "Reduce .clone() usage with references or ownership transfer",
        "explanation": (
            "Excessive .clone() calls indicate the code is fighting the borrow "
            "checker by copying data instead of restructuring ownership. Each "
            "clone allocates memory and copies data, which impacts performance. "
            "More importantly, it hides the true data flow — when everything is "
            "cloned, it's unclear who owns what and when data becomes stale."
        ),
        "fix_pattern": (
            "1. Pass references (&T) instead of owned values when the callee "
            "only needs to read.\n"
            "2. Use Cow<T> (Clone-on-Write) for read-mostly, write-rarely patterns.\n"
            "3. Transfer ownership (move) through the call chain instead of "
            "cloning at each step.\n"
            "4. For closures that capture state, clone only the specific fields "
            "needed, not entire structs."
        ),
        "example_before": (
            "fn process(config: &Config, data: &Data) {\n"
            "    let name = config.name.clone();\n"
            "    let items = data.items.clone();\n"
            "    let settings = config.settings.clone();\n"
            "    let metadata = data.metadata.clone();\n"
            "    do_work(name, items, settings, metadata);\n"
            "}"
        ),
        "example_after": (
            "fn process(config: &Config, data: &Data) {\n"
            "    // Pass references — do_work only reads these\n"
            "    do_work(&config.name, &data.items, &config.settings, &data.metadata);\n"
            "}\n"
            "\n"
            "// Or for closures that need ownership:\n"
            "let name = config.name.clone(); // clone only what the closure needs\n"
            "tokio::spawn(async move { use_name(&name).await });"
        ),
        "references": [
            "Rust Book: References and Borrowing",
            "Rust Book: Understanding Ownership",
            "std::borrow::Cow documentation",
        ],
    },
    "vague_errors": {
        "title": "Include runtime context in error messages",
        "explanation": (
            'Error messages like bail!("failed to open config") are useless in '
            "production — you know something failed but have no idea which config "
            "file, what the path was, or what the OS error was. Every bail!/anyhow! "
            "should include the variables that caused the failure so the error log "
            "alone is enough to diagnose the issue."
        ),
        "fix_pattern": (
            "1. Add {variable:?} format args to include runtime values.\n"
            "2. For chained errors, use .with_context(|| format!(...)).\n"
            "3. Include: the input that triggered the error, the expected state, "
            "and any relevant identifiers (paths, IDs, keys)."
        ),
        "example_before": (
            "let config = fs::read_to_string(path)\n"
            '    .context("failed to read config")?;\n'
            "let parsed = toml::from_str(&config)\n"
            '    .context("failed to parse config")?;'
        ),
        "example_after": (
            "let config = fs::read_to_string(path)\n"
            '    .with_context(|| format!("failed to read config at {path:?}"))?;\n'
            "let parsed: Config = toml::from_str(&config)\n"
            '    .with_context(|| format!("failed to parse TOML in {path:?}"))?;'
        ),
        "references": [
            "anyhow crate: Error context",
            "Rust Error Handling Best Practices",
        ],
    },
}
