# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `e2b3940fc65c` — Reclaim stale review-channel launch windows
- Tree hash: `a26e1222f4dc`
- Generation stamp: `snap-9a3d6b936e3e`
- Generated at (UTC): 2026-04-08T11:51:23Z
- Push decision: `await_checkpoint` — worktree_dirty
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 106 files, +10555/-3420
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
- HEAD SHA: `e2b3940fc65c1b8b2b0c5738c0180760fc5887c9`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-08T02:54:31-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: worktree_dirty
- push_eligible_now: False
- worktree_clean: False
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `published_remote` (post_push_bundle_failed)
- current_push_authorization: `push-auth-20260407T220000Z-hardening-plan` (valid=False)
- authorized_head_commit: `ee13a6c6337f395afa574e99a4234f2eaf45a161`
- approved_target_identity: `tree-receipt-20260407T220000Z:281dea21851063411d2c43c2b4621a1c2a1168b5`
- publication_backlog: recommended
- publication_guidance: 2 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `local_terminal`
- implementation_blocked: yes — reviewer_overdue

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **Master Plan (Active, Unified)**
- plan path: `dev/active/MASTER_PLAN.md`
- active MP scope: all active MP execution state
- advisory: `repair_reviewer_loop` — reviewer_overdue

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `e2b3940fc65c`

- commits: 25
- files changed: 106
- insertions: +10555
- deletions: -3420
- bundle classes touched: tooling, docs
- authority surfaces touched: 31 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `e2b3940` | Reclaim stale review-channel launch windows | 7 | +491/-109 | tooling |  |
| 2 | `9858988` | Fix review-channel session liveness fallback | 4 | +454/-101 | tooling |  |
| 3 | `483df5b` | Refresh external review snapshot for 7d7aa7c | 1 | +60/-67 | tooling |  |
| 4 | `7d7aa7c` | checkpoint: close review-channel authority convergence | 24 | +583/-149 | tooling |  |
| 5 | `1b55564` | Refresh external review snapshot for 8b77c5c | 1 | +53/-56 | tooling |  |
| 6 | `8b77c5c` | checkpoint: record dashboard observer audit findings | 3 | +225/-70 | tooling |  |
| 7 | `fba090f` | checkpoint: close push preflight bypass window | 9 | +129/-73 | tooling |  |
| 8 | `02ca820` | Refresh external review snapshot for fed1dec | 1 | +72/-79 | tooling |  |
| 9 | `fed1dec` | checkpoint: harden reviewer packet guards and runtime counts | 31 | +1230/-108 | tooling |  |
| 10 | `0a678e5` | Refresh external review snapshot for 47c7845 | 1 | +82/-75 | tooling |  |
| 11 | `47c7845` | checkpoint: truth-source hardening and review snapshot evid… | 36 | +2207/-1285 | tooling |  |
| 12 | `92a3358` | Refresh external review snapshot for 262bbad | 1 | +53/-57 | tooling |  |
| 13 | `262bbad` | docs: record review-channel revision drift fix | 4 | +99/-87 | tooling |  |
| 14 | `dec706e` | Refresh external review snapshot for 51dbf3c | 1 | +54/-60 | tooling |  |
| 15 | `51dbf3c` | checkpoint: capture residual review-channel test change | 2 | +63/-66 | tooling |  |
| 16 | `249bef9` | checkpoint: save current worktree state | 19 | +567/-95 | tooling |  |
| 17 | `6ade1a0` | Refresh external review snapshot for 4c3d9e9 | 1 | +63/-68 | tooling |  |
| 18 | `4c3d9e9` | checkpoint: add initial control-plane parity guard | 8 | +753/-64 | tooling |  |
| 19 | `d383dc2` | Refresh external review snapshot for a3628e3 | 1 | +62/-67 | tooling |  |
| 20 | `a3628e3` | Align push authorization with snapshot receipts | 14 | +373/-100 | tooling |  |
| 21 | `93b92d6` | Refresh external review snapshot for 0f2bf3e | 1 | +73/-88 | tooling |  |
| 22 | `0f2bf3e` | Add ReviewSnapshot receipt hook | 18 | +678/-201 | tooling |  |
| 23 | `922b376` | Accept snapshot-only review snapshot receipts | 10 | +186/-69 | tooling |  |
| 24 | `4d8a128` | Close packet-backed action request binding | 18 | +797/-168 | tooling |  |
| 25 | `ee13a6c` | Add architecture hardening plan for Codex review | 2 | +1148/-58 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +57/-6 |
| `bridge.md` | docs | +64/-63 |
| `dev/active/MASTER_PLAN.md` | tooling | +135/-22 |
| `dev/active/ai_governance_platform.md` | tooling | +76/-3 |
| `dev/active/platform_authority_loop.md` | tooling | +61/-1 |
| `dev/active/remote_commit_pipeline.md` | tooling | +65/-0 |
| `dev/active/remote_control_runtime.md` | tooling | +58/-18 |
| `dev/active/review_channel.md` | tooling | +20/-18 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1451/-1532 |
| `dev/audits/architecture_alignment.md` | tooling | +65/-0 |
| `dev/audits/architecture_hardening_plan.md` | tooling | +1241/-16 |
| `dev/config/devctl_repo_policy.json` | tooling | +1/-1 |
| `dev/config/git_hooks/post-commit-review-snapshot.sh` | tooling | +91/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +55/-6 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +286/-1 |
| `dev/scripts/README.md` | tooling | +76/-8 |
| `dev/scripts/checks/check_review_snapshot_freshness.py` | tooling | +61/-6 |
| `dev/scripts/checks/platform_contract_closure/field_routes_parity.py` | tooling | +318/-4 |
| `dev/scripts/checks/platform_contract_closure/field_routes_parity_compare.py` | tooling | +135/-0 |
| `dev/scripts/checks/platform_contract_closure/support.py` | tooling | +10/-0 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +34/-2 |
| `dev/scripts/devctl/commands/dashboard_builders.py` | tooling | +11/-0 |
| `dev/scripts/devctl/commands/dashboard_render/attention.py` | tooling | +3/-3 |
| `dev/scripts/devctl/commands/dashboard_render/helpers.py` | tooling | +18/-0 |
| `dev/scripts/devctl/commands/dashboard_render/markdown.py` | tooling | +4/-0 |
| `dev/scripts/devctl/commands/dashboard_render/terminal.py` | tooling | +14/-0 |
| `dev/scripts/devctl/commands/dashboard_typed_state.py` | tooling | +39/-2 |
| `dev/scripts/devctl/commands/governance/install_git_hooks.py` | tooling | +149/-90 |
| `dev/scripts/devctl/commands/governance/review_snapshot.py` | tooling | +211/-6 |
| `dev/scripts/devctl/commands/mobile_status.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/phone_status.py` | tooling | +26/-4 |
| `dev/scripts/devctl/commands/review_channel/_bridge_poll.py` | tooling | +43/-8 |
| `dev/scripts/devctl/commands/review_channel/_render_bridge.py` | tooling | +5/-0 |
| `dev/scripts/devctl/commands/review_channel/bridge_action_support.py` | tooling | +1/-27 |
| `dev/scripts/devctl/commands/review_channel/bridge_render.py` | tooling | +33/-0 |
| `dev/scripts/devctl/commands/review_channel/bridge_support.py` | tooling | +7/-0 |
| `dev/scripts/devctl/commands/review_channel/launch_conflicts.py` | tooling | +89/-0 |
| `dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor.py` | tooling | +5/-5 |
| `dev/scripts/devctl/commands/vcs/push_flow.py` | tooling | +4/-5 |
| _66 more files trimmed_ | | |

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
| `ActionResult` | `governance_runtime` | `dev.scripts.devctl.runtime.action_contracts:ActionResult` | status, reason, artifact_paths |
| `ArtifactStore` | `governance_runtime` | `dev.scripts.devctl.runtime.action_contracts:ArtifactStore` | root, managed_kinds, retention_policy |
| `AutoModeState` | `governance_runtime` | `dev.scripts.devctl.runtime.auto_mode:AutoModeState` | phase, next_transition |
| `CallerAuthorityPolicy` | `governance_runtime` | `n/a` | caller_id, allowed_actions, approval_required_actions |
| `CheckResult` | `governance_runtime` | `dev.scripts.devctl.runtime.check_result_models:CheckResult` | success, total, failed |
| `ControlPlaneReadModel` | `governance_runtime` | `dev.scripts.devctl.runtime.control_plane_read_model:ControlPlaneReadModel` | push_eligible, top_blocker, resolved_phase |
| `ControlState` | `governance_runtime` | `dev.scripts.devctl.runtime.control_state:ControlState` | approvals, active_runs, review_bridge |
| `DecisionPacket` | `governance_runtime` | `dev.scripts.devctl.runtime.finding_contracts:DecisionPacketRecord` | decision_mode, rule_summary, validation_plan |
| `FailurePacket` | `governance_runtime` | `dev.scripts.devctl.runtime.failure_packet:FailurePacket` | runner, status, primary_test_id |
| `Finding` | `governance_runtime` | `dev.scripts.devctl.runtime.finding_contracts:FindingRecord` | check_id, severity, ai_instruction |
| `LocalServiceEndpoint` | `governance_runtime` | `n/a` | service_id, discovery_fields, health_signals |
| `ProviderAdapter` | `governance_adapters` | `n/a` | provider_id, capabilities, launch_mode |
| `PushAuthorizationRecord` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:PushAuthorizationRecord` | authorization_id, authorized_head_sha, approval_mode |
| `RemoteCommitPipelineContract` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:RemoteCommitPipelineContract` | snapshot_id, state, approval_state |
| `RepoPack` | `repo_packs` | `n/a` | pack_id, policy_path, workflow_profiles |
| `ReviewCandidateRecord` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewCandidateRecord` | candidate_id, artifact_kind, valid |
| `ReviewState` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewState` | snapshot_id, bridge, current_session |
| `ReviewerRuntimeContract` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewerRuntimeContract` | reviewer_mode, reviewer_freshness, publish_clear |
| `RunRecord` | `governance_runtime` | `dev.scripts.devctl.runtime.action_contracts:RunRecord` | run_id, status, artifact_paths |
| `SessionCachePacket` | `governance_commands` | `dev.scripts.devctl.commands.governance.session_resume_support:SessionCachePacket` | last_reviewed_sha, advisory_action, blockers |
| `TypedAction` | `governance_runtime` | `dev.scripts.devctl.runtime.action_contracts:TypedAction` | action_id, repo_pack_id, parameters |
| `WorkflowAdapter` | `governance_adapters` | `n/a` | adapter_id, transport, allowed_actions |

### Key documents

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`

## 6. Reviewer hints — please verify

### Targeted hints

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
- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/check_review_snapshot_freshness.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_check_review_snapshot_freshness.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Commit 47c7845 changed dev/scripts/devctl/review_channel/reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_snapshot_models.py`) — Commit 47c7845 changed dev/scripts/devctl/runtime/review_snapshot_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/review_channel/test_ack_contract.py`) — Commit 47c7845 changed dev/scripts/devctl/tests/review_channel/test_ack_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit 4d8a128 changed dev/scripts/devctl/review_channel/packet_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`e2b3940`** — Reclaim stale review-channel launch windows
  - evolution: The live review-channel runtime exposed one more precedence bug after typed Claude ACK state landed. Once `Claude Status` / `Claude Ack` were current again, bridge-backed `status`, `doctor`, and `startup-context` could …
- **`9858988`** — Fix review-channel session liveness fallback
  - evolution: The live review-channel runtime exposed one more precedence bug after typed Claude ACK state landed. Once `Claude Status` / `Claude Ack` were current again, bridge-backed `status`, `doctor`, and `startup-context` could …
- **`483df5b`** — Refresh external review snapshot for 7d7aa7c
  - evolution: The live review-channel runtime exposed one more precedence bug after typed Claude ACK state landed. Once `Claude Status` / `Claude Ack` were current again, bridge-backed `status`, `doctor`, and `startup-context` could …
- **`7d7aa7c`** — checkpoint: close review-channel authority convergence
- **`1b55564`** — Refresh external review snapshot for 8b77c5c
- **`8b77c5c`** — checkpoint: record dashboard observer audit findings
- **`fba090f`** — checkpoint: close push preflight bypass window
- **`02ca820`** — Refresh external review snapshot for fed1dec
- **`fed1dec`** — checkpoint: harden reviewer packet guards and runtime counts
- **`0a678e5`** — Refresh external review snapshot for 47c7845
- **`47c7845`** — checkpoint: truth-source hardening and review snapshot evidence
- **`92a3358`** — Refresh external review snapshot for 262bbad
- **`262bbad`** — docs: record review-channel revision drift fix
- **`dec706e`** — Refresh external review snapshot for 51dbf3c
- **`51dbf3c`** — checkpoint: capture residual review-channel test change
- **`249bef9`** — checkpoint: save current worktree state
- **`6ade1a0`** — Refresh external review snapshot for 4c3d9e9
- **`4c3d9e9`** — checkpoint: add initial control-plane parity guard
- **`d383dc2`** — Refresh external review snapshot for a3628e3
- **`a3628e3`** — Align push authorization with snapshot receipts
- **`93b92d6`** — Refresh external review snapshot for 0f2bf3e
- **`0f2bf3e`** — Add ReviewSnapshot receipt hook
- **`922b376`** — Accept snapshot-only review snapshot receipts
- **`4d8a128`** — Close packet-backed action request binding
- **`ee13a6c`** — Add architecture hardening plan for Codex review
  - Drafts the next-session hardening plan for the ReviewSnapshot +
  - install-git-hooks subsystem at dev/audits/architecture_hardening_plan.md.
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
- repair_reviewer_loop: reviewer_overdue

### Stale warnings
- Cut a checkpoint before doing anything else.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-9a3d6b936e3e` binds this file to HEAD `e2b3940fc65c`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
