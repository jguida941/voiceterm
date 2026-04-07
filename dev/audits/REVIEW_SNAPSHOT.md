# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `60bcd6800c63` — Open policy-gated skip-preflight bypass window for ReviewSnapshot landing
- Tree hash: `471835498f27`
- Generation stamp: `snap-6d9c9d321fd6`
- Generated at (UTC): 2026-04-07T21:32:26Z
- Push decision: `no_push_needed` — remote_publish_recorded_post_push_pending
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 154 files, +17057/-6443
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
- HEAD SHA: `60bcd6800c63cd473f1b8fefbeef2ee8612bd998`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-07T17:21:27-04:00

## 2. Governance state

### Push decision
- action: `no_push_needed`
- reason: remote_publish_recorded_post_push_pending
- push_eligible_now: False
- worktree_clean: True
- next_step_command: `n/a`
- publication_backlog: none

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

Range: last 24 commits ending at `60bcd6800c63`

- commits: 24
- files changed: 154
- insertions: +17057
- deletions: -6443
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 38 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `60bcd68` | Open policy-gated skip-preflight bypass window for ReviewSn… | 2 | +100/-1 | tooling |  |
| 2 | `c98d471` | Restore script_catalog entries stripped during previous edit | 1 | +14/-0 | tooling |  |
| 3 | `4b45f9a` | Register python_typed_seams in script_catalog | 1 | +1/-0 | tooling |  |
| 4 | `5978dce` | Add ReviewSnapshot external-review surface via pre-commit r… | 33 | +4198/-680 | tooling |  |
| 5 | `b6be213` | Land reviewer-supervisor restart-policy follow-up checkpoint | 21 | +549/-98 | tooling |  |
| 6 | `244ae83` | Land MP-382 + MP-387 launch-authority closure (F21/F21a/F23… | 30 | +1306/-333 | tooling | Parser / ANSI boundary |
| 7 | `fefa621` | Checkpoint reviewer bridge state: F21/F21a/F23/F24 launch-a… | 1 | +39/-92 | docs |  |
| 8 | `846987c` | Update test_launch_sessions_if_requested_headless_requires_… | 1 | +150/-3 | tooling |  |
| 9 | `84e60bc` | Land F21 integration: wire launcher_discipline into the lau… | 4 | +248/-2 | tooling | Parser / ANSI boundary |
| 10 | `b748c6e` | Land F21 launcher-discipline pre-flight validation (pure fu… | 2 | +443/-0 | tooling |  |
| 11 | `7a8b427` | Land MP-381 dashboard wiring + ViolationRecord consumer ada… | 15 | +1728/-42 | tooling |  |
| 12 | `e35c4e3` | Land MP-381 F18 + F19 fixes per Codex instruction 269e91f22… | 2 | +312/-22 | tooling |  |
| 13 | `e564969` | Land MP-381 F14 fix: exempt parked governed pipelines from… | 3 | +330/-3 | tooling |  |
| 14 | `4f93b48` | Land F1 AST field-route helper plus MP-381 probe-report Vio… | 11 | +806/-35 | tooling |  |
| 15 | `b22bf96` | Teach field-route guard to scan package sources | 1 | +16/-7 | tooling |  |
| 16 | `080f4df` | Convert dashboard_render flat files to a package | 5 | +11/-11 | tooling |  |
| 17 | `705b7ef` | Preserve top_blocker field-route visibility in dashboard_re… | 1 | +6/-0 | tooling |  |
| 18 | `1f5e6a4` | Checkpoint reviewer bridge state | 1 | +22/-36 | docs |  |
| 19 | `d9a76f2` | Modularize oversized files flagged by post-push code_shape… | 27 | +3792/-3071 | tooling |  |
| 20 | `f66a4ec` | Remove stale PATH_POLICY_OVERRIDES for shrunken files | 1 | +0/-12 | tooling |  |
| 21 | `28f5453` | Document review-handoff recovery seam | 6 | +89/-0 | tooling |  |
| 22 | `9c83677` | Add AI-readable package-layout organization surface | 8 | +745/-28 | tooling |  |
| 23 | `93c69c3` | Modularize review-channel shape cluster into focused extrac… | 9 | +736/-657 | tooling |  |
| 24 | `9a3fabc` | Reduce commands-root layout with compatibility shims | 18 | +1416/-1310 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-1 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +2/-2 |
| `AGENTS.md` | docs | +41/-4 |
| `AUDIT_STATUS.md` | docs | +0/-474 |
| `bridge.md` | docs | +231/-221 |
| `dev/active/MASTER_PLAN.md` | tooling | +93/-1 |
| `dev/active/ai_governance_platform.md` | tooling | +88/-3 |
| `dev/active/platform_authority_loop.md` | tooling | +75/-8 |
| `dev/active/portable_code_governance.md` | tooling | +40/-8 |
| `dev/active/remote_commit_pipeline.md` | tooling | +99/-16 |
| `dev/active/remote_control_runtime.md` | tooling | +102/-4 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +437/-0 |
| `dev/audits/push_override_receipts/20260407T173000Z_review_snapshot_landing.md` | tooling | +99/-0 |
| `dev/config/devctl_repo_policy.json` | tooling | +1/-1 |
| `dev/config/launchd/review_channel_publisher_service.py` | tooling | +4/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +43/-5 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +226/-2 |
| `dev/scripts/README.md` | tooling | +56/-6 |
| `dev/scripts/checks/check_audit_status_sync.py` | tooling | +0/-112 |
| `dev/scripts/checks/check_review_snapshot_freshness.py` | tooling | +203/-0 |
| `dev/scripts/checks/code_shape/code_shape_policy.py` | tooling | +0/-18 |
| `dev/scripts/checks/package_layout/command.py` | tooling | +17/-0 |
| `dev/scripts/checks/package_layout/compatibility_redirects.py` | tooling | +3/-0 |
| `dev/scripts/checks/package_layout/organization.py` | tooling | +243/-0 |
| `dev/scripts/checks/package_layout/render.py` | tooling | +54/-0 |
| `dev/scripts/checks/package_layout/rule_models.py` | tooling | +65/-0 |
| `dev/scripts/checks/platform_contract_closure/field_routes_surface_state.py` | tooling | +126/-18 |
| `dev/scripts/checks/startup_authority_contract/command.py` | tooling | +3/-1 |
| `dev/scripts/checks/startup_authority_contract/runtime_checks.py` | tooling | +211/-22 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-1 |
| `dev/scripts/devctl/cli.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/auto_mode_status.py` | tooling | +8/-161 |
| `dev/scripts/devctl/commands/dashboard_data.py` | tooling | +34/-40 |
| `dev/scripts/devctl/commands/dashboard_render.py` | tooling | +61/-853 |
| `dev/scripts/devctl/commands/dashboard_render_helpers.py` | tooling | +84/-0 |
| `dev/scripts/devctl/commands/dashboard_render_markdown.py` | tooling | +338/-0 |
| `dev/scripts/devctl/commands/dashboard_render_terminal.py` | tooling | +454/-0 |
| `dev/scripts/devctl/commands/dashboard_violations.py` | tooling | +158/-0 |
| `dev/scripts/devctl/commands/governance/review_snapshot.py` | tooling | +180/-0 |
| `dev/scripts/devctl/commands/orchestrate_status.py` | tooling | +8/-119 |
| _114 more files trimmed_ | | |

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
- **authority_surface**: Typed authority surface touched (`dev/audits/push_override_receipts/20260407T173000Z_review_snapshot_landing.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/check_review_snapshot_freshness.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_phases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_parse.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_delta.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_git.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_hints.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_render.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_render_sections.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_sections.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_serialize.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_why.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_check_review_snapshot_freshness.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_contexts.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_handler.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_launch_control.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_session_build.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_checks.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actions.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_git.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_push_result.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_sync.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_runtime_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_recovery.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_recovery_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_render.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_render_sections.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Commit 5978dce changed dev/scripts/devctl/runtime/project_governance_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_snapshot_models.py`) — Commit 5978dce changed dev/scripts/devctl/runtime/review_snapshot_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/check_result_models.py`) — Commit 7a8b427 changed dev/scripts/devctl/runtime/check_result_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/test_check_output_contract.py`) — Commit 7a8b427 changed dev/scripts/devctl/tests/test_check_output_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Commit e35c4e3 changed dev/scripts/devctl/tests/checks/test_startup_authority_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_follow_recovery_models.py`) — Commit d9a76f2 changed dev/scripts/devctl/review_channel/reviewer_follow_recovery_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/checks/package_layout/rule_models.py`) — Commit 9c83677 changed dev/scripts/checks/package_layout/rule_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_collaboration_models.py`) — Commit 93c69c3 changed dev/scripts/devctl/runtime/review_state_collaboration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit 93c69c3 changed dev/scripts/devctl/runtime/review_state_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`60bcd68`** — Open policy-gated skip-preflight bypass window for ReviewSnapshot landing
  - Typed override receipt for publishing the ReviewSnapshot slice
  - (5978dce + 4b45f9a + c98d471) through the governed push path when
  - the stale reviewer-loop state (reason=reviewer_heartbeat_stale,
  - evolution: The commit/push path exposed a process problem that was architectural, not a reason to weaken checks. The repo already knew how to route bundles and risk add-ons, but the governed mutation path still carried only a `gua…
- **`c98d471`** — Restore script_catalog entries stripped during previous edit
  - Regression fix: 14 entries that were present at HEAD got silently
  - stripped from _CHECK_SCRIPT_ENTRIES and _PROBE_SCRIPT_ENTRIES during
  - an earlier edit to script_catalog.py and then committed into the
  - evolution: The commit/push path exposed a process problem that was architectural, not a reason to weaken checks. The repo already knew how to route bundles and risk add-ons, but the governed mutation path still carried only a `gua…
- **`4b45f9a`** — Register python_typed_seams in script_catalog
  - Pre-push scaffolding fix: check_python_typed_seams.py exists on disk
  - and is referenced by both quality_policy/defaults.py:136,315 (as an
  - AI guard ID) and bundles/registry.py:65 (as a command string), but
  - evolution: The commit/push path exposed a process problem that was architectural, not a reason to weaken checks. The repo already knew how to route bundles and risk add-ons, but the governed mutation path still carried only a `gua…
- **`5978dce`** — Add ReviewSnapshot external-review surface via pre-commit refresh hook
  - Introduces dev/audits/REVIEW_SNAPSHOT.md as a deterministic typed
  - projection of repo governance state, designed to be read directly
  - from GitHub by external reviewers (ChatGPT Pro, human auditors) so
  - evolution: The commit/push path exposed a process problem that was architectural, not a reason to weaken checks. The repo already knew how to route bundles and risk add-ons, but the governed mutation path still carried only a `gua…
- **`b6be213` | MPs: MP-382, MP-387** — Land reviewer-supervisor restart-policy follow-up checkpoint
  - Closes the manual_stop / completed restart-policy gap left open after
  - 244ae83 (MP-382 + MP-387 launch-authority closure). The launchd publisher
  - wrapper already treated those stop reasons as non-restartable, but two
  - plan: `dev/active/remote_control_runtime.md`
  - evolution: The commit/push path exposed a process problem that was architectural, not a reason to weaken checks. The repo already knew how to route bundles and risk add-ons, but the governed mutation path still carried only a `gua…
- **`244ae83` | MPs: MP-382, MP-387 | markers: F21, F21a, F23, F24** — Land MP-382 + MP-387 launch-authority closure (F21/F21a/F23/F24)
  - Resolves operator interaction mode once through governance/startup
  - authority and threads it through session preparation plus the pre-spawn
  - dispatcher gate, closing F21: _launch_and_refresh() in bridge_handler.py
  - plan: `dev/active/remote_control_runtime.md`
  - evolution: The commit/push path exposed a process problem that was architectural, not a reason to weaken checks. The repo already knew how to route bundles and risk add-ons, but the governed mutation path still carried only a `gua…
- **`fefa621` | markers: F21, F21a, F23, F24** — Checkpoint reviewer bridge state: F21/F21a/F23/F24 launch-authority findings
  - Reviewer flipped mode from single_agent to active_dual_agent and posted
  - new open findings against commit 84e60bc's F21 integration:
  - bridge_handler.py was sourcing the dispatcher gate from
  - evolution: The commit/push path exposed a process problem that was architectural, not a reason to weaken checks. The repo already knew how to route bundles and risk add-ons, but the governed mutation path still carried only a `gua…
- **`846987c` | markers: F21** — Update test_launch_sessions_if_requested_headless_requires_reviewer_proof_of_life for F21 integration
  - Closes a regression my F21 integration commit 84e60bc introduced in
  - test_review_channel.py:937. Self-correction caught by the broader
  - test_review_channel.py sweep that I should have run BEFORE pushing
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
- **`84e60bc` | MPs: MP-381 | markers: F21** — Land F21 integration: wire launcher_discipline into the launch dispatcher
  - Closes the gap Codex flagged on the prior pure-helper slice b748c6e.
  - The pure validation function from launcher_discipline.py is now called
  - inside launch_sessions_if_requested before any spawn happens.
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
- **`b748c6e` | markers: F21** — Land F21 launcher-discipline pre-flight validation (pure function)
  - Closes finding F21 (operator-flagged 'IS IT HEADLESS CODEX HUGE
  - PROBLEM') with a deterministic typed gate that the launch dispatcher
  - can call before spawning conductors.
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
- **`7a8b427` | MPs: MP-381** — Land MP-381 dashboard wiring + ViolationRecord consumer adapter
  - This commit lands the dashboard-side consumer of the MP-381
  - CheckResult / ViolationRecord contract family, completing the 5th of
  - 5 surfaces the contract family was supposed to unify (checks, probes,
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
- **`e35c4e3` | MPs: MP-381 | markers: F18, F19** — Land MP-381 F18 + F19 fixes per Codex instruction 269e91f220e9
  - F18: bind the parked-pipeline exemption in
  - collect_post_checkpoint_dirty_worktree_errors to the current git index
  - tree hash. _governed_pipeline_parked_at_checkpoint now requires
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
- **`e564969` | MPs: MP-381 | markers: F14** — Land MP-381 F14 fix: exempt parked governed pipelines from post-checkpoint dirty check
  - collect_post_checkpoint_dirty_worktree_errors now accepts repo_root and
  - pipeline kwargs and exempts dirty worktrees when a typed governed
  - remote-commit pipeline is intentionally parked at the checkpoint/approval
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
- **`4f93b48` | MPs: MP-381 | markers: F1** — Land F1 AST field-route helper plus MP-381 probe-report ViolationRecord adapter
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
- **`b22bf96`** — Teach field-route guard to scan package sources
  - _source_contains_any previously resolved only flat <module>.py files
  - and silently returned False for packages. Now it falls back to
  - scanning every .py file in a <module>/ package directory so split
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
- **`080f4df`** — Convert dashboard_render flat files to a package
  - Move dashboard_render.py + 4 split files into a dashboard_render/
  - package to relieve the commands/ directory crowding cap. The package
  - __init__.py preserves the public API (render_json, render_terminal,
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
- **`705b7ef`** — Preserve top_blocker field-route visibility in dashboard_render
  - The dashboard_render split moved the top_blocker rendering into the
  - _terminal and _markdown submodules. The field_route guard searches
  - for the literal token in dashboard_render.py's source, so the
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
- **`1f5e6a4`** — Checkpoint reviewer bridge state
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
- **`d9a76f2`** — Modularize oversized files flagged by post-push code_shape audit
  - Split four subsystem clusters that exceeded the 350-line soft limit,
  - plus remove one stale path override now below language default.
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
- **`f66a4ec`** — Remove stale PATH_POLICY_OVERRIDES for shrunken files
  - status_line/format/tests.rs (98 lines) and devctl/collect.py (253 lines)
  - are well under their language defaults (900 and 350 respectively). The
  - code_shape guard flagged these overrides as stale during push preflight.
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
- **`28f5453`** — Document review-handoff recovery seam
  - evolution: The next failure was not a bad implementation slice; it was a self-hosting reviewer interruption. A live `active_dual_agent` Codex conductor bootstrapped, narrowed into the bounded post-push shape cleanup, and then the …
- **`9c83677`** — Add AI-readable package-layout organization surface
  - Implement unified organization surface in check_package_layout output:
  - evolution: The review-channel runtime had already grown typed reviewer/implementer role slots, but a lot of the launch/bootstrap/recover path still assumed fixed provider identity: Codex was implicitly the reviewer, Claude was imp…
- **`93c69c3`** — Modularize review-channel shape cluster into focused extraction modules
  - Split three over-limit files to clear new_file_exceeds_soft_limit and
  - mixed_concerns_on_touched_file violations:
  - evolution: The review-channel runtime had already grown typed reviewer/implementer role slots, but a lot of the launch/bootstrap/recover path still assumed fixed provider identity: Codex was implicitly the reviewer, Claude was imp…
- **`9a3fabc`** — Reduce commands-root layout with compatibility shims
  - evolution: The review-channel runtime had already grown typed reviewer/implementer role slots, but a lot of the launch/bootstrap/recover path still assumed fixed provider identity: Codex was implicitly the reviewer, Claude was imp…
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-6d9c9d321fd6` binds this file to HEAD `60bcd6800c63`; if they drift, the freshness guard will fail CI.
