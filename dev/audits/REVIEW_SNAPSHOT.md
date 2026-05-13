# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `5340d35019c4` — Register Claude automation safety declaration
- Tree hash: `d2dea636dd15`
- Generation stamp: `snap-8f684cc44025`
- Generated at (UTC): 2026-05-13T02:10:39Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 64 files, +5654/-4513
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
- HEAD SHA: `5340d35019c404ffb5cf6030c4ad1016675f2f13`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-12T22:09:50-04:00

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
- publication_guidance: 37 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `5340d35019c4`

- commits: 24
- files changed: 64
- insertions: +5654
- deletions: -4513
- bundle classes touched: tooling, docs

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `5340d350` | Register Claude automation safety declaration | 3 | +102/-49 | tooling |  |
| 2 | `80fbb684` | Refresh external review snapshot for b4acaba1 | 2 | +58/-66 | docs |  |
| 3 | `b4acaba1` | Allow review-only action requests through commit gate | 4 | +202/-102 | tooling |  |
| 4 | `2135698e` | Refresh external review snapshot for d700ecb9 | 2 | +57/-57 | docs |  |
| 5 | `d700ecb9` | Reuse CLI command handler rows | 2 | +59/-70 | tooling |  |
| 6 | `2aac05ed` | Refresh external review snapshot for aaf17ee5 | 2 | +63/-67 | docs |  |
| 7 | `aaf17ee5` | Reduce orchestration adapter parameter surfaces | 5 | +92/-153 | tooling |  |
| 8 | `376cd632` | Refresh policy-owned generated surfaces for 7f3a73c8 | 1 | +2/-2 | docs |  |
| 9 | `7f3a73c8` | Refresh external review snapshot for a1c11da2 | 2 | +70/-69 | docs |  |
| 10 | `a1c11da2` | Split governance modules for code shape compliance | 42 | +3643/-2792 | tooling |  |
| 11 | `a9415b9a` | Refresh policy-owned generated surfaces for 7e006123 | 1 | +1/-1 | docs |  |
| 12 | `7e006123` | Refresh external review snapshot for 8d5bb18a | 2 | +56/-53 | docs |  |
| 13 | `8d5bb18a` | Checkpoint listing package projections | 4 | +51/-49 | tooling |  |
| 14 | `32545d54` | Package devctl list command | 4 | +221/-242 | tooling |  |
| 15 | `cdc5b9a1` | Refresh policy-owned generated surfaces for f91cbada | 1 | +1/-1 | docs |  |
| 16 | `f91cbada` | Refresh external review snapshot for 725c000d | 2 | +57/-57 | docs |  |
| 17 | `725c000d` | Allow shared schema fixture roots | 6 | +455/-319 | tooling |  |
| 18 | `97992ae2` | Refresh external review snapshot for 81f85b53 | 2 | +54/-54 | docs |  |
| 19 | `81f85b53` | Checkpoint live packet projections | 4 | +49/-47 | tooling |  |
| 20 | `454b6230` | Refresh ground truth probe receipt | 2 | +51/-50 | tooling |  |
| 21 | `eddba7ea` | Refresh external review snapshot for 555fa483 | 2 | +56/-56 | docs |  |
| 22 | `555fa483` | Checkpoint push bypass packet projections | 3 | +50/-46 | tooling |  |
| 23 | `05adb548` | Allow publish-clear managed projection receipts | 5 | +145/-52 | tooling |  |
| 24 | `c41a0250` | Refresh external review snapshot for c536d666 | 2 | +59/-59 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +38/-38 |
| `codesmells.md` | docs | +39/-0 |
| `dev/active/CLAUDE_SESSION_AUTOMATION_SAFETY_DECLARATION.md` | tooling | +52/-0 |
| `dev/active/INDEX.md` | tooling | +1/-0 |
| `dev/active/MASTER_PLAN.md` | tooling | +5/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1185/-1241 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +3/-2 |
| `dev/guides/SYSTEM_MAP.md` | docs | +5/-5 |
| `dev/scripts/checks/check_schema_fixture_handshake.py` | tooling | +8/-266 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop.py` | tooling | +6/-101 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_focus.py` | tooling | +46/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_pending.py` | tooling | +67/-0 |
| `dev/scripts/checks/schema_fixture_handshake/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/schema_fixture_handshake/command.py` | tooling | +302/-0 |
| `dev/scripts/devctl/cli.py` | tooling | +1/-12 |
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
| `dev/scripts/devctl/commands/listing.py` | tooling | +6/-136 |
| `dev/scripts/devctl/commands/listing/__init__.py` | tooling | +137/-0 |
| `dev/scripts/devctl/review_channel/agent_loop_decision_projection.py` | tooling | +11/-8 |
| `dev/scripts/devctl/review_channel/agent_loop_decision_queue_source.py` | tooling | +57/-0 |
| `dev/scripts/devctl/review_channel/agent_loop_decision_queue_targets.py` | tooling | +13/-225 |
| `dev/scripts/devctl/review_channel/agent_loop_decision_route_scope.py` | tooling | +184/-0 |
| `dev/scripts/devctl/review_channel/agent_packet_attention.py` | tooling | +23/-314 |
| `dev/scripts/devctl/review_channel/agent_packet_attention_body.py` | tooling | +21/-0 |
| `dev/scripts/devctl/review_channel/agent_packet_attention_priority.py` | tooling | +102/-0 |
| `dev/scripts/devctl/review_channel/agent_packet_attention_scope.py` | tooling | +177/-0 |
| `dev/scripts/devctl/review_channel/packet_target_runtime.py` | tooling | +156/-0 |
| `dev/scripts/devctl/review_channel/packet_target_validation.py` | tooling | +9/-102 |
| `dev/scripts/devctl/runtime/agent_loop_context_builder.py` | tooling | +166/-0 |
| `dev/scripts/devctl/runtime/agent_loop_decision.py` | tooling | +91/-42 |
| _24 more files trimmed_ | | |

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

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`8d5bb18a`** — Checkpoint listing package projections
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`32545d54`** — Package devctl list command
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`cdc5b9a1`** — Refresh policy-owned generated surfaces for f91cbada
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`f91cbada`** — Refresh external review snapshot for 725c000d
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`725c000d`** — Allow shared schema fixture roots
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`97992ae2`** — Refresh external review snapshot for 81f85b53
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`81f85b53`** — Checkpoint live packet projections
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`454b6230`** — Refresh ground truth probe receipt
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`eddba7ea`** — Refresh external review snapshot for 555fa483
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`555fa483`** — Checkpoint push bypass packet projections
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`05adb548`** — Allow publish-clear managed projection receipts
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`c41a0250`** — Refresh external review snapshot for c536d666
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-8f684cc44025` binds this file to HEAD `5340d35019c4`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
