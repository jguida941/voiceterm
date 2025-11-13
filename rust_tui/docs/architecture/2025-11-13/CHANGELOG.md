# 2025-11-13 Daily Change Log

## Changes Implemented
- Added `pty_disabled` runtime guard, PTY health probe, and fail-fast timeout constants (150 ms first byte / 500 ms total) with telemetry for `pty_attempted`, `pty_ms`, `cli_ms`, and `disable_pty`.
- Extended `CodexJobMessage` with `disable_pty`, plumbed status updates/UI redraw macro, and cleared inputs immediately on send/fail/cancel.
- Introduced `PtyCodexSession::is_responsive`, disabled persistent sessions on the first failure, and surfaced status/log messages.
- Added `state_change!` macro for scroll/input helpers and ensured `poll_codex_job` clears handles before dispatching messages.
- Throttled high-quality audio resampler warnings via `AtomicBool` and relaxed rubato length expectations to tolerate observed ±8 sample drift.
- Created/updated traceability docs (`PROJECT_OVERVIEW.md`, `master_index.md`, root `CHANGELOG.md`) and architecture notes for 2025-11-13.

## Testing & Verification
- `cargo fmt`
- `cargo test --all`
- `cargo build --release`
- Manual PTY latency check still pending (blocked in this CLI environment; to be run on-device).
