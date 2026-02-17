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
- [ ] `CQ-001c` Reduce `SettingsActionContext` constructor complexity and split
  responsibilities into smaller context structs.
- [ ] `CQ-001d` Extract repeated status emission/update patterns into focused
  helper methods with explicit intent names.

## Workstream 2 - Status-Line Consolidation

Targets:

- `src/src/bin/voiceterm/status_line/buttons.rs`
- `src/src/bin/voiceterm/status_line/format.rs`

- [ ] `CQ-002a` Centralize button color/highlight policy (single source of
  truth for full + compact row rendering).
- [ ] `CQ-002b` Isolate legacy renderer paths behind explicit compatibility
  helpers and minimize dead-code allowances.
- [ ] `CQ-002c` Split large test blocks into dedicated test modules and add
  focused fixtures/builders for clarity.

## Workstream 3 - PTY Lifecycle Canonicalization

Targets:

- `src/src/pty_session/pty.rs`
- `src/src/pty_session/session_guard.rs`

- [ ] `CQ-003a` Consolidate duplicated spawn/wire-up and drop/shutdown logic
  across `PtyCliSession` and `PtyOverlaySession`.
- [ ] `CQ-003b` Harden session-lease identity checks (owner/child process
  validation) and reduce PID-reuse ambiguity risk.
- [ ] `CQ-003c` Add throttling/policy around stale-session cleanup cadence to
  avoid unnecessary startup overhead.

## Workstream 4 - Backend/IPC Orchestration Decomposition

Targets:

- `src/src/codex/pty_backend.rs`
- `src/src/ipc/session.rs`

- [ ] `CQ-004a` Split orchestration from transport/sanitization helpers in
  `codex/pty_backend.rs`.
- [ ] `CQ-004b` Avoid repeated full-buffer sanitization in the PTY polling loop
  by introducing incremental checks.
- [ ] `CQ-004c` Further split `ipc/session.rs` into narrower modules
  (`stdin_reader`, `claude_job`, `auth_flow`, loop control wiring).

## Workstream 5 - Lint Policy Hardening

- [ ] `CQ-005a` Define a strict maintainer lint profile with a scoped allowlist
  (pedantic/nursery subset focused on maintainability and safety).
- [ ] `CQ-005b` Burn down high-value warnings first:
  - missing `#[must_use]` where meaningful
  - missing `# Errors` docs on public fallible APIs
  - redundant clones/closures
  - risky integer/float cast hot spots
  - dead-code/legacy drift in runtime modules

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
