# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `95fdd129bddd` — Refresh external review snapshot for e4eb2de9
- Tree hash: `f00343ee0135`
- Generation stamp: `snap-19476cb0c77b`
- Generated at (UTC): 2026-05-11T05:33:09Z
- Push decision: `no_push_needed` — governed_push_in_progress
- Reviewer mode: `tools_only` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 273 files, +21170/-2577
- Governance findings: 64 open / 17 fixed / 81 total
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
- HEAD SHA: `95fdd129bdddbc50cd25969df0dc6de667cc5a00`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-11T01:30:07-04:00

## 2. Governance state

### Push decision
- action: `no_push_needed`
- reason: governed_push_in_progress
- push_eligible_now: False
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report_state: `blocked` (push_preflight_running)
- publication_backlog: urgent

### Reviewer runtime
- reviewer_mode: `tools_only`
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

Range: last 25 commits ending at `95fdd129bddd`

- commits: 25
- files changed: 273
- insertions: +21170
- deletions: -2577
- bundle classes touched: docs, tooling, runtime
- authority surfaces touched: 12 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `95fdd129` | Refresh external review snapshot for e4eb2de9 | 2 | +56/-55 | docs |  |
| 2 | `e4eb2de9` | Parse provider-neutral review artifact headings | 2 | +17/-5 | runtime |  |
| 3 | `ce6ab928` | Refresh external review snapshot for ef60471d | 2 | +46/-47 | docs |  |
| 4 | `ef60471d` | Refresh external review snapshot for 5a4818e9 | 2 | +56/-56 | docs |  |
| 5 | `5a4818e9` | Use shared managed receipt prefixes | 10 | +51/-19 | tooling |  |
| 6 | `92846684` | Refresh external review snapshot for b7383d1c | 2 | +66/-65 | docs |  |
| 7 | `b7383d1c` | Enforce bridge projection guard lanes | 14 | +53/-3 | tooling |  |
| 8 | `5cf35cf1` | Refresh external review snapshot for 0298211f | 2 | +47/-47 | docs |  |
| 9 | `0298211f` | Refresh external review snapshot for 999920f3 | 2 | +46/-47 | docs |  |
| 10 | `999920f3` | Refresh external review snapshot for c574a584 | 2 | +59/-77 | docs |  |
| 11 | `c574a584` | Keep pre-commit hooks read-only | 9 | +88/-179 | tooling |  |
| 12 | `119dfed6` | Refresh external review snapshot for d6e6b253 | 2 | +70/-67 | docs |  |
| 13 | `d6e6b253` | Unify review projections and fail fast push preflight | 55 | +584/-327 | tooling |  |
| 14 | `267ccfd6` | Refresh external review snapshot for 7070ef7f | 2 | +43/-43 | docs |  |
| 15 | `7070ef7f` | Refresh external review snapshot for 7abb92dc | 2 | +44/-42 | docs |  |
| 16 | `7abb92dc` | Refresh external review snapshot for 469e8316 | 2 | +62/-64 | docs |  |
| 17 | `469e8316` | Stop review follow projection churn | 15 | +170/-93 | tooling |  |
| 18 | `1c619b33` | Refresh external review snapshot for 61fae6c9 | 2 | +45/-45 | docs |  |
| 19 | `61fae6c9` | Refresh external review snapshot for 09c341a4 | 2 | +67/-65 | docs |  |
| 20 | `09c341a4` | Refresh policy-owned generated surfaces for 268f8b2f | 1 | +2/-2 | docs |  |
| 21 | `268f8b2f` | Stop reviewer follow bridge churn | 3 | +108/-38 | tooling |  |
| 22 | `cd57ca76` | Refresh external review snapshot for 93de8d8e | 2 | +106/-91 | docs |  |
| 23 | `93de8d8e` | Fix MP-377 continuation goal attention | 215 | +18621/-922 | tooling |  |
| 24 | `25d5c79e` | Refresh external review snapshot for 319376e4 | 2 | +70/-81 | docs |  |
| 25 | `319376e4` | Ship GAP 2 provider-neutral capability slice (operator-auth… | 23 | +593/-97 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +6/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +18/-0 |
| `AGENTS.md` | docs | +7/-1 |
| `System_Connection_Flowchart.md` | docs | +1296/-1 |
| `app/operator_console/tests/state/test_state_modules.py` | tooling | +7/-7 |
| `bridge.md` | docs | +83/-84 |
| `codesmells.md` | docs | +1575/-0 |
| `dev/active/MASTER_PLAN.md` | tooling | +120/-23 |
| `dev/active/ai_governance_platform.md` | tooling | +111/-11 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1084/-1104 |
| `dev/audits/mp377_check_cli_test_parity_implementation.md` | tooling | +37/-0 |
| `dev/audits/mp377_codesmell_042_044_052_plan_ingest.md` | tooling | +46/-0 |
| `dev/audits/mp377_codesmell_048_051_plan_ingest.md` | tooling | +42/-0 |
| `dev/audits/mp377_provider_neutral_lane_routing_implementation.md` | tooling | +55/-0 |
| `dev/audits/mp377_provider_neutral_lane_routing_plan_ingest.md` | tooling | +77/-0 |
| `dev/config/devctl_repo_policy.json` | tooling | +2/-1 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +8/-131 |
| `dev/config/quality_presets/voiceterm.json` | tooling | +2/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +28/-9 |
| `dev/guides/SYSTEM_MAP.md` | docs | +9/-9 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +138/-3 |
| `dev/scripts/README.md` | tooling | +28/-15 |
| `dev/scripts/checks/check_bridge_projection_only.py` | tooling | +278/-0 |
| `dev/scripts/checks/check_check_cli_test_parity.py` | tooling | +269/-0 |
| `dev/scripts/checks/check_schema_fixture_handshake.py` | tooling | +270/-0 |
| `dev/scripts/checks/check_schema_migration_spine.py` | tooling | +80/-0 |
| `dev/scripts/checks/check_schema_version_monotonic.py` | tooling | +122/-0 |
| `dev/scripts/checks/check_state_store_authority.py` | tooling | +179/-0 |
| `dev/scripts/checks/platform_contract_closure/contract_registry_closure.py` | tooling | +146/-0 |
| `dev/scripts/checks/platform_contract_closure/emitter_parity_contract_checks.py` | tooling | +1/-0 |
| `dev/scripts/checks/platform_contract_closure/support.py` | tooling | +7/-0 |
| `dev/scripts/checks/review_surface_consistency/command.py` | tooling | +22/-5 |
| `dev/scripts/checks/startup_authority_contract/command.py` | tooling | +19/-4 |
| `dev/scripts/checks/startup_authority_contract/runtime_checks.py` | tooling | +4/-2 |
| `dev/scripts/checks/startup_authority_contract/runtime_import_atomicity.py` | tooling | +116/-27 |
| `dev/scripts/checks/startup_authority_contract/runtime_import_staged.py` | tooling | +36/-6 |
| `dev/scripts/devctl/audit_events.py` | tooling | +6/-4 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +6/-0 |
| `dev/scripts/devctl/cli.py` | tooling | +2/-0 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +4/-0 |
| _233 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 81
- open: 64
- fixed: 17
- false positives: 0

Recent findings:
- `dogfood.command.integrations-import` — `dev/scripts/devctl/commands/integrations_import.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.governance-export` — `dev/scripts/devctl/commands/governance/export.py` (n/a, verdict=`confirmed_issue`)
- `packet.transition_session_disambiguation` — `dev/scripts/devctl/review_channel/instruction_transitions.py` (critical, verdict=`confirmed_issue`)
- `packet.durable_ingestion_before_ttl` — `dev/scripts/devctl/runtime/packet_carry_forward.py` (critical, verdict=`confirmed_issue`)
- `agent_sync.ambiguity_projection` — `dev/scripts/checks/multi_agent_sync` (high, verdict=`confirmed_issue`)
- `review_channel.command_latency_under_fanout` — `dev/scripts/devctl/commands/review_channel` (high, verdict=`confirmed_issue`)
- `work_board.rows_duplication` — `dev/scripts/devctl/runtime/agent_dispatch_router.py` (high, verdict=`confirmed_issue`)
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_tests.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_test_runner/command.py` (n/a, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/push_review_snapshot_receipt_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_sync.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_receipt.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_heartbeat_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_follow_heartbeat_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_checks.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_import_atomicity.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_import_staged.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actions.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/development/orchestration_models.py`) — Commit 93de8d8e changed dev/scripts/devctl/commands/development/orchestration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/contract_registry_models.py`) — Commit 93de8d8e changed dev/scripts/devctl/platform/contract_registry_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit 93de8d8e changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit 93de8d8e changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit 93de8d8e changed dev/scripts/devctl/review_channel/packet_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/agent_loop_decision_models.py`) — Commit 93de8d8e changed dev/scripts/devctl/runtime/agent_loop_decision_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/collaboration_wake_contract.py`) — Commit 93de8d8e changed dev/scripts/devctl/runtime/collaboration_wake_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/development_packet_pressure_models.py`) — Commit 93de8d8e changed dev/scripts/devctl/runtime/development_packet_pressure_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/plan_ingestion_phase0_models.py`) — Commit 93de8d8e changed dev/scripts/devctl/runtime/plan_ingestion_phase0_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/plan_source_retention_models.py`) — Commit 93de8d8e changed dev/scripts/devctl/runtime/plan_source_retention_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit 93de8d8e changed dev/scripts/devctl/runtime/review_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_packet_models.py`) — Commit 93de8d8e changed dev/scripts/devctl/runtime/review_state_packet_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit 93de8d8e changed dev/scripts/devctl/runtime/reviewer_runtime_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Commit 93de8d8e changed dev/scripts/devctl/tests/checks/test_startup_authority_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit 93de8d8e changed dev/scripts/devctl/tests/platform/test_platform_contracts.py

### Suggested verification commands

- `cd rust && cargo test --bin voiceterm`
- `cd rust && cargo clippy --all-targets -- -D warnings`
- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`95fdd129`** — Refresh external review snapshot for e4eb2de9
- **`e4eb2de9`** — Parse provider-neutral review artifact headings
- **`ce6ab928`** — Refresh external review snapshot for ef60471d
- **`ef60471d`** — Refresh external review snapshot for 5a4818e9
- **`5a4818e9`** — Use shared managed receipt prefixes
- **`92846684`** — Refresh external review snapshot for b7383d1c
- **`b7383d1c`** — Enforce bridge projection guard lanes
- **`5cf35cf1`** — Refresh external review snapshot for 0298211f
- **`0298211f`** — Refresh external review snapshot for 999920f3
- **`999920f3`** — Refresh external review snapshot for c574a584
- **`c574a584`** — Keep pre-commit hooks read-only
- **`119dfed6`** — Refresh external review snapshot for d6e6b253
- **`d6e6b253`** — Unify review projections and fail fast push preflight
- **`267ccfd6`** — Refresh external review snapshot for 7070ef7f
- **`7070ef7f`** — Refresh external review snapshot for 7abb92dc
- **`7abb92dc`** — Refresh external review snapshot for 469e8316
- **`469e8316`** — Stop review follow projection churn
- **`1c619b33`** — Refresh external review snapshot for 61fae6c9
- **`61fae6c9`** — Refresh external review snapshot for 09c341a4
- **`09c341a4`** — Refresh policy-owned generated surfaces for 268f8b2f
- **`268f8b2f`** — Stop reviewer follow bridge churn
- **`cd57ca76`** — Refresh external review snapshot for 93de8d8e
- **`93de8d8e` | MPs: MP-377** — Fix MP-377 continuation goal attention
  - plan: `dev/active/ai_governance_platform.md`
- **`25d5c79e`** — Refresh external review snapshot for 319376e4
- **`319376e4`** — Ship GAP 2 provider-neutral capability slice (operator-authorized raw bypass)
  - Codex's TASK_COMPLETE'd slice + new module collaboration_authority_liveness.py.
  - Bypass invoked because typed pipeline blocked by 3 code-shape violations
  - that codex must address on respawn. Quality issues:
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

- open governance findings: 64

### Startup advisories
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/integrations_import.py`): dogfood.command.integrations-import: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/export.py`): dogfood.command.governance-export: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/review_channel/instruction_transitions.py`): packet.transition_session_disambiguation: source_packet_ids=rev_pkt_2691,rev_pkt_2696,rev_pkt_2705; Claude beta finding: transition_packet ack/apply/dismiss paths bypass session disambiguation, allowing cross-session packet actions. Durable owner: MP377-GUARDIR-TRANSITION-DISAMBIGUATION.
- **governance_open** (`dev/scripts/devctl/runtime/packet_carry_forward.py`): packet.durable_ingestion_before_ttl: source_packet_ids=rev_pkt_2691,rev_pkt_2696,rev_pkt_2697,rev_pkt_2699,rev_pkt_2700,rev_pkt_2701,rev_pkt_2702,rev_pkt_2704,rev_pkt_2705; packets are transport/provenance only, so packet-carried work must be promoted into PlanRow/FindingReview/GuardPromotionCandidate/knowledge state before TTL expiry. Durable owner: MP377-GUARDIR-PACKET-DURABLE-INGESTION.
- **governance_open** (`dev/scripts/checks/multi_agent_sync`): agent_sync.ambiguity_projection: source_packet_ids=rev_pkt_2697,rev_pkt_2705; canonical_active_packet_ambiguity can render empty while ambiguity exists, and expired-but-pending split state creates carry-forward debt. Durable owner: MP377-GUARDIR-AGENT-SYNC-AMBIGUITY-CARRYFORWARD.
- **governance_open** (`dev/scripts/devctl/commands/review_channel`): review_channel.command_latency_under_fanout: source_packet_ids=rev_pkt_2704,rev_pkt_2705; review-channel post and startup-context can hang under multi-agent load, tied to process-cleanup and detached sleep pressure. Durable owner: MP377-GUARDIR-FANOUT-COMMAND-HANGS.
- **governance_open** (`dev/scripts/devctl/runtime/agent_dispatch_router.py`): work_board.rows_duplication: source_packet_ids=rev_pkt_2700,rev_pkt_2705; _work_board_rows logic is duplicated between packet_route_resolution.py and agent_dispatch_router.py. Durable owner: MP377-GUARDIR-WORK-BOARD-ROUTE-DEDUP.
- **governance_open** (`dev/scripts/devctl/commands/reports_cleanup.py`): dogfood.command.reports-cleanup: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-19476cb0c77b` binds this file to HEAD `95fdd129bddd`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
