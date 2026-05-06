# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `f3489a3c1986` — Refresh external review snapshot for 26ef3f79
- Tree hash: `625f4bc37347`
- Generation stamp: `snap-5b4fd8dc9a3e`
- Generated at (UTC): 2026-05-06T14:39:50Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 13 files, +1543/-1438
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
- HEAD SHA: `f3489a3c1986ffcdda4aef3f049ee27947338ef4`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-06T09:24:58-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 18
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

Range: last 24 commits ending at `f3489a3c1986`

- commits: 24
- files changed: 13
- insertions: +1543
- deletions: -1438
- bundle classes touched: docs, tooling
- authority surfaces touched: 1 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `f3489a3c` | Refresh external review snapshot for 26ef3f79 | 2 | +58/-58 | docs |  |
| 2 | `26ef3f79` | Refresh external review snapshot for 32d6f1f2 | 2 | +46/-47 | docs |  |
| 3 | `32d6f1f2` | Refresh external review snapshot for b741a46a | 2 | +62/-62 | docs |  |
| 4 | `b741a46a` | Add measured devctl test timeout override | 10 | +91/-69 | tooling |  |
| 5 | `aed37390` | Refresh external review snapshot for c831b36a | 2 | +60/-77 | docs |  |
| 6 | `c831b36a` | Refresh external review snapshot for f6ab7bf7 | 2 | +47/-48 | docs |  |
| 7 | `f6ab7bf7` | Refresh external review snapshot for 9e3f7098 | 2 | +60/-62 | docs |  |
| 8 | `9e3f7098` | Split focused devctl router tests | 10 | +107/-100 | tooling |  |
| 9 | `3769a6c2` | Refresh external review snapshot for 72116dde | 2 | +54/-55 | docs |  |
| 10 | `72116dde` | Refresh external review snapshot for e21cd117 | 2 | +45/-43 | docs |  |
| 11 | `e21cd117` | Refresh external review snapshot for 850a2a7e | 2 | +63/-66 | docs |  |
| 12 | `850a2a7e` | Serialize focused devctl test add-on | 10 | +79/-74 | tooling |  |
| 13 | `c696409b` | Refresh external review snapshot for 88d16d7d | 2 | +55/-57 | docs |  |
| 14 | `88d16d7d` | Refresh external review snapshot for e30be54e | 2 | +44/-42 | docs |  |
| 15 | `e30be54e` | Refresh external review snapshot for 03be7736 | 2 | +66/-67 | docs |  |
| 16 | `03be7736` | Raise focused devctl test timeout floor | 10 | +83/-59 | tooling |  |
| 17 | `847dc839` | Refresh external review snapshot for 7a1c5131 | 2 | +46/-48 | docs |  |
| 18 | `7a1c5131` | Refresh external review snapshot for f6daf24e | 2 | +46/-44 | docs |  |
| 19 | `f6daf24e` | Refresh external review snapshot for 44184fe0 | 2 | +77/-85 | docs |  |
| 20 | `44184fe0` | Advance audit-packets continuation | 10 | +169/-93 | tooling |  |
| 21 | `77838451` | Refresh external review snapshot for c6583026 | 2 | +47/-44 | docs |  |
| 22 | `c6583026` | Refresh external review snapshot for d10c973a | 2 | +42/-42 | docs |  |
| 23 | `d10c973a` | Refresh external review snapshot for f5f08da5 | 2 | +50/-49 | docs |  |
| 24 | `f5f08da5` | Refresh external review snapshot for 547141d4 | 2 | +46/-47 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +5/-3 |
| `bridge.md` | docs | +44/-44 |
| `dev/active/MASTER_PLAN.md` | tooling | +27/-15 |
| `dev/active/ai_governance_platform.md` | tooling | +5/-4 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1255/-1299 |
| `dev/guides/DEVELOPMENT.md` | docs | +17/-11 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +61/-22 |
| `dev/scripts/README.md` | tooling | +15/-7 |
| `dev/scripts/devctl/commands/check/router_python_tests.py` | tooling | +26/-21 |
| `dev/scripts/devctl/commands/development/report.py` | tooling | +6/-1 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +6/-3 |
| `dev/scripts/devctl/tests/commands/check/test_check_router.py` | tooling | +27/-8 |
| `dev/scripts/devctl/tests/commands/test_development_command.py` | tooling | +49/-0 |

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

- **`f3489a3c`** — Refresh external review snapshot for 26ef3f79
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`26ef3f79`** — Refresh external review snapshot for 32d6f1f2
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`32d6f1f2`** — Refresh external review snapshot for b741a46a
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`b741a46a`** — Add measured devctl test timeout override
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`aed37390`** — Refresh external review snapshot for c831b36a
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`c831b36a`** — Refresh external review snapshot for f6ab7bf7
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`f6ab7bf7`** — Refresh external review snapshot for 9e3f7098
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`9e3f7098`** — Split focused devctl router tests
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`3769a6c2`** — Refresh external review snapshot for 72116dde
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`72116dde`** — Refresh external review snapshot for e21cd117
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`e21cd117`** — Refresh external review snapshot for 850a2a7e
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`850a2a7e`** — Serialize focused devctl test add-on
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`c696409b`** — Refresh external review snapshot for 88d16d7d
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`88d16d7d`** — Refresh external review snapshot for e30be54e
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`e30be54e`** — Refresh external review snapshot for 03be7736
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`03be7736`** — Raise focused devctl test timeout floor
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`847dc839`** — Refresh external review snapshot for 7a1c5131
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`7a1c5131`** — Refresh external review snapshot for f6daf24e
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`f6daf24e`** — Refresh external review snapshot for 44184fe0
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`44184fe0`** — Advance audit-packets continuation
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`77838451`** — Refresh external review snapshot for c6583026
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`c6583026`** — Refresh external review snapshot for d10c973a
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`d10c973a`** — Refresh external review snapshot for f5f08da5
  - evolution: Change: added the read-only `devctl develop campaign` surface and the `RemoteControlCollaborationCampaign` platform contract. The report projects the Codex/Claude remote-control campaign from existing typed state: role …
- **`f5f08da5`** — Refresh external review snapshot for 547141d4
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-5b4fd8dc9a3e` binds this file to HEAD `f3489a3c1986`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
