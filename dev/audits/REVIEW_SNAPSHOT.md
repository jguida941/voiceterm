# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `c831b36a85cd` — Refresh external review snapshot for f6ab7bf7
- Tree hash: `796449ae33c8`
- Generation stamp: `snap-05107690adab`
- Generated at (UTC): 2026-05-06T12:49:51Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 14 files, +1562/-1429
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
- HEAD SHA: `c831b36a85cde7adca387e242d687bba457c29dc`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-06T08:48:30-04:00

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
- publication_backlog: urgent
- publication_guidance: 15 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `c831b36a85cd`

- commits: 24
- files changed: 14
- insertions: +1562
- deletions: -1429
- bundle classes touched: docs, tooling
- authority surfaces touched: 1 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `c831b36a` | Refresh external review snapshot for f6ab7bf7 | 2 | +47/-48 | docs |  |
| 2 | `f6ab7bf7` | Refresh external review snapshot for 9e3f7098 | 2 | +60/-62 | docs |  |
| 3 | `9e3f7098` | Split focused devctl router tests | 10 | +107/-100 | tooling |  |
| 4 | `3769a6c2` | Refresh external review snapshot for 72116dde | 2 | +54/-55 | docs |  |
| 5 | `72116dde` | Refresh external review snapshot for e21cd117 | 2 | +45/-43 | docs |  |
| 6 | `e21cd117` | Refresh external review snapshot for 850a2a7e | 2 | +63/-66 | docs |  |
| 7 | `850a2a7e` | Serialize focused devctl test add-on | 10 | +79/-74 | tooling |  |
| 8 | `c696409b` | Refresh external review snapshot for 88d16d7d | 2 | +55/-57 | docs |  |
| 9 | `88d16d7d` | Refresh external review snapshot for e30be54e | 2 | +44/-42 | docs |  |
| 10 | `e30be54e` | Refresh external review snapshot for 03be7736 | 2 | +66/-67 | docs |  |
| 11 | `03be7736` | Raise focused devctl test timeout floor | 10 | +83/-59 | tooling |  |
| 12 | `847dc839` | Refresh external review snapshot for 7a1c5131 | 2 | +46/-48 | docs |  |
| 13 | `7a1c5131` | Refresh external review snapshot for f6daf24e | 2 | +46/-44 | docs |  |
| 14 | `f6daf24e` | Refresh external review snapshot for 44184fe0 | 2 | +77/-85 | docs |  |
| 15 | `44184fe0` | Advance audit-packets continuation | 10 | +169/-93 | tooling |  |
| 16 | `77838451` | Refresh external review snapshot for c6583026 | 2 | +47/-44 | docs |  |
| 17 | `c6583026` | Refresh external review snapshot for d10c973a | 2 | +42/-42 | docs |  |
| 18 | `d10c973a` | Refresh external review snapshot for f5f08da5 | 2 | +50/-49 | docs |  |
| 19 | `f5f08da5` | Refresh external review snapshot for 547141d4 | 2 | +46/-47 | docs |  |
| 20 | `547141d4` | Refresh external review snapshot for d6a683e1 | 2 | +59/-59 | docs |  |
| 21 | `d6a683e1` | Close push preflight guard gaps | 10 | +106/-76 | tooling |  |
| 22 | `926950f0` | Refresh external review snapshot for b2e22dca | 2 | +50/-49 | docs |  |
| 23 | `b2e22dca` | Refresh external review snapshot for 65f4852a | 2 | +46/-46 | docs |  |
| 24 | `65f4852a` | Refresh external review snapshot for 1769a22b | 2 | +75/-74 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +5/-2 |
| `bridge.md` | docs | +47/-47 |
| `dev/active/MASTER_PLAN.md` | tooling | +25/-11 |
| `dev/active/ai_governance_platform.md` | tooling | +8/-4 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1273/-1299 |
| `dev/guides/DEVELOPMENT.md` | docs | +19/-11 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +68/-16 |
| `dev/scripts/README.md` | tooling | +18/-8 |
| `dev/scripts/devctl/commands/check/router_python_tests.py` | tooling | +14/-20 |
| `dev/scripts/devctl/commands/development/report.py` | tooling | +6/-1 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +6/-2 |
| `dev/scripts/devctl/runtime/control_plane_sources.py` | tooling | +1/-1 |
| `dev/scripts/devctl/tests/commands/check/test_check_router.py` | tooling | +23/-7 |
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

- **`c831b36a`** — Refresh external review snapshot for f6ab7bf7
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`f6ab7bf7`** — Refresh external review snapshot for 9e3f7098
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`9e3f7098`** — Split focused devctl router tests
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`3769a6c2`** — Refresh external review snapshot for 72116dde
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`72116dde`** — Refresh external review snapshot for e21cd117
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`e21cd117`** — Refresh external review snapshot for 850a2a7e
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`850a2a7e`** — Serialize focused devctl test add-on
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`c696409b`** — Refresh external review snapshot for 88d16d7d
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`88d16d7d`** — Refresh external review snapshot for e30be54e
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`e30be54e`** — Refresh external review snapshot for 03be7736
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`03be7736`** — Raise focused devctl test timeout floor
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`847dc839`** — Refresh external review snapshot for 7a1c5131
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`7a1c5131`** — Refresh external review snapshot for f6daf24e
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`f6daf24e`** — Refresh external review snapshot for 44184fe0
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`44184fe0`** — Advance audit-packets continuation
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`77838451`** — Refresh external review snapshot for c6583026
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`c6583026`** — Refresh external review snapshot for d10c973a
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`d10c973a`** — Refresh external review snapshot for f5f08da5
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`f5f08da5`** — Refresh external review snapshot for 547141d4
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`547141d4`** — Refresh external review snapshot for d6a683e1
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`d6a683e1`** — Close push preflight guard gaps
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`926950f0`** — Refresh external review snapshot for b2e22dca
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`b2e22dca`** — Refresh external review snapshot for 65f4852a
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`65f4852a`** — Refresh external review snapshot for 1769a22b
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-05107690adab` binds this file to HEAD `c831b36a85cd`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
