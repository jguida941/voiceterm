# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `f6daf24ec4dc` — Refresh external review snapshot for 44184fe0
- Tree hash: `bc1e05de4e59`
- Generation stamp: `snap-248cb1aad99f`
- Generated at (UTC): 2026-05-06T11:12:59Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `single_agent`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 36 files, +2101/-1599
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
- HEAD SHA: `f6daf24ec4dcf7d0e0f89efe41f52057db750f3b`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-06T07:11:16-04:00

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
- current_push_authorization: `push-auth-20260506T111000706764Z` (valid=True)
- authorized_head_commit: `f6daf24ec4dcf7d0e0f89efe41f52057db750f3b`
- publication_backlog: recommended
- publication_guidance: 2 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `single_agent`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `f6daf24ec4dc`

- commits: 24
- files changed: 36
- insertions: +2101
- deletions: -1599
- bundle classes touched: docs, tooling
- authority surfaces touched: 3 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `f6daf24e` | Refresh external review snapshot for 44184fe0 | 2 | +77/-85 | docs |  |
| 2 | `44184fe0` | Advance audit-packets continuation | 10 | +169/-93 | tooling |  |
| 3 | `77838451` | Refresh external review snapshot for c6583026 | 2 | +47/-44 | docs |  |
| 4 | `c6583026` | Refresh external review snapshot for d10c973a | 2 | +42/-42 | docs |  |
| 5 | `d10c973a` | Refresh external review snapshot for f5f08da5 | 2 | +50/-49 | docs |  |
| 6 | `f5f08da5` | Refresh external review snapshot for 547141d4 | 2 | +46/-47 | docs |  |
| 7 | `547141d4` | Refresh external review snapshot for d6a683e1 | 2 | +59/-59 | docs |  |
| 8 | `d6a683e1` | Close push preflight guard gaps | 10 | +106/-76 | tooling |  |
| 9 | `926950f0` | Refresh external review snapshot for b2e22dca | 2 | +50/-49 | docs |  |
| 10 | `b2e22dca` | Refresh external review snapshot for 65f4852a | 2 | +46/-46 | docs |  |
| 11 | `65f4852a` | Refresh external review snapshot for 1769a22b | 2 | +75/-74 | docs |  |
| 12 | `1769a22b` | Rename latest push report artifact | 25 | +370/-145 | tooling |  |
| 13 | `bf05ad5d` | Refresh external review snapshot for ed485e2f | 2 | +64/-64 | docs |  |
| 14 | `ed485e2f` | Bound ReviewSnapshot hook refreshes | 10 | +144/-91 | tooling |  |
| 15 | `2a5505b6` | Refresh external review snapshot for 58688059 | 2 | +63/-63 | docs |  |
| 16 | `58688059` | Bound post-commit receipt refresh | 10 | +143/-56 | tooling |  |
| 17 | `ab69857d` | Refresh external review snapshot for fb0fef5d | 2 | +56/-55 | docs |  |
| 18 | `fb0fef5d` | Record role-matrix dogfood disposition | 5 | +95/-71 | tooling |  |
| 19 | `5368bb9b` | Record boot dogfood packet binding | 3 | +6/-4 | tooling |  |
| 20 | `87c24fa1` | Remove Codex boot card surface | 13 | +95/-142 | tooling |  |
| 21 | `830aa787` | Refresh external review snapshot for 4dfd3939 | 2 | +57/-56 | docs |  |
| 22 | `4dfd3939` | Add provider-neutral boot dogfood plan | 8 | +137/-84 | tooling |  |
| 23 | `ed012aee` | Refresh external review snapshot for a3b129ee | 2 | +54/-54 | docs |  |
| 24 | `a3b129ee` | Restore agents contract script mode | 2 | +50/-50 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +6/-2 |
| `bridge.md` | docs | +62/-62 |
| `dev/active/MASTER_PLAN.md` | tooling | +42/-10 |
| `dev/active/ai_governance_platform.md` | tooling | +51/-18 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1330/-1358 |
| `dev/config/devctl_repo_policy.json` | tooling | +0/-45 |
| `dev/config/git_hooks/post-commit-review-snapshot.sh` | tooling | +37/-1 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +37/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +28/-12 |
| `dev/guides/SYSTEM_MAP.md` | docs | +1/-2 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +133/-14 |
| `dev/scripts/README.md` | tooling | +43/-33 |
| `dev/scripts/checks/check_agents_contract.py` | tooling | +0/-0 |
| `dev/scripts/devctl/commands/development/report.py` | tooling | +6/-1 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +3/-1 |
| `dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py` | tooling | +11/-8 |
| `dev/scripts/devctl/commands/vcs/governed_executor_push_result.py` | tooling | +11/-3 |
| `dev/scripts/devctl/commands/vcs/push_artifact.py` | tooling | +34/-4 |
| `dev/scripts/devctl/commands/vcs/push_diagnostics.py` | tooling | +12/-1 |
| `dev/scripts/devctl/commands/vcs/push_flow.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/vcs/push_receipt_failure.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/vcs/push_report.py` | tooling | +8/-2 |
| `dev/scripts/devctl/commands/vcs/push_snapshot.py` | tooling | +2/-0 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +6/-3 |
| `dev/scripts/devctl/repo_packs/voiceterm.py` | tooling | +3/-1 |
| `dev/scripts/devctl/runtime/control_plane_sources.py` | tooling | +22/-2 |
| `dev/scripts/devctl/runtime/dirty_path_filter.py` | tooling | +5/-0 |
| `dev/scripts/devctl/tests/commands/governance/test_install_git_hooks.py` | tooling | +30/-0 |
| `dev/scripts/devctl/tests/commands/test_development_command.py` | tooling | +49/-0 |
| `dev/scripts/devctl/tests/governance/test_render_surfaces.py` | tooling | +3/-3 |
| `dev/scripts/devctl/tests/vcs/test_push.py` | tooling | +31/-10 |
| `dev/scripts/devctl/tests/vcs/test_push_artifact.py` | tooling | +45/-0 |
| `dev/scripts/devctl/tests/vcs/test_push_report.py` | tooling | +41/-0 |
| `dev/state/plan_index.jsonl` | tooling | +5/-0 |
| `dev/state/plan_ingestion_receipts.jsonl` | tooling | +1/-0 |
| `dev/state/plan_source_snapshots.jsonl` | tooling | +1/-0 |

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_push_result.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/checks/check_agents_contract.py`) — Commit a3b129ee changed dev/scripts/checks/check_agents_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`1769a22b`** — Rename latest push report artifact
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`bf05ad5d`** — Refresh external review snapshot for ed485e2f
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`ed485e2f`** — Bound ReviewSnapshot hook refreshes
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`2a5505b6`** — Refresh external review snapshot for 58688059
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`58688059`** — Bound post-commit receipt refresh
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`ab69857d`** — Refresh external review snapshot for fb0fef5d
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`fb0fef5d`** — Record role-matrix dogfood disposition
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`5368bb9b`** — Record boot dogfood packet binding
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`87c24fa1`** — Remove Codex boot card surface
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`830aa787`** — Refresh external review snapshot for 4dfd3939
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`4dfd3939`** — Add provider-neutral boot dogfood plan
  - evolution: Change: renamed the repo-pack canonical latest push report from the generic `dev/reports/push/latest.json` to `dev/reports/push/latest_push_report.json`. The old path remains a legacy read fallback only; new governed pu…
- **`ed012aee`** — Refresh external review snapshot for a3b129ee
  - evolution: Fact: the governed-bypass idea needed to become repair/proof lifecycle state before any execution path could be safe. A raw bypass command or generated markdown plan would have violated the platform authority boundary b…
- **`a3b129ee`** — Restore agents contract script mode
  - evolution: Fact: the governed-bypass idea needed to become repair/proof lifecycle state before any execution path could be safe. A raw bypass command or generated markdown plan would have violated the platform authority boundary b…
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-248cb1aad99f` binds this file to HEAD `f6daf24ec4dc`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
