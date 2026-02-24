# Autonomous Loop + Mobile Control Plane

Status: execution mirrored in `dev/active/MASTER_PLAN.md` (MP-325..MP-337)
Execution plan contract: required
Owner lane: Control-plane/governance

## Scope

Build a production-grade autonomous control plane in this repo first, then
extract a reusable template for other projects.

This plan covers:

1. Ralph loop run-correlation correctness.
2. Real `summary-and-comment` notifications.
3. Bounded mutation remediation loop.
4. Rust containerized mobile control service with SMS-first pilot and richer
   channel support next.
5. Guardrail and traceability hardening for autonomous execution.

## Execution Protocol (Required)

1. Every non-trivial agent run must be anchored to this file or another active
   `dev/active/*.md` execution-plan doc with `Execution plan contract: required`.
2. Agents must not run from memory-only plans. They must:
   - update checklist state before/after major execution steps
   - append dated entries to `## Progress Log`
   - keep `dev/active/MASTER_PLAN.md` MP status aligned with actual completion
3. Multi-agent runs must communicate through the shared active-plan doc updates
   (checklist/progress/audit sections), not ad-hoc hidden state.
4. Any scope drift, policy denial, or blocked automation path must be logged in
   this file with reason and mitigation.

## Locked Decisions

1. Rollout is phased by lane.
2. Template path is staged: repo-first, then standalone template.
3. Safety posture is allowlisted and policy-gated; no unrestricted free-form
   command execution.
4. Mobile strategy defaults to SMS backup first, then richer interactive chat.

## External Inputs

1. OpenClaw-style serialized loop with run lifecycle IDs.
2. GitHub Actions dispatch/event semantics for controlled remote execution.
3. Twilio webhook patterns for inbound/outbound SMS control.
4. Telegram Bot API patterns for interactive control loops.
5. `ntfy` pub/sub patterns for low-friction push updates.
6. `network-monitor-tui` runtime throughput panel patterns for dev-mode
   observability surfaces:
   `https://github.com/jguida941/network-monitor-tui`.

## Phase 1 - Harden Existing CodeRabbit Ralph Loop

### 1.1 Run Correlation Fix

- [x] Extend `devctl triage-loop` parser and command with:
  - [x] `--source-run-id`
  - [x] `--source-run-sha`
  - [x] `--source-event` (`workflow_run|workflow_dispatch`)
- [x] Update loop core:
  - [x] Attempt #1 consumes `source-run-id` artifacts when provided.
  - [x] Validate artifact `headSha` matches `source-run-sha` when provided.
  - [x] Fail with explicit reason `source_run_sha_mismatch` on mismatch.
- [x] Update `.github/workflows/coderabbit_ralph_loop.yml`:
  - [x] Pass `github.event.workflow_run.id` and
        `github.event.workflow_run.head_sha` to `triage-loop`.
  - [x] Keep branch fallback behavior for `workflow_dispatch`.

Acceptance:

1. Loop run does not consume unrelated newer triage runs under concurrent
   branch pushes.
2. Report includes `source_run_id`, `source_run_sha`, and correlation result.

### 1.2 Real `summary-and-comment` Behavior

- [x] Add to `devctl triage-loop`:
  - [x] `--notify summary-only|summary-and-comment`
  - [x] `--comment-target auto|pr|commit`
  - [x] `--comment-pr-number` (optional explicit target)
- [x] Implement comment publishing:
  - [x] `auto` resolves PR from backlog artifact metadata when available.
  - [x] `pr` requires an explicit/resolved PR number.
  - [x] `commit` posts commit comment for source SHA.
- [x] Update workflow permissions for comment mode:
  - [x] `pull-requests: write`
  - [x] `contents: write`
- [x] Add idempotency marker to avoid comment spam:
  - [x] Stable marker includes run context (`run_id` + `sha`).
  - [x] Update existing marker comment when present.

Acceptance:

1. `summary-and-comment` produces one canonical updatable comment per target.
2. `summary-only` does not publish comments.

## Phase 2 - Mutation Remediation Loop (Bounded)

### 2.1 New Command: `devctl mutation-loop`

- [x] Add command interface:
  - [x] `devctl mutation-loop --branch <branch>`
  - [x] `--mode report-only|plan-then-fix|fix-only`
  - [x] `--max-attempts N --threshold 0.80 --emit-bundle ...`
- [x] Inputs:
  - [x] Mutation outcomes artifacts.
  - [x] Optional policy-gated fix command.
- [x] Outputs:
  - [x] `mutation-loop.md`
  - [x] `mutation-loop.json`
  - [x] `mutation-loop-playbook.md`

Behavior:

1. `report-only`:
   - Compute score, freshness/stale age, hotspot list, survivor categories.
   - Emit remediation playbook without executing fixes.
2. `plan-then-fix` / `fix-only`:
   - Execute only allowlisted fix steps.
   - Wait for new mutation run.
   - Stop on max attempts or threshold success.

### 2.2 New Workflow: `.github/workflows/mutation_ralph_loop.yml`

- [x] Trigger on `workflow_run` completion of `Mutation Testing`.
- [x] Add `workflow_dispatch` path.
- [x] Support variables:
  - [x] `MUTATION_LOOP_MODE=report-only|always|failure-only`
  - [x] `MUTATION_EXECUTION_MODE=report-only|plan-then-fix|fix-only`
  - [x] `MUTATION_LOOP_MAX_ATTEMPTS`
  - [x] `MUTATION_LOOP_POLL_SECONDS`
  - [x] `MUTATION_LOOP_TIMEOUT_SECONDS`
  - [x] `MUTATION_LOOP_FIX_COMMAND`
  - [x] `MUTATION_NOTIFY_MODE=summary-only|summary-and-comment`
- [x] Gates:
  - [x] Default mode remains report-only.
  - [x] Auto-fix requires explicit allowlist pass.
  - [x] Emit artifact bundle + summary + optional comment.

Acceptance:

1. Mutation lane is non-blocking by default until explicit promotion.
2. Optional auto-fix mode is bounded and auditable.

## Phase 3 - Rust Containerized Mobile Control Plane

### 3.1 New Service: `voiceterm-control` (Rust)

- [ ] Add read-only endpoints for:
  - [ ] Current loop states (CodeRabbit + mutation).
  - [ ] Latest mutation score and freshness.
  - [ ] CI summaries and failing lanes.
  - [ ] `devctl report/status/triage` snapshots.
- [ ] Add controlled actions for:
  - [ ] Workflow dispatch with constrained inputs.
  - [ ] Pause/resume loop mode toggles.
  - [ ] Re-run report-only loops.
- [ ] Require explicit approval gates for:
  - [ ] Fix-mode execution.
  - [ ] Branch/tag/release-impacting actions.

### 3.2 Control API

- [ ] `GET /v1/health`
- [ ] `GET /v1/loops`
- [ ] `GET /v1/mutation`
- [ ] `GET /v1/ci`
- [ ] `POST /v1/actions/dispatch`
- [ ] `POST /v1/actions/mode`
- [ ] `GET /v1/audit`

Security baseline:

- [ ] Signed short-lived session tokens.
- [ ] Role-based scopes (`read`, `operate`, `approve`).
- [ ] Mandatory audit log entries per action.
- [ ] Policy gate before shell/workflow operations.

### 3.3 Phone Adapters

- [ ] v1: SMS adapter (Twilio webhook in/out) for backup/pilot.
- [ ] v1.5: `ntfy` push adapter for rich alerts.
- [ ] v2: interactive chat adapter (Telegram-style).

### 3.4 iPhone-First MVP (Single Operator)

Goal: ship a simple iPhone control surface fast, then expand.

Scope for MVP:

1. Read-first mobile UX with one safe action.
2. Push updates for Ralph loop attempts and final status.
3. Auditable and policy-gated command execution only.

#### MVP Architecture (Pragmatic)

- [ ] UI: lightweight web app/PWA optimized for iPhone Safari (no App Store
      dependency for first release).
- [ ] Backend: Rust `voiceterm-control` service exposes read endpoints and one
      guarded dispatch endpoint.
- [ ] Data source: `devctl triage-loop` bundle artifacts (`.md` + `.json`) and
      loop status snapshots.
- [ ] Primary notifications: push channel (`ntfy` or Slack webhook).
- [ ] SMS fallback: Twilio outbound summary messages for failure/high urgency.
- [ ] Optional dev-mode adapter: import/port `network-monitor-tui` sampling
      model for local throughput/latency panels in `--dev` and phone status
      snapshots (read-only in MVP).
- [ ] Mode-router surface: add isolated runtime mode flags so monitor/tooling
      features do not interfere with default Whisper overlay behavior:
  - [ ] Add a dedicated monitor selector (`--monitor` and/or `--mode monitor`).
  - [ ] Keep default launch path as voice overlay mode unless an explicit mode
        flag is provided.
  - [ ] Route mode-specific initialization (audio/Whisper/backend vs monitor
        sampler/UI) through separate startup branches.

#### MVP Command Set

- [ ] Read-only commands:
  - [ ] View current loop status.
  - [ ] View latest unresolved medium/high count.
  - [ ] View last 5 attempts with run URL + conclusion.
- [ ] One write command:
  - [ ] Dispatch `triage-loop` in `report-only` mode only.
- [ ] Explicitly out-of-scope for MVP:
  - [ ] `plan-then-fix` remote triggering.
  - [ ] Release/tag/branch mutating operations.

#### Notification Contract

- [ ] Add notifier plumbing to `triage-loop`:
  - [ ] `summary-only` sends final result push.
  - [ ] optional attempt updates (`attempt-start`, `attempt-done`).
- [ ] Required message fields:
  - [ ] repo
  - [ ] branch
  - [ ] run URL
  - [ ] unresolved count
  - [ ] mode
  - [ ] reason/status
- [ ] Delivery safety:
  - [ ] idempotency key per loop run
  - [ ] retry with capped backoff
  - [ ] failure audit record when notify send fails

#### Security and Ops for MVP

- [ ] Auth: short-lived signed tokens for phone client sessions.
- [ ] Policy gate: only allowlisted workflow/action inputs from phone.
- [ ] Audit: persist all phone-originated actions with actor + timestamp +
      outcome.
- [ ] Kill switch: `AUTONOMY_MODE=read-only` default until soak window passes.

#### MVP Success Criteria

1. Phone can reliably view live Ralph state and latest artifacts.
2. Phone can trigger only `report-only` loop dispatch and receive status push.
3. Every remote action and notify attempt is traceable in audit logs.
4. No uncontrolled shell execution paths are introduced.

## Phase 4 - Guardrails and Data Quality

- [x] Add policy file `dev/config/control_plane_policy.json`:
  - [x] Allowlisted workflows, refs, inputs, rate limits.
- [ ] Add replay protection (nonce + timestamp window).
- [x] Add kill switch `AUTONOMY_MODE=off|read-only|operate`.
- [x] Add branch-protection-aware action rejection (initial branch allowlist in policy gate).
- [ ] Add loop safety checks:
  - [x] stale-run detection (source-run correlation + timeout reasons)
  - [x] duplicate suppression (idempotent marker-based comment upserts)
  - [ ] max update/comment rate
- [x] Add decision traceability:
  - [x] reason code
  - [x] source evidence pointers

## Test Plan

### Unit

- [x] Source-run correlation for overlapping run timelines.
- [x] Notify target resolution + idempotent comment update.
- [x] Mutation hotspot extraction + reason-code surface.
- [x] Policy gate allowlist/denylist evaluation.
- [ ] Mobile command parser normalization + auth checks.

### Integration

- [ ] `coderabbit_ralph_loop` under overlapping source runs.
- [ ] `summary-and-comment` PR + commit targets.
- [ ] `mutation_ralph_loop` report-only on real artifacts.
- [ ] Fix-mode dry-run allowlisted vs blocked command paths.
- [ ] Twilio webhook roundtrip command dispatch.
- [ ] API auth + replay rejection.

### End-to-End

- [ ] Phone status request returns accurate run-linked state.
- [ ] Phone-triggered report-only mutation loop returns artifact summary.
- [ ] Blocked command attempt yields policy deny + audit trace.
- [ ] No repeated comment spam across repeated loop runs on same target.

## Rollout Plan

1. Milestone A: correlation fix + notify implementation (`summary-only` default).
2. Milestone B: mutation report-only workflow + 1-2 week evidence window.
3. Milestone C: guarded auto-fix enablement for selected branches.
4. Milestone D: deploy Rust control service container + SMS pilot.
5. Milestone E: add richer interactive chat control path.
6. Milestone F: extract reusable standalone template.

## Template Extraction (Stage 2)

- [ ] Package reusable workflows, policy schema, loop scaffolds, adapters, and
      docs playbook.
- [ ] Add bootstrap installer for new repos.
- [ ] Publish adoption guide with safety-first defaults.

## Phase 5 - External Repo Federation Bridge

- [x] Link external upstream sources into this repo via pinned integration
      paths:
  - [x] `integrations/code-link-ide`
  - [x] `integrations/ci-cd-hub`
- [x] Add governed import playbook:
  - [x] `dev/integrations/EXTERNAL_REPOS.md`
  - [x] `dev/scripts/sync_external_integrations.sh`
- [x] Add selective import automation for reusable surfaces
      (workflow snippets, control-plane adapters, mobile/control clients):
  - [x] `devctl integrations-sync` (policy-guarded source sync/status)
  - [x] `devctl integrations-import` (allowlisted source/profile importer)
  - [x] Policy allowlists in `dev/config/control_plane_policy.json`
        (`integration_federation` section with source/profile mappings, destination-root guards, and audit log path).
- [ ] Add `network-monitor-tui` as a third federated source for dev/inner-mode
      observability:
  - [ ] Link `integrations/network-monitor-tui` as a pinned input.
  - [ ] Add allowlisted import profile(s) for throughput/latency sampling
        helpers and TUI panel primitives.
  - [ ] Keep imported surfaces read-only in MVP (`--dev` + phone status only;
        no remote-action coupling), with unique monitor mode flags that keep
        Whisper/voice runtime untouched unless explicitly selected.

Acceptance:

1. External repos are version-pinned and auditable from this repository.
2. Reuse/import flow is documented and aligned to active-plan governance.
3. Updates/imports can be run in one command path without memory-only steps.

## Phase 6 - Scientific Audit + Learning Loop

- [x] Add repeat-to-automate governance policy:
  - [x] `AGENTS.md` continuous-improvement rule.
  - [x] Guard enforcement via `check_agents_contract.py` markers.
- [x] Add audit program directory and baseline artifacts:
  - [x] `dev/audits/README.md`
  - [x] `dev/audits/AUTOMATION_DEBT_REGISTER.md`
  - [x] `dev/audits/2026-02-24-autonomy-baseline-audit.md`
- [x] Add metric schema and event template:
  - [x] `dev/audits/METRICS_SCHEMA.md`
  - [x] `dev/audits/templates/audit_events_template.jsonl`
- [x] Add analyzer script for KPI + chart outputs:
  - [x] `python3 dev/scripts/audits/audit_metrics.py ...`
  - [x] KPI output includes script-only vs AI-assisted vs human-manual share.
  - [x] Optional matplotlib charts by area/source/trend.
- [x] Auto-emit audit events from `devctl` command executions:
  - [x] policy path `audit_metrics.event_log_path`
  - [x] env overrides for cycle/source/area labels
  - [x] unit + CLI emission tests

Acceptance:

1. Audit cycles can quantify what automation handled vs AI/manual intervention.
2. Repeated manual workaround debt is visible and tracked with closure criteria.
3. The audit program supports iterative script improvement over time.
4. `devctl` usage generates audit data automatically with minimal manual logging.

## Assumptions and Defaults

1. `develop` remains integration branch; `master` remains release branch.
2. Auto-fix is disabled by default until explicitly enabled by policy.
3. SMS is the first remote control channel; richer chat follows.
4. Autonomous write actions are auditable and policy-gated.
5. No destructive operations are introduced without explicit policy gates.

## Execution Checklist

- [x] INDEX row is present and synced.
- [x] MASTER_PLAN scope is linked.
- [x] Governance docs updated (`AGENTS`, `DEV_INDEX`, `dev/README`).
- [x] Guard checks updated and passing.
- [ ] Handoff includes evidence and unresolved risks.

## Progress Log

- 2026-02-24: Plan created under `dev/active/` with execution-contract marker,
  staged phases, acceptance criteria, and audit checklist.
- 2026-02-24: Added iPhone-first MVP execution path (read-first UI, one guarded
  write action, push+SMS fallback contract) and aligned it with MP-331 scope.
- 2026-02-24: Implemented MP-325/326 loop hardening (`triage-loop` source-run
  pinning + sha validation + comment-target upsert support) and wired
  `.github/workflows/coderabbit_ralph_loop.yml` source id/sha passing.
- 2026-02-24: Implemented MP-327/328/329 bounded mutation automation (`devctl
  mutation-loop`, `mutation_ralph_loop.yml`, policy-gated fix mode with
  `AUTONOMY_MODE` and allowlisted command prefixes).
- 2026-02-24: Implemented MP-333 enforcement updates in
  `check_active_plan_sync.py` (required execution-plan doc + marker + required
  sections validation) and added policy scaffold file
  `dev/config/control_plane_policy.json` for MP-332 baseline.
- 2026-02-24: Governance/tooling validation pass completed (`check_agents_contract`,
  `check_active_plan_sync`, `check_multi_agent_sync`,
  `docs-check --strict-tooling`, `hygiene`, `check_code_shape`,
  `check_coderabbit_gate`, `check_coderabbit_ralph_gate`, `markdownlint`,
  targeted `unittest` suites for triage/mutation loop modules).
- 2026-02-24: Added external federation bridge with pinned integration links
  (`integrations/code-link-ide`, `integrations/ci-cd-hub`) plus governed sync
  helper (`dev/scripts/sync_external_integrations.sh`) and import playbook
  (`dev/integrations/EXTERNAL_REPOS.md`).
- 2026-02-24: Added `devctl integrations-sync` and
  `devctl integrations-import` command surfaces with policy-gated source/profile
  allowlists, destination-root guards, and JSONL audit logging.
- 2026-02-24: Added `network-monitor-tui` linkage scope (MP-336 planning) for
  optional dev/inner-mode throughput + latency observability reuse, aligned with
  read-only `--dev` and phone-status surfaces.
- 2026-02-24: Added plan direction for unique monitor-mode flags (`--monitor`
  and/or `--mode monitor`) so dev/inner-mode observability can share the Rust UI
  framework without interfering with default Whisper/voice overlay startup.
- 2026-02-24: Added MP-337 repeat-to-automate governance policy and first-cycle
  audit-program scaffolding (`dev/audits/README.md`,
  `AUTOMATION_DEBT_REGISTER.md`, baseline audit checklist).
- 2026-02-24: Added audit metric schema/template and analyzer script
  (`dev/scripts/audits/audit_metrics.py`) to compute scientific audit KPIs
  (automation coverage, script-only share, AI-assisted share, manual share,
  success rate) and generate optional matplotlib charts.
- 2026-02-24: Added automatic `devctl` event emission into
  `dev/reports/audits/devctl_events.jsonl` (policy/env configurable) so every
  control-plane run contributes to KPI trend analysis by default.

## Audit Evidence

| Check | Evidence | Status |
|---|---|---|
| `check_active_plan_sync` | `ok: True` (2026-02-24 local run) | done |
| `check_agents_contract` | `ok: True` (2026-02-24 local run; repeat-to-automate markers enforced) | done |
| `check_multi_agent_sync` | `ok: True` (2026-02-24 local run) | done |
| `docs-check --strict-tooling` | `ok: True` (2026-02-24 local run) | done |
| `hygiene` | `ok: True` (2026-02-24 local run; non-blocking local warnings only) | done |
| `devctl integrations-sync --status-only --format md` | `ok: True` with pinned SHAs for both sources (2026-02-24 local run) | done |
| `devctl integrations-import --list-profiles --format md` | allowlisted source/profile matrix rendered (2026-02-24 local run) | done |
| `devctl integrations-import --source code-link-ide --profile iphone-core --format md` | preview mode planned import succeeded with destination-root policy guard (2026-02-24 local run) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_integrations_sync dev.scripts.devctl.tests.test_integrations_import` | `Ran 7 tests ... OK` (2026-02-24 local run) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_audit_metrics_script` | `Ran 2 tests ... OK` (2026-02-24 local run) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_audit_events dev.scripts.devctl.tests.test_cli_audit_events` | `Ran 5 tests ... OK` (2026-02-24 local run) | done |
| `python3 dev/scripts/audits/audit_metrics.py --input dev/audits/templates/audit_events_template.jsonl --output-md /tmp/audit-metrics.md --output-json /tmp/audit-metrics.json --chart-dir /tmp/audit-metrics-charts` | summary + JSON + chart outputs emitted (2026-02-24 local run) | done |
| `DEVCTL_AUDIT_CYCLE_ID=baseline-2026-02-24 DEVCTL_EXECUTION_SOURCE=script_only python3 dev/scripts/devctl.py list` | event row appended to `dev/reports/audits/devctl_events.jsonl` (2026-02-24 local run) | done |
