# Naming + API Cohesion Plan

Status: execution mirrored in `dev/active/MASTER_PLAN.md` (`MP-267`)
Execution plan contract: required
Owner lane: Runtime/tooling cohesion

## Scope

Run a deliberate cohesion pass across runtime and tooling surfaces so naming,
public API intent, and helper ownership stay predictable for maintainers.

In scope:

1. Naming consistency across `theme`, `event_loop`, `status_line`, and memory
   paths referenced by `MP-267`.
2. Public API intent review (remove ambiguous names, tighten contracts).
3. Duplicate helper consolidation where behavior is identical.
4. Design conformance against official Rust references before non-trivial Rust
   edits (`Rust Book`, `Reference`, API Guidelines, `std`, Clippy index).

Out of scope:

1. Large feature work unrelated to cohesion.
2. Unbounded cosmetic churn without measurable maintainability gain.

## Execution Checklist

- [x] Create an execution-plan doc with explicit checklist/progress/evidence for
  `MP-267` traceability.
- [x] Promote `swarm_run` as the canonical guarded plan-scoped swarm command
  name in devctl parser/dispatch/docs (no legacy alias).
- [x] Build a naming inventory for `theme/event_loop/status_line/memory` and
  classify conflicts by severity (`ambiguous`, `legacy`, `inconsistent`).
- [x] Build duplicate-helper inventory and propose canonical owners.
- [x] Execute first prioritized rename/consolidation slices with non-regression
  tests.
- [x] Continue prioritized runtime (`theme/event_loop/status_line/memory`)
  rename/consolidation slices with non-regression tests.
- [ ] Record Rust-reference checks and rationale for each non-trivial Rust
  change in progress/evidence.
- [ ] Close with docs/governance bundle and final `MP-267` status update.

## Initial Inventory (2026-02-25)

### Naming conflicts

| Severity | Surface | Finding | Status/owner |
|---|---|---|---|
| high | `devctl` command surfaces + workflow dispatch | Canonical command renamed to `swarm_run`, but workflow/docs still called retired `autonomy-run` token in active operator paths. | fixed in workflow + active docs (`MP-267`) |
| medium | active-plan autonomy spec evidence | Historical run/evidence rows contain pre-rename command literals (`autonomy-run`). | retained as historical evidence; explicit rename note added |
| low | module path naming | command is `swarm_run` but implementation modules remain `autonomy_run_*`. | accepted for now; treat as internal module legacy naming |

### Duplicate-helper inventory

| Severity | Surface | Duplicate pattern | Canonical owner decision |
|---|---|---|---|
| high | `dev/scripts/devctl/triage_loop_policy.py`, `mutation_loop_policy.py` | Nearly identical policy parsing/allowlist logic duplicated line-for-line. | fixed: shared engine in `dev/scripts/devctl/loop_fix_policy.py` with thin wrappers |
| medium | `rust/src/bin/voiceterm/theme_studio/*` | Repeated page-navigation helpers (`move_up`, `move_down`, `render`, label/index cycling) across page modules. | fixed: shared `theme_studio/nav.rs` + consistent `select_prev`/`select_next` state APIs |
| medium | `dev/scripts/devctl/*` render/metrics helpers | Repeated numeric helper variants (`safe_int`, `_safe_int`, `safe_float`, `_safe_float`) across autonomy/report/data-science helpers. | fixed: shared `dev/scripts/devctl/numeric.py` (`to_int`/`to_float`/`to_optional_float`) |

## Progress Log

- 2026-02-25: Opened `MP-267` execution-plan track for naming/API cohesion to
  convert ad-hoc cleanup into governed checklist-driven work.
- 2026-02-25: Renamed guarded devctl command to canonical `swarm_run` and
  removed `autonomy-run` alias path from parser/dispatch; updated primary docs
  and parser tests.
- 2026-02-25: Added closed-loop swarm sizing controller for continuous runs
  (`--feedback-*` controls), with dedicated helper module and tests, so agent
  count adaptation is deterministic and auditable.
- 2026-02-25: Updated guarded workflow/operator docs to execute canonical
  `swarm_run` command end-to-end (workflow command path, artifacts, and active
  command references).
- 2026-02-25: Consolidated duplicate triage/mutation fix-policy engines into
  shared `dev/scripts/devctl/loop_fix_policy.py` with loop-specific wrappers
  and added dedicated mutation policy tests.
- 2026-02-25: Captured first naming + duplication inventory for
  `theme/event_loop/status_line/memory` and `devctl` tooling helpers, with
  severity-based owner decisions for next slices.
- 2026-02-25: Consolidated duplicated devctl numeric parsing helpers into
  shared `dev/scripts/devctl/numeric.py`; replaced `safe_*` variants with
  canonical `to_int`/`to_float`/`to_optional_float` usage across autonomy,
  report, benchmark, and data-science modules.
- 2026-02-25: Extracted shared Theme Studio list navigation to
  `rust/src/bin/voiceterm/theme_studio/nav.rs` and standardized page state APIs
  + input dispatch on `select_prev`/`select_next` naming.
- 2026-02-27: Extracted prompt-occlusion transition handling from
  `event_loop.rs` into `event_loop/prompt_occlusion.rs` so PTY-output
  detection, timeout-based reconciliation, and input-driven resolve/clear paths
  share one runtime owner instead of duplicating suppression mutations across
  `output_dispatch`, `periodic_tasks`, and `input_dispatch`.

## Audit Evidence

| Check | Evidence | Status |
|---|---|---|
| `python3 -m unittest dev.scripts.devctl.tests.test_autonomy_run` | parser/command behavior tests pass with `swarm_run` command path | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_autonomy_run_feedback` | feedback sizing helper tests pass (downshift/upshift + config validation) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_triage_loop_policy dev.scripts.devctl.tests.test_mutation_loop_policy` | shared fix-policy engine + loop-specific wrappers covered by triage/mutation policy tests | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_autonomy_run_feedback dev.scripts.devctl.tests.test_autonomy_run dev.scripts.devctl.tests.test_autonomy_swarm dev.scripts.devctl.tests.test_autonomy_benchmark dev.scripts.devctl.tests.test_autonomy_report dev.scripts.devctl.tests.test_data_science` | `Ran 25 tests ... OK` after numeric-helper consolidation and import rewiring | done |
| `cd rust && cargo test --bin voiceterm theme_studio` | `68 passed; 0 failed` after shared Theme Studio navigation helper extraction and method rename pass | done |
| `python3 dev/scripts/devctl.py docs-check --strict-tooling` | docs/process governance checks passed (`ok: True`) after naming-cohesion updates | done |
| `python3 dev/scripts/devctl.py hygiene --fix` | hygiene passed (`ok: True`) and removed transient `__pycache__` dirs from local compile pass | done |
| `rg -n "autonomy-run" AGENTS.md dev/ARCHITECTURE.md dev/DEVELOPMENT.md .github/workflows/README.md .github/workflows/autonomy_run.yml dev/active/MASTER_PLAN.md` | active command-surface drift inventory captured; retained hits are historical evidence only where explicitly noted | done |
| `python3 dev/scripts/devctl.py swarm_run --help` | canonical command surfaces in CLI help and option set includes feedback controls | done |
| `cd rust && cargo check --bin voiceterm` | pass after extracting prompt-occlusion controller module and rewiring event-loop call paths | done |
| `cd rust && cargo test --bin voiceterm` | `1240 passed; 0 failed` after prompt-occlusion modularization pass | done |
| `cd rust && cargo fmt --check` | pass after formatting touchpoints in modularized event-loop files | done |
