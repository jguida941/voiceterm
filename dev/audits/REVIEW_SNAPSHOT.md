# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `3e795e8ea8f7` — Refresh external review snapshot for eb937a97
- Tree hash: `6feacc217154`
- Generation stamp: `snap-c5ff5fb05280`
- Generated at (UTC): 2026-05-16T17:09:23Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 177 files, +10345/-2948
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
- HEAD SHA: `3e795e8ea8f7fe7ff56c490378116275a55844ff`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-16T11:20:43-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 30
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: urgent
- publication_guidance: 10 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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

Range: last 24 commits ending at `3e795e8ea8f7`

- commits: 24
- files changed: 177
- insertions: +10345
- deletions: -2948
- bundle classes touched: docs, tooling
- authority surfaces touched: 3 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `3e795e8e` | Refresh external review snapshot for eb937a97 | 2 | +52/-55 | docs |  |
| 2 | `eb937a97` | MP377-P0-T22AN-AB: record closure receipts for cf51bd8a | 2 | +4/-2 | tooling |  |
| 3 | `ba0512b6` | Refresh external review snapshot for cf51bd8a | 2 | +45/-49 | docs |  |
| 4 | `cf51bd8a` | MP377-P0-T22AN-AB: close role-review fixtures and TTL drift | 15 | +405/-20 | tooling |  |
| 5 | `a2746730` | Refresh external review snapshot for 55c53a5b | 2 | +67/-66 | docs |  |
| 6 | `55c53a5b` | Add role-review lifecycle and pytest policy proof | 16 | +861/-151 | tooling |  |
| 7 | `cdb1b09d` | Refresh external review snapshot for 82d5e789 | 2 | +44/-46 | docs |  |
| 8 | `82d5e789` | MP-NEW-P230-OUTPUT-TRUTH-SPINE-S1: record closure receipts | 2 | +2/-1 | tooling |  |
| 9 | `d0e99b9a` | Refresh external review snapshot for a3303fd5 | 2 | +88/-82 | docs |  |
| 10 | `a3303fd5` | MP-NEW-P230-OUTPUT-TRUTH-SPINE-S1: ship keystone proof spine | 126 | +4318/-300 | tooling |  |
| 11 | `e8dd613a` | Refresh external review snapshot for 850b9015 | 2 | +66/-66 | docs |  |
| 12 | `850b9015` | MP-NEW-P229-COMMIT-TO-PLAN-ROW-REDUCER-S1: persist plan-row… | 4 | +74/-1 | tooling |  |
| 13 | `9a3a0de4` | Refresh external review snapshot for 336c8c24 | 2 | +62/-63 | docs |  |
| 14 | `336c8c24` | MP-NEW-P229-COMMIT-TO-PLAN-ROW-REDUCER-S1: close plan rows… | 18 | +659/-32 | tooling |  |
| 15 | `fb449591` | Refresh external review snapshot for 051ac121 | 2 | +76/-72 | docs |  |
| 16 | `051ac121` | MP-NEW-P220-PHASE-0C-COMMIT-ANCHOR-REF-S1: add typed plan-r… | 32 | +2341/-1650 | tooling |  |
| 17 | `7bda6d5f` | Refresh external review snapshot for e83e34c4 | 2 | +64/-76 | docs |  |
| 18 | `e83e34c4` | MP-NEW-P223-WAKE-INTERVAL-TOGGLE-S1: ingest wake loop caden… | 3 | +18/-2 | tooling |  |
| 19 | `b28e1118` | Refresh external review snapshot for b0b79671 | 2 | +64/-67 | docs |  |
| 20 | `b0b79671` | MP-NEW-P220-PHASE-0B-PACKET-DECOMP-POLICY-S1: enforce packe… | 10 | +115/-5 | tooling |  |
| 21 | `31ed8016` | Refresh external review snapshot for bd560dd8 | 2 | +57/-51 | docs |  |
| 22 | `bd560dd8` | MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: harden commit row aut… | 10 | +190/-5 | tooling |  |
| 23 | `c5c10661` | Refresh external review snapshot for 5723a4dc | 2 | +60/-60 | docs |  |
| 24 | `5723a4dc` | MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: add row-id guard | 17 | +613/-26 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +4/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +12/-0 |
| `bridge.md` | docs | +55/-55 |
| `dev/active/MASTER_PLAN.md` | tooling | +54/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +86/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +763/-776 |
| `dev/config/devctl_repo_policy.json` | tooling | +24/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +44/-5 |
| `dev/guides/SYSTEM_MAP.md` | docs | +70/-68 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +107/-0 |
| `dev/scripts/README.md` | tooling | +30/-5 |
| `dev/scripts/checks/check_commit_message_row_id_resolves.py` | tooling | +512/-13 |
| `dev/scripts/checks/check_contract_registry_composite_key_uniqueness.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_non_trivial_output_proof.py` | tooling | +12/-0 |
| `dev/scripts/checks/contract_registry_composite_key_uniqueness/command.py` | tooling | +326/-0 |
| `dev/scripts/checks/non_trivial_output_proof/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/non_trivial_output_proof/command.py` | tooling | +333/-0 |
| `dev/scripts/checks/pytest_runtime_policy/bundle_scan.py` | tooling | +30/-0 |
| `dev/scripts/checks/pytest_runtime_policy/command.py` | tooling | +1/-80 |
| `dev/scripts/checks/pytest_runtime_policy/config_policy.py` | tooling | +19/-0 |
| `dev/scripts/checks/pytest_runtime_policy/reporting.py` | tooling | +32/-0 |
| `dev/scripts/checks/pytest_runtime_policy/shell_command.py` | tooling | +150/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/development/plan_intake.py` | tooling | +25/-8 |
| `dev/scripts/devctl/commands/development/plan_intake_rows.py` | tooling | +27/-15 |
| `dev/scripts/devctl/commands/raw_git.py` | tooling | +83/-35 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/vcs/push_result_typestate.py` | tooling | +2/-1 |
| `dev/scripts/devctl/commands/vcs/raw_git_execution.py` | tooling | +114/-0 |
| `dev/scripts/devctl/context_graph/escalation.py` | tooling | +14/-3 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +6/-0 |
| `dev/scripts/devctl/platform/contract_registry.py` | tooling | +34/-1 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows_commit.py` | tooling | +123/-0 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows_role_review.py` | tooling | +115/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_development.py` | tooling | +2/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_development_packets.py` | tooling | +55/-1 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_plan_intake.py` | tooling | +53/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_plan_keystones.py` | tooling | +95/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_review.py` | tooling | +24/-4 |
| `dev/scripts/devctl/quality_policy/defaults.py` | tooling | +10/-0 |
| _137 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit 55c53a5b changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
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
- **`7bda6d5f`** — Refresh external review snapshot for e83e34c4
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`e83e34c4`** — MP-NEW-P223-WAKE-INTERVAL-TOGGLE-S1: ingest wake loop cadence plan rows
  - - Materialize R176 wake/loop cadence rows for WakeIntervalToggle, LoopCadencePolicy, and LoopCadenceReceipt\n- Repair P222 memory-ingestion titles after packet reducer ambiguity\n- Keep MP-NEW-P222-MEMORY-INGEST-S1 as superseded alias\n\nPacket: rev_pkt_4141\nRows: MP-NEW-P223-WAKE-INTERVAL-TOGGLE-S1, MP-NEW-P223-LOOP-CADENCE-POLICY-S2, MP-NEW-P223-LOOP-CADENCE-RECEIPT-S3, MP-NEW-P222-MEMORY-INGESTION-S1
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`b28e1118`** — Refresh external review snapshot for b0b79671
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`b0b79671`** — MP-NEW-P220-PHASE-0B-PACKET-DECOMP-POLICY-S1: enforce packet decomposition policy
  - - Make packet decomposition count only rows accepted by active enforced_row_prefixes\n- Add regressions for off-policy MP-NEW rows and P207 accepted rows\n- Absorb rev_pkt_4140 into corrected P221/P222/FPR-v2 plan rows\n- Keep bridge.md unstaged as projection-only\n\nPacket: rev_pkt_4140\nRows: MP-NEW-P220-PHASE-0B-PACKET-DECOMP-POLICY-S1, MP-NEW-P221-S1, MP-NEW-P221-S2, MP-NEW-P221-S3, MP-NEW-P222-MEMORY-INGESTION-S1, MP-NEW-P222-MEMORY-INGESTION-S2, MP-NEW-P207-S5-FPR-V2-CONTRACTREF-S1
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`31ed8016`** — Refresh external review snapshot for bd560dd8
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`bd560dd8`** — MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: harden commit row authority guard
  - - Widen commit row-id enforcement to active P207/P208/P218/P219/P220 plan families
  - - Run packet decomposition checks independently from row-prefix enforcement
  - - Echo scan range and mandate metadata in CommitMessageRowIdResolvesGuard reports
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`c5c10661`** — Refresh external review snapshot for 5723a4dc
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`5723a4dc`** — MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: add row-id guard
  - Plan-Row: MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1
  - Packet: rev_pkt_4134
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-c5ff5fb05280` binds this file to HEAD `3e795e8ea8f7`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
