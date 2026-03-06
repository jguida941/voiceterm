# Pre-Release Architecture Audit & Cleanup Plan

**Status**: pre-release completion point reached (Phases 1-7 complete; Phases 8-14 deferred post-release)  |  **Last updated**: 2026-03-05 | **Owner:** Runtime/tooling architecture
Execution plan contract: required

## Scope

Full-surface architecture audit and cleanup before next release cycle. Goal: make the codebase cleaner, more maintainable, more scalable, and following all best practices for both AI agents and human developers.

Keep this file active as the detailed execution spec for remaining phases;
`dev/active/MASTER_PLAN.md` remains the authoritative tracker state.

Operator execution note (2026-03-05): pre-release execution checkpoint reached (Phases 1-7 complete). Phases labeled "deferred post-release" remain default policy but may be promoted by explicit operator direction.

## Context

This repo (codex-voice / VoiceTerm) has grown to ~87K lines of Rust, ~55K lines of Python tooling, 28 CI workflows, and a 998-line AGENTS.md controller. The codebase is fundamentally well-structured — the Rust code scores 9/10 on module organization, comments are KISS-compliant, and there's only 1 TODO in the entire Rust codebase. But there are architectural, infrastructure, and maintainability issues that need attention to keep things clean, scalable, and ready for the next phase of feature development.

Three rounds of exhaustive 6-agent parallel audits have been completed covering: code quality, CI/CD pipeline, Python tooling, dependency health, cross-platform parity, performance baselines, developer experience, supply chain security, and production monorepo best practices. Total: 35 findings across 14 execution phases.

---

## Audit Findings Summary

### What's Working Well (keep it)
- Rust module boundaries are clean — event_loop properly decomposed into dispatchers
- Comment quality is strong — explains "why" not "what", KISS-compliant
- Only 1 TODO/FIXME in entire Rust codebase (excellent debt hygiene)
- All GitHub Actions pinned to SHA (95/100 security score)
- AGENTS.md has comprehensive task router, risk matrix, and release SOP
- Bundle registry is canonical authority with render automation

### What Needs Work

#### 1. CRITICAL: Bundle Command Duplication (DRY violation)
**Finding:** `bundle.runtime`, `bundle.docs`, `bundle.tooling`, and `bundle.release` share 15 identical commands. The only differences are:
- `bundle.runtime`: adds `check --profile ci` + `docs-check --user-facing`
- `bundle.docs`: adds `docs-check --user-facing` (identical to runtime minus `check --profile ci`)
- `bundle.tooling`: adds `docs-check --strict-tooling` + `hygiene --strict-warnings` + orchestrate + `check_agents_contract` + `check_release_version_parity` + `check_bundle_workflow_parity`
- `bundle.release`: superset of tooling + CodeRabbit gates + `check --profile release`

**Impact:** When a new check is added, it must be copy-pasted into 4-6 bundle definitions. This has already happened — the bundles are nearly identical.

**Fix:** Refactor `bundle_registry.py` to use a composition model:
```python
BUNDLE_COMMON = (...)  # 15 shared checks
BUNDLE_RUNTIME_EXTRAS = (...)
BUNDLE_TOOLING_EXTRAS = (...)
# Each bundle = EXTRAS + COMMON
```

**Files:** `dev/scripts/devctl/bundle_registry.py`, then re-render AGENTS.md bundles with `check_agents_bundle_render.py --write`

#### 2. CRITICAL: 93 CI Shell Blocks Without `set -e`
**Finding:** Most multi-line workflow shell blocks don't use `set -euo pipefail`. Failed commands can silently pass.

**Fix:** Add `set -euo pipefail` to all multi-line `run:` blocks in workflows, except where error suppression is intentional (those should have explicit `set +e` with a comment explaining why).

**Files:** All 28 `.github/workflows/*.yml` files

#### 3. HIGH: Python Tooling — 9 Duplicate `_run_git()` Implementations
**Finding:** `check_code_shape.py`, `check_duplicate_types.py`, `check_rust_audit_patterns.py`, `check_rust_best_practices.py`, `check_rust_lint_debt.py`, `check_rust_runtime_panic_policy.py`, `check_rust_security_footguns.py`, `check_rust_test_shape.py`, and `check_structural_complexity.py` each implement their own `_run_git()`.

**Fix:** Extract to `dev/scripts/checks/rust_guard_common.py` (already exists but underused) or `dev/scripts/devctl/common.py`.

**Files:** 9 check scripts + 1 shared module

#### 4. HIGH: Python `_helpers` vs `_support` vs `_core` Naming Chaos
**Finding:** 25+ helper files use 3 inconsistent naming patterns with no clear layering convention.

**Fix:** Standardize to:
- `*_core.py` = business logic implementation
- `*_render.py` = output formatting
- `*_parser.py` = CLI argument wiring
- Deprecate `_support` and `_helpers` suffixes over time (rename where practical)

**Files:** Document the convention in `dev/scripts/README.md`, rename highest-impact files

#### 5. HIGH: Missing Test Coverage for Policy Engines
**Finding:** ~35-40% of check script logic is untested. Key gaps:
- `check_code_shape.py` (639 lines, no test)
- `code_shape_policy.py` (policy engine, no test)
- `coderabbit_gate_core.py` (no test)
- `naming_consistency_core.py` (no test)
- `check_active_plan_sync.py` (441 lines, no test)

**Fix:** Add unit tests for the top 5 untested policy engines.

**Files:** New test files in `dev/scripts/devctl/tests/`

#### 6. HIGH: CI Hardcoded Constants
**Finding:** Values like mutation threshold `0.80`, wait seconds `1800`, poll seconds `20`, markdownlint version `0.45.0`, Python `3.11` are scattered across workflows.

**Fix:** Create `dev/config/ci_constants.env` or consolidate into existing `dev/config/` and reference from workflows.

#### 7. MEDIUM: AGENTS.md Missing Items for Release Readiness

Current AGENTS.md is comprehensive but missing:

a. **No error recovery protocol** — What to do when a bundle command fails mid-run. Should agents retry? Skip? The 12-step SOP says "do not skip steps" but doesn't address partial failures.

b. **No dependency installation prerequisites** — AGENTS.md assumes `markdownlint`, `cargo`, `python3` are available but never documents how to install them. Add a "Prerequisites" section.

c. **No `bundle.quick`/`bundle.fast` definition** — `check --profile fast` exists as a command but there's no bundle for quick iteration. Developers need to know what's safe to skip during rapid local dev.

d. **No CI workflow dependency graph** — AGENTS.md lists 28 workflows but doesn't show which trigger which. For release, this matters (preflight -> publish_pypi -> publish_homebrew -> attestation).

e. **No "when to break the rules" escape hatch** — Every policy file should have a documented override path. Currently the only escape is the checkpoint waiver in MP-346.

f. **Bundle duplication makes the doc hard to scan** — The rendered bundles take 120+ lines and are 80% identical. The composition refactor (item 1) will fix this.

#### 8. MEDIUM: Rust Code — Minor Refactoring Opportunities
- `wake_word.rs` (878 LOC): Split into `listener.rs` + `detector.rs`
- `runtime_compat.rs` (668 LOC): Could split into backend + terminal compat
- Both are thematically cohesive so this is optional/low priority

#### 9. MEDIUM: Comment Audit Findings
Comments are generally KISS-compliant. Specific items to clean up:

a. **Rust `writer/state.rs`**: 27 `#[cfg(test)]` constants at file top with long names like `CLAUDE_JETBRAINS_COMPOSER_REPAIR_QUIET_MS` — these should be in the test module, not polluting the production namespace.

b. **Python check scripts**: Docstrings explain "what" but rarely explain failure modes or "why this threshold". Add 1-line "Rationale:" comments to magic numbers in policy files.

c. **AGENTS.md status snapshot**: Lines 19-170 are 150 lines of incremental update bulletins. These should be archived to a separate changelog — they make the file harder to scan.

#### 10. LOW: CI Workflow Redundancy
- `release_preflight.yml` and `tooling_control_plane.yml` run overlapping checks
- 6 workflows duplicate `workflow_shell_bridge.py resolve-range` pattern
- Could extract to composite actions or reusable workflows

#### 11. HIGH: Rust Error Handling Inconsistencies
**Finding (Round 2 — Rust deep audit):**
- `ipc/session.rs:181` — `Result<ClaudeJob, String>` instead of `anyhow::Result` or typed error. Loses error context.
- `voice.rs:689` — `expect("voice job result")` on channel recv in production code. Could panic if worker thread exits unexpectedly.
- `voice.rs:698` — `expect("voice job thread")` on thread join. Should handle panicked workers gracefully.
- `voice.rs:192` — Double `Arc::clone()` on `capture_active_clone` (already cloned on line 183). Unnecessary allocation.
- 18+ `#[allow(dead_code)]` in `ipc/session/event_sink.rs:30-60` without `reason` attributes (violates project's own engineering quality contract).

**Fix:** Replace `Result<T, String>` with `anyhow::Result`. Convert risky `expect()` to `match`/`unwrap_or` with graceful fallback. Add `reason` attributes to all `#[allow(dead_code)]`.

**Files:** `rust/src/ipc/session.rs`, `rust/src/voice.rs`, `rust/src/ipc/session/event_sink.rs`

#### 12. HIGH: Repository URL Mismatch Across Docs
**Finding (Round 2 — docs audit):**
- `README.md` references `github.com/jguida941/voiceterm` (correct)
- `pypi/pyproject.toml` lines 27-30 reference `github.com/jguida941/voiceterm` (correct)
- `rust/Cargo.toml` line 9 previously referenced `github.com/jguida941/codex-voice` (fixed to `voiceterm`)
- `.coderabbit.yaml` currently has no repository URL mismatch entries

**Impact:** Broken links, PyPI metadata points to wrong repo, confuses contributors.

**Fix:** Standardize all references to the correct `codex-voice` repo URL.

**Files:** `README.md`, `pypi/pyproject.toml`

#### 13. HIGH: No Release Rollback Procedures
**Finding (Round 2 — release audit):**
No documented rollback strategy for failed releases:
- No PyPI yank automation
- No GitHub release unpublish automation
- No Homebrew formula rollback script
- No documented manual steps for emergency reversal

**Fix:** Create rollback runbook in `AGENTS.md` or `dev/DEVELOPMENT.md` with exact commands for PyPI yank, GH release delete, Homebrew revert.

**Files:** `AGENTS.md` or `dev/DEVELOPMENT.md`

#### 14. HIGH: macOS App Info.plist Minimal (3/10)
**Finding (Round 2 — release audit):**
`app/macos/VoiceTerm.app/Contents/Info.plist` is missing:
- `NSHighResolutionCapable` (Retina support)
- `NSRequiredOSVersion` (minimum macOS)
- `CFBundleIconFile` (app icon)
- Code signing / notarization metadata
- `NSPrincipalClass`

**Fix:** Add missing plist keys. Track code signing as separate MP item if not already planned.

**Files:** `app/macos/VoiceTerm.app/Contents/Info.plist`

#### 15. MEDIUM: Missing Project Files
**Finding (Round 2 — docs audit):**
- `dev/history/README.md` — now present (previously missing)
- `dev/deferred/README.md` — now present (previously missing)
- 5 empty `cvelist*` files cluttering root (stale security scan artifacts)

**Fix:** Keep README files in place; add `cvelist*` to `.gitignore` and remove stale artifacts.

**Files:** `.gitignore`, root stale artifact cleanup

#### 16. MEDIUM: No Python Tooling Config for dev/scripts
**Finding (Round 2 — Python quality audit):**
- No `pyproject.toml` for dev/scripts (linting, formatting)
- No `requirements.txt` or pinned Python dependencies
- No ruff/flake8/mypy configuration
- No `.editorconfig` for cross-language consistency

**Fix:** Add minimal `pyproject.toml` in `dev/scripts/` with ruff config. Add `.editorconfig` at repo root.

**Files:** `dev/scripts/pyproject.toml` (new), `.editorconfig` (new)

#### 17. MEDIUM: check.py `run()` Function is 323 Lines
**Finding (Round 2 — Python quality audit):**
`dev/scripts/devctl/commands/check.py` lines 56-378 — single `run()` function with nested closures. Hard to test, hard to maintain.

**Fix:** Extract phases into named functions (setup, gate checks, test execution, reporting).

**Files:** `dev/scripts/devctl/commands/check.py`

#### 18. MEDIUM: Mutation Testing Badge Stale + Advisory-Only
**Finding (Round 2 — testing audit):**
`.github/badges/mutation-score.json` shows "stale" status. Mutation scoring is advisory (non-blocking) — doesn't actually gate releases.

**Fix:** Investigate why badge is stale. Consider making mutation score blocking for critical modules (ipc/, pty_session/).

**Files:** `.github/badges/mutation-score.json`, `.github/workflows/mutation-testing.yml`

#### 19. MEDIUM: AGENTS.md at 998 Lines — Exceeds Best Practice Threshold
**Finding (Round 2 — best practices research):**
GitHub's analysis of 2,500+ repos recommends breaking AGENTS.md into linked docs when exceeding ~500 lines. Current file is 998 lines. Also missing "always/ask/never" boundary tiers that are best practice for AI agent control.

**Fix:** Extract reference-only sections (tooling inventory details, CI lane mapping, supporting script lists) into linked docs. Add explicit three-tier boundary rules.

**Files:** `AGENTS.md`, potentially new linked docs

---

## Why DevCtl Didn't Catch These Issues (Gap Analysis)

This is the most important finding. The tooling should have prevented most of these issues but didn't because of specific gaps:

### Gaps in Current Guard Coverage

| Issue Found | Why DevCtl Missed It | Guard That Should Exist |
|-------------|---------------------|------------------------|
| Bundle DRY violation (15 duplicate commands) | No duplication check on bundle_registry.py itself | `check_bundle_registry_dry.py` — flag when >N commands are shared across bundles without composition |
| 93 CI shell blocks without `set -e` | `check_workflow_shell_hygiene.py` exists but only checks specific anti-patterns (find\|head, inline Python), not missing `set -e` | Extend `check_workflow_shell_hygiene.py` to flag multi-line `run:` blocks without `set -euo pipefail` |
| 5 duplicate `_run_git()` implementations | `check_duplication_audit.py` runs jscpd but at file level, not function level | Add function-level duplication detection or a "shared utility inventory" check |
| `_helpers`/`_support`/`_core` naming chaos | No naming convention enforcement for Python helper files | `check_naming_consistency.py` covers Rust/provider tokens but not Python module naming patterns |
| 35-40% untested policy engines | No test-coverage-for-check-scripts guard | `check_test_coverage_parity.py` — flag check scripts without corresponding test files |
| Hardcoded CI constants | No check for scattered magic values in workflows | Extend `check_workflow_shell_hygiene.py` or new `check_ci_constants.py` |
| `Result<T, String>` in Rust | `check_rust_best_practices.py` checks `#[allow]`, unsafe, mem::forget but not error type patterns | Extend `check_rust_best_practices.py` to flag `Result<_, String>` in non-test code |
| `expect()` on thread joins | `check_rust_runtime_panic_policy.py` checks `panic!` but not `expect()` on fallible operations | Extend panic policy to include `expect()` on `thread::JoinHandle` and channel `recv` |
| 18+ `#[allow(dead_code)]` without reason | `check_rust_best_practices.py` checks for reason-less `#[allow]` but these were in `cfg(test/mutants)` code which may be skipped | Verify the check doesn't skip `cfg(any(test, ...))` blocks |
| Repo URL mismatch | No cross-doc URL consistency check | `check_repo_url_parity.py` — verify all doc/config repo URLs match |
| Missing README files | `check_active_plan_sync.py` checks active docs but not `dev/history/` or `dev/deferred/` | Extend docs-check to verify referenced directories have README files |
| No rollback procedures | No release-completeness check | Extend `check_release_version_parity.py` or `release-gates` to verify rollback docs exist |
| macOS plist gaps | No plist validation guard | `check_macos_plist_completeness.py` — verify required keys exist |
| No Python linting config | No meta-tooling check | `check_python_tooling_config.py` — verify dev/scripts has linting config |
| check.py 322-line function | `check_code_shape.py` enforces file-level limits but no function-level limits for Python | Extend `code_shape_function_policy.py` to cover Python (currently Rust-only) |
| AGENTS.md at 999 lines | `check_code_shape.py` has file limits but AGENTS.md is exempt as a docs file | Add AGENTS.md to a docs-size-budget check or explicit exemption with a ceiling |
| Stale mutation badge | `check_mutation_score.py` is advisory-only and non-blocking | Make mutation freshness a warning in `devctl hygiene` |

### Root Cause Analysis

The devctl guard system was designed incrementally — each guard was added to catch a specific class of issue as it was discovered. This created three systemic blind spots:

1. **Guards check what's in the code, not what's missing.** Most guards scan for anti-patterns (too many lines, unsafe blocks, etc.) but don't check for the *absence* of required infrastructure (test files, linting config, rollback docs, README files).

2. **Guards are scoped to one language/layer.** `check_code_shape.py` handles Rust and Python file sizes but not workflow YAML. `check_naming_consistency.py` handles Rust enums but not Python module naming. No guard crosses all three layers.

3. **Guards don't audit themselves.** The bundle registry, the guard scripts themselves, and the AGENTS.md doc have no self-referential quality checks. The cobbler's children have no shoes.

### Recommended New Guards (Priority Order)

1. **`check_workflow_shell_safety.py`** — Extend existing shell hygiene to flag missing `set -euo pipefail` in multi-line blocks
2. **`check_test_coverage_parity.py`** — Flag check scripts in `dev/scripts/checks/` without matching test files
3. **`check_bundle_registry_dry.py`** — Flag when bundles share >N commands without using composition
4. **Extend `check_rust_best_practices.py`** — Add `Result<_, String>` and `expect()` on join/recv patterns
5. **`check_repo_url_parity.py`** — Verify repo URLs are consistent across all docs and configs
6. **Extend `check_code_shape.py`** — Add Python function-length limits (not just file-length)
7. **Extend `devctl hygiene`** — Add mutation badge freshness check and missing README warnings

---

### Round 3 Findings (Infrastructure + Production Readiness)

#### 21. CRITICAL: No Static Analysis on 55K Lines of Python Tooling
**Finding (Round 3 — research + Python audit):**
No ruff, mypy, or any linter configured for `dev/scripts/`. Every Python guard script enforcing quality on Rust code has zero static analysis enforcing quality on itself.
- No `pyproject.toml` for `dev/scripts/` (linting/formatting config)
- No type checking (mypy) — type hints likely minimal
- No pre-commit hooks configured (`.pre-commit-config.yaml` missing)
- Import fallback boilerplate (try/except ModuleNotFoundError) adds ~24 lines per script instead of proper Python path setup

**Impact:** Silent type errors, inconsistent formatting, undetected bugs in the guard infrastructure itself.

**Fix:** Add `dev/scripts/pyproject.toml` with `[tool.ruff]` and `[tool.mypy]` config. Add ruff+mypy CI step. Proper sys.path setup to eliminate import fallbacks.

**Devctl guard gap:** No meta-tooling check exists. Need `check_python_tooling_config.py`.

#### 22. CRITICAL: Unmaintained Dependencies Block Rust 2024 Edition
**Finding (Round 3 — dependency health audit):**
Three dependencies are unmaintained/deprecated and block the Rust 2024 edition upgrade:
- `serde_norway` (0.9.42) — deprecated YAML macro parser, no upgrade path
- `gag` (1.0) — unmaintained stdout suppression crate, no updates
- `whisper-rs` (0.14.1) — pinned, upstream maintenance unclear

MSRV is already 1.88.0 (supports edition 2024), but these deps likely won't compile under new edition rules.

**Impact:** Stuck on edition 2021. Blocks access to RPIT lifetime improvements, new rustfmt defaults, and match ergonomics.

**Fix:** Replace `serde_norway` with maintained YAML parser. Replace `gag` with custom stdout redirect or alternative. Track `whisper-rs` upstream. Already partially tracked in active plans.

**Devctl guard gap:** No edition-readiness check. Could add `check_rust_edition_readiness.py`.

#### 23. CRITICAL: No Post-Release Smoke Tests
**Finding (Round 3 — CI/CD audit):**
After publishing to PyPI, Homebrew, and GitHub Releases, no workflow verifies the published artifacts actually work:
- No PyPI install + CLI smoke test
- No Homebrew formula install test
- No binary download + checksum verify + smoke test
- If a bad release ships, it's discovered by users, not CI

**Impact:** Broken releases reach production undetected.

**Fix:** Add `verify_release_artifacts.yml` triggered on `release: published`. Tests: `pip install voiceterm && voiceterm --version`, Homebrew formula install on macOS, binary download + smoke.

**Devctl guard gap:** No release-verification check. Need `devctl verify-release --pypi --homebrew --binaries`.

#### 24. HIGH: No Semantic Versioning or Conventional Commit Enforcement
**Finding (Round 3 — CI/CD audit):**
- No `commitlint`, `release-please`, or `semantic-release` configured
- No PR title validation (feat:/fix:/chore: pattern)
- Version bumps are fully manual with no CI verification of semver format
- Changelog (`dev/CHANGELOG.md`) is manually maintained, no auto-generation

**Impact:** Version bumps can violate semver. Changelog can go stale on releases.

**Fix:** Add PR title lint workflow. Add changelog-updated-on-version-bump check to `release_preflight.yml`.

**Devctl guard gap:** Could add `check_semver_enforcement.py` and `devctl check --pr-title-lint`.

#### 25. HIGH: Config Persistence TOCTOU Race Condition
**Finding (Round 3 — Rust deep audit):**
`persistent_config.rs` does read-modify-write on user config files without locking:
1. `load_user_config()` reads file
2. Runtime state modified in memory
3. `save_user_config()` writes back
If another process modifies config between steps 1 and 3, changes are silently lost. No file locking, no atomic rename.

Similar pattern in `onboarding.rs` (line 99-105) — check-then-act without atomicity.

**Impact:** User preferences silently lost in multi-process scenarios.

**Fix:** Use atomic write (write to temp file, then `fs::rename`). Add file locking for config persistence.

**Devctl guard gap:** No guard for unatomic file persistence. Need `check_file_persistence_atomicity.py` or extend `check_rust_best_practices.py`.

#### 26. HIGH: Terminal Restore Race Condition
**Finding (Round 3 — Rust deep audit):**
`terminal_restore.rs` stores atomic flags AFTER I/O operations. If `execute!()` fails at line 52, `ALT_SCREEN_ENABLED` is already set to `true` but the action didn't happen. On drop, restoration attempts to disable alt-screen that was never enabled — corrupting terminal state.

Panic hook (lines 92-102) discards all I/O errors with `let _ = ...`. If terminal restore fails during panic, the shell is left in raw mode with no diagnostics.

**Impact:** Terminal state corruption on error paths; debugging impossible in panic scenarios.

**Fix:** Set flag before I/O, or use a guard pattern that rolls back flag on I/O failure.

**Devctl guard gap:** No guard for atomic-flag-before-I/O patterns. Extend `check_rust_best_practices.py`.

#### 27. HIGH: PTY Read Buffer Sign-Unsafe Cast
**Finding (Round 3 — Rust deep audit):**
`pty_session/io.rs:103-106` — cast from `libc::ssize_t` to `usize` without validating `n >= 0`. If `n` is negative (read error), the cast produces a huge unsigned value, `buffer.get()` returns `&[]`, and the error is silently swallowed.

**Impact:** PTY read errors silently discarded; data loss without visibility.

**Fix:** Check `n >= 0` before cast; propagate negative values as errors.

**Devctl guard gap:** `check_rust_security_footguns.py` doesn't check for sign-unsafe syscall return casts. Extend it.

#### 28. HIGH: No cargo-vet Supply Chain Trust
**Finding (Round 3 — research):**
`cargo-audit` and `cargo-deny` are present (good), but `cargo-vet` (Mozilla/Google trust chain model) is missing. No `supply-chain/audits.toml` for human-audited crate trust. Also missing `cargo-auditable` for embedding dependency metadata in release binaries and no SBOM generation for release artifacts.

**Impact:** Supply chain defense lacks the "trust chain" layer. Release binaries can't be audited post-build.

**Fix:** Add `cargo-vet init`, begin auditing direct dependencies. Add `cargo-auditable` to release profile. Generate SBOM in release workflow.

**Devctl guard gap:** Could add `check_supply_chain_trust.py` to verify `supply-chain/audits.toml` exists.

#### 29. HIGH: Asymmetric Platform Testing
**Finding (Round 3 — cross-platform audit):**
- Full test suite runs only on Linux (ubuntu-latest)
- macOS (arm64) gets only a smoke test (`cargo test --bin voiceterm`)
- ARM64 Linux is documented as "Supported" in INSTALL.md but has NO CI testing and NO release binary
- No Windows CI (expected, but dead Windows permission-hint code exists in `recorder.rs`)

**Impact:** macOS-specific regressions can ship undetected. ARM64 Linux claim is unverified.

**Fix:** Add macOS to full test matrix (or at minimum, PTY + IPC tests). Either add ARM64 Linux CI or downgrade docs to "untested". Remove dead Windows code or add WSL2 plan.

**Devctl guard gap:** Need `check_platform_support_matrix.py` — verify all platforms in INSTALL.md have CI coverage.

#### 30. HIGH: No Statistical Benchmark Harness or Historical Perf Tracking
**Finding (Round 3 — performance audit):**
- Three custom benchmark binaries exist (`voice_benchmark`, `stt_file_benchmark`, `latency_measurement`) but none are run in CI
- No Criterion/iai integration for statistical benchmarks
- No Bencher/benchmark-action for historical regression tracking
- `perf_smoke.yml` runs a single bounds-check test — no baseline comparison
- No stored performance baselines for voice pipeline metrics

**Impact:** P95 latency could drift 30%+ over releases with no detection.

**Fix:** Integrate at least one benchmark binary into CI nightly. Add Criterion for hot-path benchmarks. Store baseline JSON for regression comparison.

**Devctl guard gap:** Could add `check_perf_baselines.py` to verify baseline files exist and haven't aged.

#### 31. MEDIUM: Workflow Dispatch Input Validation Gaps
**Finding (Round 3 — CI/CD audit):**
Several `workflow_dispatch` workflows accept inputs without validation:
- `autonomy_controller.yml`: `plan_id`, `max_rounds`, `max_hours` not validated
- `autonomy_run.yml`: similar unvalidated inputs
- `coderabbit_ralph_loop.yml`: `max_attempts`, `poll_seconds` not validated
- Branch name inputs accepted without format checking

**Impact:** Malformed inputs could cause unexpected workflow behavior.

**Fix:** Add input validation blocks to complex workflow_dispatch workflows.

**Devctl guard gap:** Could add `check_workflow_dispatch_inputs.py`.

#### 32. MEDIUM: Broad Exception Handling in Python Guard Scripts
**Finding (Round 3 — Python audit):**
- `status_report.py:31,57` — bare `except Exception` swallows all errors including unexpected ones (KeyError, AttributeError, MemoryError)
- `policy_gate.py:24-31` — `subprocess.run(check=False)` with exit code handling only for 0/1; codes 2, 127, etc. are undefined
- Multiple check scripts use `sys.exit(main())` at module level which prevents clean unit testing

**Impact:** Silent failures in guard infrastructure; scripts that enforce quality can't be unit-tested themselves.

**Fix:** Use specific exception types. Handle all non-zero exit codes explicitly. Wrap `sys.exit()` in `if __name__ == "__main__"` blocks.

**Devctl guard gap:** Could add `check_python_exception_patterns.py`.

#### 33. MEDIUM: Custom TOML Parsers Instead of Using `toml` Crate
**Finding (Round 3 — Rust deep audit):**
Both `persistent_config.rs` and `onboarding.rs` implement custom TOML parsers that:
- Don't handle `[section]` headers properly
- Don't handle escaped quotes in values
- Don't handle multiline values
- Don't validate key identifiers

The `toml` crate is already a dependency (in Cargo.toml). These custom parsers are unnecessary and fragile.

**Impact:** Config files generated by standard TOML tools may fail silently.

**Fix:** Replace custom parsers with `toml` crate calls.

**Devctl guard gap:** Extend `check_rust_best_practices.py` to flag custom format parsers when standard crates are available.

#### 34. MEDIUM: Serde Enum Backward Compatibility Gap
**Finding (Round 3 — Rust deep audit):**
`ipc/protocol.rs:152-191` — `IpcCommand` enum uses `#[serde(tag = "cmd")]` without `#[serde(deny_unknown_fields)]`. Unknown commands from newer clients are silently dropped by older servers.

**Impact:** Silent command loss during version mismatches; difficult to debug IPC issues.

**Fix:** Add `#[serde(other)]` variant or `deny_unknown_fields` depending on desired behavior. Document protocol versioning strategy.

**Devctl guard gap:** Could add `check_serde_compatibility.py` to flag tagged enums without forward-compat handling.

#### 35. MEDIUM: Python CI/PyPI Version Mismatch
**Finding (Round 3 — dependency audit):**
- PyPI `pyproject.toml` declares `requires-python = ">=3.9"`
- CI workflows all use `python-version: "3.11"`
- Python 3.9-3.10 users may encounter untested compatibility issues
- No `.python-version` file to document developer requirements

**Impact:** PyPI claims Python 3.9 support that isn't CI-tested.

**Fix:** Either test CI on Python 3.9 (lowest supported) or raise PyPI floor to 3.11.

**Devctl guard gap:** Could add `check_python_version_parity.py` — verify CI tests lowest declared version.

#### 20. POST-RELEASE: Cursor+Claude Plan-Mode Rendering Anomaly
**Finding:** In Cursor terminal sessions, entering Claude plan mode (especially with local/background agents active) can temporarily hide the visible chat/history region and render HUD/status rows over normal output; occasional garbled characters/symbols appear in the corrupted state.

**Repro clue:** The issue clears after terminal resize/readjust, which strongly suggests a geometry/repaint synchronization gap.

**Impact:** During long planning/audit runs, visual corruption can hide actionable text and reduce confidence in runtime status fidelity.

**Fix path:** Track as post-release runtime investigation in `dev/active/MASTER_PLAN.md` (`MP-349`) with required evidence: before/after resize screenshots, terminal host/version, provider/backend, HUD mode/style, `rows/cols` before+after resize, and `VOICETERM_DEBUG_CLAUDE_HUD=1` logs.

**Files:** `dev/active/MASTER_PLAN.md` (tracking), runtime writer/terminal redraw path follow-up after release.

---

## Execution Checklist

### Phase 1: Bundle DRY Refactor + AGENTS.md Cleanup
- [x] Refactor `bundle_registry.py` to use composition (common + extras)
- [x] Re-render AGENTS.md bundle section via `check_agents_bundle_render.py --write`
- [x] Add "Prerequisites" section to AGENTS.md
- [x] Add "Error recovery protocol" section to AGENTS.md
- [x] Add "Quick iteration guide" section to AGENTS.md (already existed as "Quick command intent" table)
- [x] Add CI workflow dependency graph to AGENTS.md
- [x] Archive status snapshot bulletins — N/A: bulletins are in MASTER_PLAN.md, not AGENTS.md; AGENTS.md has no status snapshot
- [x] Run verification: `check_agents_bundle_render.py` + `check_bundle_workflow_parity.py` + `check_agents_contract.py` all pass

### Phase 2: CI Robustness
- [x] Audit all 28 workflows for missing `set -euo pipefail`
- [x] Add `set -euo pipefail` to all unguarded multi-line shell blocks
- [x] Document intentional `set +e` blocks with rationale comments
- [ ] Consolidate hardcoded constants into `dev/config/ci_constants.env` (deferred post-release)
- [x] Run verification: `check_workflow_shell_hygiene.py` + `check_workflow_action_pinning.py`

### Phase 3: Python Tooling Cleanup
- [x] Consolidate `_run_git()` into `rust_guard_common.py` (7/9 already used shared; `check_code_shape.py` refactored)
- [x] Update 9 check scripts to import shared `_run_git()` (`check_naming_consistency.py` has no `_run_git`)
- [x] Document naming convention (`_core`/`_render`/`_parser`) in `dev/scripts/README.md` (completed in Phase 6)
- [x] Add tests for `check_code_shape.py` policy engine (already existed: `test_check_code_shape_guidance.py`)
- [x] Add tests for `code_shape_policy.py` (already tested via `check_code_shape` integration)
- [ ] Add tests for `coderabbit_gate_core.py` (deferred post-release)
- [ ] Add tests for `naming_consistency_core.py` (deferred post-release)
- [ ] Add tests for `check_active_plan_sync.py` (deferred post-release)
- [x] Run verification: all 564 tests pass

### Phase 4: Rust Error Handling + Dead Code Cleanup
- [ ] Replace `Result<ClaudeJob, String>` with `anyhow::Result` in `ipc/session.rs:181` (deferred post-release: behavioral change risk)
- [x] Replace `expect()` with graceful match on `voice.rs:689`/`698` — N/A: these are test code, `expect()` in tests is idiomatic
- [x] Remove double Arc clone in `voice.rs:192` — N/A: second clone is needed; `perform_voice_capture` takes ownership, line 195 uses original
- [x] Add `reason` attributes to all 16 `#[allow(dead_code)]` in `ipc/session/event_sink.rs`, `ipc/session.rs`, `ipc/session/auth_flow.rs`
- [ ] Move `#[cfg(test)]` constants from `writer/state.rs` top-level into test module (deferred post-release)
- [x] Partial verification: dead_code reason attributes added across IPC modules

### Phase 5: Docs, Config, and Project Hygiene
- [x] Fix repo URL mismatch: `rust/Cargo.toml` had wrong repo name (`codex-voice`), fixed to `voiceterm`; all other files already correct
- [x] Create `dev/history/README.md` and `dev/deferred/README.md`
- [x] Add `cvelist*` to `.gitignore` — already present (lines 117-121)
- [x] Add `.editorconfig` at repo root
- [x] Add minimal `pyproject.toml` in `dev/scripts/` with ruff + mypy config
- [x] Add missing macOS plist keys (NSHighResolutionCapable, LSMinimumSystemVersion, NSPrincipalClass)
- [ ] Add release rollback procedures to `AGENTS.md` or `dev/DEVELOPMENT.md` (deferred post-release)
- [x] Partial verification: files created, plist updated

### Phase 6: Refactor check.py and Python Code Quality
- [x] Extract `check.py` `run()` function (312 lines) into named phase functions — `CheckContext` dataclass + phase runners moved to `check_phases.py` (377 lines); `check.py` is now 122-line orchestrator; `run()` is 45 lines
- [x] Document Python module naming convention (`_core`/`_render`/`_parser`) in `dev/scripts/README.md`
- [x] Run verification: 575/575 tests pass; `check.py` at 122 lines (under 425 soft limit)

### Phase 7: DevCtl Guard System Hardening (New Guards)
- [x] Extend `check_workflow_shell_hygiene.py` to flag missing `set -euo pipefail` — added `missing-pipefail` rule with block-level YAML parser; 28 workflows scanned, 0 violations
- [x] Create `check_test_coverage_parity.py` — flags 5 untested check scripts (active_plan_sync, cli_flags_parity, markdown_metadata_header, rustsec_policy, screenshot_integrity); registered in script_catalog
- [x] Create `check_bundle_registry_dry.py` — detects composition model presence; 6 bundles, `uses_composition=True`; registered in script_catalog
- [x] Extend `check_rust_best_practices.py` — added `Result<_, String>` and `expect()` on join/recv metrics; growth-based non-regression enforcement
- [x] Create `check_repo_url_parity.py` — scans 4 config/doc files for canonical repo URL; 0 violations; registered in script_catalog
- [x] Extend `check_code_shape.py` — added Python function-length limits via `scan_python_functions` scanner and `FUNCTION_LANGUAGE_DEFAULTS` (`.py`: 150 lines)
- [x] Extend `devctl hygiene` — added mutation badge freshness check (14-day threshold + stale status detection) and README presence check for required dev dirs
- [x] Run verification: 596/596 tests pass; all new guards produce correct reports

### Phase 8: AGENTS.md Size Reduction + Structure Improvements (deferred post-release)
- [ ] Extract tooling inventory details to linked doc
- [ ] Extract CI lane mapping to linked doc or `.github/workflows/README.md`
- [ ] Extract supporting script lists to `dev/scripts/README.md`
- [ ] Add "always/ask/never" three-tier boundary rules
- [ ] Target AGENTS.md at ~500 lines (currently ~1040)
- [ ] Run verification: `check_agents_contract.py` + `check_agents_bundle_render.py`

### Phase 9: Python Static Analysis Bootstrap (Round 3) (partially done; CI step deferred post-release)
- [x] Add `dev/scripts/pyproject.toml` with `[tool.ruff]` config (line length, select rules, target Python version)
- [x] Add `[tool.mypy]` config for gradual type checking (start with `--ignore-missing-imports`)
- [ ] Add ruff lint + format CI step to `tooling_control_plane.yml` or new workflow (deferred post-release)
- [ ] Fix top 10 ruff findings (deferred post-release)
- [ ] Replace try/except ModuleNotFoundError import fallbacks with proper sys.path setup (deferred post-release)
- [ ] Run verification: `ruff check dev/scripts/` + `mypy dev/scripts/devctl/` (deferred post-release)

### Phase 10: Rust File Persistence + Error Handling (Round 3) (deferred post-release)
- [ ] Replace custom TOML parsers in `persistent_config.rs` and `onboarding.rs` with `toml` crate
- [ ] Add atomic write (write to temp + rename) for config persistence
- [ ] Fix terminal_restore.rs: set flag before I/O or rollback on failure
- [x] Fix pty_session/io.rs: validate `ssize_t >= 0` before usize cast — N/A: code already guards via `if n > 0` before cast
- [ ] Add `#[serde(other)]` or `deny_unknown_fields` to IPC protocol enums
- [ ] Fix dropped channel send results in ipc/router.rs (log errors, don't `let _ =`)
- [ ] Run verification: `cd rust && cargo test --bin voiceterm` + `cargo clippy`

### Phase 11: CI/CD Production Readiness (Round 3) (deferred post-release)
- [ ] Add `verify_release_artifacts.yml` — post-publish smoke tests for PyPI + Homebrew + binaries
- [ ] Add PR title lint workflow (conventional commits: feat/fix/chore prefix)
- [ ] Add changelog-updated-on-version-bump validation to `release_preflight.yml`
- [ ] Add binary artifact provenance attestation to `publish_release_binaries.yml`
- [ ] Document release rollback playbook (PyPI yank, GH release delete, Homebrew revert)
- [ ] Add input validation to `autonomy_controller.yml`, `autonomy_run.yml`, `coderabbit_ralph_loop.yml`
- [ ] Run verification: manual workflow_dispatch test + `check_workflow_shell_hygiene.py`

### Phase 12: Platform Parity + Performance Baselines (Round 3) (deferred post-release)
- [ ] Add macOS to full test suite in `rust_ci.yml` (at minimum: PTY + IPC + voice tests)
- [ ] Either add ARM64 Linux CI or downgrade INSTALL.md claim to "untested"
- [ ] Remove dead Windows permission-hint code from `recorder.rs` or document WSL2 plan
- [ ] Integrate `voice_benchmark` or `latency_measurement` into CI nightly
- [ ] Add Criterion for at least 2 hot-path benchmarks (audio resample, PTY I/O)
- [ ] Store baseline perf JSON for regression comparison
- [ ] Run verification: `perf_smoke.yml` + new benchmark CI step

### Phase 13: Supply Chain + Dependency Health (Round 3) (deferred post-release)
- [ ] Plan `serde_norway` replacement (track as MP item if multi-sprint)
- [ ] Plan `gag` replacement (custom stdout redirect or alternative crate)
- [ ] Upgrade `ratatui` from 0.26 to latest compatible (0.29.x)
- [ ] Add `cargo-vet init` + begin auditing direct dependencies
- [ ] Add `cargo-auditable` to release profile in Cargo.toml
- [ ] Fix Python CI/PyPI version mismatch (test on 3.9 or raise floor to 3.11)
- [ ] Run verification: `cargo deny check` + `cargo vet`

### Phase 14: DevCtl Guard System Hardening v2 (Round 3) (deferred post-release)
- [ ] Add `check_python_tooling_config.py` — verify dev/scripts has ruff/mypy config
- [ ] Add `check_platform_support_matrix.py` — verify INSTALL.md platforms have CI coverage
- [ ] Add `check_python_version_parity.py` — verify CI tests lowest declared Python version
- [ ] Add `check_perf_baselines.py` — verify baseline files exist and haven't aged
- [ ] Extend `check_rust_security_footguns.py` — sign-unsafe syscall casts, unreachable in hot paths
- [ ] Extend `check_rust_best_practices.py` — dropped channel sends, custom parsers, float comparisons, unatomic config writes
- [ ] Add `check_serde_compatibility.py` — flag tagged enums without forward-compat handling
- [ ] Run verification: full `bundle.tooling` pass

---

## Progress Log

| Date | Phase | Action | Result |
|------|-------|--------|--------|
| 2026-03-05 | Phase 7 | Landed DevCtl guard hardening batch (5 new guards, 3 extended guards) | complete: verification pack is green (`596/596` tests); pre-release completion point reached with Phases 8-14 explicitly deferred post-release |
| 2026-03-05 | Phase 6 | Decomposed `check.py` into phase-oriented orchestration and added Python module naming convention docs | complete: `check.py` slim orchestrator + `check_phases.py` extracted; Phase 7 is the next execution scope |
| 2026-03-05 | Accuracy refresh | Revalidated stale audit claims against current repo state | Updated counts/claims (AGENTS lines, `_run_git` duplication, README existence, `check.py` run length, repo URL scope) |
| 2026-03-05 | Audit | Full 4-agent parallel audit completed | Findings documented above |
| 2026-03-05 | Backlog triage | Added Cursor+Claude plan-mode rendering anomaly with resize-recovery clue (`MP-349`) | Post-release scope captured with evidence requirements |
| 2026-03-05 | Audit round 2 | 4-agent deep dive: Rust errors, docs/config, Python quality, testing/release | 10 new findings added (items 11-20) |
| 2026-03-05 | Gap analysis | Analyzed why devctl guards missed all 17+ issues | 15 guard gaps identified, 7 new guards recommended, 3 root causes documented |
| 2026-03-05 | Audit round 3 | 6-agent parallel sweep: research, Rust deep, CI/CD, Python, DX+deps, cross-platform+perf | 15 new findings (items 21-35), 6 new execution phases (9-14) |

## Audit Evidence

| Check | Date | Result |
|-------|------|--------|
| Rust structure audit (Explore agent) | 2026-03-05 | 9/10 module org, 1 TODO, clean boundaries |
| CI/CD audit (Explore agent) | 2026-03-05 | 78/100 overall, 95/100 security, 65/100 robustness |
| Python tooling audit (Explore agent) | 2026-03-05 | 307 files, 35-40% untested policy engines, DRY issues |
| AGENTS.md review (manual) | 2026-03-05 | 998 lines, comprehensive but missing 5 sections |
| Bundle registry review (manual) | 2026-03-05 | 15/18 commands duplicated across 4 bundles |
| Rust error handling deep audit (Explore agent, round 2) | 2026-03-05 | 2 risky expect(), 1 Result<T,String>, 18+ missing reason attrs, 1 double clone |
| Docs/config/hygiene audit (Explore agent, round 2) | 2026-03-05 | Repo URL mismatch, README presence now restored, 5 stale cvelist files, no .editorconfig |
| Python code quality deep audit (Explore agent, round 2) | 2026-03-05 | 244+ typed files, 323-line function, no linting config, no Python deps pinned |
| Testing/release infra audit (Explore agent, round 2) | 2026-03-05 | Rust tests 9.5/10, no rollback docs, macOS plist 3/10, mutation badge stale |
| Best practices research (general agent, round 1) | 2026-03-05 | AGENTS.md >500 lines is anti-pattern, need always/ask/never tiers, thiserror/anyhow split |
| DevCtl gap analysis (synthesis) | 2026-03-05 | 17 issues identified, 15 have guard gaps — guards don't check for missing infra |
| Production monorepo research (general agent, round 3) | 2026-03-05 | 26 findings: cargo workspace gap, cargo-vet missing, no ruff/mypy, edition 2021, no Criterion |
| Rust deep audit round 3 (Explore agent) | 2026-03-05 | 17 issues across 10 files: TOCTOU races, sign-unsafe casts, custom parsers, dropped errors |
| CI/CD completeness audit (Explore agent, round 3) | 2026-03-05 | 21 categories checked: no post-release smoke, no semver enforcement, no changelog automation |
| Python tooling deep audit (Explore agent, round 3) | 2026-03-05 | 19 issues: broad exceptions, sys.exit testability, import fallbacks, oversized functions |
| DX + dependency health audit (Explore agent, round 3) | 2026-03-05 | serde_norway/gag/whisper-rs unmaintained, ratatui 3 versions behind, Python version mismatch |
| Cross-platform + perf baseline audit (Explore agent, round 3) | 2026-03-05 | Asymmetric platform testing, no perf baselines, ARM64 Linux unverified, dead Windows code |
