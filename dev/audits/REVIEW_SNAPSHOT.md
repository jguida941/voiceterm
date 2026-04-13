# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `codex-role-portability`
- HEAD: `c06a989a8275` — Refresh external review snapshot for 1e24f79f
- Tree hash: `e5a0f719ec38`
- Generation stamp: `snap-9b3c7f89e0ad`
- Generated at (UTC): 2026-04-13T17:49:50Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 262 files, +21265/-6332
- Governance findings: 96 open / 71 fixed / 181 total
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
- Current branch: `codex-role-portability`
- HEAD SHA: `c06a989a827559335a0eed01183c384a6df9d34d`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-13T13:00:02-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 28
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: queued
- publication_guidance: Local branch still has unpublished work waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `c06a989a8275`

- commits: 25
- files changed: 262
- insertions: +21265
- deletions: -6332
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 41 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `c06a989a` | Refresh external review snapshot for 1e24f79f | 1 | +110/-83 | tooling |  |
| 2 | `1e24f79f` | Fix remote-control review-channel guard regressions and ext… | 158 | +12763/-4359 | tooling | Parser / ANSI boundary |
| 3 | `687c0478` | Refresh external review snapshot for 4372e2cd | 1 | +86/-83 | tooling |  |
| 4 | `4372e2cd` | Fix probe shims, event projection, and launch/rollover test… | 44 | +943/-142 | tooling |  |
| 5 | `f88de94b` | Refresh external review snapshot for 5ed6e2fb | 1 | +80/-71 | tooling |  |
| 6 | `5ed6e2fb` | Make review state role-neutral and bind push approval to wo… | 45 | +730/-117 | tooling |  |
| 7 | `a1c7ffe3` | Refresh external review snapshot for 00e45380 | 1 | +67/-64 | tooling |  |
| 8 | `00e45380` | Checkpoint single-agent liveness and worker-lane portability | 33 | +815/-159 | tooling |  |
| 9 | `763be95d` | Refresh external review snapshot for e8ccc7e7 | 1 | +63/-64 | tooling |  |
| 10 | `e8ccc7e7` | review_channel: remote-control attachment counts as live co… | 11 | +258/-61 | tooling |  |
| 11 | `70e2544f` | docs(audit): dashboard-loop ticks 33-48 + liveness symmetry… | 3 | +285/-51 | tooling |  |
| 12 | `5cc9e8d9` | Refresh external review snapshot for 01e436d0 | 1 | +67/-65 | tooling |  |
| 13 | `01e436d0` | docs+workflow: propagate bundle.tooling publications-ignore… | 7 | +72/-49 | tooling |  |
| 14 | `bb6bbef4` | Refresh external review snapshot for 0db1267c | 1 | +56/-59 | tooling |  |
| 15 | `0db1267c` | bundles(tooling): ignore publications warning source in str… | 3 | +53/-50 | tooling |  |
| 16 | `49dcf13e` | Refresh external review snapshot for 353f3bb6 | 1 | +59/-62 | tooling |  |
| 17 | `353f3bb6` | review_channel: priority selector drives current_session.cu… | 6 | +69/-51 | tooling |  |
| 18 | `0d2cb8ad` | Refresh external review snapshot for 637a4ad9 | 1 | +59/-62 | tooling |  |
| 19 | `637a4ad9` | docs: slice-closure updates from Codex for the review_chann… | 4 | +97/-42 | docs |  |
| 20 | `7a3091c5` | plans: record review_channel trigger primitive slice in act… | 5 | +101/-66 | tooling |  |
| 21 | `de08f5c9` | review_channel: split enrich_event_review_state to satisfy… | 2 | +103/-58 | tooling |  |
| 22 | `52878653` | Refresh external review snapshot for 061a1261 | 1 | +54/-51 | tooling |  |
| 23 | `061a1261` | review_channel: packet_control_loop priority selection + co… | 5 | +350/-62 | tooling |  |
| 24 | `2cd74a7c` | Refresh external review snapshot for 6db71aca | 1 | +107/-85 | tooling |  |
| 25 | `6db71aca` | review_channel: typed participant authoritative + action_re… | 78 | +3818/-316 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/tooling_control_plane.yml` | tooling | +1/-1 |
| `AGENTS.md` | docs | +40/-11 |
| `bridge.md` | docs | +27/-53 |
| `dev/active/MASTER_PLAN.md` | tooling | +191/-17 |
| `dev/active/ai_governance_platform.md` | tooling | +176/-16 |
| `dev/active/autonomous_governance_loop_v2.md` | tooling | +59/-19 |
| `dev/active/continuous_swarm.md` | tooling | +354/-8 |
| `dev/active/platform_authority_loop.md` | tooling | +17/-0 |
| `dev/active/remote_commit_pipeline.md` | tooling | +141/-1 |
| `dev/active/remote_control_runtime.md` | tooling | +364/-21 |
| `dev/active/review_channel.md` | tooling | +7/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +645/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1603/-1560 |
| `dev/config/devctl_policies/launcher.json` | tooling | +25/-0 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +13/-8 |
| `dev/config/git_hooks/pre-push-governed-push.sh` | tooling | +1/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +49/-8 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +269/-1 |
| `dev/scripts/README.md` | tooling | +84/-23 |
| `dev/scripts/checks/check_bundle_workflow_parity.py` | tooling | +66/-1 |
| `dev/scripts/checks/check_duplication_audit.py` | tooling | +69/-1 |
| `dev/scripts/checks/check_naming_consistency.py` | tooling | +60/-1 |
| `dev/scripts/checks/check_rustsec_policy.py` | tooling | +17/-1 |
| `dev/scripts/checks/code_shape/code_shape_policy.py` | tooling | +0/-54 |
| `dev/scripts/checks/naming_consistency/core.py` | tooling | +2/-2 |
| `dev/scripts/checks/platform_contract_closure/emitter_parity.py` | tooling | +5/-0 |
| `dev/scripts/checks/platform_contract_closure/emitter_parity_contract_checks.py` | tooling | +8/-3 |
| `dev/scripts/checks/probe_boolean_params.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_clone_density.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_concurrency.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_defensive_overchecking.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_design_smells.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_dict_as_struct.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_exception_quality.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_magic_numbers.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_path_filters.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_stringly_typed.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_type_conversions.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_unnecessary_intermediates.py` | tooling | +17/-1 |
| `dev/scripts/checks/probe_unwrap_chains.py` | tooling | +17/-1 |
| _222 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 181
- open: 96
- fixed: 71
- false positives: 0

Recent findings:
- `none_safety_chained_get_crash` — `dev/scripts/devctl/commands/dashboard_summary.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `dev/scripts/devctl/commands/autonomy/run.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `dev/scripts/devctl/commands/release/ship_verify_pypi_step.py` (n/a, verdict=`confirmed_issue`)
- `session_launch_no_dedup` — `dev/scripts/devctl/commands/review_channel/bridge_launch_control.py` (n/a, verdict=`confirmed_issue`)
- `context-graph` — `dev/scripts/devctl/context_graph/contract_nodes.py` (n/a, verdict=`fixed`)
- `startup_probe_path_bug` — `dev/scripts/devctl/runtime/startup_signals.py` (high, verdict=`confirmed_issue`)
- `guard_probe_data_isolation` — `dev/scripts/devctl/commands/check/phases.py` (critical, verdict=`confirmed_issue`)
- `finding_backlog_not_implemented` — `dev/scripts/devctl/platform/planning_ir.py` (critical, verdict=`confirmed_issue`)
- `plan_registry_consolidation` — `dev/active/INDEX.md` (high, verdict=`confirmed_issue`)
- `plan_format_enforcement_missing` — `dev/active/PLAN_FORMAT.md` (high, verdict=`confirmed_issue`)

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
- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_sanitize.py`) — Review contract-level invariants for this file
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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_remote_commit_pipeline_phases34.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actions.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_authorization.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_push.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_parser.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_handler.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_render.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_push_decision.py`) — Review contract-level invariants for this file
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
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit 6db71aca changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/validation_contracts.py`) — Commit 6db71aca changed dev/scripts/devctl/runtime/validation_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`c06a989a`** — Refresh external review snapshot for 1e24f79f
- **`1e24f79f`** — Fix remote-control review-channel guard regressions and extract oversized modules
  - Codex session 2 guard-fix work:
  - - Fixed 4 targeted guards (parameter-count, facade-wrappers, dict-schema, code-shape)
  - - Fixed attention_revision_stale false positive in commit gate
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
- **`5cc9e8d9`** — Refresh external review snapshot for 01e436d0
- **`01e436d0` | MPs: MP-377** — docs+workflow: propagate bundle.tooling publications-ignore to CI + maintainer docs
  - Co-modification required by docs-check --strict-tooling after
  - dev/scripts/devctl/bundles/registry.py extended the bundle.tooling
  - hygiene command with --ignore-warning-source publications:
  - plan: `dev/active/ai_governance_platform.md`
  - plan: `dev/active/platform_authority_loop.md`
  - plan: `dev/active/autonomous_governance_loop_v2.md`
  - plan: `dev/active/remote_commit_pipeline.md`
  - plan: `dev/active/PLAN_FORMAT.md`
- **`bb6bbef4`** — Refresh external review snapshot for 0db1267c
- **`0db1267c`** — bundles(tooling): ignore publications warning source in strict hygiene
  - The bundle.tooling hygiene gate fails on long-standing external-publication
  - drift for terminal-as-interface (tracked at 369cb67b3c85 vs 380+ impacted
  - paths across HEAD). That drift is unrelated to review-channel / runtime
- **`49dcf13e`** — Refresh external review snapshot for 353f3bb6
- **`353f3bb6`** — review_channel: priority selector drives current_session.current_instruction
  - Wires the action-request-first priority selection from
  - packet_control_loop.select_priority_pending_packet into
  - current_session.current_instruction so read-only dashboard and status
- **`0d2cb8ad`** — Refresh external review snapshot for 637a4ad9
- **`637a4ad9`** — docs: slice-closure updates from Codex for the review_channel trigger primitive
  - Concurrent with Claude's sequential push attempts, Codex finished its slice
  - documentation pass:
  - - AGENTS.md: note the new action_request_delivery + packet_control_loop
- **`7a3091c5` | MPs: MP-380, MP-387** — plans: record review_channel trigger primitive slice in active docs
  - Codex continuing its slice with plan-doc updates landing in the working
  - tree concurrently with Claude's governed push attempts:
  - - dev/active/MASTER_PLAN.md: mark the packet_control_loop + action_request
  - plan: `dev/active/remote_control_runtime.md`
- **`de08f5c9`** — review_channel: split enrich_event_review_state to satisfy function-length gate
  - check_code_shape flagged enrich_event_review_state at 172 lines (110-281),
  - over the 150-line Python function default. Extract the _compat-merging
  - block (service_identity, attach_auth_policy, push_enforcement, doctor,
- **`52878653`** — Refresh external review snapshot for 061a1261
- **`061a1261`** — review_channel: packet_control_loop priority selection + control hints
  - Adds packet_control_loop.py with select_priority_pending_packet(), which
  - picks the highest-priority live pending packet (action_request class first,
  - then findings/questions/instructions) and returns control-state metadata
- **`2cd74a7c`** — Refresh external review snapshot for 6db71aca
- **`6db71aca` | MPs: MP-355** — review_channel: typed participant authoritative + action_request delivery primitive + dashboard/control-plane parity
  - Closes six of the eight scaffolding layers named in the architectural meta-
  - finding this session. Introduces the action_request_delivery primitive that
  - stamps delivery_emitted_at_utc / delivery_observed_at_utc / delivery_observed_by
  - plan: `dev/active/review_channel.md`
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

- open governance findings: 96

### Startup advisories
- checkpoint_before_continue: staged_index_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/dashboard_summary.py`): none_safety_chained_get_crash: 
- **governance_open** (`dev/scripts/devctl/commands/autonomy/run.py`): none_safety_chained_get_crash: 
- **governance_open** (`dev/scripts/devctl/commands/release/ship_verify_pypi_step.py`): none_safety_chained_get_crash: 
- **governance_open** (`dev/scripts/devctl/commands/review_channel/bridge_launch_control.py`): session_launch_no_dedup: 
- **governance_open** (`dev/scripts/devctl/runtime/startup_signals.py`): startup_probe_path_bug: Reads dev/reports/probes/summary.json (DOES NOT EXIST). Should read dev/reports/probes/latest/summary.json. Startup quality_signals never includes probe data.
- **governance_open** (`dev/scripts/devctl/commands/check/phases.py`): guard_probe_data_isolation: Guards run in run_setup_phase, probes run in run_probe_phase. Zero data flows between them. Code-shape clusters recalculated by probes independently. Probe results not consumed by startup, planning-ir, session-resume, or quality-feedback.
- **governance_open** (`dev/scripts/devctl/platform/planning_ir.py`): finding_backlog_not_implemented: No FindingBacklog class exists. Four separate finding sources (LIVE_RUN.md, governance-review, startup blockers, system-picture) disagree. findings-priority reads only LIVE_RUN.md. Planning-IR sliced to recent 50 rows. SessionPacingState advisory-only. GuardPromotionCandidate has no consumer.

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-9b3c7f89e0ad` binds this file to HEAD `c06a989a8275`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
