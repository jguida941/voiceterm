# Unsafe Governance Checklist

This document defines how VoiceTerm uses and reviews `unsafe` Rust.

It is mandatory for any change touching `unsafe` code paths, especially PTY lifecycle and
speech-to-text integration where FFI and raw file descriptors are involved.

## Goals

- Keep `unsafe` blocks small and focused.
- Document exact invariants at each boundary.
- Require direct regression tests for each critical invariant.
- Make review expectations explicit so behavior stays stable over time.

## Required Checklist For Any Unsafe Change

1. Narrow scope:
   - Keep `unsafe` in the smallest possible function/block.
   - Prefer safe wrappers (`Result`, enums, helper functions) around raw calls.
2. Document invariants:
   - Add or update a nearby `SAFETY:` comment that states preconditions and ownership rules.
   - Explain pointer/FD/process lifetime assumptions.
3. Verify error handling:
   - Return contextual errors for syscall failures.
   - For teardown paths, explicitly document and test best-effort behavior.
4. Update tests:
   - Add or update targeted tests listed in the hotspot inventory below.
   - Do not merge unsafe changes without matching test updates (or explicit deferral note in the audit).
5. Update traceability:
   - Update `RUST_GUI_AUDIT_2026-02-15.md` (`FX-010`) and `dev/active/MASTER_PLAN.md` in the same change.

## Unsafe Hotspot Inventory And Test Expectations

### PTY lifecycle and process control (`src/src/pty_session/`)

- `pty.rs` -> `spawn_pty_child`, `child_exec`
  - Invariants:
    - `argv`, cwd, and TERM pointers remain valid through `execvp`.
    - Child path uses async-signal-safe failure handling and `_exit(1)`.
    - Parent always closes child-only FDs after fork.
  - Expected tests:
    - `pty_session::tests::wait_for_exit_reaps_forked_child`
    - `pty_session::tests::pty_cli_session_drop_terminates_descendants_in_process_group`
    - `pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group`
    - `pty_session::tests::pty_cli_session_drop_sigkill_for_ignored_sigterm`
    - `pty_session::tests::pty_overlay_session_drop_sigkill_for_ignored_sigterm`

- `pty.rs` -> `set_nonblocking`, `close_fd`, drop teardown signaling/reaping
  - Invariants:
    - FD mutation only occurs on valid descriptors.
    - Invalid or already-closed FDs are handled without undefined behavior.
    - Reaping/signal fallbacks avoid child leaks.
  - Expected tests:
    - `pty_session::tests::pty_overlay_session_set_winsize_errors_on_invalid_fd`
    - `pty_session::tests::write_all_errors_on_invalid_fd`
    - `pty_session::tests::waitpid_failed_flags_negative`
    - `pty_session::tests::pty_cli_session_drop_terminates_child`
    - `pty_session::tests::pty_overlay_session_drop_terminates_child`

- `pty.rs`/`osc.rs` -> terminal size `ioctl` interaction
  - Invariants:
    - `winsize` structs are initialized before syscall use.
    - zero/invalid dimensions fall back to safe defaults.
  - Expected tests:
    - `pty_session::tests::pty_overlay_session_set_winsize_updates_and_minimums`
    - `pty_session::tests::current_terminal_size_reads_winsize`
    - `pty_session::tests::current_terminal_size_falls_back_when_dimension_zero`
    - `pty_session::tests::current_terminal_size_falls_back_when_ioctl_dimensions_zero`

### Whisper/stderr FFI handling (`src/src/stt.rs`)

- `Transcriber::new` stderr redirect/restore (`dup`, `dup2`, `close`)
  - Invariants:
    - Original stderr FD is restored before returning (success and failure paths).
    - Saved FD is closed exactly once.
    - Redirect failures return explicit errors without leaking descriptors.
  - Expected tests:
    - `stt::tests::transcriber_rejects_missing_model`
    - `stt::tests::transcriber_restores_stderr_after_failed_model_load`

- Whisper logger callback registration (`set_log_callback`)
  - Invariants:
    - Callback installation is one-time and pointer-safe.
    - Callback never dereferences incoming raw pointers.
  - Expected tests:
    - `stt::tests::transcriber_rejects_missing_model` (installs callback path)
    - `stt::tests::transcriber_restores_stderr_after_failed_model_load` (repeat installation path in test process)

## Verification Commands For Unsafe-Focused Changes

Use these minimum checks before merge:

```bash
python3 dev/scripts/devctl.py check --profile ci
cd src && cargo test pty_session::tests::pty_cli_session_drop_terminates_descendants_in_process_group -- --nocapture
cd src && cargo test pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group -- --nocapture
cd src && cargo test pty_session::tests::pty_overlay_session_set_winsize_updates_and_minimums
cd src && cargo test stt::tests::transcriber_restores_stderr_after_failed_model_load -- --nocapture
```
