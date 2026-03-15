# IDE + Provider Modularization Plan (MP-346, MP-354)

**Status**: execution mirrored in `dev/active/MASTER_PLAN.md` (`MP-346`, `MP-354`)  |  **Last updated**: 2026-03-07 | **Owner:** Runtime/tooling architecture
Execution plan contract: required

Closure note (2026-03-07): `MP-354` is complete. This doc stays active because
`MP-346` post-next-release backlog remains here (`Step 3g`, `Step 3h`, and
AntiGravity readiness intake).

## Scope

Create stable architecture boundaries so host IDE behavior and provider behavior
can evolve independently without cross-regressions.

In scope:

1. Decompose the current writer-side God-file behavior into host policies and
   provider policies with explicit ownership.
2. Consolidate terminal-host detection into one canonical source and remove
   duplicate JetBrains/Cursor sniffing logic.
3. Expand provider abstraction beyond prompt/thinking regex detection to include
   job lifecycle, argument construction, and capability signaling.
4. Add a machine-readable host/provider compatibility matrix and CI gates.
5. Add static/tooling checks that block mixed host+provider conditionals outside
   adapter/policy modules.

Out of scope (for initial MP-346 slices):

1. New product features unrelated to modularization or compatibility hardening.
2. Full AntiGravity host implementation before a concrete runtime host
   fingerprint/detection contract exists.

## Regression Containment Contract (Required)

No MP-346/MP-354 phase can advance without a fresh checkpoint packet and explicit
operator review.

### Checkpoint Bundle (every major slice)

Run after each major extraction step and before the next phase:

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop
python3 dev/scripts/checks/check_rust_lint_debt.py --since-ref origin/develop
python3 dev/scripts/checks/check_rust_best_practices.py --since-ref origin/develop
cd rust && cargo test --bin voiceterm
```

### Manual Runtime Verification (human gate)

Required smoke checks before phase advancement (4 release-scope combinations):

1. Cursor + Codex: startup, typing, scrolling, send path.
2. Cursor + Claude: startup, typing while output streams, prompt visibility.
3. JetBrains + Codex: HUD stability under output and resize.
4. JetBrains + Claude: approval/prompt visibility and non-corrupt redraw.
Post-next-release deferred cells (non-blocking for current release scope):

1. Other + Claude: startup banner, status-line render, output scroll without
   HUD corruption, clean exit.
2. Other + Codex: same as above.
3. Gemini baseline path: command startup + non-crash capability reporting.

Checkpoint scope note (active):

- `CP-006` accepted a temporary `5/7` matrix attestation during earlier
  extraction stages.
- Operator release-scope update (2026-03-05): final closure gating for this
  release is IDE-only (`cursor` + `jetbrains`, `codex` + `claude`) with
  required manual verification `4/4`.
- `Other` host cells and `Gemini baseline` remain explicitly tracked as
  post-next-release backlog intake and are non-blocking for this release gate.

### Checkpoint Artifacts

Write one packet per major slice under:

- `dev/reports/mp346/checkpoints/<timestamp>/`

Packet contents:

1. command outputs for checkpoint bundle.
2. short manual verification notes for each required host/provider cell.
3. pass/fail summary and explicit go/no-go decision.

### Stop-the-line Criteria

If any item below occurs, stop extraction work and return to last green state:

1. any required check in the checkpoint bundle fails.
2. any required manual verification cell for the current checkpoint gate fails,
   or remains untested without explicit operator waiver noted in that checkpoint
   packet.
3. file-shape/lint-debt gates regress.
4. prompt visibility, typing, or send flow regresses in previously green cells.

## Why Guardrails Missed This Earlier

Root causes confirmed in current repo policy/tooling:

1. No MP-346-specific path override budgets existed for the known hotspot files
   (`writer/state.rs`, `event_loop.rs`, IPC provider paths).
2. Existing shape guard focused on generic limits and did not yet enforce
   host/provider isolation boundaries.
3. No compatibility-matrix source or required smoke harness existed for
   host/provider combinations, so regressions escaped as integration drift.

MP-346 includes explicit remediation for each gap above.

## Baseline Audit (Validated 2026-03-01)

This section records code-verified findings (not assumptions).
Treat this as a historical snapshot; current-state closure evidence belongs in
`Guardrail Delivery Tracking`, `Progress Log`, and checkpoint artifacts.

| Finding | Validation | Evidence |
|---|---|---|
| `writer/state.rs` is a God file | confirmed | `wc -l rust/src/bin/voiceterm/writer/state.rs` -> `2750` lines |
| `handle_message` is oversized and high-blast-radius | confirmed | `state.rs` line range `605..1486` (`882` lines) via `nl -ba` |
| Pre-clear policy is parameter-heavy and host/provider-coupled | confirmed | `should_preclear_bottom_rows(...)` has `11` parameters (`state.rs:255`) |
| Host detection logic is duplicated | confirmed | `runtime_compat.rs:detect_terminal_host`, `writer/render.rs:detect_terminal_family`, `banner.rs:is_jetbrains_terminal` |
| Hardcoded host/provider conditionals in event loop | confirmed | `event_loop.rs:629 should_emit_user_input_activity` (`Claude && Cursor`) |
| Provider runtime path is codex/claude split, not generalized | confirmed | `ipc/router.rs:start_provider_job` and `ipc/session/auth_flow.rs` only match `Codex|Claude` |
| IPC provider model is codex/claude only | confirmed | `ipc/protocol.rs:Provider` has variants `{Codex, Claude}` |
| Capabilities event hardcodes providers | confirmed | `ipc/session/state.rs:emit_capabilities` -> `vec!["codex", "claude"]` |
| Gemini exists in backend registry but not IPC provider surface | confirmed | `backend/mod.rs` includes `GeminiBackend`; IPC provider/capabilities do not |
| AntiGravity has no runtime code footprint | confirmed | repo-wide search shows only plan/docs references |
| Debug helper duplication exists | confirmed | `parse_debug_env_flag` and `debug_bytes_preview` duplicated in `writer/state.rs` and `event_loop/prompt_occlusion.rs` |
| Terminal detection in 5 files with 4 enums | confirmed | `runtime_compat.rs:TerminalHost`, `render.rs:TerminalFamily`, `texture_profile.rs:TerminalId` (11 variants), `color_mode.rs` (raw bools), `banner.rs` (raw bool) |
| Theme detection bypasses canonical host detection | confirmed | `theme/detect.rs:is_warp_terminal` reads `TERM_PROGRAM` directly instead of consuming runtime host detection |
| `prompt_occlusion.rs` is a second God file | confirmed | 1143 lines, own ANSI strip, own debug helpers, own JetBrains check |
| `claude_prompt_detect.rs` is provider-specific code with no adapter | confirmed | 930 lines, hardcoded Claude approval patterns, `ClaudePromptDetector` used for all backends |
| `claude_prompt_suppressed` name leaked into generic code | confirmed | field in `StatusLineState`, referenced in 97+ locations across status_line, writer, event_loop, terminal, button_handlers |
| 5 independent ANSI-stripping implementations | confirmed | `prompt/strip.rs`, `prompt_occlusion.rs`, `memory/ingest.rs`, `transcript_history.rs`, `toast.rs` |
| 3 copies of debug env-flag parsing | confirmed | `writer/state.rs:35`, `prompt_occlusion.rs:32`, `terminal.rs:23` -- all read `VOICETERM_DEBUG_CLAUDE_HUD` via identical `OnceLock` pattern |
| 3 copies of backend detection | confirmed | `runtime_compat.rs:BackendFamily::from_label`, `writer/state.rs:backend_label_contains`/`is_codex_backend`/`is_claude_backend`, `event_loop.rs:630` inline |
| `main.rs` main() is 530 lines | confirmed | lines 189-716, monolithic init/setup/run/shutdown function |
| `EventLoopState` is 29-field mega-struct | confirmed | `event_state.rs:87-116`, all `pub(crate)`, every handler gets `&mut EventLoopState` |
| `color_mode.rs` emerging God file | confirmed | 838 lines with its own terminal detection (JetBrains/Cursor/Warp/iTerm) at lines 74-95 |
| Wake-word has hardcoded brand fuzzy-matching | confirmed | `wake_word.rs` and `voice_control/navigation.rs` have hardcoded "kodak"->"codex", "cloud"->"claude" tables |
| 14 independent env-var-locking helpers | confirmed | `rg -n "OnceLock<Mutex<\\(\\)>>" rust/src/bin/voiceterm | wc -l` -> `14`; helpers exist in `banner.rs`, `color_mode.rs`, `config/theme.rs`, `input/spawn.rs`, `main.rs`, `onboarding.rs`, `persistent_config.rs`, `prompt/logger.rs`, `runtime_compat.rs`, `terminal.rs`, `theme_ops.rs`, `wake_word/tests.rs`, `writer/state.rs`, `theme/style_pack/tests.rs` |
| `event_loop/tests.rs` is a test-side God file | confirmed | `wc -l rust/src/bin/voiceterm/event_loop/tests.rs` -> `5918`; high churn risk for prompt-suppression rename and behavior extraction |
| Runtime CI workflows still trigger on legacy `src/**` | confirmed | `.github/workflows/rust_ci.yml`, `voice_mode_guard.yml`, `wake_word_guard.yml`, `perf_smoke.yml`, `latency_guard.yml`, `memory_guard.yml`, `coverage.yml`, `lint_hardening.yml` use `paths: "src/**"` while runtime source is `rust/src/**` |
| Governance contracts still enforce legacy runtime path token | confirmed | `AGENTS.md` task router/CI lane map uses `src/**`; `check_agents_contract.py` requires exact router row string with `src/**` |
| Existing `path-audit` cannot detect stale workspace path contracts | confirmed | `devctl path-audit` returned `ok: True` while workflow `src/**` references remain; current scanner only rewrites legacy check-script paths |

Notes:

1. Prior audit wording referenced `needs_preclear_before_redraw`; current code
   uses `should_preclear_bottom_rows` for that decision surface.
2. Terminal detection duplication is 5 files, not 3. `texture_profile.rs`
   introduces a completely disconnected `TerminalId` enum with 11 variants
   (Kitty, ITerm2, WezTerm, Foot, Mintty, VsCode, Cursor, JetBrains,
   Alacritty, Warp, Generic, Unknown) that is not referenced by any other
   detection path.
3. Debug env-flag parsing has 3 copies, not 2. `terminal.rs:23` was missed.
4. `writer/state.rs` uses raw string-contains (`backend_label_contains`) for
   backend detection instead of `runtime_compat::BackendFamily`. These can
   diverge if a backend label like "claude-fast" is added.
5. Env-lock helper duplication is broader than the prior 6-file estimate. The
   current count is 14 independent helpers with no shared test utility.

## Guardrails Gap Analysis (Validated 2026-03-01)

Full audit of every check script, devctl profile, and test harness. This section
documents why the current automation failed to catch the God-file growth,
IDE/provider coupling, and duplicated detection logic before they became
entrenched.

### Check Suite Architecture: Structural Blind Spot

100% of the 16 check scripts in `dev/scripts/checks/` are regex/line-count
pattern matchers or document-format validators. Zero perform structural code
analysis (AST parsing, complexity measurement, dependency graph, or cross-file
comparison).

| Category | Scripts | % |
|---|---|---|
| Line-count/pattern-match on code | 5 (code_shape, rust_audit_patterns, rust_best_practices, rust_lint_debt, rust_security_footguns) | 31% |
| Document string-presence/format | 5 (agents_contract, active_plan_sync, markdown_metadata_header, multi_agent_sync, screenshot_integrity) | 31% |
| CI/pipeline status gates | 2 (coderabbit_gate, coderabbit_ralph_gate) | 13% |
| Version string equality | 1 (release_version_parity) | 6% |
| Doc-to-code parity (shallow) | 1 (cli_flags_parity) | 6% |
| External tool output policy | 2 (mutation_score, rustsec_policy) | 13% |
| **Actual structural/AST analysis** | **0** | **0%** |

### What Each AI-Guard Check Catches vs Misses

The 5 AI-guard checks (`--with-ai-guard` or `--profile prepush`) are the main
code-quality defense:

| Check | What It Catches | What Slips Through |
|---|---|---|
| `check_code_shape.py` | File grows past 900/1400 lines (diff-based) | Boil-the-frog: 39 lines/commit bypasses forever. No function-length check. `writer/state.rs` grew to 2750 lines this way. |
| `check_rust_best_practices.py` | New `#[allow]` without reason, undocumented `unsafe` | 81 compound booleans, 487-line functions, duplicated enums across files |
| `check_rust_lint_debt.py` | New `unwrap()`/`expect()` growth | Everything else |
| `check_rust_audit_patterns.py` | 5 specific known-bad patterns (UTF-8 slicing, etc.) | Anything not in those 5 hardcoded regexes |
| `check_rust_security_footguns.py` | `todo!()`, `dbg!()`, shell spawn, weak crypto | Anything structural |

### Critical Automation Gaps

**Gap 1 - No function-length check (CRITICAL)**:
`writer/state.rs` has a 487-line `handle_message()` function. No check even
knows what a "function" is. They all count file lines. A 900-line file with one
800-line monster function passes clean.

**Gap 2 - No cyclomatic/cognitive complexity check (CRITICAL)**:
`handle_message()` has ~30+ cyclomatic complexity with deeply nested
`if/else if/match` chains. No check measures this. A developer could write a
function with 50 nested `if` statements and every guard passes.

**Gap 3 - No cross-file duplication detection (CRITICAL)**:
Terminal detection logic is copy-pasted in 4 files with 2 different enums
(`TerminalHost` and `TerminalFamily`). No check compares files against each
other. Every script processes files in isolation.

**Gap 4 - No architectural boundary enforcement (CRITICAL)**:
IDE code can import provider internals. Provider code can reference IDE types.
`writer/state.rs` mixes both freely with 81 compound
`codex_jetbrains`/`claude_jetbrains`/`cursor_claude` variables. No check models
module boundaries.

**Gap 5 - No absolute violation mode (HIGH)**:
`code_shape` is diff-only. It only flags growth. A file already at 2750 lines
(vs 1400 hard limit) produces zero warnings as long as it doesn't grow. There
is no periodic "everything is wrong" alarm.

**Gap 6 - No compatibility matrix validation (HIGH)**:
No check validates that IDE/provider combinations work. No check even knows
what combinations exist.

**Gap 7 - `writer/state.rs` not in hotspot override list (HIGH)**:
6 other files have frozen growth budgets in `PATH_POLICY_OVERRIDES`. The
biggest God file -- `writer/state.rs` at 2750 lines -- uses the default
40-lines-per-commit growth allowance. It was never locked down.

**Gap 8 - CI runtime-lane trigger drift (CRITICAL)**:
Multiple runtime protection workflows still use `paths: "src/**"` while the
workspace source root is `rust/src/**`. This can silently skip expected lanes
for runtime changes.

**Gap 9 - Governance/check enforcement drift (CRITICAL)**:
`AGENTS.md` and `check_agents_contract.py` still pin `src/**` in required task
router snippets. Even if workflows are fixed, policy checks can force stale
contracts back into the docs.

**Gap 10 - Workspace-path audit blind spot (HIGH)**:
`devctl path-audit` currently detects only legacy check-script path rewrites.
It does not flag stale workflow/governance workspace-root contracts (`src/**`,
`working-directory: src`), so path regressions pass with `ok: True`.

**Gap 11 - Immediate clippy-threshold tightening can hard-fail CI (HIGH)**:
`devctl check` and `rust_ci.yml` run clippy with `-D warnings`. Lowering
`cognitive-complexity-threshold` and enabling `clippy::too_many_lines` without
baseline/non-regressive rollout can fail CI immediately on existing debt
instead of guiding staged extraction.

**Gap 12 - AI-guard execution-mode mismatch in `devctl check` (CRITICAL)**:
`devctl check` invokes AI-guard scripts without commit-range refs. In clean CI
worktrees this can evaluate zero changed files (working-tree diff vs `HEAD`)
and pass with weak regression signal.

**Gap 13 - Isolation gate is scheduled too late (HIGH)**:
`check_ide_provider_isolation.py` is currently scoped to Phase 4. That leaves
Phases 1-3 without a measurable coupling budget while high-risk extraction work
is in flight. Roll out report-only mode in Phase 0, then enforce blocking mode
no later than Phase 2 completion.

### How writer/state.rs Grew to 2750 Lines Undetected

The exact failure mode in `check_code_shape.py`:

1. Soft limit for `.rs` = 900, hard limit = 1400.
2. When a file is between 900-1400 lines, it can grow by 40 lines per commit
   (`oversize_growth_limit`).
3. When a file crosses 1400, it is "hard locked" with `hard_lock_growth_limit =
   0`.
4. The check is diff-based. If a commit adds 50 lines and removes 11 lines, net
   growth = 39, and it passes.
5. Over ~47 commits of 39-line increments, the file grew from 900 to 2750
   without ever triggering.
6. `check_code_shape.py` line 55 has a comment warning about this:
   "Do not bypass shape limits with readability-reducing code-golf edits." But
   it is honor-system only, not enforced.

### devctl Profile Coverage Gaps

| Profile | Runs AI guards? | Runs structural checks? | Runs compat matrix? |
|---|---|---|---|
| `devctl check --profile ci` | NO | NO | NO |
| `devctl check --profile prepush` | YES | NO | NO |
| `devctl check --profile release` | YES | NO | NO |
| `devctl check --profile ai-guard` | YES | NO | NO |
| `devctl check --profile quick` | NO | NO | NO |
| `devctl check --profile maintainer-lint` | NO | NO | NO |

The `ci` profile runs only `cargo fmt --check`, `cargo clippy`, and
`cargo test`. It does not run any of the AI-guard check scripts. This means a
PR can pass CI without ever hitting the code-shape or best-practices checks.

### Test Coverage for IDE/Provider Combinations

| Combination | Unit Tests | Integration Tests | Stress Tests |
|---|---|---|---|
| Cursor + Claude | ~10 tests | None | 1 (`claude_hud_stress.py`, hardcoded) |
| JetBrains + Claude | ~6 tests | None | None |
| JetBrains + Codex | ~3 tests | None | None |
| Cursor + Codex | **1 test** | None | None |
| Other + Claude | Partial/incidental | None | None |
| Other + Codex | Partial/incidental | None | None |
| Any + Gemini | **Zero** | None | None |
| Any + AntiGravity | **Zero** (code doesn't exist) | None | None |

4 of 9 combinations have direct unit tests. 2 more have incidental coverage.
3 have zero coverage (all Gemini). No parameterized matrix test exists. Every
test is hand-written for one specific combination. There is no
`for host in [JetBrains, Cursor, Other] { for provider in [..] { .. } }`
anywhere.

The only stress test (`claude_hud_stress.py`) is hardcoded to
`TERM_PROGRAM=cursor` and `--claude`. No equivalent exists for JetBrains or
Codex combinations.

### Summary: Automation Blind Spots

| Category | Coverage | Consequence |
|---|---|---|
| Line-count per file | Partial (diff-only, boil-the-frog bypass) | God files grow undetected |
| Function length | **None** | Monster functions invisible |
| Cyclomatic complexity | **None** | Unmeasured complexity drift |
| Code duplication | **None** | 4x duplicated detection logic |
| Module coupling | **None** | IDE/provider code freely mixed |
| Compatibility matrix | **None** | Combinations break silently |
| Absolute violations | **None** | 2750-line file = no warning if unchanged |
| Parameterized combo tests | **None** | 5 of 9 combinations barely tested |

## Required New Guardrails (MP-346 Deliverables)

### Immediate (Block further regression -- Phase 0)

1. **Freeze `writer/state.rs`**: add to `PATH_POLICY_OVERRIDES` in
   `check_code_shape.py` with `oversize_growth_limit=0,
   hard_lock_growth_limit=0`. Add extraction escape hatch: commits tagged
   `[mp346-extraction]` in the message may use a relaxed budget (net growth
   allowed if the file also shrinks by at least that much in the same PR).

2. **Add absolute shape audit mode**: extend `check_code_shape.py` with
   `--absolute` flag (~30-40 lines of code). Scans ALL source files against
   hard limits, not just changed files. Run in `release` profile.

3. **Upgrade `ci` profile**: change `with_ai_guard: False` to `True` in
   `check_profile.py` line 39 only after commit-range ref propagation is wired
   for AI-guard invocations in `devctl check`. Monitor first 10 CI runs for
   time budget impact.

#### Immediate Add-ons (Third-Pass Audit)

- **Workspace path-contract repair (CRITICAL)**: update runtime lane workflow
  triggers and governance/task-router contracts from `src/**` to `rust/src/**`
  (`AGENTS.md`, `check_agents_contract.py`, and all runtime guard workflows).
- **Add workspace path-contract gate (CRITICAL)**: extend `devctl path-audit`
  (or add `check_workspace_path_contracts.py`) to fail on stale runtime path
  contracts (`src/**`, `working-directory: src`) outside allowlisted legacy
  release-formula contexts.
- **Enforce AI-guard on runtime CI lanes (CRITICAL)**: after path-trigger
  repair, ensure at least one runtime workflow that fires on `rust/src/**`
  executes AI-guard checks (`check_code_shape`, `check_rust_lint_debt`,
  `check_rust_best_practices`, audit/security footguns) in commit-range mode.
- **Fix `devctl check` AI-guard range wiring (CRITICAL)**: add
  `--since-ref/--head-ref` support to `devctl check` and pass those refs to all
  AI-guard scripts so CI and release lanes evaluate commit ranges, not only
  working-tree diffs.
- **Security-policy gate completion (HIGH)**: make dependency-policy enforcement
  explicit in CI/release lanes by running `cargo deny` (or documented
  equivalent) and tightening `rust/deny.toml` advisories policy beyond yanked-
  only mode.
- **Guard-script test coverage closure (HIGH)**: add dedicated tests for
  `check_code_shape.py` core shape evaluator and `check_agents_contract.py`
  contract rows before those scripts become MP-346 hard gates.
- **Cross-plan overlap gate (CRITICAL)**: before runtime extraction starts,
  declare MP-346 ownership/lock for shared hotspot files (`writer/state.rs`,
  `writer/render.rs`, `banner.rs`, `color_mode.rs`, `terminal.rs`,
  `event_loop.rs`, `prompt_occlusion.rs`) and require explicit runbook lane
  updates for any other MP scope touching those paths.

### Short-term (Catch coupling and duplication -- Phase 0.5/1)

4. **Function-length + complexity**: use `rust-code-analysis-cli`
   (`cargo install rust-code-analysis-cli`) instead of building 3 separate
   Python scripts. Write one thin wrapper `check_structural_complexity.py`
   (~80 lines) that invokes `rust-code-analysis-cli` on changed files and
   enforces:
   - Function length budget (100 lines, non-regressive)
   - Cyclomatic complexity threshold (20, non-regressive)
   - Cognitive complexity threshold (25, non-regressive)
   This replaces the originally proposed `check_function_shape.py`,
   `check_boolean_density.py`, and `check_cyclomatic_complexity.py`.
   Also enable `clippy::too_many_lines` as `warn` in `Cargo.toml` for
   real-time editor feedback, and lower `clippy.toml`
   `cognitive-complexity-threshold` from 35 to 25.

5. **Duplicate enum/type detector**: build `check_duplicate_types.py` (~80
   lines). Regex scan for `enum \w+ {` blocks, extract variant names, compare
   across files. Also integrate `jscpd` (`npm install -g jscpd`) as a periodic
   audit for general code duplication: `jscpd rust/src/ --min-lines 10
   --reporters json`.

6. **IDE/provider isolation check**: build `check_ide_provider_isolation.py`
   (~100 lines). Define allowlist of modules permitted to reference
   `TerminalHost`/`BackendFamily` and roll out in two stages:
   - Phase 0: report-only baseline output (non-blocking) with per-file counts.
   - Phase 2+: blocking mode for unauthorized references outside adapters and
     cross-product resolver modules.

7. **Compatibility matrix YAML + check**: build
   `dev/config/compat/ide_provider_matrix.yaml` and `check_compat_matrix.py`.
   Machine-readable matrix with `support_level` (stable/experimental/
   unsupported), `known_caveats`, `last_tested_version` per cell.

### Medium-term (Structural quality -- Phase 0.5/4)

8. **Parameterized matrix tests**: add `rstest` to `Cargo.toml`
   dev-dependencies. Write parameterized tests in Phase 0.5 (before
   extraction, not after). These are characterization tests that lock current
   behavior.

9. **devctl `compat-matrix` command**: build `devctl/commands/compat_matrix.py`
   for validate/report workflows. Integrate with `claude_hud_stress.py` to
   parameterize across host/provider combinations.

10. **Host/Provider trait-contract completion pass**: run one source-mapped
    method inventory before implementation to close remaining adapter gaps for
    render behavior (full-banner redraw policy, color capability handling,
    cursor/autowrap redraw controls) and unresolved cross-product policy paths
    (reserved-row budgeting and rolling/non-rolling prompt semantics).

### Tooling Build vs Buy Summary

| Guardrail | Build/Extend/Buy | Effort |
|---|---|---|
| Freeze writer/state.rs | Extend `check_code_shape.py` (6 lines) | Trivial |
| Absolute shape audit | Extend `check_code_shape.py` (~30 lines) | Small |
| CI profile upgrade | Edit `check_profile.py` (1 line) | Trivial |
| Function + complexity + density | Buy `rust-code-analysis-cli` + thin wrapper | Small |
| Clippy thresholds | Edit `clippy.toml` + `Cargo.toml` (2 lines) | Trivial |
| Duplicate type detector | Build `check_duplicate_types.py` | Small |
| General duplication audit | Buy `jscpd` (periodic only) | Trivial |
| IDE/provider isolation | Build `check_ide_provider_isolation.py` with report->block rollout | Medium |
| Compat matrix + check | Build YAML + `check_compat_matrix.py` | Medium |
| Parameterized tests | Buy `rstest` crate | Small |
| devctl compat-matrix cmd | Build `compat_matrix.py` command | Medium |

Net: 4 new Python files + 1 Cargo dependency + 3 edits to existing files
(down from 8+ new Python scripts originally proposed).

### Meta-Governance for New Check Scripts

Each new check script must:
1. Have its own unit tests in `dev/scripts/devctl/tests/`.
2. Pass a calibration step: run against the full codebase, review output,
   tune thresholds before adding to any gate profile.
3. Have an explicit threshold owner who can adjust values post-launch.
4. Be registered in `script_catalog.py` and added to `AI_GUARD_CHECKS` in
   `check_support.py`.

### Guardrail Delivery Tracking

| Guardrail | Target Phase | Deliverable | Status |
|---|---|---|---|
| Freeze `writer/state.rs` growth | Phase 0 | `check_code_shape.py` PATH_POLICY_OVERRIDES + hotspot freeze for `writer/state.rs`, `prompt_occlusion.rs`, and `claude_prompt_detect.rs` | done |
| Absolute shape audit mode | Phase 0 | `check_code_shape.py --absolute` (~30 lines) | done |
| AI-guard in `ci` profile | Phase 0 | `check_profile.py` line 39: `with_ai_guard: True` | done |
| Workspace path-contract repair | Phase 0 | workflow triggers + `AGENTS.md` + `check_agents_contract.py` move to `rust/src/**` contract | done |
| Workspace path-contract gate | Phase 0 | extend `devctl path-audit` (or new check) to fail stale `src/**` contracts | done |
| Runtime-lane AI-guard enforcement | Phase 0 | runtime workflow on `rust/src/**` executes AI guards in commit-range mode | done |
| `devctl check` AI-guard ref propagation | Phase 0 | `check` command accepts `--since-ref/--head-ref` and forwards refs to `AI_GUARD_CHECKS` scripts | done |
| Dependency-policy CI gate (`cargo deny`) | Phase 0 | security/release lane enforces deny policy with explicit failure semantics | done |
| `check_code_shape.py` evaluator coverage | Phase 0 | dedicated unit tests for `_evaluate_shape` branch matrix | done |
| `check_agents_contract.py` dedicated coverage | Phase 0 | unit tests + contract-row migration to `rust/src/**` snippets | done |
| Clippy threshold tightening | Phase 0 | `clippy.toml`: `cognitive-complexity-threshold = 25`, `Cargo.toml`: `too_many_lines = "warn"` | done |
| Parameterized characterization tests | Phase 0.5 | `rstest` crate + matrix tests for preclear/redraw/gap-rows | done |
| Duplicate enum/type detector | Phase 1 | `check_duplicate_types.py` (~80 lines) | done |
| Structural complexity check | Phase 1 | `check_structural_complexity.py` (AI-guard integrated score + nesting/branch policy with temporary exception governance) | done |
| IDE/provider isolation check | Phase 0 (report), Phase 2 (block) | `check_ide_provider_isolation.py` (~100 lines) with staged rollout | done (blocking default + narrowed explicit allowlist) |
| Mixed host/provider conditional budget | Phase 0 | baseline artifact (`rg`-based) + non-regressive checkpoint tracking until isolation check blocks | done (`dev/reports/mp346/baselines/host_provider_mix_counts.txt`) |
| Compat matrix YAML + check | Phase 4 | `ide_provider_matrix.yaml` + `check_compat_matrix.py` | done |
| Naming consistency gate | Phase 4 | `check_naming_consistency.py` + `AI_GUARD_CHECKS` + tooling-control-plane lane | done |
| Workflow-shell hygiene gate | Phase 0 | `check_workflow_shell_hygiene.py` + `docs-check --strict-tooling` enforcement + bridge migration | done |
| devctl `compat-matrix` command | Phase 4 | `devctl/commands/compat_matrix.py` | done |
| General duplication audit | Phase 4 | `check_duplication_audit.py` periodic `jscpd` wrapper (`--run-jscpd` + freshness/threshold enforcement; not CI-blocking by default) | done |
| Host/provider contract completion pass | Phase 0.5 | source-mapped adapter method inventory + closure plan for unresolved render/cross-product decisions | done |

## Concrete Extraction Targets

| Priority | File | Function/Area | Current issue | Exit criteria |
|---|---|---|---|---|
| P0 | `rust/src/bin/voiceterm/writer/state.rs` | `handle_message` | oversized central branch hub for host+provider behavior | reduced to dispatch/orchestration; host/provider policy calls extracted |
| P0 | `rust/src/bin/voiceterm/writer/state.rs` | `should_preclear_bottom_rows` | 11-parameter branch-heavy policy | replaced by typed policy/config inputs |
| P0 | `rust/src/bin/voiceterm/runtime_compat.rs`, `writer/render.rs`, `banner.rs`, `theme/detect.rs` | terminal detection helpers | duplicated JetBrains/Cursor detection logic and direct env probing bypasses | one canonical host-detection implementation |
| P1 | `rust/src/ipc/protocol.rs`, `ipc/router.rs`, `ipc/session/state.rs` | provider enum/capabilities/job routing | codex/claude-only IPC model | provider model supports `gemini` capability parity |
| P1 | `rust/src/backend/mod.rs` + IPC/runtime boundary | `AiBackend` contract | trait covers startup patterns only | trait or adapter surface includes lifecycle + command/capability hooks |
| P2 | `rust/src/bin/voiceterm/event_loop.rs` | `should_emit_user_input_activity` | hardcoded `Claude && Cursor` behavior | host/provider behavior resolved via adapters |
| P1 | `rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs` | second God file (1143 lines) | own ANSI strip, debug helpers, JetBrains check, Claude-specific approval patterns | decompose: patterns behind provider adapter, shared utilities extracted |
| P1 | `rust/src/bin/voiceterm/prompt/claude_prompt_detect.rs` | provider-specific code with no adapter (930 lines) | hardcoded Claude patterns used by all backends via boolean guard | behind `PromptDetectionStrategy` trait; providers supply own patterns |
| P1 | `rust/src/bin/voiceterm/status_line/state.rs` | `claude_prompt_suppressed` field name | Claude brand leaked into 97+ locations in generic modules | rename to `prompt_suppressed` or `prompt_occlusion_active` |
| P1 | `rust/src/bin/voiceterm/theme/texture_profile.rs` | fourth terminal enum `TerminalId` (11 variants) | disconnected from TerminalHost/TerminalFamily, duplicates detection | unify with canonical TerminalHost or explicitly layer on top |
| P2 | 5 files | ANSI-stripping duplication | `strip.rs`, `prompt_occlusion.rs`, `ingest.rs`, `transcript_history.rs`, `toast.rs` each have own impl | one shared ANSI utility module |
| P2 | `rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs` + `writer/state.rs` + `terminal.rs` | debug helper duplication (3 copies) | `parse_debug_env_flag` + `debug_bytes_preview` + `claude_hud_debug_enabled` | shared debug utility module |
| P2 | `rust/src/bin/voiceterm/writer/state.rs` | `is_codex_backend()` / `is_claude_backend()` raw string matching | divergence risk from `runtime_compat::BackendFamily` | migrate to `BackendFamily` enum usage |
| P2 | `rust/src/bin/voiceterm/terminal.rs` | `reserved_rows_for_mode` has backend-specific branching | `BackendFamily::Codex` special-cased; `claude_prompt_suppressed` param name | route through provider adapter row-policy |
| P3 | `rust/src/bin/voiceterm/main.rs` | 530-line `main()` function | monolithic init/setup/run/shutdown | decompose into startup phases |
| P3 | `rust/src/bin/voiceterm/event_state.rs` | 29-field `EventLoopState` mega-struct | all `pub(crate)`, every handler gets `&mut EventLoopState` | narrow interface per consumer; group into sub-structs |
| P3 | `rust/src/bin/voiceterm/wake_word.rs` + `voice_control/navigation.rs` | hardcoded brand fuzzy-match tables | "kodak"->"codex", "cloud"->"claude" not driven by backend registry | drive from backend registry or config |
| P3 | 14 files (runtime tests/helpers) | duplicated env-var-locking helpers | each file creates its own `OnceLock<Mutex<()>>`; no shared lock = race risk and noisy duplication | shared test utility module with canonical env-lock |
| P3 | `rust/src/bin/voiceterm/event_loop/tests.rs` | test-side God file (`5918` lines) | prompt-suppression rename and adapter extraction will cause high-churn edits in one file | split into focused modules by behavior area (prompt occlusion, redraw policy, provider matrix) |

## Target Architecture Contracts

### Host Contract (IDE/runtime host)

```rust
pub trait HostAdapter {
    fn host(&self) -> TerminalHost;
    fn cursor_save_sequence(&self) -> &'static [u8];
    fn cursor_restore_sequence(&self) -> &'static [u8];
    fn supports_sync_output(&self) -> bool;
    fn supports_scroll_region(&self) -> bool;
    fn should_skip_banner(&self) -> bool;
    fn extra_gap_rows(&self) -> usize;
    fn hud_safety_gap_rows(&self) -> usize;
    fn banner_row_safety_margin(&self) -> usize;
    fn meter_update_floor_ms(&self) -> Option<u64>;
    fn typing_redraw_hold_ms(&self) -> Option<u64>;
    fn prompt_detector_mode(&self) -> PromptDetectorMode;
    fn output_redraw_policy(&self) -> OutputRedrawPolicy;
    fn preclear_policy(&self) -> PreclearPolicy;
    fn redraw_policy(&self) -> RedrawPolicy;
    fn scroll_policy(&self) -> ScrollPolicy;
    fn timing(&self) -> HostTimingConfig;
}
```

Methods added after second audit:

- `supports_scroll_region`: JetBrains/JediTerm skips DECSTBM entirely.
- `extra_gap_rows`: JetBrains=2, Cursor=12, Other=5.
- `hud_safety_gap_rows`: per-host HUD safety buffer.
- `banner_row_safety_margin`: JetBrains clips 1 col off single-row banners.
- `meter_update_floor_ms`: JetBrains has 90ms floor.
- `typing_redraw_hold_ms`: host-tunable non-urgent redraw defer window while
  user input is active.
- `prompt_detector_mode`: host-level selection for rolling/non-rolling prompt
  detector behavior (`prompt_occlusion.rs:426-440`).
- `output_redraw_policy`: host-level output-triggered full-banner redraw policy
  currently encoded inside `DisplayState::should_force_full_banner_redraw_on_output`.

### Provider Contract (CLI/provider behavior)

```rust
pub trait ProviderAdapter {
    fn provider(&self) -> Provider;
    fn prompt_pattern(&self) -> Option<&'static str>;
    fn thinking_pattern(&self) -> Option<&'static str>;
    fn supports_prompt_occlusion(&self) -> bool;
    fn reserved_row_policy(&self) -> ReservedRowPolicy;
    fn prompt_detection_strategy(&self) -> Option<Box<dyn PromptDetectionStrategy>>;
    fn auth_subcommand(&self) -> Option<&'static str>;
    fn build_args(&self, prompt: &str, cfg: &ProviderRunConfig) -> Vec<String>;
    fn start_job(&self, request: ProviderJobRequest) -> Result<ProviderJobHandle, ProviderError>;
    fn process_events(&self, handle: &mut ProviderJobHandle) -> Vec<IpcEvent>;
}
```

Methods added after second audit:

- `reserved_row_policy`: Codex keeps stable budget, Claude adds gap rows,
  Other collapses on suppression.
- `prompt_detection_strategy`: replaces hardcoded `ClaudePromptDetector`; each
  provider supplies its own pattern set (or None for no detection).
- `auth_subcommand`: auth flow hard-codes "login"; providers may differ.

### Cross-Product Resolver (host AND provider together)

Many behaviors depend on BOTH host and provider. These cannot be expressed by
either trait alone. Introduce a `RuntimeProfile` that pre-computes all
cross-product decisions at startup:

```rust
pub struct RuntimeProfile {
    pub startup_guard_enabled: bool,
    pub hud_border_override: Option<HudBorderStyle>,
    pub scroll_redraw_min_interval: Option<Duration>,
    pub idle_redraw_hold_ms: u64,
    pub preclear_strategy: PreclearStrategy,
    pub emit_user_input_activity: bool,
    pub input_repair_hold_ms: Option<u64>,
    pub cup_only_preclear: bool,
}

impl RuntimeProfile {
    pub fn new(host: &dyn HostAdapter, provider: &dyn ProviderAdapter) -> Self {
        // resolve ALL cross-product decisions here, not in handle_message
    }
}
```

Known cross-product decisions (10 identified):

| Decision | Host | Provider | Current location |
|---|---|---|---|
| Startup guard | JetBrains | Claude | `runtime_compat.rs:162` |
| HUD border override to None | JetBrains | Claude | `state.rs:1330` |
| Scroll redraw interval (320/150/900ms) | JetBrains/Cursor | Codex/Claude | `state.rs:618` |
| Idle-gated HUD redraw (500ms) | JetBrains | Claude | `state.rs:1183` |
| Aggressive HUD repair + input repair | Cursor | Claude | `state.rs:614,648,788,898,1034` |
| User input activity emission | Cursor | Claude | `event_loop.rs:629` |
| CUP-only preclear | JetBrains | Claude | `state.rs:654` |
| Treat CR bursts as scroll-like cadence | JetBrains | Codex | `state.rs:644-646` |
| Flash-sensitive scroll profile | JetBrains/Cursor | Codex/Claude | `state.rs:638-639` |
| Destructive clear immediate repaint | Cursor | Claude | `state.rs:797-816` |

Contract requirements:

1. Host adapters must not branch on provider-specific names.
2. Provider adapters must not read terminal-host env hints.
3. Cross-product decisions must be encoded in `RuntimeProfile`, constructed
   once at startup from `(HostAdapter, ProviderAdapter)`.
4. `WriterState` receives `RuntimeProfile` via dependency injection at
   construction time. No global `is_codex_backend()` calls inside
   `handle_message`.
5. Use the Strangler Fig pattern: during migration, `handle_message` can
   query both old compound booleans and new `RuntimeProfile` fields. Remove
   old booleans only after all policy paths route through the profile.

## Execution Checklist

### Global Gates (must stay true for every phase)

- [x] Create baseline checkpoint packet `CP-000` before first code extraction.
- [x] After each phase, run the full checkpoint bundle and publish a checkpoint
  packet under `dev/reports/mp346/checkpoints/<timestamp>/`.
- [x] Append one row to `Operator Checkpoint Log` with pass/fail and go/no-go.
- [x] Do not advance to next phase without explicit operator go decision.

### Phase 0: Ground Truth + Freeze

- [x] Capture current hotspots and branch complexity baselines for:
  - `writer/state.rs`
  - `event_loop.rs`
  - `runtime_compat.rs`
  - `ipc/router.rs`
- [x] Expand hotspot freeze scope to include secondary God files:
  - `event_loop/prompt_occlusion.rs`
  - `prompt/claude_prompt_detect.rs`
- [x] Add MP-346 hotspot baselines to `check_code_shape.py` non-growth policy.
- [x] Tighten AI-guard invocation path so CI/release lanes validate commit
  ranges (not only working-tree diffs), matching post-push `--since-ref`
  behavior across all AI-guard scripts, not only `check_code_shape.py`.
- [x] Add `devctl check` parser/runner support for `--since-ref/--head-ref`
  and propagate those refs to every `AI_GUARD_CHECKS` script command.
- [x] Repair stale runtime workspace contracts:
  - workflow path filters move from `src/**` -> `rust/src/**`
  - `AGENTS.md` task-router/CI lane map uses `rust/src/**`
  - `check_agents_contract.py` required router snippet updated accordingly
- [x] Repair stale governance automation path contracts:
  - `.github/dependabot.yml` Rust ecosystem directory moves from `/src` -> `/rust`
  - `.github/CODEOWNERS` Rust source ownership moves from `/src/` -> `/rust/src/`
- [x] Extend `devctl path-audit` (or add dedicated check) to fail stale
  workspace-root contracts (`src/**`, `working-directory: src`) outside
  allowlisted legacy release-formula contexts.
- [x] Align active-doc governance map + enforcement:
  - add missing source-of-truth map rows in `AGENTS.md` for `dev/active/memory_studio.md`
    and `dev/active/RUST_AUDIT_FINDINGS.md`
  - expand `check_active_plan_sync.py` `REQUIRED_REGISTRY_ROWS` coverage for active
    scopes currently not hard-required (`loop_chat_bridge`, `rust_workspace_layout_migration`,
    `naming_api_cohesion`, `ide_provider_modularization`, `phase2`)
  - expand `check_active_plan_sync.py` `SPEC_RANGE_PATHS` so all active `spec`
    docs receive MP-range parity checks (not only the original subset).
- [x] Add dependency-policy CI gate decision:
  - enforce `cargo deny` in CI/release, or
  - document equivalent policy path with explicit failure semantics.
- [x] Add CI baseline coverage hardening for contract stability:
  - add explicit MSRV verification job for `rust-version = "1.70"`,
  - add feature-mode matrix checks beyond `--all-features`,
  - add runtime validation on at least one macOS lane in addition to Ubuntu.
- [x] Add documentation compile gate in CI (`cargo doc --workspace --no-deps --all-features`)
  so doc drift is caught before merge.
- [x] Close current RustSec vulnerability drift in the runtime graph:
  - updated transitive `bytes` from `1.11.0` to patched `1.11.1`,
  - reran `cargo deny --manifest-path rust/Cargo.toml check advisories bans licenses sources`
    to verify advisories/license policy now passes under current deny config.
- [x] Add dedicated unit coverage for:
  - `check_code_shape.py` core `_evaluate_shape` logic.
  - `check_agents_contract.py` (including router snippet migration to `rust/src/**`).
- [x] Harden `check_rust_audit_patterns.py` signal quality:
  - remove stale legacy source-root fallbacks now that workspace root is `rust/src`,
  - add assumption validation so "all-zero aggregate" output is surfaced as
    stale-pattern drift, not silent success.
- [x] Harden `check_release_version_parity.py` resilience:
  - add explicit `.exists()` guards for release metadata files
    (`Cargo.toml`, `pyproject.toml`, app `Info.plist`) and return structured
    missing-file diagnostics instead of uncaught exceptions.
- [x] Extend `check_code_shape.py` to flag stale `PATH_POLICY_OVERRIDES` entries
  when a file remains below override soft-limit for the configured review window.
- [x] Extend `failure_triage.yml` workflow coverage to include missing high-impact lanes
  (`Swarm Run`, `publish_release_binaries`) and keep workflow-name parity with
  `.github/workflows/*.yml`.
- [x] Reconcile backend-support wording across user docs so Gemini status is consistent
  between `README.md`, `dev/ARCHITECTURE.md`, and `guides/CLI_FLAGS.md`.
- [x] Resolve governance tracker drift:
  - sync `MASTER_PLAN` multi-agent board statuses with current runbook ledger state,
  - resolve local `dev/BACKLOG.md` MP-ID collisions with canonical `MASTER_PLAN`
    scopes (or rename local backlog IDs to avoid tracker ambiguity).
- [x] Add cross-plan ownership gate in multi-agent runbook + `MASTER_PLAN`
  before touching shared hotspot files used by Theme/MP-267 scopes.
- [x] Freeze net-new host/provider cross-conditionals in hotspot files except
  for extraction refactors.
- [x] Capture baseline mixed-condition counts in hotspot files
  (`writer/state.rs`, `event_loop.rs`, `terminal.rs`) using a reproducible
  `rg` query and store artifact output under
  `dev/reports/mp346/baselines/host_provider_mix_counts.txt`.
- [x] Land `check_ide_provider_isolation.py` in report-only mode and attach its
  output to checkpoint packets before any Phase 1 extraction.

### Phase 0.5: Characterization Tests (safety net before refactoring)

Tests must exist BEFORE extraction, not after. This phase writes
characterization tests that lock in current behavior so Phases 1-3 can be
validated against the existing contract.

- [x] Write parameterized matrix tests for `should_preclear_bottom_rows` across
  all `(TerminalFamily, BackendFamily)` pairs.
- [x] Write parameterized matrix tests for `scroll_redraw_min_interval` across
  all pairs.
- [x] Write parameterized matrix tests for `force_redraw` triggers across all
  pairs.
- [x] Write parameterized tests for `reserved_rows_for_mode` across all pairs.
- [x] Write parameterized tests for gap-row defaults per host.
- [x] Use `rstest` crate (add to `Cargo.toml` dev-dependencies) for matrix
  parameterization.
- [x] Run adapter-contract completion inventory:
  - host render-policy method coverage (banner redraw, color capability,
    cursor/autowrap redraw controls)
  - provider/host cross-product policy coverage (reserved-row budgets and
    rolling/non-rolling prompt policy)
  - explicitly map current host/runtime decisions in:
    - `should_use_rolling_prompt_detector` (`prompt_occlusion.rs`)
    - `should_force_full_banner_redraw_on_output` (`writer/state.rs`)
    - `treat_cr_as_scroll`, `flash_sensitive_scroll_profile`,
      `destructive_clear_repaint` (`writer/state.rs`)
- [x] Verify all 9 host/provider combinations have at least one assertion
  covering preclear, redraw timing, and gap rows.
- [x] Add explicit input-ownership contract tests for terminal caret vs HUD focus:
  - define deterministic arrow-routing behavior for Codex and Claude across
    Cursor/JetBrains/Other hosts,
  - ensure users can always both edit text and reach HUD buttons without relying
  on accidental mode flips (for example `Ctrl+T` recovery),
  - cover `should_preserve_terminal_caret_navigation` and
  `hud_navigation_direction_from_arrow` behavior with focused regression tests.

#### Phase 0.5 Adapter-Contract Completion Inventory (2026-03-02)

Host render-policy method coverage:

| Policy surface | Current owner | Characterization evidence | Closure status |
|---|---|---|---|
| Banner redraw policy (`should_force_full_banner_redraw_on_output`) | `rust/src/bin/voiceterm/writer/state.rs` (`DisplayState::should_force_full_banner_redraw_on_output`) | `writer/state/tests.rs`: `non_scrolling_output_does_not_force_full_banner_redraw`, `scrolling_output_forces_full_banner_redraw_for_multi_row_hud`, `scrolling_output_forces_full_banner_redraw_for_single_row_hud` | mapped |
| Color capability policy | `rust/src/bin/voiceterm/color_mode.rs` (`ColorMode::detect`, `env_supports_truecolor_without_colorterm`) | `color_mode.rs` matrix/environment tests (`detect_terminal_capability_matrix_cases`, JetBrains/Cursor truecolor inference tests) | mapped |
| Cursor/autowrap redraw controls | `rust/src/bin/voiceterm/writer/render.rs` (`should_disable_autowrap_during_redraw`, redraw write/clear helpers) | `writer/render.rs` tests for banner/status write/clear behavior under host-family rendering paths | mapped |

Provider/host cross-product policy coverage:

| Decision | Current owner | Characterization evidence | Closure status |
|---|---|---|---|
| Reserved-row budgets (`reserved_rows_for_mode`) | `rust/src/bin/voiceterm/terminal.rs` | `terminal.rs`: `reserved_rows_for_mode_matrix_matches_host_provider_contract` (9 host/provider cells, suppressed + unsuppressed assertions) | mapped |
| Rolling vs non-rolling prompt policy (`should_use_rolling_prompt_detector`) | `rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs` | `event_loop/tests.rs`: non-rolling approval/suppression coverage via `install_prompt_rolling_override(false)` scenarios | mapped |
| Banner redraw policy decision (`should_force_full_banner_redraw_on_output`) | `rust/src/bin/voiceterm/writer/state.rs` | `writer/state/tests.rs` redraw behavior tests listed above | mapped |
| CR-as-scroll + flash-sensitive + destructive-clear decisions (`treat_cr_as_scroll`, `flash_sensitive_scroll_profile`, `destructive_clear_repaint`) | `rust/src/bin/voiceterm/writer/state.rs` | `writer/state/tests.rs`: `pty_output_may_scroll_rows_can_treat_carriage_return_as_scroll_for_codex_jetbrains`, scroll redraw matrix tests, destructive-clear detection tests + Cursor/Claude non-scroll redraw coverage | mapped |

9-combo assertion closure:

- Preclear matrix: `writer/state/tests.rs::should_preclear_bottom_rows_matrix_matches_host_provider_contract` (9 cells).
- Redraw timing matrix: `writer/state/tests.rs::scroll_redraw_interval_matrix_matches_host_provider_contract` + `force_scroll_redraw_trigger_matrix_respects_host_provider_profile` (9 cells).
- Gap rows matrix: `terminal.rs::reserved_rows_for_mode_matrix_matches_host_provider_contract` (9 cells).

### Phase 1: Canonical Host Detection

- [x] Define one canonical `TerminalHost` detection owner in
  `runtime_compat.rs`.
- [x] Replace duplicated detection implementations in:
  - [x] `writer/render.rs` (removed writer-local `TerminalFamily` enum;
    renderer now consumes canonical `TerminalHost` directly)
  - [x] `banner.rs` (deleted local `is_jetbrains_terminal()` and now routes
    through canonical `runtime_compat::is_jetbrains_terminal()`)
  - [x] `color_mode.rs` lines 74-95 (host truecolor inference now routes
    through canonical `runtime_compat::detect_terminal_host()`)
  - [x] `theme/detect.rs` (`is_warp_terminal` now consumes canonical host signal,
    not direct env probing)
  - [x] `texture_profile.rs` (`TerminalId` now layers on top of canonical
    `TerminalHost` detection for Cursor/JetBrains host routing)
- [x] Replace all `TerminalFamily` references in `state.rs` (30+ locations)
  with `TerminalHost`.
- [x] Define caching contract: canonical `detect_terminal_host()` returns a
  cached `OnceLock<TerminalHost>`. Tests use a thread-local override to inject
  test values without polluting the process-wide cache (follow existing
  `set_terminal_size_hook` pattern in `state.rs:97`).
- [x] Route all call sites to canonical host detection APIs.
- [x] Add regression tests for JetBrains/Cursor/Other environment fingerprints.

### Phase 1.5: Shared Utilities + Backend Detection Consolidation

Extract shared code before the big refactors to reduce diff noise and prevent
merge conflicts.

- [x] Extract `parse_debug_env_flag`, `debug_bytes_preview`,
  `claude_hud_debug_enabled` into `writer/debug.rs` or a shared `debug`
  module. Delete the 3 copies in `state.rs`, `prompt_occlusion.rs`,
  `terminal.rs`.
- [x] Replace `is_codex_backend()` / `is_claude_backend()` in `state.rs` (raw
  string-contains) with `runtime_compat::BackendFamily` enum usage.
- [x] Consolidate the 5 ANSI-stripping implementations into one shared utility
  module.
- [x] Define the `ProviderAdapter` trait signature (without full
  implementation) so Phase 2 can code against trait methods instead of
  backend-name strings.
- [x] Create shared test utility module for env-var locking (replace the 14
  independent `OnceLock<Mutex<()>>` helpers with one canonical lock used by
  runtime tests and helper modules).
- [x] Rename `claude_prompt_suppressed` to `prompt_suppressed` (or
  `prompt_occlusion_active`) across all 97+ references. This is a
  find-and-replace, not a behavioral change.

### Phase 2: Host Config + Policies

Highest-risk phase. Use atomic sub-steps with individual checkpoints.

- [x] **Step 2a** (safe, data-only): Extract host timing constants from
  `writer/state.rs` into typed `HostTimingConfig` keyed by `TerminalHost`.
  No logic change -- pure data extraction. Checkpoint here.
- [x] **Step 2b**: Extract `should_preclear_bottom_rows` into a
  `PreclearPolicy` that returns both the preclear decision AND the resulting
  flags (`pre_cleared`, `force_redraw_after_preclear`,
  `force_full_banner_redraw`). Checkpoint here.
- [x] **Step 2c**: Extract the scroll/non-scroll redraw decision block (lines
  741-858) into `RedrawPolicy` that consumes preclear outputs. Checkpoint
  here.
- [x] **Step 2d**: Extract `maybe_redraw_status` idle-gating into a separate
  timing module. Checkpoint here.
- [x] **Step 2e**: Reduce `handle_message` to: dispatch message type -> call
  policy pipeline -> apply state updates. Build `RuntimeProfile` cross-product
  resolver and inject via DI at `WriterState` construction. Final checkpoint.
  (complete: runtime-profile DI + dispatch/redraw decomposition landed with
  dedicated `writer/state/*` modules; `writer/state.rs` now 448 lines.)
- [x] **Step 2f**: Flip `check_ide_provider_isolation.py` from report-only to
  blocking mode for runtime files outside approved adapter/policy modules.
  Final checkpoint before Phase 3. (complete: blocking is now default;
  allowlist narrowed to explicit policy-owner files.)
- [x] **Step 2f.1**: Isolation allowlist burn-down + shape-budget reset
  checkpoint:
  - tighten `PATH_POLICY_OVERRIDES` to current decomposition reality:
    - lower `writer/state.rs` soft/hard limits from legacy freeze (`2750`) to
      a near-current budget (target <= `600` hard ceiling),
    - add explicit path budgets for new writer decomposition modules:
      `writer/state/dispatch.rs`, `writer/state/redraw.rs`,
      `writer/state/policy.rs` so large extracted modules cannot regrow
      unnoticed,
  - remove broad mixed-signal allowlist entries first:
    `event_loop.rs` and `terminal.rs` must exit explicit mixed-path allowlist
    before broader prefix burn-down,
  - narrow remaining allowlisted prefixes (`writer/`, `event_loop/`)
    module-by-module with checkpoint evidence for each removal. (complete:
    broad prefixes removed; explicit allowlist now only
    `runtime_compat.rs`, `writer/state/profile.rs`, `writer/timing.rs`.)
- [x] **Step 2f.2**: Function-shape guardrails (non-file-size) checkpoint:
  - implement function-length enforcement for dispatcher/pipeline hotspots
    (initially `writer/state/dispatch.rs`, `writer/state/redraw.rs`,
    `event_loop/prompt_occlusion.rs`),
  - wire guard into CI/runtime bundle so post-decomposition god-function drift
    fails fast,
  - publish temporary exception protocol (single-owner + expiry + follow-up MP
    item) for unavoidable outliers. (complete: path-scoped function policies
    landed in `code_shape_policy.py` with explicit owner/expiry/follow-up
    exception entries.)
- [x] After each sub-step: run checkpoint bundle + verify no regression in
  characterization tests from Phase 0.5. (complete: `CP-007` through `CP-013`
  checkpoint artifacts and bundle outcomes are recorded in the Operator
  Checkpoint Log.)

Rollback strategy: If step 2d breaks, revert to the 2c checkpoint, not to
Phase 1. Each sub-step must be independently revertable via `git revert`.

Feature flag option: consider `VOICETERM_USE_ADAPTER_POLICIES=1` env var to
run old and new code paths in parallel during validation.

### Phase 3: Provider Adapter Expansion

- [x] **Step 3a**: Introduce `PromptDetectionStrategy` trait and wire
  `claude_prompt_detect.rs` behind a Claude adapter-owned implementation while
  keeping a short-lived fallback shim for parity testing. (complete:
  `provider_adapter::build_prompt_occlusion_detector` now routes detector
  wiring through Claude adapter strategy ownership, with temporary legacy-shim
  parity fallback.)
- [x] **Step 3a.1**: Retire the prompt-detection legacy shim after parity
  validation. (complete:
  - no open parity regressions were introduced in `CP-014`/`CP-015`,
  - repo-wide runtime usage scan shows no shim symbol usage outside prior
    planning text,
  - planning/docs state now removes shim-symbol references so it is not
    advertised as active runtime policy.)
- [x] **Step 3b**: Decompose `event_loop/prompt_occlusion.rs` into provider-
  neutral core + provider strategy hooks; remove direct Claude-specific pattern
  logic from the event-loop module. (complete: prompt-occlusion signal parsing
  moved to prompt-owned modules (`prompt/occlusion_signals.rs` +
  `prompt/claude_prompt_detect/signals.rs`), `event_loop/prompt_occlusion.rs`
  now keeps runtime orchestration only with prompt-owned signal hooks, and
  absolute shape limits are back under policy (`prompt_occlusion.rs`=`679`,
  `claude_prompt_detect.rs`=`541`) with prompt + IPC regression suites green.)
- [x] **Step 3c**: Expand provider abstraction so IPC/runtime lifecycle routes
  through provider adapters (not codex/claude match arms in router/auth/session
  code). (complete: new `ipc/provider_lifecycle.rs` now owns provider lifecycle
  start/cancel/drain routing; router and session loop runtime now delegate to
  adapter helpers instead of direct codex/claude match arms; auth command
  selection/reset policy now routes through `Provider` lifecycle helpers.)
- [x] **Step 3d**: Reconcile backend registry and IPC provider model:
  - add `Gemini` support to `ipc::Provider` and capability emission if shipped,
    or
  - explicitly mark `Gemini` as non-IPC experimental with guardrails and docs.
    (complete via explicit non-IPC path: IPC provider selection/auth/override
    now rejects `gemini` with recoverable "overlay-only experimental" errors,
    startup env override no longer silently falls back, and IPC docs/env
    surfaces now state codex/claude-only provider support.)
- [x] **Step 3e**: Explicitly classify non-IPC backends (`aider`, `opencode`,
  `custom`) as overlay-only or promote them into the provider adapter surface;
  do not leave ambiguous partial support behavior. (complete via explicit
  non-IPC classification: provider resolution now recognizes these labels as
  overlay-only non-IPC backends with dedicated diagnostics, matrix validation
  requires explicit non-IPC modes, and docs now align on codex/claude-only IPC
  support.)
- [x] **Step 3f**: Replace codex/claude-only capability list in
  `ipc/session/state.rs::emit_capabilities` with adapter-derived values.
  (complete: capability labels now derive from backend-registry discovery via
  `Provider::ipc_supported()`/`ipc_capability_labels()` with codex/claude
  fallback retained and dedicated IPC regressions added.)
- [ ] **Step 3g (post-next-release backlog)**: Stabilize Gemini overlay
  behavior for `cursor` and `jetbrains` sessions where users still report
  startup/HUD flash artifacts:
  - preserve adapter ownership boundaries (no ad-hoc host+provider branching in
    non-adapter modules),
  - route any flash mitigation through typed runtime-profile/policy contracts,
  - attach checkpoint + matrix evidence for `Cursor + Gemini` and
    `JetBrains + Gemini` before closure.
- [ ] **Step 3h (post-next-release backlog)**: Investigate JetBrains + Claude
  intermittent overlay flash between normal HUD and help/settings surfaces
  during heavy command-output sessions (for example long Bash and web-search
  activity):
  - include duplicated bottom status-strip/HUD row artifacts observed after
    long output bursts followed by short user replies (for example `thanks`,
    `testing`) as part of the same JetBrains+Claude render-sync investigation,
  - treat current behavior as **non-regressive** versus the last release
    baseline unless new evidence shows otherwise,
  - keep release scope to documentation + matrix attestation (no risky late
    runtime rewrites),
  - after release, capture focused debug logs/screenshots and route fixes
    through adapter/runtime-profile ownership paths (no ad-hoc mixed
    host+provider conditionals).
- [x] **Step 3 sequencing gate (`CP-016`)**: Steps `3a.1`, `3b`, `3c`, `3e`, and
  `3f` are closed; release-scope manual matrix is complete for IDE cells
  (`4/4`: Cursor+Codex, Cursor+Claude, JetBrains+Codex, JetBrains+Claude),
  and post-next-release deferred cells (`Other + Claude`, `Other + Codex`,
  `Gemini baseline`) remain tracked as non-blocking backlog.
- [x] After each sub-step: run checkpoint bundle and record `CP-3x` artifact.
  (complete: `CP-014`, `CP-015`, and `CP-016` checkpoint packets are recorded
  in the Operator Checkpoint Log.)
- [x] Manual matrix policy for Phase 3 checkpoints:
  - rerun matrix when host/provider behavior changes,
  - if behavior is contract-equivalent and matrix is not rerun, explicitly
    cite the latest accepted matrix attestation in the checkpoint packet,
  - for current release-readiness closure, IDE release-scope matrix (`4/4`) is
    complete; deferred `Other`/`Gemini` cells are explicitly post-release
    backlog scope.

### Phase 4: Matrix + Tooling Gates

- [x] Kick off Phase-4 compatibility-governance scaffold immediately after
  Step 2f closure (do not defer to Phase 3 completion).
- [x] Add machine-readable matrix source:
  `dev/config/compat/ide_provider_matrix.yaml`.
- [x] Add matrix validator check:
  `python3 dev/scripts/checks/check_compat_matrix.py`.
- [x] Promote isolation check policy from Phase-2 blocking baseline to full CI
  governance (allowlist ownership + threshold owner + calibration evidence):
  `python3 dev/scripts/checks/check_ide_provider_isolation.py` (wired into
  `devctl check` AI-guard profile and documented in AGENTS/runtime bundles).
- [x] Add smoke harness:
  `python3 dev/scripts/checks/compat_matrix_smoke.py`.
- [x] Add `devctl compat-matrix` command for validate/report workflows.

### Phase 5: AntiGravity Decision Gate

- [x] Select defer path for AntiGravity:
  - move AntiGravity to deferred MP scope until concrete runtime host
    fingerprint evidence exists.
- [x] Update `MASTER_PLAN`, `INDEX`, compatibility matrix scope, and user docs
  accordingly.
- [ ] Post-next-release backlog intake before AntiGravity reactivation:
  - draft host fingerprint/detection contract requirements for AntiGravity,
  - define compatibility-test plan covering `codex`, `claude`, and `gemini`
    behavior expectations on the AntiGravity host path,
  - require evidence-backed readiness review before moving AntiGravity out of
    deferred scope.

### Phase 6: Governance + ADR Lock

- [x] Add ADR for host/provider boundary ownership and extension policy
  (`dev/adr/0035-host-provider-boundary-ownership.md`).
- [x] Add ADR for compatibility matrix governance and CI fail policy
  (`dev/adr/0036-compat-matrix-governance-ci-fail-policy.md`).
- [x] Close MP-346: all release-scope matrix gates (IDE-first 4/4) and
  non-regression checks pass; post-release backlog items (Steps 3g, 3h,
  Phase 5 AntiGravity intake) are explicitly tracked. Formal closure
  recorded 2026-03-05.

### Phase 7: Post-Release Coupling Remediation (MP-354)

Goal: eliminate the remaining high-blast-radius coupling that still causes
"fix one IDE, break another" behavior in writer dispatch/timing and startup.

- [x] Step 7a: Writer state ownership split.
  - Introduce adapter-owned state containers so impossible cross-host/backend
    fields cannot exist at runtime (`JetBrainsClaude`, `JetBrainsCodex`,
    `CursorClaude`, `Generic` ownership model).
  - Keep `WriterState` focused on shared runtime state (geometry, common timers,
    display state, channels), and move adapter-specific repair fields behind
    adapter-owned state.
- [x] Step 7b: PTY output pipeline decomposition.
  - Refactor `writer/state/dispatch_pty.rs::handle_pty_output` into explicit
    stages: `analyze -> preclear policy -> write -> redraw policy -> state updates`.
  - Replace ad-hoc local boolean preamble with typed analysis outputs so branch
    ownership is visible and testable.
- [x] Step 7c: Timing/policy de-tangling.
  - Update `writer/timing.rs::resolve_idle_redraw_timing` and
    `writer/state/policy.rs::RedrawPolicy::resolve` to consume typed runtime
    profile + adapter analysis inputs without re-deriving duplicate
    IDE/provider booleans.
  - Remove duplicated cross-product gating conditions where policy ownership is
    already encoded in runtime profile or adapter analysis.
- [x] Step 7d: Startup orchestration decomposition.
  - Split `main.rs::main` into startup phases (`load config`, `prepare runtime`,
    `build state`, `run`, `shutdown`) with focused helpers and explicit data
    handoff structs for startup dependencies.
  - Preserve startup behavior parity with characterization tests and checkpoint
    bundles after each slice.
- [x] Step 7e: Shared VAD engine factory.
  - Remove duplicated `create_vad_engine` implementations by introducing one
    shared owner (audio/voice boundary), then route voice + wake-word callers
    through the same factory.
- [x] Step 7f: Python guard dedup closure.
  - Remove repeated guard import bootstrap/fallback and shared helper
    duplication by consolidating into one reusable check bootstrap path.
  - Prioritize high-frequency guard scripts used by runtime/tooling bundles
    before broader Python cleanup items.

Phase-7 checkpoint contract (required after each step):

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop
python3 dev/scripts/checks/check_structural_complexity.py --since-ref origin/develop
python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations
cd rust && cargo test --bin voiceterm
```

Phase-7 risk add-ons (required when applicable):

1. Overlay/HUD/output behavior changes (`Step 7a`-`7c`):
   - `python3 dev/scripts/devctl.py check --profile ci`
   - `cd rust && cargo test --bin voiceterm`
2. Timing/latency-sensitive policy changes (`Step 7b`, `Step 7c`):
   - `python3 dev/scripts/devctl.py check --profile prepush`
   - `./dev/scripts/tests/measure_latency.sh --voice-only --synthetic`
   - `./dev/scripts/tests/measure_latency.sh --ci-guard`
3. Direct `cargo test` runs must be followed by:
   - `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel`
4. Manual runtime verification for release-scope IDE matrix (`Cursor+Codex`,
   `Cursor+Claude`, `JetBrains+Codex`, `JetBrains+Claude`) is required at
   minimum after `Step 7c` and `Step 7d` checkpoints.

Phase-7 exit criteria:

1. `handle_pty_output` no longer owns a broad IDE/provider boolean preamble.
2. Writer adapter-specific repair state no longer lives as unconditional fields
   on the shared state struct.
3. Idle redraw timing and redraw policy stop re-deriving duplicated
   IDE/provider booleans when profile/analysis already encode ownership.
4. `main.rs::main` is reduced to orchestration-only control flow with
   decomposed startup/shutdown helpers.
5. Duplicated VAD factory logic is fully removed.
6. Guard-script bootstrap/helper duplication is reduced through shared
   utilities without lowering check reliability.
7. All checkpoint packets and operator go/no-go decisions are recorded.

## Operator Checkpoint Log

| Checkpoint | Phase | Artifact path | Bundle status | Manual matrix status | Operator decision | Notes |
|---|---|---|---|---|---|---|
| `CP-000` | baseline | `dev/reports/mp346/checkpoints/20260302T032908Z-cp000/` | fail (`check_ci`, `rust_lint_debt_since_ref`) | pending (all 7 cells) | `no-go` | automated packet captured; manual matrix gate still required before phase advancement. |
| `CP-003` | phase-0 rerun | `dev/reports/mp346/checkpoints/20260302T042017Z-cp003/` | pass (all automated bundle commands) | pending (all 7 cells) | `no-go` | CP-000 blockers revalidated and cleared on branch-aware commit-range baseline (`origin/master`); legacy `origin/develop` lint-debt check still reports historical release-range debt. |
| `CP-004` | phase-0 phase-gate | `dev/reports/mp346/checkpoints/20260302T155409Z-cp004/` | pass (all automated bundle commands) | pending (all 7 cells) | `go (phase 0.5 only)` | explicit operator approval to start characterization tests; phase-1+ extraction/refactor remains blocked until manual matrix completion. |
| `CP-005` | phase-0.5 closure | `dev/reports/mp346/checkpoints/20260302T162839Z-cp005/` | pass (all automated bundle commands) | pending (all 7 cells) | `go (manual matrix execution)` | Phase-0.5 checklist closure verified; Phase-1+ extraction/refactor remains blocked until manual matrix completion. |
| `CP-006` | manual matrix attestation | `dev/reports/mp346/checkpoints/20260304T010010Z-cp006/` | not rerun (latest full bundle pass: `CP-005`) | baseline accepted (`5/7` validated; `Other + Claude` and `Other + Codex` intentionally sequenced post-cleanup) | `go (phase 1+ cleanup now)` | operator attestation recorded for `Cursor + Codex`, `Cursor + Claude`, `JetBrains + Codex`, `JetBrains + Claude`, and Gemini baseline; remaining `Other` host cells are a post-cleanup stabilization checkpoint, not a phase-1+ blocker. |
| `CP-007` | phase-2a host timing extraction | `dev/reports/mp346/checkpoints/20260304T113723Z-cp007/` | pass (all automated bundle commands) | not rerun (latest manual attestation: `CP-006`) | `go (phase 2b next)` | data-only host timing extraction checkpoint; `HostTimingConfig` now owns writer timing constants and validation bundle stayed green. |
| `CP-008` | phase-2b preclear policy extraction | `dev/reports/mp346/checkpoints/20260304T114813Z-cp008/` | pass (all automated bundle commands) | not rerun (latest manual attestation: `CP-006`) | `go (phase 2c next)` | extracted typed `PreclearPolicy`/`PreclearOutcome` in writer state so preclear decision + post-preclear flag outcomes are resolved in one policy path while preserving existing host/provider behavior. |
| `CP-009` | phase-2c redraw policy extraction | `dev/reports/mp346/checkpoints/20260304T121404Z-cp009/` | pass (all automated bundle commands) | not rerun (latest manual attestation: `CP-006`) | `go (phase 2d next)` | extracted typed `RedrawPolicy` in writer state so scroll/non-scroll/destructive-clear redraw decisions now consume `PreclearOutcome` through one policy contract while preserving existing host/provider behavior. |
| `CP-010` | phase-2d idle-gating timing extraction | `dev/reports/mp346/checkpoints/20260304T123641Z-cp010/` | pass (all automated bundle commands) | not rerun (latest manual attestation: `CP-006`) | `go (phase 2e next)` | extracted typed idle-gating timing policy in `writer/timing.rs` so `maybe_redraw_status` throttling/quiet-window/repair settle decisions are centralized while preserving existing host/provider behavior. |
| `CP-011` | phase-2e dispatch/runtime-profile extraction (partial) | `dev/reports/mp346/checkpoints/20260304T130908Z-cp011/` | pass (all automated bundle commands; `check_ci` rerun after dead-code fix) | not rerun (latest manual attestation: `CP-006`) | `hold (continue phase 2e)` | `WriterState` now resolves a typed `RuntimeProfile` at construction and routes PTY processing through explicit policy pipeline helpers, but `writer/state.rs` decomposition targets are still in progress. |
| `CP-012` | phase-2e dispatch/runtime-profile extraction (closure) | `dev/reports/mp346/checkpoints/20260304T133654Z-cp012/` | pass (all automated bundle commands) | not rerun (latest manual attestation: `CP-006`) | `go (phase 2f next)` | completed writer-state structural decomposition (`writer/state.rs` now 448 lines) with dedicated dispatch/redraw/profile/display/policy/chunk-analysis modules while preserving runtime validation parity. |
| `CP-013` | phase-2f/2f.1/2f.2 + phase-4 kickoff closure | `dev/reports/mp346/checkpoints/20260304T163911Z-cp013/` | pass (targeted guard/runtime/governance bundle commands) | not rerun (latest manual attestation: `CP-006`) | `go (phase 3 next)` | isolation guard is now blocking by default with narrowed allowlists, shape budgets reset to decomposition reality, function-size guardrails live with owner/expiry exceptions, and compatibility-matrix governance scaffold (`yaml` + check + smoke + `devctl compat-matrix`) is active. |
| `CP-014` | phase-3a prompt strategy wiring | `dev/reports/mp346/checkpoints/20260304T174948Z-cp014/` | pass (`check_ci` + runtime/docs/governance bundle commands) | not rerun (latest manual attestation: `CP-006`) | `go (phase 3b next)` | prompt detector construction now routes through provider adapters with Claude-owned `PromptDetectionStrategy`, while a temporary legacy-shim fallback remained available for parity checks at that checkpoint. |
| `CP-015` | phase-3d explicit non-IPC Gemini guardrails | `dev/reports/mp346/checkpoints/20260304T181236Z-cp015/` | pass (targeted IPC/docs/governance commands) | not rerun (latest manual attestation: `CP-006`) | `go (phase 3b next)` | Step-3d closed via explicit non-IPC path: IPC provider selection/auth/override now rejects `gemini` with recoverable errors, `VOICETERM_PROVIDER` unsupported overrides no longer silently fall through, and docs now state codex/claude-only IPC provider support. |
| `CP-016` | phase-3 continuation sync (post-shim retirement + IPC/prompt/backend sequencing) | `dev/reports/mp346/checkpoints/20260305T032253Z-cp016/` | pass (automated runtime/governance bundle rerun) | IDE release-scope manual matrix complete (`4/4`: Cursor+Codex pass, Cursor+Claude pass with non-regressive known issues, JetBrains+Codex pass, JetBrains+Claude pass); deferred post-release backlog cells: `Other + Claude`, `Other + Codex`, `Gemini baseline` | `go (release-scope matrix complete)` | Findings cleanup for runtime artifacts + startup provider diagnostics is complete and automated gates are green; release closure uses IDE-first gating and defers `other` host/Gemini follow-up to post-next-release backlog. |

## Scope Splitting Recommendation

This MP covers guardrail tooling, God-file decomposition, provider adapter
expansion, matrix tooling, and ADRs. Consider splitting into:

- **MP-346a**: Phase 0 + 0.5 + 1 (freeze, characterization tests, canonical
  host detection, immediate guardrails). Safety-net-first work.
- **MP-346b**: Phase 1.5 + 2 (shared utilities, `handle_message`
  decomposition, structural complexity checks). God-file decomposition.
- **MP-346c**: Phase 3 + 4 + 5 + 6 (provider adapter, matrix tooling,
  AntiGravity decision, ADRs). Provider-side and governance work.

Decision on whether to split is an operator/architect gate, not an agent
decision. Record the decision in the Operator Checkpoint Log.

## Definition of Done

MP-346 is complete only when all conditions below are true:

### Structural

1. `writer/state.rs` is no longer the combined host/provider decision hub.
   Measurable: `handle_message` is under 100 lines; all policy logic is in
   separate modules.
2. `writer/state.rs` is under 800 lines total (from current 2750).
3. Host detection exists in one canonical runtime module. Zero duplicate
   detection enums or functions.
4. Provider capability surface and IPC provider model are consistent, including
   explicit classification for non-IPC backends (`aider`, `opencode`,
   `custom`) as overlay-only or adapter-integrated.
5. `RuntimeProfile` cross-product resolver exists and is injected via DI.
6. `claude_prompt_suppressed` renamed to provider-neutral name.
7. `event_loop/prompt_occlusion.rs` and `prompt/claude_prompt_detect.rs` no
   longer encode provider-specific branching in generic event-loop paths;
   provider adapters own prompt strategy wiring.
8. Prompt-side hotspots are reduced (`prompt_occlusion.rs` <= 700 lines and
   `claude_prompt_detect.rs` <= 600 lines) or each remaining exception has an
   explicit temporary override + follow-up MP item.
9. Runtime test env locking uses one shared helper utility; ad-hoc
   `OnceLock<Mutex<()>>` helpers are removed from hotspot modules.

### Tooling

10. Compatibility matrix exists as machine-readable source and is CI-enforced.
11. Static checks prevent new mixed host/provider conditionals outside adapters.
12. All guardrail deliverables from the tracking table are shipped and green.
13. AI-guard checks run in the `ci` profile.
14. Runtime CI workflows + governance/task-router contracts no longer use stale
    `src/**` runtime path filters.
15. Workspace path-contract guard fails on stale runtime path tokens outside
    allowlisted legacy-release contexts.
16. AI-guard checks invoked by `devctl check` in CI/release lanes run in
    commit-range mode and analyze non-empty changed-file sets for runtime diffs.
17. `check_ide_provider_isolation.py` runs in report mode during Phase 0 and
    blocking mode in CI no later than Phase 2 completion.
18. Mixed host/provider conditional counts in hotspot files are captured per
    checkpoint and are non-regressive while extraction is in flight.

### Governance

19. ADR(s) documenting boundaries and ownership are merged.
20. Each new check script has its own unit tests, calibration evidence, and
    an explicit threshold owner.

### Testing

21. Release-scope test coverage and manual validation exist for IDE-first
    combinations (`cursor` + `jetbrains` crossed with `codex` + `claude`);
    deferred `other` host and `gemini` follow-up combinations are explicitly
    tracked in post-next-release backlog.
22. No function in the codebase exceeds the function-length budget (100 lines)
    without an explicit `PATH_POLICY_OVERRIDES` exception with a follow-up MP.
23. Maximum cyclomatic complexity per function is under 20 without exception.

## Progress Log

- 2026-03-07: MP-354 Python residual closure `P11 + P12`:
  - standardized tooling/check report timestamps on UTC by adding shared
    `utc_timestamp()` ownership in `dev/scripts/checks/check_bootstrap.py` and
    `dev/scripts/devctl/time_utils.py`, then routing local-time report emitters in
    `dev/scripts/checks/`, `dev/scripts/devctl/commands/`, and
    `dev/scripts/mutation/cli.py` to UTC/Z timestamps so JSON/markdown outputs no
    longer mix local wall-clock and UTC report metadata (`P11`),
  - replaced raw seconds-per-day literals with named `SECONDS_PER_DAY`
    constants in process-age/report-retention tooling paths
    (`dev/scripts/devctl/process_sweep.py`,
    `dev/scripts/devctl/commands/hygiene.py`,
    `dev/scripts/devctl/reports_retention.py`,
    `dev/scripts/checks/check_screenshot_integrity.py`) so age math is explicit
    and shared across the remaining runtime/tooling cleanup surface (`P12`),
  - initial strict-tooling reruns surfaced two governance follow-ups that were
    resolved in-scope: registered/documented `check_bootstrap.py` in
    `script_catalog.py` + `dev/scripts/README.md`, and moved the shared
    `utc_timestamp()` helper from `devctl/common.py` into dedicated
    `devctl/time_utils.py` when the working-tree shape guard flagged
    `common.py` growth over the soft limit,
  - added focused unit coverage in
    `dev/scripts/devctl/tests/test_check_bootstrap.py` so the new
    `check_bootstrap.py` catalog entry does not introduce fresh test-parity
    debt,
  - reran the MP-354 tooling checkpoint subset after docs sync to confirm the
    UTC timestamp sweep and seconds-per-day constant cleanup are green.
- 2026-03-07: MP-354 residual low-risk closure `R14 + R15 + R16 + R17`:
  - replaced hardcoded legacy UI accent colors in `rust/src/legacy_ui.rs` with
    named constants so color ownership is explicit and no longer buried as
    anonymous `Color::Rgb` literals (`R14`),
  - updated `banner::BannerConfig` known-domain fields to typed ownership
    (`Theme` + `Pipeline`) and removed startup-callsite string allocations in
    `main.rs` (`R15`),
  - removed repeated `terminal_host()` re-resolution inside
    `writer/render.rs` by resolving host family once per render/clear path and
    threading it through cursor-prefix/suffix helpers (`R16`),
  - reduced `#[cfg(test)]`/`#[cfg(not(test))]` accessor duplication in
    `theme/style_pack/state.rs` by introducing shared read/write helper owners
    for runtime style-pack and theme-file override state (`R17`),
  - reran focused legacy/banner/writer/theme style-pack tests plus full
    checkpoint/quick-sweep bundles with green results.
- 2026-03-07: MP-354 queued `R12 + R13 + R18` closure (input/wake-word low-risk dedup):
  - extracted control-byte parsing in `input/parser.rs` into
    `parse_control_byte_event` so `consume_bytes` no longer repeats
    `flush_pending + push` blocks for each control key event (`R12`),
  - added `WakeListener::try_join(self) -> Result<(), WakeListener>` in
    `wake_word.rs` and removed duplicated listener
    destructure/join/reconstruct logic from `reap_finished_listener` and
    `stop_listener` (`R13`),
  - replaced the repetitive send-intent suffix `matches!` matrix in
    `wake_word/matcher.rs` with `SEND_WORD_VARIANTS` +
    `SEND_SUFFIX_WORDS` lookup-driven logic while preserving existing
    `"son"` suffix behavior constraints (`R18`),
  - reran focused parser/wake tests plus full checkpoint/quick-sweep bundles
    with green results.
- 2026-03-07: MP-354 queued `R6 + R7 + R11` closure (style/theme mapping cleanup):
  - introduced a shared `GlyphTable` helper in `theme/mod.rs` and routed
    repeated HUD/overlay glyph selectors through table-owned resolution without
    behavior changes,
  - replaced repeated runtime override enum mapping blocks in
    `theme/style_pack/apply.rs` with macro-generated conversion impls plus a
    shared `apply_runtime_override` helper that preserves existing "only apply
    when override is present" semantics,
  - replaced repetitive `ThemeDefaultable` impl blocks in
    `theme/style_schema.rs` with one declarative macro invocation,
  - reran focused theme tests + `theme_studio_v2` feature-gated compile check
    and full checkpoint/quick-sweep bundles with green results.
- 2026-03-07: MP-354 queued `R8 + R9 + R10` closure (typed context +
  validator split + signal grouping):
  - updated `theme/rule_profile.rs::RuleEvalContext` to use typed runtime
    ownership (`BackendKind` + `ColorMode`) instead of stringly-typed backend
    and color-mode fields, while preserving condition-evaluation behavior in
    `theme/rule_profile/eval.rs`,
  - split `AppConfig::validate` range/path/model responsibilities in
    `rust/src/config/validation.rs` into focused helpers
    (`validate_voice_pipeline_bounds`, `canonicalize_paths`,
    `validate_whisper_config`) without changing validation contracts,
  - grouped prompt-occlusion chunk flags in
    `event_loop/prompt_occlusion/detection.rs` by introducing
    `ApprovalSignals` and `PromptContextSignals` under `OutputChunkSignals`,
    then updated coordinator wiring in `event_loop/prompt_occlusion.rs`,
  - reran focused config/prompt-occlusion tests plus `theme_studio_v2`
    feature-gated compile check and full checkpoint/quick-sweep bundles with
    green results.
- 2026-03-07: MP-354 Step 7f closure (Python guard dedup closure):
  - added shared guard bootstrap helper
    (`dev/scripts/checks/check_bootstrap.py`) to consolidate import fallback
    resolution and runtime error report emission (`emit_runtime_error`),
  - consolidated repeated guard helpers in `rust_guard_common.py`
    (`list_changed_paths`, `collect_rust_files`,
    `normalize_changed_rust_paths`) and migrated high-frequency guard scripts
    (`check_code_shape`, `check_duplicate_types`,
    `check_structural_complexity`, `check_rust_audit_patterns`,
    `check_rust_lint_debt`, `check_rust_best_practices`,
    `check_rust_runtime_panic_policy`, `check_rust_security_footguns`,
    `check_rust_test_shape`) to shared ownership,
  - reran focused guard-unit checks plus full Step-7 checkpoint and required
    post-direct-`cargo test` quick sweep with green results.
- 2026-03-07: MP-354 Step 7e closure (shared VAD engine factory):
  - introduced shared `audio::create_vad_engine` ownership in
    `rust/src/audio/vad.rs` and exported it via `rust/src/audio/mod.rs`,
  - removed duplicated local `create_vad_engine` implementations from
    `rust/src/voice.rs`, `rust/src/bin/voiceterm/wake_word/detector.rs`, and
    `rust/src/bin/latency_measurement.rs`, routing all three callers through the
    shared factory,
  - reran focused voice/wake-word/latency tests plus full Step-7 checkpoint and
    required post-direct-`cargo test` quick sweep with green results.
- 2026-03-07: MP-354 Step 7d closure (startup orchestration decomposition):
  - split `main.rs` startup flow into explicit phases (`load_config_phase`,
    `prepare_runtime_phase`, `build_state_phase`, `run_runtime_phase`,
    `shutdown_runtime_phase`) with typed handoff structs for backend/config,
    runtime inputs, and execution/runtime teardown ownership,
  - preserved startup behavior parity while resolving a Step-7d checkpoint
    `check_code_shape` finding by moving `main.rs` inline tests into dedicated
    `main_tests.rs`, keeping runtime logic unchanged and restoring file-shape
    compliance,
  - reran Step-7 checkpoint commands (CI profile, docs/governance sync, shape,
    structural complexity, IDE/provider isolation, direct `cargo test --bin
    voiceterm`, and required quick process sweep) with green results.
- 2026-03-07: MP-354 Step 7c closure (timing/policy de-tangling):
  - updated `writer/timing.rs::resolve_idle_redraw_timing` to consume typed
    runtime ownership (`RuntimeVariant`) instead of re-deriving JetBrains
    provider pairings from terminal/backend fields inside the timing resolver,
  - updated `writer/state/policy.rs::RedrawPolicy::resolve` to branch on typed
    runtime ownership (`RuntimeVariant`) while keeping adapter-analysis inputs
    explicit (`composer/destructive-clear/cursor-save` signals) and removing
    duplicate cross-product runtime booleans from policy context,
  - wired runtime variant ownership through writer profile/adapter wiring
    (`runtime_compat`, `writer/state/profile.rs`, `writer/state/adapter_state.rs`,
    `writer/state/dispatch_pty.rs`, `writer/state/redraw.rs`) without changing
    runtime behavior contracts,
  - refreshed writer timing/policy tests and reran full Step-7 checkpoint and
    timing risk add-on bundles with green results.
- 2026-03-07: MP-354 Step 7b closure (PTY output pipeline decomposition):
  - decomposed `writer/state/dispatch_pty.rs::handle_pty_output` into explicit
    typed stages (`analyze -> preclear -> write -> redraw policy -> state
    updates`) with stage-owned data handoff structs and focused helpers,
  - removed mixed local boolean preamble ownership from `handle_pty_output`
    while keeping adapter-owned state access behind writer adapter accessors,
  - preserved runtime behavior parity via writer-state characterization tests
    plus full runtime checkpoint reruns,
  - fixed `dev/scripts/tests/measure_latency.sh` empty-array expansion under
    `set -u` (`SKIP_STT_ARGS`/`VOICE_ONLY_ARGS`) so Step-7 risk latency gates
    execute reliably in voice-only/CI synthetic modes.
- 2026-03-07: MP-354 Step 7a closure (writer adapter state ownership split):
  - added adapter-owned writer repair state container ownership in
    `writer/state/adapter_state.rs` with explicit runtime variants
    (`JetBrainsClaude`, `JetBrainsCodex`, `CursorClaude`, `Generic`),
  - removed IDE/provider-specific repair fields from the shared `WriterState`
    struct and rerouted writer dispatch/redraw flows through adapter-owned
    state accessors without feature/behavior changes,
  - updated writer-state tests to validate the same repair/redraw behavior
    while using adapter-owned state ownership boundaries.
- 2026-03-07: MP-354 execution intake + plan hardening:
  - promoted post-release coupling/code-smell findings from backlog-only notes
    into executable `Phase 7` steps (`7a`-`7f`) with required checkpoint bundle
    and explicit exit criteria,
  - prioritized runtime-critical slices first (`WriterState` adapter ownership,
    `handle_pty_output` decomposition, startup decomposition, shared VAD
    factory), with Python guard dedup as a parallel follow-up track,
  - revalidated findings against current code shape and marked parser finding
    `P1` as conditional (split-owner parser modules are not direct copy-paste
    duplicates in current state),
  - tied ongoing execution authority to `MASTER_PLAN` via new active scope
    `MP-354` while retaining historical MP-346 closure evidence.
- 2026-03-05: Operator scope update for release-readiness closure:
  - manual closure matrix for this release is IDE-only (`4/4` required cells):
    `Cursor + Codex`, `Cursor + Claude`, `JetBrains + Codex`,
    `JetBrains + Claude`,
  - `Other + Claude`, `Other + Codex`, and `Gemini baseline` are now explicit
    post-next-release backlog items and non-blocking for current release
    closure.
- 2026-03-05: CP-016 manual matrix partial refresh recorded (operator local verification):
  - pass: `Cursor + Codex` startup/typing/scroll/send behavior remains aligned
    with the pre-change baseline,
  - pass (non-regressive known issues): `Cursor + Claude` remains workable for
    release; reported issues are the same as the last release baseline and are
    already tracked in `Step 3g` post-next-release backlog,
  - pass: `JetBrains + Codex` HUD stability under output/resize remained
    non-regressive versus the pre-change baseline,
  - pass: `JetBrains + Claude` approval/prompt visibility and redraw behavior
    remained non-regressive for release-readiness execution,
  - deferred post-next-release cells (non-blocking for release closure):
    `Other + Claude`, `Other + Codex`, and `Gemini` baseline.
- 2026-03-05: Backlog intake captured for post-next-release follow-up:
  - added explicit `Step 3g` to stabilize Gemini `cursor`/`jetbrains` flashing
    behavior under adapter/runtime-profile ownership rules,
  - added explicit `Step 3h` for JetBrains+Claude intermittent help/settings
    overlay flashing plus duplicated bottom status-strip artifacts during heavy
    output as a non-regressive, post-release follow-up investigation,
  - added explicit AntiGravity reactivation-readiness intake checklist with
    planned `codex`/`claude`/`gemini` compatibility-test design requirements
    before deferred-scope lift.
- 2026-03-01: Initial MP-346 plan created and wired into active docs.
- 2026-03-01: Plan rewritten with source-validated audit findings, concrete
  extraction targets, trait contracts, phased execution order, and explicit
  done criteria.
- 2026-03-01: Added regression-containment contract: per-slice checkpoint
  bundle, required manual host/provider matrix verification, stop-the-line
  criteria, and operator checkpoint log for go/no-go control.
- 2026-03-01: Reality checks recorded:
  - God-file concentration in `writer/state.rs` (`2750` LOC).
  - `handle_message` size (`882` LOC).
  - terminal-host detection duplication.
  - IPC/provider mismatch for Gemini.
  - no runtime AntiGravity footprint.
- 2026-03-01: Full guardrails gap analysis added. Audited all 16 check scripts,
  all devctl profiles, and all IDE/provider test coverage. Key findings:
  - 100% of checks are regex/line-count matchers; zero structural analysis.
  - No function-length, cyclomatic complexity, duplication, or coupling checks.
  - `writer/state.rs` not in `PATH_POLICY_OVERRIDES` (used default 40-line
    growth budget, allowing boil-the-frog growth to 2750 lines).
  - `ci` profile does not run AI-guard checks (PRs can pass CI without
    code-shape or best-practices validation).
  - 4 of 9 IDE/provider combinations have unit tests; 3 have zero coverage.
  - No parameterized matrix test exists.
  - 11 new guardrail deliverables defined and tracked per phase.
- 2026-03-01: Second-pass audit by 5 parallel agents. Major additions:
  - 13 additional missed hotspots: terminal detection in 5 files (not 3),
    `prompt_occlusion.rs` (1143 lines) as second God file,
    `claude_prompt_detect.rs` (930 lines) needs adapter trait,
    `claude_prompt_suppressed` leaked into 97+ locations, 5 ANSI-strip
    implementations, 3 debug-flag copies, 3 backend-detection copies,
    `main()` is 530 lines, `EventLoopState` 29-field mega-struct,
    `color_mode.rs` (838 lines) emerging God file, hardcoded wake-word
    brand tables, 6 duplicate test env-lock helpers.
  - Trait contract expanded: +6 `HostAdapter` methods (scroll region,
    gap rows, safety margin, meter floor), +3 `ProviderAdapter` methods
    (row policy, prompt detection strategy, auth subcommand). New
    `RuntimeProfile` cross-product resolver for 10 identified decisions.
  - Phase ordering restructured: added Phase 0.5 (characterization tests
    before refactoring), Phase 1.5 (shared utilities + backend detection
    consolidation). Phase 2 decomposed into 5 atomic sub-steps (2a-2e)
    with individual checkpoints. Parameterized tests moved from Phase 4
    to Phase 0.5.
  - Tooling strategy revised: use `rust-code-analysis-cli` instead of 3
    separate Python scripts. Use `rstest` crate. Use `jscpd` for general
    duplication. Net: 4 new Python files instead of 8+.
  - Manual verification expanded from 5 to 7 combinations (added
    Other+Claude and Other+Codex).
  - Definition of Done expanded with quantitative targets: `handle_message`
    under 100 lines, `writer/state.rs` under 800 lines, max cyclomatic
    complexity 20, max function length 100 lines.
  - Scope splitting recommendation added (MP-346a/b/c).
  - Strangler Fig and DI patterns explicitly named.
  - Meta-governance added for new check scripts (unit tests, calibration,
    threshold owner).
- 2026-03-01: Third-pass cross-check added additional systemic risks and
  corresponding deliverables:
  - Runtime CI workflows + policy docs still contain stale `src/**` trigger
    contracts despite `rust/` workspace migration.
  - `check_agents_contract.py` currently enforces the stale router row string,
    so governance must migrate in lockstep with workflow trigger fixes.
  - `devctl path-audit` currently cannot detect workspace-root contract drift
    (it only scans legacy check-script path rewrites).
  - Host adapter contract expanded with explicit `typing_redraw_hold_ms`.
  - Definition of Done now includes workspace path-contract correctness gates.
- 2026-03-02: User docs now publish explicit host IDE compatibility status
  (README + `guides/USAGE.md` canonical matrix, with Quick Start/Guides Index/
  Troubleshooting links) so Cursor, JetBrains, and AntiGravity support claims
  are explicit and unverified hosts are not implied as supported.
- 2026-03-02: Senior-architect audit triage merged into MP-346 as validated
  deltas:
  - Accepted: stale runtime workflow path-contract risk (`src/**`), missing
    dedicated unit coverage for `check_code_shape.py` core evaluator and
    `check_agents_contract.py`, dependency-policy gate hardening (`cargo deny`
    policy path), and cross-plan shared-file ownership gate before extraction.
  - Accepted with rewrite: adapter-contract completion pass added as a
    source-mapped inventory step (render-policy methods + unresolved
    cross-product decisions) rather than hard-coding method signatures up
    front.
  - Rejected as inaccurate/overstated for this repo state: "Linux CI absent"
    (Ubuntu runtime lane exists), "`serde_norway` unused" (used in
    `voice_macros.rs`), and "no unsafe governance at all" (governance exists,
    but targeted unsafe-comment cleanup remains valid follow-up work).
- 2026-03-02: Exhaustive cross-surface audit intake triage (validated against
  repo state before acceptance):
  - Accepted:
    - stale Rust path contracts in `.github/dependabot.yml` (`/src`) and
      `.github/CODEOWNERS` (`/src/`),
    - `check_active_plan_sync.py` under-enforces active docs beyond the current
      6 required rows,
    - `failure_triage.yml` is missing at least `Swarm Run` and
      `publish_release_binaries` in `workflow_run.workflows`,
    - existing RustSec evidence shows `bytes@1.11.0` vulnerability still present
      in lockfile/audit artifacts,
    - runtime CI baseline lacks explicit MSRV verification, feature-mode matrix
      coverage, and macOS runtime-lane validation (current runtime lane is
      Ubuntu-only),
    - CI has no explicit `cargo doc` compilation gate,
    - user docs drift on Gemini support wording (`README` vs
      `dev/ARCHITECTURE.md` and `guides/CLI_FLAGS.md`),
    - multi-agent tracker drift: `MASTER_PLAN` lane board remains all `planned`
      while runbook ledger records multiple `ready-for-review` updates,
    - local backlog tracker reuses MP IDs (`MP-148/149`) with semantics that
      conflict with `MASTER_PLAN`.
  - Rejected/rewritten as inaccurate for this repo:
    - "orphaned check scripts" (`check_agents_contract.py`,
      `check_cli_flags_parity.py`, and `check_screenshot_integrity.py`) are
      already wired in tooling/release workflows,
    - "`theme_studio_v2` dead feature flag" is false (feature-gated code exists),
    - "no IPC protocol serialization tests" is false (`rust/src/ipc/tests.rs`
      includes serde round-trip coverage),
    - "panic in PTY counters is production path" is false (guarded by
      `#[cfg(any(test, feature = \"mutants\"))]`),
    - "cross-platform CI absent" rewritten to "runtime lane is Ubuntu-only";
      release binary workflow already covers macOS + Linux.
- 2026-03-02: Fifth-pass execution-order audit added CI-signal hardening:
  - `devctl check` AI-guard scripts currently run without commit-range refs.
  - Phase 0 now requires `--since-ref/--head-ref` propagation through
    `devctl check` before flipping CI profile AI guards.
  - Secondary God files (`prompt_occlusion.rs`, `claude_prompt_detect.rs`) now
    share hotspot-freeze status with `writer/state.rs`.
- 2026-03-02: Sixth-pass maintainability audit tightened phase order and
  measurable coupling gates:
  - env-lock helper duplication revised from 6 to 14 files
    (`OnceLock<Mutex<()>>` scan).
  - test-side hotspot added: `event_loop/tests.rs` at 5918 lines.
  - isolation gate rollout changed to report-only in Phase 0, blocking by
    Phase 2 (instead of waiting until Phase 4).
  - Phase 3 decomposed into atomic provider/prompt sub-steps (`3a`-`3f`) so
    `PromptDetectionStrategy` and prompt-occlusion extraction are checkpointed.
  - Definition of Done expanded with prompt-hotspot size targets and checkpoint
    coupling-budget tracking.
- 2026-03-02: Seventh-pass independent Claude-audit triage (claim-by-claim
  validation against repo state):
  - Accepted:
    - adapter-contract scope still needed explicit mapping for host-level prompt
      detector mode/output redraw policy and 3 runtime cross-product decisions
      (`treat_cr_as_scroll`, `flash_sensitive_scroll_profile`,
      `destructive_clear_repaint`),
    - `check_rust_audit_patterns.py` currently reports all-zero aggregate
      metrics in this tree (`ok: true` with zero matches), so stale-pattern drift
      can pass silently,
    - `check_release_version_parity.py` reads app plist without `.exists()`
      guard, risking uncaught exceptions if bundle layout shifts,
    - `check_active_plan_sync.py` still needs `SPEC_RANGE_PATHS` expansion for
      active spec docs added after initial enforcement set,
    - `check_code_shape.py` has at least one stale path override
      (`event_loop/input_dispatch.rs` currently 555 lines vs override soft limit
      1200 / hard limit 1561).
  - Rejected/rewritten:
    - "Aider/OpenCode absent from plan" is stale: Phase 3 already includes
      explicit non-IPC backend classification for `aider` and `opencode`,
    - "wrong file paths for claude_prompt_detect/color_mode in plan" is stale in
      current file; current references resolve to actual paths.
- 2026-03-02: User-reported Codex/Claude keyboard UX conflict triage:
  - Current arrow routing in `event_loop/input_dispatch.rs` switches ownership
    between terminal-caret navigation and HUD button navigation using
    `insert_pending_send`, which can make one surface reachable while blocking
    the other depending on runtime state.
  - `Ctrl+T` (`ToggleSendMode`) is currently used by users as a recovery path to
    regain overlay control, but this is mode toggling rather than explicit
    focus ownership and is confusing in-session.
  - Added Phase 0.5 test requirement for deterministic input-ownership behavior
    and parity validation across Codex/Claude host combinations.
- 2026-03-02: Phase-0 execution kickoff completed with concrete guardrail
  hardening and CP-000 evidence capture:
  - landed `check_code_shape.py` hotspot freeze entries for
    `writer/state.rs`, `event_loop/prompt_occlusion.rs`, and
    `prompt/claude_prompt_detect.rs`,
  - added `check_code_shape.py --absolute` mode for repository-wide hard-limit
    scans,
  - enabled AI-guard in `devctl check --profile ci`,
  - added `devctl check` `--since-ref/--head-ref` parser/runner support and
    propagated commit-range refs to AI-guard scripts
    (`code_shape`, `rust_lint_debt`, `rust_best_practices`,
    `rust_audit_patterns`, `rust_security_footguns`),
  - added dedicated unit coverage for `_evaluate_shape` branch behavior in
    `test_check_code_shape_guidance.py`,
  - captured `CP-000` packet at
    `dev/reports/mp346/checkpoints/20260302T032908Z-cp000/`,
  - captured baseline mixed-condition artifact at
    `dev/reports/mp346/baselines/host_provider_mix_counts.txt`,
  - operator decision remains `no-go` pending manual matrix verification and
    failing bundle items.
- 2026-03-02: CP-000 blocker revalidation + phase-0 guardrail cleanup rerun:
  - replaced the temporary check-shape budget shortcut by extracting shared
    policy/config into `dev/scripts/checks/code_shape_policy.py`, returning
    `check_code_shape.py` to the existing soft-limit contract,
  - trimmed `dev/scripts/devctl/commands/check.py` back to the default Python
    shape budget without adding new path overrides,
  - updated `check_rust_lint_debt.py` to strip `#[cfg(test)]` blocks before
    counting debt metrics and added dedicated unit coverage in
    `dev/scripts/devctl/tests/test_check_rust_lint_debt.py`,
  - removed three runtime `unwrap()` calls in
    `rust/src/bin/voiceterm/writer/sanitize.rs`,
  - captured `CP-003` packet at
    `dev/reports/mp346/checkpoints/20260302T042017Z-cp003/` with all automated
    bundle checks passing on `master` against `origin/master`,
  - operator decision remains `no-go` pending completion of the required
    7-cell manual runtime matrix.
- 2026-03-02: Follow-up guardrail correctness pass:
  - tightened `check_rust_audit_patterns.py` runtime scoping to require true
    `rust/src/**` descendants (no prefix-collision matches such as
    `rust/src2/**`),
  - expanded guard unit tests to validate main-path behavior for
    `--since-ref/--head-ref` forwarding and stale-pattern warning emission from
    JSON report output,
  - landed `check_ide_provider_isolation.py` with report-only default mode,
    optional `--fail-on-violations` blocking mode, and dedicated unit tests,
  - extended `devctl path-audit` to detect stale workspace-contract tokens
    (`src/**`, `working-directory: src`, `directory: /src`, CODEOWNERS `/src/`)
    in workflow/governance path-contract surfaces,
  - expanded `check_active_plan_sync.py` required-row and spec-range coverage
    for active MP-346-linked docs (`loop_chat_bridge`,
    `rust_workspace_layout_migration`, `naming_api_cohesion`,
    `ide_provider_modularization`, `phase2`).
- 2026-03-02: Phase-0 tracker/state sync and post-review blocker cleanup:
  - reduced `check_active_plan_sync.py` back under the shape soft limit while
    keeping expanded `REQUIRED_REGISTRY_ROWS` + `SPEC_RANGE_PATHS` coverage,
  - documented `check_ide_provider_isolation.py` in `dev/scripts/README.md` to
    satisfy hygiene script-inventory requirements,
  - aligned `check_rust_audit_patterns.py` docs wording with current strict
    `rust/src` source-root behavior,
  - added dedicated unit coverage for `check_agents_contract.py`,
  - updated `devctl path-audit` aggregate reporting to expose both combined and
    unique checked-file counts after workspace-contract scan aggregation,
  - revalidated `check_code_shape`, `hygiene`, `path-audit`,
    `check_active_plan_sync`, and `docs-check --strict-tooling` as green.
- 2026-03-02: Backend-support wording parity cleanup:
  - aligned user docs so Gemini status now consistently reads
    "experimental (currently not working)" across `README.md`,
    `guides/USAGE.md`, `dev/ARCHITECTURE.md`, and `guides/CLI_FLAGS.md`.
- 2026-03-02: CI baseline hardening follow-up:
  - added a documentation compile gate to `rust_ci.yml`
    (`cargo doc --workspace --no-deps --all-features`) and synced workflow
    docs in `.github/workflows/README.md`.
- 2026-03-02: Dependency-policy gate decision closed:
  - selected the enforce path (not documentation-only) by wiring
    `cargo deny --manifest-path rust/Cargo.toml check advisories bans licenses sources`
    into both `security_guard.yml` and `release_preflight.yml`,
  - expanded `security_guard.yml` path triggers to include `rust/deny.toml`,
  - updated `.github/workflows/README.md` workflow summaries so the gate is
    visible in plain-language release/security lane docs.
- 2026-03-02: Dependency-policy local remediation closure:
  - updated `rust/Cargo.lock` transitive `bytes` to `1.11.1` to close
    `RUSTSEC-2026-0007`,
  - updated `rust/deny.toml` with crate-scoped license exceptions
    (`unicode-ident` `Unicode-3.0`, `whisper-rs` + `whisper-rs-sys` `Unlicense`)
    and explicit advisory ignore for `RUSTSEC-2024-0436` (`paste`, no safe
    upgrade available),
  - reran `cargo deny --manifest-path rust/Cargo.toml check advisories bans licenses sources`
    locally with result: `advisories ok, bans ok, licenses ok, sources ok`.
- 2026-03-02: Phase-0 governance/tooling gate closure pass:
  - captured hotspot size + branch-site baseline artifact at
    `dev/reports/mp346/baselines/hotspot_branch_complexity_baseline.txt`
    covering `writer/state.rs`, `event_loop.rs`, `runtime_compat.rs`, and
    `ipc/router.rs`,
  - expanded `.github/workflows/rust_ci.yml` with explicit MSRV validation
    (`1.70.0`), feature-mode matrix checks (`default`, `--no-default-features`),
    and macOS runtime smoke validation in addition to Ubuntu,
  - extended `.github/workflows/failure_triage.yml` watchlist with
    `Swarm Run` and `publish_release_binaries`,
  - extended `check_code_shape.py` with stale-override review-window detection
    (`--stale-override-review-window-days`) and removed stale override entries
    for `event_loop/input_dispatch.rs` and `status_line/buttons.rs`,
  - resolved tracker drift by syncing `MASTER_PLAN` lane statuses with runbook
    ledger state for `AGENT-1..3` and renaming local `dev/BACKLOG.md` IDs to
    `LB-*` to avoid canonical `MP-*` collisions,
  - added explicit cross-plan shared-hotspot ownership + conditional-freeze
    governance in the merged markdown-swarm plan in `review_channel.md` and mirrored
    the gate in `MASTER_PLAN` branch-guard policy.
- 2026-03-02: Phase-0 checkpoint/go decision closure:
  - captured `CP-004` packet at
    `dev/reports/mp346/checkpoints/20260302T155409Z-cp004/` with full
    checkpoint bundle pass on `origin/develop` baseline,
  - recorded explicit phase-advance decision as `go (phase 0.5 only)` so
    characterization test work can proceed,
  - retained `no-go` for phase-1+ extraction/refactor until the required
    7-cell manual runtime matrix is completed and attached.
- 2026-03-02: Phase-0.5 characterization kickoff (matrix + input ownership):
  - added `rstest` (`0.18`) to `rust/Cargo.toml` dev-dependencies for matrix
    parameterization,
  - added 9-way `(TerminalFamily, BackendFamily)` matrix characterization tests
    in dedicated `writer/state/tests.rs` (wired via `state.rs:#[cfg(test)] mod tests;`)
    for `should_preclear_bottom_rows`,
    `scroll_redraw_min_interval`, and force-redraw trigger timing behavior,
  - added focused input-ownership contract tests in
    `event_loop/input_dispatch.rs` for
    `should_preserve_terminal_caret_navigation` +
    `hud_navigation_direction_from_arrow`, including Codex/Claude coverage
    across Cursor/JetBrains/Other host matrix labels,
  - validated with `cd rust && cargo test --bin voiceterm` (`1387` passed).
- 2026-03-02: Phase-0.5 characterization closure pass (remaining 4 checklist items):
  - added host/provider matrix assertions in `terminal.rs` for
    `reserved_rows_for_mode` across all 9 host/provider pairs (including
    suppressed and unsuppressed prompt states),
  - converted runtime gap-row default checks to parameterized host-default
    tests in `runtime_compat.rs` (`parse_claude_extra_gap_rows`,
    `parse_hud_safety_gap_rows`),
  - completed and recorded the adapter-contract completion inventory in this
    plan (host render-policy coverage + cross-product decision mapping),
  - closed explicit 9-combo assertion evidence for preclear, redraw timing, and
    gap-row behaviors.
- 2026-03-02: CP-005 packet capture for Phase-0.5 closure:
  - captured `CP-005` packet at
    `dev/reports/mp346/checkpoints/20260302T162839Z-cp005/`,
  - automated checkpoint bundle status: all pass (`check_ci`,
    `docs_check_strict_tooling`, `active_plan_sync`, `multi_agent_sync`,
    `code_shape_since_ref`, `rust_lint_debt_since_ref`,
    `rust_best_practices_since_ref`, `cargo_test_bin_voiceterm`),
  - operator decision updated to `go (manual matrix execution)` with retained
    `no-go` for phase-1+ extraction/refactor until the 7-cell manual runtime
    matrix evidence is attached.
- 2026-03-04: CP-006 manual matrix attestation recorded from operator
  validation evidence:
  - pass: `Cursor + Codex`, `Cursor + Claude`, `JetBrains + Codex`,
    `JetBrains + Claude`,
  - pass (baseline accepted): `Gemini` baseline path,
  - intentionally sequenced post-cleanup: `Other + Claude`, `Other + Codex`,
  - operator decision updated to `go (phase 1+ cleanup now)` for
    cleanup/refactor work; `Other` host cells move to post-cleanup
    stabilization validation (non-blocking for current phase advancement).
- 2026-03-04: Phase-1 incremental cleanup slice (status-line/runtime host-policy
  boundary):
  - moved status-line JetBrains+Claude single-line fallback branching behind
    canonical `runtime_compat` helper
    (`should_force_single_line_full_hud_for_env`) so
    `status_line/layout.rs` and `status_line/buttons.rs` no longer compose
    host+provider checks inline,
  - aligned writer-side host detection ownership by routing
    `writer/render.rs` terminal-family detection through canonical
    `runtime_compat::detect_terminal_host()` mapping and removing duplicate
    host-sniffing helpers from render,
  - retained existing rendering semantics (DEC cursor save/restore rules,
    JetBrains-specific scroll-region bypass, and full-HUD single-line fallback
    behavior) with targeted runtime tests.
- 2026-03-04: Phase-1 incremental cleanup slice (writer host-enum unification):
  - removed `writer/render.rs` `TerminalFamily` enum and switched renderer
    policy branches to canonical `TerminalHost`,
  - migrated `writer/state.rs` host-policy checks from `TerminalFamily` to
    `TerminalHost` across runtime paths (including redraw/preclear/timing
    matrix logic) while preserving current behavior,
  - updated writer/state characterization coverage to use canonical host enums
    and reran writer-targeted tests plus `cargo test --bin voiceterm` for
    regression containment.
- 2026-03-04: MP-346 runtime checkpoint rerun for this cleanup slice:
  - `bundle.runtime` command set executed and green (including
    `devctl check --profile ci`, docs/hygiene/sync guards, parity checks,
    markdownlint, and root guard scan),
  - HUD/runtime risk add-on executed and green:
    `cd rust && cargo test --bin voiceterm`,
  - docs governance gate required user-facing evidence for runtime edits, so
    this slice now records an `Unreleased` changelog entry plus
    `guides/USAGE.md` IDE-compatibility clarification while keeping runtime
    behavior unchanged.
- 2026-03-04: Phase-1 incremental cleanup slice (banner/color/theme host
  routing):
  - removed duplicated banner host detection by deleting local
    `banner.rs::is_jetbrains_terminal` and routing skip policy to
    `runtime_compat::is_jetbrains_terminal`,
  - switched color truecolor inference to canonical host routing
    (`runtime_compat::detect_terminal_host`) while preserving non-host
    terminal-program hints (`vscode`, `wezterm`, `iterm`, `warp`),
  - updated `theme/detect.rs` so Warp checks now honor canonical host
    precedence (`JetBrains`/`Cursor` short-circuit before Warp fallback),
  - expanded regression coverage for JetBrains/Cursor/Other host fingerprints
    in banner/color/theme tests.
- 2026-03-04: Phase-1 incremental cleanup slice (texture-profile host layering):
  - routed `theme/texture_profile.rs` host identification through canonical
    `runtime_compat::detect_terminal_host()` first, so Cursor/JetBrains mapping
    is owned by one source of truth,
  - reduced texture-profile env detection to non-host capability IDs
    (`kitty`/`iterm`/`wezterm`/`warp`/etc.) while preserving existing
    `KITTY_WINDOW_ID` and `ITERM_SESSION_ID` fallback behavior,
  - added dedicated texture-profile regressions for host precedence and
    non-host fallback paths.
- 2026-03-04: Phase-1 incremental cleanup slice (canonical host cache
  contract):
  - moved terminal host fingerprint parsing into
    `runtime_compat::detect_terminal_host_from_env` and made
    `runtime_compat::detect_terminal_host` the canonical cached owner
    (`OnceLock<TerminalHost>` in runtime builds),
  - added a thread-local test override hook
    (`runtime_compat::set_terminal_host_override`) with reset scoping around
    env-based assertions so tests can inject deterministic host values without
    polluting cache ownership semantics,
  - removed writer-local host cache duplication in `writer/render.rs` so all
    host cache ownership routes through `runtime_compat`.
- 2026-03-04: Phase-1 follow-up hardening (panic-safe host override reset):
  - replaced test helper override scoping with a drop-guard pattern in
    `runtime_compat` tests so thread-local host overrides restore on both
    normal return and unwind,
  - added regression coverage that intentionally panics inside
    `with_terminal_host_override` and asserts host detection returns to the
    prior env-derived value after unwind.
- 2026-03-04: Phase-1.5 incremental cleanup slice (shared HUD debug helpers):
  - extracted canonical HUD debug helpers into shared
    `hud_debug` module (`parse_debug_env_flag`, `claude_hud_debug_enabled`,
    `debug_bytes_preview`),
  - removed duplicated helper implementations from `writer/state.rs`,
    `event_loop/prompt_occlusion.rs`, and `terminal.rs`,
  - rerouted runtime HUD anomaly/log preview call sites to shared helpers
    without behavior changes to prompt-occlusion or writer policies.
- 2026-03-04: Phase-1.5 incremental cleanup slice (BackendFamily routing in
  writer state):
  - removed raw backend-label substring parsing from `writer/state.rs`,
  - switched `is_codex_backend()` / `is_claude_backend()` to resolve through
    canonical `runtime_compat::backend_family_from_env()` +
    `BackendFamily` enum matching,
  - reran full runtime test suite to confirm no behavior regression.
- 2026-03-04: Phase-1.5 incremental cleanup slice (provider adapter signature):
  - added `provider_adapter.rs` contract module with signature-only
    definitions for `ProviderAdapter`, `PromptDetectionStrategy`,
    `ProviderId`, `ReservedRowPolicy`, and `ProviderRunConfig`,
  - registered the module in `main.rs` so later phase extraction can wire
    runtime/provider paths against shared trait contracts,
  - added focused contract tests and documented a temporary module-level
    `dead_code` allowance because this phase intentionally lands signatures
    before runtime wiring in Phase 2/3.
- 2026-03-04: Phase-1.5 closure slice (ANSI utility + env-lock utility +
  neutral suppression naming):
  - added shared `ansi` utility module and rerouted ANSI stripping in
    `prompt/strip.rs`, `event_loop/prompt_occlusion.rs`, and
    `memory/ingest.rs`, plus test-side strip helpers in
    `transcript_history.rs` and `toast.rs`,
  - added shared test-only `test_env` utility module (`env_lock`,
    `with_env_lock`) and replaced the duplicated env-lock helpers across
    runtime test modules with one canonical lock owner,
  - renamed `claude_prompt_suppressed` to provider-neutral
    `prompt_suppressed` across runtime modules and tests,
  - reran full runtime validation (`cargo test --bin voiceterm`) and
    `bundle.runtime` checks green after the closure slice.
- 2026-03-04: Phase-2a data-only host timing extraction:
  - added canonical `runtime_compat::HostTimingConfig` keyed by
    `TerminalHost` with typed duration helpers for host timing surfaces
    (preclear cadence, scroll-redraw cadence, idle holds, typing holds, and
    JetBrains/Cursor Claude repair windows),
  - replaced writer-side hardcoded timing constants in runtime paths with
    `HostTimingConfig` lookups while preserving behavior and existing
    characterization expectations,
  - kept timing resolution derived from `terminal_family` so runtime/tests do
    not drift if host state is overridden during harness setup,
  - validation: `python3 dev/scripts/devctl.py check --profile ci`,
    `python3 dev/scripts/devctl.py docs-check --user-facing`,
    `python3 dev/scripts/devctl.py hygiene`,
    `python3 dev/scripts/checks/check_active_plan_sync.py`,
    `python3 dev/scripts/checks/check_multi_agent_sync.py`,
    `python3 dev/scripts/checks/check_cli_flags_parity.py`,
    `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`,
    `python3 dev/scripts/checks/check_code_shape.py`,
    `python3 dev/scripts/checks/check_rust_lint_debt.py`,
    `python3 dev/scripts/checks/check_rust_best_practices.py`,
    `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`,
    `find . -maxdepth 1 -type f -name '--*'`,
    `cd rust && cargo test --bin voiceterm`.
- 2026-03-04: Phase-2b preclear policy extraction:
  - added typed `PreclearPolicy`/`PreclearOutcome` in
    `writer/state.rs` so preclear decisioning and post-preclear redraw flags
    (`pre_cleared`, `force_redraw_after_preclear`,
    `force_full_banner_redraw`) are resolved through one policy contract,
  - refactored `WriterMessage::PtyOutput` preclear path to consume policy
    outputs instead of mutating preclear flags inline,
  - added focused policy coverage in `writer/state/tests.rs` for
    Cursor+Claude immediate redraw flags, JetBrains+Claude resize-repair
    preclear flags, and the no-preclear outcome gate,
  - validation: `python3 dev/scripts/devctl.py check --profile ci`,
    `python3 dev/scripts/devctl.py docs-check --user-facing`,
    `python3 dev/scripts/devctl.py hygiene`,
    `python3 dev/scripts/checks/check_active_plan_sync.py`,
    `python3 dev/scripts/checks/check_multi_agent_sync.py`,
    `python3 dev/scripts/checks/check_cli_flags_parity.py`,
    `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`,
    `python3 dev/scripts/checks/check_code_shape.py`,
    `python3 dev/scripts/checks/check_rust_lint_debt.py`,
    `python3 dev/scripts/checks/check_rust_best_practices.py`,
    `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`,
    `find . -maxdepth 1 -type f -name '--*'`,
    `cd rust && cargo test --bin voiceterm`.
- 2026-03-04: Phase-2c redraw policy extraction:
  - added typed `RedrawPolicyContext`/`RedrawPolicy` in `writer/state.rs`
    so output-triggered redraw decisions (scroll cadence, non-scroll
    cursor-line mutation, destructive-clear recovery, and host/provider
    immediate-vs-idle redraw routing) are resolved through one policy contract
    that consumes `PreclearOutcome`,
  - refactored `WriterMessage::PtyOutput` redraw decision path to consume
    `RedrawPolicy` outputs instead of mutating redraw flags inline,
  - added focused policy coverage in `writer/state/tests.rs` for
    JetBrains+Claude idle-gated scroll redraw behavior, Cursor+Claude
    non-scroll immediate redraw forcing, JetBrains+Claude destructive-clear
    deferred repair arming, and Codex+JetBrains preclear-outcome redraw
    triggering,
  - validation: `python3 dev/scripts/devctl.py check --profile ci`,
    `python3 dev/scripts/devctl.py docs-check --user-facing`,
    `python3 dev/scripts/devctl.py hygiene`,
    `python3 dev/scripts/checks/check_active_plan_sync.py`,
    `python3 dev/scripts/checks/check_multi_agent_sync.py`,
    `python3 dev/scripts/checks/check_cli_flags_parity.py`,
    `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`,
    `python3 dev/scripts/checks/check_code_shape.py`,
    `python3 dev/scripts/checks/check_rust_lint_debt.py`,
    `python3 dev/scripts/checks/check_rust_best_practices.py`,
    `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`,
    `find . -maxdepth 1 -type f -name '--*'`,
    `cd rust && cargo test --bin voiceterm`.
- 2026-03-04: Phase-2d idle-gating timing extraction:
  - added dedicated `writer/timing.rs` policy module
    (`IdleRedrawTimingContext` + `resolve_idle_redraw_timing`) and moved
    non-urgent typing hold plus JetBrains idle/repair gating decisions out of
    `writer/state.rs`,
  - refactored `maybe_redraw_status` to consume timing policy outputs
    (`defer_redraw`, `clear_cursor_restore_settle_until`) while preserving
    existing redraw side effects and backend-specific guards,
  - added focused timing policy tests in `writer/timing.rs` for
    JetBrains+Claude idle hold selection, JetBrains+Codex scroll idle gating,
    priority max-wait behavior, composer quiet-window gating, and expired
    cursor-restore settle-window clearing,
  - validation: `python3 dev/scripts/devctl.py check --profile ci`,
    `python3 dev/scripts/devctl.py docs-check --user-facing`,
    `python3 dev/scripts/devctl.py hygiene`,
    `python3 dev/scripts/checks/check_active_plan_sync.py`,
    `python3 dev/scripts/checks/check_multi_agent_sync.py`,
    `python3 dev/scripts/checks/check_cli_flags_parity.py`,
    `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`,
    `python3 dev/scripts/checks/check_code_shape.py`,
    `python3 dev/scripts/checks/check_rust_lint_debt.py`,
    `python3 dev/scripts/checks/check_rust_best_practices.py`,
    `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`,
    `find . -maxdepth 1 -type f -name '--*'`,
    `cd rust && cargo test --bin voiceterm`.
- 2026-03-04: Phase-2e message-dispatch + runtime-profile extraction (partial):
  - introduced typed `RuntimeProfile` cross-product resolver in
    `writer/state.rs` and injected it via `WriterState` construction (`new` ->
    `with_runtime_profile`), replacing runtime env lookups inside writer
    handling paths with injected profile fields,
  - reduced `handle_message` to dispatch-only (`handle_message` ->
    `dispatch_message`) and refactored PTY handling to call explicit
    preclear/redraw policy pipeline helpers plus dedicated policy-outcome state
    application helpers (`run_preclear_policy_pipeline`,
    `run_redraw_policy_pipeline`, `apply_preclear_outcome`,
    `apply_redraw_policy_outcome`),
  - added runtime-profile matrix coverage in `writer/state/tests.rs` and
    updated writer-state tests to use runtime-profile host override helper
    (`set_terminal_family_for_tests`) so injected profile behavior is covered
    without environment re-probing inside `handle_message`,
  - validation: `python3 dev/scripts/devctl.py check --profile ci`,
    `python3 dev/scripts/devctl.py docs-check --user-facing`,
    `python3 dev/scripts/devctl.py hygiene`,
    `python3 dev/scripts/checks/check_active_plan_sync.py`,
    `python3 dev/scripts/checks/check_multi_agent_sync.py`,
    `python3 dev/scripts/checks/check_cli_flags_parity.py`,
    `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`,
    `python3 dev/scripts/checks/check_code_shape.py`,
    `python3 dev/scripts/checks/check_rust_lint_debt.py`,
    `python3 dev/scripts/checks/check_rust_best_practices.py`,
    `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`,
    `find . -maxdepth 1 -type f -name '--*'`,
    `cd rust && cargo test --bin voiceterm`.
- 2026-03-04: Phase-2e structural decomposition closure:
  - completed god-file extraction for writer state by splitting
    `writer/state.rs` into focused modules:
    `state/dispatch.rs`, `state/redraw.rs`, `state/profile.rs`,
    `state/display.rs`, `state/policy.rs`, `state/chunk_analysis.rs`,
  - retained dispatch-only `handle_message` with policy-pipeline orchestration
    and RuntimeProfile DI while removing policy/parser/state-shape bulk from
    the root state file,
  - reduced `writer/state.rs` from `2439` lines (pre-split baseline) to `448`
    lines, satisfying the MP-346 Step-2e structural-size target,
  - validation: `python3 dev/scripts/devctl.py check --profile ci`,
    `python3 dev/scripts/devctl.py docs-check --user-facing`,
    `python3 dev/scripts/devctl.py hygiene`,
    `python3 dev/scripts/checks/check_active_plan_sync.py`,
    `python3 dev/scripts/checks/check_multi_agent_sync.py`,
    `python3 dev/scripts/checks/check_cli_flags_parity.py`,
    `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`,
    `python3 dev/scripts/checks/check_code_shape.py`,
    `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md`,
    `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`,
    `find . -maxdepth 1 -type f -name '--*'`,
    `cd rust && cargo test --bin voiceterm writer::state::tests:: -- --nocapture`.
- 2026-03-04: Post-closure governance audit tightened remaining Phase-2 scope:
  - added Step-2f.1 allowlist burn-down + shape-budget reset checklist so
    report-only coupling debt cannot hide behind broad allowlists or legacy
    `PATH_POLICY_OVERRIDES` ceilings,
  - added Step-2f.2 function-shape guardrail checkpoint so dispatcher/pipeline
    extractions cannot re-form into oversized single-function hubs,
  - moved compatibility-governance kickoff to immediately after Step-2f
    closure to avoid indefinite Phase-4 deferral.
- 2026-03-04: Step-2f/2f.1/2f.2 + Phase-4 kickoff implementation closure:
  - `check_ide_provider_isolation.py` now defaults to blocking mode and
    mixed-signal allowlists were narrowed from broad prefixes to explicit
    policy-owner files only (`runtime_compat.rs`, `writer/state/profile.rs`,
    `writer/timing.rs`),
  - removed `event_loop.rs` and `terminal.rs` explicit allowlist entries and
    fixed remaining mixed runtime statement in `event_loop.rs` by splitting
    host/provider conditions into separate policy booleans,
  - tightened `code_shape_policy.py` to decomposition-era file budgets for
    `writer/state.rs` and new writer decomposition modules
    (`dispatch.rs`, `redraw.rs`, `policy.rs`),
  - enabled function-size guardrails for dispatcher/pipeline hotspots with
    explicit temporary exception protocol (owner + expiry + follow-up MP item),
  - landed compatibility-governance scaffold:
    `dev/config/compat/ide_provider_matrix.yaml`,
    `check_compat_matrix.py`,
    `compat_matrix_smoke.py`,
    and `devctl compat-matrix` command wiring,
  - captured checkpoint packet `CP-013` at
    `dev/reports/mp346/checkpoints/20260304T163911Z-cp013/`.
- 2026-03-04: Post-CP-013 hardening + Phase-3 prep cleanup:
  - hardened `check_ide_provider_isolation.py` signal detection to catch
    host-enum + provider-backend helper coupling patterns (including
    `*_backend`/`is_*_backend`) while keeping broad helper-name false positives
    out of blocking results,
  - added isolation regression coverage for multiline `#[cfg(test)]` function
    signatures so test helpers are skipped consistently before coupling
    analysis,
  - fixed `check_rust_lint_debt.py` allow-attribute matching so inner
    `#![allow(...)]` attributes are counted; removed now-unneeded temporary
    `#![allow(dead_code)]` from `provider_adapter.rs`,
  - further reduced mixed host/provider call-site coupling by routing writer
    geometry-collapse checks and JetBrains+Claude fallback decisions through
    RuntimeProfile-owned booleans (`runtime_profile.claude_jetbrains`) and
    canonical compatibility helpers,
  - reduced prompt hotspot footprint by extracting Claude prompt detector tests
    into `prompt/claude_prompt_detect/tests.rs` (`claude_prompt_detect.rs` now
    `623` lines) and trimming redundant helper logic in
    `event_loop/prompt_occlusion.rs` (now `1143` lines, under current
    decomposition hard limit),
  - validation: `python3 -m unittest dev.scripts.devctl.tests.test_check_ide_provider_isolation dev.scripts.devctl.tests.test_check_rust_lint_debt`,
    `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md`,
    `python3 dev/scripts/checks/check_rust_lint_debt.py --format md`,
    `python3 dev/scripts/checks/check_code_shape.py --format md`,
    `python3 dev/scripts/checks/check_code_shape.py --absolute --format md`,
    `python3 dev/scripts/checks/check_rust_best_practices.py --format md`,
    `python3 dev/scripts/checks/check_compat_matrix.py --format md`,
    `python3 dev/scripts/checks/compat_matrix_smoke.py --format md`,
    `cd rust && cargo test --bin voiceterm --quiet`.

- 2026-03-04: Ran `devctl swarm_run` (`20260304-035730Z-c01`, `MP-346`); selected_agents=6, worker_agents=5, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/20260304-035730Z-c01/summary.md`.
- 2026-03-04: Ran `devctl swarm_run` (`20260304-035730Z-c02`, `MP-346`); selected_agents=6, worker_agents=5, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/20260304-035730Z-c02/summary.md`.
- 2026-03-04: Phase-3a prompt strategy wiring checkpoint (`CP-014`) landed:
  - implemented concrete provider adapter resolution in
    `rust/src/bin/voiceterm/provider_adapter.rs` and wired
    `build_prompt_occlusion_detector` as the prompt detector entrypoint,
  - routed runtime startup detector construction through adapter strategy
    ownership in `main.rs` (replacing direct
    `ClaudePromptDetector::new_for_backend` construction),
  - Claude adapter now owns `PromptDetectionStrategy` detector policy; non-Claude
    providers keep fallback behavior via existing backend-label policy path,
  - added temporary parity shim so
    detector routing can be toggled to legacy behavior during short-lived
    phase-3 validation,
  - validation: `cargo test --bin voiceterm provider_adapter::tests:: -- --nocapture`,
    `cargo test --bin voiceterm prompt::claude_prompt_detect::tests:: -- --nocapture`,
    `python3 dev/scripts/devctl.py check --profile ci`,
    `python3 dev/scripts/devctl.py docs-check --user-facing`,
    `python3 dev/scripts/devctl.py hygiene`,
    `python3 dev/scripts/checks/check_active_plan_sync.py --format md`,
    `python3 dev/scripts/checks/check_multi_agent_sync.py --format md`,
    `python3 dev/scripts/checks/check_cli_flags_parity.py`,
    `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`,
    `python3 dev/scripts/checks/check_code_shape.py --format md`,
    `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations --format md`,
    `python3 dev/scripts/checks/check_compat_matrix.py --format md`,
    `python3 dev/scripts/checks/compat_matrix_smoke.py --format md`,
    `python3 dev/scripts/checks/check_rust_lint_debt.py --format md`,
    `python3 dev/scripts/checks/check_rust_best_practices.py --format md`,
    `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`,
    `find . -maxdepth 1 -type f -name '--*'`,
    `cd rust && cargo test --bin voiceterm --quiet`,
  - captured checkpoint packet:
    `dev/reports/mp346/checkpoints/20260304T174948Z-cp014/`.
- 2026-03-04: Post-CP-014 review follow-up fixed a strategy-contract bug and
  closed Phase-3 checklist gaps:
  - fixed `provider_adapter::ClaudePromptDetectionStrategy::build_detector`
    to honor the `backend_label` argument (removed hardcoded `"claude"`),
  - added provider-adapter regression coverage for strategy backend-policy
    forwarding and shim env restoration behavior,
  - added explicit Step `3a.1` shim-retirement criteria and clarified Phase-3
    manual-matrix rerun policy to match checkpoint evidence expectations,
  - validation: `cd rust && cargo test --bin voiceterm provider_adapter::tests:: -- --nocapture`.
- 2026-03-04: Additional pre-Step-3b cleanup review landed:
  - unified provider label classification in `provider_adapter` to use
    canonical `runtime_compat::BackendFamily::from_label` mapping instead of a
    duplicate parser,
  - removed redundant `ProviderId::Claude` gate from
    `build_prompt_occlusion_detector` so adapter behavior keys only on adapter
    capability (`supports_prompt_occlusion`) plus strategy availability,
  - tightened `check_code_shape` path budget for
    `prompt/claude_prompt_detect.rs` to post-split reality (`soft=600`,
    `hard=650`) so regrowth cannot hide behind the old `930` freeze ceiling,
  - validation: `cd rust && cargo test --bin voiceterm provider_adapter::tests:: -- --nocapture`,
    `python3 dev/scripts/checks/check_code_shape.py --format md`,
    `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md`.
- 2026-03-04: Step-3d explicit non-IPC Gemini guardrails landed:
  - kept IPC provider surface codex/claude-only and codified Gemini as
    overlay-only experimental in IPC provider-selection paths,
  - `Provider` parsing now classifies `gemini` as unsupported-in-IPC and emits
    explicit recoverable errors instead of silent fallback behavior,
  - `/provider`, `/auth <provider>`, and `send_prompt` provider overrides now
    reject unsupported/unknown provider names consistently using one parser
    diagnostic path,
  - startup `VOICETERM_PROVIDER` override now logs and falls back to codex on
    unsupported provider values (including `gemini`) rather than silently
    accepting ambiguous runtime state,
  - user/developer docs now explicitly state IPC provider support is
    `codex|claude` and that Gemini remains overlay-only experimental outside IPC,
  - validation: `cd rust && cargo test ipc::tests:: -- --nocapture`,
    `python3 dev/scripts/checks/check_active_plan_sync.py --format md`,
    `python3 dev/scripts/checks/check_multi_agent_sync.py --format md`.
- 2026-03-04: Post-Step-3d IPC wrapper-override regression fix landed before
  Step-3b kickoff:
  - `handle_send_prompt` now handles wrapper commands before provider override
    parsing so invalid overrides cannot block wrapper execution (notably `/exit`
    during auth),
  - added IPC regressions for `/exit` + invalid override during auth and wrapper
    command behavior with invalid overrides,
  - validation: `cd rust && cargo test ipc::tests:: -- --nocapture`,
    `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md`,
    `python3 dev/scripts/checks/check_code_shape.py --format md`.
- 2026-03-04: Ran `devctl swarm_run` (`mp346-swarmrun-20260304t1`, `MP-346`); selected_agents=5, worker_agents=4, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/mp346-swarmrun-20260304t1/summary.md`.
- 2026-03-04: Tooling/CI guardrail follow-up for findings #3/#4/#5:
  - `rust_ci.yml` now runs `devctl check --profile ai-guard` in the normal
    runtime lane (`--skip-fmt --skip-clippy --skip-tests`) so isolation and AI
    guard scripts are not release-only,
  - `check_ide_provider_isolation.py` now scans both runtime and IPC roots and
    tracks `let`-bound host/provider signals so split-statement coupling cases
    are detected without broad helper-name false positives,
  - `code_shape_policy.py` prompt hotspot budgets now match MP-346 DoD hard
    ceilings (`prompt_occlusion.rs` `<=700`, `claude_prompt_detect.rs` `<=600`)
    while keeping existing oversize files hard-locked against growth,
  - `release_preflight.yml` AI-guard step now explicitly uses `--skip-tests`
    to avoid duplicating the runtime-bundle test phase.
- 2026-03-04: Ran `devctl swarm_run` (`20260304-mp346-multiagent-live`, `MP-346`); selected_agents=5, worker_agents=4, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/20260304-mp346-multiagent-live/summary.md`.
- 2026-03-04: Post-review follow-up closed compact approval-card regression and
  removed alias-level prompt detector coupling in runtime callsites:
  - `prompt::PromptOcclusionDetector` is now a concrete wrapper type (not a
    type alias), with delegated detector API used by runtime/event-loop state
    and adapter construction paths,
  - event-loop tests now construct `PromptOcclusionDetector` directly instead
    of `ClaudePromptDetector`, eliminating runtime-type alias dependency,
  - shared numbered-approval-card parsing now accepts compact dot-numbered
    option payloads (`1.Yes` / `2.No`) so non-rolling approval suppression does
    not miss compact Claude approval cards,
  - validation: `cd rust && cargo test --bin voiceterm event_loop::prompt_occlusion::tests::numbered_approval_hint_detects_compact_prefix_variant -- --nocapture`,
    `cd rust && cargo test --bin voiceterm prompt::claude_prompt_detect::tests::shared_approval_parser_accepts_compact_dot_numbering -- --nocapture`,
    `cd rust && cargo test --bin voiceterm provider_adapter::tests:: -- --nocapture`,
    `cd rust && cargo clippy --bin voiceterm -- -D warnings`,
    `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md`.
- 2026-03-04: Plan-governance audit sync confirmed current continuation scope:
  - Step `3a.1` is closed (shim retirement docs/state cleanup complete), and
    `CP-016` continuation now starts at Step `3f`,
  - Step `3c`/`3f` remain open: IPC lifecycle/capability emission is still
    codex/claude-concrete in router/auth/session paths,
  - Step `3e` was open at this checkpoint: explicit non-IPC classification for
    `aider`/`opencode`/`custom` needed runtime + matrix + docs parity
    (completed later on 2026-03-04 in the Step-3e closure entry below),
  - Step `3b` remains open with prompt hotspot absolute-shape failures and
    Claude-coupled logic still in `event_loop/prompt_occlusion.rs`,
  - earlier progress-log wording that called Aider/OpenCode concerns "stale"
    was narrowed to plan-scope presence only; runtime enforcement was still
    open at this checkpoint and is now closed under Step `3e`.
- 2026-03-04: Step-3a.1 shim-retirement docs/state cleanup landed:
  - confirmed no runtime shim symbol usage remains via repo-wide search,
  - retired remaining shim-symbol mentions from active tracker/spec text and
    updated Step-3 + `CP-016` sequencing to start from Step `3f`,
  - validation: `python3 dev/scripts/checks/check_active_plan_sync.py`,
    `python3 dev/scripts/checks/check_multi_agent_sync.py`,
    `rg -n "legacy shim" dev/active/ide_provider_modularization.md dev/active/MASTER_PLAN.md`.
- 2026-03-04: Step-3e explicit non-IPC backend classification landed:
  - `ipc::Provider` resolution now classifies `aider`, `opencode`, and
    `custom` as explicit overlay-only non-IPC backends (not unknown typos),
    while preserving explicit overlay-only-experimental diagnostics for
    `gemini`,
  - IPC help/provider diagnostics now call out codex/claude as IPC-only and
    classify `gemini`/`aider`/`opencode`/`custom` as non-IPC overlay paths,
  - compatibility matrix + smoke/validation checks now require explicit non-IPC
    modes and declared matrix cells for `aider`/`opencode`/`custom`,
  - docs (`CLI_FLAGS`, `USAGE`, `ARCHITECTURE`) now use aligned wording for the
    codex/claude IPC surface vs overlay-only non-IPC backends,
  - validation: `cd rust && cargo test ipc::tests:: -- --nocapture`,
    `python3 dev/scripts/checks/check_compat_matrix.py --format md`,
    `python3 dev/scripts/checks/compat_matrix_smoke.py --format md`.
- 2026-03-04: Step-3f adapter-derived IPC capability emission landed:
  - `Provider::ipc_supported()` now derives IPC capability providers from
    backend registry discovery filtered through IPC provider resolution,
  - `emit_capabilities` now emits provider labels through the derived
    `ipc_capability_labels()` path instead of a static codex/claude list,
  - regression coverage now asserts derived capability labels plus explicit
    non-IPC override rejections for `aider`/`opencode`/`custom` across
    `/provider`, `send_prompt`, and `/auth` paths,
  - validation: `cd rust && cargo test ipc::tests:: -- --nocapture`,
    `python3 dev/scripts/checks/check_compat_matrix.py --format md`,
    `python3 dev/scripts/checks/compat_matrix_smoke.py --format md`.
- 2026-03-04: Step-3c IPC lifecycle adapterization + isolation guard hardening landed:
  - added `ipc/provider_lifecycle.rs` as the lifecycle adapter owner for
    provider job start/cancel/drain paths so router + session loop runtime no
    longer duplicate codex/claude lifecycle match arms,
  - auth lifecycle now resolves command/reset policy through `Provider`
    lifecycle helpers (`auth_command`, `resets_session_on_auth_success`) so
    auth flow/event processing no longer hard-code provider-specific branches,
  - provider job-end emissions in event processors now resolve provider labels
    through `Provider::as_str()` ownership instead of literal strings,
  - `check_ide_provider_isolation.py` now enforces file-scope host/provider
    coupling detection (in addition to same-statement coupling), includes
    non-IPC provider label coverage (`aider`/`opencode`/`custom`), and keeps
    explicit temporary file-scope allowlist debt for open Step-3b hotspots,
  - validation: `cd rust && cargo test ipc::tests:: -- --nocapture`,
    `cd rust && cargo test --bin voiceterm event_loop::prompt_occlusion::tests:: -- --nocapture`,
    `cd rust && cargo test --bin voiceterm prompt::claude_prompt_detect::tests:: -- --nocapture`,
    `python3 -m unittest dev.scripts.devctl.tests.test_check_ide_provider_isolation`,
    `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md`,
    `python3 dev/scripts/devctl.py check --profile ai-guard --skip-fmt --skip-clippy --skip-tests`.
- 2026-03-04: Step-3b prompt-occlusion decomposition closure landed:
  - split prompt-signal parsing and provider-marker heuristics out of
    `event_loop/prompt_occlusion.rs` into prompt-owned modules
    (`prompt/occlusion_signals.rs` and
    `prompt/claude_prompt_detect/signals.rs`),
  - event-loop prompt-occlusion runtime now consumes prompt-owned signal hooks
    (no direct event-loop coupling to Claude parser internals),
  - temporary `check_ide_provider_isolation.py` file-scope allowlist debt for
    `event_loop/prompt_occlusion.rs` was removed after scanner rerun confirmed
    no unauthorized mixed-signal coupling,
  - hotspot absolute-shape blockers are closed with hard-limit compliance:
    `event_loop/prompt_occlusion.rs`=`679` and
    `prompt/claude_prompt_detect.rs`=`541`,
  - validation: `cd rust && cargo test ipc::tests:: -- --nocapture`,
    `cd rust && cargo test --bin voiceterm event_loop::prompt_occlusion::tests:: -- --nocapture`,
    `cd rust && cargo test --bin voiceterm prompt::claude_prompt_detect::tests:: -- --nocapture`,
    `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md`,
    `python3 dev/scripts/checks/check_code_shape.py --absolute --format md`.
- 2026-03-05: Phase-5 defer-scope closure recorded:
  - selected defer path: AntiGravity moved out of active MP-346 host matrix
    scope until concrete runtime host fingerprint evidence exists,
  - updated `MASTER_PLAN`, `INDEX`, `dev/config/compat/ide_provider_matrix.yaml`,
    `README.md`, and `guides/USAGE.md` so active verified hosts remain Cursor
    and JetBrains while `Other` stays stabilizing,
  - historical checkpoint note (superseded): this entry originally tracked
    `CP-016` pending on `7/7`; current release-scope closure is IDE-first
    (`4/4`) per 2026-03-05 operator scope update.
- 2026-03-05: Phase-6 ADR governance closure landed:
  - added ADR `0035` (`host-provider-boundary-ownership`) and ADR `0036`
    (`compat-matrix-governance-ci-fail-policy`) with `Accepted` status,
  - updated `dev/adr/README.md` index to include both ADRs,
  - historical checkpoint note (superseded): this entry originally tracked
    `CP-016` pending `7/7`; release-scope closure now uses IDE-first `4/4`
    with deferred `other`/`gemini` backlog follow-up.
- 2026-03-05: Findings cleanup patch for runtime artifacts + startup provider override:
  - `.gitignore` now ignores nested `.voiceterm/memory/` paths
    (`**/.voiceterm/memory/`) and tracked runtime artifacts
    `rust/.voiceterm/memory/events*.jsonl` were removed from git index,
  - `ipc/session/state.rs` startup provider override handling now emits a
    recoverable IPC error event when `VOICETERM_PROVIDER` is invalid, then
    falls back to the discovered IPC default provider,
  - added IPC regression coverage:
    `ipc_state_invalid_voiceterm_provider_emits_recoverable_startup_error`,
  - validation: `cd rust && cargo fmt --all -- --check`,
    `cd rust && cargo test ipc::tests:: -- --nocapture`,
    `python3 dev/scripts/devctl.py check --profile ci`.
- 2026-03-05: CP-016 checkpoint packet refresh captured:
  - recorded automated runtime/governance rerun artifact at
    `dev/reports/mp346/checkpoints/20260305T032253Z-cp016/`
    (`summary.md`, `exit_codes.env`),
  - added operator-facing manual closure assets in the same packet:
    `manual_matrix_notes.md` (original `7/7` worksheet; now superseded by
    IDE-first `4/4` release-scope closure update) and
    `waiver_template.md` (explicit temporary-waiver template),
  - full automated continuation bundle is green (`docs-check --user-facing`,
    `hygiene`, parity/screenshot/shape/isolation/matrix/rust guards,
    `markdownlint`, active-plan sync, multi-agent sync),
  - historical checkpoint note (superseded): this entry originally marked
    Phase-3 closure blocked on `7/7`; release-scope closure now uses IDE-first
    `4/4` and tracks deferred cells as post-release backlog.
- 2026-03-05: CP-016 waiver request drafted for blocked physical-host matrix gate:
  - current execution environment is `TERM_PROGRAM=vscode`; this session cannot
    exercise required Cursor/JetBrains/Other-host runtime surfaces,
  - optional IPC sanity invocation (`voiceterm --json-ipc`) returns sandbox
    `Operation not permitted (os error 1)`,
  - populated `waiver_template.md` with risk/guardrails/expiry (`2026-03-12`)
    and updated CP-016 `summary.md` to `waiver requested` pending operator
    approve/deny.
- 2026-03-05: CP-016 waiver decision approved:
  - operator decision is now `approve waiver` in `waiver_template.md`,
  - CP-016 state is `go (temporary waiver approved)`,
  - historical waiver note (superseded): `7/7` requirement was later replaced
    by IDE-first `4/4` release-scope closure.
- 2026-03-05: CP-016 waiver-state consistency fix:
  - aligned Step-3 checklist semantics with approved temporary-waiver state
    (waiver is not closure),
  - historical note (superseded): preserved `7/7` rerun requirement at that
    time; current release-scope closure uses IDE-first `4/4`.
- 2026-03-05: Post-waiver tooling hardening slice landed (under CP-016 guardrails):
  - `check_ide_provider_isolation.py` now skips broader test-only cfg forms
    (for example `#[cfg(any(test, feature = "mutants"))]`) to avoid false
    production coupling signals,
  - `check_compat_matrix.py` and `compat_matrix_smoke.py` now parse YAML
    matrix payloads directly (with JSON fallback when YAML tooling is absent),
  - `compat_matrix_smoke.py` runtime backend extraction now derives from
    `BackendRegistry::new()` constructor ownership instead of `mod` declarations,
  - added dedicated unit coverage for matrix scripts:
    `test_check_compat_matrix.py` and `test_compat_matrix_smoke.py`, plus
    expanded cfg-test coverage in `test_check_ide_provider_isolation.py`,
  - validation:
    `python3 -m unittest dev.scripts.devctl.tests.test_check_ide_provider_isolation dev.scripts.devctl.tests.test_check_compat_matrix dev.scripts.devctl.tests.test_compat_matrix_smoke`,
    `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations --format md`,
    `python3 dev/scripts/checks/check_compat_matrix.py --format md`,
    `python3 dev/scripts/checks/compat_matrix_smoke.py --format md`.
- 2026-03-05: Multi-agent review + cleanup continuation slice landed:
  - fixed IPC cancellation parity: preemptive provider-job cancellation in
    `handle_send_prompt` now emits `JobEnd(cancelled)` consistently (same
    contract as `/cancel` and `/exit`),
  - added IPC regression coverage for wrapper-command and prompt-preemption
    cancellation paths,
  - `check_compat_matrix.py` now detects duplicate `hosts[].id` and
    `providers[].id` entries as explicit validation errors,
  - `compat_matrix_smoke.py` now enforces runtime coverage against unfiltered
    parsed runtime host/backend/provider sets (except explicit
    `BackendFamily::Other` sentinel exclusion) so new runtime variants cannot
    bypass matrix governance accidentally,
  - validation:
    `cd rust && cargo test ipc::tests:: -- --nocapture`,
    `python3 -m unittest dev.scripts.devctl.tests.test_check_ide_provider_isolation dev.scripts.devctl.tests.test_check_compat_matrix dev.scripts.devctl.tests.test_compat_matrix_smoke`,
    `python3 dev/scripts/checks/check_compat_matrix.py --format md`,
    `python3 dev/scripts/checks/compat_matrix_smoke.py --format md`,
    `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations --format md`.
- 2026-03-05: Reviewer follow-up hardening slice landed (parallel lanes):
  - isolation core cfg-test detection now refuses `cfg(...not(test)...)`
    expressions so production paths are not skipped by mistake,
  - matrix smoke backend discovery is now constructor-pattern based across the
    backend module (not tied to a single `BackendRegistry` vec! layout),
  - matrix validator now fails explicit malformed `hosts[]`/`providers[]`
    entries that do not provide a string `id`,
  - IPC regression coverage now includes active-Claude wrapper cancellation and
    `/cancel` provider `JobEnd(cancelled)` emission,
  - memory-guard targeted lane was rerun and is green in this session,
  - validation:
    `python3 -m unittest dev.scripts.devctl.tests.test_check_ide_provider_isolation dev.scripts.devctl.tests.test_check_compat_matrix dev.scripts.devctl.tests.test_compat_matrix_smoke`,
    `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations --format md`,
    `python3 dev/scripts/checks/check_compat_matrix.py --format md`,
    `python3 dev/scripts/checks/compat_matrix_smoke.py --format md`,
    `cd rust && cargo test ipc::tests:: -- --nocapture`,
    `cd rust && cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture`.
- 2026-03-05: Closure-gate CI stabilization slice landed:
  - `legacy_tui::tests::memory_guard_backend_threads_drop` now waits for
    backend-thread count to return to baseline before asserting no leak,
    avoiding suite-order teardown race noise while preserving memory-guard
    intent,
  - full `devctl check --profile ci` rerun is now green in this session.
- 2026-03-05: Tooling hygiene + workflow-bridge hardening slice landed:
  - extracted remaining workflow shell-heavy range/scope/path logic into
    `dev/scripts/workflow_bridge/shell.py` and rewired
    `tooling_control_plane.yml`, `security_guard.yml`, `failure_triage.yml`,
    and `mutation-testing.yml`,
  - added `check_workflow_shell_hygiene.py` and wired it into
    `docs-check --strict-tooling` plus explicit tooling-control-plane CI steps,
  - added explicit naming-consistency guard execution in
    `tooling_control_plane.yml` and synchronized release-governance docs to
    require same-SHA `release_preflight.yml` before workflow-first publish,
  - validation:
    `python3 -m unittest dev.scripts.devctl.tests.test_workflow_shell_bridge dev.scripts.devctl.tests.test_check_workflow_shell_hygiene dev.scripts.devctl.tests.test_docs_check dev.scripts.devctl.tests.test_check`,
    `python3 dev/scripts/devctl.py docs-check --strict-tooling --format md`,
    `python3 dev/scripts/checks/check_workflow_shell_hygiene.py --format md`,
    `python3 dev/scripts/checks/check_naming_consistency.py --format md`.
- 2026-03-05: Tooling closure + maintainability follow-up slice landed:
  - split oversized workflow bridge logic into dedicated helper modules under
    `dev/scripts/workflow_bridge/` and kept
    `dev/scripts/workflow_bridge/autonomy.py` as a thin command router,
  - split oversized hygiene ADR governance logic from
    `dev/scripts/devctl/commands/hygiene_audits.py` into focused companion
    modules (`hygiene_audits_archive.py`, `hygiene_audits_adrs*.py`) while
    preserving existing command/test interfaces,
  - expanded workflow-shell hygiene guard discovery to scan both `.yml` and
    `.yaml` workflows and added auditable rule-level suppression token support
    (`workflow-shell-hygiene: allow=<rule-id>[,<rule-id>|all]`),
  - synchronized release docs to the same-SHA preflight-first sequence required
    by `devctl release-gates` and publish workflow gates, and added explicit
    compat-matrix drift checks to maintainer guidance,
  - validation:
    `python3 -m unittest dev.scripts.devctl.tests.test_autonomy_workflow_bridge dev.scripts.devctl.tests.test_hygiene dev.scripts.devctl.tests.test_check_workflow_shell_hygiene dev.scripts.devctl.tests.test_check_coderabbit_gate dev.scripts.devctl.tests.test_check_coderabbit_ralph_gate`,
    `python3 dev/scripts/checks/check_code_shape.py`,
    `python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop --head-ref <git stash create snapshot>`,
    `python3 dev/scripts/devctl.py docs-check --strict-tooling --format md`,
    `python3 dev/scripts/devctl.py hygiene --fix --format md`.
- 2026-03-05: Rust guardrail expansion follow-up landed:
  - added `check_rust_test_shape.py` and
    `check_rust_runtime_panic_policy.py` into the `devctl check` AI-guard
    sequence, commit-range forwarding, and `audit-scaffold` action synthesis,
  - added `check_clippy_high_signal.py` enforcement to `rust_ci.yml` using
    lint histogram JSON emitted by `collect_clippy_warnings.py`,
  - updated governance docs (`AGENTS.md`, `dev/scripts/README.md`,
    `dev/DEVELOPMENT.md`, `dev/DEVCTL_AUTOGUIDE.md`,
    `.github/workflows/README.md`) to include new guard behavior and command
    surfaces,
  - validation:
    `python3 -m unittest dev.scripts.devctl.tests.test_collect_clippy_warnings dev.scripts.devctl.tests.test_check_clippy_high_signal dev.scripts.devctl.tests.test_check_rust_test_shape dev.scripts.devctl.tests.test_check_rust_runtime_panic_policy dev.scripts.devctl.tests.test_check dev.scripts.devctl.tests.test_audit_scaffold`,
    `python3 dev/scripts/checks/check_rust_test_shape.py --format md`,
    `python3 dev/scripts/checks/check_rust_runtime_panic_policy.py --format md`,
    `python3 dev/scripts/rust_tools/collect_clippy_warnings.py --working-directory rust --output-lints-json /tmp/clippy-lints.json`,
    `python3 dev/scripts/checks/check_clippy_high_signal.py --input-lints-json /tmp/clippy-lints.json --format md`.
- 2026-03-05: Runtime-lane AI-guard commit-range enforcement landed:
  - `rust_ci.yml`, `release_preflight.yml`, and `security_guard.yml` now
    resolve `since/head` refs via
    `python3 dev/scripts/workflow_bridge/shell.py resolve-range` and pass those
    refs into `devctl check --profile ai-guard`,
  - `rust_ci.yml` and `security_guard.yml` now run checkout with
    `fetch-depth: 0` so PR base/head refs are available for range-mode guards,
  - `devctl check` now runs `clippy-high-signal-guard` after lint-histogram
    collection completes (no setup-phase race), and
    `check_naming_consistency.py` was split into
    `naming_consistency_core.py` so shape policy remains green,
  - validation:
    `python3 -m unittest dev.scripts.devctl.tests.test_check dev.scripts.devctl.tests.test_check_naming_consistency dev.scripts.devctl.tests.test_check_rust_runtime_panic_policy dev.scripts.devctl.tests.test_check_rust_test_shape dev.scripts.devctl.tests.test_check_rust_lint_debt dev.scripts.devctl.tests.test_collect_clippy_warnings`,
    `python3 dev/scripts/devctl.py check --profile ai-guard --format md`,
    `python3 dev/scripts/devctl.py docs-check --strict-tooling --format md`,
    `python3 dev/scripts/devctl.py hygiene --fix --strict-warnings --format md`.
- 2026-03-05: Clippy zero-warning restoration + MSRV metadata sync landed:
  - resolved new strict-clippy lints (`manual_repeat_n`,
    `unnecessary_map_or`, `manual_is_multiple_of`) across runtime and benchmark
    paths so `--deny-warnings` remains green,
  - synchronized `rust/Cargo.toml` `rust-version` to `1.88.0` so manifest
    metadata matches the active CI MSRV lane contract,
  - validation:
    `cd rust && cargo fmt --all`,
    `python3 dev/scripts/rust_tools/collect_clippy_warnings.py --working-directory rust --deny-warnings --quiet-json-stream --propagate-exit-code --output-lints-json /tmp/clippy-lints-postfix.json`,
    `python3 dev/scripts/devctl.py check --profile ai-guard --skip-tests --format md`.
- 2026-03-05: Pending MP-346 guardrail closure slice landed:
  - fixed Python 3.11 compatibility in `devctl release-gates` markdown rendering
    (`release_gates.py` no longer uses a 3.12-only f-string backslash expression),
  - ratcheted Clippy thresholds to the planned Phase-0 values
    (`rust/clippy.toml` cognitive complexity `35 -> 25`; `rust/Cargo.toml`
    now sets `too_many_lines = "warn"`),
  - added and integrated `check_duplicate_types.py` and
    `check_structural_complexity.py` into `devctl check` AI-guard pack,
    commit-range forwarding, and `audit-scaffold` guard synthesis,
  - added `check_duplication_audit.py` as the periodic `jscpd` wrapper with
    report-freshness and duplication-percentage policy checks (`--run-jscpd`),
  - expanded unit coverage for all new scripts and updated `devctl` guard
    wiring tests (`test_check.py`, `test_audit_scaffold.py`, and dedicated new
    script tests),
  - updated tooling docs (`dev/scripts/README.md`,
    `dev/DEVCTL_AUTOGUIDE.md`) to include the new guardrails.
- 2026-03-05: MP-346 continuation validation + audit-evidence cleanup landed:
  - reran full `devctl check --profile ci` after interrupted prior session;
    all 17 steps (including full workspace test suite) are green,
  - resolved a post-merge shape regression by adding an explicit
    `code_shape_policy.py` path budget for
    `dev/scripts/checks/check_rust_lint_debt.py`,
  - reran tooling bundle commands in contract order
    (`docs-check --strict-tooling`, `hygiene --fix --strict-warnings`,
    orchestration status/watch, workflow/rust/code-shape guards, markdownlint),
  - removed stale pre-remediation audit rows that contradicted current MP-346
    guard behavior (legacy `ci` profile/no commit-range forwarding/legacy
    `src/**` contract findings).
- 2026-03-05: Senior architecture reconciliation audit recorded (multi-agent):
  - confirmed prior guardrail-delivery row dispute is resolved correctly:
    rows `476`, `478`, `479`, and `486` are `done`,
  - corrected checklist drift by marking Phase-2 and Phase-3
    "after each sub-step" execution rows complete (`CP-007`..`CP-013` and
    `CP-014`..`CP-016`),
  - validated historical closure blockers at that checkpoint: `CP-016` manual
    matrix pending (`7/7` at the time), and current non-regression rerun was
    blocked by
    `check_code_shape.py` (`check_router.py`, `docs_check_support.py`) plus
    missing duplication-report evidence for `check_duplication_audit.py`,
  - operator sequencing decision: defer physical-host matrix execution until
    the final pre-release closure gate to avoid stale attestations while
    modularization and tooling cleanup are still changing behavior,
  - continuation sequence is now:
    (1) resolve shape-policy blockers (`check_router.py`,
    `docs_check_support.py`) and duplication evidence readiness (`jscpd`),
    (2) rerun closure non-regression bundle with shape+duplication evidence
    restored and green,
    (3) execute/record physical-host matrix `7/7` as final pre-release
    validation (historical plan step; superseded by IDE-first `4/4`
    release-scope closure),
    (4) update `CP-016` packet/checkpoint log from waiver to completed,
    (5) close `MP-346` and sync `MASTER_PLAN` tracker row,
  - follow-on tooling/process hardening work is tracked in reopened `MP-347`
    scope.
- 2026-03-05: MP-347 Phase-1 closure cleanup completion:
  - resolved shape-policy blockers by decomposing check-router and docs-check
    helper surfaces (`check_router.py` now orchestration-only with split
    constants/support/render modules; `docs_check_support.py` now compatibility
    exports over split policy/messaging modules),
  - extended `check_duplication_audit.py` with explicit
    `status`/`blocked_by_tooling` report fields so tooling/environment blockers
    are first-class in evidence packets,
  - added constrained-environment duplication evidence fallback support
    (`--run-python-fallback` via shared `check_duplication_audit_support.py`) with
    dedicated regression coverage in
    `dev/scripts/devctl/tests/test_check_duplication_audit.py` while keeping
    `jscpd` as the primary evidence generator,
  - generated canonical duplication evidence via
    `python3 dev/scripts/checks/check_duplication_audit.py --run-jscpd` with
    `dev/reports/duplication/jscpd-report.json` (`duplication_percent=0.93`,
    `duplicates_count=34`, fresh report age),
  - reran closure non-regression bundle row `2310` end-to-end and confirmed all
    listed checks are green,
  - cleaned stale changelog archive reference to retired legacy MVP notes.
- 2026-03-05: MP-347 Phase-1 closure verification refresh:
  - reconciled duplication-audit helper ownership to a single canonical module
    (`check_duplication_audit_support.py`) and removed duplicate helper naming
    drift,
  - removed stale archive path literals from active docs/changelog so archive
    reference scan reports `missing=0`,
  - reran full closure non-regression command pack from row `2331`
    end-to-end and confirmed all listed checks are green, including fresh
    `check_duplication_audit.py --run-jscpd` evidence
    (`duplication_percent=0.93`, `duplicates_count=34`).
- 2026-03-05: Architecture audit refresh (parallel tracks, post-green rerun):
  - reran tooling/runtime/governance guard packs (`check_code_shape`,
    `check_duplication_audit --run-jscpd`, structural/naming/type checks,
    rust quality guards, workflow parity checks, matrix checks, strict tooling
    docs-check) and confirmed green status for core closure gates in the
    current dirty-tree state,
  - historical checkpoint note (superseded): this entry originally kept
    `CP-016` open for deferred physical-host `7/7`; release-scope closure is
    now IDE-first `4/4`,
  - narrowed remaining MP-347 follow-up to five explicit hardening items:
    (1) promote check-router risk add-ons to a single machine-readable source
    of truth with parity enforcement,
    (2) remove/consolidate duplicated docs-check policy constants
    (`docs_check_constants.py` vs `docs_check_policy.py`) to avoid drift,
    (3) harden strict-hygiene determinism so `docs-check --strict-tooling`
    followed by `hygiene --strict-warnings` does not fail on regenerated
    `dev/scripts/**/__pycache__` warnings in local dirty-tree runs,
    (4) pay down expiring function-size exceptions before `2026-05-15`
    (`dispatch_message`, `maybe_redraw_status`,
    `feed_prompt_output_and_sync`),
    (5) reduce documented dead-code allow backlog (`24` current instances),
  - continuation sequencing:
    (A) MP-347 Phase-2 SSOT/dedup + strict-hygiene determinism hardening,
    (B) MP-347 Phase-3 exception/dead-code paydown,
    (C) historical plan step: final pre-release manual matrix `7/7` + CP-016
    closure (superseded by IDE-first `4/4` release-scope closure).
- 2026-03-05: MP-347 Phase-2 hygiene-contract closure slice:
  - registered `check_duplication_audit_support.py` in
    `dev/scripts/devctl/script_catalog.py`,
  - documented `check_duplication_audit_support.py` in
    `dev/scripts/README.md` to satisfy hygiene script inventory policy,
  - reran `python3 dev/scripts/devctl.py hygiene --fix --strict-warnings`
    and confirmed strict hygiene is green (`errors=0`, `warnings=0`),
  - remaining MP-347 follow-up narrows to risk-add-on SSOT consolidation,
    docs-check policy dedup, and function/dead-code debt paydown.
- 2026-03-05: MP-347 duplication cleanup follow-up slice:
  - consolidated repeated runtime/test env scaffolding into shared
    `test_env` helpers (`with_terminal_host_env_overrides`,
    `with_terminal_color_env_overrides`) and removed duplicate local env
    setup blocks in `main.rs`, `runtime_compat.rs`, `config/theme.rs`,
    `theme_ops.rs`,
  - deduplicated PTY reader loop implementation via shared
    `spawn_reader_thread_inner` and unified style-schema V2/V3/V4 pack
    normalization through one constructor path,
  - extracted shared memory-store test fixture helper and shared overlay
    section-line renderer to reduce cross-module clone drift,
  - refreshed duplication evidence via
    `python3 dev/scripts/checks/check_duplication_audit.py --run-jscpd`:
    `duplication_percent=0.32`, `duplicates_count=14` (down from `0.93`/`34`).
- 2026-03-07: Post-release code smell + coupling audit:
  - full-codebase code smell audit (Rust: 18 findings, Python: 16 findings)
    organized by severity (HIGH: 6, MEDIUM: 17, LOW: 15),
  - targeted IDE/backend coupling audit confirmed the root cause of
    cross-IDE regression ("fix one IDE, break another") is structural:
    `handle_pty_output` (337 lines, 15+ boolean flags), `RedrawPolicy::resolve`
    (125 lines, 27-field context), and `resolve_idle_redraw_timing` (119 lines)
    are the three worst tangling points,
  - 41% of WriterState fields are IDE/backend-specific, 15 functions branch on
    BOTH IDE and backend, 3 impossible-state field groups exist,
  - proposed PtyAdapter enum pattern to eliminate impossible states by having
    each adapter own its specific fields (compiler-enforced isolation replacing
    615 `if jetbrains { ... }` checks),
  - all findings added to post-release execution backlog section with
    prioritized execution order.
- 2026-03-05: mutation-policy alignment refresh:
  - release profile remains non-blocking for mutation score
    (`devctl check --profile release` uses mutation-score `--report-only`),
  - scheduled mutation workflow threshold check is now advisory/report-only
    across branches (warnings + badge updates, no hard-fail gate).
## Post-Release Code Smell + Coupling Audit (2026-03-07)

Full-codebase code smell audit + targeted IDE/backend coupling audit performed
post-release. Findings below extend MP-346 with concrete structural improvements
that were not in the original release scope but directly support the plan's goal
of preventing cross-regressions between IDE and backend behavior.

### Coupling Audit Summary (WriterState + dispatch layer)

Validates the architectural concern that drove MP-346. The coupling is confirmed
to be the root cause of the "fix one IDE, break another" problem.

| Metric | Count |
|---|---|
| WriterState fields that are IDE/backend-specific | 11 of 27 (41%) |
| Functions that branch on BOTH IDE and backend | 15 |
| Severely tangled functions (3+ cross-checks in one function) | 3 (581 lines total) |
| "Impossible state" field groups (allocated but never used) | 3 |
| References to "jetbrains" across writer/ tree | 615 |
| IDE x Backend combos with specialized behavior | 3 of 9 (33%) |
| IDE x Backend combos silently using generic "Other" fallback | 6 of 9 (67%) |

#### The Three Worst Tangling Points

1. **`handle_pty_output`** (`dispatch_pty.rs:4-341`, 337 lines): Computes 15+
   boolean flags from the IDE x Backend cross-product before doing anything.
   Lines 5-129 are a 110-line flag-computation preamble with each flag being a
   specific (IDE, Backend) pair hardcoded as a local boolean. No dispatch table,
   no trait, no strategy object.

2. **`RedrawPolicy::resolve`** (`policy.rs:150-275`, 125 lines): Takes a
   `RedrawPolicyContext` with 27 fields, 11 of which are IDE+Backend
   cross-product flags. Nested if-chains combine `claude_jetbrains`,
   `codex_jetbrains`, and `cursor_claude` in the same decision tree.

3. **`resolve_idle_redraw_timing`** (`timing.rs:50-169`, 119 lines):
   Re-derives `claude_jetbrains` and `codex_jetbrains` from raw fields even
   though the caller already has these booleans on `RuntimeProfile`. Has 5
   separate `if claude_jetbrains { ... }` guard blocks checking different
   JetBrains cursor-state fields.

#### Impossible State Fields

| When running in... | Fields allocated but never used |
|---|---|
| Cursor IDE | 9 `jetbrains_*` fields (cursor tracking, composer repair, etc.) |
| JetBrains IDE | 3 `cursor_*` fields (startup clear, scroll preclear) |
| Codex backend | 6 `jetbrains_claude_*` fields (Claude-specific repair) |

#### Cross-Regression Paths Confirmed

- Fixing a JetBrains cursor bug touches `handle_pty_output`, which shares the
  preclear pipeline with Cursor via `PreclearPolicy::resolve`.
- Changing Codex output rendering touches `RedrawPolicy::resolve`, which shares
  the `force_full_banner_redraw` flag with Claude's path.
- `resolve_idle_redraw_timing` shares `jetbrains_idle_gated` boolean between
  Claude and Codex timing, so changing one backend's idle hold affects the other.

#### Target Architecture (PtyAdapter pattern)

The clean fix is a three-layer architecture:

**Layer 1: Terminal Capabilities** (how the IDE terminal works):
```rust
trait TerminalCapabilities {
    fn cursor_save_sequence(&self) -> &[u8];
    fn supports_scroll_regions(&self) -> bool;
    fn supports_sync_output(&self) -> bool;
}
// Implementations: JetBrainsTerminal, CursorTerminal, GenericTerminal
```

**Layer 2: Backend HUD Policy** (how the AI backend wants the HUD):
```rust
trait HudPolicy {
    fn reserved_row_budget(&self) -> usize;
    fn treat_cr_as_scroll(&self) -> bool;
    fn idle_redraw_hold(&self) -> Duration;
}
// Implementations: ClaudePolicy, CodexPolicy, GenericPolicy
```

**Layer 3: PTY Adapters** (cross-product combos that need special behavior):
```rust
enum PtyAdapter {
    JetBrainsClaude(JetBrainsClaudeAdapter),  // owns 9 cursor repair fields
    JetBrainsCodex(JetBrainsCodexAdapter),    // owns CR-as-scroll state
    CursorClaude(CursorClaudeAdapter),        // owns input repair, startup preclear
    Generic,                                   // no state needed
}

trait PtyChunkPolicy {
    fn analyze_chunk(&mut self, bytes: &[u8], may_scroll: bool) -> ChunkAnalysis;
    fn preclear_strategy(&self, display: &DisplayState) -> PreclearStrategy;
    fn redraw_timing(&self, now: Instant) -> RedrawTiming;
}
```

Each adapter owns its specific state. JetBrains cursor repair fields do not
exist when running in Cursor. The compiler enforces what is currently enforced
by 615 `if jetbrains { ... }` checks scattered across the codebase.

### Rust Code Smell Findings

| # | Severity | Category | File(s) | Description |
|---|---|---|---|---|
| R1 | HIGH | God function | `main.rs:193-726` | `main()` is 533 lines: CLI parsing, config validation, audio backend, session setup, PTY spawn, channel creation, writer thread, EventLoopState (40+ fields), run loop. Extract into `load_config()`, `setup_session()`, `build_event_loop()`, `run()`. |
| R2 | HIGH | God struct | `writer/state.rs:137-167` | `WriterState` has 30+ fields mixing terminal geometry, 6 timing fields, 9 JetBrains-specific fields, display/theme/mouse. Compose into `TerminalGeometry`, `TimingState`, `PtyAdapter` (IDE-specific), `DisplayState`. |
| R3 | HIGH | Long function | `dispatch_pty.rs:4-340` | `handle_pty_output` is 337 lines: 20+ boolean flags (5-129), policy context (131-147), stdout write (163-212), redraw triggers (215-310). Extract into analyze/write/update pipeline via `PtyChunkAnalysis` struct. |
| R4 | HIGH | Duplicated logic | `voice.rs:473-487`, `wake_word/detector.rs:118-134` | `create_vad_engine` duplicated with only a minor trait bound difference (`Send` vs no `Send`). Move to shared `audio` module with `+ Send` bound. |
| R5 | MEDIUM | Excessive clone | `main.rs:415-416, 499-566` | `config.app.clone()` copies full `AppConfig`. Move into last consumer, pass `&AppConfig` references earlier. |
| R6 | MEDIUM | Repetitive functions | `theme/mod.rs:280-409` | 8 glyph functions with identical `match glyph_set { Unicode => ..., Ascii => ... }` structure. Replace with `GlyphTable` data struct. |
| R7 | MEDIUM | Boilerplate mapping | `style_pack/apply.rs:22-101` | 9 blocks mapping Runtime→Schema enums 1:1 by variant name. Use `impl From<Runtime...> for Schema...` or a declarative macro. |
| R8 | MEDIUM | Stringly-typed | `rule_profile.rs:236-246` | `RuleEvalContext` uses `backend: String`, `color_mode: String` where enums (`BackendKind`, `ColorMode`) would catch typos at compile time. |
| R9 | MEDIUM | Long function | `config/validation.rs:34-258` | `validate()` is 224 lines of sequential range checks + path canonicalization + model discovery. Split into `validate_voice_pipeline_bounds()`, `validate_whisper_config()`, `canonicalize_paths()`. |
| R10 | MEDIUM | God struct | `detection.rs:17-37` | `OutputChunkSignals` has 17 boolean fields. Group into `ApprovalSignals` and `PromptContextSignals` sub-structs. |
| R11 | LOW | Boilerplate | `style_schema.rs:362-411` | 10 identical `impl ThemeDefaultable` blocks. Use a declarative macro. |
| R12 | LOW | Repetitive dispatch | `input/parser.rs:44-121` | 15+ match arms each call `flush_pending` then `push(InputEvent::Xxx)`. Extract into const lookup table or helper. |
| R13 | LOW | Duplicated logic | `wake_word.rs:253-268, 328-356` | `WakeListener` destructure-try-join-reconstruct pattern duplicated. Add `fn try_join(self) -> Result<(), WakeListener>`. |
| R14 | LOW | Magic numbers | `legacy_ui.rs:179-184` | 6 hardcoded `Color::Rgb(...)` values. Define named constants or derive from theme. |
| R15 | LOW | Clone-heavy | `banner.rs:133-144` | `BannerConfig` uses owned `String` fields for known-domain values. Use enums (`Theme`, `Pipeline`) instead. |
| R16 | LOW | Leaky abstraction | `render.rs:73-381` (10+ call sites) | `terminal_host()` called repeatedly across render functions. Accept `TerminalHost` as parameter or thread through render context. |
| R17 | LOW | Duplicated logic | `style_pack/state.rs:52-157` | Every state accessor has near-duplicated `#[cfg(test)]` and `#[cfg(not(test))]` bodies. Define `StateStorage<T>` trait or unify on single `Mutex` path. |
| R18 | LOW | Repetitive match | `wake_word/matcher.rs:262-292` | 24 manually expanded phonetic variant match arms. Extract into `SEND_WORD_VARIANTS` + `SEND_SUFFIX_WORDS` lookup. |

### Python Code Smell Findings

| # | Severity | Category | File(s) | Description |
|---|---|---|---|---|
| P1 | HIGH | Duplicated logic | `cli_parser/quality.py` vs `cli_parser/builders_checks.py`, `cli_parser/reporting.py` vs `cli_parser/builders_ops.py` | ~430 lines of identical argparse registration across two file pairs. Pick one canonical source, delete duplicate. |
| P2 | HIGH | Duplicated boilerplate | All 9 `check_*.py` in `dev/scripts/checks/` | Identical try/except import fallback blocks repeated 3-4 times per file (~180 lines total). Make checks directory a proper package or add shared bootstrap. |
| P3 | MEDIUM | Duplicated logic | `mcp_tools.py:92-135` | `tool_status_snapshot` and `tool_report_snapshot` near-identical. Extract `_snapshot_handler(tool_name, include_ci_default)`. |
| P4 | MEDIUM | Duplicated error handling | 8 guard scripts | Identical 10-line `RuntimeError` catch block in every `main()`. Extract `emit_error_report()` into `rust_guard_common.py`. |
| P5 | MEDIUM | God functions | `check_rust_lint_debt.py` (192 lines), `check_code_shape.py` (186 lines), `mcp_transport.py` (150 lines), `hygiene.py` (146 lines) | `main()` / `run()` / `serve_stdio()` handle parsing, scanning, metrics, and reporting in one function. Extract `_scan_files()`, `_emit_report()`, or use method dispatch dict. |
| P6 | MEDIUM | Duplicated helpers | `check_duplicate_types.py`, `check_structural_complexity.py` | Both contain identical `_collect_rust_files()` and `_normalize_changed_paths()`. Move to `rust_guard_common.py`. |
| P7 | MEDIUM | Duplicated helpers | `check_code_shape.py`, `check_rust_audit_patterns.py` | Both reinvent `_list_changed_paths()` which already exists in `git_change_paths.py` as `list_changed_paths_with_base_map()`. Migrate. |
| P8 | MEDIUM | Stringly-typed dicts | `mcp.py:28-90`, `mcp_tools.py:92-212` | `_load_allowlist()` returns raw dicts (`result["ok"]`, `result["error"]`). Use `@dataclass AllowlistResult`. |
| P9 | MEDIUM | Missing abstraction | `mcp.py:199-261` | Same error payload dict pattern repeated 4 times. Extract `_emit_mcp_error(args, msg, code)`. |
| P10 | MEDIUM | Deep nesting | `collect.py:238-298` | 5 indentation levels in `collect_dev_log_summary()`. Extract `_parse_session_file(path) -> SessionStats`. |
| P11 | MEDIUM | Inconsistent timestamps | Multiple Python files | Some use `datetime.now(timezone.utc)` (UTC), some use `datetime.now()` (local time). Reports have mixed timezones. Standardize on UTC. |
| P12 | LOW | Magic numbers | `process_sweep.py:77`, `hygiene.py:183` | Raw `86400` for seconds-per-day. Define `SECONDS_PER_DAY` constant. |
| P13 | LOW | Stringly-typed dicts | `audit_scaffold.py:19-83`, `check_router_constants.py:71-158` | `GUARD_SPECS` and `RISK_ADDONS` use plain dicts. Use `@dataclass(frozen=True)`. |
| P14 | LOW | Global state | All 9 guard scripts | `guard = GuardContext(REPO_ROOT)` at module level. Create inside `main()` and pass as parameter for testability. |
| P15 | LOW | Overlapping constants | `check_router_constants.py:27-59`, `docs_check_policy.py:19-52` | Both define overlapping `TOOLING_CHANGE_PREFIXES` / `DOCS_PREFIXES`. Extract shared `PATH_CLASSIFICATION` module. |
| P16 | LOW | Compatibility shims | `docs_check_constants.py`, `docs_check_support.py` | Re-export-only modules that add import indirection. Delete once all callers import from canonical source. |

### Phase-7 Priority Queue (MP-354)

Prioritized execution order after validating findings against current code.

| Priority | Scope | Status | Notes |
|---|---|---|---|
| 1 | `R2 + R3` Writer adapter ownership + `handle_pty_output` decomposition + timing/policy de-tangling | complete (`Steps 7a/7b/7c/7d/7e/7f`) | Highest regression source in current runtime path is now closed with checkpoint parity. |
| 2 | `R1` startup decomposition (`main.rs`) | complete (`Step 7d`) | Phase split landed with checkpoint parity and code-shape remediation. |
| 3 | `R4` shared `create_vad_engine` owner | complete (`Step 7e`) | Shared `audio::create_vad_engine` now owns runtime + wake-word + benchmark callers. |
| 4 | `P2 + P4 + P6 + P7` guard bootstrap/helper dedup | complete (`Step 7f`) | Shared guard bootstrap/error path and helper ownership are now centralized in check utilities. |
| 5 | `R8 + R9 + R10` typed context + validator split + signal grouping | complete | Typed context ownership, validation helper split, and prompt-signal grouping landed with checkpoint parity. |
| 6 | `R6 + R7 + R11` style/theme mapping cleanup | complete | Glyph-table consolidation, runtime→schema conversion dedup, and `ThemeDefaultable` macro cleanup landed with checkpoint parity. |
| 7 | `R12 + R13 + R18` input/wake-word low-risk dedup cleanup | complete | Control-byte dispatch helper extraction, `WakeListener::try_join` lifecycle dedup, and send-intent lookup-table matcher simplification landed with checkpoint parity. |
| 8 | `R14 + R15 + R16 + R17` residual low-risk cleanup (legacy/banner/render/style-pack state) | complete | Named legacy UI color constants, typed `BannerConfig` ownership, render host-resolution threading cleanup, and style-pack state accessor dedup landed with checkpoint parity. |
| 9 | `P11 + P12` Python residual reporting cleanup | complete | UTC/Z report timestamp normalization landed across tooling/check emitters, and explicit `SECONDS_PER_DAY` constants now own process/report age math. |

Revalidation note for Python parser finding `P1`:

1. `cli_parser/quality.py` vs `cli_parser/builders_checks.py` and
   `cli_parser/reporting.py` vs `cli_parser/builders_ops.py` are currently
   split-owner parser modules, not direct copy-paste twins in current `develop`
   state.
2. Keep `P1` as a conditional cleanup candidate only if a concrete duplication
   diff proves net deletion without reducing parser ownership clarity.

## Audit Evidence

| Check | Evidence | Status |
|---|---|---|
| `python3 dev/scripts/devctl.py list` + `python3 dev/scripts/devctl.py docs-check --strict-tooling` + `python3 dev/scripts/devctl.py hygiene --strict-warnings` + `python3 dev/scripts/devctl.py orchestrate-status --format md` + `python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md` + `python3 dev/scripts/checks/check_agents_contract.py` + `python3 dev/scripts/checks/check_release_version_parity.py` + `python3 dev/scripts/checks/check_bundle_workflow_parity.py` + `python3 dev/scripts/checks/check_active_plan_sync.py` + `python3 dev/scripts/checks/check_multi_agent_sync.py` + `python3 dev/scripts/checks/check_cli_flags_parity.py` + `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120` + `python3 dev/scripts/checks/check_code_shape.py` + `python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop --format json` + `python3 dev/scripts/checks/check_structural_complexity.py --since-ref origin/develop --format json` + `python3 dev/scripts/checks/check_workflow_shell_hygiene.py` + `python3 dev/scripts/checks/check_workflow_action_pinning.py` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations` + `python3 dev/scripts/checks/check_compat_matrix.py` + `python3 dev/scripts/checks/compat_matrix_smoke.py` + `python3 dev/scripts/checks/check_naming_consistency.py` + `python3 dev/scripts/checks/check_rust_test_shape.py` + `python3 dev/scripts/checks/check_rust_lint_debt.py` + `python3 dev/scripts/checks/check_rust_best_practices.py` + `python3 dev/scripts/checks/check_rust_runtime_panic_policy.py` + `python3 -m unittest dev.scripts.devctl.tests.test_check_bootstrap dev.scripts.devctl.tests.test_script_catalog` + `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md` + `find . -maxdepth 1 -type f -name '--*'` | MP-354 Python residual `P11 + P12` checkpoint rerun is green after UTC/Z tooling/check timestamp normalization (`check_bootstrap.py` + `devctl/time_utils.py` + report emitters), explicit `SECONDS_PER_DAY` age-math constants (`process_sweep.py`, `hygiene.py`, `reports_retention.py`, `check_screenshot_integrity.py`), `check_bootstrap.py` catalog/README registration, and focused bootstrap helper unit coverage; initial `common.py` shape regression was resolved by extracting the shared timestamp helper into `devctl/time_utils.py`. | done |
| `python3 dev/scripts/devctl.py check --profile ci` + `python3 dev/scripts/devctl.py docs-check --strict-tooling` + `python3 dev/scripts/checks/check_active_plan_sync.py` + `python3 dev/scripts/checks/check_multi_agent_sync.py` + `python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_structural_complexity.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations` + `cd rust && cargo test --bin voiceterm` | MP-354 residual low-risk `R14 + R15 + R16 + R17` checkpoint rerun is green after named legacy UI color constants (`legacy_ui.rs`), typed banner config ownership (`banner.rs` + `main.rs`), render host-resolution threading cleanup (`writer/render.rs`), and style-pack override state accessor dedup (`theme/style_pack/state.rs`); direct runtime checkpoint remains green (`1537 passed`, `0 failed`). | done |
| `cd rust && cargo test --lib legacy_ui:: -- --nocapture` + `cd rust && cargo test --bin voiceterm banner::tests:: -- --nocapture` + `cd rust && cargo test --bin voiceterm writer::render::tests:: -- --nocapture` + `cd rust && cargo test --bin voiceterm theme::style_pack::tests:: -- --nocapture` | focused regression pack is green for the R14/R15/R16/R17 slice (legacy UI rendering constants, startup banner config typing, writer render host threading, and style-pack runtime override state behavior). | done |
| `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` | required post-direct-`cargo test` process-sweep rerun completed for R14/R15/R16/R17 scope; no failures (sandbox-only `ps` permission warnings expected). | done |
| `python3 dev/scripts/devctl.py check --profile ci` + `python3 dev/scripts/devctl.py docs-check --strict-tooling` + `python3 dev/scripts/checks/check_active_plan_sync.py` + `python3 dev/scripts/checks/check_multi_agent_sync.py` + `python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_structural_complexity.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations` + `cd rust && cargo test --bin voiceterm` | MP-354 queued `R12 + R13 + R18` checkpoint rerun is green after parser control-byte dispatch dedup (`input/parser.rs`), wake-listener lifecycle join dedup (`wake_word.rs`), and lookup-based send-intent suffix matching (`wake_word/matcher.rs`); direct runtime checkpoint remains green (`1537 passed`, `0 failed`). | done |
| `cd rust && cargo test --bin voiceterm input::parser::tests:: -- --nocapture` + `cd rust && cargo test --bin voiceterm wake_word::tests:: -- --nocapture` | focused regression pack is green for the R12/R13/R18 slice (input parser control dispatch, wake listener lifecycle ownership, and wake-word send-intent suffix matching). | done |
| `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` | required post-direct-`cargo test` process-sweep rerun completed for R12/R13/R18 scope; no failures (sandbox-only `ps` permission warnings expected). | done |
| `python3 dev/scripts/devctl.py check --profile ci` + `python3 dev/scripts/devctl.py docs-check --strict-tooling` + `python3 dev/scripts/checks/check_active_plan_sync.py` + `python3 dev/scripts/checks/check_multi_agent_sync.py` + `python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_structural_complexity.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations` + `cd rust && cargo test --bin voiceterm` | MP-354 queued `R6 + R7 + R11` checkpoint rerun is green after glyph-table consolidation (`theme/mod.rs`), runtime→schema conversion dedup (`theme/style_pack/apply.rs`), and macro-based `ThemeDefaultable` cleanup (`theme/style_schema.rs`); direct runtime checkpoint remains green (`1535 passed`, `0 failed`). | done |
| `cd rust && cargo test --bin voiceterm theme:: -- --nocapture` + `cd rust && cargo check --bin voiceterm --features theme_studio_v2` | focused regression pack is green for the R6/R7/R11 style/theme mapping slice (theme glyph resolution behavior + runtime override conversion path + style-schema normalization path). | done |
| `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` | required post-direct-`cargo test` process-sweep rerun completed for R6/R7/R11 scope; no failures (sandbox-only `ps` permission warnings expected). | done |
| `python3 dev/scripts/devctl.py check --profile ci` + `python3 dev/scripts/devctl.py docs-check --strict-tooling` + `python3 dev/scripts/checks/check_active_plan_sync.py` + `python3 dev/scripts/checks/check_multi_agent_sync.py` + `python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_structural_complexity.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations` + `cd rust && cargo test --bin voiceterm` | MP-354 queued `R8 + R9 + R10` checkpoint rerun is green after typed `RuleEvalContext` ownership, `AppConfig::validate` helper decomposition, and grouped prompt-occlusion output signals; direct runtime checkpoint remains green (`1535 passed`, `0 failed`). | done |
| `cd rust && cargo test --lib config::tests:: -- --nocapture` + `cd rust && cargo test --bin voiceterm event_loop::prompt_occlusion::tests:: -- --nocapture` + `cd rust && cargo check --bin voiceterm --features theme_studio_v2` | focused regression pack is green for the R8/R9/R10 slice (`config` validation contracts, prompt-occlusion signal behavior, and feature-gated Theme Studio rule-profile compilation). | done |
| `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` | required post-direct-`cargo test` process-sweep rerun completed for R8/R9/R10 scope; no failures (sandbox-only `ps` permission warnings expected). | done |
| `python3 dev/scripts/devctl.py check --profile ci` + `python3 dev/scripts/devctl.py docs-check --strict-tooling` + `python3 dev/scripts/checks/check_active_plan_sync.py` + `python3 dev/scripts/checks/check_multi_agent_sync.py` + `python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_structural_complexity.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations` + `cd rust && cargo test --bin voiceterm` | Step-7f checkpoint bundle rerun is green after shared Python guard bootstrap/helper dedup migration (`check_bootstrap.py` + `rust_guard_common.py` helper ownership); direct runtime checkpoint remains green (`1535 passed`, `0 failed`). | done |
| `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` | required post-direct-`cargo test` process-sweep rerun completed for Step-7f scope; no failures (sandbox-only `ps` permission warnings expected). | done |
| `python3 dev/scripts/devctl.py check --profile ci` + `python3 dev/scripts/devctl.py docs-check --strict-tooling` + `python3 dev/scripts/checks/check_active_plan_sync.py` + `python3 dev/scripts/checks/check_multi_agent_sync.py` + `python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_structural_complexity.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations` + `cd rust && cargo test --bin voiceterm` | Step-7e checkpoint bundle rerun is green after shared `audio::create_vad_engine` factory consolidation and duplicate owner removal (`voice`, `wake_word`, `latency_measurement`); direct runtime checkpoint remains green (`1535 passed`, `0 failed`). | done |
| `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` | required post-direct-`cargo test` process-sweep rerun completed for Step-7e scope; no failures (sandbox-only `ps` permission warnings expected). | done |
| `python3 dev/scripts/devctl.py check --profile ci` + `python3 dev/scripts/devctl.py docs-check --strict-tooling` + `python3 dev/scripts/checks/check_active_plan_sync.py` + `python3 dev/scripts/checks/check_multi_agent_sync.py` + `python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_structural_complexity.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations` + `cd rust && cargo test --bin voiceterm` | Step-7d checkpoint bundle rerun is green after startup phase decomposition; initial CI rerun surfaced a `main.rs` shape-limit regression, remediated by moving inline `main` tests to `main_tests.rs` without runtime behavior change (`cargo test --bin voiceterm`: `1535 passed`, `0 failed`). | done |
| `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` | required post-direct-`cargo test` process-sweep rerun completed for Step-7d scope; no failures (sandbox-only `ps` permission warnings expected). | done |
| `python3 dev/scripts/devctl.py check --profile ci` + `python3 dev/scripts/devctl.py docs-check --strict-tooling` + `python3 dev/scripts/checks/check_active_plan_sync.py` + `python3 dev/scripts/checks/check_multi_agent_sync.py` + `python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_structural_complexity.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations` + `cd rust && cargo test --bin voiceterm` | Step-7c checkpoint bundle rerun is green after timing/policy runtime-variant de-tangling and plan updates (`cargo test --bin voiceterm`: `1535 passed`, `0 failed`). | done |
| `python3 dev/scripts/devctl.py check --profile prepush` + `./dev/scripts/tests/measure_latency.sh --voice-only --synthetic` + `./dev/scripts/tests/measure_latency.sh --ci-guard` | Step-7c timing/latency risk add-ons are green after runtime-variant timing/policy changes (`voice-only` synthetic avg totals: short `1979.0 ms`, medium `3968.9 ms`; CI guard totals unchanged at short `1700.0 ms`, medium `3700.0 ms`). | done |
| `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` | required post-direct-`cargo test` process-sweep rerun completed for Step-7c scope; no failures (sandbox-only `ps` permission warnings expected). | done |
| `python3 dev/scripts/devctl.py check --profile ci` + `python3 dev/scripts/devctl.py docs-check --strict-tooling` + `python3 dev/scripts/checks/check_active_plan_sync.py` + `python3 dev/scripts/checks/check_multi_agent_sync.py` + `python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_structural_complexity.py --since-ref origin/develop` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations` + `cd rust && cargo test --bin voiceterm` | Step-7b checkpoint bundle rerun is green after `handle_pty_output` stage decomposition and docs updates. | done |
| `python3 dev/scripts/devctl.py check --profile prepush` + `./dev/scripts/tests/measure_latency.sh --voice-only --synthetic` + `./dev/scripts/tests/measure_latency.sh --ci-guard` | Step-7b timing/latency risk add-ons are green; both synthetic latency guards execute successfully after fixing empty-array expansion in `measure_latency.sh` for `set -u` shells. | done |
| `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` | required post-direct-`cargo test` process-sweep rerun is complete; no failures (sandbox-only `ps` permission warnings remain expected). | done |
| `python3 dev/scripts/checks/check_active_plan_sync.py` + `python3 dev/scripts/checks/check_multi_agent_sync.py` | Step-7a checkpoint rerun confirms active-doc and multi-agent governance remain aligned after adapter-state ownership split (`ok: True` for both checks). | done |
| `python3 dev/scripts/devctl.py docs-check --strict-tooling` | strict-tooling docs governance rerun is green after Step-7a plan updates (`ok: True`, `active_plan_sync_ok: True`, `multi_agent_sync_ok: True`). | done |
| `python3 dev/scripts/devctl.py check --profile ci` | full CI-profile checkpoint passed after Step-7a implementation (`clippy` success, ai-guard checks green, and test suites completed including `src/lib.rs` `543` tests, `src/bin/voiceterm` `1661` tests, and CLI integration tests). | done |
| `cd rust && cargo test --bin voiceterm` | required direct runtime checkpoint passed for Step-7a scope (`1535 passed`, `0 failed`). | done |
| `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` | required post-direct-cargo process sweep completed; no failures (sandbox emitted expected `ps` permission warnings for `process-sweep-pre/post`). | done |
| `python3 dev/scripts/devctl.py check --profile ci --format md` | confirms full CI profile is green after continuation rerun (`fmt`, `clippy`, AI-guard checks, `clippy-high-signal`, and full workspace tests) | done |
| `python3 dev/scripts/devctl.py docs-check --strict-tooling` + `python3 dev/scripts/devctl.py hygiene --fix --strict-warnings` + `python3 dev/scripts/devctl.py orchestrate-status --format md` + `python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md` | confirms tooling-bundle preflight commands are green in current branch state | done |
| `python3 dev/scripts/devctl.py hygiene --fix --strict-warnings` (2026-03-05 architecture-refresh rerun) | strict hygiene now passes after script-catalog alignment (`duplication_audit_support` registered) and local cache cleanup via `--fix` | done |
| `python3 dev/scripts/checks/check_code_shape.py` + `python3 dev/scripts/checks/check_rust_lint_debt.py` + `python3 dev/scripts/checks/check_rust_best_practices.py` + `python3 dev/scripts/checks/check_rust_runtime_panic_policy.py` + `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md` | confirms post-override shape/rust/style guards are green and the `check_rust_lint_debt.py` soft-limit violation is cleared | done |
| `python3.11 dev/scripts/devctl.py list` + `python3 dev/scripts/devctl.py list` | confirms `devctl` command surface now parses under both Python 3.11 (CI contract) and Python 3.12 after release-gates rendering fix | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_check_duplicate_types dev.scripts.devctl.tests.test_check_structural_complexity dev.scripts.devctl.tests.test_check_duplication_audit dev.scripts.devctl.tests.test_check dev.scripts.devctl.tests.test_audit_scaffold` | validates new duplicate-type/structural-complexity/duplication-audit scripts and updated AI-guard/audit-scaffold wiring coverage | done |
| `python3 dev/scripts/checks/check_duplicate_types.py --format md` + `python3 dev/scripts/checks/check_structural_complexity.py --format md` + `python3 dev/scripts/devctl.py check --profile ai-guard --skip-tests --format md` | confirms new MP-346 guardrails execute cleanly in direct mode and inside AI-guard profile orchestration | done |
| `python3 dev/scripts/checks/check_duplication_audit.py --report-path /tmp/nonexistent-jscpd-report.json --format md` | confirms periodic `jscpd` wrapper emits deterministic failure guidance when report evidence is missing (expected until scheduled/local jscpd runs are recorded) | done |
| `python3 dev/scripts/checks/check_duplication_audit.py --run-jscpd --allow-missing-tool --run-python-fallback --format md` + `python3 -m unittest dev.scripts.devctl.tests.test_check_duplication_audit` | confirms duplication evidence can be regenerated in constrained environments through explicit fallback scanning while preserving `jscpd`-first flow and regression coverage (`8` tests passed) | done |
| `nl -ba .github/workflows/rust_ci.yml | sed -n '44,132p'` + `nl -ba .github/workflows/release_preflight.yml | sed -n '30,132p'` + `nl -ba .github/workflows/security_guard.yml | sed -n '68,148p'` | confirms runtime/release/security workflows now resolve commit ranges and pass `--since-ref/--head-ref` into `devctl check --profile ai-guard` | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_check dev.scripts.devctl.tests.test_check_naming_consistency dev.scripts.devctl.tests.test_check_rust_runtime_panic_policy dev.scripts.devctl.tests.test_check_rust_test_shape dev.scripts.devctl.tests.test_check_rust_lint_debt dev.scripts.devctl.tests.test_collect_clippy_warnings` + `python3 dev/scripts/devctl.py check --profile ai-guard --format md` + `python3 dev/scripts/devctl.py docs-check --strict-tooling --format md` + `python3 dev/scripts/devctl.py hygiene --fix --strict-warnings --format md` | confirms clippy sequencing fix, naming-check shape split, and strict tooling/hygiene governance remain green | done |
| `cd rust && cargo fmt --all` + `python3 dev/scripts/rust_tools/collect_clippy_warnings.py --working-directory rust --deny-warnings --quiet-json-stream --propagate-exit-code --output-lints-json /tmp/clippy-lints-postfix.json` + `python3 dev/scripts/devctl.py check --profile ai-guard --skip-tests --format md` | confirms strict clippy is back to zero warnings after lint-family updates and AI-guard/clippy-high-signal gates remain green | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_collect_clippy_warnings dev.scripts.devctl.tests.test_check_clippy_high_signal dev.scripts.devctl.tests.test_check_rust_test_shape dev.scripts.devctl.tests.test_check_rust_runtime_panic_policy dev.scripts.devctl.tests.test_check dev.scripts.devctl.tests.test_audit_scaffold` | confirms collector histogram output behavior, new Rust guard scripts, AI-guard wiring, and audit-scaffold integration are regression-safe | done |
| `python3 dev/scripts/checks/check_rust_test_shape.py --format md` + `python3 dev/scripts/checks/check_rust_runtime_panic_policy.py --format md` + `python3 dev/scripts/rust_tools/collect_clippy_warnings.py --working-directory rust --output-lints-json /tmp/clippy-lints.json` + `python3 dev/scripts/checks/check_clippy_high_signal.py --input-lints-json /tmp/clippy-lints.json --format md` | confirms new test-shape/runtime-panic guards and clippy high-signal baseline gate execute cleanly against current tree | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_workflow_shell_bridge dev.scripts.devctl.tests.test_check_workflow_shell_hygiene dev.scripts.devctl.tests.test_docs_check` | confirms workflow bridge, workflow-shell hygiene guard, and strict-tooling docs-check wiring regressions are green (`25` tests passed) | done |
| `python3 dev/scripts/devctl.py docs-check --strict-tooling --format md` | confirms strict-tooling governance gates remain green with workflow-shell hygiene enforcement active | done |
| `python3 dev/scripts/checks/check_workflow_shell_hygiene.py --format md` + `rg -n "find .*\\| head -n 1|python(?:3)? <<|python(?:3)? -c" .github/workflows/*.yml` | confirms no banned shell patterns remain in workflow run blocks | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_autonomy_workflow_bridge dev.scripts.devctl.tests.test_hygiene dev.scripts.devctl.tests.test_check_workflow_shell_hygiene` | confirms workflow bridge refactor + hygiene audit module split + workflow-shell suppression/discovery updates remain regression-safe (`39` tests passed) | done |
| `python3 dev/scripts/checks/check_code_shape.py` + `python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop --head-ref <git stash create snapshot>` | confirms both working-tree and simulated commit-range shape policies are green after module-split cleanup | done |
| `wc -l rust/src/bin/voiceterm/writer/state.rs` | reports `2750` lines | done |
| `nl -ba rust/src/bin/voiceterm/writer/state.rs | sed -n '600,1505p'` | `handle_message` spans `605..1486` and next top-level helper starts at `1493` | done |
| `wc -l rust/src/bin/voiceterm/writer/state.rs` (2026-03-04 closure rerun) | reports `448` lines after Step-2e decomposition extraction | done |
| `wc -l rust/src/bin/voiceterm/writer/state/{dispatch.rs,redraw.rs,profile.rs,display.rs,policy.rs,chunk_analysis.rs}` | confirms policy/dispatch/runtime-profile decomposition landed in dedicated modules | done |
| `sed -n '1,220p' rust/src/bin/voiceterm/runtime_compat.rs` | canonical host detection exists there today | done |
| `sed -n '1,220p' rust/src/bin/voiceterm/writer/render.rs` and `sed -n '160,280p' rust/src/bin/voiceterm/banner.rs` | duplicate host-detection logic confirmed | done |
| `sed -n '180,280p' rust/src/ipc/protocol.rs` and `sed -n '1,260p' rust/src/ipc/session/state.rs` | provider enum/capabilities limited to codex+claude | done |
| `sed -n '1,220p' rust/src/backend/mod.rs` | backend registry includes Gemini backend | done |
| `rg -n "antigravity|anti-gravity|anti gravity" .` | no runtime/source references outside docs/plans | done |
| `rg -n "antigravity" dev/config/compat/ide_provider_matrix.yaml` | returns no matches, confirming AntiGravity host/cells were removed from the active matrix scope | done |
| `rg -n "AntiGravity|deferred|runtime host fingerprint evidence" dev/active/MASTER_PLAN.md dev/active/INDEX.md README.md guides/USAGE.md` | confirms tracker/index/user docs now mark AntiGravity as deferred and outside active verified host scope | done |
| `sed -n '1,220p' dev/adr/0035-host-provider-boundary-ownership.md` + `sed -n '1,240p' dev/adr/0036-compat-matrix-governance-ci-fail-policy.md` | confirms Phase-6 ADR deliverables are present with `Status: Accepted` and `Date: 2026-03-05` | done |
| `python3 dev/scripts/devctl.py hygiene` | confirms ADR index/metadata governance stays green after adding ADR `0035` + `0036` (`ok: true`; warnings only) | done |
| `rg -n "parse_debug_env_flag|debug_bytes_preview" rust/src/bin/voiceterm/writer/state.rs rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs` | helper duplication confirmed | done |
| `cat dev/scripts/checks/check_code_shape.py` lines 60-115 | `writer/state.rs` absent from `PATH_POLICY_OVERRIDES`; 6 other files frozen | done |
| `nl -ba dev/scripts/checks/check_code_shape.py` | hotspot freeze overrides now include `writer/state.rs`, `prompt_occlusion.rs`, and `claude_prompt_detect.rs`; plus new `--absolute` mode | done |
| `python3 dev/scripts/checks/check_code_shape.py --absolute --format md` | absolute mode executes and reports repository-wide hard-limit results | done |
| `nl -ba dev/scripts/devctl/commands/check_profile.py` + `python3 dev/scripts/devctl.py check --profile ci --dry-run` | `ci` profile now enables AI-guard steps | done |
| `nl -ba dev/scripts/devctl/cli_parser/quality.py` + `nl -ba dev/scripts/devctl/commands/check.py` + `nl -ba dev/scripts/devctl/commands/check_support.py` | `devctl check` now accepts `--since-ref/--head-ref` and forwards commit-range args to supported AI-guard scripts | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_check_code_shape_guidance` | includes evaluator branch coverage for `_evaluate_shape` + `_evaluate_absolute_shape` | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_check.CheckProfileTests dev.scripts.devctl.tests.test_check.CheckProfileFlagConflictTests dev.scripts.devctl.tests.test_check.CheckProgressFeedbackTests` | validates parser/profile/AI-guard wiring updates and ref-forwarding behavior | done |
| `dev/reports/mp346/checkpoints/20260302T032908Z-cp000/exit_codes.env` + `summary.md` | `CP-000` captured with explicit bundle pass/fail and `no-go` operator decision | done |
| `dev/reports/mp346/baselines/host_provider_mix_counts.txt` | baseline mixed host/provider conditional counts captured for non-regression tracking | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_check_rust_audit_patterns` | validates strict `rust/src/**` scope matching plus commit-range/stale-warning main-path behavior | done |
| `python3 dev/scripts/checks/check_rust_audit_patterns.py --format json` + `python3 dev/scripts/checks/check_rust_audit_patterns.py --since-ref origin/master --head-ref HEAD --format json` | confirms stale-pattern warning emits in working-tree mode and ref-aware commit-range mode executes with explicit scope filtering | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_check_ide_provider_isolation` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md` | report-only isolation check landed with dedicated unit coverage and runtime report output | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_path_audit` + `python3 dev/scripts/devctl.py path-audit --format md` | path-audit now aggregates legacy script-path scan and workspace-contract scan with dedicated workspace-token detection tests | done |
| `python3 dev/scripts/checks/check_active_plan_sync.py --format md` | confirms expanded `REQUIRED_REGISTRY_ROWS` + `SPEC_RANGE_PATHS` coverage remains synchronized with active-doc registry | done |
| `wc -l dev/scripts/checks/check_active_plan_sync.py` + `python3 dev/scripts/checks/check_code_shape.py --format md` | confirms `check_active_plan_sync.py` is back below soft-limit budget (`441` lines) and shape guard passes in working-tree mode | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_check_agents_contract` + `python3 dev/scripts/checks/check_agents_contract.py` | adds dedicated contract-script coverage, including router-snippet enforcement for `rust/src/**` | done |
| `python3 dev/scripts/devctl.py hygiene` | confirms script-inventory governance is green after documenting `check_ide_provider_isolation.py` in `dev/scripts/README.md` | done |
| `python3 dev/scripts/devctl.py path-audit --format md` | confirms aggregate path-audit output reports `checked_files` and `unique_checked_files` with zero legacy/workspace-contract violations | done |
| `nl -ba README.md`, `nl -ba guides/USAGE.md`, `nl -ba dev/ARCHITECTURE.md`, `nl -ba guides/CLI_FLAGS.md` | confirms Gemini backend wording is aligned to "experimental (currently not working)" across user/developer docs | done |
| `nl -ba .github/workflows/rust_ci.yml` + `nl -ba .github/workflows/README.md` | confirms Rust CI now includes `cargo doc --workspace --no-deps --all-features` and workflow docs describe the added gate | done |
| `cd rust && cargo doc --workspace --no-deps --all-features` | validates the new CI documentation compile gate command completes successfully in the current tree | done |
| `nl -ba .github/workflows/security_guard.yml` + `nl -ba .github/workflows/release_preflight.yml` + `nl -ba .github/workflows/README.md` | confirms dependency-policy CI/release decision is enforced via explicit `cargo deny` gates and documented in workflow guidance | done |
| `cargo update -p bytes --precise 1.11.1 --manifest-path rust/Cargo.toml` + `rg -n "name = \"bytes\"|version = \"1.11.1\"" rust/Cargo.lock` + `cargo deny --manifest-path rust/Cargo.toml check advisories bans licenses sources` | confirms transitive `bytes` moved to patched `1.11.1` and deny gate now passes with current policy exceptions | done |
| `cat dev/reports/mp346/baselines/hotspot_branch_complexity_baseline.txt` | captures Phase-0 hotspot size + branch-site baseline for `writer/state.rs`, `event_loop.rs`, `runtime_compat.rs`, and `ipc/router.rs` | done |
| `nl -ba .github/workflows/rust_ci.yml` + `nl -ba .github/workflows/README.md` | confirms CI baseline hardening now includes MSRV (`1.70.0`), feature-mode matrix (`default`, `--no-default-features`), and macOS runtime smoke validation | done |
| `nl -ba .github/workflows/failure_triage.yml` + workflow `name:` scan | confirms failure triage watchlist now includes `Swarm Run` and `publish_release_binaries` with name parity to workflow headers | done |
| `nl -ba dev/scripts/checks/check_code_shape.py` + `nl -ba dev/scripts/checks/code_shape_policy.py` | confirms stale override review-window gate (`--stale-override-review-window-days`) and removal of stale overrides for `event_loop/input_dispatch.rs` + `status_line/buttons.rs` | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_check_code_shape_guidance` | validates stale-override evaluator coverage in addition to existing shape-evaluator branch tests | done |
| `nl -ba dev/active/MASTER_PLAN.md` + `nl -ba dev/active/review_channel.md` + `nl -ba dev/BACKLOG.md` | confirms board/ledger status sync, cross-plan shared-hotspot ownership/freeze gate activation, and local backlog ID deconfliction (`LB-*`) | done |
| `cat dev/reports/mp346/checkpoints/20260302T155409Z-cp004/summary.md` + `exit_codes.env` | confirms CP-004 full checkpoint bundle pass with explicit `go (phase 0.5 only)` and retained phase-1+ `no-go` | done |
| `cat dev/reports/mp346/checkpoints/20260302T162839Z-cp005/summary.md` + `exit_codes.env` | confirms CP-005 Phase-0.5 closure bundle pass with explicit `go (manual matrix execution)` and retained phase-1+ `no-go` pending manual matrix evidence | done |
| `cat dev/reports/mp346/checkpoints/20260304T010010Z-cp006/summary.md` | confirms CP-006 operator manual-matrix attestation (`5/7` cells pass) plus explicit phase-1+ `go`; remaining `Other` host cells are sequenced to post-cleanup stabilization validation | done |
| `cat dev/reports/mp346/checkpoints/20260304T113723Z-cp007/summary.md` + `exit_codes.env` | confirms CP-007 Phase-2a checkpoint bundle pass with explicit `go (phase 2b next)` decision while reusing CP-006 manual-matrix attestation | done |
| `cat dev/reports/mp346/checkpoints/20260304T114813Z-cp008/summary.md` + `exit_codes.env` | confirms CP-008 Phase-2b checkpoint bundle pass with explicit `go (phase 2c next)` decision while reusing CP-006 manual-matrix attestation | done |
| `cat dev/reports/mp346/checkpoints/20260304T121404Z-cp009/summary.md` + `exit_codes.env` | confirms CP-009 Phase-2c checkpoint bundle pass with explicit `go (phase 2d next)` decision while reusing CP-006 manual-matrix attestation | done |
| `cat dev/reports/mp346/checkpoints/20260304T123641Z-cp010/summary.md` + `exit_codes.env` | confirms CP-010 Phase-2d checkpoint bundle pass with explicit `go (phase 2e next)` decision while reusing CP-006 manual-matrix attestation | done |
| `cat dev/reports/mp346/checkpoints/20260304T130908Z-cp011/summary.md` + `exit_codes.env` | confirms CP-011 Phase-2e partial checkpoint bundle pass with explicit hold (`continue phase 2e`) while reusing CP-006 manual-matrix attestation | done |
| `rg -n "struct HostTimingConfig|impl HostTimingConfig" rust/src/bin/voiceterm/runtime_compat.rs` + `rg -n "fn host_timing\\(&self\\)|should_preclear_bottom_rows|scroll_redraw_min_interval_for_profile|should_defer_non_urgent_redraw_for_recent_input" rust/src/bin/voiceterm/writer/state.rs` | confirms Phase-2a host timing extraction now routes writer timing behavior through canonical `HostTimingConfig` keyed by `TerminalHost` | done |
| `nl -ba rust/src/bin/voiceterm/writer/state/tests.rs` + matrix test names (`*_matrix_*`) | verifies 9-way host/provider matrix characterization coverage for preclear, scroll redraw interval, and force-redraw trigger timing | done |
| `rg -n "struct PreclearPolicy|struct PreclearOutcome|fn resolve\\(ctx: PreclearPolicyContext\\)|fn outcome\\(self, pre_cleared: bool\\)" rust/src/bin/voiceterm/writer/state.rs` + `rg -n "preclear_policy_.*flags|preclear_policy_outcome_without_preclear_disables_post_preclear_flags" rust/src/bin/voiceterm/writer/state/tests.rs` | confirms Phase-2b extraction landed typed preclear policy outputs and focused regression coverage for policy flag outcomes | done |
| `rg -n "struct RedrawPolicyContext|struct RedrawPolicy|fn resolve\\(ctx: RedrawPolicyContext" rust/src/bin/voiceterm/writer/state.rs` + `rg -n "redraw_policy_.*" rust/src/bin/voiceterm/writer/state/tests.rs` | confirms Phase-2c extraction landed typed redraw policy outputs wired to `PreclearOutcome` and focused regression coverage for scroll/non-scroll/destructive redraw policy outcomes | done |
| `rg -n "struct IdleRedrawTimingContext|resolve_idle_redraw_timing|should_defer_non_urgent_redraw_for_recent_input" rust/src/bin/voiceterm/writer/timing.rs rust/src/bin/voiceterm/writer/state.rs` + `cd rust && cargo test --bin voiceterm writer::timing::tests::` | confirms Phase-2d extraction landed typed timing policy module for `maybe_redraw_status` idle/quiet-window gating with focused policy coverage | done |
| `nl -ba rust/src/bin/voiceterm/event_loop/input_dispatch.rs` + input ownership test names (`insert_pending_preserves_caret_*`, `hud_navigation_direction_from_arrow_*`) | verifies deterministic caret-vs-HUD arrow ownership contract coverage for Codex/Claude across Cursor/JetBrains/Other labels | done |
| `cd rust && cargo test --bin voiceterm` | validates runtime suite with new `rstest` dependency and Phase-0.5 characterization tests (`1387` passed) | done |
| `rg -n "should_force_single_line_full_hud_for_env" rust/src/bin/voiceterm/status_line/layout.rs rust/src/bin/voiceterm/status_line/buttons.rs rust/src/bin/voiceterm/runtime_compat.rs` | confirms status-line host/provider full-HUD fallback routing now consumes canonical runtime-compat helper instead of inline host+provider conditionals | done |
| `nl -ba rust/src/bin/voiceterm/writer/render.rs` | confirms writer render host-family detection now maps from `runtime_compat::detect_terminal_host()` and no longer carries duplicate host-sniffing helpers | done |
| `cd rust && cargo test --bin voiceterm single_line_full_hud_policy_only_for_claude_on_jetbrains && cargo test --bin voiceterm full_single_line_fallback && cargo test --bin voiceterm terminal_family_maps_from_runtime_terminal_host` | validates canonical single-line fallback policy helper, status-line full-HUD fallback behavior, and writer render host-mapping coverage | done |
| `python3 dev/scripts/devctl.py check --profile ci` | validates runtime guard/check/test profile for this slice (`fmt`, `clippy`, ai-guard scripts, and test lanes); sandbox-only warning observed for process sweep `ps` probing | done |
| `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_multi_agent_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'` | validates remaining `bundle.runtime` documentation/governance/shape/parity/lint gates for this slice | done |
| `nl -ba rust/src/bin/voiceterm/theme/texture_profile.rs` + `rg -n "detect_terminal_id_for_host|terminal_id_for_host|detect_terminal_host" rust/src/bin/voiceterm/theme/texture_profile.rs` | confirms `TerminalId` now layers Cursor/JetBrains routing through canonical runtime host detection before non-host terminal capability mapping | done |
| `cd rust && cargo test --bin voiceterm --features theme_studio_v2 texture_profile` | validates texture-profile host-layering regressions and fallback coverage (`24` passed) | done |
| `nl -ba rust/src/bin/voiceterm/runtime_compat.rs` + `rg -n "TERMINAL_HOST_CACHE|set_terminal_host_override|detect_terminal_host_from_env|detect_terminal_host\\(" rust/src/bin/voiceterm/runtime_compat.rs` + `nl -ba rust/src/bin/voiceterm/writer/render.rs` | confirms canonical host-detection cache ownership lives in runtime_compat with test override contract and writer render no longer duplicates host caching | done |
| `cd rust && cargo test --bin voiceterm runtime_compat::tests::detect_terminal_host_handles_jetbrains_and_cursor && cargo test --bin voiceterm runtime_compat::tests::detect_terminal_host_allows_thread_local_override && cargo test --bin voiceterm runtime_compat::tests::detect_terminal_host_override_resets_after_panic && cargo test --bin voiceterm writer::render::tests::cursor_terminal_uses_combined_cursor_save_restore_sequences && cargo test --bin voiceterm writer::render::tests::jetbrains_terminal_uses_dec_only_cursor_save_restore_sequences` | validates env fingerprint detection, thread-local override behavior (including unwind-safe reset), and writer render host-path non-regression coverage | done |
| `cd rust && cargo test --bin voiceterm` | validates full runtime suite after canonical host-cache contract cleanup (`1470` passed) | done |
| `python3 dev/scripts/devctl.py swarm_run --plan-doc dev/active/ide_provider_modularization.md --mp-scope MP-346 --run-label 20260304-035730Z-c01` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/20260304-035730Z-c01/summary.md` (2026-03-04 local run) | done |
| `python3 dev/scripts/devctl.py swarm_run --plan-doc dev/active/ide_provider_modularization.md --mp-scope MP-346 --run-label 20260304-035730Z-c02` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/20260304-035730Z-c02/summary.md` (2026-03-04 local run) | done |
| `rg -n "parse_debug_env_flag|claude_hud_debug_enabled|debug_bytes_preview" rust/src/bin/voiceterm/writer/state.rs rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs rust/src/bin/voiceterm/terminal.rs && nl -ba rust/src/bin/voiceterm/hud_debug.rs` | confirms duplicate HUD debug helpers were removed from runtime hotspots and centralized in shared `hud_debug` module | done |
| `cd rust && cargo test --bin voiceterm` | validates runtime suite after Phase-1.5 shared HUD debug extraction (`1471` passed) | done |
| `rg -n "backend_label_contains|backend_family_from_env|BackendFamily::Codex|BackendFamily::Claude" rust/src/bin/voiceterm/writer/state.rs && sed -n '128,180p' rust/src/bin/voiceterm/writer/state.rs` | confirms writer-state backend routing no longer uses raw label substring parsing and now consumes canonical `BackendFamily` mapping | done |
| `cd rust && cargo test --bin voiceterm` | validates runtime suite after BackendFamily routing update in writer state (`1471` passed) | done |
| `nl -ba rust/src/bin/voiceterm/provider_adapter.rs && rg -n "mod provider_adapter" rust/src/bin/voiceterm/main.rs` | confirms Phase-1.5 provider adapter contract module is defined and registered for runtime extraction follow-up | done |
| `cd rust && cargo test --bin voiceterm provider_adapter::tests && python3 dev/scripts/devctl.py check --profile ci` | validates provider adapter contract tests and confirms CI profile remains green after adding signature-only module (`1600` voiceterm-bin tests passed in check profile run) | done |
| `nl -ba rust/src/bin/voiceterm/ansi.rs && rg -n "strip_ansi_preserve_controls|crate::ansi::strip_ansi|strip_ansi_for_approval_window" rust/src/bin/voiceterm/prompt/strip.rs rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs rust/src/bin/voiceterm/memory/ingest.rs rust/src/bin/voiceterm/transcript_history.rs rust/src/bin/voiceterm/toast.rs` | confirms shared ANSI utility module landed and former duplicate stripping call sites now route through it | done |
| `nl -ba rust/src/bin/voiceterm/test_env.rs && rg -n "OnceLock<Mutex<\\(\\)>>" rust/src/bin/voiceterm` | confirms one canonical env-lock owner remains (`test_env.rs`) and duplicated per-module env-lock helpers were removed | done |
| `rg -n "claude_prompt_suppressed" rust/src/bin/voiceterm && rg -n "prompt_suppressed" rust/src/bin/voiceterm/status_line/state.rs rust/src/bin/voiceterm/terminal.rs rust/src/bin/voiceterm/event_loop.rs rust/src/bin/voiceterm/writer/state.rs` | confirms provider-neutral rename completed in runtime and no legacy field references remain in code | done |
| `cd rust && cargo test --bin voiceterm && python3 dev/scripts/devctl.py check --profile ci && python3 dev/scripts/devctl.py docs-check --user-facing && python3 dev/scripts/devctl.py hygiene && python3 dev/scripts/checks/check_active_plan_sync.py && python3 dev/scripts/checks/check_multi_agent_sync.py && python3 dev/scripts/checks/check_cli_flags_parity.py && python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120 && python3 dev/scripts/checks/check_code_shape.py && python3 dev/scripts/checks/check_rust_lint_debt.py && python3 dev/scripts/checks/check_rust_best_practices.py && markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md && find . -maxdepth 1 -type f -name '--*'` | validates full runtime and docs/governance bundle after Phase-1.5 closure slice (all passing; hygiene warnings remain non-blocking) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_check_ide_provider_isolation dev.scripts.devctl.tests.test_check_rust_lint_debt` | regression coverage for isolation scanner edge-cases + lint-debt inner-allow parsing passes (`14` tests) | done |
| `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md` | blocking isolation gate stays green after scanner hardening (`files_with_mixed_signals=3`, `unauthorized_files=0`) | done |
| `python3 dev/scripts/checks/check_rust_lint_debt.py --format md` | lint-debt gate stays green with inner `#![allow(...)]` parsing enabled (`violations=0`) | done |
| `python3 dev/scripts/checks/check_code_shape.py --format md` + `python3 dev/scripts/checks/check_code_shape.py --absolute --format md` | shape gates remain green after prompt/test decomposition and writer-profile cleanup (`function_violations=0`) | done |
| `python3 dev/scripts/checks/check_compat_matrix.py --format md` + `python3 dev/scripts/checks/compat_matrix_smoke.py --format md` | compatibility governance remains valid (`12/12` declared cells) with expected Gemini non-IPC warning (`overlay-only-experimental`) | done |
| `wc -l rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs rust/src/bin/voiceterm/prompt/claude_prompt_detect.rs rust/src/bin/voiceterm/prompt/claude_prompt_detect/tests.rs` | confirms prompt hotspot split (`prompt_occlusion.rs`=`1143`, `claude_prompt_detect.rs`=`623`) with extracted Claude detector tests in dedicated module | done |
| `nl -ba rust/src/bin/voiceterm/writer/state/profile.rs | sed -n '55,75p'` + `nl -ba rust/src/bin/voiceterm/writer/state/dispatch.rs | sed -n '388,404p'` + `nl -ba rust/src/bin/voiceterm/writer/state/redraw.rs | sed -n '120,156p'` | geometry-collapse policy now consumes RuntimeProfile `claude_jetbrains` boolean at writer call sites instead of raw host+backend tuple checks | done |
| `nl -ba rust/src/bin/voiceterm/writer/state/redraw.rs | sed -n '250,270p'` + `nl -ba rust/src/bin/voiceterm/runtime_compat.rs | sed -n '360,376p'` | JetBrains+Claude single-line fallback and cursor-toggle policy now route through profile/helper contracts rather than mixed inline conditionals | done |
| `cd rust && cargo test --bin voiceterm --quiet` | validates full runtime suite after post-CP-013 hardening and profile-based writer routing cleanup (`1501` passed) | done |
| `nl -ba rust/src/bin/voiceterm/provider_adapter.rs` + `nl -ba rust/src/bin/voiceterm/main.rs | sed -n '92,108p'` + `nl -ba rust/src/bin/voiceterm/main.rs | sed -n '524,540p'` | confirms Phase-3a adapter routing: runtime now constructs prompt detector via `build_prompt_occlusion_detector` and provider adapter owns Claude strategy wiring | done |
| `cd rust && cargo test --bin voiceterm provider_adapter::tests:: -- --nocapture` + `cd rust && cargo test --bin voiceterm prompt::claude_prompt_detect::tests:: -- --nocapture` | validates provider-adapter strategy wiring plus Claude detector behavior regressions (`6` and `36` tests passed) | done |
| `python3 dev/scripts/devctl.py check --profile ci` + `python3 dev/scripts/devctl.py docs-check --user-facing` + `python3 dev/scripts/devctl.py hygiene` + `python3 dev/scripts/checks/check_active_plan_sync.py --format md` + `python3 dev/scripts/checks/check_multi_agent_sync.py --format md` + `python3 dev/scripts/checks/check_cli_flags_parity.py` + `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120` + `python3 dev/scripts/checks/check_code_shape.py --format md` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations --format md` + `python3 dev/scripts/checks/check_compat_matrix.py --format md` + `python3 dev/scripts/checks/compat_matrix_smoke.py --format md` + `python3 dev/scripts/checks/check_rust_lint_debt.py --format md` + `python3 dev/scripts/checks/check_rust_best_practices.py --format md` + `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md` + `find . -maxdepth 1 -type f -name '--*'` | full Step-3a runtime/governance/docs validation bundle passes (hygiene warnings remain non-blocking) | done |
| `nl -ba rust/src/ipc/protocol.rs | sed -n '220,340p'` + `nl -ba rust/src/ipc/session/state.rs | sed -n '89,116p'` + `cd rust && cargo test ipc::tests:: -- --nocapture` | confirms Step-3f capability emission is adapter/registry-derived via `Provider::ipc_supported()` + `ipc_capability_labels()` with IPC regressions passing (`82` tests) | done |
| `nl -ba rust/src/ipc/protocol.rs | sed -n '205,360p'` + `nl -ba rust/src/ipc/router.rs | sed -n '20,220p'` + `nl -ba rust/src/ipc/tests.rs | sed -n '108,520p'` | confirms Step-3e runtime classification: `aider`/`opencode`/`custom` are explicit overlay-only non-IPC labels with dedicated diagnostics and regression coverage | done |
| `python3 dev/scripts/checks/check_compat_matrix.py --format md` + `python3 dev/scripts/checks/compat_matrix_smoke.py --format md` | confirms Step-3e matrix policy: explicit non-IPC provider modes required for `aider`/`opencode`/`custom`, with matrix coverage now `24/24` declared cells | done |
| `nl -ba dev/config/compat/ide_provider_matrix.yaml | sed -n '20,260p'` + `nl -ba guides/CLI_FLAGS.md | sed -n '108,320p'` + `nl -ba guides/USAGE.md | sed -n '56,90p'` + `nl -ba dev/ARCHITECTURE.md | sed -n '45,70p'` | confirms Step-3e docs/matrix parity: IPC surface remains `codex`/`claude`; `gemini` is overlay-only experimental; `aider`/`opencode`/`custom` are explicit overlay-only non-IPC | done |
| `cat dev/reports/mp346/checkpoints/20260304T174948Z-cp014/summary.md` + `cat dev/reports/mp346/checkpoints/20260304T174948Z-cp014/exit_codes.env` | captures Step-3a checkpoint packet with `go (phase 3b next)` and retained manual-matrix baseline from `CP-006` | done |
| `cat dev/reports/mp346/checkpoints/20260304T181236Z-cp015/summary.md` + `cat dev/reports/mp346/checkpoints/20260304T181236Z-cp015/exit_codes.env` | captures Step-3d checkpoint packet with explicit non-IPC Gemini guardrails and codex/claude-only IPC policy confirmation | done |
| `nl -ba rust/src/ipc/protocol.rs | sed -n '195,268p'` + `nl -ba rust/src/ipc/router.rs | sed -n '104,140p'` + `nl -ba rust/src/ipc/router.rs | sed -n '337,389p'` + `nl -ba rust/src/ipc/session/state.rs | sed -n '33,43p'` | confirms Step-3d non-IPC Gemini guardrails: shared provider-resolution diagnostics, explicit override/auth rejection, and no silent `VOICETERM_PROVIDER` fallback for unsupported provider values | done |
| `cd rust && cargo test ipc::tests:: -- --nocapture` | validates IPC provider parsing/routing/auth regression suite after explicit non-IPC Gemini guardrails | done |
| `nl -ba guides/CLI_FLAGS.md | sed -n '250,306p'` + `nl -ba dev/ARCHITECTURE.md | sed -n '847,864p'` + `nl -ba dev/CHANGELOG.md | sed -n '8,24p'` | confirms docs/changelog explicitly describe IPC provider support as `codex|claude` with Gemini overlay-only experimental outside IPC | done |
| `nl -ba rust/src/ipc/router.rs | sed -n '76,156p'` + `nl -ba rust/src/ipc/tests.rs | sed -n '518,592p'` | confirms wrapper commands now bypass provider override parsing and adds `/exit`-during-auth invalid-override regressions | done |
| `cd rust && cargo test ipc::tests:: -- --nocapture` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md` + `python3 dev/scripts/checks/check_code_shape.py --format md` | validates post-Step-3d wrapper-override regression fix and guardrail parity | done |
| `python3 dev/scripts/devctl.py swarm_run --plan-doc dev/active/ide_provider_modularization.md --mp-scope MP-346 --run-label mp346-swarmrun-20260304t1` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/mp346-swarmrun-20260304t1/summary.md` (2026-03-04 local run) | done |
| `nl -ba .github/workflows/rust_ci.yml | sed -n '32,80p'` + `nl -ba .github/workflows/release_preflight.yml | sed -n '114,126p'` | confirms runtime CI now executes `devctl` AI-guard in the standard lane and release preflight AI-guard step is explicitly non-duplicative (`--skip-tests`) | done |
| `nl -ba dev/scripts/checks/check_ide_provider_isolation.py | sed -n '13,240p'` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md` | confirms isolation scanner now covers both `rust/src/bin/voiceterm` and `rust/src/ipc`, with local-binding split-signal tracking active in blocking mode | done |
| `nl -ba dev/scripts/checks/code_shape_policy.py | sed -n '90,101p'` + `python3 dev/scripts/checks/check_code_shape.py --format md` | confirms prompt hotspot budgets now enforce MP-346 DoD hard ceilings (`700/600`) with hard-lock growth policy retained | done |
| `python3 dev/scripts/devctl.py swarm_run --plan-doc dev/active/ide_provider_modularization.md --mp-scope MP-346 --run-label 20260304-mp346-multiagent-live` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/20260304-mp346-multiagent-live/summary.md` (2026-03-04 local run) | done |
| `nl -ba rust/src/bin/voiceterm/prompt/mod.rs | sed -n '1,120p'` + `nl -ba rust/src/bin/voiceterm/event_state.rs | sed -n '12,50p'` | confirms `PromptOcclusionDetector` is now a concrete wrapper type used by event-loop runtime state (no alias-level coupling in runtime callsites) | done |
| `nl -ba rust/src/bin/voiceterm/prompt/claude_prompt_detect.rs | sed -n '520,640p'` + `cd rust && cargo test --bin voiceterm event_loop::prompt_occlusion::tests::numbered_approval_hint_detects_compact_prefix_variant -- --nocapture` + `cd rust && cargo test --bin voiceterm prompt::claude_prompt_detect::tests::shared_approval_parser_accepts_compact_dot_numbering -- --nocapture` | confirms shared numbered-card parser now detects compact dot-numbered approval cards (`1.Yes`/`2.No`) and fixes prompt-occlusion regression coverage | done |
| `cd rust && cargo test --bin voiceterm provider_adapter::tests:: -- --nocapture` + `cd rust && cargo clippy --bin voiceterm -- -D warnings` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md` | confirms provider-adapter detector-wrapper integration compiles cleanly and isolation gate remains green after decoupling follow-up | done |
| `nl -ba rust/src/ipc/provider_lifecycle.rs` + `nl -ba rust/src/ipc/router.rs | sed -n '1,280p'` + `nl -ba rust/src/ipc/session/loop_runtime.rs | sed -n '1,120p'` | confirms Step-3c lifecycle adapterization: router/session runtime now delegate provider start/cancel/drain through dedicated adapter ownership (`ipc/provider_lifecycle.rs`) | done |
| `nl -ba rust/src/ipc/protocol.rs | sed -n '286,338p'` + `nl -ba rust/src/ipc/session/auth_flow.rs | sed -n '1,80p'` + `nl -ba rust/src/ipc/session/event_processing/auth.rs | sed -n '1,90p'` | confirms auth lifecycle routes through provider helper policy (`auth_command`, `resets_session_on_auth_success`) instead of hard-coded provider branches | done |
| `cd rust && cargo test ipc::tests:: -- --nocapture` + `cd rust && cargo test --bin voiceterm event_loop::prompt_occlusion::tests:: -- --nocapture` + `cd rust && cargo test --bin voiceterm prompt::claude_prompt_detect::tests:: -- --nocapture` | validates Step-3c lifecycle refactor and prompt-side non-regression tests remain green (`84`, `34`, and `40` tests passed) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_check_ide_provider_isolation` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md` + `python3 dev/scripts/devctl.py check --profile ai-guard --skip-fmt --skip-clippy --skip-tests` | confirms isolation guardrail upgrade is enforced in blocking mode with unit coverage and AI-guard profile integration; temporary file-scope allowlist debt is explicit (`files_with_file_signal_coupling=5`, `unauthorized_files=0`) | done |
| `python3 dev/scripts/checks/check_code_shape.py --absolute --format md` + `wc -l rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs rust/src/bin/voiceterm/prompt/claude_prompt_detect.rs` | confirms Step-3b hotspot closure: absolute shape gate is green and prompt hotspots are under hard limits (`prompt_occlusion.rs=679`, `claude_prompt_detect.rs=541`) | done |
| `cd rust && cargo test --bin voiceterm event_loop::prompt_occlusion::tests:: -- --nocapture` + `cd rust && cargo test --bin voiceterm prompt::claude_prompt_detect::tests:: -- --nocapture` | validates prompt-occlusion orchestration and detector parser regressions remain green after Step-3b decomposition (`34` + `40` tests passed) | done |
| `cd rust && cargo test ipc::tests:: -- --nocapture` | validates IPC regression suite remains green after Step-3b prompt decomposition (`84` tests passed) | done |
| `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md` | confirms isolation blocking gate remains green after Step-3b decomposition (`unauthorized_files=0`) | done |
| `nl -ba dev/scripts/checks/check_ide_provider_isolation.py | sed -n '53,72p'` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --format md` + `python3 -m unittest dev.scripts.devctl.tests.test_check_ide_provider_isolation` | confirms temporary Step-3b allowlist entry for `event_loop/prompt_occlusion.rs` is removed and isolation checker coverage remains green (`14` tests) | done |
| `cat dev/reports/mp346/checkpoints/20260305T032253Z-cp016/summary.md` + `cat dev/reports/mp346/checkpoints/20260305T032253Z-cp016/exit_codes.env` | captures CP-016 continuation packet refresh: automated runtime/governance bundle rerun is green, with temporary waiver approval while manual matrix remains due by expiry | done |
| `cat dev/reports/mp346/checkpoints/20260305T032253Z-cp016/manual_matrix_notes.md` + `cat dev/reports/mp346/checkpoints/20260305T032253Z-cp016/waiver_template.md` | captures CP-016 manual closure scaffolding: original `7/7` worksheet + waiver template artifacts (historical), superseded by IDE-first `4/4` release-scope closure update | done |
| `printf 'TERM_PROGRAM=%s\nTERM=%s\n' "${TERM_PROGRAM:-<unset>}" "${TERM:-<unset>}"` + attempted optional IPC sanity command (`printf '{"cmd":"get_capabilities"}\n'` piped to `voiceterm --json-ipc`) | confirms CP-016 session runs under VS Code terminal and sandbox blocks local JSON IPC runtime startup (`Operation not permitted (os error 1)`), so required physical-host matrix cells cannot be executed here | done |
| `cat dev/reports/mp346/checkpoints/20260305T032253Z-cp016/waiver_template.md` + `cat dev/reports/mp346/checkpoints/20260305T032253Z-cp016/summary.md` | confirms waiver packet records explicit `approve waiver` decision and CP-016 summary now records temporary waiver approval with expiry-bound exit criteria | done |
| `git check-ignore -v rust/.voiceterm/memory/events.jsonl rust/.voiceterm/memory/events.1.jsonl` + `git status --short rust/.voiceterm/memory/events.jsonl rust/.voiceterm/memory/events.1.jsonl` | confirms runtime artifacts are ignored via `**/.voiceterm/memory/` and removed from tracked changeset | done |
| `cd rust && cargo fmt --all -- --check` + `cd rust && cargo test ipc::tests:: -- --nocapture` + `python3 dev/scripts/devctl.py check --profile ci` + `python3 dev/scripts/devctl.py docs-check --user-facing` + `python3 dev/scripts/devctl.py hygiene` + `python3 dev/scripts/checks/check_active_plan_sync.py` + `python3 dev/scripts/checks/check_multi_agent_sync.py` + `python3 dev/scripts/checks/check_cli_flags_parity.py` + `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120` + `python3 dev/scripts/checks/check_code_shape.py` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations` + `python3 dev/scripts/checks/check_compat_matrix.py` + `python3 dev/scripts/checks/compat_matrix_smoke.py` + `python3 dev/scripts/checks/check_rust_lint_debt.py` + `python3 dev/scripts/checks/check_rust_best_practices.py` + `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md` | confirms CP-016 automated continuation bundle remains green after findings cleanup slice; only documented non-blocking warnings remain (`hygiene` report-footprint/process-sweep warnings, expected non-IPC runtime labels in matrix smoke) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_check_ide_provider_isolation dev.scripts.devctl.tests.test_check_compat_matrix dev.scripts.devctl.tests.test_compat_matrix_smoke` | validates post-waiver tooling hardening coverage for cfg-test isolation handling plus dedicated matrix check-script unit tests (`19` passed) | done |
| `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations --format md` + `python3 dev/scripts/checks/check_compat_matrix.py --format md` + `python3 dev/scripts/checks/compat_matrix_smoke.py --format md` | confirms hardening slice guardrails remain green: blocking isolation check passes, matrix policy check passes, and smoke runtime backend ownership now maps to `BackendRegistry` entries (non-IPC warnings remain expected) | done |
| `cd rust && cargo test ipc::tests:: -- --nocapture` | confirms IPC cancellation parity cleanup remains green with new regression coverage for wrapper-command and prompt-preemption cancellation event emission (`87` passed) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_check_ide_provider_isolation dev.scripts.devctl.tests.test_check_compat_matrix dev.scripts.devctl.tests.test_compat_matrix_smoke` | confirms matrix/isolation tooling cleanup regressions remain green after duplicate-id detection and runtime-set enforcement updates (`24` passed) | done |
| `python3 dev/scripts/checks/check_compat_matrix.py --format md` + `python3 dev/scripts/checks/compat_matrix_smoke.py --format md` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations --format md` | confirms post-review guardrails remain green: duplicate-id policy active, runtime-set matrix smoke coverage active, and blocking isolation gate unchanged (`ok: True`) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_check_ide_provider_isolation dev.scripts.devctl.tests.test_check_compat_matrix dev.scripts.devctl.tests.test_compat_matrix_smoke` | confirms reviewer follow-up script hardening coverage is green after cfg-not(test) precision + schema strictness + backend parser resilience updates (`27` passed) | done |
| `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations --format md` + `python3 dev/scripts/checks/check_compat_matrix.py --format md` + `python3 dev/scripts/checks/compat_matrix_smoke.py --format md` | confirms CP-016 guardrails remain green after reviewer follow-up hardening (`ok: True` across blocking isolation + matrix validation + runtime smoke coverage) | done |
| `cd rust && cargo test ipc::tests:: -- --nocapture` + `cd rust && cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture` | confirms IPC regression suite remains green with added Claude cancellation assertions (`89` passed) and targeted memory-guard lane is green (`1` passed) | done |
| `cd rust && cargo test legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture` + `cd rust && cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture` | confirms memory-guard assertion remains green in both default-feature and no-default-feature lane variants after baseline-wait stabilization update (`1` passed in each lane) | done |
| `python3 dev/scripts/devctl.py check --profile ci` | confirms MP-346 closure-gate bundle is green after reviewer follow-up + memory-guard stabilization (`exit:0`; non-blocking process-sweep `ps` sandbox warnings only) | done |
| `python3 dev/scripts/checks/check_code_shape.py` + `python3 dev/scripts/checks/check_duplication_audit.py` + `python3 dev/scripts/checks/check_structural_complexity.py` + `python3 dev/scripts/checks/check_duplicate_types.py` + `python3 dev/scripts/checks/check_naming_consistency.py` + `python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations` + `python3 dev/scripts/checks/check_rust_test_shape.py` + `python3 dev/scripts/checks/check_rust_lint_debt.py --absolute --report-dead-code` + `python3 dev/scripts/checks/check_rust_best_practices.py` + `python3 dev/scripts/checks/check_rust_runtime_panic_policy.py` + `python3 dev/scripts/checks/check_rust_security_footguns.py` + `python3 dev/scripts/rust_tools/collect_clippy_warnings.py --output-lints-json /tmp/clippy_lints.json --quiet-json-stream` + `python3 dev/scripts/checks/check_clippy_high_signal.py --input-lints-json /tmp/clippy_lints.json` + `python3 dev/scripts/devctl.py docs-check --strict-tooling` | architecture reconciliation rerun is now fully green after modularizing `check_router`/`docs_check_support` and generating fresh `jscpd` evidence (`duplication_percent=0.93`); historical `7/7` closure wording is superseded by IDE-first `4/4` release-scope gate | done |
| `python3 dev/scripts/devctl.py hygiene --strict-warnings` + `python3 dev/scripts/devctl.py hygiene --fix --strict-warnings` | catalog/docs registration for `check_duplication_audit_support.py` is complete, but strict hygiene still shows local repeatability noise: after `docs-check --strict-tooling`, regenerated `dev/scripts/checks/__pycache__` warnings fail strict mode unless `--fix` is applied (`--fix --strict-warnings` rerun is green) | open |
