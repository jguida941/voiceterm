# Audit Metrics Schema

Use this schema for JSONL event logs that feed
`python3 dev/scripts/audits/audit_metrics.py`.

This schema is for machine-readable operational telemetry. It is not the prose
session-history surface. For AI/contributor handoff, update the active plan's
`Session Resume` and `Progress Log`; use these JSONL logs for command/run
metrics, governance evidence, later SQLite indexing, and ML/ranking inputs.

## Event fields

Required:

- `timestamp` (ISO-8601 string)
- `cycle_id` (audit cycle identifier)
- `area` (for example `governance`, `loops`, `federation`, `manual-physical`)
- `step` (specific command or manual action label)
- `automated` (`true`/`false`)
- `success` (`true`/`false`)

Recommended:

- `execution_source`: `script_only` | `ai_assisted` | `human_manual`
- `actor`: `script` | `ai` | `human` | `hybrid`
- `duration_seconds` (non-negative number)
- `retries` (non-negative integer)
- `manual_reason` (string, required when `automated=false`)
- `repeated_workaround` (`true` when this workaround has happened before)
- `command` (`devctl` command name when auto-emitted)
- `returncode` (process-style command result)
- `argv` (invocation args sample)

## Auto-emitted `devctl` events

Every `python3 dev/scripts/devctl.py ...` invocation appends one event row to:

- policy path: `control_plane_policy.json` -> `audit_metrics.event_log_path`
- env override: `DEVCTL_AUDIT_EVENT_LOG`

Default path:

- `dev/reports/audits/devctl_events.jsonl`

Useful env controls:

- `DEVCTL_AUDIT_CYCLE_ID` (example `baseline-2026-02-24`)
- `DEVCTL_AUDIT_AREA` (override inferred area bucket)
- `DEVCTL_AUDIT_STEP` (override default step label)
- `DEVCTL_EXECUTION_SOURCE` (`script_only|ai_assisted|human_manual|other`)
- `DEVCTL_EXECUTION_ACTOR` (`script|ai|human|hybrid`)
- `DEVCTL_AUDIT_AUTOMATED` (`true|false`)
- `DEVCTL_AUDIT_RETRIES` (integer)
- `DEVCTL_MANUAL_REASON` (string for manual intervention context)
- `DEVCTL_REPEATED_WORKAROUND` (`true|false`)
- `DEVCTL_AUDIT_DISABLE` (`true|false`)

## Core metrics

The analyzer computes:

1. `automation_coverage_pct`: automated events / total events.
2. `script_only_pct`: script-only events / total events.
3. `ai_assisted_pct`: AI-assisted events / total events.
4. `human_manual_pct`: human-manual events / total events.
5. `success_rate_pct`: successful events / total events.
6. `repeated_workaround_pct`: repeated-workaround events / total events.
7. Area-level success/automation percentages and mean durations.
8. Manual-reason frequency ranking.

## Output artifacts

- Markdown summary (`--output-md`)
- JSON summary (`--output-json`)
- Optional charts (`--chart-dir`) when `matplotlib` is available:
  - `source_breakdown.png`
  - `area_source_breakdown.png`
  - `automation_coverage_trend.png`

## Portable governance review ledger

Portable-governance effectiveness also needs adjudicated finding data, not only
command audit events.

Use these surfaces together:

- Schema: `dev/config/templates/portable_governance_finding_review.schema.json`
- Command: `python3 dev/scripts/devctl.py governance-review --format md`
- Log path: `dev/reports/governance/finding_reviews.jsonl`
- Summary artifacts: `dev/reports/governance/latest/review_summary.{md,json}`

That ledger captures:

- `false_positive` findings
- `confirmed_issue` findings
- `fixed` findings
- `deferred` or `waived` debt

`python3 dev/scripts/devctl.py data-science --format md` rolls those rows into
the main telemetry snapshot so false-positive rate and cleanup progress stay
visible while the repo keeps using the guards/probes to clean up code.
