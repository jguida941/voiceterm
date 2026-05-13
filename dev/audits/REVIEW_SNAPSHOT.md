# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `c912d41bcb6b` — Append McGilchrist speaker bio to Priority 102 ERROR-FORMAT SPEC
- Tree hash: `5123d27b68c6`
- Generation stamp: `snap-b87b70d50f0d`
- Generated at (UTC): 2026-05-13T06:47:57Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 55 files, +4562/-965
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
- HEAD SHA: `c912d41bcb6b7deda03a4a973a8efc7141786205`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-13T02:47:28-04:00

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
- publication_backlog: queued
- publication_guidance: 1 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `c912d41bcb6b`

- commits: 24
- files changed: 55
- insertions: +4562
- deletions: -965
- bundle classes touched: docs, tooling
- authority surfaces touched: 2 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `c912d41b` | Append McGilchrist speaker bio to Priority 102 ERROR-FORMAT… | 2 | +3/-1 | docs |  |
| 2 | `e0204888` | Refresh external review snapshot for ea524877 | 2 | +73/-68 | docs |  |
| 3 | `ea524877` | Record P102 typestate research synthesis + session-end state | 4 | +324/-4 | docs |  |
| 4 | `676766de` | Surface packet guard-error lifecycle details | 11 | +633/-29 | tooling |  |
| 5 | `6f16325d` | Add review-channel command freshness metadata | 8 | +335/-8 | tooling |  |
| 6 | `c910beb7` | Add typed security and Rust audit report contracts | 10 | +325/-46 | tooling |  |
| 7 | `029384fc` | Refresh external review snapshot for f216a49b | 2 | +62/-62 | docs |  |
| 8 | `f216a49b` | Separate read-only status command and runtime readiness | 6 | +158/-3 | tooling |  |
| 9 | `b6511619` | Refresh external review snapshot for 26377459 | 2 | +52/-52 | docs |  |
| 10 | `26377459` | Add PeerAwarenessPolicy contract and body-observation oracl… | 10 | +868/-0 | tooling |  |
| 11 | `6fb64ce4` | Refresh external review snapshot for a59a8198 | 2 | +52/-52 | docs |  |
| 12 | `a59a8198` | Add OperationalSummaryView readable packet projection | 6 | +659/-2 | tooling |  |
| 13 | `3f38220f` | Refresh external review snapshot for 36a1a87b | 2 | +66/-66 | docs |  |
| 14 | `36a1a87b` | Honor docs-check generated surface aliases | 11 | +177/-60 | tooling |  |
| 15 | `ee552370` | Refresh external review snapshot for f0d0b9db | 2 | +64/-64 | docs |  |
| 16 | `f0d0b9db` | Improve governance CLI dogfood ergonomics | 12 | +129/-55 | tooling |  |
| 17 | `63ce7cbe` | Refresh external review snapshot for 3e9b18d8 | 2 | +56/-55 | docs |  |
| 18 | `3e9b18d8` | Record post-push governance updates | 3 | +87/-56 | docs |  |
| 19 | `47b6ac17` | Refresh external review snapshot for 285123c6 | 2 | +52/-52 | docs |  |
| 20 | `285123c6` | chore(push): auto-commit preflight-generated changes | 1 | +61/-0 | docs |  |
| 21 | `10c86a85` | Refresh external review snapshot for 63e6af81 | 2 | +68/-62 | docs |  |
| 22 | `63e6af81` | Update governed executor projection path test | 5 | +96/-59 | tooling |  |
| 23 | `5734839a` | Refresh external review snapshot for 5340d350 | 2 | +60/-60 | docs |  |
| 24 | `5340d350` | Register Claude automation safety declaration | 3 | +102/-49 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +60/-60 |
| `codesmells.md` | docs | +439/-0 |
| `dev/active/CLAUDE_SESSION_AUTOMATION_SAFETY_DECLARATION.md` | tooling | +52/-0 |
| `dev/active/INDEX.md` | tooling | +1/-0 |
| `dev/active/MASTER_PLAN.md` | tooling | +13/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +43/-8 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +820/-808 |
| `dev/config/devctl_repo_policy.json` | tooling | +5/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +4/-0 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +34/-1 |
| `dev/scripts/README.md` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/agent_mind/peer_awareness.py` | tooling | +120/-0 |
| `dev/scripts/devctl/commands/agent_mind/renderers.py` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/agent_mind/slice_builder.py` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/check/router_resolve.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/docs/check.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/docs/check_runtime.py` | tooling | +22/-3 |
| `dev/scripts/devctl/commands/review_channel/bridge_render.py` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +20/-0 |
| `dev/scripts/devctl/commands/review_channel/status.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/status_readiness.py` | tooling | +158/-1 |
| `dev/scripts/devctl/commands/security.py` | tooling | +24/-20 |
| `dev/scripts/devctl/governance/push_policy.py` | tooling | +1/-0 |
| `dev/scripts/devctl/governance/push_policy_parse.py` | tooling | +2/-0 |
| `dev/scripts/devctl/governance/push_routing.py` | tooling | +1/-0 |
| `dev/scripts/devctl/platform/artifact_schema_rows.py` | tooling | +26/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows.py` | tooling | +198/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_review.py` | tooling | +96/-0 |
| `dev/scripts/devctl/review_channel/event_render.py` | tooling | +73/-2 |
| `dev/scripts/devctl/review_channel/packet_lifecycle.py` | tooling | +68/-25 |
| `dev/scripts/devctl/review_channel/packet_lifecycle_disposition.py` | tooling | +44/-2 |
| `dev/scripts/devctl/review_channel/parser_argument_groups.py` | tooling | +12/-1 |
| `dev/scripts/devctl/review_channel/parser_query_arguments.py` | tooling | +9/-0 |
| `dev/scripts/devctl/review_channel/readable_packet_projection.py` | tooling | +594/-5 |
| `dev/scripts/devctl/runtime/__init__.py` | tooling | +18/-0 |
| `dev/scripts/devctl/runtime/agent_mind_slice.py` | tooling | +2/-0 |
| `dev/scripts/devctl/runtime/audit_report_contracts.py` | tooling | +104/-0 |
| `dev/scripts/devctl/runtime/packet_guard_errors.py` | tooling | +234/-0 |
| `dev/scripts/devctl/runtime/peer_awareness_policy.py` | tooling | +329/-0 |
| `dev/scripts/devctl/rust_audit/render.py` | tooling | +13/-0 |
| _15 more files trimmed_ | | |

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
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit 676766de changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/audit_report_contracts.py`) — Commit c910beb7 changed dev/scripts/devctl/runtime/audit_report_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`c912d41b`** — Append McGilchrist speaker bio to Priority 102 ERROR-FORMAT SPEC
  - Tarides/Ambiata OCaml-Haskell-Idris engineer; talk archive cite.
  - Bridge.md projection refresh after codex liveness expiration.
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`e0204888`** — Refresh external review snapshot for ea524877
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`ea524877`** — Record P102 typestate research synthesis + session-end state
  - 5-agent + 3-Rust-hint research consolidated into Priority 102 entries
  - in codesmells.md (SLSA+in-toto twin, Dagster decorator, dbt/HTN/LangGraph
  - kinship, ZGraph audit, Idris error format spec, safeguard plan).
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`676766de`** — Surface packet guard-error lifecycle details
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`6f16325d`** — Add review-channel command freshness metadata
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`c910beb7`** — Add typed security and Rust audit report contracts
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`029384fc`** — Refresh external review snapshot for f216a49b
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`f216a49b`** — Separate read-only status command and runtime readiness
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`b6511619`** — Refresh external review snapshot for 26377459
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`26377459`** — Add PeerAwarenessPolicy contract and body-observation oracle agent_message boundary
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`6fb64ce4`** — Refresh external review snapshot for a59a8198
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-b87b70d50f0d` binds this file to HEAD `c912d41bcb6b`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
