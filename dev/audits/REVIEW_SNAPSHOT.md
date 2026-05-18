# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `preserve/guardir-extraction-unreviewed-2026-05-18`
- HEAD: `92ef40320030` — UNREVIEWED PRESERVATION SNAPSHOT — voiceterm governance patch quarantine
- Tree hash: `7f3b513bf7f5`
- Generation stamp: `snap-1135aefe4549`
- Generated at (UTC): 2026-05-18T14:54:28Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 246 files, +28047/-1420
- Governance findings: 36 open / 0 fixed / 36 total
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
- Current branch: `preserve/guardir-extraction-unreviewed-2026-05-18`
- HEAD SHA: `92ef403200300169fe3e43b966c9e8288354b340`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-18T10:54:08-04:00

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
- publication_backlog: queued
- publication_guidance: Local branch still has unpublished work waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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
- advisory: `no_push_needed` — clean_worktree

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `92ef40320030`

- commits: 24
- files changed: 246
- insertions: +28047
- deletions: -1420
- bundle classes touched: docs, tooling
- authority surfaces touched: 8 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `92ef4032` | UNREVIEWED PRESERVATION SNAPSHOT — voiceterm governance pat… | 69 | +7933/-165 | tooling |  |
| 2 | `835060c2` | Refresh external review snapshot for 47944776 | 2 | +80/-74 | docs |  |
| 3 | `47944776` | Add semantic output consumption gates | 67 | +6820/-72 | tooling |  |
| 4 | `85932c69` | Refresh external review snapshot for 6859108d | 2 | +79/-72 | docs |  |
| 5 | `6859108d` | Add publication scope integrity guard | 7 | +395/-5 | tooling |  |
| 6 | `4529338e` | Enforce successful closure proof for plan rows | 62 | +4313/-163 | tooling |  |
| 7 | `a066d4c7` | Refresh external review snapshot for e5354d23 | 2 | +67/-65 | docs |  |
| 8 | `e5354d23` | Backfill P13 applied plan row | 3 | +15/-0 | tooling |  |
| 9 | `18273b32` | Add substrate commit plan-row guard | 8 | +716/-2 | tooling |  |
| 10 | `a58de5fa` | Add git operation receipts | 17 | +584/-35 | tooling |  |
| 11 | `c6c267ad` | Fix packet lifecycle and registry coverage | 30 | +492/-73 | tooling |  |
| 12 | `87bd473d` | Refresh external review snapshot for c4612178 | 2 | +49/-49 | docs |  |
| 13 | `c4612178` | Record artifact proof blockers | 4 | +288/-2 | tooling |  |
| 14 | `5a14bc01` | Refresh external review snapshot for 24b2bc02 | 2 | +123/-119 | docs |  |
| 15 | `24b2bc02` | Fix governance checkpoint gates | 43 | +3146/-111 | tooling |  |
| 16 | `bd28e78b` | Record raw git closure receipt warnings | 1 | +3/-0 | tooling |  |
| 17 | `18fae0b6` | Refresh bridge projection | 1 | +4/-4 | docs |  |
| 18 | `6f17c007` | Preserve raw git closure error codes | 12 | +488/-18 | tooling |  |
| 19 | `b1410fcc` | Fix typed peer collaboration and raw git closure gates | 29 | +1765/-83 | tooling |  |
| 20 | `febe8986` | Refresh external review snapshot for 8bda213b | 2 | +59/-59 | docs |  |
| 21 | `8bda213b` | Checkpoint R287 packet intake state | 4 | +74/-80 | tooling |  |
| 22 | `91f2ed42` | Add governed transition schema fixtures | 16 | +402/-49 | tooling |  |
| 23 | `477f01ae` | Refresh external review snapshot for 2a99a103 | 2 | +55/-55 | docs |  |
| 24 | `2a99a103` | Repair packet plan continuity state | 6 | +97/-65 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +3/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +9/-0 |
| `bridge.md` | docs | +114/-113 |
| `dev/active/MASTER_PLAN.md` | tooling | +146/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +36/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +688/-674 |
| `dev/config/devctl_repo_policy.json` | tooling | +23/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +15/-1 |
| `dev/guides/SYSTEM_MAP.md` | docs | +117/-116 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +64/-0 |
| `dev/scripts/README.md` | tooling | +16/-5 |
| `dev/scripts/checks/check_command_output_consumed.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_control_decision_consistency.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_control_decision_obeyed.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_feature_has_proof_receipt.py` | tooling | +65/-1 |
| `dev/scripts/checks/check_packet_absorption_required.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_plan_gold_claims_resolve.py` | tooling | +15/-0 |
| `dev/scripts/checks/check_plan_metric_freshness.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_publication_scope_integrity.py` | tooling | +477/-2 |
| `dev/scripts/checks/check_substrate_commits_have_applied_plan_row.py` | tooling | +526/-7 |
| `dev/scripts/checks/command_output_consumed/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/command_output_consumed/command.py` | tooling | +120/-0 |
| `dev/scripts/checks/control_decision_consistency/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/control_decision_consistency/command.py` | tooling | +116/-0 |
| `dev/scripts/checks/control_decision_obeyed/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/control_decision_obeyed/command.py` | tooling | +109/-0 |
| `dev/scripts/checks/packet_absorption_required/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/packet_absorption_required/command.py` | tooling | +149/-0 |
| `dev/scripts/checks/plan_gold_claims_resolve/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/plan_gold_claims_resolve/command.py` | tooling | +282/-0 |
| `dev/scripts/checks/plan_gold_claims_resolve/symbol_index.py` | tooling | +170/-0 |
| `dev/scripts/checks/plan_metric_freshness/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/plan_metric_freshness/command.py` | tooling | +253/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +5/-1 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +28/-2 |
| `dev/scripts/devctl/cli_parser/exceptions.py` | tooling | +19/-4 |
| `dev/scripts/devctl/command_runner.py` | tooling | +37/-1 |
| `dev/scripts/devctl/commands/check/router.py` | tooling | +12/-0 |
| `dev/scripts/devctl/commands/check/router_coverage.py` | tooling | +98/-0 |
| `dev/scripts/devctl/commands/check/router_render.py` | tooling | +12/-0 |
| _206 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 36
- open: 36
- fixed: 0
- false positives: 0

Recent findings:
- `dogfood.command.push` — `dev/scripts/devctl/commands/vcs/push.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_tests.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_test_runner/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-cleanup` — `dev/scripts/devctl/commands/process/cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.install-git-hooks` — `dev/scripts/devctl/commands/governance/install_git_hooks.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/governance/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.render-surfaces` — `dev/scripts/devctl/commands/governance/render_surfaces.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.remote-control` — `dev/scripts/devctl/commands/remote_control/command.py` (n/a, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_push.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_parser.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_sync.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/governance/push_state_models.py`) — Commit 92ef4032 changed dev/scripts/devctl/governance/push_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit 92ef4032 changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/agent_loop_decision_models.py`) — Commit 92ef4032 changed dev/scripts/devctl/runtime/agent_loop_decision_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_packet_models.py`) — Commit 92ef4032 changed dev/scripts/devctl/runtime/review_state_packet_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit 92ef4032 changed dev/scripts/devctl/runtime/reviewer_runtime_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/startup_context_models.py`) — Commit 92ef4032 changed dev/scripts/devctl/runtime/startup_context_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_intake_models.py`) — Commit 92ef4032 changed dev/scripts/devctl/runtime/work_intake_models.py
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

- **`92ef4032`** — UNREVIEWED PRESERVATION SNAPSHOT — voiceterm governance patch quarantine
  - Operator-issued 2026-05-18T~14:30Z UTC. This is an emergency preservation
  - snapshot, NOT a release commit. It captures the 69-path uncommitted
  - governance patch + 3 untracked files from working tree of
- **`835060c2`** — Refresh external review snapshot for 47944776
- **`47944776`** — Add semantic output consumption gates
- **`85932c69`** — Refresh external review snapshot for 6859108d
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

- open governance findings: 36

### Startup advisories
- no_push_needed: clean_worktree

### Stale warnings
- Move straight to the governed push path.

### Open gap rows
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
- **governance_open** (`dev/scripts/devctl/commands/governance/install_git_hooks.py`): dogfood.command.install-git-hooks: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/relaunch_loop.py`): dogfood.command.relaunch-loop: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/relaunch_loop.py`): dogfood.command.relaunch-loop: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-1135aefe4549` binds this file to HEAD `92ef40320030`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
