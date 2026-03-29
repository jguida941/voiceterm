# Pre-Release Architecture Audit & Cleanup Plan

**Status**: pre-release completion point reached (Phases 1-7 complete; Phase 15 docs-IA audit intake added; Phases 8-14 deferred post-release)  |  **Last updated**: 2026-03-09 | **Owner:** Runtime/tooling architecture
Execution plan contract: required

## Scope

Full-surface architecture audit and cleanup before next release cycle. Goal: make the codebase cleaner, more maintainable, more scalable, and following all best practices for both AI agents and human developers.

Keep this file active as the detailed execution spec for remaining phases;
`dev/active/MASTER_PLAN.md` remains the authoritative tracker state.
This file is the single canonical source for both pre-release findings and
execution sequencing in this lane.

Operator execution note (2026-03-05): pre-release execution checkpoint reached (Phases 1-7 complete). Phases labeled "deferred post-release" remain default policy but may be promoted by explicit operator direction.

## Execution Quality Contract (Plan-Specific)

All remediation work executed from this plan must preserve the project's
existing readability baseline:

- Keep comments simple and intent-focused (explain "why", not obvious "what").
- Use concise, plain-language docstrings for public Python APIs.
- Prefer small, named functions over dense logic blocks.
- Keep naming explicit so behavior is understandable without cross-file guesswork.
- If a cleanup may reduce clarity, choose the clearer implementation even if it
  is slightly less compact.

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

### Round 4 Findings (Developer Information Architecture + Active Directory Hygiene)

#### 36. CRITICAL: Durable maintainer guides are mixed into `dev/` root without a dedicated namespace
**Finding (Round 4 — docs organization audit):**
- `dev/` currently contains 76 markdown files, with 7 top-level policy/guide docs mixed together (`ARCHITECTURE`, `DEVELOPMENT`, `DEVCTL_AUTOGUIDE`, `MCP_DEVCTL_ALIGNMENT`, `BACKLOG`, `CHANGELOG`, `README`).
- Stable guide material is interleaved with tracker/governance surfaces, making discovery and ownership boundaries blurry.

**Impact:** New contributors and agents must memorize path exceptions; move operations are high-risk because ownership boundaries are implicit rather than structural.

**Fix:** Create `dev/guides/` and move durable maintainer guides there:
- `dev/guides/ARCHITECTURE.md`
- `dev/guides/DEVELOPMENT.md`
- `dev/guides/DEVCTL_AUTOGUIDE.md`
- `dev/guides/MCP_DEVCTL_ALIGNMENT.md`
- `dev/guides/README.md` as the canonical maintainer-guide index.

#### 37. HIGH: Duplicate developer entrypoints create drift risk (`DEV_INDEX.md` vs `dev/README.md`)
**Finding (Round 4 — docs organization audit):**
- Both files are "Developer Index" entrypoints with overlapping navigation lists.
- This duplicates maintenance and increases drift risk during path reorganizations.

**Impact:** Source-of-truth ambiguity for onboarding and AI agents; link drift becomes likely during staged moves.

**Fix:** Make `dev/README.md` the canonical developer index and reduce `DEV_INDEX.md` to a short bridge page that points to `dev/README.md` + key top-level user docs only.

#### 38. HIGH: `dev/BACKLOG.md` is orphaned from active execution governance
**Finding (Round 4 — docs organization audit):**
- `dev/BACKLOG.md` has `LB-*` items but no references in AGENTS/devctl/docs checks (`0` matches from code/docs/workflow scan).
- Items in this file are not tied to `MASTER_PLAN` execution state.

**Impact:** Hidden backlog state bypasses active-plan governance and can diverge from tracked `MP-*` commitments.

**Fix:** Either:
1. Merge actionable items into `dev/active/MASTER_PLAN.md` as `MP-*`, or
2. Move file to `dev/deferred/LOCAL_BACKLOG.md` with explicit "non-execution, reference-only" contract.

#### 39. HIGH: `dev/active/` mixes execution docs with generated/reference artifacts
**Finding (Round 4 — docs organization audit):**
- `dev/active/RUST_AUDIT_FINDINGS.md` is generated artifact output, not long-lived execution intent.
- `dev/active/phase2.md` is long-range reference research, not active execution state.
- Active directory currently has 15 files with mixed intent classes.

**Impact:** Active execution surface is noisy; generated/reference files dilute the "what is active now" signal.

**Fix:** Keep `MASTER_PLAN` + active specs/runbooks in `dev/active/`; move generated/reference material out:
- Move generated findings to `dev/reports/audits/` (or `dev/audits/findings/`), keep a pointer doc only if needed.
- Move long-range references to `dev/reference/` or `dev/deferred/` and keep INDEX links explicit.

#### 40. CRITICAL: Documentation path moves have a broad guard/workflow blast radius
**Finding (Round 4 — migration safety audit):**
- Top-level guide paths are hardcoded across checks, workflow path filters, docs indexes, and tests.
- Example coupling: `dev/DEVELOPMENT.md` is referenced by tooling workflow triggers and multiple `docs-check`/`check-router` constants.
- `dev/CHANGELOG.md` is deeply coupled to release scripts and parity checks.

**Impact:** Blind path moves will break docs gates, CI trigger routing, and release automation.

**Fix:** Use a two-step compatibility migration:
1. Introduce new canonical paths and update all constants/parsers/tests/workflow path filters.
2. Keep temporary bridge docs at old paths for one cycle; remove after all checks pass and references converge.

#### 41. MEDIUM: docs-check path policy is duplicated in two modules
**Finding (Round 4 — tooling organization audit):**
- `docs_check_constants.py` and `docs_check_policy.py` carry overlapping path constants.
- Any reorg requires dual edits, increasing mismatch risk.

**Impact:** Directory migration changes are harder and error-prone.

**Fix:** Consolidate path policy constants into a single module and import it in both call paths.

#### 42. MEDIUM: `pre_release_architecture_audit.md` is active but weakly discoverable
**Finding (Round 4 — docs discovery audit):**
- This plan is indexed in `dev/active/INDEX.md` but not linked in AGENTS source-of-truth map.

**Impact:** Operators can miss the current architecture audit execution state.

**Fix:** Add this file to AGENTS source-of-truth map under architecture/tooling audit context.

### Round 4 Proposed Target Layout

```text
dev/
  guides/
    README.md
    ARCHITECTURE.md
    DEVELOPMENT.md
    DEVCTL_AUTOGUIDE.md
    MCP_DEVCTL_ALIGNMENT.md
  active/
    INDEX.md
    MASTER_PLAN.md
    *.md (execution specs/runbooks only)
  audits/
  reports/
  deferred/
  history/
  adr/
  README.md
  CHANGELOG.md
```

Round 4 pushback decision: keep `dev/CHANGELOG.md` at its current path for now; it is tightly coupled to release scripts/tests/checks and is not worth moving during the first organization pass.

### Round 4 Compatibility Map (Required Before Any Path Moves)

| Surface | Coupled files today | Required update for guide-path migration |
|---|---|---|
| Docs policy gates | `dev/scripts/devctl/commands/docs_check_constants.py`, `dev/scripts/devctl/commands/docs_check_policy.py`, `dev/scripts/devctl/commands/docs_check.py` | Update required-doc and evolution-trigger path lists to new `dev/guides/*` paths |
| Router lane classification | `dev/scripts/devctl/commands/check_router_constants.py` | Update `TOOLING_EXACT_PATHS` for moved guide docs |
| Workflow triggers | `.github/workflows/tooling_control_plane.yml` | Update `on.push.paths` and `on.pull_request.paths` entries |
| Active-plan governance links | `AGENTS.md`, `DEV_INDEX.md`, `dev/README.md` | Repoint canonical links and remove duplicate entrypoint drift |
| Generated findings default path | `dev/scripts/devctl/commands/audit_scaffold.py`, parser defaults + tests + docs | Repoint default output path if `RUST_AUDIT_FINDINGS.md` leaves `dev/active/` |
| Release metadata/changelog | `check_release_version_parity.py`, `ship_common.py`, `release_prep.py`, `generate-release-notes.sh`, `update-homebrew.sh`, tests | Keep `dev/CHANGELOG.md` stable in Phase 15; re-evaluate only in a later dedicated release-path migration |

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
- [x] Move `#[cfg(test)]` constants from `writer/state.rs` top-level into test module (completed 2026-03-07: moved timing constants into `writer/state/tests.rs`, keeping production module scope focused on runtime paths)
- [x] Partial verification: dead_code reason attributes added across IPC modules
- [ ] Close the Rust runtime panic/resource-leak backlog cluster from
      `issues.md`: `ISS-050` and `ISS-051` stay owned here until production
      `unwrap()` risk is burned down on live Rust paths and voice-capture job
      shutdown closes microphone/device ownership deterministically instead of
      detaching leaked workers.

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
- [ ] Remove stale/confusing bridge-era references while trimming the file
      (for example legacy runbook/doc entrypoints that are no longer canonical)
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
- [ ] Close the release/push hardening backlog cluster from `issues.md`:
      `ISS-016`, `ISS-058`, and `ISS-059` stay owned here until push/release
      workflow tests stop relying on heavy mocks that hide integration
      failures, `rust_ci.yml` no longer performs unguarded badge-update pushes,
      and release workflows validate required secrets before attempting live
      publish paths.
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
- [x] Upgrade `ratatui` from 0.26 to latest compatible (landed at `ratatui 0.30.0` + `crossterm 0.29.0`; transitive `lru` moved to `0.16.3` and cleared the `RUSTSEC-2026-0002` path)
- [ ] Add `cargo-vet init` + begin auditing direct dependencies
- [ ] Add `cargo-auditable` to release profile in Cargo.toml
- [ ] Fix Python CI/PyPI version mismatch (`ISS-031`) (test on 3.9 or raise floor to 3.11)
- [ ] Run verification: `cargo deny check` + `cargo vet`

### Phase 14: DevCtl Guard System Hardening v2 (Round 3) (deferred post-release)
- [ ] Add `check_python_tooling_config.py` — verify dev/scripts has ruff/mypy config
- [ ] Add `check_platform_support_matrix.py` — verify INSTALL.md platforms have CI coverage
- [ ] Add `check_python_version_parity.py` — verify CI tests lowest declared Python version
- [ ] Add `check_perf_baselines.py` — verify baseline files exist and haven't aged
- [x] Extend `check_rust_security_footguns.py` — sign-unsafe syscall casts, PID wrap-cast detection, and `unreachable!()` hot-path detection landed
- [x] Extend `check_rust_best_practices.py` — dropped channel sends, suspicious `OpenOptions::create(true)` chains, float-literal equality detection, non-atomic persistent TOML write detection, custom-parser detection, and detached-thread spawn detection landed
- [x] Add `check_python_broad_except.py` — fail newly added broad Python exception handlers (including bare `except:`) unless a nearby `broad-except: allow reason=...` comment documents why fail-soft behavior is intentional; keep the guard diff-aware so existing broad-except debt does not block unrelated local work
- [x] Add `check_python_subprocess_policy.py` — fail repo-owned Python tooling/app code when `subprocess.run(...)` omits an explicit `check=` keyword, remediate the remaining production call sites in the same slice, and wire the guard into AI-guard plus shared bundle/workflow lanes
- [x] Extend `check_python_global_mutable.py` — detect non-regressive growth of mutable default arguments (`[]`, `{}`, `set()`, `list()`, etc.) in addition to `global` keyword usage so Python mutable-state mistakes are blocked by default lanes
- [x] Add `devctl report --python-guard-backlog` utility slice — aggregate `check_python_dict_schema.py`, `check_python_global_mutable.py`, `check_parameter_count.py`, `check_nesting_depth.py`, `check_god_class.py`, `check_python_broad_except.py`, and `check_python_subprocess_policy.py` into one ranked hotspot report for staged debt burn-down before stricter gate promotion
- [x] Continue Phase-14 Rust guard expansion by extending `check_rust_best_practices.py` with dropped channel-send result detection and `unwrap()` on `join`/`recv` paths, then update the guard docs/tests in the same slice
- [x] Add `check_guard_enforcement_inventory.py` — verify cataloged check scripts still have a real bundle/workflow enforcement lane or an explicit exemption. Initial policy decisions:
  - count direct raw invocations from `bundle_registry.py` and workflow `run:` blocks
  - allow explicit indirect owner mappings only for current lane-owner commands: `devctl docs-check` owns its strict-tooling check family and `devctl check` owns the current AI-guard pack
  - keep helper-only/manual-only/report-only exceptions explicit in the guard (`bootstrap`, advisory `check_duplication_audit.py`, duplication-audit support module, `rustsec_policy`, `mutation_score`, and the still-red `check_test_coverage_parity.py` backlog)
  - close the immediately green catalog gaps in the same slice by promoting `check_bundle_registry_dry.py` and `check_repo_url_parity.py` into shared governance bundles/workflows instead of merely reporting them
- [x] Add `check_serde_compatibility.py` — flag tagged enums without explicit fallback or documented strictness policy
- [x] Add `check_architecture_surface_sync.py` — new guard for the new rule domain "path-to-authority wiring" so changed/untracked surfaces fail when they are not wired into the right docs/governance/config surfaces. MVP decisions validated by the 2026-03-08 external-tool comparison:
  - scope only NEW files (`git diff --name-only --diff-filter=A` plus `git ls-files --others --exclude-standard`), not all changed files, to avoid false-positive fatigue and baseline drift
  - implement as a declarative `SURFACE_ZONES` registry with per-zone severity and allowlist support, not hard-coded branching logic
  - first zones:
    - `active-plan`: new `dev/active/*.md` files must be registered in `dev/active/INDEX.md`, mirrored in `dev/active/MASTER_PLAN.md`, and linked from discovery docs when required
    - `check-script`: new `dev/scripts/checks/check_*.py` entrypoints must be registered in `script_catalog.py`, referenced by at least one bundle, and wired into the matching workflow surface when they are intended to gate CI
    - `devctl-command`: new `dev/scripts/devctl/commands/*.py` files (excluding helper/test-only modules) must be reachable from parser-builder registration and the maintainer command docs
    - `app-surface`: new `app/**` surfaces must be mentioned by an owning active plan doc (initially any explicit owning plan mention is acceptable; tighten to plan-specific authority only if needed after MVP)
    - `workflow`: new `.github/workflows/*.yml` files must be reflected in `.github/workflows/README.md`
  - explicit exclusions: test files, helper-only modules, gitignored files, and temporary caches should not trigger zone failures
  - performance budget: filter candidate paths by zone globs before reading authority docs and keep the guard under a `<5s` CI budget on normal repo-sized diffs
  - git assumptions to document: `git ls-files --others --exclude-standard` is correct for this repo and intentionally excludes ignored files; note that it does not recurse into submodules, which is a non-issue because this repo currently has no submodules
- [ ] Close the guard false-failure backlog cluster from `issues.md`:
      `ISS-067` stays owned here until guard infrastructure distinguishes
      malformed input/infrastructure errors from real policy violations and
      emits structured failure modes instead of letting internal JSON decode
      failures masquerade as ordinary mutation-score findings.
  - required integration steps belong in the checklist, not tribal memory: `script_catalog.py`, `_SHARED_GOVERNANCE_CHECKS`, `tooling_control_plane.yml`, `release_preflight.yml`, AGENTS onboarding/docs, and a closing `check_bundle_workflow_parity.py` verification step
- [x] Extend `check_duplication_audit.py` + `check_duplication_audit_support.py` with advisory `--check-shared-logic` heuristics instead of creating a separate `check_shared_logic_candidates.py` script. This is a refinement of the duplication domain, not a new architecture-rule domain. MVP decisions:
  - keep default severity advisory / report-only; do not make semantic/shared-logic heuristics blocking until false-positive behavior is well understood
  - first heuristics:
    - `new-file-vs-shared-helper`: newly added Python/Rust/tooling files with high line-overlap against known shared-helper surfaces
    - `orchestration-pattern-clone`: newly added Python command-runner files with high project-import overlap against existing command-runner scaffolds
  - exclude stdlib-only import overlap from the orchestration heuristic and keep Rust semantic-duplication ambitions out of MVP
  - document decision criteria in the plan: use the existing duplication-audit/reporting surfaces and avoid new script/catalog/workflow boilerplate for this check family
- [ ] Add explicit Phase-14 implementation checklist items for the research-validated gaps:
  - `SURFACE_SYNC_ALLOWLIST` / exception path from day one
  - explicit test-file exclusion policy for `dev/scripts/devctl/tests/test_*.py` and similar helper/test surfaces
  - AGENTS onboarding/update step for the new architecture-surface guard
  - app-zone authority-spec clarification (what counts as the owning plan mention)
  - final `check_bundle_workflow_parity.py` verification after all wiring changes land
- [ ] Run verification: full `bundle.tooling` pass
- [ ] Promote Python clean-code guards from backlog utility to stricter default-lane gating after hotspot debt drops below agreed thresholds (track via recurring `report --python-guard-backlog` evidence snapshots)

### Phase 15: Developer Docs IA Reorganization + Active Directory Hygiene (Round 4) (new)
- [x] Create `dev/guides/` and move durable maintainer guides (`ARCHITECTURE`, `DEVELOPMENT`, `DEVCTL_AUTOGUIDE`, `MCP_DEVCTL_ALIGNMENT`) into canonical guide paths (completed with temporary bridge files at legacy `dev/*.md` paths for one migration cycle)
- [x] Reduce duplicate index drift: make `dev/README.md` canonical; convert `DEV_INDEX.md` into a thin bridge page (completed: `DEV_INDEX.md` is now a compact bridge to canonical `dev/README.md`)
- [x] Resolve `dev/BACKLOG.md` governance gap (completed: moved canonical local backlog to `dev/deferred/LOCAL_BACKLOG.md` with explicit reference-only contract and retained `dev/BACKLOG.md` bridge file)
- [x] Clean `dev/active/` intent boundaries (completed: moved generated/reference ownership to canonical `dev/reports/audits/RUST_AUDIT_FINDINGS.md` + `dev/deferred/phase2.md`, with explicit bridge pointers retained in `dev/active/INDEX.md`)
- [x] Consolidate docs path-policy constants (`docs_check_constants.py` + `docs_check_policy.py`) into single-source ownership before path move rollout (completed by making `docs_check_policy.py` canonical and converting `docs_check_constants.py` into a compatibility re-export shim with regression coverage in `test_docs_check_constants.py`)
- [x] Update all coupled path surfaces listed in Round 4 compatibility map in one atomic change set (completed for guide-path migration surfaces: docs policy constants, router exact-path classification, tooling-control-plane workflow path filters, and active governance entrypoint links)
- [ ] Retire temporary bridge entrypoints once the compatibility cycle truly
      closes: `dev/ARCHITECTURE.md` and `dev/BACKLOG.md` should not remain
      permanent duplicate docs after canonical-path references are cleaned up.
- [ ] Audit `dev/` for duplicate or confusing entrypoints after the guide-path
      migration and collapse each concern to one clearly named canonical owner
      plus, at most, a short-lived bridge with an explicit removal trigger.
- [ ] Keep the new desktop wrapper from recreating the same problem: clean up
      `app/operator_console/` package layout as part of the broader developer
      information-architecture pass instead of letting a second messy subtree
      grow next to `devctl`.
- [x] Run verification: `bundle.tooling` + `python3 dev/scripts/devctl.py check-router --since-ref origin/develop --format md` + `python3 dev/scripts/checks/check_release_version_parity.py` (rerun 2026-03-06 after docs-policy, index-authority, and guide-path migration slices; all gates green)

### Phase 16: Consolidated Audit Execution Kickoff (2026-03-06)
- [x] Treat `dev/active/pre_release_architecture_audit.md` as the sole execution checklist authority for this lane
- [x] Keep all audit findings and remediation sequencing in this document (no split active-doc audit authority)
- [x] Correct stale/contradictory audit statements before implementation batches begin
- [x] Tag uncertain findings as "investigate-first" (for example: `Arc::clone` in `rust/src/voice.rs`, shared join helper extraction scope)
- [x] Define import-fallback migration contract before removing `ModuleNotFoundError` fallback paths
- [x] Run verification: `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_multi_agent_sync.py`, and `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- [x] Start implementation: remove `env::set_var` usage from `main.rs` by wiring runtime theme/backend overrides (`set_runtime_theme_file_override`, `set_runtime_backend_label`) and validate with `cd rust && cargo test --bin voiceterm`
- [x] Retire `audit-scaffold` legacy output-root compatibility (`dev/active/`) so generated remediation artifacts are constrained to canonical `dev/reports/audits/`
- [x] Retire `docs-check` legacy tooling-doc alias acceptance for `dev/DEVELOPMENT.md` and require canonical `dev/guides/DEVELOPMENT.md`
- [x] Fix strict-tooling false negatives for canonical docs in untracked directories by collecting git status with `--untracked-files=all`
- [x] Continue MP-265 runtime decomposition by splitting writer message routing (`writer/state/dispatch.rs`) from PTY-heavy output handling (`writer/state/dispatch_pty.rs`) and remove temporary dispatch/redraw/prompt exceptions after functions fell below default limits
- [x] Split current `dev_command` god-file hotspots (`broker`, `review_artifact`) into focused modules and tighten the shape guard for the whole `rust/src/bin/voiceterm/dev_command/` lane with prefix-based budgets instead of one-file whack-a-mole overrides
- [ ] Run a fresh maintainability census before the next cleanup slice and map
      the biggest hotspots to their owning MPs: current intake includes
      `app/operator_console/ui.py`, `app/operator_console/bridge_model.py`,
      `app/operator_console/theme.py`, `rust/src/bin/voiceterm/event_loop.rs`,
      `rust/src/bin/voiceterm/main.rs`,
      `rust/src/bin/voiceterm/dev_command/{broker,review_artifact,command_state}.rs`,
      `rust/src/bin/voiceterm/dev_panel/{review_surface,cockpit_page/mod}.rs`,
      and the flat `dev/scripts/devctl/commands/` package.

---

## Progress Log

| Date | Phase | Action | Result |
|------|-------|--------|--------|
| 2026-03-12 | Phase 15 (execution) | Finished the `dev/scripts` package-layout cleanup by moving repo-owned references from deleted root Python wrappers to canonical package entrypoints (`mutation/`, `coderabbit/`, `workflow_bridge/`, `rust_tools/`, `badges/`, `artifacts/`), extending `devctl path-audit/path-rewrite` so stale script-path references are enforced automatically, and tightening directory READMEs so `checks/` and the package roots describe intentional entrypoint vs helper structure. In the same slice, the remaining router/docs portability leak was reduced by moving `check-router` lane/risk-addon rules and `docs-check` doc-governance path lists into `dev/config/devctl_repo_policy.json`, and portable onboarding was simplified by teaching `governance-bootstrap` to write a starter repo policy plus exporting AI-friendly setup templates. Another repo can now get to a first-run policy/bootstrap path without patching devctl command code. A portability review still confirmed that the reusable guard/probe engine is ahead of the higher-level workflow helpers: Ralph, mutation, and process hygiene remain VoiceTerm-specific follow-up extraction work. | bounded slice complete: targeted `py_compile` + `pytest` for router/docs/bootstrap policy surfaces are green, repo-governance behavior now lives in policy instead of hidden Python constants, and exported templates plus starter-policy generation make cross-repo adoption materially simpler; broader repo-agnostic control-plane extraction remains open tracked follow-up |
| 2026-03-10 | Phase 16 (execution) | Closed a bounded daemon/runtime correctness slice plus the next documentation-IA cleanup. The daemon session registry now prunes exited handles before list/status/send paths, agent drivers stay quiescent behind a startup gate until `agent_spawned` has been recorded/broadcast, targeted daemon regression coverage landed, and the advanced app docs (`app/README.md`, `app/operator_console/README.md`, `app/ios/README.md`) now use the same beginner-first "run vs extend" navigation split as the top-level docs. In the same slice, review-channel status now supports typed heartbeat self-heal and host-process hygiene no longer self-reports same-session pytest/check helper subtrees as leaked repo tooling. | complete for this bounded slice: `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm daemon:: -- --nocapture`, `python3 -m pytest dev/scripts/devctl/tests/test_review_channel.py dev/scripts/devctl/tests/test_process_sweep.py dev/scripts/devctl/tests/test_hygiene.py -q --tb=short`, `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md --refresh-bridge-heartbeat-if-stale`, `python3 dev/scripts/devctl.py hygiene --strict-warnings --format md`, `python3 dev/scripts/devctl.py docs-check --user-facing`, and `markdownlint ... app/README.md app/ios/README.md app/operator_console/README.md` are green on the current working tree |
| 2026-03-09 | Phase 14 (execution) | Extended `check_python_global_mutable.py` after a manual AST audit pass to cover mutable default argument growth, closing a guard gap where Python mutable-state bugs could bypass policy if no `global` keyword was used | complete for this bounded slice: helper detection for mutable defaults landed (`[]`, `{}`, `set()/list()/dict()/defaultdict()/deque()`), targeted guard/report tests pass, and current repo-owned target roots remain clean for this pattern while future regressions are now blocked |
| 2026-03-09 | Phase 14 (execution) | Hardened `check_python_broad_except.py` to treat bare `except:` handlers as broad-except violations, then remediated newly added fail-soft sites with explicit rationale comments in devctl autonomy/data-science helper modules | complete for this bounded slice: targeted guard tests pass, broad-except guard now runs green on the current working tree with documented fail-soft intent, and optional plotting/telemetry paths no longer rely on undocumented broad handlers |
| 2026-03-09 | Phase 14 (execution) | Added `devctl report --python-guard-backlog` as a new utility-level guard surface that aggregates dict-schema/global-mutable/parameter-count/nesting-depth/god-class plus broad-except/subprocess-policy outputs into one ranked hotspot digest for maintainability planning | complete for this bounded slice: new `python_guard_report.py` collector/renderer landed, `report` parser/build/report/render paths now expose the new section and top-N control, targeted test coverage is green (`test_report.py`, `test_python_guard_report.py`, `test_status_report_parallel.py`), and operator docs now include ready-to-run commands for commit-range hotspot audits |
| 2026-03-09 | Phase 14 (execution) | Hardened default local guard enforcement by enabling AI-guard scripts in `devctl check --profile quick` and its alias `fast`, then updated profile tests and command docs so post-test quick follow-up no longer skips structural/code-quality checks by default | complete for this slice: targeted `test_check.py` profile tests and guard-run-based quick paths stay green, and `AGENTS.md` + `dev/scripts/README.md` + `dev/guides/DEVELOPMENT.md` now document quick/fast as guard-on local lanes rather than fmt/clippy-only shortcuts |
| 2026-03-09 | Phase 16 (execution) | Continued MP-265 Rust overlay maintainability cleanup by extracting review-surface three-lane helpers into `rust/src/bin/voiceterm/dev_panel/review_surface_lanes.rs` and moving Control-page section builders into `rust/src/bin/voiceterm/dev_panel/cockpit_page/control_sections.rs`, then rewiring both parent modules to consume the focused helper surfaces | complete for this slice: hotspot files dropped to `review_surface.rs` `657` lines (from `858`) and `cockpit_page/mod.rs` `495` lines (from `766`) with behavior preserved; guarded runtime validation is green (`python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm dev_panel::`, including post-run quick hygiene) |
| 2026-03-09 | Phase 14 (execution) | Added `check_guard_enforcement_inventory.py` so cataloged check scripts now fail when they lose all real bundle/workflow enforcement lanes without an explicit exemption; promoted `check_bundle_registry_dry.py` and `check_repo_url_parity.py` into shared governance lanes in the same slice | complete for the initial inventory contract: targeted unit coverage passes, tooling/release workflows now execute the two previously green-but-unenforced guards, `docs-check` is modeled as the current owner of `check_markdown_metadata_header.py`, and `check_test_coverage_parity.py` stays an explicit advisory backlog exemption until the current untested-check debt is burned down |
| 2026-03-09 | Phase 14 (execution) | Extended `check_rust_security_footguns.py` with sign-unsafe syscall return-cast detection so changed non-test Rust files now fail when `libc::read/write/recv/send/...` results are cast to unsigned types like `usize` without an explicit non-negative guard first | partial completion for checklist item: targeted unit coverage passes and the working-tree guard remains green on the current diff; the remaining planned follow-up in this checklist item is unreachable-hot-path detection, which stays deferred instead of being silently implied complete |
| 2026-03-09 | Phase 14 (execution) | Extended `check_rust_security_footguns.py` again with PID wrap-cast detection so changed non-test Rust files now fail when process identifiers are narrowed via `child.id() as i32` or `libc::getpid() as i32` instead of using checked conversions or typed PID paths | partial completion for checklist item: targeted unit coverage passes, the working-tree guard remains green on the current diff, and the remaining planned follow-up in this checklist item stays explicit (unreachable-hot-path detection is still pending) |
| 2026-03-09 | Phase 14 (execution) | Extended `check_rust_security_footguns.py` with `unreachable!()` hot-path detection so changed non-test Rust runtime hot-path files now fail when they add `unreachable!()` assumptions in `rust/src/bin/voiceterm/**`, `rust/src/audio/**`, or `rust/src/ipc/**` | complete for the currently planned security-footgun checklist item: targeted unit coverage passes and the working-tree guard remains green on the current diff |
| 2026-03-09 | Phase 14 (execution) | Extended `check_rust_best_practices.py` with suspicious `OpenOptions::new().create(true)` detection so changed non-test Rust files now fail when overwrite/create semantics are left implicit instead of being made explicit with `append(true)`, `truncate(...)`, or `create_new(true)` | partial completion for checklist item: targeted unit coverage passes, the working-tree guard remains green on the current diff, and the remaining planned follow-up in this checklist item stays explicit (`custom parsers`, float-comparison policy, and non-atomic persistent TOML writes were still pending at this point) |
| 2026-03-09 | Phase 14 (execution) | Extended `check_rust_best_practices.py` with direct float-literal equality/inequality detection so changed non-test Rust files now fail when runtime code adds `==` / `!=` comparisons against float literals instead of using an epsilon-style comparison | partial completion for checklist item: targeted unit coverage passes, the current working-tree guard remains green on the current diff, and the remaining planned follow-up in this checklist item stays explicit (`custom parsers` and non-atomic persistent TOML writes were still pending at this point) |
| 2026-03-09 | Phase 14 (execution) | Extended `check_rust_best_practices.py` with non-atomic persistent TOML write detection so changed non-test Rust files now fail when app-owned `~/.config/voiceterm/**.toml` persistence paths keep using direct overwrite helpers (`fs::write`, `File::create`, truncate-open) instead of a temp-file swap | partial completion for checklist item: targeted unit coverage passes, the current working-tree guard remains green on the current diff, and the remaining planned follow-up in this checklist item stays explicit (`custom parsers` only) |
| 2026-03-09 | Phase 14 (execution) | Extended `check_rust_best_practices.py` with custom persistent TOML parser detection so changed non-test Rust config/state readers now fail when they add hand-rolled parse functions (`split_once('=')`, `contents.lines()`, `trim_matches('\"')`, `strip_prefix(...)`) instead of using the already-available `toml` crate | complete for the currently planned best-practices checklist item: targeted unit coverage passes and the working-tree guard remains green on the current diff |
| 2026-03-09 | Phase 14 (execution) | Added `check_python_broad_except.py` so newly added `except Exception` / `except BaseException` handlers in repo-owned Python tooling and Operator Console code now require a nearby `broad-except: allow reason=...` comment; kept the guard diff-aware and line-added scoped so existing broad-except debt in unrelated dirty files does not block unrelated local work | complete for the initial broad-except contract: targeted unit coverage passes, AI-guard now forwards `--since-ref/--head-ref` to the new check, and tooling/release workflows execute the raw diff-scoped guard directly |
| 2026-03-09 | Phase 14 (execution) | Added `check_python_subprocess_policy.py` so repo-owned Python tooling and Operator Console code now fail when `subprocess.run(...)` omits an explicit `check=` keyword; remediated the remaining production call sites in `check_review_channel_bridge.py`, `release_guard.py`, `review_channel.py`, `mutants_runner.py`, and `repo_state.py` in the same slice | complete for the initial subprocess-policy contract: targeted unit coverage passes, the working-tree guard remains green on the current diff, AI-guard now includes the policy with `--since-ref/--head-ref` forwarding, and tooling/release workflows execute the raw guard directly |
| 2026-03-09 | Phase 14 (execution) | Added `check_serde_compatibility.py` so changed non-test Rust files now fail when they introduce internally or adjacently tagged `Deserialize` enums without either a `#[serde(other)]` fallback variant or a nearby `serde-compat: allow reason=...` comment documenting intentional fail-closed behavior | complete for the initial serde-compatibility contract: targeted unit coverage passes, AI-guard forwards `--since-ref/--head-ref` to the new guard, bundle/workflow lanes execute it, and `audit-scaffold` now includes the guard in Rust remediation output |
| 2026-03-09 | Phase 14 (execution) | Extended `check_duplication_audit.py` with advisory `--check-shared-logic` heuristics for newly added Python/tooling files so the existing duplication-audit surface can flag helper-overlap and command-scaffold clones without a second standalone scanner | complete for MVP: `new-file-vs-shared-helper` and `orchestration-pattern-clone` now run in warning-only mode over explicit paths or new-file git diffs, Rust semantic duplication remains intentionally out of scope for this tranche, and targeted unit coverage plus docs updates landed in the same slice |
| 2026-03-09 | Phase 14 (execution) | Added `check_architecture_surface_sync.py` as the missing path-to-authority guard for newly added active-plan docs, check scripts, devctl command entrypoints, app surfaces, and workflow files; wired it into the canonical script catalog, shared governance bundles, tooling/release workflows, and maintainer docs in the same slice | complete for MVP: targeted unit coverage passes, the bundle/workflow/doc surfaces now all mention the new guard, and the guard supports both diff-range mode (`--since-ref/--head-ref`) and targeted local verification (`--paths`) so the repo catches "new file, forgot the authority wiring" regressions before they scale |
| 2026-03-09 | Phase 16 (execution) | Continued the `devctl` maintainability cleanup after the initial helper/parsers pass: split `collect_dev_log_summary()` into session/event helper stages, reduced `audit_scripts()` to a coordinator plus inventory/message helpers, extracted per-entry evaluation from `publication_sync.py`, and split `dev/scripts/devctl/triage/support.py` markdown rendering into section helpers while keeping outputs stable | complete for slice: targeted tests pass for `test_collect_dev_logs`, `test_status_report_parallel`, `test_hygiene`, `test_publication_sync`, `test_check_publication_sync`, and `test_triage`, so the newly modularized report/triage/hygiene/publication paths stay behaviorally aligned |
| 2026-03-09 | Phase 16 (execution) | Cleaned the new `devctl` maintainability tranche captured by the architecture audit: extracted shared path/JSON/output helpers into `dev/scripts/devctl/common.py`, removed duplicate repo-relative/UTC helpers across review/publication/autonomy slices, decomposed the transitional review-channel prompt/command/parsers into smaller helpers/builders, refactored `status_report.py` into section appenders, and reduced new-test duplication with shared loader fixtures plus command-specific helper cleanup in `test_check.py`, `test_ship.py`, and the new review/process/publication slices | complete for slice: targeted tooling tests pass (`test_bundle_registry`, `test_check_bundle_workflow_parity`, `test_common`, `test_check`, `test_ship`, `test_review_channel`, `test_process_{sweep,watch,audit,cleanup}`, `test_guard_run`, `test_function_duplication_guard`, `test_publication_sync`, `test_check_publication_sync`, `test_clippy_pedantic`, `test_mobile_status`, `test_status_report_parallel`, `test_audit_scaffold`), and `bundle_registry.py` now composes post-push guard checks from the canonical shared list instead of drifting via manual expansion |
| 2026-03-09 | Phase 16 (execution) | Collapsed the repeated `write_output`/`pipe_output` command tail across the `devctl` command surface onto the shared `emit_output()` helper, extending the helper to support injected writer/piper callbacks plus optional secondary JSON outputs so existing command tests and JSON sidecar report flows stayed stable | complete for slice: all touched command modules except `mcp.py` now use the shared emitter, targeted compile/test packs pass across status/report/process/security/hygiene/publication/triage/orchestrate/check/sync/release-gates/mobile/phone/controller/autonomy/mutation/loop/import/docs/failure-cleanup slices, and the only remaining tail outlier is the multi-shape `mcp.py` dispatcher |
| 2026-03-09 | Phase 16 (execution) | Finished the follow-up `devctl` cleanup after the output-tail sweep: moved the remaining `mcp.py` output branches onto the shared emitter, split `common.py` into a slimmer compatibility/runtime-runner module plus `common_io.py`, decomposed `cli_parser/builders_ops.py` into parser-family modules, split `dev/scripts/devctl/review_channel/parser.py` into argument-group helpers, extracted triage bundle writing into `dev/scripts/devctl/triage/bundle.py`, and trimmed the remaining over-limit `security`, `triage`, `autonomy_benchmark`, and `autonomy_swarm` command flows into smaller helpers | partial completion for maintainability census: targeted tests and governance checks stay green, `check_code_shape` dropped from 40 to 34 violations and the devctl-specific remaining debt is now concentrated in `collect.py`, the review-channel files, `process_sweep_{core,scans}.py`, and `rust_audit_report.py` instead of the broad command-surface boilerplate that kicked off this tranche |
| 2026-03-09 | Phase 16 (execution) | Continued the maintainability census with the next smallest devctl hotspots: extracted guarded Dev Mode session summarization into `collect_dev_logs.py`, moved process path/command predicates into `process_sweep_matching.py`, and moved scope-specific process matchers into `process_sweep_scope_matchers.py` so `collect.py`, `process_sweep_core.py`, and `process_sweep_scans.py` all fall back under the active shape budget without changing the public `process_sweep.py` surface | complete for slice: targeted `py_compile` and process-sweep/status-report test packs pass, `check_code_shape` dropped again from 34 to 31 violations, and the remaining devctl-specific shape debt is now limited to `commands/review_channel.py`, `review_channel*.py`, and `rust_audit_report.py` while `check_review_channel_bridge.py` stays blocked only by the pre-existing untracked bridge files `bridge.md` and `dev/active/review_channel.md` |
| 2026-03-09 | Phase 16 (execution) | Closed the remaining working-tree code-shape debt for this tooling tranche by extracting the function-exception catalog into `code_shape_function_exceptions.py`, moving shared shape dataclasses into `code_shape_shared.py`, reducing `check_bundle_workflow_parity.py::build_report`, reducing `check_rust_best_practices.py::main`, and moving shared Start Swarm widget updates into `app/operator_console/views/swarm_status_widgets.py` so `home_workspace.py` drops back under its explicit path budget | complete for slice: `check_code_shape.py --format md` is now green on the dirty working tree, the temporary function exceptions for `build_report`, `main`, and `HomeWorkspace.__init__` were removed instead of renewed, and targeted check/operator-console test packs stay green after the policy split |
| 2026-03-09 | Phase 14 (execution) | Extended `check_rust_best_practices.py` again with an `--absolute` full-tree audit mode so Rust best-practice debt is visible even when hotspot files are not part of the current diff | complete for slice: unit coverage passes, maintainer docs note the new mode, and the absolute audit now exposes a 32-file backlog led by suppressed send results, `Result<_, String>` surfaces, and undocumented unsafe blocks instead of hiding that debt behind changed-file-only scanning |
| 2026-03-09 | Phase 14 (execution) | Extended `check_rust_best_practices.py` to detect suppressed channel-send results and `unwrap()` on `join`/`recv` paths, then updated the checker docs/tests so this new Rust-risk tranche is explicit in repo governance | complete for slice: dedicated unit coverage passes, AGENTS/dev-scripts docs now describe the broader guard contract, and the working-tree audit now surfaces concrete follow-up debt in `dev_command/broker/mod.rs` (`let _ = update_tx.send(...)`) plus existing reason-less allow growth instead of silently allowing those patterns |
| 2026-03-09 | Phase 14 (execution) | Extended `check_rust_best_practices.py` again with a detached-thread metric for bare `thread::spawn(...)` statements that drop their `JoinHandle` without a nearby `detached-thread: allow reason=...` note, then tightened the heuristic so `JoinHandle`-returning helper functions are not false-positive debt and cleaned the remaining dirty-tree `UserInputActivity` send site in `event_loop.rs` | complete for slice: `python3 -m pytest dev/scripts/devctl/tests/test_check_rust_best_practices.py -q --tb=short` passes, `python3 dev/scripts/checks/check_rust_best_practices.py --format md` is green on the current dirty tree, and the absolute audit drops further to 19 remaining violations with `dropped_send_results`, `dropped_emit_results`, and `detached_thread_spawns` all at zero |
| 2026-03-09 | Phase 14 (execution) | Burned down the remaining absolute Rust best-practices backlog to zero by converting the last `Result<_, String>` hotspots to typed errors, replacing the resampler’s float-literal equality branch with an epsilon comparison, documenting the remaining unsafe/`allow(...)` sites, teaching `check_rust_best_practices.py` to accept `SAFETY:` comments as the first line inside `unsafe { ... }` blocks, and moving onboarding/config/theme-export persistence onto shared atomic text writes plus `toml` parsing/serialization | complete for slice: targeted Rust module tests pass for `persistent_config`, `onboarding`, `theme_studio::export_page`, and the new `persistence_io` helper; `python3 -m pytest dev/scripts/devctl/tests/test_check_rust_best_practices.py -q --tb=short` passes with the new inside-block safety regression coverage; `python3 dev/scripts/checks/check_rust_best_practices.py --format md` stays green on the working tree; and `python3 dev/scripts/checks/check_rust_best_practices.py --absolute --format md` is now fully green with `violations: 0` |
| 2026-03-09 | Phase 14 (execution) | Added `check_rust_compiler_warnings.py` as a changed-file rustc warning guard that runs a no-run JSON `cargo test` compile, filters warnings to repo-owned changed `.rs` paths, and fails on warning-only debt that Clippy/best-practices guards do not see; then promoted it into the canonical bundle/workflow surfaces and fixed the first real hit (`review_artifact/state.rs::load_from_content` dead-code warning) | complete for slice: the new unit coverage passes, `check_rust_compiler_warnings.py --format md` is green on the dirty tree after the review-artifact fix, `check_guard_enforcement_inventory.py` / `check_architecture_surface_sync.py` stay green once the new guard is wired into `script_catalog.py`, `bundle_registry.py`, `rust_ci.yml`, `tooling_control_plane.yml`, and `release_preflight.yml`, and bundle/render parity stays green after the AGENTS/README updates |
| 2026-03-09 | Phase 16 (execution) | Completed the `dev_command` hotspot cleanup after operator review flagged `review_artifact.rs` and `broker.rs` as medium-sized god modules; tightened the shape guard so the whole `rust/src/bin/voiceterm/dev_command/` lane now uses a stricter prefix budget instead of relying on permissive Rust defaults | complete for slice: `review_artifact` split into `artifact/state/format/tab` modules, `broker` split into `completion/path/summary` modules, `check_code_shape` now supports prefix-based hotspot policies with a `dev_command/` budget plus an explicit `command_state.rs` exception, and the follow-up hotspot census remains open for `main`, `event_loop`, `dev_panel/review_surface`, `dev_panel/cockpit_page`, and `input_dispatch/overlay` |
| 2026-03-08 | Phase 15 + Phase 16 (intake) | Captured the next maintainability/IA tranche from operator feedback: bridge-doc retirement must stay explicit (`dev/ARCHITECTURE.md`, `dev/BACKLOG.md`), AGENTS trimming still needs real execution, the PyQt Operator Console needs package cleanup, and the next runtime/tooling hotspot census should prioritize `event_loop`, `main`, `dev_command`, `dev_panel`, and the flat `devctl/commands` surface | planned: Phase 15 and Phase 16 checklists now carry the follow-up work instead of leaving it as chat-only feedback |
| 2026-03-08 | Phase 16 (execution) | Extended the advisory pedantic lane into the existing `report`/`triage` architecture instead of creating a second lint-triage path | complete: `check --profile pedantic` now emits structured artifacts under `dev/reports/check/`, `report --pedantic` and `triage --pedantic` ingest those artifacts through the shared project snapshot, `dev/config/clippy/pedantic_policy.json` records promote/defer/review policy, and unit coverage locks the collector/parser/report/triage seams |
| 2026-03-08 | Phase 14 (research validation) | Validated the architecture-surface-sync and shared-logic guard design against primary tool docs and folded the resulting design decisions into the deferred guard plan | complete: Phase 14 now explicitly chooses one new guard (`check_architecture_surface_sync.py`) plus one extension of the existing duplication audit (`--check-shared-logic`), records the 5-zone MVP, advisory-severity rule for shared-logic heuristics, performance/allowlist/test-exclusion constraints, and the missing wiring/checklist steps before implementation begins |
| 2026-03-08 | Phase 16 (execution) | Added an explicit advisory `devctl check --profile pedantic` lane and maintainer-doc guidance so pedantic Clippy is opt-in for intentional lint sweeps instead of a release blocker | complete: check-profile wiring, parser/list surfaces, unit coverage, and maintainer docs now make pedantic usage explicit without changing bundle or workflow requirements |
| 2026-03-08 | Phase 14 (backlog intake) | Captured the next architecture-governance guard tranche from active operator feedback: add an architecture-surface sync guard for changed/untracked paths plus a new-file duplicate/shared-logic guard so AI/dev runs fail earlier when new surfaces are not wired into repo authority or when shared utility logic is being copied instead of extended | planned: keep this post-release under MP-347 Phase 14, with exact first-target coverage defined in the execution checklist before implementation begins |
| 2026-03-07 | Phase 16 (execution) | Followed up Theme Studio maintainability cleanup by extracting shared vertical-arrow navigation and runtime-override cycle helpers in `theme_studio_input.rs` so page handlers no longer duplicate up/down dispatch and style-cycle wiring | complete: `cd rust && cargo fmt`, `cd rust && cargo test --bin voiceterm theme_studio -- --nocapture` (`68` tests passed), `cd rust && cargo test --bin voiceterm writer::state:: -- --nocapture` (`135` tests passed), plus required process sweep `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` |
| 2026-03-07 | Phase 16 (execution) | Continued maintainability cleanup in Theme scope by refactoring `event_loop/input_dispatch/overlay/theme_studio_input.rs` into page-scoped byte handlers (global/home/colors/borders/components/preview/export) and extracting runtime-style adjustment routing into focused helpers | complete: `cd rust && cargo fmt`, `cd rust && cargo test --bin voiceterm theme_studio -- --nocapture` (`68` tests passed), required process sweep `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel`, full runtime gate `python3 dev/scripts/devctl.py check --profile ci` (`1661` tests passed), plus `docs-check --user-facing`, `hygiene`, active-plan sync, CLI parity, screenshot integrity, and markdownlint all green |
| 2026-03-06 | Phase 16 (execution) | Completed readability pass on Rust/Python comment and policy language (writer dispatch path + shape/complexity guard text), then reran full runtime CI profile after targeted rustfmt alignment | complete: `python3 dev/scripts/devctl.py check --profile ci` is green, comments are simpler in touched files, and governance docs checks remain green |
| 2026-03-06 | Phase 16 (execution) | Continued MP-265 writer-state cleanup by splitting message routing into `writer/state/dispatch.rs` and PTY-heavy output into `writer/state/dispatch_pty.rs`; removed temporary complexity exceptions for dispatch/redraw/prompt after re-checking function metrics | complete: `check_structural_complexity.py` now runs with `exceptions_defined=0`, `check_code_shape.py` is green, and `cargo test --bin voiceterm` passed (`1535` tests) |
| 2026-03-06 | Phase 15 (active-dir hygiene) | Revalidated backlog/active-boundary cleanup coupling updates with targeted checks (`test_audit_scaffold`, `docs-check --strict-tooling`, `hygiene --strict-warnings`, `check_active_plan_sync`, `check_multi_agent_sync`, `check_agents_contract`, `check_bundle_workflow_parity`, `check-router --since-ref origin/develop`, `check_release_version_parity`) | complete: all targeted verification gates passed after canonical-path migration updates (`dev/deferred/*`, `dev/reports/audits/*`) |
| 2026-03-06 | Phase 15 (active-dir hygiene) | Closed backlog-governance gap by moving canonical local backlog to `dev/deferred/LOCAL_BACKLOG.md`, keeping a bridge at `dev/BACKLOG.md`, and adding reference-only execution contract text | complete: local `LB-*` backlog tracking is now explicitly non-authoritative and decoupled from active `MASTER_PLAN` execution state |
| 2026-03-06 | Phase 15 (active-dir hygiene) | Closed active-intent boundary cleanup by moving canonical generated/reference surfaces to `dev/reports/audits/RUST_AUDIT_FINDINGS.md` and `dev/deferred/phase2.md`, then updating AGENTS/docs/workflow/index references | complete: `dev/active/` retains bridge pointers only, while canonical generated/reference ownership now lives outside active execution surfaces |
| 2026-03-06 | Phase 15 (active-dir hygiene) | Reran verification pack after guide-path migration coupling updates (`bundle.tooling`, `check-router --since-ref origin/develop`, `check_release_version_parity.py`) | complete: migration remains non-regressive across docs policy gates, workflow parity, and tooling control-plane checks |
| 2026-03-06 | Phase 15 (active-dir hygiene) | Completed guide-path migration (`dev/guides/`) for durable maintainer docs and added temporary bridge files at legacy `dev/*.md` paths | complete: canonical maintainer-guide ownership now lives under `dev/guides/` while existing links remain stable during transition |
| 2026-03-06 | Phase 15 (active-dir hygiene) | Updated all mapped guide-path coupling surfaces in one batch (docs-check policy constants, check-router tooling exact paths, tooling-control-plane workflow path filters, AGENTS/DEV_INDEX/dev README governance links, and related tests) | complete: migration blast radius controls from Round 4 compatibility map are now implemented for the guide-path rollout |
| 2026-03-06 | Phase 15 (active-dir hygiene) | Ran full verification pack after docs-path policy and index-authority updates (`bundle.tooling`, `check-router --since-ref origin/develop`, `check_release_version_parity.py`) | complete: all commands succeeded; no new guard violations introduced by Phase-15 slices |
| 2026-03-06 | Phase 15 (active-dir hygiene) | Reduced duplicate index drift by converting `DEV_INDEX.md` into a bridge page and explicitly marking `dev/README.md` as canonical | complete: one authoritative developer index remains (`dev/README.md`) while root discovery remains intact through the bridge |
| 2026-03-06 | Phase 15 (active-dir hygiene) | Consolidated docs-check path-policy ownership by keeping `docs_check_policy.py` as canonical and converting `docs_check_constants.py` into compatibility exports only | complete: path constants no longer have dual-maintenance drift risk; compatibility imports preserved and covered by `dev/scripts/devctl/tests/test_docs_check_constants.py` |
| 2026-03-06 | Phase 16 (execution) | Removed the stale structural-complexity exception for `writer/state/redraw.rs::maybe_redraw_status` after splitting redraw gating, geometry sync, pending-state apply, render, and commit helpers | complete: measured complexity is now below default policy (`score=13`, `branch_points=2`, `max_nesting_depth=2`) and `check_structural_complexity.py` now has only one active exception left |
| 2026-03-06 | Phase 16 (execution) | Removed the stale structural-complexity exception for `event_loop/prompt_occlusion.rs::feed_prompt_output_and_sync` after the detection split reduced the function below default guard thresholds | complete: measured complexity is now below default policy (`score=9`, `branch_points=7`, `max_nesting_depth=3`) and `check_structural_complexity.py` remains green with two active exceptions left |
| 2026-03-06 | Phase 16 (execution) | Retired `audit-scaffold` transition output-root compatibility by removing `dev/active/` output acceptance and keeping canonical `dev/reports/audits/` enforcement in parser/help text + tests | complete: output-root policy now enforces one canonical remediation artifact location and regression coverage stays green (`test_audit_scaffold`) |
| 2026-03-06 | Phase 16 (execution) | Retired `docs-check` bridge-alias acceptance for `dev/DEVELOPMENT.md` and required canonical `dev/guides/DEVELOPMENT.md`; updated docs-check tests to reject legacy-only updates | complete: strict-tooling governance now enforces canonical maintainer-doc ownership without legacy aliases |
| 2026-03-06 | Phase 16 (execution) | Fixed strict-tooling untracked-directory false negatives by collecting git status with `--untracked-files=all` in `collect_git_status` | complete: strict-tooling docs policy now detects canonical untracked files directly (`dev/guides/*`) while preserving existing commit-range behavior |
| 2026-03-06 | Phase 16 (execution) | Landed MP-265 shape-budget cleanup slice by extracting compact/minimal plus single-line status-line helpers and moving `theme/rule_profile.rs` inline tests into a submodule | complete for slice: `status_line/format.rs` 990 -> 657, `theme/rule_profile.rs` 922 -> 265, and both raised `PATH_POLICY_OVERRIDES` entries were removed |
| 2026-03-06 | Phase 15 (active-dir hygiene) | Registered raw multi-agent audit merge transcript at `dev/active/move.md` and linked it as supporting evidence | complete: transcript provenance retained in active-doc context while execution authority remains with this plan and `dev/active/MASTER_PLAN.md` |
| 2026-03-06 | Phase 16 (execution) | Completed governance sync and corrected audit-plan sequencing assumptions; started do-now remediation by replacing `main.rs` `env::set_var` flow with runtime overrides | complete for kickoff slice: active-plan gates green + `cargo test --bin voiceterm` green (`1526` passed) |
| 2026-03-06 | Phase 16 (kickoff) | Consolidated pre-release findings + execution authority into this single plan while adding explicit readability contract (simple comments, clear docstrings, easy-to-understand naming) | complete |
| 2026-03-06 | Phase 15 (intake) | Ran full docs-information-architecture and active-directory organization audit with path-coupling analysis | added Round 4 findings + target layout + compatibility map; execution now staged for migration implementation |
| 2026-03-05 | Phase 7 | Landed DevCtl guard hardening batch (5 new guards, 3 extended guards) | complete: verification pack is green (`596/596` tests); pre-release completion point reached with Phases 8-14 explicitly deferred post-release |
| 2026-03-05 | Phase 6 | Decomposed `check.py` into phase-oriented orchestration and added Python module naming convention docs | complete: `check.py` slim orchestrator + `check_phases.py` extracted; Phase 7 is the next execution scope |
| 2026-03-05 | Accuracy refresh | Revalidated stale audit claims against current repo state | Updated counts/claims (AGENTS lines, `_run_git` duplication, README existence, `check.py` run length, repo URL scope) |
| 2026-03-05 | Audit | Full 4-agent parallel audit completed | Findings documented above |
| 2026-03-05 | Backlog triage | Added Cursor+Claude plan-mode rendering anomaly with resize-recovery clue (`MP-349`) | Post-release scope captured with evidence requirements |
| 2026-03-05 | Audit round 2 | 4-agent deep dive: Rust errors, docs/config, Python quality, testing/release | 10 new findings added (items 11-20) |
| 2026-03-05 | Gap analysis | Analyzed why devctl guards missed all 17+ issues | 15 guard gaps identified, 7 new guards recommended, 3 root causes documented |
| 2026-03-05 | Audit round 3 | 6-agent parallel sweep: research, Rust deep, CI/CD, Python, DX+deps, cross-platform+perf | 15 new findings (items 21-35), 6 new execution phases (9-14) |

## Session Resume

- Current status: this plan remains active; start from the highest-priority
  open item in `## Execution Checklist` and the latest dated entry in
  `## Progress Log`.
- Next action: keep current-slice decisions and blockers in this file instead
  of chat-only notes, then update this section when the promoted slice
  changes.
- Context rule: treat `dev/active/MASTER_PLAN.md` as tracker authority and
  load only the local sections needed for the active checklist item.

## Audit Evidence

| Check | Date | Result |
|-------|------|--------|
| Phase-14 guard enforcement inventory | 2026-03-09 | Added `check_guard_enforcement_inventory.py` to reconcile `script_catalog.py` against real bundle/workflow enforcement lanes. The guard treats helper/manual/report-only scripts as explicit exemptions, recognizes the current `devctl docs-check` strict-tooling family and `devctl check` AI-guard pack as indirect owner surfaces, and promoted `check_bundle_registry_dry.py` plus `check_repo_url_parity.py` into shared governance bundles/workflows in the same slice. Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_guard_enforcement_inventory dev.scripts.devctl.tests.test_bundle_registry dev.scripts.devctl.tests.test_script_catalog` passes. Local evidence: `python3 dev/scripts/checks/check_guard_enforcement_inventory.py --format md`, `python3 dev/scripts/checks/check_bundle_registry_dry.py`, and `python3 dev/scripts/checks/check_repo_url_parity.py` all remain green on the current working tree. |
| Phase-14 Python broad-except rationale guard | 2026-03-09 | Added `check_python_broad_except.py` to flag newly added `except Exception` / `except BaseException` handlers unless a nearby `broad-except: allow reason=...` comment documents the fail-soft behavior. The guard is intentionally diff-aware and keyed to added handler lines so current unrelated broad-except debt in the dirty tree does not become accidental baseline policy. Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_python_broad_except dev.scripts.devctl.tests.test_check dev.scripts.devctl.tests.test_script_catalog` passes. Local evidence: `python3 dev/scripts/checks/check_python_broad_except.py --paths dev/scripts/checks/check_python_broad_except.py --format md` exits clean on the new guard file. |
| Phase-14 Python subprocess policy guard | 2026-03-09 | Added `check_python_subprocess_policy.py` to fail repo-owned Python tooling/app code when `subprocess.run(...)` omits an explicit `check=` keyword, matching Ruff `PLW1510` semantics while keeping enforcement repo-scoped (`dev/scripts/**`, `app/operator_console/**`) and test-excluded. The same slice made the remaining production call sites explicit (`check=False`) and wired the new guard through `devctl check` AI-guard plus shared bundle/workflow lanes. Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_python_subprocess_policy dev.scripts.devctl.tests.test_check dev.scripts.devctl.tests.test_bundle_registry dev.scripts.devctl.tests.test_script_catalog` passes. Local evidence: `python3 dev/scripts/checks/check_python_subprocess_policy.py --format md` remains green on the current working tree. |
| Phase-14 Rust security-footguns expansion | 2026-03-09 | Extended `check_rust_security_footguns.py` with sign-unsafe syscall-return cast detection for changed non-test Rust files. The guard now flags cases where `libc::read/write/recv/send/pread/pwrite` results are cast to unsigned integer types without an explicit prior sign/zero guard in the same local statement window. Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_rust_security_footguns` passes. Local evidence: `python3 dev/scripts/checks/check_rust_security_footguns.py --format md` remains green on the current working tree (`sign_unsafe_syscall_casts +0`). |
| Phase-14 Rust security-footguns expansion (PID wrap casts) | 2026-03-09 | Extended `check_rust_security_footguns.py` with `pid_signed_wrap_casts` so changed non-test Rust files now flag `child.id() as i32` and `libc::getpid() as i32` style conversions that can silently wrap on narrower signed PID paths. Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_rust_security_footguns` passes. Local evidence: `python3 dev/scripts/checks/check_rust_security_footguns.py --format md` remains green on the current working tree (`pid_signed_wrap_casts +0`). |
| Phase-14 Rust security-footguns expansion (`unreachable!()` hot paths) | 2026-03-09 | Extended `check_rust_security_footguns.py` with a new `unreachable_hot_path_calls` metric that flags changed non-test Rust files adding `unreachable!()` in runtime hot-path surfaces (`rust/src/bin/voiceterm/**`, `rust/src/audio/**`, `rust/src/ipc/**`). The metric intentionally ignores non-hot-path surfaces such as `rust/src/devtools/**` so internal tooling state helpers do not create false-positive noise. Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_rust_security_footguns` passes. Local evidence: `python3 dev/scripts/checks/check_rust_security_footguns.py --format md` remains green on the current working tree (`unreachable_hot_path_calls +0`). |
| Phase-14 Rust guard expansion (`check_rust_best_practices` suspicious `OpenOptions`) | 2026-03-09 | Extended `check_rust_best_practices.py` with a new `suspicious_open_options` metric that flags changed non-test Rust files adding `OpenOptions::new().create(true)` chains without explicit overwrite/create semantics (`append(true)`, `truncate(...)`, or `create_new(true)`). This follows the same risk class called out by Clippy's `suspicious_open_options` lint while keeping enforcement repo-specific and non-regressive. Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_rust_best_practices` passes. Local evidence: `python3 dev/scripts/checks/check_rust_best_practices.py --format md` remains green on the current working tree (`suspicious_open_options +0`). |
| Phase-14 Rust guard expansion (`check_rust_best_practices` float literal equality) | 2026-03-09 | Extended `check_rust_best_practices.py` with a new `float_literal_comparisons` metric that flags changed non-test Rust files adding direct `==` / `!=` comparisons against float literals. This is a repo-specific non-regression slice aligned with the risk class behind Clippy's `float_cmp` lint, but kept intentionally narrow to avoid noisy pseudo-parser behavior. Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_rust_best_practices` passes. Local evidence: `python3 dev/scripts/checks/check_rust_best_practices.py --format md` remains green on the current working tree (`float_literal_comparisons +0`). |
| Phase-14 Rust guard expansion (`check_rust_best_practices` persistent TOML writes) | 2026-03-09 | Extended `check_rust_best_practices.py` with a new `nonatomic_persistent_toml_writes` metric that flags changed non-test Rust files adding direct overwrite helpers (`fs::write`, `File::create`, truncate-open `OpenOptions`) in app-owned persistent TOML paths such as `config.toml`, onboarding state, and theme exports under `~/.config/voiceterm`. Temp-path writes are intentionally ignored so future temp-file swap remediations do not trigger false positives. Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_rust_best_practices` passes. Local evidence: `python3 dev/scripts/checks/check_rust_best_practices.py --format md` remains green on the current working tree (`nonatomic_persistent_toml_writes +0`). |
| Phase-14 Rust guard expansion (`check_rust_best_practices` custom parsers) | 2026-03-09 | Extended `check_rust_best_practices.py` with a new `custom_persistent_toml_parsers` metric that flags changed non-test Rust config/state readers adding hand-rolled persistent TOML parsers in places where the repo already depends on the `toml` crate. The metric is intentionally scoped to persisted TOML/state readers and looks for parser functions that manually split on `=` / iterate line-by-line / trim quoted values instead of routing through `toml::from_str`. Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_rust_best_practices` passes. Local evidence: `python3 dev/scripts/checks/check_rust_best_practices.py --format md` remains green on the current working tree (`custom_persistent_toml_parsers +0`). |
| Phase-14 Serde compatibility guard | 2026-03-09 | Added `check_serde_compatibility.py` to catch newly introduced internally/adjacently tagged Rust `Deserialize` enums that lack both a `#[serde(other)]` fallback variant and a nearby `serde-compat: allow reason=...` comment documenting intentional fail-closed behavior. Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_serde_compatibility dev.scripts.devctl.tests.test_check dev.scripts.devctl.tests.test_bundle_registry dev.scripts.devctl.tests.test_script_catalog dev.scripts.devctl.tests.test_audit_scaffold` passes. Local evidence: `python3 dev/scripts/checks/check_serde_compatibility.py --format md` remains green on the current working tree (`violations: 0`). |
| Phase-14 shared-logic heuristic extension | 2026-03-09 | Extended `check_duplication_audit.py` + `check_duplication_audit_support.py` with advisory `--check-shared-logic` mode that scans newly added Python/tooling files for `new-file-vs-shared-helper` and `orchestration-pattern-clone` candidates. The mode works without a jscpd report when used as a diff/local heuristic-only pass, while still honoring existing duplication-report thresholds when report data is present. Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_duplication_audit` passes. Local evidence: `python3 dev/scripts/checks/check_duplication_audit.py --check-shared-logic --paths dev/scripts/checks/check_duplication_audit.py --report-path /tmp/voiceterm-shared-logic-missing.json --format md` exits clean with zero findings on the sampled path. |
| Phase-14 architecture surface sync guard | 2026-03-09 | Added `check_architecture_surface_sync.py` with five MVP zones (`active-plan`, `check-script`, `devctl-command`, `app-surface`, `workflow`), declarative allowlist-backed zone registration, and explicit new-file-only scanning (`git diff --diff-filter=A` + `git ls-files --others --exclude-standard`). Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_architecture_surface_sync dev.scripts.devctl.tests.test_bundle_registry dev.scripts.devctl.tests.test_script_catalog` passes. Targeted local evidence: `python3 dev/scripts/checks/check_architecture_surface_sync.py --paths dev/scripts/checks/check_architecture_surface_sync.py --format md` now succeeds once the new guard is registered in `script_catalog.py`, referenced by shared governance bundles, and wired into `tooling_control_plane.yml` plus `release_preflight.yml`. |
| Devctl maintainability cleanup tranche, pass 2 | 2026-03-09 | Further modularized `dev/scripts/devctl/collect.py`, `dev/scripts/devctl/commands/hygiene_audits.py`, `dev/scripts/devctl/publication_sync.py`, and `dev/scripts/devctl/triage/support.py`; also reduced repeated test scaffolding in `dev/scripts/devctl/tests/test_check.py` and `test_ship.py`. Verification: `python3 -m py_compile dev/scripts/devctl/collect.py dev/scripts/devctl/tests/test_collect_dev_logs.py dev/scripts/devctl/commands/hygiene_audits.py dev/scripts/devctl/publication_sync.py dev/scripts/devctl/triage/support.py`; `python3 -m pytest dev/scripts/devctl/tests/test_collect_dev_logs.py dev/scripts/devctl/tests/test_status_report_parallel.py dev/scripts/devctl/tests/test_hygiene.py -q --tb=short -k 'CollectDevLogsTests or scripts_audit or fix_pycache_dirs or parallel'`; `python3 -m pytest dev/scripts/devctl/tests/test_check.py dev/scripts/devctl/tests/test_ship.py dev/scripts/devctl/tests/test_publication_sync.py dev/scripts/devctl/tests/test_check_publication_sync.py dev/scripts/devctl/tests/test_triage.py -q --tb=short` all pass. |
| Devctl maintainability cleanup tranche | 2026-03-09 | Consolidated duplicated helpers into `dev/scripts/devctl/common.py` (`display_path`, `resolve_repo_path`, `read_json_object`, `emit_output`), switched review/publication/autonomy consumers to the shared surfaces, split the review-channel prompt/launcher and status-report renderers into smaller helpers, replaced the manual `bundle.post-push` guard block with shared-list composition, and reduced repeated test scaffolding in `test_check.py` and `test_ship.py`. Verification: `python3 -m py_compile dev/scripts/devctl/common.py dev/scripts/devctl/publication_sync_git.py dev/scripts/devctl/autonomy/run_helpers.py dev/scripts/devctl/autonomy/benchmark_helpers.py dev/scripts/devctl/clippy_pedantic.py dev/scripts/devctl/commands/loop_packet_helpers.py dev/scripts/devctl/data_science_metrics.py dev/scripts/devctl/review_channel/state.py dev/scripts/devctl/review_channel/handoff.py dev/scripts/devctl/review_channel.py dev/scripts/devctl/cli_parser/builders_ops.py dev/scripts/devctl/cli_parser/release.py dev/scripts/devctl/cli_parser/quality.py dev/scripts/devctl/cli_parser/builders_checks.py dev/scripts/devctl/cli_parser/reporting.py dev/scripts/devctl/status_report.py dev/scripts/devctl/commands/audit_scaffold.py dev/scripts/devctl/commands/review_channel.py dev/scripts/devctl/commands/mobile_status.py dev/scripts/devctl/cli.py`; `python3 -m pytest dev/scripts/devctl/tests/test_bundle_registry.py dev/scripts/devctl/tests/test_check_bundle_workflow_parity.py dev/scripts/devctl/tests/test_common.py dev/scripts/devctl/tests/test_review_channel.py -q --tb=short`; `python3 -m pytest dev/scripts/devctl/tests/test_process_sweep.py dev/scripts/devctl/tests/test_process_watch.py dev/scripts/devctl/tests/test_process_audit.py dev/scripts/devctl/tests/test_process_cleanup.py dev/scripts/devctl/tests/test_guard_run.py dev/scripts/devctl/tests/test_function_duplication_guard.py -q --tb=short`; `python3 -m pytest dev/scripts/devctl/tests/test_publication_sync.py dev/scripts/devctl/tests/test_check_publication_sync.py dev/scripts/devctl/tests/test_clippy_pedantic.py dev/scripts/devctl/tests/test_mobile_status.py dev/scripts/devctl/tests/test_status_report_parallel.py dev/scripts/devctl/tests/test_audit_scaffold.py dev/scripts/devctl/tests/test_check.py dev/scripts/devctl/tests/test_ship.py -q --tb=short` all pass. |
| Devctl maintainability cleanup tranche, pass 3 | 2026-03-09 | Consolidated the command-output tail boilerplate across the `devctl` command surface by extending `emit_output()` with injected writer/piper callbacks plus optional secondary outputs, then migrated the repeated `write_output` + `pipe_output` + exit-pattern logic in the command modules to the shared helper while preserving module-level test patch seams. Verification: `python3 -m py_compile dev/scripts/devctl/common.py dev/scripts/devctl/tests/test_common.py dev/scripts/devctl/commands/status.py dev/scripts/devctl/commands/report.py dev/scripts/devctl/commands/path_audit.py dev/scripts/devctl/commands/path_rewrite.py dev/scripts/devctl/commands/process_audit.py dev/scripts/devctl/commands/process_cleanup.py dev/scripts/devctl/commands/process_watch.py dev/scripts/devctl/commands/guard_run.py dev/scripts/devctl/commands/security.py dev/scripts/devctl/commands/hygiene.py dev/scripts/devctl/commands/compat_matrix.py dev/scripts/devctl/commands/publication_sync.py dev/scripts/devctl/commands/triage.py dev/scripts/devctl/commands/orchestrate_status.py dev/scripts/devctl/commands/orchestrate_watch.py dev/scripts/devctl/commands/check_router.py dev/scripts/devctl/commands/cihub_setup.py dev/scripts/devctl/commands/integrations_sync.py dev/scripts/devctl/commands/reports_cleanup.py dev/scripts/devctl/commands/ship.py dev/scripts/devctl/commands/phone_status.py dev/scripts/devctl/commands/mobile_status.py dev/scripts/devctl/commands/autonomy_loop_support.py dev/scripts/devctl/commands/autonomy_report.py dev/scripts/devctl/commands/autonomy_benchmark.py dev/scripts/devctl/commands/autonomy_swarm.py dev/scripts/devctl/commands/autonomy_run.py dev/scripts/devctl/commands/controller_action.py dev/scripts/devctl/commands/data_science.py dev/scripts/devctl/commands/mutation_loop.py dev/scripts/devctl/commands/triage_loop.py dev/scripts/devctl/commands/docs_check.py dev/scripts/devctl/commands/release_gates.py dev/scripts/devctl/commands/sync.py dev/scripts/devctl/commands/failure_cleanup.py dev/scripts/devctl/commands/loop_packet.py dev/scripts/devctl/commands/integrations_import.py dev/scripts/devctl/commands/check_phases.py dev/scripts/devctl/commands/listing.py`; `python3 -m pytest dev/scripts/devctl/tests/test_common.py dev/scripts/devctl/tests/test_status.py dev/scripts/devctl/tests/test_report.py dev/scripts/devctl/tests/test_path_audit.py dev/scripts/devctl/tests/test_path_rewrite.py dev/scripts/devctl/tests/test_process_audit.py dev/scripts/devctl/tests/test_process_cleanup.py dev/scripts/devctl/tests/test_process_watch.py dev/scripts/devctl/tests/test_guard_run.py -q --tb=short`; `python3 -m pytest dev/scripts/devctl/tests/test_security.py dev/scripts/devctl/tests/test_hygiene.py dev/scripts/devctl/tests/test_publication_sync.py dev/scripts/devctl/tests/test_triage.py dev/scripts/devctl/tests/test_orchestrate_status.py dev/scripts/devctl/tests/test_orchestrate_watch.py dev/scripts/devctl/tests/test_check_router.py dev/scripts/devctl/tests/test_cihub_setup.py dev/scripts/devctl/tests/test_integrations_sync.py dev/scripts/devctl/tests/test_reports_cleanup.py dev/scripts/devctl/tests/test_ship.py -q --tb=short`; `python3 -m pytest dev/scripts/devctl/tests/test_phone_status.py dev/scripts/devctl/tests/test_mobile_status.py dev/scripts/devctl/tests/test_autonomy_report.py dev/scripts/devctl/tests/test_autonomy_benchmark.py dev/scripts/devctl/tests/test_autonomy_swarm.py dev/scripts/devctl/tests/test_autonomy_run.py dev/scripts/devctl/tests/test_data_science.py dev/scripts/devctl/tests/test_controller_action.py dev/scripts/devctl/tests/test_mutation_loop.py dev/scripts/devctl/tests/test_triage_loop.py dev/scripts/devctl/tests/test_docs_check.py dev/scripts/devctl/tests/test_release_gates.py dev/scripts/devctl/tests/test_sync.py dev/scripts/devctl/tests/test_failure_cleanup.py dev/scripts/devctl/tests/test_loop_packet.py dev/scripts/devctl/tests/test_integrations_import.py dev/scripts/devctl/tests/test_check.py -q --tb=short` all pass. |
| Devctl maintainability cleanup tranche, pass 4 | 2026-03-09 | Finished the command-tail/systemic follow-up by moving `mcp.py` onto the shared emitter, extracting path/output/env helpers into `dev/scripts/devctl/common_io.py`, decomposing parser families into `cli_parser/builders_docs_reporting.py` and `cli_parser/builders_governance.py`, splitting `dev/scripts/devctl/review_channel/parser.py` by argument group, and extracting triage bundle writes into `dev/scripts/devctl/triage/bundle.py` while trimming the remaining over-limit command `run()` functions in `security.py`, `triage.py`, `autonomy_benchmark.py`, and `autonomy_swarm.py`. Verification: `python3 -m py_compile dev/scripts/devctl/common.py dev/scripts/devctl/common_io.py dev/scripts/devctl/cli_parser/builders_ops.py dev/scripts/devctl/cli_parser/builders_docs_reporting.py dev/scripts/devctl/cli_parser/builders_governance.py dev/scripts/devctl/review_channel/parser.py dev/scripts/devctl/commands/mcp.py dev/scripts/devctl/commands/security.py dev/scripts/devctl/commands/triage.py dev/scripts/devctl/commands/autonomy_benchmark.py dev/scripts/devctl/commands/autonomy_swarm.py dev/scripts/devctl/triage/bundle.py dev/scripts/devctl/triage/support.py`; `python3 -m pytest dev/scripts/devctl/tests/test_common.py dev/scripts/devctl/tests/test_mcp.py dev/scripts/devctl/tests/test_security.py dev/scripts/devctl/tests/test_triage.py dev/scripts/devctl/tests/test_autonomy_benchmark.py dev/scripts/devctl/tests/test_autonomy_swarm.py dev/scripts/devctl/tests/test_review_channel.py dev/scripts/devctl/tests/test_report.py dev/scripts/devctl/tests/test_status_report_parallel.py dev/scripts/devctl/tests/test_audit_scaffold.py dev/scripts/devctl/tests/test_hygiene.py dev/scripts/devctl/tests/test_ship.py -q --tb=short`; `python3 dev/scripts/devctl.py docs-check --strict-tooling`; `python3 dev/scripts/checks/check_active_plan_sync.py`; `python3 dev/scripts/checks/check_multi_agent_sync.py`; `python3 dev/scripts/checks/check_code_shape.py --format md` all pass or report expected residual debt. Residual shape debt after this pass is reduced to 34 total violations, with the devctl-specific remainder limited to `collect.py`, `commands/review_channel.py`, `review_channel*.py`, `process_sweep_core.py`, `process_sweep_scans.py`, and `rust_audit_report.py`; `check_review_channel_bridge.py` remains red only because the pre-existing bridge files `bridge.md` and `dev/active/review_channel.md` are untracked in the dirty tree. |
| Devctl maintainability cleanup tranche, pass 5 | 2026-03-09 | Reduced the next devctl shape hotspots by extracting guarded Dev Mode session summarization into `dev/scripts/devctl/collect_dev_logs.py`, moving pure process path/command predicates into `dev/scripts/devctl/process_sweep_matching.py`, and moving scope-specific process row matchers into `dev/scripts/devctl/process_sweep_scope_matchers.py` while keeping the public `process_sweep.py` facade stable. Verification: `python3 -m py_compile dev/scripts/devctl/collect.py dev/scripts/devctl/collect_dev_logs.py dev/scripts/devctl/process_sweep_core.py dev/scripts/devctl/process_sweep_scans.py dev/scripts/devctl/process_sweep_matching.py dev/scripts/devctl/process_sweep_scope_matchers.py dev/scripts/devctl/process_sweep.py`; `python3 -m pytest dev/scripts/devctl/tests/test_collect_dev_logs.py dev/scripts/devctl/tests/test_collect_ci_runs.py dev/scripts/devctl/tests/test_status_report_parallel.py dev/scripts/devctl/tests/test_orchestrate_watch.py dev/scripts/devctl/tests/test_orchestrate_status.py -q --tb=short`; `python3 -m pytest dev/scripts/devctl/tests/test_process_sweep.py dev/scripts/devctl/tests/test_process_audit.py dev/scripts/devctl/tests/test_process_cleanup.py dev/scripts/devctl/tests/test_check.py dev/scripts/devctl/tests/test_hygiene.py -q --tb=short`; `python3 dev/scripts/checks/check_code_shape.py --format md` all pass or report expected residual debt. Residual shape debt after this pass is reduced to 31 total violations, with the devctl-specific remainder limited to `commands/review_channel.py`, `review_channel*.py`, and `rust_audit_report.py`; `check_review_channel_bridge.py` remains red only because the pre-existing bridge files `bridge.md` and `dev/active/review_channel.md` are untracked in the dirty tree. |
| Devctl maintainability cleanup tranche, pass 6 | 2026-03-09 | Cleared the final working-tree shape debt by splitting `code_shape_policy.py` into a slimmer policy surface plus `code_shape_shared.py` and `code_shape_function_exceptions.py`, removing temporary exceptions after shrinking `check_bundle_workflow_parity.py::build_report`, `check_rust_best_practices.py::main`, and `app/operator_console/views/home_workspace.py::__init__`, and extracting shared Start Swarm widget updates into `app/operator_console/views/swarm_status_widgets.py`. Verification: `python3 -m py_compile dev/scripts/checks/code_shape_shared.py dev/scripts/checks/code_shape_function_exceptions.py dev/scripts/checks/code_shape_policy.py dev/scripts/checks/code_shape_function_policy.py dev/scripts/checks/check_bundle_workflow_parity.py dev/scripts/checks/check_rust_best_practices.py app/operator_console/views/swarm_status_widgets.py app/operator_console/views/home_workspace.py app/operator_console/views/activity_workspace.py`; `python3 -m pytest dev/scripts/devctl/tests/test_check_code_shape_guidance.py dev/scripts/devctl/tests/test_check_bundle_workflow_parity.py dev/scripts/devctl/tests/test_check_rust_best_practices.py -q --tb=short`; `python3 -m pytest app/operator_console/tests/ -q --tb=short`; `python3 dev/scripts/checks/check_code_shape.py --format md` all pass. Result: working-tree `check_code_shape` is fully green with zero violations and no renewed temporary exceptions for the fixed Python hotspots. |
| Phase-14 Rust guard expansion (`check_rust_best_practices --absolute`) | 2026-03-09 | Added `--absolute` full-tree mode to `check_rust_best_practices.py` so it can audit all tracked/untracked non-test Rust files instead of only changed-file growth. Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_rust_best_practices` passes. Full-tree evidence: `python3 dev/scripts/checks/check_rust_best_practices.py --absolute --format md` reports 32 current violations across `263` Rust files scanned, with the highest-signal clusters in suppressed send results (`dev_command/broker/mod.rs`, `main.rs`, `theme_ops.rs`, `event_loop/*`, `voice_control/*`, `codex/*`, `ipc/*`), `Result<_, String>` usage (`auth.rs`, `config/cli.rs`, `ipc/session*.rs`, `theme/rule_profile/eval.rs`), and undocumented unsafe blocks (`terminal.rs`, `pty_session/*`). |
| Phase-14 Rust guard expansion (`check_rust_best_practices`) | 2026-03-09 | Added `dropped_send_results` and `unwrap_on_join_recv` metrics to `check_rust_best_practices.py`, updated guard docs in `AGENTS.md` + `dev/scripts/README.md`, and extended unit coverage in `dev/scripts/devctl/tests/test_check_rust_best_practices.py`. Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_rust_best_practices` passes. Working-tree audit evidence: `python3 dev/scripts/checks/check_rust_best_practices.py --format md` now reports 5 current dirty-tree violations, including suppressed `update_tx.send(...)` results in `rust/src/bin/voiceterm/dev_command/broker/mod.rs`, which keeps the next Rust cleanup slice explicit rather than hidden. |
| Phase-14 Rust guard expansion (`check_rust_best_practices` detached-thread + final send cleanup) | 2026-03-09 | Added a `detached_thread_spawns` metric to `check_rust_best_practices.py` so changed non-test Rust files now fail when they add bare `thread::spawn(...)` statements that drop their `JoinHandle` without a nearby `detached-thread: allow reason=...` note; tightened the heuristic so `JoinHandle`-returning helper functions are not false positives; and cleaned the last dirty-tree `UserInputActivity` send site by routing it through the existing best-effort writer helper. Verification: `python3 -m pytest dev/scripts/devctl/tests/test_check_rust_best_practices.py -q --tb=short` passes. Local evidence: `python3 dev/scripts/checks/check_rust_best_practices.py --format md` is green on the current dirty tree, while `python3 dev/scripts/checks/check_rust_best_practices.py --absolute --format md` drops to 19 remaining violations with `dropped_send_results`, `dropped_emit_results`, and `detached_thread_spawns` all at `+0`. |
| Phase-14 Rust best-practices backlog burn-down (`check_rust_best_practices --absolute`) | 2026-03-09 | Finished the remaining absolute Rust best-practices debt by moving the last persistence hotspots to shared atomic writes plus `toml` parsing/serialization (`persistent_config.rs`, `onboarding.rs`, `theme_studio/export_page.rs`, new `persistence_io.rs`), tightening the guard so `SAFETY:` comments immediately inside `unsafe { ... }` blocks count as valid documentation, and cleaning the final float-comparison / reason-less `allow(...)` / undocumented-unsafe debt in the touched runtime files. Verification: `cargo test --bin voiceterm persistence_io::tests -- --nocapture`, `cargo test --bin voiceterm onboarding::tests -- --nocapture`, `cargo test --bin voiceterm persistent_config::tests -- --nocapture`, `cargo test --bin voiceterm export_page -- --nocapture`, `python3 -m pytest dev/scripts/devctl/tests/test_check_rust_best_practices.py -q --tb=short`, and `python3 -m py_compile dev/scripts/checks/check_rust_best_practices.py dev/scripts/devctl/tests/test_check_rust_best_practices.py` all pass. Local evidence: both `python3 dev/scripts/checks/check_rust_best_practices.py --format md` and `python3 dev/scripts/checks/check_rust_best_practices.py --absolute --format md` are now green with `violations: 0`. |
| Phase-14 Rust compiler warning guard (`check_rust_compiler_warnings`) | 2026-03-09 | Added `check_rust_compiler_warnings.py` so changed-file Rust warning debt is enforced through a real `cargo test --no-run --message-format=json` compile instead of static heuristics; the guard is now registered in `script_catalog.py`, promoted into the canonical guard bundles, and enforced by `rust_ci.yml`, `tooling_control_plane.yml`, and `release_preflight.yml`. Verification: `python3 -m py_compile dev/scripts/checks/check_rust_compiler_warnings.py dev/scripts/devctl/tests/test_check_rust_compiler_warnings.py`, `python3 -m pytest dev/scripts/devctl/tests/test_check_rust_compiler_warnings.py -q --tb=short`, `python3 dev/scripts/checks/check_rust_compiler_warnings.py --format md`, `python3 dev/scripts/checks/check_guard_enforcement_inventory.py`, `python3 dev/scripts/checks/check_architecture_surface_sync.py --paths dev/scripts/checks/check_rust_compiler_warnings.py dev/scripts/devctl/tests/test_check_rust_compiler_warnings.py .github/workflows/rust_ci.yml --format md`, `python3 dev/scripts/checks/check_bundle_workflow_parity.py`, `python3 dev/scripts/checks/check_agents_bundle_render.py`, and `python3 dev/scripts/checks/check_workflow_shell_hygiene.py` all pass. The first live run caught a real `dead_code` warning in `rust/src/bin/voiceterm/dev_command/review_artifact/state.rs`; that warning was resolved by documenting the preview/test-only helper instead of suppressing the new guard. |
| Dev-command hotspot decomposition + guard hardening | 2026-03-09 | `rust/src/bin/voiceterm/dev_command/review_artifact.rs` (`770`) was split into `review_artifact/{artifact.rs (131), state.rs (126), format.rs (48), tab.rs (66)}`; `rust/src/bin/voiceterm/dev_command/broker.rs` (`714`) was split into `broker/{mod.rs (344), summary.rs (230), completion.rs (124), path.rs (19)}`; `check_code_shape` now supports `PATH_POLICY_PREFIX_OVERRIDES` and enforces a stricter `rust/src/bin/voiceterm/dev_command/` budget (`soft=360`, `hard=450`) with an exact `command_state.rs` override (`soft=500`, `hard=550`). Verification: `python3 -m unittest dev.scripts.devctl.tests.test_check_code_shape_guidance`, `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm dev_command:: -- --nocapture`, `python3 dev/scripts/checks/check_active_plan_sync.py`, and `python3 dev/scripts/checks/check_multi_agent_sync.py` all pass. Working-tree `check_code_shape` audit still reports unrelated existing hotspots in `app/operator_console/`, `dev/scripts/devctl/review_channel.py`, `dev/scripts/devctl/process_sweep_scans.py`, and `rust/src/bin/voiceterm/event_loop/tests.rs`, keeping the deeper maintainability census explicit instead of hidden. |
| Pedantic advisory report/triage integration | 2026-03-08 | `check --profile pedantic` now emits `dev/reports/check/clippy-pedantic-summary.json` + `clippy-pedantic-lints.json`; `report --pedantic` and `triage --pedantic` ingest those artifacts through the shared snapshot path with policy classification from `dev/config/clippy/pedantic_policy.json`; targeted verification: `python3 -m unittest dev.scripts.devctl.tests.test_collect_clippy_warnings dev.scripts.devctl.tests.test_clippy_pedantic dev.scripts.devctl.tests.test_report dev.scripts.devctl.tests.test_triage dev.scripts.devctl.tests.test_status_report_parallel dev.scripts.devctl.tests.test_check` |
| Phase-14 external tool comparison (primary docs) | 2026-03-08 | Reviewed primary docs for dependency-cruiser orphan rules, `cargo modules orphans --deny`, ArchUnit slice rules, PyTestArch rule model, jscpd, PMD CPD, Simian, and Semgrep custom-rule authoring. Result: custom `check_architecture_surface_sync.py` remains justified as a new guard domain, while shared-logic detection belongs as an advisory extension of `check_duplication_audit.py` rather than a new standalone script. Caveat captured in plan text: the "ArchUnit/PyTestArch lack built-in orphan detection" point is an inference from their documented rule model and examples, not a direct vendor statement. |
| Maintainability hotspot census | 2026-03-08 | Local size scan confirmed the next cleanup tranche should explicitly cover `app/operator_console/ui.py` (`667`), `app/operator_console/bridge_model.py` (`508`), `app/operator_console/theme.py` (`380`), `rust/src/bin/voiceterm/event_loop.rs` (`728`), `rust/src/bin/voiceterm/main.rs` (`868`), `rust/src/bin/voiceterm/dev_command/review_artifact.rs` (`755`), `rust/src/bin/voiceterm/dev_command/broker.rs` (`643`), `rust/src/bin/voiceterm/dev_panel/review_surface.rs` (`779`), `rust/src/bin/voiceterm/dev_panel/cockpit_page/mod.rs` (`576`), and the flat `dev/scripts/devctl/commands/` package with multiple 300+ line command files. |
| Advisory pedantic lint lane | 2026-03-08 | Added opt-in `devctl check --profile pedantic` wiring plus maintainer-doc guidance; verification includes parser/profile unit coverage and targeted `devctl` dry-run/profile checks so pedantic usage is explicit but not required by bundle or release lanes |
| Theme Studio helper dedup follow-up | 2026-03-07 | `theme_studio_input.rs` now uses `apply_vertical_arrow_navigation` and `apply_theme_studio_runtime_override_cycle` to centralize repeated handler logic; verification: `cd rust && cargo fmt`, `cd rust && cargo test --bin voiceterm theme_studio -- --nocapture` (`68` passed), `cd rust && cargo test --bin voiceterm writer::state:: -- --nocapture` (`135` passed), `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` |
| Theme Studio input-dispatch maintainability refactor | 2026-03-07 | `cd rust && cargo fmt`; `cd rust && cargo test --bin voiceterm theme_studio -- --nocapture` (`68` passed); `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel`; `python3 dev/scripts/devctl.py check --profile ci`; `python3 dev/scripts/devctl.py docs-check --user-facing`; `python3 dev/scripts/devctl.py hygiene`; `python3 dev/scripts/checks/check_active_plan_sync.py`; `python3 dev/scripts/checks/check_multi_agent_sync.py`; `python3 dev/scripts/checks/check_cli_flags_parity.py`; `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`; `markdownlint ...` all pass |
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
| Docs IA census + path-coupling audit (manual) | 2026-03-06 | `dev/` markdown layout inventory (`76` files), orphan backlog detection (`dev/BACKLOG.md` referenced `0` times), and migration blast-radius map across checks/workflows/tests/docs |
| Audit merge transcript evidence (manual) | 2026-03-06 | Raw 4-agent merge transcript retained at `dev/active/move.md`; authoritative findings remain in `dev/active/audit.md` and execution sequencing remains in this document |
| Active-plan governance checks | 2026-03-06 | `check_active_plan_sync`, `check_multi_agent_sync`, `docs-check --strict-tooling`, and `hygiene` all pass after audit-doc registration/link updates |
| Phase-16 transition-compat cleanup verification | 2026-03-06 | `python3 -m unittest dev.scripts.devctl.tests.test_audit_scaffold`, `python3 -m unittest dev.scripts.devctl.tests.test_docs_check dev.scripts.devctl.tests.test_docs_check_constants`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene --strict-warnings`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_multi_agent_sync.py`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_bundle_workflow_parity.py`, `python3 dev/scripts/devctl.py check-router --since-ref origin/develop --format md`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/devctl.py orchestrate-status --format md`, and `python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md` all pass (watch warnings remain non-blocking stale-agent notices) |
| Phase-15 boundary cleanup verification | 2026-03-06 | `python3 -m unittest dev.scripts.devctl.tests.test_audit_scaffold`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene --strict-warnings`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_multi_agent_sync.py`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_bundle_workflow_parity.py`, `python3 dev/scripts/devctl.py check-router --since-ref origin/develop --format md`, and `python3 dev/scripts/checks/check_release_version_parity.py` all pass after canonical path updates |
| Runtime do-now kickoff validation | 2026-03-06 | `cd rust && cargo test --bin voiceterm` passes after removing `main.rs` `env::set_var` usage via runtime overrides (`1526` passed) |
| MP-265 shape-budget cleanup slice | 2026-03-06 | `theme/rule_profile.rs` tests extracted to `theme/rule_profile/tests.rs`; compact/minimal status-line helpers extracted to `status_line/format/compact.rs`; single-line status helpers extracted to `status_line/format/single_line.rs`; raised `PATH_POLICY_OVERRIDES` entries removed | `cargo clippy --bin voiceterm --all-targets -- -D warnings`, `cargo test --bin voiceterm`, and `check_code_shape` green after runtime module sizes dropped below the Rust default soft limit |
| Phase-16 writer dispatch decomposition + exception retirement | 2026-03-06 | `dispatch.rs` now handles message routing, PTY-heavy logic moved to `dispatch_pty.rs`, and temporary `dispatch`/`redraw`/`prompt_occlusion` complexity exceptions were removed | `cd rust && cargo test --bin voiceterm` (`1535` passed), `python3 dev/scripts/checks/check_code_shape.py --format md`, and `python3 dev/scripts/checks/check_structural_complexity.py --format md` all pass with structural exceptions at `0` |
| Phase-16 readability + full CI rerun | 2026-03-06 | Simplified dense comments/reason text in `writer/state/dispatch*.rs`, `check_structural_complexity.py`, and `code_shape_policy.py` after formatting in-flight Rust files that previously blocked `fmt-check` | `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_multi_agent_sync.py`, and `python3 dev/scripts/devctl.py docs-check --strict-tooling` all pass |
