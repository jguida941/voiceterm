# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `92a33583320c` — Refresh external review snapshot for 262bbad
- Tree hash: `4ef58e7c47de`
- Generation stamp: `snap-2c069daaae33`
- Generated at (UTC): 2026-04-08T01:16:27Z
- Push decision: `await_checkpoint` — dirty_path_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 114 files, +13014/-2681
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
- HEAD SHA: `92a33583320cd523bc5ba2acbbda226faeeddd60`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-07T20:25:20-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: dirty_path_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `published_remote` (post_push_bundle_failed)
- current_push_authorization: `push-auth-20260407T220000Z-hardening-plan` (valid=False)
- authorized_head_commit: `ee13a6c6337f395afa574e99a4234f2eaf45a161`
- approved_target_identity: `tree-receipt-20260407T220000Z:281dea21851063411d2c43c2b4621a1c2a1168b5`
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
- active plan: **Review Channel + Shared Screen Plan**
- plan path: `dev/active/review_channel.md`
- active MP scope: `MP-355`
- advisory: `checkpoint_before_continue` — dirty_path_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `92a33583320c`

- commits: 25
- files changed: 114
- insertions: +13014
- deletions: -2681
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 27 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `92a3358` | Refresh external review snapshot for 262bbad | 1 | +53/-57 | tooling |  |
| 2 | `262bbad` | docs: record review-channel revision drift fix | 4 | +99/-87 | tooling |  |
| 3 | `dec706e` | Refresh external review snapshot for 51dbf3c | 1 | +54/-60 | tooling |  |
| 4 | `51dbf3c` | checkpoint: capture residual review-channel test change | 2 | +63/-66 | tooling |  |
| 5 | `249bef9` | checkpoint: save current worktree state | 19 | +567/-95 | tooling |  |
| 6 | `6ade1a0` | Refresh external review snapshot for 4c3d9e9 | 1 | +63/-68 | tooling |  |
| 7 | `4c3d9e9` | checkpoint: add initial control-plane parity guard | 8 | +753/-64 | tooling |  |
| 8 | `d383dc2` | Refresh external review snapshot for a3628e3 | 1 | +62/-67 | tooling |  |
| 9 | `a3628e3` | Align push authorization with snapshot receipts | 14 | +373/-100 | tooling |  |
| 10 | `93b92d6` | Refresh external review snapshot for 0f2bf3e | 1 | +73/-88 | tooling |  |
| 11 | `0f2bf3e` | Add ReviewSnapshot receipt hook | 18 | +678/-201 | tooling |  |
| 12 | `922b376` | Accept snapshot-only review snapshot receipts | 10 | +186/-69 | tooling |  |
| 13 | `4d8a128` | Close packet-backed action request binding | 18 | +797/-168 | tooling |  |
| 14 | `ee13a6c` | Add architecture hardening plan for Codex review | 2 | +1148/-58 | tooling |  |
| 15 | `e21d8e8` | Close MP-377 typed-continuity tranche (Legs 1+2+3 follow-up… | 12 | +872/-68 | tooling |  |
| 16 | `f9388da` | Add install-git-hooks command for portable pre-commit snaps… | 5 | +704/-50 | tooling |  |
| 17 | `d155b02` | Refresh REVIEW_SNAPSHOT to track branch tip at 60bcd68 | 1 | +112/-108 | tooling |  |
| 18 | `60bcd68` | Open policy-gated skip-preflight bypass window for ReviewSn… | 2 | +100/-1 | tooling |  |
| 19 | `c98d471` | Restore script_catalog entries stripped during previous edit | 1 | +14/-0 | tooling |  |
| 20 | `4b45f9a` | Register python_typed_seams in script_catalog | 1 | +1/-0 | tooling |  |
| 21 | `5978dce` | Add ReviewSnapshot external-review surface via pre-commit r… | 33 | +4198/-680 | tooling |  |
| 22 | `b6be213` | Land reviewer-supervisor restart-policy follow-up checkpoint | 21 | +549/-98 | tooling |  |
| 23 | `244ae83` | Land MP-382 + MP-387 launch-authority closure (F21/F21a/F23… | 30 | +1306/-333 | tooling | Parser / ANSI boundary |
| 24 | `fefa621` | Checkpoint reviewer bridge state: F21/F21a/F23/F24 launch-a… | 1 | +39/-92 | docs |  |
| 25 | `846987c` | Update test_launch_sessions_if_requested_headless_requires_… | 1 | +150/-3 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-1 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +2/-2 |
| `AGENTS.md` | docs | +38/-6 |
| `AUDIT_STATUS.md` | docs | +0/-474 |
| `bridge.md` | docs | +105/-157 |
| `dev/active/MASTER_PLAN.md` | tooling | +141/-7 |
| `dev/active/ai_governance_platform.md` | tooling | +97/-4 |
| `dev/active/platform_authority_loop.md` | tooling | +154/-8 |
| `dev/active/portable_code_governance.md` | tooling | +40/-8 |
| `dev/active/remote_commit_pipeline.md` | tooling | +164/-16 |
| `dev/active/remote_control_runtime.md` | tooling | +145/-21 |
| `dev/active/review_channel.md` | tooling | +1/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1506/-1116 |
| `dev/audits/architecture_hardening_plan.md` | tooling | +1140/-16 |
| `dev/audits/push_override_receipts/20260407T173000Z_review_snapshot_landing.md` | tooling | +99/-0 |
| `dev/config/devctl_repo_policy.json` | tooling | +1/-1 |
| `dev/config/git_hooks/post-commit-review-snapshot.sh` | tooling | +91/-0 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +97/-0 |
| `dev/config/launchd/review_channel_publisher_service.py` | tooling | +4/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +43/-7 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +249/-3 |
| `dev/scripts/README.md` | tooling | +58/-11 |
| `dev/scripts/checks/check_audit_status_sync.py` | tooling | +0/-112 |
| `dev/scripts/checks/check_review_snapshot_freshness.py` | tooling | +264/-6 |
| `dev/scripts/checks/platform_contract_closure/field_routes_parity.py` | tooling | +318/-4 |
| `dev/scripts/checks/platform_contract_closure/field_routes_parity_compare.py` | tooling | +135/-0 |
| `dev/scripts/checks/platform_contract_closure/support.py` | tooling | +10/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-1 |
| `dev/scripts/devctl/cli.py` | tooling | +6/-0 |
| `dev/scripts/devctl/commands/governance/install_git_hooks.py` | tooling | +480/-90 |
| `dev/scripts/devctl/commands/governance/review_snapshot.py` | tooling | +391/-6 |
| `dev/scripts/devctl/commands/governance/session_resume.py` | tooling | +25/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +24/-1 |
| `dev/scripts/devctl/commands/mobile_status.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/phone_status.py` | tooling | +26/-4 |
| `dev/scripts/devctl/commands/review_channel/_bridge_poll.py` | tooling | +43/-8 |
| `dev/scripts/devctl/commands/review_channel/_ensure_helpers.py` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/review_channel/_ensure_supervisor.py` | tooling | +16/-0 |
| `dev/scripts/devctl/commands/review_channel/_follow_runtime.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/review_channel/_publisher.py` | tooling | +0/-68 |
| _74 more files trimmed_ | | |

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

- **risk**: Parser / ANSI boundary — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/check_review_snapshot_freshness.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_render.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_check_review_snapshot_freshness.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/audits/push_override_receipts/20260407T173000Z_review_snapshot_landing.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_phases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_parse.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_delta.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_git.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_hints.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_render_sections.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_sections.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_serialize.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_why.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_contexts.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_handler.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_launch_control.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_session_build.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit 4d8a128 changed dev/scripts/devctl/review_channel/packet_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Commit 5978dce changed dev/scripts/devctl/runtime/project_governance_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_snapshot_models.py`) — Commit 5978dce changed dev/scripts/devctl/runtime/review_snapshot_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`e21d8e8` | MPs: MP-377, MP-3** — Close MP-377 typed-continuity tranche (Legs 1+2+3 follow-ups A/B/C)
  - Lands the three remaining items on the typed-continuity Session Resume
  - parent in dev/active/MASTER_PLAN.md (the [ ] item: "Replace boolean-only
  - Session Resume detection with typed continuity state in startup-context /
  - plan: `dev/active/ai_governance_platform.md`
  - plan: `dev/active/platform_authority_loop.md`
  - plan: `dev/active/remote_commit_pipeline.md`
  - plan: `dev/active/PLAN_FORMAT.md`
- **`f9388da`** — Add install-git-hooks command for portable pre-commit snapshot refresh
  - Closes the gap between the architectural promise "every governed commit
  - regenerates the ReviewSnapshot inside the commit" and the reality that
  - the pre-commit hook inside governed_executor_phases.execute_commit only
- **`d155b02`** — Refresh REVIEW_SNAPSHOT to track branch tip at 60bcd68
  - The ReviewSnapshot surface committed in 5978dce recorded state at
  - its parent (b6be213), which is correct for the pre-commit-hook
  - semantics it demonstrates. But every subsequent commit in the
- **`60bcd68`** — Open policy-gated skip-preflight bypass window for ReviewSnapshot landing
  - Typed override receipt for publishing the ReviewSnapshot slice
  - (5978dce + 4b45f9a + c98d471) through the governed push path when
  - the stale reviewer-loop state (reason=reviewer_heartbeat_stale,
- **`c98d471`** — Restore script_catalog entries stripped during previous edit
  - Regression fix: 14 entries that were present at HEAD got silently
  - stripped from _CHECK_SCRIPT_ENTRIES and _PROBE_SCRIPT_ENTRIES during
  - an earlier edit to script_catalog.py and then committed into the
- **`4b45f9a`** — Register python_typed_seams in script_catalog
  - Pre-push scaffolding fix: check_python_typed_seams.py exists on disk
  - and is referenced by both quality_policy/defaults.py:136,315 (as an
  - AI guard ID) and bundles/registry.py:65 (as a command string), but
- **`5978dce`** — Add ReviewSnapshot external-review surface via pre-commit refresh hook
  - Introduces dev/audits/REVIEW_SNAPSHOT.md as a deterministic typed
  - projection of repo governance state, designed to be read directly
  - from GitHub by external reviewers (ChatGPT Pro, human auditors) so
- **`b6be213` | MPs: MP-382, MP-387** — Land reviewer-supervisor restart-policy follow-up checkpoint
  - Closes the manual_stop / completed restart-policy gap left open after
  - 244ae83 (MP-382 + MP-387 launch-authority closure). The launchd publisher
  - wrapper already treated those stop reasons as non-restartable, but two
  - plan: `dev/active/remote_control_runtime.md`
- **`244ae83` | MPs: MP-382, MP-387 | markers: F21, F21a, F23, F24** — Land MP-382 + MP-387 launch-authority closure (F21/F21a/F23/F24)
  - Resolves operator interaction mode once through governance/startup
  - authority and threads it through session preparation plus the pre-spawn
  - dispatcher gate, closing F21: _launch_and_refresh() in bridge_handler.py
  - plan: `dev/active/remote_control_runtime.md`
- **`fefa621` | markers: F21, F21a, F23, F24** — Checkpoint reviewer bridge state: F21/F21a/F23/F24 launch-authority findings
  - Reviewer flipped mode from single_agent to active_dual_agent and posted
  - new open findings against commit 84e60bc's F21 integration:
  - bridge_handler.py was sourcing the dispatcher gate from
- **`846987c` | markers: F21** — Update test_launch_sessions_if_requested_headless_requires_reviewer_proof_of_life for F21 integration
  - Closes a regression my F21 integration commit 84e60bc introduced in
  - test_review_channel.py:937. Self-correction caught by the broader
  - test_review_channel.py sweep that I should have run BEFORE pushing
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
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
- checkpoint_before_continue: dirty_path_budget_exceeded

### Stale warnings
- Keep editing the current slice.
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-2c069daaae33` binds this file to HEAD `92a33583320c`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
