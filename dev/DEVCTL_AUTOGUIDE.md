# Devctl Autoguide

This guide explains how to run the `devctl` control plane end-to-end with
minimal manual intervention.

Use this with:

- `AGENTS.md` for policy, required bundles, and release SOP
- `dev/DEVELOPMENT.md` for lifecycle flow and verification matrix
- `dev/scripts/README.md` for full command inventory

## What It Controls

`devctl` is the maintainer entrypoint for:

1. Quality gates (`check`, `docs-check`, `hygiene`, security guards)
2. Triage and reporting (`status`, `report`, `triage`, `triage-loop`, `mutation-loop`)
3. Release verification and distribution (`ship`, `release`, `pypi`, `homebrew`)
4. Orchestration guardrails (`orchestrate-status`, `orchestrate-watch`)
5. External federation guardrails (`integrations-sync`, `integrations-import`)

## Fast Paths

### Normal push path

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/devctl.py triage --ci --format md
```

### Tooling/process/CI path

```bash
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md
python3 dev/scripts/devctl.py triage --ci --no-cihub --emit-bundle \
  --bundle-dir .cihub/coderabbit --bundle-prefix tooling-pass --format md
```

### Release path

```bash
python3 dev/scripts/devctl.py ship --version X.Y.Z --prepare-release --verify --tag --notes --github --yes
```

`ship --verify` requires both:

- `check_coderabbit_gate.py`
- `check_coderabbit_ralph_gate.py`

## Always-On Ralph Loop

`CodeRabbit Ralph Loop` runs after `CodeRabbit Triage Bridge` completes on
`develop` and `master` branches.

Runtime controls are repo variables:

- `RALPH_LOOP_MODE`: `always` | `failure-only` | `disabled`
- `RALPH_EXECUTION_MODE`: `report-only` | `plan-then-fix` | `fix-only`
- `RALPH_LOOP_MAX_ATTEMPTS`
- `RALPH_LOOP_POLL_SECONDS`
- `RALPH_LOOP_TIMEOUT_SECONDS`
- `RALPH_LOOP_FIX_COMMAND`
- `RALPH_NOTIFY_MODE`: `summary-only` | `summary-and-comment`
- `RALPH_COMMENT_TARGET`: `auto` | `pr` | `commit`
- `RALPH_COMMENT_PR_NUMBER`: optional explicit PR target

Default operating mode:

1. `RALPH_LOOP_MODE=always`
2. `RALPH_EXECUTION_MODE=plan-then-fix`

In `plan-then-fix`, the loop reports backlog state first, then runs bounded
fix attempts when a fix command is configured.

## Local Ralph/Triage Loop

Use `triage-loop` to run the same logic locally or in custom automation.

```bash
python3 dev/scripts/devctl.py triage-loop \
  --repo owner/repo \
  --branch develop \
  --mode plan-then-fix \
  --max-attempts 3 \
  --poll-seconds 20 \
  --timeout-seconds 1800 \
  --source-event workflow_dispatch \
  --notify summary-and-comment \
  --comment-target auto \
  --fix-command "python3 dev/scripts/devctl.py check --profile ci" \
  --emit-bundle \
  --bundle-dir .cihub/coderabbit \
  --bundle-prefix coderabbit-ralph-loop \
  --mp-proposal \
  --format md \
  --output /tmp/coderabbit-ralph-loop.md \
  --json-output /tmp/coderabbit-ralph-loop.json
```

Output includes:

- attempt-by-attempt status (`run_id`, `sha`, `conclusion`, `backlog_count`)
- unresolved medium/high count
- final reason
- source run correlation fields (`source_run_id`, `source_run_sha`, `source_correlation`)
- optional MASTER_PLAN proposal artifact

## Mutation Ralph Loop

`Mutation Ralph Loop` runs after `Mutation Testing` and can stay report-only by
default until policy gates are promoted.

Runtime controls are repo variables:

- `MUTATION_LOOP_MODE`: `always` | `failure-only` | `disabled`
- `MUTATION_EXECUTION_MODE`: `report-only` | `plan-then-fix` | `fix-only`
- `MUTATION_LOOP_MAX_ATTEMPTS`
- `MUTATION_LOOP_POLL_SECONDS`
- `MUTATION_LOOP_TIMEOUT_SECONDS`
- `MUTATION_LOOP_THRESHOLD`
- `MUTATION_LOOP_FIX_COMMAND`
- `MUTATION_NOTIFY_MODE`: `summary-only` | `summary-and-comment`
- `MUTATION_COMMENT_TARGET`: `auto` | `pr` | `commit`
- `MUTATION_COMMENT_PR_NUMBER`: optional explicit PR target

Local command:

```bash
python3 dev/scripts/devctl.py mutation-loop \
  --repo owner/repo \
  --branch develop \
  --mode report-only \
  --threshold 0.80 \
  --max-attempts 3 \
  --emit-bundle \
  --bundle-dir .cihub/mutation \
  --bundle-prefix mutation-ralph-loop \
  --format md \
  --output /tmp/mutation-ralph-loop.md \
  --json-output /tmp/mutation-ralph-loop.json
```

Fix mode policy gates:

- `AUTONOMY_MODE` must be `operate`
- branch must be allowlisted in `dev/config/control_plane_policy.json`
- fix command must match allowlisted prefixes

## MASTER_PLAN Proposal Loop

`triage-loop --mp-proposal` emits a proposal markdown file. It does not edit
`dev/active/MASTER_PLAN.md` directly.

Recommended automation pattern:

1. loop generates proposal artifact
2. reviewer agent validates evidence + policy gates
3. only allowlisted plan/status sections are updated

## Failure Handling

If the loop is blocked or fails:

1. Read the generated `*.md` and `*.json` artifacts.
2. Run `devctl triage --ci` for a current owner/severity snapshot.
3. Run `devctl audit-scaffold --force --yes --format md` for guard-driven
   remediation scaffolding.
4. Re-run `triage-loop` after fixes land.

## Guardrail Checklist

Use these checks before promoting release commits:

```bash
python3 dev/scripts/checks/check_coderabbit_gate.py --branch master
python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master
python3 dev/scripts/devctl.py check --profile release
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
```

## External Federation (Guarded)

Use these commands when pulling reusable patterns from linked repos:

```bash
python3 dev/scripts/devctl.py integrations-sync --status-only --format md
python3 dev/scripts/devctl.py integrations-import --list-profiles --format md
python3 dev/scripts/devctl.py integrations-import --source code-link-ide --profile iphone-core --format md
python3 dev/scripts/devctl.py integrations-import --source ci-cd-hub --profile workflow-templates --apply --yes --format md
```

Policy rules are enforced from `dev/config/control_plane_policy.json`:

1. source names and profile mappings are allowlisted
2. import destinations must remain under allowlisted destination roots
3. each sync/import action is appended to `dev/reports/integration_import_audit.jsonl`

## Audit Metrics (Scientific Loop)

Use the audit metrics helper to quantify how much the workflow is script-driven
vs AI-assisted vs manual, then track trend lines over time.

```bash
python3 dev/scripts/audits/audit_metrics.py \
  --input dev/reports/audits/baseline-events.jsonl \
  --output-md dev/reports/audits/baseline-metrics.md \
  --output-json dev/reports/audits/baseline-metrics.json \
  --chart-dir dev/reports/audits/charts
```

Baseline schema and KPI definitions live in:

- `dev/audits/METRICS_SCHEMA.md`
- `dev/audits/templates/audit_events_template.jsonl`

`devctl` commands now auto-append one event row to the audit event log (default
`dev/reports/audits/devctl_events.jsonl`). Use env overrides to label cycles
and source type during experiments:

```bash
DEVCTL_AUDIT_CYCLE_ID=baseline-2026-02-24 \
DEVCTL_EXECUTION_SOURCE=ai_assisted \
python3 dev/scripts/devctl.py triage-loop --help
```
