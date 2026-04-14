# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `dde973d5387f` — Refresh external review snapshot for 24689590
- Tree hash: `2a04da77920b`
- Generation stamp: `snap-cf014a2276db`
- Generated at (UTC): 2026-04-14T06:31:57Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 316 files, +24057/-6902
- Governance findings: 118 open / 79 fixed / 211 total
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
- HEAD SHA: `dde973d5387fe334dd228288c16100ae1706d4c5`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-13T19:13:33-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 33
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `published_remote` (post_push_bundle_pending)
- publication_backlog: urgent
- publication_guidance: 22 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

### Reviewer runtime
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `local_terminal`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `dde973d5387f`

- commits: 25
- files changed: 316
- insertions: +24057
- deletions: -6902
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 41 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `dde973d5` | Refresh external review snapshot for 24689590 | 1 | +64/-72 | tooling |  |
| 2 | `24689590` | Add dogfood governance recording and plan registry authorit… | 17 | +901/-113 | tooling |  |
| 3 | `27b7826c` | Refresh external review snapshot for a83b7f81 | 1 | +83/-84 | tooling |  |
| 4 | `a83b7f81` | Add dogfood coverage and bridge portability | 47 | +1760/-224 | tooling |  |
| 5 | `e78905c2` | Refresh external review snapshot for d6e474d5 | 1 | +47/-51 | tooling |  |
| 6 | `d6e474d5` | Refresh bridge.md projection from typed state for push | 2 | +69/-172 | docs |  |
| 7 | `871812bb` | Refresh review snapshot for governance-quality-sweep push | 1 | +55/-59 | tooling |  |
| 8 | `45376a16` | Refresh external review snapshot for a19534a9 | 1 | +63/-65 | tooling |  |
| 9 | `a19534a9` | Fix active_target routing, projection parity, and dogfood s… | 31 | +1070/-143 | tooling |  |
| 10 | `ffafe4ff` | Expand contract closure to internal types and wire governan… | 13 | +584/-66 | tooling |  |
| 11 | `9e75a66d` | Refresh external review snapshot for 5a4236c1 | 1 | +59/-63 | tooling |  |
| 12 | `5a4236c1` | Wire FindingBacklog, connection pairs, and probe split advi… | 42 | +1803/-224 | tooling | Parser / ANSI boundary |
| 13 | `67afd4d5` | Refresh external review snapshot for d0e5ac47 | 1 | +80/-83 | tooling |  |
| 14 | `d0e5ac47` | Consolidate plan system: typed phases, plan ingestion, guar… | 29 | +1219/-229 | tooling |  |
| 15 | `c06a989a` | Refresh external review snapshot for 1e24f79f | 1 | +110/-83 | tooling |  |
| 16 | `1e24f79f` | Fix remote-control review-channel guard regressions and ext… | 158 | +12763/-4359 | tooling | Parser / ANSI boundary |
| 17 | `687c0478` | Refresh external review snapshot for 4372e2cd | 1 | +86/-83 | tooling |  |
| 18 | `4372e2cd` | Fix probe shims, event projection, and launch/rollover test… | 44 | +943/-142 | tooling |  |
| 19 | `f88de94b` | Refresh external review snapshot for 5ed6e2fb | 1 | +80/-71 | tooling |  |
| 20 | `5ed6e2fb` | Make review state role-neutral and bind push approval to wo… | 45 | +730/-117 | tooling |  |
| 21 | `a1c7ffe3` | Refresh external review snapshot for 00e45380 | 1 | +67/-64 | tooling |  |
| 22 | `00e45380` | Checkpoint single-agent liveness and worker-lane portability | 33 | +815/-159 | tooling |  |
| 23 | `763be95d` | Refresh external review snapshot for e8ccc7e7 | 1 | +63/-64 | tooling |  |
| 24 | `e8ccc7e7` | review_channel: remote-control attachment counts as live co… | 11 | +258/-61 | tooling |  |
| 25 | `70e2544f` | docs(audit): dashboard-loop ticks 33-48 + liveness symmetry… | 3 | +285/-51 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +53/-12 |
| `bridge.md` | docs | +91/-221 |
| `dev/active/INDEX.md` | tooling | +35/-49 |
| `dev/active/MASTER_PLAN.md` | tooling | +195/-51 |
| `dev/active/ai_governance_platform.md` | tooling | +401/-54 |
| `dev/active/autonomous_governance_loop_v2.md` | tooling | +59/-19 |
| `dev/active/continuous_swarm.md` | tooling | +354/-8 |
| `dev/active/platform_authority_loop.md` | tooling | +51/-1 |
| `dev/active/remote_commit_pipeline.md` | tooling | +113/-1 |
| `dev/active/remote_control_runtime.md` | tooling | +284/-21 |
| `dev/active/review_channel.md` | tooling | +7/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +645/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1684/-1664 |
| `dev/config/devctl_policies/launcher.json` | tooling | +25/-0 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +45/-9 |
| `dev/config/quality_presets/portable_python.json` | tooling | +3/-1 |
| `dev/config/quality_presets/portable_rust.json` | tooling | +1/-0 |
| `dev/config/templates/portable_governance_finding_review.schema.json` | tooling | +1/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +74/-10 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +402/-2 |
| `dev/scripts/README.md` | tooling | +81/-36 |
| `dev/scripts/checks/active_plan/contract.py` | tooling | +0/-16 |
| `dev/scripts/checks/active_plan/typed_phase_contract.py` | tooling | +104/-0 |
| `dev/scripts/checks/check_active_plan_sync.py` | tooling | +25/-54 |
| `dev/scripts/checks/check_bundle_workflow_parity.py` | tooling | +66/-1 |
| `dev/scripts/checks/check_duplication_audit.py` | tooling | +69/-1 |
| `dev/scripts/checks/check_naming_consistency.py` | tooling | +60/-1 |
| `dev/scripts/checks/check_rustsec_policy.py` | tooling | +17/-1 |
| `dev/scripts/checks/code_shape/code_shape_policy.py` | tooling | +0/-54 |
| `dev/scripts/checks/code_shape_support/probe_split_advisor.py` | tooling | +342/-0 |
| `dev/scripts/checks/governance_closure/command.py` | tooling | +11/-0 |
| `dev/scripts/checks/governance_closure/contract_connectivity.py` | tooling | +91/-0 |
| `dev/scripts/checks/naming_consistency/core.py` | tooling | +2/-2 |
| `dev/scripts/checks/platform_contract_closure/emitter_parity_contract_checks.py` | tooling | +8/-3 |
| `dev/scripts/checks/platform_contract_closure/field_routes.py` | tooling | +27/-0 |
| `dev/scripts/checks/platform_contract_closure/field_routes_planning.py` | tooling | +165/-0 |
| `dev/scripts/checks/probe_boolean_params.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_clone_density.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_concurrency.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_defensive_overchecking.py` | tooling | +17/-1 |
| _276 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 211
- open: 118
- fixed: 79
- false positives: 0

Recent findings:
- `dogfood.code_shape_push_regression` — `dev/scripts/devctl/commands/vcs/push.py` (n/a, verdict=`confirmed_issue`)
- `dogfood_finding_id_instability` — `dev/scripts/devctl/runtime/dogfood_log.py` (n/a, verdict=`confirmed_issue`)
- `dogfood_read_only_registration_missing` — `dev/scripts/devctl/cli_parser/entrypoint.py` (n/a, verdict=`confirmed_issue`)
- `finding_backlog_writer_closure_broken` — `dev/scripts/devctl/runtime/finding_backlog.py` (n/a, verdict=`confirmed_issue`)
- `dogfood_governance_pipeline_missing` — `dev/scripts/devctl/runtime/dogfood_log.py` (n/a, verdict=`confirmed_issue`)
- `bridge_authority_conflict` — `bridge.md` (n/a, verdict=`confirmed_issue`)
- `plan_markdown_projection_missing` — `dev/scripts/devctl/platform/planning_ir_models.py` (n/a, verdict=`confirmed_issue`)
- `plan_authority_gap` — `dev/active/MASTER_PLAN.md` (n/a, verdict=`confirmed_issue`)
- `bridge_metadata_parsed_as_authority` — `dev/scripts/devctl/review_channel/handoff.py` (n/a, verdict=`confirmed_issue`)
- `authority_snapshot_3_fields_missing` — `dev/scripts/devctl/runtime/startup_context.py` (n/a, verdict=`confirmed_issue`)

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

- **risk**: Parser / ANSI boundary — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_heading_aliases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_sanitize.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_validation_stall.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_parse.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_git.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_phases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_metadata.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_sections.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_promotion.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_doctor_surface.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_publication.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_receipt.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_remote_commit_pipeline_phases34.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actions.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_authorization.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_push.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_parser.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/ack_contract.py`) — Commit a83b7f81 changed dev/scripts/devctl/review_channel/ack_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/dogfood_models.py`) — Commit a83b7f81 changed dev/scripts/devctl/runtime/dogfood_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Commit a83b7f81 changed dev/scripts/devctl/runtime/project_governance_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/review_channel/test_ack_contract.py`) — Commit a83b7f81 changed dev/scripts/devctl/tests/review_channel/test_ack_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/planning_ir_models.py`) — Commit 5a4236c1 changed dev/scripts/devctl/platform/planning_ir_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_intake_models.py`) — Commit 5a4236c1 changed dev/scripts/devctl/runtime/work_intake_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/checks/active_plan/typed_phase_contract.py`) — Commit d0e5ac47 changed dev/scripts/checks/active_plan/typed_phase_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/test_active_plan_contract.py`) — Commit d0e5ac47 changed dev/scripts/devctl/tests/test_active_plan_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit 1e24f79f changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/bridge_projection_contract.py`) — Commit 1e24f79f changed dev/scripts/devctl/review_channel/bridge_projection_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/pending_packet_models.py`) — Commit 1e24f79f changed dev/scripts/devctl/review_channel/pending_packet_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Commit 1e24f79f changed dev/scripts/devctl/review_channel/reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit 1e24f79f changed dev/scripts/devctl/runtime/review_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_packet_models.py`) — Commit 1e24f79f changed dev/scripts/devctl/runtime/review_state_packet_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit 1e24f79f changed dev/scripts/devctl/runtime/reviewer_runtime_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/governance/push_state_models.py`) — Commit 5ed6e2fb changed dev/scripts/devctl/governance/push_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Commit 5ed6e2fb changed dev/scripts/devctl/runtime/remote_commit_pipeline_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_collaboration_models.py`) — Commit 5ed6e2fb changed dev/scripts/devctl/runtime/review_state_collaboration_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`dde973d5`** — Refresh external review snapshot for 24689590
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`24689590`** — Add dogfood governance recording and plan registry authority ordering
  - - Wire devctl dogfood --record-governance with stable signal_type=dogfood
  -   findings, default target-path resolution, and override knobs
  - - Put persisted PlanRegistry authority before rendered markdown projections
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`27b7826c`** — Refresh external review snapshot for a83b7f81
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`a83b7f81`** — Add dogfood coverage and bridge portability
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`e78905c2`** — Refresh external review snapshot for d6e474d5
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`d6e474d5`** — Refresh bridge.md projection from typed state for push
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`871812bb`** — Refresh review snapshot for governance-quality-sweep push
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`45376a16`** — Refresh external review snapshot for a19534a9
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`a19534a9`** — Fix active_target routing, projection parity, and dogfood session 6 findings
  - Routing fix:
  - - startup/session-resume/dashboard now promote MP377-P0 instead of
  -   stale review_channel continuity for active_target selection
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`ffafe4ff`** — Expand contract closure to internal types and wire governance-closure guard
  - Contract closure expansion:
  - - Added PlanPhase, PlanTask, FindingBacklog, SessionPacingState to
  -   FIELD_ROUTE_FAMILY_REGISTRY with expected consumer routes
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`9e75a66d`** — Refresh external review snapshot for 5a4236c1
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`5a4236c1`** — Wire FindingBacklog, connection pairs, and probe split advisor into startup loop
  - Three connection pairs landed (closes feedback loops):
  - - SessionPacingState.live_finding_count now populated from planning-ir
  -   (was always 0)
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`67afd4d5`** — Refresh external review snapshot for d0e5ac47
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`d0e5ac47` | MPs: MP-377** — Consolidate plan system: typed phases, plan ingestion, guard wiring, registry reduction
  - Architecture session deliverables:
  - - Consolidated MP-377 execution authority under ai_governance_platform.md
  -   with typed phases/tasks, reduced active owner docs to 3-5 live entries
  - plan: `dev/active/ai_governance_platform.md`
  - plan: `dev/active/platform_authority_loop.md`
  - plan: `dev/active/autonomous_governance_loop_v2.md`
  - plan: `dev/active/remote_commit_pipeline.md`
  - plan: `dev/active/PLAN_FORMAT.md`
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`c06a989a`** — Refresh external review snapshot for 1e24f79f
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`1e24f79f`** — Fix remote-control review-channel guard regressions and extract oversized modules
  - Codex session 2 guard-fix work:
  - - Fixed 4 targeted guards (parameter-count, facade-wrappers, dict-schema, code-shape)
  - - Fixed attention_revision_stale false positive in commit gate
  - evolution: Fact: the repo already had the right typed reducers, but the last-mile authority read was still fragmented. `startup-context`, `session-resume`, and `review-channel --action status|doctor` each exposed adjacent truths (…
- **`687c0478`** — Refresh external review snapshot for 4372e2cd
  - evolution: Fact: the architecture docs already said reviewer, implementer, and operator are role-first contracts over one shared backend, but the active execution plans still mixed that with live-proof language that read as `Codex…
- **`4372e2cd`** — Fix probe shims, event projection, and launch/rollover test regressions from role-neutral rename
  - Codex 6+7 self-review of the role-neutral rename (5ed6e2fb) found and fixed:
  - - Probe compatibility shims: 14 probe_*.py files used import * which dropped
  -   private helpers. Fixed to proper proxy-style re-exports preserving main()
  - evolution: Fact: the architecture docs already said reviewer, implementer, and operator are role-first contracts over one shared backend, but the active execution plans still mixed that with live-proof language that read as `Codex…
- **`f88de94b`** — Refresh external review snapshot for 5ed6e2fb
  - evolution: Fact: the architecture docs already said reviewer, implementer, and operator are role-first contracts over one shared backend, but the active execution plans still mixed that with live-proof language that read as `Codex…
- **`5ed6e2fb`** — Make review state role-neutral and bind push approval to worktree
  - evolution: Fact: the architecture docs already said reviewer, implementer, and operator are role-first contracts over one shared backend, but the active execution plans still mixed that with live-proof language that read as `Codex…
- **`a1c7ffe3`** — Refresh external review snapshot for 00e45380
  - evolution: Fact: the architecture docs already said reviewer, implementer, and operator are role-first contracts over one shared backend, but the active execution plans still mixed that with live-proof language that read as `Codex…
- **`00e45380`** — Checkpoint single-agent liveness and worker-lane portability
  - Project live single_agent_active authority, carry resolved worker worktree identity through launch/session/dashboard surfaces, and keep recovery assessment honest when the only blocker is checkpoint_required.
  - evolution: Fact: the architecture docs already said reviewer, implementer, and operator are role-first contracts over one shared backend, but the active execution plans still mixed that with live-proof language that read as `Codex…
- **`763be95d`** — Refresh external review snapshot for e8ccc7e7
  - evolution: Fact: the architecture docs already said reviewer, implementer, and operator are role-first contracts over one shared backend, but the active execution plans still mixed that with live-proof language that read as `Codex…
- **`e8ccc7e7`** — review_channel: remote-control attachment counts as live conductor in single_agent mode
  - In single_agent reviewer mode, attach_conductor_session_state() now reads
  - active remote-control attachments via load_remote_control_attachments() and
  - adds their providers to active_providers alongside conductor-session-file
  - evolution: Fact: the architecture docs already said reviewer, implementer, and operator are role-first contracts over one shared backend, but the active execution plans still mixed that with live-proof language that read as `Codex…
- **`70e2544f`** — docs(audit): dashboard-loop ticks 33-48 + liveness symmetry fix verification
  - Post-push dashboard observations from the Claude remote-control lane:
  - - Ticks 33-35: post-push steady-state verification (HEAD synced, worktree clean)
  - - Tick 36: detected new Codex session PID 90192 on ttys014
  - evolution: Fact: the architecture docs already said reviewer, implementer, and operator are role-first contracts over one shared backend, but the active execution plans still mixed that with live-proof language that read as `Codex…
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- architecture plan for the extracted AI-governance system under `MP-377`.
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b ev…
- 2026-04-11 remote-participant visibility follow-up in `MP-380..MP-387`
- the reopened MP-384/MP-387 F1 parity flake is now narrowed at the CLI edge
- Current 2026-04-05 reviewer-handoff closure inside that same lane: `MP-387`
- the `MP-381` field-route proof helper
- `MP-383` / `MP-381` packet-backed action-request and shared

## 8. Known gaps and open items

- open governance findings: 118

### Startup advisories
- checkpoint_before_continue: staged_index_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/vcs/push.py`): dogfood.code_shape_push_regression: 
- **governance_open** (`dev/scripts/devctl/runtime/dogfood_log.py`): dogfood_finding_id_instability: 
- **governance_open** (`dev/scripts/devctl/cli_parser/entrypoint.py`): dogfood_read_only_registration_missing: 
- **governance_open** (`dev/scripts/devctl/runtime/finding_backlog.py`): finding_backlog_writer_closure_broken: 
- **governance_open** (`dev/scripts/devctl/runtime/dogfood_log.py`): dogfood_governance_pipeline_missing: 
- **governance_open** (`bridge.md`): bridge_authority_conflict: 
- **governance_open** (`dev/scripts/devctl/platform/planning_ir_models.py`): plan_markdown_projection_missing: 
- **governance_open** (`dev/active/MASTER_PLAN.md`): plan_authority_gap: 

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-cf014a2276db` binds this file to HEAD `dde973d5387f`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
