# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `f4b6c1cae6b7` — Refresh external review snapshot for d8f090f2
- Tree hash: `eb5a8c524e70`
- Generation stamp: `snap-0f3249ab73ef`
- Generated at (UTC): 2026-05-06T18:26:14Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 41 files, +3716/-1982
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
- HEAD SHA: `f4b6c1cae6b77f3dfe8d5cf16282664af4735a90`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-06T13:25:01-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 27
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report_state: `post_push_green` (push_completed)
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
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `f4b6c1cae6b7`

- commits: 24
- files changed: 41
- insertions: +3716
- deletions: -1982
- bundle classes touched: docs, tooling
- authority surfaces touched: 1 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `f4b6c1ca` | Refresh external review snapshot for d8f090f2 | 2 | +53/-48 | docs |  |
| 2 | `d8f090f2` | Refresh external review snapshot for 2f05dc5a | 2 | +48/-51 | docs |  |
| 3 | `2f05dc5a` | Refresh external review snapshot for e4958183 | 2 | +61/-63 | docs |  |
| 4 | `e4958183` | Record remote-control parity handoff | 2 | +60/-60 | docs |  |
| 5 | `218bb398` | Refresh external review snapshot for 74bfb1c2 | 2 | +52/-47 | docs |  |
| 6 | `74bfb1c2` | Refresh external review snapshot for 3d4ae574 | 2 | +48/-51 | docs |  |
| 7 | `3d4ae574` | Refresh external review snapshot for e08186fa | 2 | +85/-71 | docs |  |
| 8 | `e08186fa` | Fix remote-control packet scope parity | 29 | +1090/-543 | tooling |  |
| 9 | `e13fb3d2` | Refresh external review snapshot for e6a486b1 | 2 | +46/-46 | docs |  |
| 10 | `e6a486b1` | Refresh external review snapshot for f4aa0823 | 2 | +46/-44 | docs |  |
| 11 | `f4aa0823` | Refresh external review snapshot for 17c86a1f | 2 | +61/-63 | docs |  |
| 12 | `17c86a1f` | Record remote-control campaign packet | 2 | +54/-54 | docs |  |
| 13 | `111e1de3` | Refresh external review snapshot for 5dee4db9 | 2 | +44/-44 | docs |  |
| 14 | `5dee4db9` | Refresh external review snapshot for 3bf94665 | 2 | +45/-43 | docs |  |
| 15 | `3bf94665` | Refresh external review snapshot for c95aa86b | 2 | +73/-71 | docs |  |
| 16 | `c95aa86b` | Fold exception proof into campaign lane | 18 | +702/-202 | tooling |  |
| 17 | `9d7ae361` | Refresh external review snapshot for a6c1034e | 2 | +49/-48 | docs |  |
| 18 | `a6c1034e` | Refresh external review snapshot for c0796505 | 2 | +48/-49 | docs |  |
| 19 | `c0796505` | Refresh external review snapshot for 2b8397a5 | 2 | +72/-64 | docs |  |
| 20 | `2b8397a5` | Add remote-control pair campaign view | 20 | +722/-84 | tooling |  |
| 21 | `f3489a3c` | Refresh external review snapshot for 26ef3f79 | 2 | +58/-58 | docs |  |
| 22 | `26ef3f79` | Refresh external review snapshot for 32d6f1f2 | 2 | +46/-47 | docs |  |
| 23 | `32d6f1f2` | Refresh external review snapshot for b741a46a | 2 | +62/-62 | docs |  |
| 24 | `b741a46a` | Add measured devctl test timeout override | 10 | +91/-69 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +4/-2 |
| `bridge.md` | docs | +98/-93 |
| `dev/active/MASTER_PLAN.md` | tooling | +23/-4 |
| `dev/active/ai_governance_platform.md` | tooling | +35/-5 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1260/-1231 |
| `dev/guides/DEVELOPMENT.md` | docs | +21/-6 |
| `dev/guides/SYSTEM_MAP.md` | docs | +5/-5 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +54/-6 |
| `dev/scripts/README.md` | tooling | +18/-5 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_instruction.py` | tooling | +87/-12 |
| `dev/scripts/checks/review_surface_consistency/bridge_poll_parity.py` | tooling | +61/-0 |
| `dev/scripts/checks/review_surface_consistency/disk_parity.py` | tooling | +123/-0 |
| `dev/scripts/checks/review_surface_consistency/parity.py` | tooling | +29/-441 |
| `dev/scripts/checks/review_surface_consistency/queue_parity.py` | tooling | +57/-0 |
| `dev/scripts/checks/review_surface_consistency/recovery_parity.py` | tooling | +261/-0 |
| `dev/scripts/devctl/commands/check/router_python_tests.py` | tooling | +12/-1 |
| `dev/scripts/devctl/commands/development/campaign.py` | tooling | +318/-1 |
| `dev/scripts/devctl/commands/development/campaign_exception_proof.py` | tooling | +168/-0 |
| `dev/scripts/devctl/commands/development/models.py` | tooling | +66/-0 |
| `dev/scripts/devctl/commands/development/parser.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/development/render.py` | tooling | +70/-68 |
| `dev/scripts/devctl/commands/development/render_campaign.py` | tooling | +125/-0 |
| `dev/scripts/devctl/commands/development/report.py` | tooling | +21/-1 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +4/-2 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_development.py` | tooling | +83/-69 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_development_campaign.py` | tooling | +157/-0 |
| `dev/scripts/devctl/review_channel/current_session_attention.py` | tooling | +2/-2 |
| `dev/scripts/devctl/review_channel/current_session_packet_normalize.py` | tooling | +4/-2 |
| `dev/scripts/devctl/review_channel/current_session_projection.py` | tooling | +9/-3 |
| `dev/scripts/devctl/review_channel/current_session_queue.py` | tooling | +87/-3 |
| `dev/scripts/devctl/review_channel/current_session_support.py` | tooling | +3/-9 |
| `dev/scripts/devctl/runtime/runtime_truth_snapshot.py` | tooling | +2/-10 |
| `dev/scripts/devctl/tests/checks/test_check_multi_agent_sync.py` | tooling | +86/-0 |
| `dev/scripts/devctl/tests/checks/test_check_review_surface_consistency.py` | tooling | +27/-0 |
| `dev/scripts/devctl/tests/commands/check/test_check_router.py` | tooling | +4/-1 |
| `dev/scripts/devctl/tests/commands/test_development_command.py` | tooling | +183/-0 |
| `dev/scripts/devctl/tests/review_channel/test_current_session_projection.py` | tooling | +101/-0 |
| `dev/scripts/devctl/tests/runtime/test_runtime_truth_snapshot.py` | tooling | +37/-0 |
| `dev/state/plan_index.jsonl` | tooling | +3/-0 |
| `dev/state/plan_ingestion_receipts.jsonl` | tooling | +3/-0 |
| _1 more files trimmed_ | | |

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

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`f4b6c1ca`** — Refresh external review snapshot for d8f090f2
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`d8f090f2`** — Refresh external review snapshot for 2f05dc5a
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`2f05dc5a`** — Refresh external review snapshot for e4958183
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`e4958183`** — Record remote-control parity handoff
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`218bb398`** — Refresh external review snapshot for 74bfb1c2
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`74bfb1c2`** — Refresh external review snapshot for 3d4ae574
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`3d4ae574`** — Refresh external review snapshot for e08186fa
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`e08186fa`** — Fix remote-control packet scope parity
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`e13fb3d2`** — Refresh external review snapshot for e6a486b1
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`e6a486b1`** — Refresh external review snapshot for f4aa0823
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`f4aa0823`** — Refresh external review snapshot for 17c86a1f
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`17c86a1f`** — Record remote-control campaign packet
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`111e1de3`** — Refresh external review snapshot for 5dee4db9
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`5dee4db9`** — Refresh external review snapshot for 3bf94665
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`3bf94665`** — Refresh external review snapshot for c95aa86b
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`c95aa86b`** — Fold exception proof into campaign lane
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`9d7ae361`** — Refresh external review snapshot for a6c1034e
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`a6c1034e`** — Refresh external review snapshot for c0796505
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`c0796505`** — Refresh external review snapshot for 2b8397a5
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`2b8397a5`** — Add remote-control pair campaign view
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`f3489a3c`** — Refresh external review snapshot for 26ef3f79
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`26ef3f79`** — Refresh external review snapshot for 32d6f1f2
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`32d6f1f2`** — Refresh external review snapshot for b741a46a
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`b741a46a`** — Add measured devctl test timeout override
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
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
- checkpoint_before_continue: staged_index_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-0f3249ab73ef` binds this file to HEAD `f4b6c1cae6b7`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
