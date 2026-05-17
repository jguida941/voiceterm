# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `e5354d23ecfa` — Backfill P13 applied plan row
- Tree hash: `56fd7e3397dc`
- Generation stamp: `snap-36c42050d1a3`
- Generated at (UTC): 2026-05-17T06:15:43Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 122 files, +8728/-1171
- Governance findings: 44 open / 0 fixed / 44 total
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
- HEAD SHA: `e5354d23ecfa1392c4a7dcac5f9042207c5aa6ec`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-17T02:15:14-04:00

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
- publication_guidance: 8 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `tools_only`
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

Range: last 24 commits ending at `e5354d23ecfa`

- commits: 24
- files changed: 122
- insertions: +8728
- deletions: -1171
- bundle classes touched: tooling, docs

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `e5354d23` | Backfill P13 applied plan row | 3 | +15/-0 | tooling |  |
| 2 | `18273b32` | Add substrate commit plan-row guard | 8 | +716/-2 | tooling |  |
| 3 | `a58de5fa` | Add git operation receipts | 17 | +584/-35 | tooling |  |
| 4 | `c6c267ad` | Fix packet lifecycle and registry coverage | 30 | +492/-73 | tooling |  |
| 5 | `87bd473d` | Refresh external review snapshot for c4612178 | 2 | +49/-49 | docs |  |
| 6 | `c4612178` | Record artifact proof blockers | 4 | +288/-2 | tooling |  |
| 7 | `5a14bc01` | Refresh external review snapshot for 24b2bc02 | 2 | +123/-119 | docs |  |
| 8 | `24b2bc02` | Fix governance checkpoint gates | 43 | +3146/-111 | tooling |  |
| 9 | `bd28e78b` | Record raw git closure receipt warnings | 1 | +3/-0 | tooling |  |
| 10 | `18fae0b6` | Refresh bridge projection | 1 | +4/-4 | docs |  |
| 11 | `6f17c007` | Preserve raw git closure error codes | 12 | +488/-18 | tooling |  |
| 12 | `b1410fcc` | Fix typed peer collaboration and raw git closure gates | 29 | +1765/-83 | tooling |  |
| 13 | `febe8986` | Refresh external review snapshot for 8bda213b | 2 | +59/-59 | docs |  |
| 14 | `8bda213b` | Checkpoint R287 packet intake state | 4 | +74/-80 | tooling |  |
| 15 | `91f2ed42` | Add governed transition schema fixtures | 16 | +402/-49 | tooling |  |
| 16 | `477f01ae` | Refresh external review snapshot for 2a99a103 | 2 | +55/-55 | docs |  |
| 17 | `2a99a103` | Repair packet plan continuity state | 6 | +97/-65 | tooling |  |
| 18 | `685d0892` | Refresh external review snapshot for d7591b71 | 2 | +57/-57 | docs |  |
| 19 | `d7591b71` | Bind task-started packets to plan rows | 4 | +55/-49 | tooling |  |
| 20 | `bfd73b2f` | Refresh external review snapshot for 6f057634 | 2 | +63/-63 | docs |  |
| 21 | `6f057634` | Record ground-truth receipt for governance push | 2 | +50/-52 | tooling |  |
| 22 | `be28caed` | Refresh external review snapshot for 08895a8a | 2 | +58/-56 | docs |  |
| 23 | `08895a8a` | Document role review completion guard | 3 | +84/-89 | tooling |  |
| 24 | `f0577b3b` | Refresh policy-owned generated surfaces for 996c3335 | 1 | +1/-1 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `bridge.md` | docs | +98/-97 |
| `dev/active/MASTER_PLAN.md` | tooling | +48/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +36/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +818/-826 |
| `dev/config/devctl_repo_policy.json` | tooling | +23/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +15/-1 |
| `dev/guides/SYSTEM_MAP.md` | docs | +87/-86 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +64/-0 |
| `dev/scripts/README.md` | tooling | +15/-5 |
| `dev/scripts/checks/check_substrate_commits_have_applied_plan_row.py` | tooling | +459/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +28/-2 |
| `dev/scripts/devctl/cli_parser/exceptions.py` | tooling | +19/-4 |
| `dev/scripts/devctl/commands/development/campaign.py` | tooling | +32/-2 |
| `dev/scripts/devctl/commands/development/campaign_exception_proof.py` | tooling | +2/-1 |
| `dev/scripts/devctl/commands/development/campaign_idris_gate.py` | tooling | +142/-0 |
| `dev/scripts/devctl/commands/development/final_response_gate.py` | tooling | +209/-2 |
| `dev/scripts/devctl/commands/development/next_slice_blockers.py` | tooling | +85/-1 |
| `dev/scripts/devctl/commands/development/packet_attention_lifecycle.py` | tooling | +12/-16 |
| `dev/scripts/devctl/commands/governance/close_raw_git_exceptions.py` | tooling | +198/-9 |
| `dev/scripts/devctl/commands/governance/exceptions.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/governance/exceptions_pending.py` | tooling | +2/-1 |
| `dev/scripts/devctl/commands/governance/exceptions_report.py` | tooling | +35/-0 |
| `dev/scripts/devctl/commands/vcs/push_render_surface_sync.py` | tooling | +2/-0 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +4/-0 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows.py` | tooling | +34/-2 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows_commit.py` | tooling | +55/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows.py` | tooling | +67/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_review.py` | tooling | +2/-0 |
| `dev/scripts/devctl/platform/schema_migration_spine.py` | tooling | +50/-11 |
| `dev/scripts/devctl/review_channel/active_packet_authority.py` | tooling | +2/-5 |
| `dev/scripts/devctl/review_channel/agent_packet_attention_scope.py` | tooling | +3/-9 |
| `dev/scripts/devctl/review_channel/agent_sync_packet_classification.py` | tooling | +12/-14 |
| `dev/scripts/devctl/review_channel/agent_work_board_packets.py` | tooling | +2/-9 |
| `dev/scripts/devctl/review_channel/collaboration_session.py` | tooling | +26/-2 |
| `dev/scripts/devctl/review_channel/packet_loop_attention.py` | tooling | +23/-1 |
| `dev/scripts/devctl/review_channel/packet_plan_integration.py` | tooling | +2/-3 |
| `dev/scripts/devctl/review_channel/packet_terminal_lifecycle_states.py` | tooling | +74/-0 |
| _82 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 44
- open: 44
- fixed: 0
- false positives: 0

Recent findings:
- `dogfood.command.pipeline` — `dev/scripts/devctl/commands/pipeline/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-audit` — `dev/scripts/devctl/commands/process/audit.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.check-router` — `dev/scripts/devctl/commands/check/router.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.push` — `dev/scripts/devctl/commands/vcs/push.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_tests.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_test_runner/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-cleanup` — `dev/scripts/devctl/commands/process/cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/governance/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)

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

- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit a58de5fa changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit c6c267ad changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_identity_contract_rows.py`) — Commit 24b2bc02 changed dev/scripts/devctl/platform/runtime_identity_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_mode_authority_contract.py`) — Commit 24b2bc02 changed dev/scripts/devctl/runtime/reviewer_mode_authority_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_reviewer_mode_authority_contract.py`) — Commit 24b2bc02 changed dev/scripts/devctl/tests/runtime/test_reviewer_mode_authority_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`e5354d23`** — Backfill P13 applied plan row
- **`18273b32`** — Add substrate commit plan-row guard
- **`a58de5fa`** — Add git operation receipts
- **`c6c267ad`** — Fix packet lifecycle and registry coverage
- **`87bd473d`** — Refresh external review snapshot for c4612178
- **`c4612178`** — Record artifact proof blockers
- **`5a14bc01`** — Refresh external review snapshot for 24b2bc02
- **`24b2bc02`** — Fix governance checkpoint gates
- **`bd28e78b`** — Record raw git closure receipt warnings
  - Seal PlanRowClosureReceipt rows emitted by the raw-git wrapper for the R297 checkpoint and projection refresh. The rows preserve plan_row_missing warnings for the ad-hoc feature ids used by the bypass receipts.
- **`18fae0b6`** — Refresh bridge projection
  - Projection-only bridge refresh after the raw-git checkpoint and push. Evidence path: bridge.md.
- **`6f17c007`** — Preserve raw git closure error codes
  - R297 raw-git exception closure now propagates governed transition error codes through the close-raw-git CLI JSON path. Evidence: rev_pkt_4265; focused CLI suite 11 passed; runtime lifecycle suite 8 passed; docs-check strict-tooling passed; instruction surface sync passed.
- **`b1410fcc`** — Fix typed peer collaboration and raw git closure gates
- **`febe8986`** — Refresh external review snapshot for 8bda213b
- **`8bda213b`** — Checkpoint R287 packet intake state
- **`91f2ed42`** — Add governed transition schema fixtures
- **`477f01ae`** — Refresh external review snapshot for 2a99a103
- **`2a99a103`** — Repair packet plan continuity state
- **`685d0892`** — Refresh external review snapshot for d7591b71
- **`d7591b71`** — Bind task-started packets to plan rows
- **`bfd73b2f`** — Refresh external review snapshot for 6f057634
- **`6f057634`** — Record ground-truth receipt for governance push
- **`be28caed`** — Refresh external review snapshot for 08895a8a
- **`08895a8a`** — Document role review completion guard
- **`f0577b3b`** — Refresh policy-owned generated surfaces for 996c3335
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- 2026-05-11 slice 18 fix arc + bilateral protocol consolidation (MP-377):
- 2026-05-14 launch-bootstrap repair family (MP-378): after the relaunch
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:

## 8. Known gaps and open items

- open governance findings: 44

### Startup advisories
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/pipeline/command.py`): dogfood.command.pipeline: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/process/audit.py`): dogfood.command.process-audit: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/check/router.py`): dogfood.command.check-router: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/vcs/push.py`): dogfood.command.push: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/reports_cleanup.py`): dogfood.command.reports-cleanup: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/python_tests.py`): dogfood.command.test-python: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/python_test_runner/command.py`): dogfood.command.test-python: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/process/cleanup.py`): dogfood.command.process-cleanup: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-36c42050d1a3` binds this file to HEAD `e5354d23ecfa`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
