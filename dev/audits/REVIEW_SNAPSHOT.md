# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `a59a819893a4` — Add OperationalSummaryView readable packet projection
- Tree hash: `98866a963098`
- Generation stamp: `snap-651575dcc755`
- Generated at (UTC): 2026-05-13T05:16:22Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 77 files, +5980/-4072
- Governance findings: 43 open / 0 fixed / 43 total
- Probe hints: 0 total across 0 files scanned

## 1. Identity

- Repository: **VoiceTerm**
- Product thesis: This is the product thesis for the governance stack in this repository.
Absorb these four commitments before engaging with SOP, guard, routing,
or plan detail — they explain why the process exists.

This repo builds a portable AI governance platform proven through one
production client (VoiceTerm...
- Remote: `https://github.com/jguida941/voiceterm.git`
- Default branch: `master`
- Current branch: `feature/governance-quality-sweep`
- HEAD SHA: `a59a819893a4567f8af2a7c92cc9c1d8127c3b83`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-13T01:15:51-04:00

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
- publication_guidance: 7 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `remote_control`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `a59a819893a4`

- commits: 24
- files changed: 77
- insertions: +5980
- deletions: -4072
- bundle classes touched: tooling, docs
- authority surfaces touched: 2 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `a59a8198` | Add OperationalSummaryView readable packet projection | 6 | +659/-2 | tooling |  |
| 2 | `3f38220f` | Refresh external review snapshot for 36a1a87b | 2 | +66/-66 | docs |  |
| 3 | `36a1a87b` | Honor docs-check generated surface aliases | 11 | +177/-60 | tooling |  |
| 4 | `ee552370` | Refresh external review snapshot for f0d0b9db | 2 | +64/-64 | docs |  |
| 5 | `f0d0b9db` | Improve governance CLI dogfood ergonomics | 12 | +129/-55 | tooling |  |
| 6 | `63ce7cbe` | Refresh external review snapshot for 3e9b18d8 | 2 | +56/-55 | docs |  |
| 7 | `3e9b18d8` | Record post-push governance updates | 3 | +87/-56 | docs |  |
| 8 | `47b6ac17` | Refresh external review snapshot for 285123c6 | 2 | +52/-52 | docs |  |
| 9 | `285123c6` | chore(push): auto-commit preflight-generated changes | 1 | +61/-0 | docs |  |
| 10 | `10c86a85` | Refresh external review snapshot for 63e6af81 | 2 | +68/-62 | docs |  |
| 11 | `63e6af81` | Update governed executor projection path test | 5 | +96/-59 | tooling |  |
| 12 | `5734839a` | Refresh external review snapshot for 5340d350 | 2 | +60/-60 | docs |  |
| 13 | `5340d350` | Register Claude automation safety declaration | 3 | +102/-49 | tooling |  |
| 14 | `80fbb684` | Refresh external review snapshot for b4acaba1 | 2 | +58/-66 | docs |  |
| 15 | `b4acaba1` | Allow review-only action requests through commit gate | 4 | +202/-102 | tooling |  |
| 16 | `2135698e` | Refresh external review snapshot for d700ecb9 | 2 | +57/-57 | docs |  |
| 17 | `d700ecb9` | Reuse CLI command handler rows | 2 | +59/-70 | tooling |  |
| 18 | `2aac05ed` | Refresh external review snapshot for aaf17ee5 | 2 | +63/-67 | docs |  |
| 19 | `aaf17ee5` | Reduce orchestration adapter parameter surfaces | 5 | +92/-153 | tooling |  |
| 20 | `376cd632` | Refresh policy-owned generated surfaces for 7f3a73c8 | 1 | +2/-2 | docs |  |
| 21 | `7f3a73c8` | Refresh external review snapshot for a1c11da2 | 2 | +70/-69 | docs |  |
| 22 | `a1c11da2` | Split governance modules for code shape compliance | 42 | +3643/-2792 | tooling |  |
| 23 | `a9415b9a` | Refresh policy-owned generated surfaces for 7e006123 | 1 | +1/-1 | docs |  |
| 24 | `7e006123` | Refresh external review snapshot for 8d5bb18a | 2 | +56/-53 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +58/-58 |
| `codesmells.md` | docs | +162/-0 |
| `dev/active/CLAUDE_SESSION_AUTOMATION_SAFETY_DECLARATION.md` | tooling | +52/-0 |
| `dev/active/INDEX.md` | tooling | +1/-0 |
| `dev/active/MASTER_PLAN.md` | tooling | +11/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +10/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1155/-1176 |
| `dev/config/devctl_repo_policy.json` | tooling | +5/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +4/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +3/-3 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +34/-1 |
| `dev/scripts/README.md` | tooling | +8/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop.py` | tooling | +6/-101 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_focus.py` | tooling | +46/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_pending.py` | tooling | +67/-0 |
| `dev/scripts/devctl/cli.py` | tooling | +1/-12 |
| `dev/scripts/devctl/commands/check/router_resolve.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/development/final_response_gate.py` | tooling | +20/-285 |
| `dev/scripts/devctl/commands/development/final_response_gate_agent_loop.py` | tooling | +293/-0 |
| `dev/scripts/devctl/commands/development/orchestration_agent_loop.py` | tooling | +2/-14 |
| `dev/scripts/devctl/commands/development/orchestration_agent_loop_rows.py` | tooling | +4/-32 |
| `dev/scripts/devctl/commands/development/orchestration_inputs.py` | tooling | +2/-14 |
| `dev/scripts/devctl/commands/development/parser.py` | tooling | +5/-160 |
| `dev/scripts/devctl/commands/development/parser_collaboration.py` | tooling | +204/-0 |
| `dev/scripts/devctl/commands/development/report.py` | tooling | +2/-228 |
| `dev/scripts/devctl/commands/development/report_assembly.py` | tooling | +252/-0 |
| `dev/scripts/devctl/commands/development/report_assembly_collaboration.py` | tooling | +104/-0 |
| `dev/scripts/devctl/commands/development/report_assembly_final.py` | tooling | +92/-0 |
| `dev/scripts/devctl/commands/docs/check.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/docs/check_runtime.py` | tooling | +22/-3 |
| `dev/scripts/devctl/commands/review_channel/bridge_render.py` | tooling | +6/-0 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +19/-0 |
| `dev/scripts/devctl/governance/push_policy.py` | tooling | +1/-0 |
| `dev/scripts/devctl/governance/push_policy_parse.py` | tooling | +2/-0 |
| `dev/scripts/devctl/governance/push_routing.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/agent_loop_decision_projection.py` | tooling | +11/-8 |
| `dev/scripts/devctl/review_channel/agent_loop_decision_queue_source.py` | tooling | +57/-0 |
| `dev/scripts/devctl/review_channel/agent_loop_decision_queue_targets.py` | tooling | +13/-225 |
| `dev/scripts/devctl/review_channel/agent_loop_decision_route_scope.py` | tooling | +184/-0 |
| `dev/scripts/devctl/review_channel/agent_packet_attention.py` | tooling | +23/-314 |
| _37 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 43
- open: 43
- fixed: 0
- false positives: 0

Recent findings:
- `packet.transition_session_disambiguation` — `dev/scripts/devctl/review_channel/instruction_transitions.py` (critical, verdict=`confirmed_issue`)
- `packet.durable_ingestion_before_ttl` — `dev/scripts/devctl/runtime/packet_carry_forward.py` (critical, verdict=`confirmed_issue`)
- `agent_sync.ambiguity_projection` — `dev/scripts/checks/multi_agent_sync` (high, verdict=`confirmed_issue`)
- `review_channel.command_latency_under_fanout` — `dev/scripts/devctl/commands/review_channel` (high, verdict=`confirmed_issue`)
- `work_board.rows_duplication` — `dev/scripts/devctl/runtime/agent_dispatch_router.py` (high, verdict=`confirmed_issue`)
- `dogfood.command.process-audit` — `dev/scripts/devctl/commands/process/audit.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_tests.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_test_runner/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-cleanup` — `dev/scripts/devctl/commands/process/cleanup.py` (n/a, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_render.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`a59a8198`** — Add OperationalSummaryView readable packet projection
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`3f38220f`** — Refresh external review snapshot for 36a1a87b
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`36a1a87b`** — Honor docs-check generated surface aliases
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`ee552370`** — Refresh external review snapshot for f0d0b9db
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`f0d0b9db`** — Improve governance CLI dogfood ergonomics
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`63ce7cbe`** — Refresh external review snapshot for 3e9b18d8
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`3e9b18d8`** — Record post-push governance updates
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`47b6ac17`** — Refresh external review snapshot for 285123c6
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`285123c6`** — chore(push): auto-commit preflight-generated changes
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`10c86a85`** — Refresh external review snapshot for 63e6af81
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`63e6af81`** — Update governed executor projection path test
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`5734839a`** — Refresh external review snapshot for 5340d350
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`5340d350`** — Register Claude automation safety declaration
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`80fbb684`** — Refresh external review snapshot for b4acaba1
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`b4acaba1`** — Allow review-only action requests through commit gate
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`2135698e`** — Refresh external review snapshot for d700ecb9
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`d700ecb9`** — Reuse CLI command handler rows
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`2aac05ed`** — Refresh external review snapshot for aaf17ee5
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`aaf17ee5`** — Reduce orchestration adapter parameter surfaces
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`376cd632`** — Refresh policy-owned generated surfaces for 7f3a73c8
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`7f3a73c8`** — Refresh external review snapshot for a1c11da2
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`a1c11da2`** — Split governance modules for code shape compliance
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`a9415b9a`** — Refresh policy-owned generated surfaces for 7e006123
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`7e006123`** — Refresh external review snapshot for 8d5bb18a
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- 2026-05-11 slice 18 fix arc + bilateral protocol consolidation (MP-377):
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b ev…
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:

## 8. Known gaps and open items

- open governance findings: 43

### Startup advisories
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/review_channel/instruction_transitions.py`): packet.transition_session_disambiguation: source_packet_ids=rev_pkt_2691,rev_pkt_2696,rev_pkt_2705; Claude beta finding: transition_packet ack/apply/dismiss paths bypass session disambiguation, allowing cross-session packet actions. Durable owner: MP377-GUARDIR-TRANSITION-DISAMBIGUATION.
- **governance_open** (`dev/scripts/devctl/runtime/packet_carry_forward.py`): packet.durable_ingestion_before_ttl: source_packet_ids=rev_pkt_2691,rev_pkt_2696,rev_pkt_2697,rev_pkt_2699,rev_pkt_2700,rev_pkt_2701,rev_pkt_2702,rev_pkt_2704,rev_pkt_2705; packets are transport/provenance only, so packet-carried work must be promoted into PlanRow/FindingReview/GuardPromotionCandidate/knowledge state before TTL expiry. Durable owner: MP377-GUARDIR-PACKET-DURABLE-INGESTION.
- **governance_open** (`dev/scripts/checks/multi_agent_sync`): agent_sync.ambiguity_projection: source_packet_ids=rev_pkt_2697,rev_pkt_2705; canonical_active_packet_ambiguity can render empty while ambiguity exists, and expired-but-pending split state creates carry-forward debt. Durable owner: MP377-GUARDIR-AGENT-SYNC-AMBIGUITY-CARRYFORWARD.
- **governance_open** (`dev/scripts/devctl/commands/review_channel`): review_channel.command_latency_under_fanout: source_packet_ids=rev_pkt_2704,rev_pkt_2705; review-channel post and startup-context can hang under multi-agent load, tied to process-cleanup and detached sleep pressure. Durable owner: MP377-GUARDIR-FANOUT-COMMAND-HANGS.
- **governance_open** (`dev/scripts/devctl/runtime/agent_dispatch_router.py`): work_board.rows_duplication: source_packet_ids=rev_pkt_2700,rev_pkt_2705; _work_board_rows logic is duplicated between packet_route_resolution.py and agent_dispatch_router.py. Durable owner: MP377-GUARDIR-WORK-BOARD-ROUTE-DEDUP.
- **governance_open** (`dev/scripts/devctl/commands/process/audit.py`): dogfood.command.process-audit: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/reports_cleanup.py`): dogfood.command.reports-cleanup: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/python_tests.py`): dogfood.command.test-python: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-651575dcc755` binds this file to HEAD `a59a819893a4`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
