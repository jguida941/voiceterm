# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `3c067775d6aa` — Split review-state and push authority responsibilities
- Tree hash: `5e8ebfc405d9`
- Generation stamp: `snap-7d964fbb9728`
- Generated at (UTC): 2026-05-11T07:35:12Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 84 files, +2969/-2404
- Governance findings: 48 open / 10 fixed / 58 total
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
- HEAD SHA: `3c067775d6aa9520083476de68aed21beb5f13b0`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-11T03:34:28-04:00

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
- publication_guidance: 30 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `3c067775d6aa`

- commits: 24
- files changed: 84
- insertions: +2969
- deletions: -2404
- bundle classes touched: tooling, docs, runtime
- authority surfaces touched: 4 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `3c067775` | Split review-state and push authority responsibilities | 24 | +992/-743 | tooling |  |
| 2 | `87f8b2dd` | Refresh external review snapshot for 7a094406 | 1 | +43/-43 | tooling |  |
| 3 | `7a094406` | Refresh policy-owned generated surfaces for 77b19aac | 1 | +1/-1 | docs |  |
| 4 | `77b19aac` | Refresh external review snapshot for e4f6713d | 2 | +59/-59 | docs |  |
| 5 | `e4f6713d` | Refine package layout debt enforcement | 5 | +365/-270 | tooling |  |
| 6 | `d5d39f76` | Refresh external review snapshot for 19755d06 | 1 | +43/-44 | tooling |  |
| 7 | `19755d06` | Refresh external review snapshot for e450826a | 2 | +93/-120 | docs |  |
| 8 | `e450826a` | Refresh ground-truth probe receipt | 1 | +1/-0 | tooling |  |
| 9 | `76a552d9` | Refresh external review snapshot for 95fdd129 | 1 | +46/-45 | tooling |  |
| 10 | `95fdd129` | Refresh external review snapshot for e4eb2de9 | 2 | +56/-55 | docs |  |
| 11 | `e4eb2de9` | Parse provider-neutral review artifact headings | 2 | +17/-5 | runtime |  |
| 12 | `ce6ab928` | Refresh external review snapshot for ef60471d | 2 | +46/-47 | docs |  |
| 13 | `ef60471d` | Refresh external review snapshot for 5a4818e9 | 2 | +56/-56 | docs |  |
| 14 | `5a4818e9` | Use shared managed receipt prefixes | 10 | +51/-19 | tooling |  |
| 15 | `92846684` | Refresh external review snapshot for b7383d1c | 2 | +66/-65 | docs |  |
| 16 | `b7383d1c` | Enforce bridge projection guard lanes | 14 | +53/-3 | tooling |  |
| 17 | `5cf35cf1` | Refresh external review snapshot for 0298211f | 2 | +47/-47 | docs |  |
| 18 | `0298211f` | Refresh external review snapshot for 999920f3 | 2 | +46/-47 | docs |  |
| 19 | `999920f3` | Refresh external review snapshot for c574a584 | 2 | +59/-77 | docs |  |
| 20 | `c574a584` | Keep pre-commit hooks read-only | 9 | +88/-179 | tooling |  |
| 21 | `119dfed6` | Refresh external review snapshot for d6e6b253 | 2 | +70/-67 | docs |  |
| 22 | `d6e6b253` | Unify review projections and fail fast push preflight | 55 | +584/-327 | tooling |  |
| 23 | `267ccfd6` | Refresh external review snapshot for 7070ef7f | 2 | +43/-43 | docs |  |
| 24 | `7070ef7f` | Refresh external review snapshot for 7abb92dc | 2 | +44/-42 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `AGENTS.md` | docs | +4/-1 |
| `app/operator_console/tests/state/test_state_modules.py` | tooling | +7/-7 |
| `bridge.md` | docs | +39/-42 |
| `dev/active/MASTER_PLAN.md` | tooling | +44/-20 |
| `dev/active/ai_governance_platform.md` | tooling | +17/-11 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +969/-1008 |
| `dev/config/devctl_repo_policy.json` | tooling | +2/-1 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +8/-131 |
| `dev/config/quality_presets/voiceterm.json` | tooling | +2/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +18/-9 |
| `dev/guides/SYSTEM_MAP.md` | docs | +2/-2 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +80/-3 |
| `dev/scripts/README.md` | tooling | +12/-10 |
| `dev/scripts/checks/package_layout/baseline_debt.py` | tooling | +43/-11 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/dashboard_utils.py` | tooling | +18/-203 |
| `dev/scripts/devctl/commands/development/baseline_inventory.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/governance/session_resume_paths.py` | tooling | +10/-2 |
| `dev/scripts/devctl/commands/pipeline/support.py` | tooling | +2/-2 |
| `dev/scripts/devctl/commands/reporting/dashboard_utils.py` | tooling | +203/-0 |
| `dev/scripts/devctl/commands/review_channel/_bridge_poll_support.py` | tooling | +8/-2 |
| `dev/scripts/devctl/commands/review_channel/_render_bridge.py` | tooling | +7/-1 |
| `dev/scripts/devctl/commands/review_channel/status.py` | tooling | +5/-1 |
| `dev/scripts/devctl/commands/vcs/commit_action_request_authority.py` | tooling | +19/-102 |
| `dev/scripts/devctl/commands/vcs/commit_action_request_evidence.py` | tooling | +6/-17 |
| `dev/scripts/devctl/commands/vcs/commit_action_request_lifecycle.py` | tooling | +0/-2 |
| `dev/scripts/devctl/commands/vcs/commit_action_request_lifecycle_gate.py` | tooling | +43/-0 |
| `dev/scripts/devctl/commands/vcs/commit_action_request_pipeline.py` | tooling | +62/-0 |
| `dev/scripts/devctl/commands/vcs/commit_action_request_revision.py` | tooling | +35/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_sync.py` | tooling | +0/-4 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +3/-3 |
| `dev/scripts/devctl/commands/vcs/push_pipeline_state_sync.py` | tooling | +0/-4 |
| `dev/scripts/devctl/commands/vcs/push_preflight_projection.py` | tooling | +19/-75 |
| `dev/scripts/devctl/commands/vcs/push_preflight_snapshot_receipt.py` | tooling | +104/-0 |
| `dev/scripts/devctl/commands/vcs/push_review_snapshot_receipt_guard.py` | tooling | +33/-6 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +4/-1 |
| `dev/scripts/devctl/governance/push_policy.py` | tooling | +2/-0 |
| `dev/scripts/devctl/governance/push_policy_parse.py` | tooling | +4/-0 |
| _44 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 58
- open: 48
- fixed: 10
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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/remote_commit_pipeline_artifact.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/push_review_snapshot_receipt_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_sync.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_receipt.py`) — Review contract-level invariants for this file

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

- **`3c067775`** — Split review-state and push authority responsibilities
- **`87f8b2dd`** — Refresh external review snapshot for 7a094406
- **`7a094406`** — Refresh policy-owned generated surfaces for 77b19aac
- **`77b19aac`** — Refresh external review snapshot for e4f6713d
- **`e4f6713d`** — Refine package layout debt enforcement
- **`d5d39f76`** — Refresh external review snapshot for 19755d06
- **`19755d06`** — Refresh external review snapshot for e450826a
- **`e450826a`** — Refresh ground-truth probe receipt
- **`76a552d9`** — Refresh external review snapshot for 95fdd129
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

- open governance findings: 48

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-7d964fbb9728` binds this file to HEAD `3c067775d6aa`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
