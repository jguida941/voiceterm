# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `d2e648f6a7e3` — Refresh external review snapshot for dff02c8
- Tree hash: `6f45e049989d`
- Generation stamp: `snap-bab810255661`
- Generated at (UTC): 2026-04-08T16:51:40Z
- Push decision: `await_checkpoint` — worktree_dirty
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 144 files, +14354/-3333
- Governance findings: 39 open / 68 fixed / 121 total
- Probe hints: 0 total across 0 files scanned

## 1. Identity

- Repository: **VoiceTerm**
- Product thesis: This is the product thesis for the governance stack in this repository.
Absorb these four commitments before engaging with SOP, guard, routing,
or plan detail — they explain why the process exists.

This repo builds a portable AI governance platform proven through one
production client (VoiceTerm, a Rust voice-first terminal overlay for AI
CLIs). The product thesis is that executable local control — guards,
probes, typed actions, deterministic policy resolution — is what makes
AI-assisted engineering reliable, not prompt instructions alone.

**Mission**: Ship a reusable governance stack that any repo can adopt by
installing the platform and selecting a repo pack, without forking
VoiceTerm-specific code.

**Proof obligation**: Every claim about quality, safety, or process
compliance must be backed by a repo-owned executable artifact (guard
script, probe, typed action, CI workflow) that produces the same result
regardless of which AI model or operator runs it. Prompt-only governance
is not accepted as proof.

**Platform boundaries**: VoiceTerm is one client of the platform; portable
governance layers must not hardcode repo names, bridge paths, plan doc
locations, or product-specific defaults. Repo-local assumptions belong in
the repo pack, not in the platform core. MCP servers, operator consoles,
mobile surfaces, and overlay/TUI adapters are clients, not authority.

**Current priority**: Harden the governance stack for multi-repo adoption —
remove VoiceTerm-local assumptions from portable layers, stabilize the
typed contract surface (ProjectGovernance, StartupContext, ReviewState,
TypedAction → ActionResult → RunRecord), and close the remaining probe
and guard gaps so the platform proves its own thesis before external
adopters arrive.
- Remote: `https://github.com/jguida941/voiceterm.git`
- Default branch: `master`
- Current branch: `feature/governance-quality-sweep`
- HEAD SHA: `d2e648f6a7e33f6aa4adb6aae4c42ef5801652c2`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-08T12:20:49-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: worktree_dirty
- push_eligible_now: False
- worktree_clean: False
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260407T220000Z-hardening-plan` (valid=False)
- authorized_head_commit: `ee13a6c6337f395afa574e99a4234f2eaf45a161`
- approved_target_identity: `tree-receipt-20260407T220000Z:281dea21851063411d2c43c2b4621a1c2a1168b5`
- publication_backlog: urgent
- publication_guidance: 15 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

### Reviewer runtime
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `local_terminal`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **Master Plan (Active, Unified)**
- plan path: `dev/active/MASTER_PLAN.md`
- active MP scope: all active MP execution state
- advisory: `checkpoint_allowed` — worktree_dirty_within_budget

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `d2e648f6a7e3`

- commits: 24
- files changed: 144
- insertions: +14354
- deletions: -3333
- bundle classes touched: tooling, docs
- authority surfaces touched: 32 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `d2e648f` | Refresh external review snapshot for dff02c8 | 1 | +79/-77 | tooling |  |
| 2 | `dff02c8` | Converge coordination control-plane read model | 38 | +1496/-112 | tooling |  |
| 3 | `fb212c0` | Refresh review bridge checkpoint state | 2 | +54/-51 | docs |  |
| 4 | `fb46a8a` | Refresh external review snapshot for 70290f0 | 1 | +67/-66 | tooling |  |
| 5 | `70290f0` | Add coordination posture reducers | 19 | +2131/-62 | tooling |  |
| 6 | `36addcb` | Refresh external review snapshot for 05bc3c5 | 1 | +65/-65 | tooling |  |
| 7 | `05bc3c5` | Add PlanningIRSnapshot platform reducer | 14 | +1419/-66 | tooling |  |
| 8 | `941781e` | Refresh external review snapshot for b681930 | 1 | +62/-64 | tooling |  |
| 9 | `b681930` | Checkpoint startup coordination and session hint fixes | 14 | +344/-108 | tooling |  |
| 10 | `ca07a33` | Add typed startup coordination state | 26 | +2273/-141 | tooling |  |
| 11 | `f858e28` | Route startup blockers through shared check renderer | 7 | +481/-187 | tooling |  |
| 12 | `b2a8dbb` | Refresh external review snapshot for b8234a7 | 1 | +61/-64 | tooling |  |
| 13 | `b8234a7` | Prioritize review-loop relaunch recovery | 11 | +236/-98 | tooling |  |
| 14 | `e2b3940` | Reclaim stale review-channel launch windows | 7 | +491/-109 | tooling |  |
| 15 | `9858988` | Fix review-channel session liveness fallback | 4 | +454/-101 | tooling |  |
| 16 | `483df5b` | Refresh external review snapshot for 7d7aa7c | 1 | +60/-67 | tooling |  |
| 17 | `7d7aa7c` | checkpoint: close review-channel authority convergence | 24 | +583/-149 | tooling |  |
| 18 | `1b55564` | Refresh external review snapshot for 8b77c5c | 1 | +53/-56 | tooling |  |
| 19 | `8b77c5c` | checkpoint: record dashboard observer audit findings | 3 | +225/-70 | tooling |  |
| 20 | `fba090f` | checkpoint: close push preflight bypass window | 9 | +129/-73 | tooling |  |
| 21 | `02ca820` | Refresh external review snapshot for fed1dec | 1 | +72/-79 | tooling |  |
| 22 | `fed1dec` | checkpoint: harden reviewer packet guards and runtime counts | 31 | +1230/-108 | tooling |  |
| 23 | `0a678e5` | Refresh external review snapshot for 47c7845 | 1 | +82/-75 | tooling |  |
| 24 | `47c7845` | checkpoint: truth-source hardening and review snapshot evid… | 36 | +2207/-1285 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +60/-3 |
| `bridge.md` | docs | +82/-81 |
| `dev/active/MASTER_PLAN.md` | tooling | +130/-29 |
| `dev/active/ai_governance_platform.md` | tooling | +141/-12 |
| `dev/active/platform_authority_loop.md` | tooling | +106/-1 |
| `dev/active/remote_control_runtime.md` | tooling | +73/-2 |
| `dev/active/review_channel.md` | tooling | +19/-18 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1422/-1433 |
| `dev/audits/architecture_alignment.md` | tooling | +65/-0 |
| `dev/audits/architecture_hardening_plan.md` | tooling | +101/-0 |
| `dev/config/devctl_repo_policy.json` | tooling | +1/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +82/-9 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +356/-0 |
| `dev/scripts/README.md` | tooling | +93/-13 |
| `dev/scripts/checks/startup_authority_contract/command.py` | tooling | +8/-0 |
| `dev/scripts/checks/startup_authority_contract/runtime_checks.py` | tooling | +59/-0 |
| `dev/scripts/devctl/commands/check/__init__.py` | tooling | +2/-2 |
| `dev/scripts/devctl/commands/check/phase_support.py` | tooling | +2/-1 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +75/-12 |
| `dev/scripts/devctl/commands/dashboard_builders.py` | tooling | +11/-0 |
| `dev/scripts/devctl/commands/dashboard_render/attention.py` | tooling | +4/-4 |
| `dev/scripts/devctl/commands/dashboard_render/helpers.py` | tooling | +18/-0 |
| `dev/scripts/devctl/commands/dashboard_render/markdown.py` | tooling | +35/-0 |
| `dev/scripts/devctl/commands/dashboard_render/terminal.py` | tooling | +30/-0 |
| `dev/scripts/devctl/commands/dashboard_typed_state.py` | tooling | +49/-2 |
| `dev/scripts/devctl/commands/governance/session_resume_render.py` | tooling | +70/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +67/-0 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +61/-0 |
| `dev/scripts/devctl/commands/governance/startup_context_blocker_render.py` | tooling | +62/-0 |
| `dev/scripts/devctl/commands/governance/startup_context_render.py` | tooling | +114/-0 |
| `dev/scripts/devctl/commands/review_channel/_render_bridge.py` | tooling | +5/-0 |
| `dev/scripts/devctl/commands/review_channel/bridge_action_support.py` | tooling | +1/-27 |
| `dev/scripts/devctl/commands/review_channel/bridge_render.py` | tooling | +33/-0 |
| `dev/scripts/devctl/commands/review_channel/bridge_support.py` | tooling | +7/-0 |
| `dev/scripts/devctl/commands/review_channel/doctor_support.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/launch_conflicts.py` | tooling | +89/-0 |
| `dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_git.py` | tooling | +9/-22 |
| `dev/scripts/devctl/platform/coordination_snapshot.py` | tooling | +223/-10 |
| `dev/scripts/devctl/platform/coordination_snapshot_models.py` | tooling | +210/-0 |
| _104 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 121
- open: 39
- fixed: 68
- false positives: 0

Recent findings:
- `agent_checkpoint_contract_ignorance` — `dev/scripts/devctl/review_channel/bridge_sanitize.py` (n/a, verdict=`confirmed_issue`)
- `claude_uses_osascript_not_typed_system` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `push_invalidation_head_equality` — `dev/scripts/devctl/review_channel/push_state.py` (n/a, verdict=`confirmed_issue`)
- `reviewer_truth_distributed_no_owner` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `startup_surface_tokens_unpopulated` — `dev/scripts/devctl/runtime/startup_context.py` (n/a, verdict=`confirmed_issue`)
- `terminal_window_id_not_captured` — `dev/scripts/devctl/review_channel/terminal_app.py` (n/a, verdict=`confirmed_issue`)
- `bridge_projection_drops_operator_direction` — `dev/scripts/devctl/review_channel/bridge_projection_state.py` (n/a, verdict=`confirmed_issue`)
- `bridge_still_active_gate_not_projection` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `need_review_channel_doctor_surface` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `reviewer_runtime_contract_needed` — `dev/scripts/devctl/platform/runtime_state_contract_rows.py` (n/a, verdict=`confirmed_issue`)

### Probe report
- run_state: `missing`
- warnings: 0
- errors: 0
- files scanned: 0
- total hints: 0

## 5. Architecture surface

### Contract ownership map

| Contract | Owner layer | Runtime model | Tokens |
|---|---|---|---|
| `ActionResult` | `governance_runtime` | `n/a` | status |
| `ArtifactStore` | `governance_runtime` | `n/a` | root |
| `AutoModeState` | `governance_runtime` | `n/a` | phase |
| `CallerAuthorityPolicy` | `governance_runtime` | `n/a` | caller_id |
| `CheckResult` | `governance_runtime` | `n/a` | success |
| `ControlPlaneReadModel` | `governance_runtime` | `n/a` | push_eligible |
| `ControlState` | `governance_runtime` | `n/a` | approvals |
| `CoordinationSnapshot` | `governance_core` | `n/a` | current_slice |
| `DecisionPacket` | `governance_runtime` | `n/a` | decision_mode |
| `FailurePacket` | `governance_runtime` | `n/a` | runner |
| `Finding` | `governance_runtime` | `n/a` | check_id |
| `LocalServiceEndpoint` | `governance_runtime` | `n/a` | service_id |
| `ProviderAdapter` | `governance_adapters` | `n/a` | provider_id |
| `PushAuthorizationRecord` | `governance_runtime` | `n/a` | authorization_id |
| `RemoteCommitPipelineContract` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:RemoteCommitPipelineContract` | snapshot_id |
| `RepoPack` | `repo_packs` | `n/a` | pack_id |
| `ReviewCandidateRecord` | `governance_runtime` | `n/a` | candidate_id |
| `ReviewState` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewState` | snapshot_id |
| `ReviewerRuntimeContract` | `governance_runtime` | `n/a` | reviewer_mode |
| `RunRecord` | `governance_runtime` | `n/a` | run_id |
| `SessionCachePacket` | `governance_commands` | `n/a` | last_reviewed_sha |
| `TypedAction` | `governance_runtime` | `n/a` | action_id |
| `WorkflowAdapter` | `governance_adapters` | `n/a` | adapter_id |

### Key documents

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`

## 6. Reviewer hints — please verify

### Targeted hints

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_checks.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_git.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_render.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_models_core.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_models_quality.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_models_sections.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_render.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_render_sections.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_sections.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_sections_architecture.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_sections_quality.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_sections_review.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_serialize.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_sources.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_utils.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_review_snapshot.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/coordination_snapshot_models.py`) — Commit dff02c8 changed dev/scripts/devctl/platform/coordination_snapshot_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit dff02c8 changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit dff02c8 changed dev/scripts/devctl/runtime/review_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/coordination_topology_models.py`) — Commit 70290f0 changed dev/scripts/devctl/platform/coordination_topology_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/planning_ir_models.py`) — Commit 05bc3c5 changed dev/scripts/devctl/platform/planning_ir_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_collaboration_models.py`) — Commit ca07a33 changed dev/scripts/devctl/runtime/review_state_collaboration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_intake_models.py`) — Commit ca07a33 changed dev/scripts/devctl/runtime/work_intake_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Commit ca07a33 changed dev/scripts/devctl/tests/checks/test_startup_authority_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/check_result_models.py`) — Commit f858e28 changed dev/scripts/devctl/runtime/check_result_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/test_check_output_contract.py`) — Commit f858e28 changed dev/scripts/devctl/tests/test_check_output_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Commit 47c7845 changed dev/scripts/devctl/review_channel/reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_snapshot_models.py`) — Commit 47c7845 changed dev/scripts/devctl/runtime/review_snapshot_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/review_channel/test_ack_contract.py`) — Commit 47c7845 changed dev/scripts/devctl/tests/review_channel/test_ack_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`d2e648f`** — Refresh external review snapshot for dff02c8
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`dff02c8`** — Converge coordination control-plane read model
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`fb212c0`** — Refresh review bridge checkpoint state
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`fb46a8a`** — Refresh external review snapshot for 70290f0
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`70290f0`** — Add coordination posture reducers
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`36addcb`** — Refresh external review snapshot for 05bc3c5
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`05bc3c5`** — Add PlanningIRSnapshot platform reducer
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`941781e`** — Refresh external review snapshot for b681930
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`b681930`** — Checkpoint startup coordination and session hint fixes
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`ca07a33`** — Add typed startup coordination state
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`f858e28`** — Route startup blockers through shared check renderer
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`b2a8dbb`** — Refresh external review snapshot for b8234a7
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`b8234a7`** — Prioritize review-loop relaunch recovery
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`e2b3940`** — Reclaim stale review-channel launch windows
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`9858988`** — Fix review-channel session liveness fallback
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`483df5b`** — Refresh external review snapshot for 7d7aa7c
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`7d7aa7c`** — checkpoint: close review-channel authority convergence
- **`1b55564`** — Refresh external review snapshot for 8b77c5c
- **`8b77c5c`** — checkpoint: record dashboard observer audit findings
- **`fba090f`** — checkpoint: close push preflight bypass window
- **`02ca820`** — Refresh external review snapshot for fed1dec
- **`fed1dec`** — checkpoint: harden reviewer packet guards and runtime counts
- **`0a678e5`** — Refresh external review snapshot for 47c7845
- **`47c7845`** — checkpoint: truth-source hardening and review snapshot evidence
### Active MP scope (from MASTER_PLAN.md)

- `dev/active/devctl_reporting_upgrade.md` is the phased `devctl` reporting/CIHub specification, but not a separate execution tracker; implementation tasks stay in this file under `MP-297..MP-300`, `MP-303`, `MP-306`, `MP…
- `dev/active/autonomous_control_plane.md` is the autonomous loop + mobile control-plane execution spec; implementation tasks stay in this file under `MP-325..MP-338, MP-340`.
- `dev/active/loop_chat_bridge.md` is the loop artifact-to-chat suggestion coordination runbook; execution evidence and operator handoffs for this path stay there under `MP-338`.
- `dev/active/naming_api_cohesion.md` is the naming/API cohesion execution spec; implementation tasks stay in this file under `MP-267`.
- `dev/active/ide_provider_modularization.md` is the IDE/provider adapter modularization execution spec; implementation tasks stay in this file under `MP-346`, `MP-354`.
- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/ralph_guardrail_control_plane.md` is the Ralph guardrail control plane execution spec; implementation tasks stay in this file under `MP-360..MP-367`.
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- architecture plan for the extracted AI-governance system under `MP-377`.

## 8. Known gaps and open items

- open governance findings: 39

### Startup advisories
- checkpoint_allowed: worktree_dirty_within_budget

### Stale warnings
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/review_channel/bridge_sanitize.py`): agent_checkpoint_contract_ignorance: 
- **governance_open** (`dev/scripts/devctl/review_channel/state.py`): claude_uses_osascript_not_typed_system: 
- **governance_open** (`dev/scripts/devctl/review_channel/push_state.py`): push_invalidation_head_equality: 
- **governance_open** (`dev/scripts/devctl/review_channel/state.py`): reviewer_truth_distributed_no_owner: 
- **governance_open** (`dev/scripts/devctl/runtime/startup_context.py`): startup_surface_tokens_unpopulated: 
- **governance_open** (`dev/scripts/devctl/review_channel/terminal_app.py`): terminal_window_id_not_captured: 
- **governance_open** (`dev/scripts/devctl/review_channel/bridge_projection_state.py`): bridge_projection_drops_operator_direction: 
- **governance_open** (`dev/scripts/devctl/review_channel/state.py`): bridge_still_active_gate_not_projection: 

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-bab810255661` binds this file to HEAD `d2e648f6a7e3`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
