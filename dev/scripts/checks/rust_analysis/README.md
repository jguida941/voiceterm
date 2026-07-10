# Rust Analysis Guards

Implementation package for Rust-focused checks and shared helpers.

- Keep the stable public entrypoints at `dev/scripts/checks/check_*.py`.
- Keep shared Rust-analysis helpers here so the crowded `checks/` root stays
  reserved for thin wrappers and a smaller set of public entrypoints.
