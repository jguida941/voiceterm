# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `64ad27ef9dad` — Refresh external review snapshot for 08859553 + sync bridge.md from typed review-state
- Tree hash: `b92605c758b6`
- Generation stamp: `snap-5ab2be626df5`
- Generated at (UTC): 2026-04-15T00:08:32Z
- Push decision: `await_checkpoint` — worktree_dirty
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 183 files, +14007/-3375
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
- HEAD SHA: `64ad27ef9dad232177d3d8794436d59540370c10`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-14T20:00:13-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: worktree_dirty
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 0
- unstaged_path_count: 1
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `post_push_green` (push_completed)
- current_push_authorization: `push-auth-20260414T235920457061Z` (valid=True)
- authorized_head_commit: `64ad27ef9dad232177d3d8794436d59540370c10`
- approved_target_identity: `tree-receipt-20260414T235920457061Z:b92605c758b672b41f560328dac29e419004012c`
- publication_backlog: none

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
- advisory: `checkpoint_allowed` — worktree_dirty_within_budget

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `64ad27ef9dad`

- commits: 25
- files changed: 183
- insertions: +14007
- deletions: -3375
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 17 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `64ad27ef` | Refresh external review snapshot for 08859553 + sync bridge… | 1 | +64/-93 | tooling |  |
| 2 | `08859553` | Extract canonical operator_interaction_mode reducer to oper… | 7 | +343/-189 | tooling |  |
| 3 | `951b86aa` | Propagate attachment-overrides-local_terminal promotion to… | 3 | +69/-19 | tooling |  |
| 4 | `dba730f7` | Wire reviewer-wake path + fix dashboard render keying + pen… | 14 | +769/-12 | tooling |  |
| 5 | `493b9d03` | Fix attachment override of operator_interaction_mode; rever… | 4 | +131/-60 | tooling |  |
| 6 | `60a8d1bd` | Refresh external review snapshot for 686a1283 | 1 | +61/-69 | tooling |  |
| 7 | `686a1283` | Align authority parity and review packet handling | 15 | +623/-157 | tooling | Parser / ANSI boundary |
| 8 | `6361080a` | Fix review-channel watch follow liveness | 16 | +1255/-183 | tooling |  |
| 9 | `3d78ef9f` | Refresh external review snapshot for 6fdde964 | 1 | +60/-69 | tooling |  |
| 10 | `6fdde964` | Align authority snapshots and dashboard headers | 28 | +996/-241 | tooling |  |
| 11 | `455a2c64` | Add authority snapshot runtime contract | 34 | +1779/-635 | tooling |  |
| 12 | `dde973d5` | Refresh external review snapshot for 24689590 | 1 | +64/-72 | tooling |  |
| 13 | `24689590` | Add dogfood governance recording and plan registry authorit… | 17 | +901/-113 | tooling |  |
| 14 | `27b7826c` | Refresh external review snapshot for a83b7f81 | 1 | +83/-84 | tooling |  |
| 15 | `a83b7f81` | Add dogfood coverage and bridge portability | 47 | +1760/-224 | tooling |  |
| 16 | `e78905c2` | Refresh external review snapshot for d6e474d5 | 1 | +47/-51 | tooling |  |
| 17 | `d6e474d5` | Refresh bridge.md projection from typed state for push | 2 | +69/-172 | docs |  |
| 18 | `871812bb` | Refresh review snapshot for governance-quality-sweep push | 1 | +55/-59 | tooling |  |
| 19 | `45376a16` | Refresh external review snapshot for a19534a9 | 1 | +63/-65 | tooling |  |
| 20 | `a19534a9` | Fix active_target routing, projection parity, and dogfood s… | 31 | +1070/-143 | tooling |  |
| 21 | `ffafe4ff` | Expand contract closure to internal types and wire governan… | 13 | +584/-66 | tooling |  |
| 22 | `9e75a66d` | Refresh external review snapshot for 5a4236c1 | 1 | +59/-63 | tooling |  |
| 23 | `5a4236c1` | Wire FindingBacklog, connection pairs, and probe split advi… | 42 | +1803/-224 | tooling | Parser / ANSI boundary |
| 24 | `67afd4d5` | Refresh external review snapshot for d0e5ac47 | 1 | +80/-83 | tooling |  |
| 25 | `d0e5ac47` | Consolidate plan system: typed phases, plan ingestion, guar… | 29 | +1219/-229 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +28/-8 |
| `bridge.md` | docs | +70/-179 |
| `dev/active/INDEX.md` | tooling | +35/-49 |
| `dev/active/MASTER_PLAN.md` | tooling | +101/-35 |
| `dev/active/ai_governance_platform.md` | tooling | +455/-39 |
| `dev/active/platform_authority_loop.md` | tooling | +34/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1459/-1511 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +32/-1 |
| `dev/config/quality_presets/portable_python.json` | tooling | +3/-1 |
| `dev/config/quality_presets/portable_rust.json` | tooling | +1/-0 |
| `dev/config/templates/portable_governance_finding_review.schema.json` | tooling | +1/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +65/-6 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +300/-2 |
| `dev/scripts/README.md` | tooling | +51/-27 |
| `dev/scripts/checks/active_plan/contract.py` | tooling | +0/-16 |
| `dev/scripts/checks/active_plan/typed_phase_contract.py` | tooling | +104/-0 |
| `dev/scripts/checks/check_active_plan_sync.py` | tooling | +25/-54 |
| `dev/scripts/checks/code_shape/code_shape_policy.py` | tooling | +0/-6 |
| `dev/scripts/checks/code_shape_support/probe_split_advisor.py` | tooling | +342/-0 |
| `dev/scripts/checks/governance_closure/command.py` | tooling | +11/-0 |
| `dev/scripts/checks/governance_closure/contract_connectivity.py` | tooling | +91/-0 |
| `dev/scripts/checks/platform_contract_closure/field_routes.py` | tooling | +27/-0 |
| `dev/scripts/checks/platform_contract_closure/field_routes_planning.py` | tooling | +165/-0 |
| `dev/scripts/checks/probe_split_advisor.py` | tooling | +13/-0 |
| `dev/scripts/checks/review_channel_bridge/report.py` | tooling | +86/-13 |
| `dev/scripts/devctl/cli.py` | tooling | +5/-0 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +3/-1 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +168/-153 |
| `dev/scripts/devctl/commands/dashboard_builders.py` | tooling | +112/-9 |
| `dev/scripts/devctl/commands/dashboard_header.py` | tooling | +69/-0 |
| `dev/scripts/devctl/commands/dashboard_health.py` | tooling | +110/-0 |
| `dev/scripts/devctl/commands/dashboard_render/markdown.py` | tooling | +6/-1 |
| `dev/scripts/devctl/commands/dashboard_render/terminal.py` | tooling | +6/-1 |
| `dev/scripts/devctl/commands/governance/common.py` | tooling | +6/-1 |
| `dev/scripts/devctl/commands/governance/review.py` | tooling | +6/-4 |
| `dev/scripts/devctl/commands/governance/session_resume.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_authority_payload.py` | tooling | +85/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +154/-132 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +34/-18 |
| `dev/scripts/devctl/commands/governance/startup_context_render.py` | tooling | +2/-0 |
| _143 more files trimmed_ | | |

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_receipt.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_receipt.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_heading_aliases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_sanitize.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_validation_stall.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_parse.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit 455a2c64 changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit 455a2c64 changed dev/scripts/devctl/runtime/review_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit 455a2c64 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/ack_contract.py`) — Commit a83b7f81 changed dev/scripts/devctl/review_channel/ack_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/dogfood_models.py`) — Commit a83b7f81 changed dev/scripts/devctl/runtime/dogfood_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Commit a83b7f81 changed dev/scripts/devctl/runtime/project_governance_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/review_channel/test_ack_contract.py`) — Commit a83b7f81 changed dev/scripts/devctl/tests/review_channel/test_ack_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/planning_ir_models.py`) — Commit 5a4236c1 changed dev/scripts/devctl/platform/planning_ir_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_intake_models.py`) — Commit 5a4236c1 changed dev/scripts/devctl/runtime/work_intake_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/checks/active_plan/typed_phase_contract.py`) — Commit d0e5ac47 changed dev/scripts/checks/active_plan/typed_phase_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/test_active_plan_contract.py`) — Commit d0e5ac47 changed dev/scripts/devctl/tests/test_active_plan_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`64ad27ef`** — Refresh external review snapshot for 08859553 + sync bridge.md from typed review-state
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`08859553`** — Extract canonical operator_interaction_mode reducer to operator_context + delegate 3 launcher sites (closes rev_pkt_0463)
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`951b86aa`** — Propagate attachment-overrides-local_terminal promotion to launcher/ensure-follow/supervisor (rev_pkt_0459)
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`dba730f7`** — Wire reviewer-wake path + fix dashboard render keying + pending_action_requests filtering
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`493b9d03`** — Fix attachment override of operator_interaction_mode; revert policy default (closes rev_pkt_0448)
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`60a8d1bd`** — Refresh external review snapshot for 686a1283
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`686a1283`** — Align authority parity and review packet handling
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`6361080a`** — Fix review-channel watch follow liveness
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`3d78ef9f`** — Refresh external review snapshot for 6fdde964
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`6fdde964`** — Align authority snapshots and dashboard headers
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`455a2c64`** — Add authority snapshot runtime contract
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`dde973d5`** — Refresh external review snapshot for 24689590
- **`24689590`** — Add dogfood governance recording and plan registry authority ordering
  - - Wire devctl dogfood --record-governance with stable signal_type=dogfood
  -   findings, default target-path resolution, and override knobs
  - - Put persisted PlanRegistry authority before rendered markdown projections
- **`27b7826c`** — Refresh external review snapshot for a83b7f81
- **`a83b7f81`** — Add dogfood coverage and bridge portability
- **`e78905c2`** — Refresh external review snapshot for d6e474d5
- **`d6e474d5`** — Refresh bridge.md projection from typed state for push
- **`871812bb`** — Refresh review snapshot for governance-quality-sweep push
- **`45376a16`** — Refresh external review snapshot for a19534a9
- **`a19534a9`** — Fix active_target routing, projection parity, and dogfood session 6 findings
  - Routing fix:
  - - startup/session-resume/dashboard now promote MP377-P0 instead of
  -   stale review_channel continuity for active_target selection
- **`ffafe4ff`** — Expand contract closure to internal types and wire governance-closure guard
  - Contract closure expansion:
  - - Added PlanPhase, PlanTask, FindingBacklog, SessionPacingState to
  -   FIELD_ROUTE_FAMILY_REGISTRY with expected consumer routes
- **`9e75a66d`** — Refresh external review snapshot for 5a4236c1
- **`5a4236c1`** — Wire FindingBacklog, connection pairs, and probe split advisor into startup loop
  - Three connection pairs landed (closes feedback loops):
  - - SessionPacingState.live_finding_count now populated from planning-ir
  -   (was always 0)
- **`67afd4d5`** — Refresh external review snapshot for d0e5ac47
- **`d0e5ac47` | MPs: MP-377** — Consolidate plan system: typed phases, plan ingestion, guard wiring, registry reduction
  - Architecture session deliverables:
  - - Consolidated MP-377 execution authority under ai_governance_platform.md
  -   with typed phases/tasks, reduced active owner docs to 3-5 live entries
  - plan: `dev/active/ai_governance_platform.md`
  - plan: `dev/active/platform_authority_loop.md`
  - plan: `dev/active/autonomous_governance_loop_v2.md`
  - plan: `dev/active/remote_commit_pipeline.md`
  - plan: `dev/active/PLAN_FORMAT.md`
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
- checkpoint_allowed: worktree_dirty_within_budget

### Stale warnings
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-5ab2be626df5` binds this file to HEAD `64ad27ef9dad`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
