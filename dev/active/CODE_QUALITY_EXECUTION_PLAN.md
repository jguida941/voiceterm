# Code Quality Execution Plan (Rust Best-Practice Audit)

Date: 2026-02-17  
Status: Active execution  
Parent tracker: `dev/active/MASTER_PLAN.md` (`MP-184`..`MP-189`)

`dev/active/MASTER_PLAN.md` remains the canonical plan. This document is the
execution detail for the code-quality audit workstream.

## Objective

Raise code quality across the full VoiceTerm Rust codebase by:

- reducing coupling in high-change runtime modules
- consolidating duplicated logic paths
- improving naming and ownership clarity
- tightening reliability boundaries around PTY/process lifecycle code
- enforcing a practical, maintainable Rust style/lint baseline

## Baseline (Captured Before Execution)

- `python3 dev/scripts/devctl.py check --profile ci` passes.
- Full strict lint sweep surfaces concentrated maintainability debt in:
  - `src/src/bin/voiceterm/settings_handlers.rs`
  - `src/src/bin/voiceterm/status_line/buttons.rs`
  - `src/src/bin/voiceterm/status_line/format.rs`
  - `src/src/pty_session/pty.rs`
  - `src/src/codex/pty_backend.rs`
  - `src/src/ipc/session.rs`

## Workstream 1 - Settings Handler Decomposition

Target: `src/src/bin/voiceterm/settings_handlers.rs`

- [x] `CQ-001a` Move tests out of runtime file into
  `src/src/bin/voiceterm/settings_handlers/tests.rs`.
- [x] `CQ-001b` Consolidate repeated enum-cycling logic via a shared helper.
- [x] `CQ-001c1` Remove the oversized `SettingsActionContext::new` constructor
  and switch call sites to explicit field initialization for clearer ownership
  wiring.
- [x] `CQ-001c2` Split `SettingsActionContext` into smaller sub-context bundles
  (status/timers/layout) to reduce mutable alias surface further.
- [x] `CQ-001d` Extract repeated status emission/update patterns into focused
  helper methods (`set_transient_status`, `reset_voice_visuals`) with explicit
  intent names.
- [x] `CQ-001e` Remove `ButtonActionContext::new` (high-arg constructor) and
  switch event-loop wiring to explicit struct literals to keep context
  construction consistent and clippy-clean.

## Workstream 2 - Status-Line Consolidation

Targets:

- `src/src/bin/voiceterm/status_line/buttons.rs`
- `src/src/bin/voiceterm/status_line/format.rs`

- [x] `CQ-002a` Centralize button color/highlight policy (single source of
  truth for full + compact row rendering) and shared queue/ready/latency badge
  helpers in `status_line/buttons.rs`.
- [x] `CQ-002b` Isolate legacy renderer paths behind explicit compatibility
  helpers and minimize dead-code allowances (`status_line/buttons.rs` legacy
  row helpers now test-gated via `#[cfg(test)]`, with shared framing/separator
  helpers).
- [x] `CQ-002c1` Split `status_line/buttons.rs` tests into
  `status_line/buttons/tests.rs` to keep runtime and test code separate.
- [x] `CQ-002c2` Apply the same split/fixture cleanup to
  `status_line/format.rs` tests.

## Workstream 3 - PTY Lifecycle Canonicalization

Targets:

- `src/src/pty_session/pty.rs`
- `src/src/pty_session/session_guard.rs`

- [x] `CQ-003a` Consolidate duplicated spawn/wire-up and drop/shutdown logic
  across `PtyCliSession` and `PtyOverlaySession` (landed shared
  `start_pty_session`, `shutdown_pty_child`, `close_pty_session_handles`,
  newline-send helper, and shared `is_alive` PID guard path).
- [x] `CQ-003b` Harden session-lease identity checks (owner/child process
  validation) and reduce PID-reuse ambiguity risk (landed optional
  owner/child start-time lease identity fields with validation checks before
  stale-process termination).
- [x] `CQ-003c` Add throttling/policy around stale-session cleanup cadence to
  avoid unnecessary startup overhead (landed atomic minimum-interval cleanup
  gate with deterministic policy helper coverage).

## Workstream 4 - Backend/IPC Orchestration Decomposition

Targets:

- `src/src/codex/pty_backend.rs`
- `src/src/ipc/session.rs`

- [ ] `CQ-004a` Split orchestration from transport/sanitization helpers in
  `codex/pty_backend.rs` (in progress: landed shared persistent-PTY argument
  builder plus codex-job start/recoverable/final event helpers, persistent
  attempt helper, output-resolution helper, and output-finalization helper
  extraction; landed `codex/pty_backend/output_sanitize.rs` extraction for PTY
  sanitize/control-byte parsing helpers and `codex/pty_backend/session_call.rs`
  extraction for persistent-session polling/timeouts/cache logic; landed
  `codex/pty_backend/job_flow.rs` extraction for codex-job orchestration/event
  emission flow so `pty_backend.rs` now primarily owns backend lifecycle/session
  wiring plus compatibility re-exports; landed
  `codex/pty_backend/test_support.rs` extraction for test-only job-hook/thread
  accounting/reset-session state so runtime lifecycle code is no longer
  interleaved with test scaffolding; remaining orchestration split is now
  incremental cleanup).
- [x] `CQ-004b` Avoid repeated full-buffer sanitization in the PTY polling loop
  by introducing incremental checks (landed `SanitizedOutputCache` dirty-refresh
  flow in `call_codex_via_session` so full-buffer sanitization only reruns after
  new raw bytes arrive, plus focused cache-refresh regression coverage in
  `src/src/codex/tests.rs`).
- [ ] `CQ-004c` Further split `ipc/session.rs` into narrower modules
  (`stdin_reader`, `claude_job`, `auth_flow`, loop control wiring`) (in
  progress: landed `session/stdin_reader.rs` and `session/claude_job.rs` module
  extraction with `session.rs` delegating through thin wrappers, plus
  `session/auth_flow.rs` extraction for provider login orchestration/hook state;
  Claude launch flow remains split into focused arg/PTY/piped/reader helpers,
  and duplicated stdout/stderr reader-thread logic consolidates through a shared
  Claude line-reader helper; landed `session/loop_control.rs` extraction for IPC
  loop iteration/exit policy with `session.rs` wrapper compatibility; landed
  `session/test_support.rs` extraction for event-sink and loop-count test
  infrastructure, with `loop_control` updating counts through focused helpers
  instead of direct static wiring; landed `session/state.rs` extraction for
  `IpcState` construction/capabilities emission and `session/event_sink.rs`
  extraction for event emit/test capture plumbing so `session.rs` stays focused
  on runtime adapters and loop orchestration; remaining boundary hardening is
  now incremental cleanup).

## Workstream 5 - Lint Policy Hardening

- [x] `CQ-005a` Define a strict maintainer lint profile with a scoped allowlist
  (landed `devctl check --profile maintainer-lint` + CI workflow
  `.github/workflows/lint_hardening.yml`, using a focused clippy subset:
  `redundant_clone`, `redundant_closure_for_method_calls`,
  `cast_possible_wrap`, and `dead_code`).
- [ ] `CQ-005b` Burn down high-value warnings first:
  - missing `#[must_use]` where meaningful
  - missing `# Errors` docs on public fallible APIs
  - redundant clones/closures
  - risky integer/float cast hot spots
  - dead-code/legacy drift in runtime modules
  - progress: current `redundant_clone`, `redundant_closure_for_method_calls`,
    and `cast_possible_wrap` findings for the maintainer-lint profile are
    resolved across `src/` and `src/bin/voiceterm/`; `#[must_use]` and
    `# Errors` docs burn-down sweep is now clean under
    `cargo clippy --workspace --all-features -- -W clippy::must_use_candidate -W clippy::missing_errors_doc`;
    remaining burn-down is scoped to evaluating/adding precision and
    truncation cast lint families to maintainer policy.

## Verification Gates Per Slice

For each landed slice:

1. `python3 dev/scripts/devctl.py check --profile ci`
2. Targeted tests for touched risk areas (PTY/process/session/overlay as needed)
3. `python3 dev/scripts/devctl.py docs-check --user-facing` when behavior/UI docs
   are impacted
4. Self-review against security, memory, error handling, concurrency, and
   performance checklists in `AGENTS.md`

## Primary Rust References

- Rust API Guidelines: <https://rust-lang.github.io/api-guidelines/>
- Rust Book (Modules): <https://doc.rust-lang.org/book/ch07-00-managing-growing-projects-with-packages-crates-and-modules.html>
- Rust Book (Test Organization): <https://doc.rust-lang.org/book/ch11-03-test-organization.html>
- Clippy docs: <https://doc.rust-lang.org/clippy/>
- Rust std safety comment guidance: <https://std-dev-guide.rust-lang.org/policy/safety-comments.html>
