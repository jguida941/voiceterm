# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `5723a4dcc8a6` — MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: add row-id guard
- Tree hash: `1f71e0e16c80`
- Generation stamp: `snap-6879078027ef`
- Generated at (UTC): 2026-05-15T22:14:53Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 81 files, +5178/-879
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
- HEAD SHA: `5723a4dcc8a6370c8a26712f547b77de65a5ee6c`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-15T18:14:17-04:00

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

Range: last 24 commits ending at `5723a4dcc8a6`

- commits: 24
- files changed: 81
- insertions: +5178
- deletions: -879
- bundle classes touched: tooling, docs
- authority surfaces touched: 1 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `5723a4dc` | MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: add row-id guard | 17 | +613/-26 | tooling |  |
| 2 | `de2facd0` | Refresh external review snapshot for 0acaba67 | 2 | +56/-55 | docs |  |
| 3 | `0acaba67` | MP-NEW-P220-S1: add TDD acceptance tests | 7 | +351/-1 | tooling |  |
| 4 | `5f6420b1` | Refresh external review snapshot for 71579a7e | 2 | +56/-55 | docs |  |
| 5 | `71579a7e` | MP-NEW-P220-S1: repair packet range title decomposition | 9 | +145/-20 | tooling |  |
| 6 | `1c0700a6` | Refresh external review snapshot for 55ee7b75 | 2 | +51/-49 | docs |  |
| 7 | `55ee7b75` | MP377-P0: close checkpoint automation plan row | 3 | +3/-1 | tooling |  |
| 8 | `431f8ee8` | Refresh external review snapshot for ef6b8496 | 2 | +61/-59 | docs |  |
| 9 | `ef6b8496` | PKT-BIND-REV-PKT-4132: ingest P219 system-map-first packet | 3 | +3/-0 | tooling |  |
| 10 | `07029b1e` | Refresh external review snapshot for 52f7c49f | 2 | +59/-58 | docs |  |
| 11 | `52f7c49f` | MP-NEW-P207-S4: fail closed on raw-git feature proof emissi… | 3 | +128/-11 | tooling |  |
| 12 | `023b3213` | Refresh external review snapshot for b14770b5 | 2 | +58/-58 | docs |  |
| 13 | `b14770b5` | MP377-P0: speed system-picture graph freshness | 2 | +9/-4 | tooling |  |
| 14 | `62675b25` | Refresh external review snapshot for bf73cf9b | 2 | +75/-73 | docs |  |
| 15 | `bf73cf9b` | MP377-P0: allow edit-only plan override and align review re… | 19 | +494/-35 | tooling |  |
| 16 | `881b1cb5` | Refresh external review snapshot for 69f6fe21 | 2 | +53/-51 | docs |  |
| 17 | `69f6fe21` | reconcile governance plan rows from rev_pkt_4128 | 4 | +55/-7 | tooling |  |
| 18 | `43607fa3` | Refresh external review snapshot for 35fbdaf0 | 2 | +104/-95 | docs |  |
| 19 | `35fbdaf0` | raw-git: emit feature proof receipts | 19 | +812/-11 | tooling |  |
| 20 | `c39b26ef` | ingest-plan: materialize MP-NEW packet closure rows | 12 | +367/-8 | tooling |  |
| 21 | `d6fbbf81` | MP-NEW-P207: add FeatureProofReceipt emission | 25 | +693/-23 | tooling |  |
| 22 | `81711617` | Refresh external review snapshot for a76b9b88 | 2 | +72/-67 | docs |  |
| 23 | `a76b9b88` | master-state-red: fix schema fixtures + dedup + system map… | 29 | +796/-50 | tooling |  |
| 24 | `bfbcfe48` | Refresh external review snapshot for 7ebc3232 | 2 | +64/-62 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +5/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +15/-0 |
| `AGENTS.md` | docs | +1/-0 |
| `bridge.md` | docs | +45/-45 |
| `dev/active/MASTER_PLAN.md` | tooling | +51/-2 |
| `dev/active/ai_governance_platform.md` | tooling | +53/-3 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +664/-637 |
| `dev/config/devctl_repo_policy.json` | tooling | +11/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +44/-5 |
| `dev/guides/SYSTEM_MAP.md` | docs | +72/-71 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +143/-0 |
| `dev/scripts/README.md` | tooling | +34/-2 |
| `dev/scripts/checks/_ast_helpers.py` | tooling | +20/-0 |
| `dev/scripts/checks/check_action_result_status_domain.py` | tooling | +30/-17 |
| `dev/scripts/checks/check_commit_message_row_id_resolves.py` | tooling | +382/-0 |
| `dev/scripts/checks/check_feature_has_proof_receipt.py` | tooling | +239/-0 |
| `dev/scripts/checks/runtime_bridge_projection_separation/command.py` | tooling | +5/-8 |
| `dev/scripts/checks/schema_fixture_handshake/command.py` | tooling | +36/-0 |
| `dev/scripts/checks/schema_fixture_handshake/git_tracking.py` | tooling | +38/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/development/plan_intake.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/development/plan_intake_decomposition.py` | tooling | +222/-14 |
| `dev/scripts/devctl/commands/development/plan_intake_rows.py` | tooling | +52/-0 |
| `dev/scripts/devctl/commands/raw_git.py` | tooling | +397/-12 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py` | tooling | +20/-0 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +1/-0 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +2/-0 |
| `dev/scripts/devctl/platform/artifact_schema_rows.py` | tooling | +17/-0 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows_commit.py` | tooling | +81/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_development_roles.py` | tooling | +30/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_plan_intake.py` | tooling | +33/-0 |
| `dev/scripts/devctl/platform/schema_migration_spine.py` | tooling | +14/-0 |
| `dev/scripts/devctl/platform/system_picture.py` | tooling | +7/-2 |
| `dev/scripts/devctl/review_channel/event_projection_assembly.py` | tooling | +6/-32 |
| `dev/scripts/devctl/review_channel/projection_bundle.py` | tooling | +4/-0 |
| `dev/scripts/devctl/review_channel/recovery_command_suppression.py` | tooling | +47/-0 |
| `dev/scripts/devctl/review_channel/status_bundle.py` | tooling | +5/-0 |
| `dev/scripts/devctl/runtime/agent_loop_decision.py` | tooling | +7/-0 |
| `dev/scripts/devctl/runtime/agent_loop_decision_builder.py` | tooling | +19/-2 |
| `dev/scripts/devctl/runtime/agent_loop_decision_support.py` | tooling | +20/-0 |
| _41 more files trimmed_ | | |

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
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit d6fbbf81 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/governance_proposed_contracts.py`) — Commit a76b9b88 changed dev/scripts/devctl/runtime/governance_proposed_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`5723a4dc`** — MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: add row-id guard
  - Plan-Row: MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1
  - Packet: rev_pkt_4134
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`de2facd0`** — Refresh external review snapshot for 0acaba67
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`0acaba67`** — MP-NEW-P220-S1: add TDD acceptance tests
  - Plan-Row: MP-NEW-P220-TDD-FIRST-ACCEPTANCE-S1
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`5f6420b1`** — Refresh external review snapshot for 71579a7e
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`71579a7e`** — MP-NEW-P220-S1: repair packet range title decomposition
  - Plan-Row: MP-NEW-P220-PLAN-INTAKE-DECOMPOSITION-S1
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`1c0700a6`** — Refresh external review snapshot for 55ee7b75
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`55ee7b75` | MPs: MP-378** — MP377-P0: close checkpoint automation plan row
  - Plan-Row: MP377-P0-CHECKPOINT-AUTOMATION-S1
  - Packet: rev_pkt_4122
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`431f8ee8`** — Refresh external review snapshot for ef6b8496
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`ef6b8496`** — PKT-BIND-REV-PKT-4132: ingest P219 system-map-first packet
  - - Add typed plan row for rev_pkt_4132 after P207-S4 publication
  - - Persist PlanIntentIngestionReceipt and PlanSourceSnapshot evidence
  - - Verify active plan sync, plan-row contract refs, and tooling bundle
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`07029b1e`** — Refresh external review snapshot for 52f7c49f
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`52f7c49f`** — MP-NEW-P207-S4: fail closed on raw-git feature proof emission
  - Make raw-git return ok=false and a nonzero exit when required FeatureProofReceipt emission fails, instead of downgrading the failure to a warning. Add a regression that simulates a proof-store write failure and verifies the raw git receipt remains auditable while the command fails closed.\n\nProof:\n- python3 -m py_compile dev/scripts/devctl/commands/raw_git.py dev/scripts/devctl/runtime/feature_proof_receipt.py dev/scripts/devctl/tests/commands/test_raw_git.py\n- python3 dev/scripts/devctl.py test-python --suite devctl --path dev/scripts/devctl/tests/commands/test_raw_git.py --timeout-seconds 420 --per-test-timeout-seconds 90 --parallel-workers 1\n- python3 dev/scripts/devctl.py test-python --suite devctl --path dev/scripts/devctl/tests/checks/test_check_feature_has_proof_receipt.py --timeout-seconds 420 --per-test-timeout-seconds 90 --parallel-workers 1\n\nComposes with: rev_pkt_4129, rev_pkt_4131, MP-NEW-P207-S4.
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`023b3213`** — Refresh external review snapshot for b14770b5
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`b14770b5`** — MP377-P0: speed system-picture graph freshness
  - Use the bounded latest ContextGraphSnapshot resolver inside SystemPicture instead of loading the full graph snapshot archive. This keeps check_system_picture_freshness usable on the current repo archive, which is over 22 GB.\n\nProof:\n- python3 -m py_compile dev/scripts/devctl/platform/system_picture.py dev/scripts/devctl/tests/platform/test_system_picture.py\n- python3 dev/scripts/devctl.py test-python --suite devctl --path dev/scripts/devctl/tests/platform/test_system_picture.py --timeout-seconds 420 --per-test-timeout-seconds 90 --parallel-workers 1\n- python3 dev/scripts/devctl.py test-python --suite devctl --path dev/scripts/devctl/tests/context_graph/test_snapshot.py --timeout-seconds 420 --per-test-timeout-seconds 90 --parallel-workers 1\n- python3 dev/scripts/checks/check_system_picture_freshness.py --format md\n\nComposes with: MP377-P0-CHECKPOINT-AUTOMATION-S1 and R148/R159 proof-gate dogfood.
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`62675b25`** — Refresh external review snapshot for bf73cf9b
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`bf73cf9b`** — MP377-P0: allow edit-only plan override and align review recovery projections
  - Packet: rev_pkt_4122
  - Plan-Row: MP377-P0-CHECKPOINT-AUTOMATION-S1
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`881b1cb5`** — Refresh external review snapshot for 69f6fe21
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`69f6fe21`** — reconcile governance plan rows from rev_pkt_4128
  - - Absorb rev_pkt_4128 architectural correction into plan rows
  - - Materialize P212-P214 governance follow-up slices
  - - Record GovernanceReconciliationReceipt rejecting UnifiedSystemProjection
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`43607fa3`** — Refresh external review snapshot for 35fbdaf0
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`35fbdaf0`** — raw-git: emit feature proof receipts
  - - Emit FeatureProofReceipt artifacts from devctl raw-git commit
  - - Update pushed commit ranges with raw-git push receipt evidence
  - - Add check_feature_has_proof_receipt guard and workflow/bundle enforcement
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`c39b26ef`** — ingest-plan: materialize MP-NEW packet closure rows
  - - Add packet-body decomposer for concrete MP-NEW rows and bounded slice ranges
  - - Preserve PKT-BIND fallback for packets without closure row ids
  - - Let Rows-to-Ingest amendments update row titles while explicit plan-row evidence keeps owner titles
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`d6fbbf81` | MPs: MP-378** — MP-NEW-P207: add FeatureProofReceipt emission
  - - Add FeatureProofReceipt contract and artifact schema for commit-level feature proof
  - - Emit FeatureProofReceipt from governed commit success beside CommitReceipt and FeatureLifecycleProof
  - - Register FeatureProofReceipt fixtures and SYSTEM_MAP/contract-registry coverage
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`81711617`** — Refresh external review snapshot for a76b9b88
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`a76b9b88`** — master-state-red: fix schema fixtures + dedup + system map refresh
  - - Add OperatorDirectivePacket fixture roots
  - - Dedup _call_name across check_action_result_status_domain + runtime_bridge_projection_separation
  - - Refresh SYSTEM_MAP via render-surfaces for new contracts
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`bfbcfe48`** — Refresh external review snapshot for 7ebc3232
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-6879078027ef` binds this file to HEAD `5723a4dcc8a6`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
