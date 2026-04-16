# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `5146e65182bf` — Refresh external review snapshot for a14356d3
- Tree hash: `28d3d3fb6fdc`
- Generation stamp: `snap-0879b3bc76de`
- Generated at (UTC): 2026-04-16T01:32:49Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 155 files, +12871/-4309
- Governance findings: 112 open / 86 fixed / 212 total
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
- HEAD SHA: `5146e65182bf2d8804567d11289d778d90203c9b`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-15T21:04:16-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 8
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `post_push_green` (push_completed)
- current_push_authorization: `push-auth-20260416T013032888275Z` (valid=True)
- authorized_head_commit: `5146e65182bf2d8804567d11289d778d90203c9b`
- approved_target_identity: `tree-receipt-20260416T010353966600Z:cccc4a6dd384dfac9a5990bfe05087bb4a0de16f`
- publication_backlog: recommended
- publication_guidance: 2 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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

Range: last 25 commits ending at `5146e65182bf`

- commits: 25
- files changed: 155
- insertions: +12871
- deletions: -4309
- bundle classes touched: docs, tooling
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 19 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `5146e651` | Refresh external review snapshot for a14356d3 | 2 | +72/-89 | docs |  |
| 2 | `a14356d3` | Fix review-channel launch authority and runtime packet pari… | 28 | +732/-126 | tooling |  |
| 3 | `bc1b011b` | Refresh external review snapshot for d599b9b6 | 2 | +61/-61 | docs |  |
| 4 | `d599b9b6` | Fix startup repair authority parity | 11 | +395/-58 | tooling |  |
| 5 | `7d35f8e8` | Refresh external review snapshot for f3350f0d | 2 | +74/-69 | docs |  |
| 6 | `f3350f0d` | Implement dogfood campaign contract and bound startup autho… | 23 | +908/-99 | tooling | Parser / ANSI boundary |
| 7 | `8b587485` | Refresh external review snapshot for 5807328b | 2 | +66/-68 | docs |  |
| 8 | `5807328b` | Harden shim governance and review state parsing | 15 | +292/-94 | tooling |  |
| 9 | `2454de6b` | Refresh external review snapshot for 63ad7200 | 1 | +62/-66 | tooling |  |
| 10 | `63ad7200` | Repair event-backed bridge projection parity | 11 | +214/-83 | tooling |  |
| 11 | `8dfa6a83` | Refresh external review snapshot for 0af6b46f | 1 | +58/-61 | tooling |  |
| 12 | `0af6b46f` | Repair bridge poll metadata projection | 10 | +224/-73 | tooling |  |
| 13 | `ae95f570` | Refresh external review snapshot for 1bd047a3 | 2 | +77/-72 | docs |  |
| 14 | `1bd047a3` | Stabilize review-channel authority recovery | 30 | +1402/-482 | tooling |  |
| 15 | `97054783` | Refresh external review snapshot for 5304aecb | 2 | +66/-65 | docs |  |
| 16 | `5304aecb` | Refresh external review snapshot for 0f66c9d8 | 2 | +85/-82 | docs |  |
| 17 | `0f66c9d8` | Stabilize review-channel authority recovery | 88 | +6781/-1634 | tooling |  |
| 18 | `1271a075` | Refresh external review snapshot for fc86c018 | 2 | +51/-47 | docs |  |
| 19 | `fc86c018` | Mark Q94 fixed in LIVE_RUN | 1 | +9/-1 | tooling |  |
| 20 | `9c63556a` | Refresh external review snapshot for 8d1c30a0 | 2 | +74/-82 | docs |  |
| 21 | `8d1c30a0` | Fail closed on stale dashboard daemon state | 5 | +304/-31 | tooling |  |
| 22 | `847adc03` | Refresh external review snapshot for 5daed3c2 | 1 | +54/-52 | tooling |  |
| 23 | `5daed3c2` | Delete redesign_research/ — operator: stop making MDs, use… | 5 | +0/-748 | tooling |  |
| 24 | `acac5ee0` | Refresh external review snapshot for f5dc6d5e | 1 | +62/-66 | tooling |  |
| 25 | `f5dc6d5e` | Push redesign research bundle for Codex (operator directive… | 5 | +748/-0 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `0` | tooling | +0/-0 |
| `AGENTS.md` | docs | +50/-17 |
| `bridge.md` | docs | +69/-72 |
| `dev/active/MASTER_PLAN.md` | tooling | +100/-2 |
| `dev/active/ai_governance_platform.md` | tooling | +839/-9 |
| `dev/active/continuous_swarm.md` | tooling | +24/-0 |
| `dev/active/portable_code_governance.md` | tooling | +31/-2 |
| `dev/active/remote_control_runtime.md` | tooling | +24/-1 |
| `dev/audits/LIVE_RUN.md` | tooling | +9/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1304/-1318 |
| `dev/audits/redesign_research/00_codex_directive.md` | tooling | +55/-55 |
| `dev/audits/redesign_research/01_livelogs_findings.md` | tooling | +191/-191 |
| `dev/audits/redesign_research/02_plans_landscape.md` | tooling | +216/-216 |
| `dev/audits/redesign_research/03_debt_ledger.md` | tooling | +142/-142 |
| `dev/audits/redesign_research/04_today_postmortem.md` | tooling | +144/-144 |
| `dev/config/quality_presets/voiceterm.json` | tooling | +28/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +58/-7 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +364/-1 |
| `dev/scripts/README.md` | tooling | +61/-17 |
| `dev/scripts/checks/check_review_snapshot_freshness.py` | tooling | +6/-252 |
| `dev/scripts/checks/review_snapshot_freshness/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/review_snapshot_freshness/command.py` | tooling | +260/-0 |
| `dev/scripts/checks/startup_authority_contract/runtime_import_atomicity.py` | tooling | +36/-1 |
| `dev/scripts/checks/startup_authority_contract/runtime_import_git.py` | tooling | +37/-0 |
| `dev/scripts/devctl/commands/check/__init__.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/check_phases.py` | tooling | +0/-13 |
| `dev/scripts/devctl/commands/dashboard_health.py` | tooling | +9/-3 |
| `dev/scripts/devctl/commands/governance/import_findings.py` | tooling | +26/-4 |
| `dev/scripts/devctl/commands/governance/session_resume_authority_payload.py` | tooling | +121/-55 |
| `dev/scripts/devctl/commands/governance/session_resume_render.py` | tooling | +3/-1 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +29/-30 |
| `dev/scripts/devctl/commands/governance/startup_repair_runtime.py` | tooling | +41/-2 |
| `dev/scripts/devctl/commands/reporting/dogfood.py` | tooling | +28/-0 |
| `dev/scripts/devctl/commands/review_channel/_ensure_supervisor.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/review_channel/_reviewer_supervisor_autostart.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/review_channel/_supervisor_restart_policy.py` | tooling | +38/-0 |
| `dev/scripts/devctl/commands/review_channel/bridge_support.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/event_watch_support.py` | tooling | +11/-2 |
| `dev/scripts/devctl/commands/review_channel/status.py` | tooling | +32/-0 |
| `dev/scripts/devctl/commands/vcs/commit.py` | tooling | +34/-217 |
| _115 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 212
- open: 112
- fixed: 86
- false positives: 0

Recent findings:
- `dogfood_finding_id_instability` — `dev/scripts/devctl/runtime/dogfood_log.py` (n/a, verdict=`confirmed_issue`)
- `dogfood_read_only_registration_missing` — `dev/scripts/devctl/cli_parser/entrypoint.py` (n/a, verdict=`confirmed_issue`)
- `finding_backlog_writer_closure_broken` — `dev/scripts/devctl/runtime/finding_backlog.py` (n/a, verdict=`confirmed_issue`)
- `dogfood_governance_pipeline_missing` — `dev/scripts/devctl/runtime/dogfood_log.py` (n/a, verdict=`confirmed_issue`)
- `bridge_authority_conflict` — `bridge.md` (n/a, verdict=`confirmed_issue`)
- `plan_markdown_projection_missing` — `dev/scripts/devctl/platform/planning_ir_models.py` (n/a, verdict=`confirmed_issue`)
- `plan_authority_gap` — `dev/active/MASTER_PLAN.md` (n/a, verdict=`confirmed_issue`)
- `bridge_metadata_parsed_as_authority` — `dev/scripts/devctl/review_channel/handoff.py` (n/a, verdict=`confirmed_issue`)
- `authority_snapshot_3_fields_missing` — `dev/scripts/devctl/runtime/startup_context.py` (n/a, verdict=`fixed`)
- `dogfood.command.startup-context` — `dev/scripts/devctl/commands/governance/startup_context.py` (n/a, verdict=`confirmed_issue`)

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
| `ActionResult` | `governance_runtime` | `n/a` | status, reason |
| `ArtifactStore` | `governance_runtime` | `n/a` | root, managed_kinds |
| `AutoModeState` | `governance_runtime` | `n/a` | phase, next_transition |
| `CallerAuthorityPolicy` | `governance_runtime` | `n/a` | caller_id, allowed_actions |
| `CheckResult` | `governance_runtime` | `n/a` | success, total |
| `ControlPlaneReadModel` | `governance_runtime` | `n/a` | push_eligible, top_blocker |
| `ControlState` | `governance_runtime` | `n/a` | approvals, active_runs |
| `CoordinationSnapshot` | `governance_core` | `n/a` | current_slice, recommended_topology |
| `DecisionPacket` | `governance_runtime` | `n/a` | decision_mode, rule_summary |
| `FailurePacket` | `governance_runtime` | `n/a` | runner, status |
| `Finding` | `governance_runtime` | `n/a` | check_id, severity |
| `LocalServiceEndpoint` | `governance_runtime` | `n/a` | service_id, discovery_fields |
| `ProviderAdapter` | `governance_adapters` | `n/a` | provider_id, capabilities |
| `PushAuthorizationRecord` | `governance_runtime` | `n/a` | authorization_id, authorized_head_sha |
| `RemoteCommitPipelineContract` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:RemoteCommitPipelineContract` | snapshot_id, state |
| `RepoPack` | `repo_packs` | `n/a` | pack_id, policy_path |
| `ReviewCandidateRecord` | `governance_runtime` | `n/a` | candidate_id, artifact_kind |
| `ReviewState` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewState` | snapshot_id, bridge |
| `ReviewerRuntimeContract` | `governance_runtime` | `n/a` | reviewer_mode, reviewer_freshness |
| `RunRecord` | `governance_runtime` | `n/a` | run_id, status |
| `SessionCachePacket` | `governance_commands` | `n/a` | last_reviewed_sha, advisory_action |
| `TypedAction` | `governance_runtime` | `n/a` | action_id, repo_pack_id |
| `WorkflowAdapter` | `governance_adapters` | `n/a` | adapter_id, transport |

### Key documents

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`

## 6. Reviewer hints — please verify

### Targeted hints

- **risk**: Parser / ANSI boundary — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_import_atomicity.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_import_git.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_metadata.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/check_review_snapshot_freshness.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/review_snapshot_freshness/__init__.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/review_snapshot_freshness/command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_check_review_snapshot_freshness.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_git.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_phases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_sections.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/dogfood_models.py`) — Commit f3350f0d changed dev/scripts/devctl/runtime/dogfood_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Commit f3350f0d changed dev/scripts/devctl/tests/checks/test_startup_authority_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit 1bd047a3 changed dev/scripts/devctl/runtime/reviewer_runtime_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/heartbeat_launch_contract.py`) — Commit 0f66c9d8 changed dev/scripts/devctl/review_channel/heartbeat_launch_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/review_channel/test_ack_contract.py`) — Commit 0f66c9d8 changed dev/scripts/devctl/tests/review_channel/test_ack_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`5146e651`** — Refresh external review snapshot for a14356d3
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`a14356d3`** — Fix review-channel launch authority and runtime packet parity
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`bc1b011b`** — Refresh external review snapshot for d599b9b6
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`d599b9b6`** — Fix startup repair authority parity
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`7d35f8e8`** — Refresh external review snapshot for f3350f0d
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`f3350f0d`** — Implement dogfood campaign contract and bound startup authority
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`8b587485`** — Refresh external review snapshot for 5807328b
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`5807328b`** — Harden shim governance and review state parsing
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`2454de6b`** — Refresh external review snapshot for 63ad7200
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`63ad7200`** — Repair event-backed bridge projection parity
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`8dfa6a83`** — Refresh external review snapshot for 0af6b46f
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`0af6b46f`** — Repair bridge poll metadata projection
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`ae95f570`** — Refresh external review snapshot for 1bd047a3
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`1bd047a3`** — Stabilize review-channel authority recovery
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`97054783`** — Refresh external review snapshot for 5304aecb
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`5304aecb`** — Refresh external review snapshot for 0f66c9d8
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`0f66c9d8`** — Stabilize review-channel authority recovery
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`1271a075`** — Refresh external review snapshot for fc86c018
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`fc86c018`** — Mark Q94 fixed in LIVE_RUN
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`9c63556a`** — Refresh external review snapshot for 8d1c30a0
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`8d1c30a0`** — Fail closed on stale dashboard daemon state
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`847adc03`** — Refresh external review snapshot for 5daed3c2
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`5daed3c2`** — Delete redesign_research/ — operator: stop making MDs, use existing master plan + 24 active plans + LIVE_RUN.md
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`acac5ee0`** — Refresh external review snapshot for f5dc6d5e
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`f5dc6d5e`** — Push redesign research bundle for Codex (operator directive 2026-04-15)
  - Operator: "All this needs to be pushed to Codex. It is going to plan and code
  - this. Your job is research and push findings. You are not coding a goddamn line."
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
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

- open governance findings: 112

### Startup advisories
- checkpoint_allowed: worktree_dirty_within_budget

### Stale warnings
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/runtime/dogfood_log.py`): dogfood_finding_id_instability: 
- **governance_open** (`dev/scripts/devctl/cli_parser/entrypoint.py`): dogfood_read_only_registration_missing: 
- **governance_open** (`dev/scripts/devctl/runtime/finding_backlog.py`): finding_backlog_writer_closure_broken: 
- **governance_open** (`dev/scripts/devctl/runtime/dogfood_log.py`): dogfood_governance_pipeline_missing: 
- **governance_open** (`bridge.md`): bridge_authority_conflict: 
- **governance_open** (`dev/scripts/devctl/platform/planning_ir_models.py`): plan_markdown_projection_missing: 
- **governance_open** (`dev/active/MASTER_PLAN.md`): plan_authority_gap: 
- **governance_open** (`dev/scripts/devctl/review_channel/handoff.py`): bridge_metadata_parsed_as_authority: 

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-0879b3bc76de` binds this file to HEAD `5146e65182bf`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
