# Autonomy Baseline Audit - 2026-02-24

Purpose: run the first full-system audit cycle for autonomy surfaces, highest
risk first, with clear automated vs physical/manual evidence.

## Scope

- CodeRabbit loop hardening (`triage-loop`, workflow wiring, notify behavior).
- Mutation loop behavior (report-only first, guarded fix paths).
- External federation controls (`integrations-sync`, `integrations-import`).
- Multi-agent coordination/audit controls.
- Phone-control readiness checks (where implemented) plus manual test script.
- Scientific-style measurement of automation quality, including AI vs script
  execution share and trend charts.

MP linkage: `MP-325..MP-337`.

## Phase 0 - Prep

- [ ] Confirm clean understanding of target branch and scope in `MASTER_PLAN`.
- [ ] Run `python3 dev/scripts/devctl.py orchestrate-status --format md`.
- [ ] Run `python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md`.
- [ ] Confirm active execution plan updates are in `dev/active/*.md` (no memory-only state).

## Phase 1 - Highest-risk automated gates

- [ ] `python3 dev/scripts/checks/check_agents_contract.py`
- [ ] `python3 dev/scripts/checks/check_active_plan_sync.py`
- [ ] `python3 dev/scripts/checks/check_multi_agent_sync.py`
- [ ] `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- [ ] `python3 dev/scripts/devctl.py hygiene`
- [ ] `python3 dev/scripts/checks/check_coderabbit_gate.py --branch master`
- [ ] `python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master`
- [ ] `python3 dev/scripts/devctl.py mutation-score --threshold 0.80 --max-age-hours 72`

## Phase 2 - Loop behavior verification

- [ ] `python3 dev/scripts/devctl.py triage-loop --help`
- [ ] `python3 dev/scripts/devctl.py mutation-loop --help`
- [ ] Validate source-run pinning evidence in latest loop bundle (`source_run_id`, `source_run_sha`, correlation result).
- [ ] Validate notify mode behavior (`summary-only` no comment; `summary-and-comment` idempotent marker update).
- [ ] Validate mutation mode policy paths (`report-only` default, deny reason codes for blocked fix commands).

## Phase 3 - Federation and template-readiness checks

- [ ] `python3 dev/scripts/devctl.py integrations-sync --status-only --format md`
- [ ] `python3 dev/scripts/devctl.py integrations-import --list-profiles --format md`
- [ ] Profile preview checks:
  - [ ] `python3 dev/scripts/devctl.py integrations-import --source code-link-ide --profile iphone-core --format md`
  - [ ] `python3 dev/scripts/devctl.py integrations-import --source ci-cd-hub --profile workflow-templates --dry-run --format md`
- [ ] Confirm import results stay under policy destination roots.
- [ ] Confirm JSONL audit record appended for sync/import runs.

## Phase 4 - Metrics instrumentation and charting

1. Create a cycle event log using
   `dev/audits/templates/audit_events_template.jsonl` as the schema baseline.
   - `devctl` commands auto-emit rows to
     `dev/reports/audits/devctl_events.jsonl`; set `DEVCTL_AUDIT_CYCLE_ID` for
     cycle labeling.
2. Record every major audit step (automated and manual) with:
   - source bucket (`script_only`, `ai_assisted`, `human_manual`)
   - outcome (`success`)
   - duration/retries
   - manual reason and `repeated_workaround` when not automated
3. Run the analyzer:

```bash
python3 dev/scripts/audits/audit_metrics.py \
  --input dev/reports/audits/baseline-events.jsonl \
  --output-md dev/reports/audits/baseline-metrics.md \
  --output-json dev/reports/audits/baseline-metrics.json \
  --chart-dir dev/reports/audits/charts
```

1. Capture these baseline KPIs:
   - automation coverage
   - script-only share
   - AI-assisted share
   - manual intervention share
   - success rate
   - repeated-workaround share

## Phase 5 - Manual/physical operator script

Use this section for guided operator testing on desktop + iPhone surfaces.

1. Desktop runtime:
   - [ ] Start VoiceTerm in target mode.
   - [ ] Trigger a non-destructive report path (`status`, `report`, loop status views).
   - [ ] Capture logs and screenshots for each major UI/state transition.
2. Mobile/remote control rehearsal (current capability level):
   - [ ] Run read-only status requests through available adapter path.
   - [ ] Attempt one intentionally blocked action and capture policy-deny output.
   - [ ] Confirm audit log contains actor/timestamp/action/reason.
3. If phone-control service endpoints are implemented:
   - [ ] `GET /v1/health`
   - [ ] `GET /v1/loops`
   - [ ] `GET /v1/mutation`
   - [ ] `GET /v1/ci`
   - [ ] `GET /v1/audit`
   - [ ] One guarded `POST` action with expected allow/deny result.

## Phase 6 - Findings triage and repeat-to-automate capture

- [ ] Classify findings by severity (`critical`, `high`, `medium`, `low`).
- [ ] Open/refresh MP items for unresolved high/critical findings.
- [ ] For each repeated manual workaround (2+ occurrences), do one:
  - [ ] Add/extend guarded automation (`devctl`/workflow/check + tests), or
  - [ ] Log debt in `dev/audits/AUTOMATION_DEBT_REGISTER.md` with exit criteria.
- [ ] Include KPI deltas in findings summary (did script-only share rise and manual share drop?).
- [ ] Update `dev/history/ENGINEERING_EVOLUTION.md` if tooling/process governance changed.

## Evidence Log

| Area | Command or step | Result | Evidence path |
|---|---|---|---|
| governance | `check_active_plan_sync` | pending | |
| loops | `triage-loop`/`mutation-loop` verification | pending | |
| federation | sync/import checks | pending | |
| metrics | `audit_metrics.py` summary + charts | pending | |
| manual | desktop + phone script | pending | |

## Exit Criteria

1. No unresolved critical findings.
2. High findings have owner + MP + target date.
3. Repeat-to-automate rule applied to all repeated manual steps.
4. Audit summary and links captured in active plan + handoff.
