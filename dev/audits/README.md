# Audit Program

Use this directory for repeatable, evidence-backed system audits.

## What goes here

- Cycle runbooks/checklists (for example baseline or release audits).
- Automation-debt tracking when repeated manual work cannot be automated yet.
- Audit outcome summaries with command evidence and follow-up MP links.

## Conventions

1. Name cycle docs with date prefix: `YYYY-MM-DD-<scope>.md`.
2. Keep checklists explicit and risk-ordered (highest-risk first).
3. Link every major finding to `dev/active/MASTER_PLAN.md` MP scope.
4. If a workaround repeats 2+ times, either automate it or log it in
   `AUTOMATION_DEBT_REGISTER.md`.
5. Store large/raw artifacts under `dev/reports/`; keep this directory as
   concise operator-facing markdown.
6. `devctl` commands auto-emit JSONL events to
   `dev/reports/audits/devctl_events.jsonl` (policy/env configurable).

## Current entry points

- Baseline runbook: `2026-02-24-autonomy-baseline-audit.md`
- Automation debt register: `AUTOMATION_DEBT_REGISTER.md`
- Metrics schema: `METRICS_SCHEMA.md`
- Event template: `templates/audit_events_template.jsonl`
- Analyzer: `python3 dev/scripts/audits/audit_metrics.py ...`
