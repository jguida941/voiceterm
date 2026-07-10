# Naming Consistency

Helper logic for `check_naming_consistency.py`.

- Keep the public guard entrypoint at
  `dev/scripts/checks/check_naming_consistency.py`.
- Keep matrix parsing, provider-token extraction, Rust enum parsing, and shared
  helper logic under `dev/scripts/checks/naming_consistency/` so the crowded
  checks root stays reserved for stable runnable entrypoints.
