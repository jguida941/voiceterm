# Release Review: 1.0.28 (2026-01-31)

## Summary
- Theme picker overlay with numbered selection.
- Live waveform + dB meter and transcript preview in the status line.
- Optional notification sounds and refreshed shortcut tables.

## Reviewed areas
- Overlay runtime (`rust_tui/src/bin/codex_overlay/main.rs`, `rust_tui/src/bin/codex_overlay/status_line.rs`).
- Overlay panels and IO (`rust_tui/src/bin/codex_overlay/writer.rs`, `rust_tui/src/bin/codex_overlay/theme_picker.rs`).
- Config + docs (`rust_tui/src/config/mod.rs`, `docs/CLI_FLAGS.md`, `docs/USAGE.md`).
- Release metadata (`rust_tui/Cargo.toml`, `Codex Voice.app/Contents/Info.plist`).

## Verification
- `cd rust_tui && cargo build --release --bin codex-voice`
- `cd rust_tui && cargo clippy --workspace --all-features -- -D warnings`
- `cd rust_tui && cargo test`

## Notes / risks
- Terminal bell output depends on user terminal settings (may be muted).
- Theme selection is session-only (no persistence).
