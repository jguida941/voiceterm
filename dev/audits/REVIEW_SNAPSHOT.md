# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `477f01aedd7b` — Refresh external review snapshot for 2a99a103
- Tree hash: `f47847b4eb26`
- Generation stamp: `snap-7f05b63fba91`
- Generated at (UTC): 2026-05-16T22:47:55Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 63 files, +5009/-1567
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
- HEAD SHA: `477f01aedd7bdbb1b2cbaa02da1a3d348c823cd0`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-16T18:24:56-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 15
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: urgent
- publication_guidance: 34 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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

Range: last 24 commits ending at `477f01aedd7b`

- commits: 24
- files changed: 63
- insertions: +5009
- deletions: -1567
- bundle classes touched: docs, tooling
- authority surfaces touched: 2 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `477f01ae` | Refresh external review snapshot for 2a99a103 | 2 | +55/-55 | docs |  |
| 2 | `2a99a103` | Repair packet plan continuity state | 6 | +97/-65 | tooling |  |
| 3 | `685d0892` | Refresh external review snapshot for d7591b71 | 2 | +57/-57 | docs |  |
| 4 | `d7591b71` | Bind task-started packets to plan rows | 4 | +55/-49 | tooling |  |
| 5 | `bfd73b2f` | Refresh external review snapshot for 6f057634 | 2 | +63/-63 | docs |  |
| 6 | `6f057634` | Record ground-truth receipt for governance push | 2 | +50/-52 | tooling |  |
| 7 | `be28caed` | Refresh external review snapshot for 08895a8a | 2 | +58/-56 | docs |  |
| 8 | `08895a8a` | Document role review completion guard | 3 | +84/-89 | tooling |  |
| 9 | `f0577b3b` | Refresh policy-owned generated surfaces for 996c3335 | 1 | +1/-1 | docs |  |
| 10 | `996c3335` | Refresh external review snapshot for c433c686 | 2 | +55/-61 | docs |  |
| 11 | `c433c686` | MP-378 require resolvable pytest proof nodes | 5 | +247/-51 | tooling |  |
| 12 | `b632df44` | Refresh external review snapshot for ad84e97b | 2 | +64/-70 | docs |  |
| 13 | `ad84e97b` | MP-378 record pytest nodes in feature proof receipts | 4 | +196/-49 | tooling |  |
| 14 | `00ab91b8` | Refresh external review snapshot for 494e0914 | 2 | +65/-73 | docs |  |
| 15 | `494e0914` | MP-378 require role review timeout governance chain | 3 | +141/-53 | tooling |  |
| 16 | `b707ad20` | Refresh external review snapshot for aa840939 | 2 | +58/-62 | docs |  |
| 17 | `aa840939` | MP-378 add governed transition typechecker proof | 8 | +1149/-68 | tooling |  |
| 18 | `ab38e2a8` | Refresh external review snapshot for b38d2bd7 | 2 | +59/-64 | docs |  |
| 19 | `b38d2bd7` | MP-378 add bypass expire error code proof | 7 | +61/-52 | tooling |  |
| 20 | `9283311c` | Refresh external review snapshot for 54bb3a07 | 2 | +66/-75 | docs |  |
| 21 | `54bb3a07` | MP-378 repair packet debt and bypass expiry proof | 19 | +800/-143 | tooling |  |
| 22 | `12328ec3` | Refresh external review snapshot for e9de52ef | 2 | +67/-73 | docs |  |
| 23 | `e9de52ef` | MP-NEW-P209 add bypass expire CLI | 7 | +384/-68 | tooling |  |
| 24 | `4ca0ae78` | MP-NEW-P208 enforce terminal role-review proof | 32 | +1077/-118 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `bridge.md` | docs | +62/-62 |
| `dev/active/MASTER_PLAN.md` | tooling | +8/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1284/-1321 |
| `dev/guides/SYSTEM_MAP.md` | docs | +22/-21 |
| `dev/scripts/README.md` | tooling | +1/-0 |
| `dev/scripts/checks/check_role_review_completed.py` | tooling | +12/-0 |
| `dev/scripts/checks/non_trivial_output_proof/command.py` | tooling | +1/-1 |
| `dev/scripts/checks/role_review_completed/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/role_review_completed/command.py` | tooling | +324/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/bypass/command.py` | tooling | +4/-0 |
| `dev/scripts/devctl/commands/bypass/expire.py` | tooling | +307/-39 |
| `dev/scripts/devctl/commands/bypass/expire_report.py` | tooling | +110/-0 |
| `dev/scripts/devctl/commands/raw_git.py` | tooling | +1/-1 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows_commit.py` | tooling | +30/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_pipeline.py` | tooling | +5/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_transitions.py` | tooling | +151/-0 |
| `dev/scripts/devctl/review_channel/packet_debt_ordering.py` | tooling | +27/-0 |
| `dev/scripts/devctl/review_channel/packet_debt_remediation.py` | tooling | +16/-1 |
| `dev/scripts/devctl/review_channel/packet_lifecycle.py` | tooling | +25/-15 |
| `dev/scripts/devctl/review_channel/packet_lifecycle_clock.py` | tooling | +0/-2 |
| `dev/scripts/devctl/review_channel/packet_plan_integration.py` | tooling | +2/-3 |
| `dev/scripts/devctl/runtime/bypass_lifecycle_closure.py` | tooling | +105/-0 |
| `dev/scripts/devctl/runtime/bypass_lifecycle_evaluation.py` | tooling | +33/-28 |
| `dev/scripts/devctl/runtime/bypass_lifecycle_receipts.py` | tooling | +42/-0 |
| `dev/scripts/devctl/runtime/commit_receipt.py` | tooling | +56/-26 |
| `dev/scripts/devctl/runtime/commit_to_plan_row_reducer.py` | tooling | +1/-12 |
| `dev/scripts/devctl/runtime/feature_proof_output_proof.py` | tooling | +48/-2 |
| `dev/scripts/devctl/runtime/feature_proof_receipt.py` | tooling | +12/-0 |
| `dev/scripts/devctl/runtime/feature_proof_role_review.py` | tooling | +61/-0 |
| `dev/scripts/devctl/runtime/feature_proof_test_refs.py` | tooling | +153/-1 |
| `dev/scripts/devctl/runtime/governed_transition_typechecker.py` | tooling | +341/-0 |
| `dev/scripts/devctl/runtime/governed_transition_typechecker_helpers.py` | tooling | +128/-0 |
| `dev/scripts/devctl/runtime/governed_transition_typechecker_models.py` | tooling | +106/-0 |
| `dev/scripts/devctl/runtime/packet_kind_ttl.py` | tooling | +17/-4 |
| `dev/scripts/devctl/runtime/ref_collections.py` | tooling | +22/-0 |
| `dev/scripts/devctl/runtime/remote_commit_pipeline_models.py` | tooling | +9/-8 |
| _23 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_parsers.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/governed_transition_typechecker_models.py`) — Commit aa840939 changed dev/scripts/devctl/runtime/governed_transition_typechecker_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Commit 4ca0ae78 changed dev/scripts/devctl/runtime/remote_commit_pipeline_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit 4ca0ae78 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`477f01ae`** — Refresh external review snapshot for 2a99a103
- **`2a99a103`** — Repair packet plan continuity state
- **`685d0892`** — Refresh external review snapshot for d7591b71
- **`d7591b71`** — Bind task-started packets to plan rows
- **`bfd73b2f`** — Refresh external review snapshot for 6f057634
- **`6f057634`** — Record ground-truth receipt for governance push
- **`be28caed`** — Refresh external review snapshot for 08895a8a
- **`08895a8a`** — Document role review completion guard
- **`f0577b3b`** — Refresh policy-owned generated surfaces for 996c3335
- **`996c3335`** — Refresh external review snapshot for c433c686
- **`c433c686` | MPs: MP-378** — MP-378 require resolvable pytest proof nodes
- **`b632df44`** — Refresh external review snapshot for ad84e97b
- **`ad84e97b` | MPs: MP-378** — MP-378 record pytest nodes in feature proof receipts
- **`00ab91b8`** — Refresh external review snapshot for 494e0914
- **`494e0914` | MPs: MP-378** — MP-378 require role review timeout governance chain
- **`b707ad20`** — Refresh external review snapshot for aa840939
- **`aa840939` | MPs: MP-378** — MP-378 add governed transition typechecker proof
- **`ab38e2a8`** — Refresh external review snapshot for b38d2bd7
- **`b38d2bd7` | MPs: MP-378** — MP-378 add bypass expire error code proof
- **`9283311c`** — Refresh external review snapshot for 54bb3a07
- **`54bb3a07` | MPs: MP-378** — MP-378 repair packet debt and bypass expiry proof
- **`12328ec3`** — Refresh external review snapshot for e9de52ef
- **`e9de52ef`** — MP-NEW-P209 add bypass expire CLI
- **`4ca0ae78`** — MP-NEW-P208 enforce terminal role-review proof
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
- checkpoint_before_continue: staged_index_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-7f05b63fba91` binds this file to HEAD `477f01aedd7b`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
