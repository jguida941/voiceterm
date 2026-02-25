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
2. Triage and reporting (`status`, `report`, `data-science`, `triage`, `triage-loop`, `mutation-loop`, `autonomy-run`, `autonomy-report`, `phone-status`, `controller-action`, `autonomy-swarm`, `autonomy-benchmark`)
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

`check --profile release` also enforces strict remote release gates by running:

- `status --ci --require-ci`
- `CI=1 check_coderabbit_gate.py --branch master`
- `CI=1 check_coderabbit_ralph_gate.py --branch master`

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

## Human-Readable Loop Digest

Use `autonomy-report` when you want one dated operator bundle with readable
markdown, structured JSON, copied source artifacts, and charts.

```bash
python3 dev/scripts/devctl.py autonomy-report \
  --source-root dev/reports/autonomy \
  --library-root dev/reports/autonomy/library \
  --run-label daily-ops \
  --format md \
  --output /tmp/autonomy-report.md \
  --json-output /tmp/autonomy-report.json
```

Output bundle:

1. `dev/reports/autonomy/library/<run-label>/summary.md`
2. `dev/reports/autonomy/library/<run-label>/summary.json`
3. `dev/reports/autonomy/library/<run-label>/sources/*` (copied input artifacts)
4. `dev/reports/autonomy/library/<run-label>/charts/*` (when matplotlib is available)

## Phone Status Read Surface

Use `phone-status` when you want an iPhone/SSH-safe snapshot from autonomy loop
queue artifacts.

```bash
python3 dev/scripts/devctl.py phone-status \
  --phone-json dev/reports/autonomy/queue/phone/latest.json \
  --view compact \
  --emit-projections dev/reports/autonomy/controller_state/latest \
  --format md \
  --output /tmp/phone-status.md \
  --json-output /tmp/phone-status.json
```

Views:

1. `full`: original queue payload
2. `compact`: small operator summary
3. `trace`: terminal trace and draft context
4. `actions`: loop next-actions plus guarded operator shortcuts

Projection bundle output (optional):

1. `full.json`
2. `compact.json`
3. `trace.ndjson`
4. `actions.json`
5. `latest.md`

## Controller Actions (Guarded)

Use `controller-action` for one bounded operator action at a time.

```bash
python3 dev/scripts/devctl.py controller-action \
  --action dispatch-report-only \
  --repo owner/repo \
  --branch develop \
  --dry-run \
  --format md \
  --output /tmp/controller-action-dispatch.md \
  --json-output /tmp/controller-action-dispatch.json
```

Supported actions:

1. `refresh-status`: read-only projection from phone-status artifacts
2. `dispatch-report-only`: workflow dispatch with `report-only` mode
3. `pause-loop`: request `AUTONOMY_MODE=read-only`
4. `resume-loop`: request `AUTONOMY_MODE=operate`

Guard behavior:

1. Dispatch requires workflow + branch allowlist pass from
   `dev/config/control_plane_policy.json`
2. All write actions are blocked when `AUTONOMY_MODE=off`
3. `--dry-run` shows intended remote command without executing it

## Adaptive Swarm (Metadata + Budget)

Use `autonomy-swarm` to auto-size agent count from multiple signals:

1. change size (`files_changed`, `lines_changed`)
2. problem complexity keywords (`refactor`, `parser`, `security`, etc.)
3. prompt complexity (`prompt_tokens` or estimate from question text)
4. optional token-budget cap (`token_budget / per_agent_token_cost`)

This is usually smarter than using only token count.

```bash
python3 dev/scripts/devctl.py autonomy-swarm \
  --question "large runtime refactor touching parser/security/workspace" \
  --prompt-tokens 48000 \
  --token-budget 120000 \
  --max-agents 20 \
  --parallel-workers 6 \
  --dry-run \
  --no-post-audit \
  --run-label swarm-plan \
  --format md \
  --output /tmp/autonomy-swarm.md \
  --json-output /tmp/autonomy-swarm.json
```

Live one-command execution example (default reviewer + digest behavior):

```bash
python3 dev/scripts/devctl.py autonomy-swarm \
  --agents 10 \
  --question-file dev/active/autonomous_control_plane.md \
  --mode report-only \
  --run-label swarm-live \
  --format md \
  --output /tmp/autonomy-swarm-live.md \
  --json-output /tmp/autonomy-swarm-live.json
```

Execution mode (not plan-only) runs parallel bounded `autonomy-loop` lanes,
reserves one default reviewer slot (`AGENT-REVIEW`) when agent count is >1, and
then automatically runs a post-audit digest (`autonomy-report`) unless you pass
`--no-post-audit` (or `--no-reviewer-lane` to disable reviewer-slot behavior).
For `--mode plan-then-fix` or `--mode fix-only`, pass `--fix-command "<cmd>"`.

1. `dev/reports/autonomy/swarms/<run-label>/summary.md`
2. `dev/reports/autonomy/swarms/<run-label>/summary.json`
3. `dev/reports/autonomy/swarms/<run-label>/AGENT-*/` per-lane artifacts/logs
4. `dev/reports/autonomy/swarms/<run-label>/charts/*`
5. `dev/reports/autonomy/library/<run-label>-digest/summary.md`
6. `dev/reports/autonomy/library/<run-label>-digest/summary.json`

## Swarm Benchmark Matrix (Tradeoff Reports)

Use `autonomy-benchmark` when you want measurable throughput/quality tradeoffs
across different swarm sizes and tactics before running live write-mode flows.

The command enforces active-plan scope first (`plan-doc`, `INDEX`,
`MASTER_PLAN`, `mp-scope`) and then runs a matrix of swarm batches by:

1. swarm counts (`--swarm-counts`, for example `10,15,20,30,40`)
2. tactic profiles (`--tactics`, for example
   `uniform,specialized,research-first,test-first`)

```bash
python3 dev/scripts/devctl.py autonomy-benchmark \
  --plan-doc dev/active/autonomous_control_plane.md \
  --mp-scope MP-338 \
  --swarm-counts 10,15,20,30,40 \
  --tactics uniform,specialized,research-first,test-first \
  --agents 4 \
  --parallel-workers 4 \
  --max-concurrent-swarms 10 \
  --dry-run \
  --format md \
  --output /tmp/autonomy-benchmark.md \
  --json-output /tmp/autonomy-benchmark.json
```

If you use `--mode plan-then-fix` or `--mode fix-only`, you must also pass
`--fix-command "<cmd>"`.

Continuous mode (hands-off checklist progression until failure/limit):

```bash
python3 dev/scripts/devctl.py autonomy-run \
  --plan-doc dev/active/autonomous_control_plane.md \
  --mp-scope MP-338 \
  --mode report-only \
  --continuous \
  --continuous-max-cycles 10 \
  --run-label swarm-continuous \
  --format md \
  --output /tmp/autonomy-run-continuous.md \
  --json-output /tmp/autonomy-run-continuous.json
```

Continuous runs stop when one of these happens:

1. no unchecked checklist items remain in the plan doc
2. a cycle fails swarm/governance/plan-update checks
3. `--continuous-max-cycles` is reached

Output bundle:

1. `dev/reports/autonomy/benchmarks/<run-label>/summary.md`
2. `dev/reports/autonomy/benchmarks/<run-label>/summary.json`
3. `dev/reports/autonomy/benchmarks/<run-label>/scenarios/*/summary.{md,json}`
4. `dev/reports/autonomy/benchmarks/<run-label>/charts/*`

## Guarded Plan-Scoped Swarm Pipeline

Use `autonomy-run` when you want one command to execute this full path:

1. load active plan scope (`plan-doc`, `INDEX`, `MASTER_PLAN` token checks)
2. derive next unchecked plan steps into a swarm prompt
3. run `autonomy-swarm` with default reviewer + post-audit behavior
4. run governance checks (`check_active_plan_sync`, `check_multi_agent_sync`,
   `docs-check --strict-tooling`, `orchestrate-status`, `orchestrate-watch`)
5. append run evidence to plan `Progress Log` + `Audit Evidence`

```bash
python3 dev/scripts/devctl.py autonomy-run \
  --plan-doc dev/active/autonomous_control_plane.md \
  --mp-scope MP-338 \
  --mode report-only \
  --run-label swarm-guarded \
  --format md \
  --output /tmp/autonomy-run.md \
  --json-output /tmp/autonomy-run.json
```

If you use `--mode plan-then-fix` or `--mode fix-only`, you must also pass
`--fix-command "<cmd>"`.

Optional workflow-dispatch equivalent:

```bash
gh workflow run autonomy_run.yml \
  -f plan_doc=dev/active/autonomous_control_plane.md \
  -f mp_scope=MP-338 \
  -f branch_base=develop \
  -f mode=report-only \
  -f agents=10 \
  -f dry_run=true
```

Output bundle:

1. `dev/reports/autonomy/runs/<run-label>/summary.md`
2. `dev/reports/autonomy/runs/<run-label>/summary.json`
3. `dev/reports/autonomy/runs/<run-label>/autonomy-swarm.{md,json}`
4. `dev/reports/autonomy/runs/<run-label>/logs/*`

## Guardrail Checklist

Use these checks before promoting release commits:

```bash
python3 dev/scripts/devctl.py check --profile release
CI=1 python3 dev/scripts/checks/check_coderabbit_gate.py --branch master
CI=1 python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master
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

## Data Science Snapshots (Always-On)

`devctl` now refreshes a rolling data-science snapshot after every command
unless disabled (`DEVCTL_DATA_SCIENCE_DISABLE=1`).

Manual rebuild:

```bash
python3 dev/scripts/devctl.py data-science --format md
```

Default generated outputs:

- `dev/reports/data_science/latest/summary.md`
- `dev/reports/data_science/latest/summary.json`
- `dev/reports/data_science/latest/charts/*.svg`
- `dev/reports/data_science/history/snapshots.jsonl`

Use source/output overrides for focused experiments:

```bash
python3 dev/scripts/devctl.py data-science \
  --output-root dev/reports/data_science \
  --event-log dev/reports/audits/devctl_events.jsonl \
  --swarm-root dev/reports/autonomy/swarms \
  --benchmark-root dev/reports/autonomy/benchmarks \
  --max-events 20000 \
  --format md
```
