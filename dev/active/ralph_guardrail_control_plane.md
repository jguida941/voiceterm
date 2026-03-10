# Ralph Guardrail Control Plane

**Status**: active - Phase 1 scaffolding  |  **Last updated**: 2026-03-09 | **Owner:** Control-plane/guardrails
Execution plan contract: required
This spec is execution mirrored in `dev/active/MASTER_PLAN.md` under `MP-360..MP-367`.

## Scope

Close the gap between "guards detect issues" and "AI fixes them automatically
under human control." Today the Ralph loop has infrastructure (backlog parsing,
retry, escalation) but no AI brain, no cross-architecture enforcement, and no
operator visibility into what the loop is doing. This plan delivers:

1. **AI-driven remediation** — `ralph_ai_fix.py` reads CodeRabbit findings,
   invokes Claude Code with false-positive filtering, runs architecture-specific
   validation, commits and pushes. The loop becomes genuinely autonomous.
2. **Cross-architecture guard alignment** — every guard runs consistently across
   Rust, PyQt6 operator console, Python devctl, and iOS. No architecture gets a
   pass. Documented as a mandatory policy in `AGENTS.md`.
3. **Structured guardrail report** — `ralph-report.json` with per-finding
   status (fixed / false-positive / pending), standards references, fix skills
   used, and aggregate analytics (fix rate, by-architecture, by-severity).
4. **Guardrail configuration registry** — `dev/config/ralph_guardrails.json`
   mapping finding categories to AGENTS.md standards, documentation links, and
   AI fix skills so the brain knows what rules apply and how to fix each class.
5. **devctl ralph-status command** — CLI analytics surface with SVG charts
   (fix rate over time, findings by architecture, false-positive rate) that
   feeds the data-science snapshot and phone status projections.
6. **Operator console Ralph dashboard** — PyQt6 widget showing live loop
   status, finding breakdown, fix progress, control buttons (start/pause/resume
   loop, adjust max attempts, switch approval mode), and guard health charts.
7. **Phone/iOS status integration** — Ralph loop metrics in phone compact/full
   views so operators can monitor and send control actions from mobile.
8. **Unified control surface** — same start/pause/configure/monitor controls
   available from devctl CLI, operator console, and phone app. All three
   surfaces read/write the same control state.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        GitHub Actions                            │
│  CodeRabbit ─► Triage Bridge ─► Ralph AI Loop                    │
│                                    │                             │
│               ralph_guardrails.json (standards / skills / config)│
│                                    │                             │
│               ralph_ai_fix.py ─► Claude Code ─► validate ─► push │
│                                    │                             │
│               ralph-report.json (structured findings + analytics)│
└────────────────────────┬─────────────────────────────────────────┘
                         │  artifacts
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   ┌───────────┐  ┌────────────┐  ┌────────────┐
   │ devctl CLI │  │ Operator   │  │ Phone/iOS  │
   │            │  │ Console    │  │            │
   │ ralph-    │  │ Ralph      │  │ Ralph      │
   │ status    │  │ dashboard  │  │ compact    │
   │ + charts  │  │ + controls │  │ + actions  │
   └───────────┘  └────────────┘  └────────────┘
         │               │               │
         └───────────────┼───────────────┘
                         ▼
              ralph-control-state.json
              (shared start/pause/config)
```

## Execution Checklist

### Phase 1: AI fix wrapper and policy wiring (MP-360)

- [x] Create `dev/scripts/ralph_ai_fix.py` — AI fix wrapper that reads backlog,
      invokes Claude Code, validates per-architecture, commits and pushes
- [x] Add `ralph_ai_fix.py` to `control_plane_policy.json` triage_loop allowlist
- [x] Set `ralph_ai_fix.py` as default fix command in `coderabbit_ralph_loop.yml`
- [x] Add approval-mode support (`strict|balanced|trusted`) via `RALPH_APPROVAL_MODE`
- [x] Add cross-architecture quality enforcement section to `AGENTS.md`
- [x] Wire 7 new guard scripts into `tooling_control_plane.yml`
- [x] Document `ralph_ai_fix.py` in `dev/scripts/README.md`
- [ ] Add unit tests for `ralph_ai_fix.py` (load_backlog, build_prompt,
      detect_architectures, has_changes)

### Phase 2: Guardrail configuration registry (MP-361)

- [ ] Create `dev/config/ralph_guardrails.json` — standards registry mapping
      finding categories to AGENTS.md sections, doc links, and fix skills
- [ ] Define fix skills enum: `code-shape-fix`, `dedup-extract`, `facade-inline`,
      `global-mutable-fix`, `naming-fix`, `security-fix`, `docs-fix`
- [ ] Add standards refs per guard (e.g., facade-wrappers → AGENTS.md §Engineering
      quality contract rule 5)
- [ ] Wire guardrails config into `ralph_ai_fix.py` prompt builder so AI gets
      standards context with each finding
- [ ] Add tests for guardrails config loading and validation

### Phase 3: Structured guardrail report (MP-362)

- [ ] Define `ralph-report.json` schema (per-finding status, standards refs,
      fix skills, aggregate analytics)
- [ ] Emit `ralph-report.json` from `ralph_ai_fix.py` after each attempt
- [ ] Add report to workflow artifact upload in `coderabbit_ralph_loop.yml`
- [ ] Add analytics aggregation: fix rate, by-architecture, by-severity,
      false-positive rate, time-to-fix
- [ ] Add report rendering to `triage_loop.py` markdown output

### Phase 4: devctl ralph-status command (MP-363)

- [ ] Create `dev/scripts/devctl/commands/ralph_status.py` — CLI command
- [ ] Create `dev/scripts/devctl/ralph_status_views.py` — view rendering
- [ ] Add parser registration in `cli_parser/reporting.py`
- [ ] Add handler registration in `cli.py`
- [ ] Generate SVG charts: fix rate over time, findings by architecture,
      false-positive rate (reuse `data_science/rendering.py` pattern)
- [ ] Wire into data-science auto-refresh snapshot
- [ ] Add tests

### Phase 5: Operator console Ralph dashboard (MP-364)

- [ ] Create `app/operator_console/state/snapshots/ralph_guardrail_snapshot.py`
      — dataclass for Ralph loop state (phase, findings, analytics, controls)
- [ ] Create `app/operator_console/views/workflow/ralph_dashboard.py`
      — PyQt6 widget with finding table, progress bars, guard health indicators
- [ ] Add control buttons: Start Loop, Pause, Resume, Configure (max attempts,
      approval mode, target branch)
- [ ] Add activity report option "guardrails" to REPORT_OPTIONS
- [ ] Wire into RefreshMixin snapshot cycle
- [ ] Add tests for snapshot loading and dashboard rendering

### Phase 6: Phone/iOS status integration (MP-365)

- [ ] Add `ralph` section to phone status payload (`build_phone_status`)
- [ ] Add `ralph` compact view fields: phase, fix_rate, unresolved, last_attempt
- [ ] Add `ralph` actions: start-loop, pause-loop, configure
- [ ] Wire into `phone_status_views.py` markdown rendering
- [ ] Update iOS `MobileRelayViewModel` to display Ralph metrics
- [ ] Add tests for phone status Ralph integration

### Phase 7: Unified control surface (MP-366)

- [ ] Create `dev/config/ralph_control_state.json` — shared control state
      (mode, max_attempts, approval_mode, target_branch, paused)
- [ ] Add `devctl ralph-control` command for CLI control
      (start, pause, resume, configure)
- [ ] Wire control state into operator console control buttons
- [ ] Wire control state into phone actions
- [ ] Add policy gates: `AUTONOMY_MODE=operate` required for write actions
- [ ] Add control state change audit logging to `devctl_events.jsonl`
- [ ] Add tests for control state transitions

### Phase 8: Guard enforcement inventory alignment (MP-367)

- [ ] Add `check_ralph_guardrail_parity.py` — guard that verifies every entry in
      `AI_GUARD_CHECKS` has a step in `tooling_control_plane.yml`, a row in
      `ralph_guardrails.json`, and a skill mapping
- [ ] Wire parity guard into `tooling_control_plane.yml`
- [ ] Add to `AI_GUARD_CHECKS` in `check_support.py`
- [ ] Add tests

## Progress Log

- 2026-03-09: Phase 1 scaffolding complete. Created `ralph_ai_fix.py` with
  architecture-specific validation (Rust/PyQt6/devctl/iOS), approval-mode
  support, and Claude Code integration. Updated `control_plane_policy.json`
  allowlist, `coderabbit_ralph_loop.yml` default fix command, and `AGENTS.md`
  cross-architecture enforcement policy. Wired 7 new guard scripts into
  `tooling_control_plane.yml`. All guards passing green. Plan doc created and
  registered. Next: Phase 1 unit tests, then Phase 2 guardrails config.

## Audit Evidence

- `python3 dev/scripts/checks/check_facade_wrappers.py` → ok: True, 0 violations
- `python3 dev/scripts/checks/check_structural_similarity.py` → ok: True, -5 pairs
- `python3 dev/scripts/checks/check_python_global_mutable.py` → ok: True, 0 violations
- `python3 dev/scripts/devctl.py hygiene` → Scripts section clean (26 top-level, 51 check scripts)
- `python3 -c "import ast; ast.parse(open('dev/scripts/ralph_ai_fix.py').read())"` → syntax valid
- `python3 -c "import json; json.load(open('dev/config/control_plane_policy.json'))"` → valid
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/coderabbit_ralph_loop.yml'))"` → valid
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/tooling_control_plane.yml'))"` → valid
