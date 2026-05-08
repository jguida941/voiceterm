# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `b31a24aa87bf` — Refresh external review snapshot for 82b4bfd3
- Tree hash: `aad5baf6af95`
- Generation stamp: `snap-db606619d89d`
- Generated at (UTC): 2026-05-08T03:53:07Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 64 files, +3787/-1519
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
- HEAD SHA: `b31a24aa87bf980772a910f5a15f7cc18879e71a`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-07T23:50:46-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report_state: `blocked` (push_preflight_running)
- current_push_authorization: `push-auth-20260508T034356184237Z` (valid=True)
- authorized_head_commit: `82b4bfd3a0deb8f279fb9199539d81d8c044af04`
- publication_backlog: urgent
- publication_guidance: 33 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `b31a24aa87bf`

- commits: 24
- files changed: 64
- insertions: +3787
- deletions: -1519
- bundle classes touched: docs, tooling
- authority surfaces touched: 4 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `b31a24aa` | Refresh external review snapshot for 82b4bfd3 | 2 | +60/-61 | docs |  |
| 2 | `82b4bfd3` | Refresh external review snapshot for d98a872c | 2 | +54/-56 | docs |  |
| 3 | `d98a872c` | Refresh push preflight generated surfaces | 2 | +53/-51 | tooling |  |
| 4 | `07a47a09` | Refresh external review snapshot for 14721847 | 2 | +63/-64 | docs |  |
| 5 | `14721847` | Tune governed push preflight timeouts | 10 | +129/-59 | tooling |  |
| 6 | `b12b368d` | Refresh external review snapshot for 783a42be | 2 | +43/-43 | docs |  |
| 7 | `783a42be` | Refresh external review snapshot for fcd130a0 | 2 | +42/-40 | docs |  |
| 8 | `fcd130a0` | Refresh external review snapshot for e44db441 | 2 | +85/-112 | docs |  |
| 9 | `e44db441` | Checkpoint push preflight projections | 3 | +54/-53 | docs |  |
| 10 | `9931921c` | Refresh external review snapshot for 590da1c5 | 2 | +62/-66 | docs |  |
| 11 | `590da1c5` | Improve publication deferral and review projections | 17 | +833/-66 | tooling |  |
| 12 | `91001cfe` | Refresh external review snapshot for 1c730de5 | 2 | +45/-46 | docs |  |
| 13 | `1c730de5` | Refresh external review snapshot for 82b2ff19 | 2 | +42/-41 | docs |  |
| 14 | `82b2ff19` | Refresh external review snapshot for d3be3f32 | 2 | +54/-57 | docs |  |
| 15 | `d3be3f32` | Refresh generated governance surfaces | 3 | +55/-54 | docs |  |
| 16 | `959994de` | Refresh external review snapshot for d7bd8e78 | 2 | +63/-63 | docs |  |
| 17 | `d7bd8e78` | Add checkpoint repair authority lifecycle | 22 | +1025/-109 | tooling |  |
| 18 | `df0f445d` | Refresh external review snapshot for ebd484c1 | 2 | +64/-67 | docs |  |
| 19 | `ebd484c1` | Checkpoint governance lifecycle repairs | 23 | +655/-145 | tooling |  |
| 20 | `55d37a77` | Refresh external review snapshot for 1ea5b46b | 2 | +42/-43 | docs |  |
| 21 | `1ea5b46b` | Refresh external review snapshot for 89fb139b | 2 | +43/-42 | docs |  |
| 22 | `89fb139b` | Refresh external review snapshot for fd14c251 | 2 | +63/-66 | docs |  |
| 23 | `fd14c251` | Ingest guard smartness automation findings | 6 | +96/-49 | tooling |  |
| 24 | `84bb8da1` | Refresh external review snapshot for 3c74fb47 | 2 | +62/-66 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `bridge.md` | docs | +61/-61 |
| `dev/active/MASTER_PLAN.md` | tooling | +11/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1252/-1292 |
| `dev/guides/SYSTEM_MAP.md` | docs | +9/-5 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +31/-0 |
| `dev/scripts/README.md` | tooling | +2/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth.py` | tooling | +58/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop.py` | tooling | +9/-21 |
| `dev/scripts/devctl/cli_parser/quality.py` | tooling | +2/-2 |
| `dev/scripts/devctl/commands/check/router_execution.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/check/router_python_tests.py` | tooling | +2/-1 |
| `dev/scripts/devctl/commands/development/next_slice.py` | tooling | +25/-0 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +6/-0 |
| `dev/scripts/devctl/commands/governance/startup_context_defer.py` | tooling | +110/-1 |
| `dev/scripts/devctl/commands/governance/startup_repair_commit_pipeline.py` | tooling | +73/-0 |
| `dev/scripts/devctl/commands/governance/startup_repair_runtime.py` | tooling | +4/-3 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +2/-32 |
| `dev/scripts/devctl/commands/review_channel/event_queue_report.py` | tooling | +51/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor.py` | tooling | +18/-5 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +5/-1 |
| `dev/scripts/devctl/commands/vcs/push_preflight_timeout.py` | tooling | +45/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_pipeline.py` | tooling | +94/-1 |
| `dev/scripts/devctl/platform/system_map.py` | tooling | +40/-1 |
| `dev/scripts/devctl/review_channel/agent_loop_decision_queue_targets.py` | tooling | +47/-13 |
| `dev/scripts/devctl/review_channel/agent_packet_attention.py` | tooling | +6/-18 |
| `dev/scripts/devctl/review_channel/agent_sync_readers.py` | tooling | +50/-0 |
| `dev/scripts/devctl/review_channel/event_reducer.py` | tooling | +28/-0 |
| `dev/scripts/devctl/review_channel/event_render.py` | tooling | +2/-5 |
| `dev/scripts/devctl/review_channel/event_render_queue.py` | tooling | +26/-0 |
| `dev/scripts/devctl/review_channel/events.py` | tooling | +14/-1 |
| `dev/scripts/devctl/review_channel/packet_loop_attention.py` | tooling | +24/-0 |
| `dev/scripts/devctl/review_channel/projection_bundle.py` | tooling | +11/-6 |
| `dev/scripts/devctl/runtime/action_routing.py` | tooling | +1/-0 |
| `dev/scripts/devctl/runtime/action_routing_publication_defer.py` | tooling | +102/-1 |
| `dev/scripts/devctl/runtime/agent_loop_blocker_actions.py` | tooling | +22/-0 |
| `dev/scripts/devctl/runtime/agent_loop_checkpoint_repair.py` | tooling | +81/-0 |
| `dev/scripts/devctl/runtime/agent_loop_decision_sources.py` | tooling | +19/-17 |
| `dev/scripts/devctl/runtime/agent_loop_decision_support.py` | tooling | +2/-2 |
| `dev/scripts/devctl/runtime/agent_loop_policy.py` | tooling | +20/-10 |
| _24 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/python_test_contract.py`) — Commit 14721847 changed dev/scripts/devctl/runtime/python_test_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/startup_repair_models.py`) — Commit d7bd8e78 changed dev/scripts/devctl/runtime/startup_repair_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit d7bd8e78 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`b31a24aa`** — Refresh external review snapshot for 82b4bfd3
- **`82b4bfd3`** — Refresh external review snapshot for d98a872c
- **`d98a872c`** — Refresh push preflight generated surfaces
- **`07a47a09`** — Refresh external review snapshot for 14721847
- **`14721847`** — Tune governed push preflight timeouts
- **`b12b368d`** — Refresh external review snapshot for 783a42be
- **`783a42be`** — Refresh external review snapshot for fcd130a0
- **`fcd130a0`** — Refresh external review snapshot for e44db441
- **`e44db441`** — Checkpoint push preflight projections
- **`9931921c`** — Refresh external review snapshot for 590da1c5
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-db606619d89d` binds this file to HEAD `b31a24aa87bf`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
