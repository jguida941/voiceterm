# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `6859108d3ee9` — Add publication scope integrity guard
- Tree hash: `ae95efbd9f2c`
- Generation stamp: `snap-d4271331c61f`
- Generated at (UTC): 2026-05-17T17:42:14Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 170 files, +13360/-1258
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
- HEAD SHA: `6859108d3ee9157b7acc3b11d9385e7615d398a1`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-17T13:41:51-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report_state: `published_remote` (post_push_bundle_pending)
- publication_backlog: urgent
- publication_guidance: 11 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `6859108d3ee9`

- commits: 24
- files changed: 170
- insertions: +13360
- deletions: -1258
- bundle classes touched: docs, tooling
- authority surfaces touched: 4 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `6859108d` | Add publication scope integrity guard | 7 | +395/-5 | tooling |  |
| 2 | `4529338e` | Enforce successful closure proof for plan rows | 62 | +4313/-163 | tooling |  |
| 3 | `a066d4c7` | Refresh external review snapshot for e5354d23 | 2 | +67/-65 | docs |  |
| 4 | `e5354d23` | Backfill P13 applied plan row | 3 | +15/-0 | tooling |  |
| 5 | `18273b32` | Add substrate commit plan-row guard | 8 | +716/-2 | tooling |  |
| 6 | `a58de5fa` | Add git operation receipts | 17 | +584/-35 | tooling |  |
| 7 | `c6c267ad` | Fix packet lifecycle and registry coverage | 30 | +492/-73 | tooling |  |
| 8 | `87bd473d` | Refresh external review snapshot for c4612178 | 2 | +49/-49 | docs |  |
| 9 | `c4612178` | Record artifact proof blockers | 4 | +288/-2 | tooling |  |
| 10 | `5a14bc01` | Refresh external review snapshot for 24b2bc02 | 2 | +123/-119 | docs |  |
| 11 | `24b2bc02` | Fix governance checkpoint gates | 43 | +3146/-111 | tooling |  |
| 12 | `bd28e78b` | Record raw git closure receipt warnings | 1 | +3/-0 | tooling |  |
| 13 | `18fae0b6` | Refresh bridge projection | 1 | +4/-4 | docs |  |
| 14 | `6f17c007` | Preserve raw git closure error codes | 12 | +488/-18 | tooling |  |
| 15 | `b1410fcc` | Fix typed peer collaboration and raw git closure gates | 29 | +1765/-83 | tooling |  |
| 16 | `febe8986` | Refresh external review snapshot for 8bda213b | 2 | +59/-59 | docs |  |
| 17 | `8bda213b` | Checkpoint R287 packet intake state | 4 | +74/-80 | tooling |  |
| 18 | `91f2ed42` | Add governed transition schema fixtures | 16 | +402/-49 | tooling |  |
| 19 | `477f01ae` | Refresh external review snapshot for 2a99a103 | 2 | +55/-55 | docs |  |
| 20 | `2a99a103` | Repair packet plan continuity state | 6 | +97/-65 | tooling |  |
| 21 | `685d0892` | Refresh external review snapshot for d7591b71 | 2 | +57/-57 | docs |  |
| 22 | `d7591b71` | Bind task-started packets to plan rows | 4 | +55/-49 | tooling |  |
| 23 | `bfd73b2f` | Refresh external review snapshot for 6f057634 | 2 | +63/-63 | docs |  |
| 24 | `6f057634` | Record ground-truth receipt for governance push | 2 | +50/-52 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +3/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +9/-0 |
| `bridge.md` | docs | +105/-104 |
| `dev/active/MASTER_PLAN.md` | tooling | +125/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +36/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +747/-749 |
| `dev/config/devctl_repo_policy.json` | tooling | +23/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +15/-1 |
| `dev/guides/SYSTEM_MAP.md` | docs | +115/-114 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +64/-0 |
| `dev/scripts/README.md` | tooling | +16/-5 |
| `dev/scripts/checks/check_feature_has_proof_receipt.py` | tooling | +65/-1 |
| `dev/scripts/checks/check_plan_gold_claims_resolve.py` | tooling | +15/-0 |
| `dev/scripts/checks/check_plan_metric_freshness.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_publication_scope_integrity.py` | tooling | +271/-0 |
| `dev/scripts/checks/check_substrate_commits_have_applied_plan_row.py` | tooling | +526/-7 |
| `dev/scripts/checks/plan_gold_claims_resolve/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/plan_gold_claims_resolve/command.py` | tooling | +282/-0 |
| `dev/scripts/checks/plan_gold_claims_resolve/symbol_index.py` | tooling | +170/-0 |
| `dev/scripts/checks/plan_metric_freshness/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/plan_metric_freshness/command.py` | tooling | +253/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +4/-0 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +28/-2 |
| `dev/scripts/devctl/cli_parser/exceptions.py` | tooling | +19/-4 |
| `dev/scripts/devctl/command_runner.py` | tooling | +37/-1 |
| `dev/scripts/devctl/commands/check/router.py` | tooling | +12/-0 |
| `dev/scripts/devctl/commands/check/router_coverage.py` | tooling | +98/-0 |
| `dev/scripts/devctl/commands/check/router_render.py` | tooling | +12/-0 |
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
| `dev/scripts/devctl/commands/python_test_runner/command.py` | tooling | +40/-1 |
| `dev/scripts/devctl/commands/raw_git.py` | tooling | +136/-24 |
| _130 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 43
- open: 43
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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_sync.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/python_test_contract.py`) — Commit 4529338e changed dev/scripts/devctl/runtime/python_test_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit a58de5fa changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit c6c267ad changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_identity_contract_rows.py`) — Commit 24b2bc02 changed dev/scripts/devctl/platform/runtime_identity_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_mode_authority_contract.py`) — Commit 24b2bc02 changed dev/scripts/devctl/runtime/reviewer_mode_authority_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_reviewer_mode_authority_contract.py`) — Commit 24b2bc02 changed dev/scripts/devctl/tests/runtime/test_reviewer_mode_authority_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`6859108d`** — Add publication scope integrity guard
- **`4529338e`** — Enforce successful closure proof for plan rows
- **`a066d4c7`** — Refresh external review snapshot for e5354d23
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

- open governance findings: 43

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-d4271331c61f` binds this file to HEAD `6859108d3ee9`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
