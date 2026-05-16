# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `b707ad203b35` — Refresh external review snapshot for aa840939
- Tree hash: `608303e00c26`
- Generation stamp: `snap-388d9e7ba380`
- Generated at (UTC): 2026-05-16T20:34:06Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 203 files, +12885/-3379
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
- HEAD SHA: `b707ad203b35968aba0125bc5f732b6dc677120f`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-16T16:26:03-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 2
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: urgent
- publication_guidance: 19 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_before_continue` — dirty_after_local_checkpoint

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `b707ad203b35`

- commits: 25
- files changed: 203
- insertions: +12885
- deletions: -3379
- bundle classes touched: docs, tooling
- authority surfaces touched: 5 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `b707ad20` | Refresh external review snapshot for aa840939 | 2 | +58/-62 | docs |  |
| 2 | `aa840939` | MP-378 add governed transition typechecker proof | 8 | +1149/-68 | tooling |  |
| 3 | `ab38e2a8` | Refresh external review snapshot for b38d2bd7 | 2 | +59/-64 | docs |  |
| 4 | `b38d2bd7` | MP-378 add bypass expire error code proof | 7 | +61/-52 | tooling |  |
| 5 | `9283311c` | Refresh external review snapshot for 54bb3a07 | 2 | +66/-75 | docs |  |
| 6 | `54bb3a07` | MP-378 repair packet debt and bypass expiry proof | 19 | +800/-143 | tooling |  |
| 7 | `12328ec3` | Refresh external review snapshot for e9de52ef | 2 | +67/-73 | docs |  |
| 8 | `e9de52ef` | MP-NEW-P209 add bypass expire CLI | 7 | +384/-68 | tooling |  |
| 9 | `4ca0ae78` | MP-NEW-P208 enforce terminal role-review proof | 32 | +1077/-118 | tooling |  |
| 10 | `3e795e8e` | Refresh external review snapshot for eb937a97 | 2 | +52/-55 | docs |  |
| 11 | `eb937a97` | MP377-P0-T22AN-AB: record closure receipts for cf51bd8a | 2 | +4/-2 | tooling |  |
| 12 | `ba0512b6` | Refresh external review snapshot for cf51bd8a | 2 | +45/-49 | docs |  |
| 13 | `cf51bd8a` | MP377-P0-T22AN-AB: close role-review fixtures and TTL drift | 15 | +405/-20 | tooling |  |
| 14 | `a2746730` | Refresh external review snapshot for 55c53a5b | 2 | +67/-66 | docs |  |
| 15 | `55c53a5b` | Add role-review lifecycle and pytest policy proof | 16 | +861/-151 | tooling |  |
| 16 | `cdb1b09d` | Refresh external review snapshot for 82d5e789 | 2 | +44/-46 | docs |  |
| 17 | `82d5e789` | MP-NEW-P230-OUTPUT-TRUTH-SPINE-S1: record closure receipts | 2 | +2/-1 | tooling |  |
| 18 | `d0e99b9a` | Refresh external review snapshot for a3303fd5 | 2 | +88/-82 | docs |  |
| 19 | `a3303fd5` | MP-NEW-P230-OUTPUT-TRUTH-SPINE-S1: ship keystone proof spine | 126 | +4318/-300 | tooling |  |
| 20 | `e8dd613a` | Refresh external review snapshot for 850b9015 | 2 | +66/-66 | docs |  |
| 21 | `850b9015` | MP-NEW-P229-COMMIT-TO-PLAN-ROW-REDUCER-S1: persist plan-row… | 4 | +74/-1 | tooling |  |
| 22 | `9a3a0de4` | Refresh external review snapshot for 336c8c24 | 2 | +62/-63 | docs |  |
| 23 | `336c8c24` | MP-NEW-P229-COMMIT-TO-PLAN-ROW-REDUCER-S1: close plan rows… | 18 | +659/-32 | tooling |  |
| 24 | `fb449591` | Refresh external review snapshot for 051ac121 | 2 | +76/-72 | docs |  |
| 25 | `051ac121` | MP-NEW-P220-PHASE-0C-COMMIT-ANCHOR-REF-S1: add typed plan-r… | 32 | +2341/-1650 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +4/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +12/-0 |
| `bridge.md` | docs | +75/-75 |
| `dev/active/MASTER_PLAN.md` | tooling | +42/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +51/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1042/-1062 |
| `dev/config/devctl_repo_policy.json` | tooling | +9/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +29/-2 |
| `dev/guides/SYSTEM_MAP.md` | docs | +64/-62 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +67/-0 |
| `dev/scripts/README.md` | tooling | +27/-3 |
| `dev/scripts/checks/check_commit_message_row_id_resolves.py` | tooling | +90/-10 |
| `dev/scripts/checks/check_contract_registry_composite_key_uniqueness.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_non_trivial_output_proof.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_role_review_completed.py` | tooling | +12/-0 |
| `dev/scripts/checks/contract_registry_composite_key_uniqueness/command.py` | tooling | +326/-0 |
| `dev/scripts/checks/non_trivial_output_proof/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/non_trivial_output_proof/command.py` | tooling | +334/-1 |
| `dev/scripts/checks/pytest_runtime_policy/bundle_scan.py` | tooling | +30/-0 |
| `dev/scripts/checks/pytest_runtime_policy/command.py` | tooling | +1/-80 |
| `dev/scripts/checks/pytest_runtime_policy/config_policy.py` | tooling | +19/-0 |
| `dev/scripts/checks/pytest_runtime_policy/reporting.py` | tooling | +32/-0 |
| `dev/scripts/checks/pytest_runtime_policy/shell_command.py` | tooling | +150/-0 |
| `dev/scripts/checks/role_review_completed/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/role_review_completed/command.py` | tooling | +324/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/bypass/command.py` | tooling | +4/-0 |
| `dev/scripts/devctl/commands/bypass/expire.py` | tooling | +307/-39 |
| `dev/scripts/devctl/commands/bypass/expire_report.py` | tooling | +110/-0 |
| `dev/scripts/devctl/commands/development/plan_intake.py` | tooling | +25/-8 |
| `dev/scripts/devctl/commands/development/plan_intake_rows.py` | tooling | +27/-15 |
| `dev/scripts/devctl/commands/raw_git.py` | tooling | +84/-36 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/vcs/push_result_typestate.py` | tooling | +2/-1 |
| `dev/scripts/devctl/commands/vcs/raw_git_execution.py` | tooling | +114/-0 |
| `dev/scripts/devctl/context_graph/escalation.py` | tooling | +14/-3 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +6/-0 |
| `dev/scripts/devctl/platform/contract_registry.py` | tooling | +34/-1 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows_commit.py` | tooling | +153/-0 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows_role_review.py` | tooling | +115/-0 |
| _163 more files trimmed_ | | |

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/governed_transition_typechecker_models.py`) — Commit aa840939 changed dev/scripts/devctl/runtime/governed_transition_typechecker_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Commit 4ca0ae78 changed dev/scripts/devctl/runtime/remote_commit_pipeline_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit 4ca0ae78 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/bypass_lifecycle_models.py`) — Commit a3303fd5 changed dev/scripts/devctl/runtime/bypass_lifecycle_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/startup_context_models.py`) — Commit a3303fd5 changed dev/scripts/devctl/runtime/startup_context_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/master_plan_contract.py`) — Commit 051ac121 changed dev/scripts/devctl/runtime/master_plan_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`b707ad20`** — Refresh external review snapshot for aa840939
- **`aa840939` | MPs: MP-378** — MP-378 add governed transition typechecker proof
- **`ab38e2a8`** — Refresh external review snapshot for b38d2bd7
- **`b38d2bd7` | MPs: MP-378** — MP-378 add bypass expire error code proof
- **`9283311c`** — Refresh external review snapshot for 54bb3a07
- **`54bb3a07` | MPs: MP-378** — MP-378 repair packet debt and bypass expiry proof
- **`12328ec3`** — Refresh external review snapshot for e9de52ef
- **`e9de52ef`** — MP-NEW-P209 add bypass expire CLI
- **`4ca0ae78`** — MP-NEW-P208 enforce terminal role-review proof
- **`3e795e8e`** — Refresh external review snapshot for eb937a97
- **`eb937a97`** — MP377-P0-T22AN-AB: record closure receipts for cf51bd8a
- **`ba0512b6`** — Refresh external review snapshot for cf51bd8a
- **`cf51bd8a`** — MP377-P0-T22AN-AB: close role-review fixtures and TTL drift
- **`a2746730`** — Refresh external review snapshot for 55c53a5b
- **`55c53a5b`** — Add role-review lifecycle and pytest policy proof
- **`cdb1b09d`** — Refresh external review snapshot for 82d5e789
- **`82d5e789`** — MP-NEW-P230-OUTPUT-TRUTH-SPINE-S1: record closure receipts
  - Refs: a3303fd531efc130ce357703968e2b0e46993a7c rev_pkt_4157 rev_pkt_4171
- **`d0e99b9a`** — Refresh external review snapshot for a3303fd5
- **`a3303fd5`** — MP-NEW-P230-OUTPUT-TRUTH-SPINE-S1: ship keystone proof spine
  - Refs: rev_pkt_4157 rev_pkt_4164 rev_pkt_4165 rev_pkt_4166 rev_pkt_4167 rev_pkt_4168 rev_pkt_4169 rev_pkt_4170 rev_pkt_4171 rev_pkt_4175 rev_pkt_4180
- **`e8dd613a`** — Refresh external review snapshot for 850b9015
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`850b9015`** — MP-NEW-P229-COMMIT-TO-PLAN-ROW-REDUCER-S1: persist plan-row closure proof
  - Packet: rev_pkt_4147
  - Plan-Row: MP-NEW-P229-COMMIT-TO-PLAN-ROW-REDUCER-S1
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`9a3a0de4`** — Refresh external review snapshot for 336c8c24
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`336c8c24`** — MP-NEW-P229-COMMIT-TO-PLAN-ROW-REDUCER-S1: close plan rows from raw-git feature proof
  - Packet: rev_pkt_4147
  - Plan-Row: MP-NEW-P229-COMMIT-TO-PLAN-ROW-REDUCER-S1
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`fb449591`** — Refresh external review snapshot for 051ac121
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`051ac121`** — MP-NEW-P220-PHASE-0C-COMMIT-ANCHOR-REF-S1: add typed plan-row commit anchors
  - - Add PlanRow commit_anchor_ref and applied_at_utc fields with additive schema v2
  - - Hydrate applied/completed row commit anchors from legacy commit: anchor refs in plan intake and packet-plan integration
  - - Enforce post-Phase-0c typed commit anchors in P40 while preserving pre-window legacy compatibility
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
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
- checkpoint_before_continue: dirty_after_local_checkpoint

### Stale warnings
- Relaunch the reviewer loop immediately.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-388d9e7ba380` binds this file to HEAD `b707ad203b35`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
