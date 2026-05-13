# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `a9415b9af0db` — Refresh policy-owned generated surfaces for 7e006123
- Tree hash: `8b2e35a1f20a`
- Generation stamp: `snap-3ef256d6db95`
- Generated at (UTC): 2026-05-13T00:33:04Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 67 files, +4716/-1950
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
- HEAD SHA: `a9415b9af0dbaa4b51728d66fb33f77a59f76642`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-12T19:18:09-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 41
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: urgent
- publication_guidance: 27 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `a9415b9af0db`

- commits: 24
- files changed: 67
- insertions: +4716
- deletions: -1950
- bundle classes touched: docs, tooling
- authority surfaces touched: 9 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `a9415b9a` | Refresh policy-owned generated surfaces for 7e006123 | 1 | +1/-1 | docs |  |
| 2 | `7e006123` | Refresh external review snapshot for 8d5bb18a | 2 | +56/-53 | docs |  |
| 3 | `8d5bb18a` | Checkpoint listing package projections | 4 | +51/-49 | tooling |  |
| 4 | `32545d54` | Package devctl list command | 4 | +221/-242 | tooling |  |
| 5 | `cdc5b9a1` | Refresh policy-owned generated surfaces for f91cbada | 1 | +1/-1 | docs |  |
| 6 | `f91cbada` | Refresh external review snapshot for 725c000d | 2 | +57/-57 | docs |  |
| 7 | `725c000d` | Allow shared schema fixture roots | 6 | +455/-319 | tooling |  |
| 8 | `97992ae2` | Refresh external review snapshot for 81f85b53 | 2 | +54/-54 | docs |  |
| 9 | `81f85b53` | Checkpoint live packet projections | 4 | +49/-47 | tooling |  |
| 10 | `454b6230` | Refresh ground truth probe receipt | 2 | +51/-50 | tooling |  |
| 11 | `eddba7ea` | Refresh external review snapshot for 555fa483 | 2 | +56/-56 | docs |  |
| 12 | `555fa483` | Checkpoint push bypass packet projections | 3 | +50/-46 | tooling |  |
| 13 | `05adb548` | Allow publish-clear managed projection receipts | 5 | +145/-52 | tooling |  |
| 14 | `c41a0250` | Refresh external review snapshot for c536d666 | 2 | +59/-59 | docs |  |
| 15 | `c536d666` | Checkpoint post-commit packet projections | 4 | +84/-48 | tooling |  |
| 16 | `ed1fbf18` | Refresh external review snapshot for dea85ab1 | 2 | +60/-58 | docs |  |
| 17 | `dea85ab1` | Fix governed commit pipeline reload fallback | 8 | +417/-54 | tooling |  |
| 18 | `753cf164` | Fix governed commit pipeline retention | 8 | +190/-55 | tooling |  |
| 19 | `cae10c5e` | Refresh external review snapshot for 6bd6f207 | 2 | +60/-59 | docs |  |
| 20 | `6bd6f207` | Fix governed commit pipeline retention | 10 | +230/-56 | tooling |  |
| 21 | `42683c3f` | Refresh external review snapshot for c8cf1c84 | 2 | +49/-48 | docs |  |
| 22 | `c8cf1c84` | Post-commit working tree cleanup: bridge heartbeat + codesm… | 4 | +39/-3 | docs |  |
| 23 | `e76ed6f3` | Refresh external review snapshot for eb336244 | 2 | +82/-76 | docs |  |
| 24 | `eb336244` | Land MP377 BypassLifecycle composability + charter addition… | 48 | +2199/-407 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `AGENTS.md` | docs | +1/-0 |
| `bridge.md` | docs | +64/-64 |
| `codesmells.md` | docs | +578/-0 |
| `dev/active/MASTER_PLAN.md` | tooling | +28/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +12/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1121/-1138 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +3/-2 |
| `dev/guides/DEVELOPMENT.md` | docs | +17/-6 |
| `dev/guides/SYSTEM_MAP.md` | docs | +7/-7 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +27/-0 |
| `dev/scripts/README.md` | tooling | +13/-2 |
| `dev/scripts/checks/check_schema_fixture_handshake.py` | tooling | +8/-266 |
| `dev/scripts/checks/schema_fixture_handshake/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/schema_fixture_handshake/command.py` | tooling | +302/-0 |
| `dev/scripts/devctl/approval_mode.py` | tooling | +30/-1 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/listing.py` | tooling | +6/-136 |
| `dev/scripts/devctl/commands/listing/__init__.py` | tooling | +137/-0 |
| `dev/scripts/devctl/commands/review_channel/_recover.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/review_channel/bridge_action_support.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/bridge_handler.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/bridge_launch_control.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/launcher_discipline_enforcement.py` | tooling | +57/-7 |
| `dev/scripts/devctl/commands/vcs/commit_guard_bundle.py` | tooling | +4/-2 |
| `dev/scripts/devctl/commands/vcs/commit_guard_replay.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/vcs/commit_preflight.py` | tooling | +2/-2 |
| `dev/scripts/devctl/commands/vcs/commit_preflight_validators.py` | tooling | +19/-1 |
| `dev/scripts/devctl/commands/vcs/commit_runtime_flow.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/vcs/governed_executor.py` | tooling | +17/-14 |
| `dev/scripts/devctl/commands/vcs/governed_executor_pipeline_memory.py` | tooling | +37/-0 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +1/-0 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_bypass_lifecycle.py` | tooling | +191/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_governed_exception_core.py` | tooling | +2/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_governed_exceptions.py` | tooling | +12/-0 |
| `dev/scripts/devctl/review_channel/launch.py` | tooling | +42/-49 |
| `dev/scripts/devctl/review_channel/launch_bypass.py` | tooling | +31/-0 |
| `dev/scripts/devctl/review_channel/launch_commands.py` | tooling | +66/-0 |
| _27 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_pipeline_memory.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_handler.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_launch_control.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/bypass_lifecycle_models.py`) — Commit eb336244 changed dev/scripts/devctl/runtime/bypass_lifecycle_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/startup_context_models.py`) — Commit eb336244 changed dev/scripts/devctl/runtime/startup_context_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit eb336244 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`c536d666`** — Checkpoint post-commit packet projections
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`ed1fbf18`** — Refresh external review snapshot for dea85ab1
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`dea85ab1`** — Fix governed commit pipeline reload fallback
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`753cf164`** — Fix governed commit pipeline retention
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`cae10c5e`** — Refresh external review snapshot for 6bd6f207
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`6bd6f207`** — Fix governed commit pipeline retention
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`42683c3f`** — Refresh external review snapshot for c8cf1c84
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`c8cf1c84`** — Post-commit working tree cleanup: bridge heartbeat + codesmells.md cycle 8 + MASTER_PLAN/plan_index auto-gen refresh
  - Cleans working tree before codex re-launch per operator directive 19:32Z.
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`e76ed6f3`** — Refresh external review snapshot for eb336244
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`eb336244`** — Land MP377 BypassLifecycle composability + charter additions P88-P93 (claude-mutation-lane handoff)
  - Codex landed full BypassLifecycle typed runtime in claude's mutation lane per codex
  - gate diagnostic 2026-05-12T18:52Z: "Claude's lane has stage/commit capabilities;
  - current loop pinned to rev_pkt_3736."
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
- checkpoint_before_continue: staged_index_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-3ef256d6db95` binds this file to HEAD `a9415b9af0db`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
