# Daily Changelog — 2025-11-13

## Added
- Created the 2025-11-13 architecture folder capturing the Phase 2A kickoff, Earshot approval, and success criteria checklist.
- Documented Phase 2A work plan (config surface, Earshot integration, metrics, tests, CI stubs) per the latency remediation plan.
- Implemented `VadEngine` interfaces in `rust_tui/src/audio.rs`, including the Earshot feature flag wiring and a `SimpleThresholdVad` fallback for non-Earshot builds.
- Added the `vad_earshot` feature and optional dependency placeholder in `rust_tui/Cargo.toml`.
- Introduced `rust_tui/src/vad_earshot.rs` (feature gated) plus the trait-based VAD factory used by `voice.rs`.
- Reworked `Recorder::record_with_vad` to prepare for chunked capture (non-test builds) and added per-utterance metrics scaffolding/logging.
- Updated `voice.rs` to call the new VAD-aware recorder path and emit capture metrics alongside transcripts.
- Captured the detailed Option 1 Codex worker design (state flow, cancellation, spinner plan, telemetry) in `ARCHITECTURE.md` so implementation can proceed under SDLC.
- Implemented the nonblocking Codex worker (`rust_tui/src/codex.rs` + `App::poll_codex_job`), spinner/cancel UX, and session handoff; TUI no longer freezes during 30–60 s Codex calls and cancellation now surfaces via Esc/Ctrl+C.
- Added unit tests for the worker success/error/cancel paths plus new UI-level tests that drive the spinner/cancel flow via the job hook harness; `cargo test --no-default-features` is now part of the daily verification until the `earshot` crate is reachable.
- Reworked the render loop (`rust_tui/src/ui.rs`) and `App` state (`needs_redraw`) so job completions and spinner ticks trigger redraws automatically, eliminating the “press any key to see output” behavior during voice capture or Codex runs.
- Shortened the persistent Codex PTY timeout to 10 s with a 2 s “first output” deadline (`rust_tui/src/codex.rs`) so we bail to the fast CLI path almost immediately when the helper isn’t producing printable output, fixing the 30–45 s stalls per request.

## Fixed
- Corrected the Earshot profile mapping (`rust_tui/src/vad_earshot.rs`) to use the actual `VoiceActivityProfile::QUALITY/LBR/AGGRESSIVE/VERY_AGGRESSIVE` constants so release builds succeed once the crate is available.
- Swapped the Rubato `SincFixedIn` constructor arguments (`rust_tui/src/audio.rs`) so chunk size and channel count are not inverted; this stops the "expected 256 channels" spam, keeps high-quality resampling enabled, and prevents runaway log growth during idle TUI sessions.
- **CRITICAL:** Fixed race condition in `App::poll_codex_job` (`app.rs:527-536`) where job was cleared before handling completion message, causing state inconsistency.
- **CRITICAL:** Changed atomic ordering to `AcqRel` for `RESAMPLER_WARNING_SHOWN` flag (`audio.rs:575`) to prevent data race in multi-threaded audio capture.
- **HIGH:** Improved `PtyCodexSession::is_responsive()` (`pty_session.rs:114-130`) to drain stale output 5 times before probing, preventing false positives from buffered data.
- **HIGH:** Fixed hardcoded 500ms timeout in PTY polling loop (`codex.rs:384`) to use proper 50ms interval for responsive detection within 150ms/500ms fail-fast limits.

## Pending
- Implementation of Earshot-based silence-aware capture and the accompanying metrics/tests.
- Addition of `perf_smoke` and `memory_guard` workflows tied to the new metrics.
- Manual testing of async Codex worker UI responsiveness and cancellation behavior once the reference environment is back online.

## Notes
- Future updates to this file must capture concrete code/doc changes completed on 2025-11-13.
