# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `e31232a48acb` — Refresh external review snapshot for 2602f22
- Tree hash: `c9d83712d6bd`
- Generation stamp: `snap-65a854377b35`
- Generated at (UTC): 2026-04-08T18:13:14Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 81 files, +9546/-1617
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
- HEAD SHA: `e31232a48acb0b4ad1b860696d39df39ffa8c264`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-08T14:12:41-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260407T220000Z-hardening-plan` (valid=False)
- authorized_head_commit: `ee13a6c6337f395afa574e99a4234f2eaf45a161`
- approved_target_identity: `tree-receipt-20260407T220000Z:281dea21851063411d2c43c2b4621a1c2a1168b5`
- publication_backlog: urgent
- publication_guidance: 5 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `remote_control`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **Master Plan (Active, Unified)**
- plan path: `dev/active/MASTER_PLAN.md`
- active MP scope: all active MP execution state
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `e31232a48acb`

- commits: 24
- files changed: 81
- insertions: +9546
- deletions: -1617
- bundle classes touched: tooling, docs
- authority surfaces touched: 8 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `e31232a` | Refresh external review snapshot for 2602f22 | 1 | +56/-53 | tooling |  |
| 2 | `2602f22` | Add CHANGELOG entry for LIVE_RUN.md + log Q17 router misrou… | 3 | +113/-58 | tooling |  |
| 3 | `f58c69f` | Refresh external review snapshot for b6af0d3 | 1 | +44/-45 | tooling |  |
| 4 | `b6af0d3` | Refresh external review snapshot for 69719d3 | 1 | +55/-51 | tooling |  |
| 5 | `69719d3` | Add LIVE_RUN.md — running trial log of every issue found th… | 2 | +736/-50 | tooling |  |
| 6 | `e215663` | Refresh external review snapshot for f177aae | 1 | +69/-65 | tooling |  |
| 7 | `f177aae` | Q4 tactical fix: flip BridgeConfig.operator_interaction_mod… | 2 | +52/-46 | tooling |  |
| 8 | `ca59eaf` | Hotfix: defensive pending_approvals tolerates dict-shaped p… | 2 | +74/-55 | tooling |  |
| 9 | `f567eb1` | Refresh external review snapshot for d58eecb | 1 | +52/-49 | tooling |  |
| 10 | `d58eecb` | Expand Q4 root cause with file:line breadcrumbs for Codex f… | 2 | +51/-51 | docs |  |
| 11 | `00640d0` | Refresh external review snapshot for 6546c09 | 1 | +62/-64 | tooling |  |
| 12 | `6546c09` | Add Q4 remote_control interaction_mode classification bug t… | 2 | +45/-43 | docs |  |
| 13 | `5fe9148` | Refresh external review snapshot for 84f9140 | 1 | +64/-81 | tooling |  |
| 14 | `84f9140` | Clear stale path overrides and refresh bridge checkpoint | 3 | +83/-94 | tooling |  |
| 15 | `d2e648f` | Refresh external review snapshot for dff02c8 | 1 | +79/-77 | tooling |  |
| 16 | `dff02c8` | Converge coordination control-plane read model | 38 | +1496/-112 | tooling |  |
| 17 | `fb212c0` | Refresh review bridge checkpoint state | 2 | +54/-51 | docs |  |
| 18 | `fb46a8a` | Refresh external review snapshot for 70290f0 | 1 | +67/-66 | tooling |  |
| 19 | `70290f0` | Add coordination posture reducers | 19 | +2131/-62 | tooling |  |
| 20 | `36addcb` | Refresh external review snapshot for 05bc3c5 | 1 | +65/-65 | tooling |  |
| 21 | `05bc3c5` | Add PlanningIRSnapshot platform reducer | 14 | +1419/-66 | tooling |  |
| 22 | `941781e` | Refresh external review snapshot for b681930 | 1 | +62/-64 | tooling |  |
| 23 | `b681930` | Checkpoint startup coordination and session hint fixes | 14 | +344/-108 | tooling |  |
| 24 | `ca07a33` | Add typed startup coordination state | 26 | +2273/-141 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +28/-0 |
| `bridge.md` | docs | +97/-100 |
| `dev/CHANGELOG.md` | docs | +26/-0 |
| `dev/active/MASTER_PLAN.md` | tooling | +69/-11 |
| `dev/active/ai_governance_platform.md` | tooling | +103/-11 |
| `dev/active/platform_authority_loop.md` | tooling | +73/-0 |
| `dev/active/remote_control_runtime.md` | tooling | +31/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +716/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1382/-1360 |
| `dev/guides/DEVELOPMENT.md` | docs | +46/-6 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +180/-0 |
| `dev/scripts/README.md` | tooling | +50/-10 |
| `dev/scripts/checks/code_shape/code_shape_policy.py` | tooling | +0/-12 |
| `dev/scripts/checks/startup_authority_contract/command.py` | tooling | +8/-0 |
| `dev/scripts/checks/startup_authority_contract/runtime_checks.py` | tooling | +59/-0 |
| `dev/scripts/devctl/commands/check/__init__.py` | tooling | +2/-2 |
| `dev/scripts/devctl/commands/check/phase_support.py` | tooling | +2/-1 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +41/-10 |
| `dev/scripts/devctl/commands/dashboard_render/attention.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/dashboard_render/markdown.py` | tooling | +31/-0 |
| `dev/scripts/devctl/commands/dashboard_render/terminal.py` | tooling | +16/-0 |
| `dev/scripts/devctl/commands/dashboard_typed_state.py` | tooling | +10/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_render.py` | tooling | +70/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +67/-0 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +61/-0 |
| `dev/scripts/devctl/commands/governance/startup_context_render.py` | tooling | +112/-0 |
| `dev/scripts/devctl/commands/review_channel/doctor_support.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_git.py` | tooling | +9/-22 |
| `dev/scripts/devctl/platform/coordination_snapshot.py` | tooling | +223/-10 |
| `dev/scripts/devctl/platform/coordination_snapshot_models.py` | tooling | +210/-0 |
| `dev/scripts/devctl/platform/coordination_snapshot_support.py` | tooling | +296/-0 |
| `dev/scripts/devctl/platform/coordination_topology.py` | tooling | +128/-0 |
| `dev/scripts/devctl/platform/coordination_topology_models.py` | tooling | +115/-0 |
| `dev/scripts/devctl/platform/coordination_topology_support.py` | tooling | +339/-0 |
| `dev/scripts/devctl/platform/planning_ir.py` | tooling | +67/-0 |
| `dev/scripts/devctl/platform/planning_ir_findings.py` | tooling | +110/-0 |
| `dev/scripts/devctl/platform/planning_ir_models.py` | tooling | +146/-0 |
| `dev/scripts/devctl/platform/planning_ir_reduction.py` | tooling | +334/-0 |
| `dev/scripts/devctl/platform/planning_ir_sources.py` | tooling | +272/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_review.py` | tooling | +5/-0 |
| _41 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_checks.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_git.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Commit f177aae changed dev/scripts/devctl/runtime/project_governance_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit ca59eaf changed dev/scripts/devctl/runtime/review_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/coordination_snapshot_models.py`) — Commit dff02c8 changed dev/scripts/devctl/platform/coordination_snapshot_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit dff02c8 changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/coordination_topology_models.py`) — Commit 70290f0 changed dev/scripts/devctl/platform/coordination_topology_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/planning_ir_models.py`) — Commit 05bc3c5 changed dev/scripts/devctl/platform/planning_ir_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_collaboration_models.py`) — Commit ca07a33 changed dev/scripts/devctl/runtime/review_state_collaboration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_intake_models.py`) — Commit ca07a33 changed dev/scripts/devctl/runtime/work_intake_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Commit ca07a33 changed dev/scripts/devctl/tests/checks/test_startup_authority_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`e31232a`** — Refresh external review snapshot for 2602f22
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`2602f22`** — Add CHANGELOG entry for LIVE_RUN.md + log Q17 router misrouting
  - - dev/CHANGELOG.md: Added section names LIVE_RUN.md; Fixed section names
  -   the three code landings (Q4 default, Q11 hotfix, stale overrides).
  -   This unblocks the Q17 docs-check --user-facing preflight that misrouted
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`f58c69f`** — Refresh external review snapshot for b6af0d3
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`b6af0d3`** — Refresh external review snapshot for 69719d3
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`69719d3`** — Add LIVE_RUN.md — running trial log of every issue found this session
  - Operator directive from remote_control session: log everything. Every
  - finding, every working component, every unknown or suspected blind spot.
  - Single authoritative file that Codex can pull from during review.
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`e215663`** — Refresh external review snapshot for f177aae
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`f177aae`** — Q4 tactical fix: flip BridgeConfig.operator_interaction_mode default to remote_control
  - One-line tactical unblock matching Q4 (rev_pkt_0129) fix recommendation #4.
  - This flips the hardcoded dataclass default in
  - project_governance_contract.py:209 from "local_terminal" to "remote_control"
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`ca59eaf`** — Hotfix: defensive pending_approvals tolerates dict-shaped packets
  - Q11 surfaced during this session: after posting 10 typed finding
  - packets (Q1-Q10, rev_pkt_0120..rev_pkt_0129) via review-channel post,
  - the next review-channel --action status call crashed with:
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`f567eb1`** — Refresh external review snapshot for d58eecb
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`d58eecb`** — Expand Q4 root cause with file:line breadcrumbs for Codex fix
  - Replaces the Q4 classification bug description with the full root
  - cause breadcrumb chain Codex needs to implement the fix:
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`00640d0`** — Refresh external review snapshot for 6546c09
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`6546c09`** — Add Q4 remote_control interaction_mode classification bug to bridge
  - Q4 (CLASSIFICATION): `startup-context.interaction_mode=local_terminal`
  - while this session is actually `remote_control` (operator on phone;
  - bridge "Remote Session Protocol" section declares it explicitly). The
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`5fe9148`** — Refresh external review snapshot for 84f9140
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`84f9140`** — Clear stale path overrides and refresh bridge checkpoint
  - Bundles two mutually dependent changes: `devctl commit` cannot land
  - either one in isolation because its pre-commit guard
  - (`startup-authority-contract-guard`) counts staged files as
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
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
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-65a854377b35` binds this file to HEAD `e31232a48acb`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
