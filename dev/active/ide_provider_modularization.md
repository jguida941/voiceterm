# IDE + Provider Modularization Plan (MP-346)

**Status**: execution mirrored in `dev/active/MASTER_PLAN.md` (`MP-346`)  |  **Last updated**: 2026-03-04 | **Owner:** Runtime/tooling architecture
Execution plan contract: required

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

No MP-346 phase can advance without a fresh checkpoint packet and explicit
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

Required smoke checks before phase advancement (7 combinations):

1. Cursor + Codex: startup, typing, scrolling, send path.
2. Cursor + Claude: startup, typing while output streams, prompt visibility.
3. JetBrains + Codex: HUD stability under output and resize.
4. JetBrains + Claude: approval/prompt visibility and non-corrupt redraw.
5. Other + Claude (iTerm2/Terminal.app): startup banner, status line render,
   output scroll without HUD corruption, clean exit.
6. Other + Codex (iTerm2/Terminal.app): same as above.
7. Gemini baseline path: command startup + non-crash capability reporting.

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
2. any manual verification cell fails or is untested.
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
| Runtime-lane AI-guard enforcement | Phase 0 | runtime workflow on `rust/src/**` executes AI guards in commit-range mode | pending |
| `devctl check` AI-guard ref propagation | Phase 0 | `check` command accepts `--since-ref/--head-ref` and forwards refs to `AI_GUARD_CHECKS` scripts | done |
| Dependency-policy CI gate (`cargo deny`) | Phase 0 | security/release lane enforces deny policy with explicit failure semantics | done |
| `check_code_shape.py` evaluator coverage | Phase 0 | dedicated unit tests for `_evaluate_shape` branch matrix | done |
| `check_agents_contract.py` dedicated coverage | Phase 0 | unit tests + contract-row migration to `rust/src/**` snippets | done |
| Clippy threshold tightening | Phase 0 | `clippy.toml`: `cognitive-complexity-threshold = 25`, `Cargo.toml`: `too_many_lines = "warn"` | pending |
| Parameterized characterization tests | Phase 0.5 | `rstest` crate + matrix tests for preclear/redraw/gap-rows | done |
| Duplicate enum/type detector | Phase 1 | `check_duplicate_types.py` (~80 lines) | pending |
| Structural complexity check | Phase 1 | `rust-code-analysis-cli` + `check_structural_complexity.py` (~80 lines) | pending |
| IDE/provider isolation check | Phase 0 (report), Phase 2 (block) | `check_ide_provider_isolation.py` (~100 lines) with staged rollout | done (report-only baseline) |
| Mixed host/provider conditional budget | Phase 0 | baseline artifact (`rg`-based) + non-regressive checkpoint tracking until isolation check blocks | done (`dev/reports/mp346/baselines/host_provider_mix_counts.txt`) |
| Compat matrix YAML + check | Phase 4 | `ide_provider_matrix.yaml` + `check_compat_matrix.py` | pending |
| devctl `compat-matrix` command | Phase 4 | `devctl/commands/compat_matrix.py` | pending |
| General duplication audit | Phase 4 | `jscpd` integration (periodic, not CI gate) | pending |
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

- [ ] Define one canonical `TerminalHost` detection owner in
  `runtime_compat.rs`.
- [ ] Replace duplicated detection implementations in:
  - `writer/render.rs` (delete `TerminalFamily` enum, replace with
    `TerminalHost`)
  - `banner.rs` (delete `is_jetbrains_terminal()`)
  - `color_mode.rs` lines 74-95 (route through canonical detection)
  - `theme/detect.rs` (`is_warp_terminal` should consume canonical host signal,
    not direct env probing)
  - `texture_profile.rs` (either unify `TerminalId` with `TerminalHost` or
    explicitly layer `TerminalId` on top of `TerminalHost` with a documented
    mapping)
- [ ] Replace all `TerminalFamily` references in `state.rs` (30+ locations)
  with `TerminalHost`.
- [ ] Define caching contract: canonical `detect_terminal_host()` returns a
  cached `OnceLock<TerminalHost>`. Tests use a thread-local override to inject
  test values without polluting the process-wide cache (follow existing
  `set_terminal_size_hook` pattern in `state.rs:97`).
- [ ] Route all call sites to canonical host detection APIs.
- [ ] Add regression tests for JetBrains/Cursor/Other environment fingerprints.

### Phase 1.5: Shared Utilities + Backend Detection Consolidation

Extract shared code before the big refactors to reduce diff noise and prevent
merge conflicts.

- [ ] Extract `parse_debug_env_flag`, `debug_bytes_preview`,
  `claude_hud_debug_enabled` into `writer/debug.rs` or a shared `debug`
  module. Delete the 3 copies in `state.rs`, `prompt_occlusion.rs`,
  `terminal.rs`.
- [ ] Replace `is_codex_backend()` / `is_claude_backend()` in `state.rs` (raw
  string-contains) with `runtime_compat::BackendFamily` enum usage.
- [ ] Consolidate the 5 ANSI-stripping implementations into one shared utility
  module.
- [ ] Define the `ProviderAdapter` trait signature (without full
  implementation) so Phase 2 can code against trait methods instead of
  backend-name strings.
- [ ] Create shared test utility module for env-var locking (replace the 14
  independent `OnceLock<Mutex<()>>` helpers with one canonical lock used by
  runtime tests and helper modules).
- [ ] Rename `claude_prompt_suppressed` to `prompt_suppressed` (or
  `prompt_occlusion_active`) across all 97+ references. This is a
  find-and-replace, not a behavioral change.

### Phase 2: Host Config + Policies

Highest-risk phase. Use atomic sub-steps with individual checkpoints.

- [ ] **Step 2a** (safe, data-only): Extract host timing constants from
  `writer/state.rs` into typed `HostTimingConfig` keyed by `TerminalHost`.
  No logic change -- pure data extraction. Checkpoint here.
- [ ] **Step 2b**: Extract `should_preclear_bottom_rows` into a
  `PreclearPolicy` that returns both the preclear decision AND the resulting
  flags (`pre_cleared`, `force_redraw_after_preclear`,
  `force_full_banner_redraw`). Checkpoint here.
- [ ] **Step 2c**: Extract the scroll/non-scroll redraw decision block (lines
  741-858) into `RedrawPolicy` that consumes preclear outputs. Checkpoint
  here.
- [ ] **Step 2d**: Extract `maybe_redraw_status` idle-gating into a separate
  timing module. Checkpoint here.
- [ ] **Step 2e**: Reduce `handle_message` to: dispatch message type -> call
  policy pipeline -> apply state updates. Build `RuntimeProfile` cross-product
  resolver and inject via DI at `WriterState` construction. Final checkpoint.
- [ ] **Step 2f**: Flip `check_ide_provider_isolation.py` from report-only to
  blocking mode for runtime files outside approved adapter/policy modules.
  Final checkpoint before Phase 3.
- [ ] After each sub-step: run checkpoint bundle + verify no regression in
  characterization tests from Phase 0.5.

Rollback strategy: If step 2c breaks, revert to the 2b checkpoint, not to
Phase 1. Each sub-step must be independently revertable via `git revert`.

Feature flag option: consider `VOICETERM_USE_ADAPTER_POLICIES=1` env var to
run old and new code paths in parallel during validation.

### Phase 3: Provider Adapter Expansion

- [ ] **Step 3a**: Introduce `PromptDetectionStrategy` trait and wire
  `claude_prompt_detect.rs` behind a Claude adapter-owned implementation while
  keeping a short-lived fallback shim for parity testing.
- [ ] **Step 3b**: Decompose `event_loop/prompt_occlusion.rs` into provider-
  neutral core + provider strategy hooks; remove direct Claude-specific pattern
  logic from the event-loop module.
- [ ] **Step 3c**: Expand provider abstraction so IPC/runtime lifecycle routes
  through provider adapters (not codex/claude match arms in router/auth/session
  code).
- [ ] **Step 3d**: Reconcile backend registry and IPC provider model:
  - add `Gemini` support to `ipc::Provider` and capability emission if shipped,
    or
  - explicitly mark `Gemini` as non-IPC experimental with guardrails and docs.
- [ ] **Step 3e**: Explicitly classify non-IPC backends (`aider`, `opencode`,
  `custom`) as overlay-only or promote them into the provider adapter surface;
  do not leave ambiguous partial support behavior.
- [ ] **Step 3f**: Replace codex/claude-only capability list in
  `ipc/session/state.rs::emit_capabilities` with adapter-derived values.
- [ ] After each sub-step: run checkpoint bundle + manual matrix verification
  and record `CP-3x` artifact.

### Phase 4: Matrix + Tooling Gates

- [ ] Add machine-readable matrix source:
  `dev/config/compat/ide_provider_matrix.yaml`.
- [ ] Add matrix validator check:
  `python3 dev/scripts/checks/check_compat_matrix.py`.
- [ ] Promote isolation check policy from Phase-2 blocking baseline to full CI
  governance (allowlist ownership + threshold owner + calibration evidence):
  `python3 dev/scripts/checks/check_ide_provider_isolation.py`.
- [ ] Add smoke harness:
  `python3 dev/scripts/checks/compat_matrix_smoke.py`.
- [ ] Add `devctl compat-matrix` command for validate/report workflows.

### Phase 5: AntiGravity Decision Gate

- [ ] Decide one of:
  - define concrete AntiGravity host fingerprints + detection + tests and keep
    it in MP-346 active scope, or
  - move AntiGravity to deferred MP scope until runtime host evidence exists.
- [ ] Update `MASTER_PLAN`, `INDEX`, and compatibility matrix scope accordingly.

### Phase 6: Governance + ADR Lock

- [ ] Add ADR for host/provider boundary ownership and extension policy.
- [ ] Add ADR for compatibility matrix governance and CI fail policy.
- [ ] Close MP-346 only after all matrix gates and non-regression checks pass.

## Operator Checkpoint Log

| Checkpoint | Phase | Artifact path | Bundle status | Manual matrix status | Operator decision | Notes |
|---|---|---|---|---|---|---|
| `CP-000` | baseline | `dev/reports/mp346/checkpoints/20260302T032908Z-cp000/` | fail (`check_ci`, `rust_lint_debt_since_ref`) | pending (all 7 cells) | `no-go` | automated packet captured; manual matrix gate still required before phase advancement. |
| `CP-003` | phase-0 rerun | `dev/reports/mp346/checkpoints/20260302T042017Z-cp003/` | pass (all automated bundle commands) | pending (all 7 cells) | `no-go` | CP-000 blockers revalidated and cleared on branch-aware commit-range baseline (`origin/master`); legacy `origin/develop` lint-debt check still reports historical release-range debt. |
| `CP-004` | phase-0 phase-gate | `dev/reports/mp346/checkpoints/20260302T155409Z-cp004/` | pass (all automated bundle commands) | pending (all 7 cells) | `go (phase 0.5 only)` | explicit operator approval to start characterization tests; phase-1+ extraction/refactor remains blocked until manual matrix completion. |
| `CP-005` | phase-0.5 closure | `dev/reports/mp346/checkpoints/20260302T162839Z-cp005/` | pass (all automated bundle commands) | pending (all 7 cells) | `go (manual matrix execution)` | Phase-0.5 checklist closure verified; Phase-1+ extraction/refactor remains blocked until manual matrix completion. |
| `CP-006` | manual matrix attestation | `dev/reports/mp346/checkpoints/20260304T010010Z-cp006/` | not rerun (latest full bundle pass: `CP-005`) | baseline accepted (`5/7` validated; `Other + Claude` and `Other + Codex` intentionally sequenced post-cleanup) | `go (phase 1+ cleanup now)` | operator attestation recorded for `Cursor + Codex`, `Cursor + Claude`, `JetBrains + Codex`, `JetBrains + Claude`, and Gemini baseline; remaining `Other` host cells are a post-cleanup stabilization checkpoint, not a phase-1+ blocker. |

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

21. Test coverage exists for all 7 supported IDE/provider combinations (at
    minimum parameterized matrix tests for preclear, redraw, timing, and
    capability behavior per cell).
22. No function in the codebase exceeds the function-length budget (100 lines)
    without an explicit `PATH_POLICY_OVERRIDES` exception with a follow-up MP.
23. Maximum cyclomatic complexity per function is under 20 without exception.

## Progress Log

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
    governance in `MULTI_AGENT_WORKTREE_RUNBOOK.md` Section 7/18 and mirrored
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
- 2026-03-04: MP-346 runtime checkpoint rerun for this cleanup slice:
  - `bundle.runtime` command set executed and green (including
    `devctl check --profile ci`, docs/hygiene/sync guards, parity checks,
    markdownlint, and root guard scan),
  - HUD/runtime risk add-on executed and green:
    `cd rust && cargo test --bin voiceterm`,
  - docs governance gate required user-facing evidence for runtime edits, so
    this slice now records an `Unreleased` changelog entry plus README
    compatibility clarification while keeping runtime behavior unchanged.

## Audit Evidence

| Check | Evidence | Status |
|---|---|---|
| `wc -l rust/src/bin/voiceterm/writer/state.rs` | reports `2750` lines | done |
| `nl -ba rust/src/bin/voiceterm/writer/state.rs | sed -n '600,1505p'` | `handle_message` spans `605..1486` and next top-level helper starts at `1493` | done |
| `sed -n '1,220p' rust/src/bin/voiceterm/runtime_compat.rs` | canonical host detection exists there today | done |
| `sed -n '1,220p' rust/src/bin/voiceterm/writer/render.rs` and `sed -n '160,280p' rust/src/bin/voiceterm/banner.rs` | duplicate host-detection logic confirmed | done |
| `sed -n '180,280p' rust/src/ipc/protocol.rs` and `sed -n '1,260p' rust/src/ipc/session/state.rs` | provider enum/capabilities limited to codex+claude | done |
| `sed -n '1,220p' rust/src/backend/mod.rs` | backend registry includes Gemini backend | done |
| `rg -n "antigravity|anti-gravity|anti gravity" .` | no runtime/source references outside docs/plans | done |
| `rg -n "parse_debug_env_flag|debug_bytes_preview" rust/src/bin/voiceterm/writer/state.rs rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs` | helper duplication confirmed | done |
| `cat dev/scripts/checks/check_code_shape.py` lines 60-115 | `writer/state.rs` absent from `PATH_POLICY_OVERRIDES`; 6 other files frozen | done |
| `cat dev/scripts/checks/check_code_shape.py` lines 243-322 | diff-only evaluation; no absolute violation mode; no function-level analysis | done |
| `cat dev/scripts/checks/check_rust_best_practices.py` | 4 regex metrics only; no complexity, duplication, or coupling checks | done |
| `cat dev/scripts/devctl/commands/check_profile.py` lines 31-82 | `ci` profile sets `with_ai_guard=False`; only runs fmt+clippy+test | done |
| `python3 dev/scripts/devctl.py check --profile ci --dry-run` | confirms ci profile executes only fmt/clippy/test (no AI-guard steps) | done |
| `python3 dev/scripts/devctl.py check --profile release --dry-run` | confirms AI-guard steps exist but are release-profile scoped unless explicitly invoked | done |
| `cat dev/scripts/devctl/cli_parser_builders_checks.py` + `cat dev/scripts/devctl/commands/check.py` | `devctl check` has no `--since-ref/--head-ref`, and AI-guard calls do not pass commit-range refs | done |
| `rg -c "#\[test\]" rust/src/bin/voiceterm/writer/state.rs` + manual review | ~25 IDE/provider combo tests; no parameterized matrix coverage | done |
| `cat dev/scripts/tests/claude_hud_stress.py` | hardcoded `TERM_PROGRAM=cursor`; no multi-host parameterization | done |
| `rg -rn "TerminalFamily|TerminalHost|BackendFamily" rust/src/bin/voiceterm/` | IDE/provider types referenced in 12+ files with no boundary enforcement | done |
| `rg -n "src/\*\*" .github/workflows/*.yml AGENTS.md` | runtime lanes + AGENTS routing still reference legacy `src/**` contracts | done |
| `python3 dev/scripts/devctl.py path-audit --format md` | returned `ok: True` despite stale runtime workspace contracts; confirms audit blind spot | done |
| `cat dev/scripts/checks/check_agents_contract.py` (`REQUIRED_ROUTER_SNIPPETS`) | guard script currently requires exact `src/**` router row text | done |
| `nl -ba .github/dependabot.yml` + `nl -ba .github/CODEOWNERS` | Dependabot still points Cargo updates to `/src`; CODEOWNERS still maps `/src/` | done |
| `nl -ba dev/scripts/checks/check_active_plan_sync.py` (`REQUIRED_REGISTRY_ROWS`) | active-plan sync hard-requires 6 docs only; missing several active scopes | done |
| `nl -ba .github/workflows/failure_triage.yml` + workflow `name:` scan | failure triage omits `Swarm Run` and `publish_release_binaries` from watched workflow list | done |
| `rg -n "name = \"bytes\"|version = \"1.11.0\"" rust/Cargo.lock` + `cat rustsec-audit.json` | lockfile still has `bytes 1.11.0`; RustSec artifact includes `RUSTSEC-2026-0007` | done |
| `nl -ba .github/workflows/rust_ci.yml` + `nl -ba rust/Cargo.toml` | runtime lane uses Ubuntu only + `--all-features`; manifest declares `rust-version = "1.70"` with no dedicated MSRV job | done |
| `rg -n "cargo doc" .github/workflows/*.yml` | no CI workflow currently runs `cargo doc` gate | done |
| `nl -ba README.md`, `nl -ba dev/ARCHITECTURE.md`, `nl -ba guides/CLI_FLAGS.md` | Gemini support wording is inconsistent across user/developer docs | done |
| `nl -ba dev/active/MASTER_PLAN.md` (agent board) + `nl -ba dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md` (ledger) | board/ledger status drift: board is all `planned` while ledger includes `ready-for-review` entries | done |
| `rg -n "MP-14[6-9]" dev/BACKLOG.md dev/active/MASTER_PLAN.md` | local backlog reuses MP IDs that already map to different work in MASTER_PLAN | done |
| `rg -n "OnceLock<Mutex<\\(\\)>>" rust/src/bin/voiceterm | wc -l` | reports `14` independent env-lock helpers (broader than prior 6-file estimate) | done |
| `find rust/src/bin/voiceterm -name '*.rs' -print0 | xargs -0 wc -l | sort -nr | head -n 25` | confirms top hotspots include `event_loop/tests.rs` (`5918`), `prompt_occlusion.rs` (`1143`), `claude_prompt_detect.rs` (`930`) | done |
| `rg -n "(JetBrains|Cursor|TerminalHost|TerminalFamily).*(codex|claude|BackendFamily|Provider::)|((codex|claude|BackendFamily|Provider::).*(JetBrains|Cursor|TerminalHost|TerminalFamily))" rust/src/bin/voiceterm` | mixed host/provider conditionals still present in `writer/state.rs` and `event_loop.rs`; coupling budget gate required | done |
| `python3 dev/scripts/checks/check_rust_audit_patterns.py --format json` | script reports `ok: true` with all 5 pattern totals at `0`; no violation signal emitted | done |
| `nl -ba dev/scripts/checks/check_rust_audit_patterns.py` | source-root candidates still include legacy `src/src` and `src` fallbacks | done |
| `nl -ba dev/scripts/checks/check_release_version_parity.py` | plist read path currently opens file directly without `.exists()` guard | done |
| `nl -ba dev/scripts/checks/check_active_plan_sync.py` | `SPEC_RANGE_PATHS` omits active spec docs (`rust_workspace_layout_migration`, `naming_api_cohesion`, `ide_provider_modularization`) | done |
| `wc -l rust/src/bin/voiceterm/event_loop/input_dispatch.rs` + `nl -ba dev/scripts/checks/check_code_shape.py` | stale override candidate: file is 555 lines while override soft/hard limits are 1200/1561 | done |
| `nl -ba rust/src/bin/voiceterm/event_loop/input_dispatch.rs` + `nl -ba rust/src/bin/voiceterm/event_loop/tests.rs | sed -n '4647,4731p'` | confirms current arrow-routing split (`insert_pending_send` gates caret preservation) and existing tests encode mutually-exclusive HUD-focus vs caret behavior | done |
| `nl -ba dev/scripts/checks/check_code_shape.py` | hotspot freeze overrides now include `writer/state.rs`, `prompt_occlusion.rs`, and `claude_prompt_detect.rs`; plus new `--absolute` mode | done |
| `python3 dev/scripts/checks/check_code_shape.py --absolute --format md` | absolute mode executes and reports repository-wide hard-limit results | done |
| `nl -ba dev/scripts/devctl/commands/check_profile.py` + `python3 dev/scripts/devctl.py check --profile ci --dry-run` | `ci` profile now enables AI-guard steps | done |
| `nl -ba dev/scripts/devctl/cli_parser_quality.py` + `nl -ba dev/scripts/devctl/commands/check.py` + `nl -ba dev/scripts/devctl/commands/check_support.py` | `devctl check` now accepts `--since-ref/--head-ref` and forwards commit-range args to supported AI-guard scripts | done |
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
| `nl -ba dev/active/MASTER_PLAN.md` + `nl -ba dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md` + `nl -ba dev/BACKLOG.md` | confirms board/ledger status sync, cross-plan shared-hotspot ownership/freeze gate activation, and local backlog ID deconfliction (`LB-*`) | done |
| `cat dev/reports/mp346/checkpoints/20260302T155409Z-cp004/summary.md` + `exit_codes.env` | confirms CP-004 full checkpoint bundle pass with explicit `go (phase 0.5 only)` and retained phase-1+ `no-go` | done |
| `cat dev/reports/mp346/checkpoints/20260302T162839Z-cp005/summary.md` + `exit_codes.env` | confirms CP-005 Phase-0.5 closure bundle pass with explicit `go (manual matrix execution)` and retained phase-1+ `no-go` pending manual matrix evidence | done |
| `cat dev/reports/mp346/checkpoints/20260304T010010Z-cp006/summary.md` | confirms CP-006 operator manual-matrix attestation (`5/7` cells pass) plus explicit phase-1+ `go`; remaining `Other` host cells are sequenced to post-cleanup stabilization validation | done |
| `nl -ba rust/src/bin/voiceterm/writer/state/tests.rs` + matrix test names (`*_matrix_*`) | verifies 9-way host/provider matrix characterization coverage for preclear, scroll redraw interval, and force-redraw trigger timing | done |
| `nl -ba rust/src/bin/voiceterm/event_loop/input_dispatch.rs` + input ownership test names (`insert_pending_preserves_caret_*`, `hud_navigation_direction_from_arrow_*`) | verifies deterministic caret-vs-HUD arrow ownership contract coverage for Codex/Claude across Cursor/JetBrains/Other labels | done |
| `cd rust && cargo test --bin voiceterm` | validates runtime suite with new `rstest` dependency and Phase-0.5 characterization tests (`1387` passed) | done |
| `rg -n "should_force_single_line_full_hud_for_env" rust/src/bin/voiceterm/status_line/layout.rs rust/src/bin/voiceterm/status_line/buttons.rs rust/src/bin/voiceterm/runtime_compat.rs` | confirms status-line host/provider full-HUD fallback routing now consumes canonical runtime-compat helper instead of inline host+provider conditionals | done |
| `nl -ba rust/src/bin/voiceterm/writer/render.rs` | confirms writer render host-family detection now maps from `runtime_compat::detect_terminal_host()` and no longer carries duplicate host-sniffing helpers | done |
| `cd rust && cargo test --bin voiceterm single_line_full_hud_policy_only_for_claude_on_jetbrains && cargo test --bin voiceterm full_single_line_fallback && cargo test --bin voiceterm terminal_family_maps_from_runtime_terminal_host` | validates canonical single-line fallback policy helper, status-line full-HUD fallback behavior, and writer render host-mapping coverage | done |
| `python3 dev/scripts/devctl.py check --profile ci` | validates runtime guard/check/test profile for this slice (`fmt`, `clippy`, ai-guard scripts, and test lanes); sandbox-only warning observed for process sweep `ps` probing | done |
| `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_multi_agent_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'` | validates remaining `bundle.runtime` documentation/governance/shape/parity/lint gates for this slice | done |
