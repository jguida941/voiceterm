# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `d48cf3b41b24` — Refresh external review snapshot for 06e31e4e
- Tree hash: `9ce2f76bd326`
- Generation stamp: `snap-a5e390351971`
- Generated at (UTC): 2026-05-06T19:54:55Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 44 files, +3504/-2219
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
- HEAD SHA: `d48cf3b41b24febda057f2741d547fc30b30efb8`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-06T15:53:05-04:00

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
- current_push_authorization: `push-auth-20260506T194444742607Z` (valid=True)
- authorized_head_commit: `06e31e4ed52cd2101ec35d784f826ea88298f3d7`
- publication_backlog: recommended
- publication_guidance: 3 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `d48cf3b41b24`

- commits: 24
- files changed: 44
- insertions: +3504
- deletions: -2219
- bundle classes touched: docs, tooling

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `d48cf3b4` | Refresh external review snapshot for 06e31e4e | 2 | +49/-52 | docs |  |
| 2 | `06e31e4e` | Refresh external review snapshot for dbaa9ad3 | 2 | +65/-66 | docs |  |
| 3 | `dbaa9ad3` | Ingest packet expiry lifecycle sweep plan | 8 | +129/-69 | tooling |  |
| 4 | `1d065cd2` | Refresh external review snapshot for b75cd4c7 | 1 | +60/-60 | tooling |  |
| 5 | `b75cd4c7` | Refresh external review snapshot for 7a73b299 | 1 | +11/-6 | docs |  |
| 6 | `7a73b299` | Refresh external review snapshot for a90c3aa9 | 2 | +44/-44 | docs |  |
| 7 | `a90c3aa9` | Refresh external review snapshot for 2b535a3c | 2 | +46/-44 | docs |  |
| 8 | `2b535a3c` | Refresh external review snapshot for c4fd1c3e | 2 | +75/-81 | docs |  |
| 9 | `c4fd1c3e` | Ingest universal governance lifecycle plan | 8 | +191/-121 | tooling |  |
| 10 | `af287813` | Refresh external review snapshot for 7b73c670 | 2 | +53/-48 | docs |  |
| 11 | `7b73c670` | Refresh external review snapshot for bca3c2fd | 2 | +49/-52 | docs |  |
| 12 | `bca3c2fd` | Refresh external review snapshot for 34ce6fc1 | 2 | +84/-91 | docs |  |
| 13 | `34ce6fc1` | Stop archived packets blocking live work | 29 | +998/-398 | tooling |  |
| 14 | `f4b6c1ca` | Refresh external review snapshot for d8f090f2 | 2 | +53/-48 | docs |  |
| 15 | `d8f090f2` | Refresh external review snapshot for 2f05dc5a | 2 | +48/-51 | docs |  |
| 16 | `2f05dc5a` | Refresh external review snapshot for e4958183 | 2 | +61/-63 | docs |  |
| 17 | `e4958183` | Record remote-control parity handoff | 2 | +60/-60 | docs |  |
| 18 | `218bb398` | Refresh external review snapshot for 74bfb1c2 | 2 | +52/-47 | docs |  |
| 19 | `74bfb1c2` | Refresh external review snapshot for 3d4ae574 | 2 | +48/-51 | docs |  |
| 20 | `3d4ae574` | Refresh external review snapshot for e08186fa | 2 | +85/-71 | docs |  |
| 21 | `e08186fa` | Fix remote-control packet scope parity | 29 | +1090/-543 | tooling |  |
| 22 | `e13fb3d2` | Refresh external review snapshot for e6a486b1 | 2 | +46/-46 | docs |  |
| 23 | `e6a486b1` | Refresh external review snapshot for f4aa0823 | 2 | +46/-44 | docs |  |
| 24 | `f4aa0823` | Refresh external review snapshot for 17c86a1f | 2 | +61/-63 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +2/-0 |
| `bridge.md` | docs | +160/-160 |
| `dev/active/MASTER_PLAN.md` | tooling | +44/-6 |
| `dev/active/ai_governance_platform.md` | tooling | +72/-23 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1212/-1202 |
| `dev/guides/DEVELOPMENT.md` | docs | +13/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +2/-2 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +80/-0 |
| `dev/scripts/README.md` | tooling | +9/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_instruction.py` | tooling | +87/-12 |
| `dev/scripts/checks/platform_contract_closure/typed_state_writer_authority.py` | tooling | +2/-0 |
| `dev/scripts/checks/review_surface_consistency/bridge_poll_parity.py` | tooling | +61/-0 |
| `dev/scripts/checks/review_surface_consistency/disk_parity.py` | tooling | +123/-0 |
| `dev/scripts/checks/review_surface_consistency/parity.py` | tooling | +29/-441 |
| `dev/scripts/checks/review_surface_consistency/queue_parity.py` | tooling | +57/-0 |
| `dev/scripts/checks/review_surface_consistency/recovery_parity.py` | tooling | +261/-0 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +2/-0 |
| `dev/scripts/devctl/review_channel/current_session_attention.py` | tooling | +3/-29 |
| `dev/scripts/devctl/review_channel/current_session_bridge_state.py` | tooling | +105/-0 |
| `dev/scripts/devctl/review_channel/current_session_checkpoint.py` | tooling | +154/-0 |
| `dev/scripts/devctl/review_channel/current_session_event_state.py` | tooling | +210/-0 |
| `dev/scripts/devctl/review_channel/current_session_packet_normalize.py` | tooling | +4/-2 |
| `dev/scripts/devctl/review_channel/current_session_projection.py` | tooling | +27/-262 |
| `dev/scripts/devctl/review_channel/current_session_queue.py` | tooling | +87/-3 |
| `dev/scripts/devctl/review_channel/current_session_support.py` | tooling | +7/-14 |
| `dev/scripts/devctl/review_channel/event_reducer_inbox.py` | tooling | +1/-15 |
| `dev/scripts/devctl/review_channel/state_status_inputs.py` | tooling | +40/-19 |
| `dev/scripts/devctl/review_channel/status_snapshot_authority.py` | tooling | +26/-1 |
| `dev/scripts/devctl/review_channel/timestamp_parse.py` | tooling | +20/-0 |
| `dev/scripts/devctl/runtime/review_packet_inbox.py` | tooling | +0/-2 |
| `dev/scripts/devctl/runtime/review_packet_inbox_liveness.py` | tooling | +6/-2 |
| `dev/scripts/devctl/runtime/review_packet_inbox_rows.py` | tooling | +9/-1 |
| `dev/scripts/devctl/runtime/runtime_truth_snapshot.py` | tooling | +2/-10 |
| `dev/scripts/devctl/tests/checks/test_check_multi_agent_sync.py` | tooling | +86/-0 |
| `dev/scripts/devctl/tests/checks/test_check_review_surface_consistency.py` | tooling | +27/-0 |
| `dev/scripts/devctl/tests/review_channel/test_current_session_projection.py` | tooling | +266/-0 |
| `dev/scripts/devctl/tests/review_channel/test_state_status_inputs.py` | tooling | +48/-0 |
| `dev/scripts/devctl/tests/review_channel/test_status_snapshot_authority.py` | tooling | +28/-0 |
| `dev/scripts/devctl/tests/runtime/test_development_packet_pressure.py` | tooling | +27/-1 |
| `dev/scripts/devctl/tests/runtime/test_review_packet_inbox.py` | tooling | +27/-0 |
| _4 more files trimmed_ | | |

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

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`d48cf3b4`** — Refresh external review snapshot for 06e31e4e
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`06e31e4e`** — Refresh external review snapshot for dbaa9ad3
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`dbaa9ad3`** — Ingest packet expiry lifecycle sweep plan
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`1d065cd2`** — Refresh external review snapshot for b75cd4c7
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`b75cd4c7`** — Refresh external review snapshot for 7a73b299
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`7a73b299`** — Refresh external review snapshot for a90c3aa9
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`a90c3aa9`** — Refresh external review snapshot for 2b535a3c
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`2b535a3c`** — Refresh external review snapshot for c4fd1c3e
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`c4fd1c3e`** — Ingest universal governance lifecycle plan
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`af287813`** — Refresh external review snapshot for 7b73c670
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`7b73c670`** — Refresh external review snapshot for bca3c2fd
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`bca3c2fd`** — Refresh external review snapshot for 34ce6fc1
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`34ce6fc1`** — Stop archived packets blocking live work
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`f4b6c1ca`** — Refresh external review snapshot for d8f090f2
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`d8f090f2`** — Refresh external review snapshot for 2f05dc5a
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`2f05dc5a`** — Refresh external review snapshot for e4958183
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`e4958183`** — Record remote-control parity handoff
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`218bb398`** — Refresh external review snapshot for 74bfb1c2
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`74bfb1c2`** — Refresh external review snapshot for 3d4ae574
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`3d4ae574`** — Refresh external review snapshot for e08186fa
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`e08186fa`** — Fix remote-control packet scope parity
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`e13fb3d2`** — Refresh external review snapshot for e6a486b1
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`e6a486b1`** — Refresh external review snapshot for f4aa0823
  - evolution: Change: ingested Claude/operator `rev_pkt_3114` as a narrowed plan correction instead of adding a parallel plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request lifecycle checkpoint and commit-seam proof, w…
- **`f4aa0823`** — Refresh external review snapshot for 17c86a1f
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-a5e390351971` binds this file to HEAD `d48cf3b41b24`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
