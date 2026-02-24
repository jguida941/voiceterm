# Rust Workspace Layout Migration (MP-339)

Execution plan contract: required

## Scope

- Rename the top-level Rust workspace directory from `src/` to `rust/`.
- Update all repository path contracts that reference:
  - source tree paths (for example `rust/src/**`)
  - workspace metadata files (`rust/Cargo.toml`)
  - build/test run commands (`cd rust && cargo ...`)
  - build artifacts (`rust/target/**`)
  - CI workflow triggers and working-directory declarations
  - tooling scripts and guard checks
  - active/user/developer docs that are expected to track current behavior
- Preserve runtime behavior and release behavior; this is a path/layout migration only.
- Keep archive records under `dev/archive/` as historical references unless strict tooling checks require an update.

## Execution Checklist

- [x] Register this execution plan in `dev/active/INDEX.md`.
- [x] Link MP scope in `dev/active/MASTER_PLAN.md` (`MP-339`).
- [x] Move filesystem workspace directory: `src/` -> `rust/`.
- [x] Update tooling/runtime/CI/scripts for new workspace root path.
- [x] Update docs/governance references required by this migration.
- [x] Run required tooling/process bundle checks and sync gates.
- [x] Capture verification evidence and residual risk notes.

## Progress Log

- 2026-02-24: Plan created. Scope anchored to `MP-339`, with registry + master-plan linkage completed before implementation.
- 2026-02-24: Inventory completed for path contracts (`src/src`, `src/Cargo.toml`, `cd src`, `working-directory: src`, and `src/target`) and rewrite targets were batched across runtime/tooling/CI/docs.
- 2026-02-24: Executed filesystem rename (`mv src rust`) and updated references to `rust/src/**`, `rust/Cargo.toml`, `cd rust`, `working-directory: rust`, and `rust/target/**`.
- 2026-02-24: Follow-up sweep fixed residual workflow cache/trigger keys still pinned to `src/Cargo.lock`; all active non-archive contracts now reference `rust/Cargo.lock`.
- 2026-02-24: Added rename-aware baseline mapping to Rust debt guards (`check_rust_lint_debt.py`, `check_rust_best_practices.py`) via shared helper `git_change_paths.py` so path-only workspace moves do not create false debt growth failures.
- 2026-02-24: Validation rerun completed with sync + docs/tooling gates passing and Rust debt guards green in working-tree mode.
- 2026-02-24: Hardened Rust guardrails after migration audit findings: `check_rust_audit_patterns.py` now scans active source roots (`rust/src` first, legacy fallback roots) and fails fast if no Rust files are discovered so path drift cannot silently bypass the guard.
- 2026-02-24: Updated `check_rust_security_footguns.py` to use rename-aware base-path mapping (`git_change_paths.py`), eliminating false-positive growth caused by `src/` -> `rust/` rename-only moves.
- 2026-02-24: Extended `check_rust_best_practices.py` with a non-regressive `std::mem::forget`/`mem::forget` usage metric and added script tests/docs updates for the tightened policy.
- 2026-02-24: Reduced unsafe initialization surface in PTY/OSC runtime paths by replacing `mem::zeroed()` winsize setup with explicit `libc::winsize` struct initialization (`rust/src/pty_session/pty.rs`, `rust/src/pty_session/osc.rs`) and validated with targeted PTY/STT/winsize regression tests.

## Audit Evidence

- Path-scan result after rewrite (excluding archive history): no remaining legacy runtime/tooling path contracts (`src/src`, `src/Cargo.toml`, `cd src`, `working-directory: src`, `src/target`) outside explicit migration-log text.
- Passed:
  - `python3 dev/scripts/checks/check_active_plan_sync.py`
  - `python3 dev/scripts/checks/check_multi_agent_sync.py`
  - `python3 dev/scripts/checks/check_release_version_parity.py`
  - `python3 dev/scripts/checks/check_cli_flags_parity.py`
  - `python3 dev/scripts/checks/check_agents_contract.py`
  - `python3 dev/scripts/devctl.py docs-check --strict-tooling`
  - `python3 dev/scripts/devctl.py hygiene`
  - `python3 dev/scripts/devctl.py orchestrate-status --format md`
  - `python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md`
  - `python3 dev/scripts/checks/check_coderabbit_gate.py --branch master` (local non-blocking fallback; GitHub API unreachable)
  - `python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master` (local non-blocking fallback; GitHub API unreachable)
  - `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`
  - `cd rust && cargo check --bin voiceterm`
  - `python3 dev/scripts/checks/check_rust_lint_debt.py`
  - `python3 dev/scripts/checks/check_rust_best_practices.py`
  - `python3 dev/scripts/checks/check_rust_security_footguns.py`
  - `python3 dev/scripts/checks/check_rust_audit_patterns.py`
  - `python3 -m unittest dev.scripts.devctl.tests.test_check_rust_best_practices dev.scripts.devctl.tests.test_check_rust_audit_patterns dev.scripts.devctl.tests.test_check_rust_security_footguns`
  - `cd rust && cargo test pty_session::tests::pty_cli_session_drop_terminates_descendants_in_process_group -- --nocapture`
  - `cd rust && cargo test pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group -- --nocapture`
  - `cd rust && cargo test stt::tests::transcriber_restores_stderr_after_failed_model_load -- --nocapture`
  - `cd rust && cargo test pty_session::tests::current_terminal_size_reads_winsize`
  - `cd rust && cargo test pty_session::tests::current_terminal_size_falls_back_when_dimension_zero`
  - `cd rust && cargo test pty_session::tests::current_terminal_size_falls_back_when_ioctl_dimensions_zero`
  - `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`
