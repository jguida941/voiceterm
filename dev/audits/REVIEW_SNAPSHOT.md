# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `590da1c50f89` — Improve publication deferral and review projections
- Tree hash: `b666a367fc29`
- Generation stamp: `snap-bd68b01af045`
- Generated at (UTC): 2026-05-08T01:52:37Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 205 files, +13070/-4019
- Governance findings: 158 open / 88 fixed / 260 total
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
- HEAD SHA: `590da1c50f897027a7fe00acdb8e814fc8a98190`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-07T21:51:52-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: urgent
- publication_guidance: 23 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `tools_only`
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
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `590da1c50f89`

- commits: 24
- files changed: 205
- insertions: +13070
- deletions: -4019
- bundle classes touched: docs, tooling
- authority surfaces touched: 31 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `590da1c5` | Improve publication deferral and review projections | 17 | +833/-66 | tooling |  |
| 2 | `91001cfe` | Refresh external review snapshot for 1c730de5 | 2 | +45/-46 | docs |  |
| 3 | `1c730de5` | Refresh external review snapshot for 82b2ff19 | 2 | +42/-41 | docs |  |
| 4 | `82b2ff19` | Refresh external review snapshot for d3be3f32 | 2 | +54/-57 | docs |  |
| 5 | `d3be3f32` | Refresh generated governance surfaces | 3 | +55/-54 | docs |  |
| 6 | `959994de` | Refresh external review snapshot for d7bd8e78 | 2 | +63/-63 | docs |  |
| 7 | `d7bd8e78` | Add checkpoint repair authority lifecycle | 22 | +1025/-109 | tooling |  |
| 8 | `df0f445d` | Refresh external review snapshot for ebd484c1 | 2 | +64/-67 | docs |  |
| 9 | `ebd484c1` | Checkpoint governance lifecycle repairs | 23 | +655/-145 | tooling |  |
| 10 | `55d37a77` | Refresh external review snapshot for 1ea5b46b | 2 | +42/-43 | docs |  |
| 11 | `1ea5b46b` | Refresh external review snapshot for 89fb139b | 2 | +43/-42 | docs |  |
| 12 | `89fb139b` | Refresh external review snapshot for fd14c251 | 2 | +63/-66 | docs |  |
| 13 | `fd14c251` | Ingest guard smartness automation findings | 6 | +96/-49 | tooling |  |
| 14 | `84bb8da1` | Refresh external review snapshot for 3c74fb47 | 2 | +62/-66 | docs |  |
| 15 | `3c74fb47` | Fix checkpoint retry restaging | 15 | +147/-67 | tooling |  |
| 16 | `533fb308` | Automate checkpoint staging and next selection | 21 | +637/-101 | tooling |  |
| 17 | `d10257cd` | Refresh external review snapshot for 42addd24 | 2 | +56/-58 | docs |  |
| 18 | `42addd24` | Fix develop next typed plan selection | 6 | +196/-63 | tooling |  |
| 19 | `7482406d` | Refresh external review snapshot for ba581203 | 2 | +55/-55 | docs |  |
| 20 | `ba581203` | Refresh external review snapshot for 3d532df6 | 2 | +76/-77 | docs |  |
| 21 | `3d532df6` | Refresh policy-owned generated surfaces for 95a1050e | 1 | +2/-2 | docs |  |
| 22 | `95a1050e` | Refresh external review snapshot for 78741171 | 2 | +123/-95 | docs |  |
| 23 | `78741171` | Checkpoint packet intake and role authority repairs | 159 | +8583/-2539 | tooling |  |
| 24 | `e3f17d25` | Refresh external review snapshot for d48cf3b4 | 2 | +53/-48 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `AGENTS.md` | docs | +4/-0 |
| `bridge.md` | docs | +109/-109 |
| `dev/active/MASTER_PLAN.md` | tooling | +46/-1 |
| `dev/active/ai_governance_platform.md` | tooling | +24/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1249/-1229 |
| `dev/config/launchd/review_channel_publisher_service.py` | tooling | +12/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +33/-6 |
| `dev/guides/SYSTEM_MAP.md` | docs | +12/-8 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +104/-4 |
| `dev/scripts/README.md` | tooling | +28/-0 |
| `dev/scripts/checks/check_devctl_cold_boot.py` | tooling | +12/-0 |
| `dev/scripts/checks/devctl_cold_boot/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/devctl_cold_boot/command.py` | tooling | +68/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth.py` | tooling | +58/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop.py` | tooling | +9/-21 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_instruction.py` | tooling | +53/-2 |
| `dev/scripts/checks/review_channel_bridge/report.py` | tooling | +8/-0 |
| `dev/scripts/checks/review_channel_bridge/typed_state.py` | tooling | +93/-5 |
| `dev/scripts/devctl/commands/check/router_python_tests.py` | tooling | +29/-0 |
| `dev/scripts/devctl/commands/development/next_slice.py` | tooling | +227/-5 |
| `dev/scripts/devctl/commands/development/packet_attention.py` | tooling | +85/-169 |
| `dev/scripts/devctl/commands/development/packet_attention_actionable.py` | tooling | +51/-0 |
| `dev/scripts/devctl/commands/development/packet_attention_commands.py` | tooling | +34/-0 |
| `dev/scripts/devctl/commands/development/packet_attention_lifecycle.py` | tooling | +129/-0 |
| `dev/scripts/devctl/commands/development/packet_attention_support.py` | tooling | +169/-0 |
| `dev/scripts/devctl/commands/development/packet_attention_types.py` | tooling | +37/-0 |
| `dev/scripts/devctl/commands/development/plan_intake.py` | tooling | +82/-79 |
| `dev/scripts/devctl/commands/development/plan_intake_render.py` | tooling | +101/-0 |
| `dev/scripts/devctl/commands/development/plan_intake_sources.py` | tooling | +45/-0 |
| `dev/scripts/devctl/commands/development/report.py` | tooling | +23/-7 |
| `dev/scripts/devctl/commands/development/watcher/clock.py` | tooling | +3/-13 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +6/-0 |
| `dev/scripts/devctl/commands/governance/startup_context_defer.py` | tooling | +110/-1 |
| `dev/scripts/devctl/commands/governance/startup_context_render.py` | tooling | +36/-0 |
| `dev/scripts/devctl/commands/governance/startup_repair_commit_pipeline.py` | tooling | +73/-0 |
| `dev/scripts/devctl/commands/governance/startup_repair_runtime.py` | tooling | +4/-3 |
| `dev/scripts/devctl/commands/review_channel/_publisher.py` | tooling | +44/-0 |
| `dev/scripts/devctl/commands/review_channel/_recover.py` | tooling | +7/-1 |
| `dev/scripts/devctl/commands/review_channel/_render_bridge.py` | tooling | +30/-25 |
| _165 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 260
- open: 158
- fixed: 88
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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_git.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_index_lock.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_managed_projection.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_phases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_prepare.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_handler.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_interaction_mode.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_launch_control.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_launch_headless.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_launch_observe.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_render.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_scope.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_session_build.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_stale_refresh.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_success_report.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_packet_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_session_owner.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_gate.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/startup_repair_models.py`) — Commit d7bd8e78 changed dev/scripts/devctl/runtime/startup_repair_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit d7bd8e78 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/python_test_contract.py`) — Commit 42addd24 changed dev/scripts/devctl/runtime/python_test_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Commit 78741171 changed dev/scripts/devctl/review_channel/reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/startup_context_models.py`) — Commit 78741171 changed dev/scripts/devctl/runtime/startup_context_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`590da1c5`** — Improve publication deferral and review projections
- **`91001cfe`** — Refresh external review snapshot for 1c730de5
- **`1c730de5`** — Refresh external review snapshot for 82b2ff19
- **`82b2ff19`** — Refresh external review snapshot for d3be3f32
- **`d3be3f32`** — Refresh generated governance surfaces
- **`959994de`** — Refresh external review snapshot for d7bd8e78
- **`d7bd8e78`** — Add checkpoint repair authority lifecycle
- **`df0f445d`** — Refresh external review snapshot for ebd484c1
- **`ebd484c1`** — Checkpoint governance lifecycle repairs
- **`55d37a77`** — Refresh external review snapshot for 1ea5b46b
- **`1ea5b46b`** — Refresh external review snapshot for 89fb139b
- **`89fb139b`** — Refresh external review snapshot for fd14c251
- **`fd14c251`** — Ingest guard smartness automation findings
- **`84bb8da1`** — Refresh external review snapshot for 3c74fb47
- **`3c74fb47`** — Fix checkpoint retry restaging
- **`533fb308`** — Automate checkpoint staging and next selection
- **`d10257cd`** — Refresh external review snapshot for 42addd24
- **`42addd24`** — Fix develop next typed plan selection
- **`7482406d`** — Refresh external review snapshot for ba581203
- **`ba581203`** — Refresh external review snapshot for 3d532df6
- **`3d532df6`** — Refresh policy-owned generated surfaces for 95a1050e
- **`95a1050e`** — Refresh external review snapshot for 78741171
- **`78741171`** — Checkpoint packet intake and role authority repairs
- **`e3f17d25`** — Refresh external review snapshot for d48cf3b4
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
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
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-bd68b01af045` binds this file to HEAD `590da1c50f89`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
