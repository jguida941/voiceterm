# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `dda60185b806` — Fix role topology push preflight blockers
- Tree hash: `cabdca9ca64d`
- Generation stamp: `snap-0bf7b27bf4f0`
- Generated at (UTC): 2026-05-09T15:02:02Z
- Push decision: `await_review` — review_loop_relaunch_required
- Reviewer mode: `tools_only` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 233 files, +10175/-3392
- Governance findings: 158 open / 66 fixed / 238 total
- Probe hints: 0 total across 0 files scanned

## 1. Identity

- Repository: **VoiceTerm**
- Product thesis: This is the product thesis for the governance stack in this repository.
Absorb these four commitments before engaging with SOP, guard, routing,
or plan detail — they explain why the process exists.

This repo builds a portable AI governance platform proven through one
production client (VoiceTerm, a Rust voice-first terminal overlay for AI
CLIs). The product thesis is that executable local control — guards,
probes, typed actions, deterministic policy resolution — is what m...
- Remote: `https://github.com/jguida941/voiceterm.git`
- Default branch: `master`
- Current branch: `feature/governance-quality-sweep`
- HEAD SHA: `dda60185b8060d391971c97b58704fa1b0936d05`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-09T11:01:22-04:00

## 2. Governance state

### Push decision
- action: `await_review`
- reason: review_loop_relaunch_required
- push_eligible_now: False
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: urgent
- publication_guidance: 15 local commit(s) waiting for governed push once review is accepted.

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `remote_control`
- implementation_blocked: yes — review_loop_relaunch_required

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `repair_reviewer_loop` — review_loop_relaunch_required

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `dda60185b806`

- commits: 24
- files changed: 233
- insertions: +10175
- deletions: -3392
- bundle classes touched: docs, tooling
- authority surfaces touched: 30 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `dda60185` | Fix role topology push preflight blockers | 13 | +211/-91 | tooling |  |
| 2 | `6ebd631e` | Make review topology role-based | 41 | +1303/-421 | tooling |  |
| 3 | `2164a20f` | Refresh external review snapshot for afafb9c1 | 2 | +54/-55 | docs |  |
| 4 | `afafb9c1` | Refresh external review snapshot for 8845a49e | 2 | +68/-67 | docs |  |
| 5 | `8845a49e` | Refresh external review snapshot for eb9a1578 | 2 | +54/-56 | docs |  |
| 6 | `eb9a1578` | Sync generated surfaces for governed push | 3 | +58/-57 | docs |  |
| 7 | `f5d30b58` | Refresh external review snapshot for d13e587e | 2 | +95/-86 | docs |  |
| 8 | `d13e587e` | Checkpoint packet pressure and validation scope repair | 122 | +3531/-1229 | tooling |  |
| 9 | `5ae52585` | Refresh system map after validation scope modules | 2 | +74/-71 | tooling |  |
| 10 | `4dffbed7` | Thread validation scope through push preflight | 32 | +960/-204 | tooling |  |
| 11 | `c2b8d6ec` | Fix push preflight scope propagation | 6 | +138/-68 | tooling |  |
| 12 | `f8b8d50c` | Refresh policy-owned generated surfaces for f8ca0325 | 1 | +1/-1 | docs |  |
| 13 | `f8ca0325` | Fix governed push validation scope | 16 | +918/-214 | tooling |  |
| 14 | `18c1db4b` | Refresh policy-owned generated surfaces for 3ce8a67d | 1 | +5/-5 | docs |  |
| 15 | `3ce8a67d` | Fix governed commit staged snapshot validation | 14 | +404/-72 | tooling |  |
| 16 | `a196ba90` | Wire session-liveness running-process check + scope reviewe… | 14 | +324/-93 | tooling |  |
| 17 | `b6a74ca6` | Wire actor-scope into TASK_COMPLETE + filter anchor kinds f… | 18 | +334/-97 | tooling |  |
| 18 | `314cb439` | Add SessionTerminationPolicy + TaskCompleteDecision typed c… | 25 | +826/-95 | tooling |  |
| 19 | `d31f125b` | Refresh plan_index + MASTER_PLAN bindings + bridge typed-st… | 4 | +79/-67 | tooling |  |
| 20 | `7a797932` | Refresh external review snapshot for 7f4f1eac | 2 | +74/-75 | docs |  |
| 21 | `7f4f1eac` | Land T22AN-AC: typed wake-packet observations (CommandClass… | 14 | +513/-118 | tooling |  |
| 22 | `0fb675ca` | Refresh external review snapshot for a1cb556e | 2 | +41/-40 | docs |  |
| 23 | `a1cb556e` | Refresh external review snapshot for 00c06f24 | 2 | +42/-39 | docs |  |
| 24 | `00c06f24` | Refresh external review snapshot for ff62a305 | 2 | +68/-71 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +4/-1 |
| `app/operator_console/state/bridge/bridge_heading_aliases.py` | tooling | +75/-0 |
| `app/operator_console/state/bridge/lane_builder.py` | tooling | +31/-56 |
| `app/operator_console/state/bridge/lane_live_trace.py` | tooling | +47/-0 |
| `app/operator_console/state/sessions/session_builder.py` | tooling | +22/-4 |
| `app/operator_console/state/snapshots/snapshot_builder.py` | tooling | +14/-6 |
| `app/operator_console/tests/state/test_state_modules.py` | tooling | +1/-1 |
| `bridge.md` | docs | +142/-141 |
| `dev/README.md` | docs | +1/-1 |
| `dev/active/MASTER_PLAN.md` | tooling | +78/-1 |
| `dev/active/ai_governance_platform.md` | tooling | +32/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1280/-1237 |
| `dev/guides/DEVELOPMENT.md` | docs | +25/-3 |
| `dev/guides/SYSTEM_MAP.md` | docs | +15/-15 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +85/-1 |
| `dev/scripts/README.md` | tooling | +32/-12 |
| `dev/scripts/checks/contract_connectivity/findings.py` | tooling | +15/-1 |
| `dev/scripts/checks/multi_agent_sync/command.py` | tooling | +18/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop.py` | tooling | +6/-1 |
| `dev/scripts/checks/platform_contract_closure/emitter_parity.py` | tooling | +7/-0 |
| `dev/scripts/checks/review_channel_bridge/command.py` | tooling | +20/-1 |
| `dev/scripts/checks/review_channel_bridge/report.py` | tooling | +8/-8 |
| `dev/scripts/checks/review_surface_consistency/command.py` | tooling | +14/-0 |
| `dev/scripts/checks/startup_authority_contract/command.py` | tooling | +17/-0 |
| `dev/scripts/checks/startup_authority_contract/runtime_import_atomicity.py` | tooling | +2/-1 |
| `dev/scripts/checks/startup_authority_contract/runtime_import_git.py` | tooling | +25/-0 |
| `dev/scripts/checks/startup_authority_contract/runtime_import_staged.py` | tooling | +96/-0 |
| `dev/scripts/checks/system_picture_freshness/command.py` | tooling | +15/-0 |
| `dev/scripts/checks/tandem_consistency/command.py` | tooling | +14/-0 |
| `dev/scripts/checks/tandem_consistency/implementer_checks.py` | tooling | +13/-8 |
| `dev/scripts/checks/tandem_consistency/operator_checks.py` | tooling | +4/-1 |
| `dev/scripts/checks/tandem_consistency/support.py` | tooling | +11/-7 |
| `dev/scripts/checks/tandem_consistency/system_checks.py` | tooling | +5/-3 |
| `dev/scripts/devctl/cli_parser/builders_checks.py` | tooling | +16/-0 |
| `dev/scripts/devctl/cli_parser/builders_docs_reporting.py` | tooling | +9/-0 |
| `dev/scripts/devctl/cli_parser/quality.py` | tooling | +17/-0 |
| `dev/scripts/devctl/commands/check/__init__.py` | tooling | +7/-0 |
| `dev/scripts/devctl/commands/check/commit_snapshot.py` | tooling | +35/-0 |
| `dev/scripts/devctl/commands/check/router.py` | tooling | +43/-10 |
| `dev/scripts/devctl/commands/check/router_plan.py` | tooling | +29/-11 |
| _193 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 238
- open: 158
- fixed: 66
- false positives: 0

Recent findings:
- `dogfood.command.orchestrate-watch` — `dev/scripts/devctl/commands/governance/orchestrate_watch.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.integrations-import` — `dev/scripts/devctl/commands/integrations_import.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.governance-export` — `dev/scripts/devctl/commands/governance/export.py` (n/a, verdict=`confirmed_issue`)
- `packet.transition_session_disambiguation` — `dev/scripts/devctl/review_channel/instruction_transitions.py` (critical, verdict=`confirmed_issue`)
- `packet.durable_ingestion_before_ttl` — `dev/scripts/devctl/runtime/packet_carry_forward.py` (critical, verdict=`confirmed_issue`)
- `agent_sync.ambiguity_projection` — `dev/scripts/checks/multi_agent_sync` (high, verdict=`confirmed_issue`)
- `review_channel.command_latency_under_fanout` — `dev/scripts/devctl/commands/review_channel` (high, verdict=`confirmed_issue`)
- `work_board.rows_duplication` — `dev/scripts/devctl/runtime/agent_dispatch_router.py` (high, verdict=`confirmed_issue`)
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_tests.py` (n/a, verdict=`confirmed_issue`)

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
| `RemoteCommitPipelineContract` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:RemoteCommitPipelineContract` | snapshot_id, state |
| `ReviewState` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewState` | snapshot_id, bridge |

### Key documents

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`

## 6. Reviewer hints — please verify

### Targeted hints

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_guard_summary.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_recovery_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_trigger_gate.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_duty_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_duty_identity.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_duty_proof.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_parser.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_push_decision.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_heading_aliases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_metadata.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_sections.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_sanitize.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_validation_stall.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_import_atomicity.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_import_git.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_import_staged.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_follow_recovery_models.py`) — Commit 6ebd631e changed dev/scripts/devctl/review_channel/reviewer_follow_recovery_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Commit 6ebd631e changed dev/scripts/devctl/review_channel/reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_collaboration_models.py`) — Commit 6ebd631e changed dev/scripts/devctl/runtime/review_state_collaboration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit 6ebd631e changed dev/scripts/devctl/runtime/reviewer_runtime_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py`) — Commit 6ebd631e changed dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/bridge_projection_contract.py`) — Commit d13e587e changed dev/scripts/devctl/review_channel/bridge_projection_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit d13e587e changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/development_packet_pressure_models.py`) — Commit d13e587e changed dev/scripts/devctl/runtime/development_packet_pressure_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_packet_models.py`) — Commit d13e587e changed dev/scripts/devctl/runtime/review_state_packet_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/review_channel/test_ack_contract.py`) — Commit d13e587e changed dev/scripts/devctl/tests/review_channel/test_ack_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Commit 3ce8a67d changed dev/scripts/devctl/tests/checks/test_startup_authority_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit 314cb439 changed dev/scripts/devctl/review_channel/packet_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/governance/session_orientation_models.py`) — Commit 7f4f1eac changed dev/scripts/devctl/commands/governance/session_orientation_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`dda60185`** — Fix role topology push preflight blockers
- **`6ebd631e`** — Make review topology role-based
- **`2164a20f`** — Refresh external review snapshot for afafb9c1
- **`afafb9c1`** — Refresh external review snapshot for 8845a49e
- **`8845a49e`** — Refresh external review snapshot for eb9a1578
- **`eb9a1578`** — Sync generated surfaces for governed push
- **`f5d30b58`** — Refresh external review snapshot for d13e587e
- **`d13e587e`** — Checkpoint packet pressure and validation scope repair
- **`5ae52585`** — Refresh system map after validation scope modules
- **`4dffbed7`** — Thread validation scope through push preflight
- **`c2b8d6ec`** — Fix push preflight scope propagation
- **`f8b8d50c`** — Refresh policy-owned generated surfaces for f8ca0325
- **`f8ca0325`** — Fix governed push validation scope
- **`18c1db4b`** — Refresh policy-owned generated surfaces for 3ce8a67d
- **`3ce8a67d`** — Fix governed commit staged snapshot validation
- **`a196ba90`** — Wire session-liveness running-process check + scope reviewer-targeted action_request
  - Closes the F21 stale-evidence-as-liveness pattern at the launch path
  - (running conductor process now treated as live even when prepared launch
  - authority is stale) and the packet-lifecycle state-sync gap where
  - evolution: Change: Codex session completion no longer depends on packet body prose such as "leave pending" to keep a conductor alive after `TASK_COMPLETE`. `SessionTerminationPolicy` names the allowed termination mode, session act…
- **`b6a74ca6`** — Wire actor-scope into TASK_COMPLETE + filter anchor kinds from loop attention
  - Closes rev_pkt_3245 (continuation_anchor actor-scope) and the kind-filter
  - bug demonstrated by claude refresh anchors being acked as transport-receipts.
  - evolution: Change: Codex session completion no longer depends on packet body prose such as "leave pending" to keep a conductor alive after `TASK_COMPLETE`. `SessionTerminationPolicy` names the allowed termination mode, session act…
- **`314cb439`** — Add SessionTerminationPolicy + TaskCompleteDecision typed contracts
  - Defines the typed shapes that gate session-end behavior:
  - - SessionTerminationPolicy with end_on_task_complete / keep_awake_via_packets / session_end_when_anchor_drained modes
  - - TaskCompleteDecision recording termination intent + next_command + anchor reference
  - evolution: Change: Codex session completion no longer depends on packet body prose such as "leave pending" to keep a conductor alive after `TASK_COMPLETE`. `SessionTerminationPolicy` names the allowed termination mode, session act…
- **`d31f125b`** — Refresh plan_index + MASTER_PLAN bindings + bridge typed-state churn (raw bypass with --no-verify per operator authorization to break stuck-pipeline cascade)
  - evolution: Change: Codex session completion no longer depends on packet body prose such as "leave pending" to keep a conductor alive after `TASK_COMPLETE`. `SessionTerminationPolicy` names the allowed termination mode, session act…
- **`7a797932`** — Refresh external review snapshot for 7f4f1eac
  - evolution: Change: Codex session completion no longer depends on packet body prose such as "leave pending" to keep a conductor alive after `TASK_COMPLETE`. `SessionTerminationPolicy` names the allowed termination mode, session act…
- **`7f4f1eac`** — Land T22AN-AC: typed wake-packet observations (CommandClassification + scoped_operator_override_command + override-vocab constants + suppress_artifact_writes default)
  - evolution: Change: Codex session completion no longer depends on packet body prose such as "leave pending" to keep a conductor alive after `TASK_COMPLETE`. `SessionTerminationPolicy` names the allowed termination mode, session act…
- **`0fb675ca`** — Refresh external review snapshot for a1cb556e
  - evolution: Change: Codex session completion no longer depends on packet body prose such as "leave pending" to keep a conductor alive after `TASK_COMPLETE`. `SessionTerminationPolicy` names the allowed termination mode, session act…
- **`a1cb556e`** — Refresh external review snapshot for 00c06f24
  - evolution: Change: Codex session completion no longer depends on packet body prose such as "leave pending" to keep a conductor alive after `TASK_COMPLETE`. `SessionTerminationPolicy` names the allowed termination mode, session act…
- **`00c06f24`** — Refresh external review snapshot for ff62a305
  - evolution: Change: Codex session completion no longer depends on packet body prose such as "leave pending" to keep a conductor alive after `TASK_COMPLETE`. `SessionTerminationPolicy` names the allowed termination mode, session act…
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/autonomous_governance_loop_v2.md` MP-377): headless
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b ev…
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:

## 8. Known gaps and open items

- open governance findings: 158

### Startup advisories
- repair_reviewer_loop: review_loop_relaunch_required

### Stale warnings
- Cut a checkpoint before doing anything else.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/governance/orchestrate_watch.py`): dogfood.command.orchestrate-watch: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/integrations_import.py`): dogfood.command.integrations-import: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/export.py`): dogfood.command.governance-export: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/review_channel/instruction_transitions.py`): packet.transition_session_disambiguation: source_packet_ids=rev_pkt_2691,rev_pkt_2696,rev_pkt_2705; Claude beta finding: transition_packet ack/apply/dismiss paths bypass session disambiguation, allowing cross-session packet actions. Durable owner: MP377-GUARDIR-TRANSITION-DISAMBIGUATION.
- **governance_open** (`dev/scripts/devctl/runtime/packet_carry_forward.py`): packet.durable_ingestion_before_ttl: source_packet_ids=rev_pkt_2691,rev_pkt_2696,rev_pkt_2697,rev_pkt_2699,rev_pkt_2700,rev_pkt_2701,rev_pkt_2702,rev_pkt_2704,rev_pkt_2705; packets are transport/provenance only, so packet-carried work must be promoted into PlanRow/FindingReview/GuardPromotionCandidate/knowledge state before TTL expiry. Durable owner: MP377-GUARDIR-PACKET-DURABLE-INGESTION.
- **governance_open** (`dev/scripts/checks/multi_agent_sync`): agent_sync.ambiguity_projection: source_packet_ids=rev_pkt_2697,rev_pkt_2705; canonical_active_packet_ambiguity can render empty while ambiguity exists, and expired-but-pending split state creates carry-forward debt. Durable owner: MP377-GUARDIR-AGENT-SYNC-AMBIGUITY-CARRYFORWARD.
- **governance_open** (`dev/scripts/devctl/commands/review_channel`): review_channel.command_latency_under_fanout: source_packet_ids=rev_pkt_2704,rev_pkt_2705; review-channel post and startup-context can hang under multi-agent load, tied to process-cleanup and detached sleep pressure. Durable owner: MP377-GUARDIR-FANOUT-COMMAND-HANGS.
- **governance_open** (`dev/scripts/devctl/runtime/agent_dispatch_router.py`): work_board.rows_duplication: source_packet_ids=rev_pkt_2700,rev_pkt_2705; _work_board_rows logic is duplicated between packet_route_resolution.py and agent_dispatch_router.py. Durable owner: MP377-GUARDIR-WORK-BOARD-ROUTE-DEDUP.

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-0bf7b27bf4f0` binds this file to HEAD `dda60185b806`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
