# Changelog

## 2025-11-13
- Documented and implemented fail-fast PTY remediation (see `docs/architecture/2025-11-13/`), including `pty_disabled` runtime flag, responsive probe, and 150 ms / 500 ms timeouts.
- Added UI redraw macro, immediate input clearing, and PTY disable propagation via `CodexJobMessage::disable_pty`.
- Throttled high-quality audio resampler logs (single warning per process) and relaxed rubato length tolerance for cross-platform stability.
- Established project traceability docs (`PROJECT_OVERVIEW.md`, `master_index.md`) and logged verification via `cargo fmt`, `cargo test --all`, and `cargo build --release`.
