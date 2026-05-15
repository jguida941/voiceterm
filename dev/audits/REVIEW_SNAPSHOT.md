# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `e83e34c4cb26` — MP-NEW-P223-WAKE-INTERVAL-TOGGLE-S1: ingest wake loop cadence plan rows
- Tree hash: `c29de07fdb34`
- Generation stamp: `snap-45ca2ef576a5`
- Generated at (UTC): 2026-05-15T23:07:56Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 49 files, +3690/-859
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
- HEAD SHA: `e83e34c4cb26c64cc5d02270184c53ad5ab5b92e`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-15T19:07:20-04:00

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

Range: last 25 commits ending at `e83e34c4cb26`

- commits: 25
- files changed: 49
- insertions: +3690
- deletions: -859
- bundle classes touched: tooling, docs

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `e83e34c4` | MP-NEW-P223-WAKE-INTERVAL-TOGGLE-S1: ingest wake loop caden… | 3 | +18/-2 | tooling |  |
| 2 | `b28e1118` | Refresh external review snapshot for b0b79671 | 2 | +64/-67 | docs |  |
| 3 | `b0b79671` | MP-NEW-P220-PHASE-0B-PACKET-DECOMP-POLICY-S1: enforce packe… | 10 | +115/-5 | tooling |  |
| 4 | `31ed8016` | Refresh external review snapshot for bd560dd8 | 2 | +57/-51 | docs |  |
| 5 | `bd560dd8` | MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: harden commit row aut… | 10 | +190/-5 | tooling |  |
| 6 | `c5c10661` | Refresh external review snapshot for 5723a4dc | 2 | +60/-60 | docs |  |
| 7 | `5723a4dc` | MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: add row-id guard | 17 | +613/-26 | tooling |  |
| 8 | `de2facd0` | Refresh external review snapshot for 0acaba67 | 2 | +56/-55 | docs |  |
| 9 | `0acaba67` | MP-NEW-P220-S1: add TDD acceptance tests | 7 | +351/-1 | tooling |  |
| 10 | `5f6420b1` | Refresh external review snapshot for 71579a7e | 2 | +56/-55 | docs |  |
| 11 | `71579a7e` | MP-NEW-P220-S1: repair packet range title decomposition | 9 | +145/-20 | tooling |  |
| 12 | `1c0700a6` | Refresh external review snapshot for 55ee7b75 | 2 | +51/-49 | docs |  |
| 13 | `55ee7b75` | MP377-P0: close checkpoint automation plan row | 3 | +3/-1 | tooling |  |
| 14 | `431f8ee8` | Refresh external review snapshot for ef6b8496 | 2 | +61/-59 | docs |  |
| 15 | `ef6b8496` | PKT-BIND-REV-PKT-4132: ingest P219 system-map-first packet | 3 | +3/-0 | tooling |  |
| 16 | `07029b1e` | Refresh external review snapshot for 52f7c49f | 2 | +59/-58 | docs |  |
| 17 | `52f7c49f` | MP-NEW-P207-S4: fail closed on raw-git feature proof emissi… | 3 | +128/-11 | tooling |  |
| 18 | `023b3213` | Refresh external review snapshot for b14770b5 | 2 | +58/-58 | docs |  |
| 19 | `b14770b5` | MP377-P0: speed system-picture graph freshness | 2 | +9/-4 | tooling |  |
| 20 | `62675b25` | Refresh external review snapshot for bf73cf9b | 2 | +75/-73 | docs |  |
| 21 | `bf73cf9b` | MP377-P0: allow edit-only plan override and align review re… | 19 | +494/-35 | tooling |  |
| 22 | `881b1cb5` | Refresh external review snapshot for 69f6fe21 | 2 | +53/-51 | docs |  |
| 23 | `69f6fe21` | reconcile governance plan rows from rev_pkt_4128 | 4 | +55/-7 | tooling |  |
| 24 | `43607fa3` | Refresh external review snapshot for 35fbdaf0 | 2 | +104/-95 | docs |  |
| 25 | `35fbdaf0` | raw-git: emit feature proof receipts | 19 | +812/-11 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +2/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +6/-0 |
| `bridge.md` | docs | +49/-49 |
| `dev/active/MASTER_PLAN.md` | tooling | +39/-2 |
| `dev/active/ai_governance_platform.md` | tooling | +53/-3 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +705/-682 |
| `dev/config/devctl_repo_policy.json` | tooling | +15/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +30/-6 |
| `dev/guides/SYSTEM_MAP.md` | docs | +30/-29 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +96/-0 |
| `dev/scripts/README.md` | tooling | +13/-3 |
| `dev/scripts/checks/check_commit_message_row_id_resolves.py` | tooling | +422/-3 |
| `dev/scripts/checks/check_feature_has_proof_receipt.py` | tooling | +239/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/development/plan_intake_decomposition.py` | tooling | +65/-14 |
| `dev/scripts/devctl/commands/raw_git.py` | tooling | +397/-12 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +2/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_plan_intake.py` | tooling | +53/-0 |
| `dev/scripts/devctl/platform/schema_migration_spine.py` | tooling | +14/-0 |
| `dev/scripts/devctl/platform/system_picture.py` | tooling | +7/-2 |
| `dev/scripts/devctl/review_channel/event_projection_assembly.py` | tooling | +6/-32 |
| `dev/scripts/devctl/review_channel/projection_bundle.py` | tooling | +4/-0 |
| `dev/scripts/devctl/review_channel/recovery_command_suppression.py` | tooling | +47/-0 |
| `dev/scripts/devctl/review_channel/status_bundle.py` | tooling | +5/-0 |
| `dev/scripts/devctl/runtime/agent_loop_decision.py` | tooling | +7/-0 |
| `dev/scripts/devctl/runtime/agent_loop_decision_builder.py` | tooling | +19/-2 |
| `dev/scripts/devctl/runtime/agent_loop_decision_support.py` | tooling | +20/-0 |
| `dev/scripts/devctl/runtime/agent_loop_policy.py` | tooling | +1/-0 |
| `dev/scripts/devctl/runtime/feature_proof_receipt.py` | tooling | +5/-0 |
| `dev/scripts/devctl/tests/checks/test_check_commit_message_row_id_resolves.py` | tooling | +209/-0 |
| `dev/scripts/devctl/tests/checks/test_check_feature_has_proof_receipt.py` | tooling | +79/-0 |
| `dev/scripts/devctl/tests/checks/test_check_packet_decomposition_completeness.py` | tooling | +196/-0 |
| `dev/scripts/devctl/tests/commands/test_development_command.py` | tooling | +36/-0 |
| `dev/scripts/devctl/tests/commands/test_plan_intake_decomposition.py` | tooling | +62/-0 |
| `dev/scripts/devctl/tests/commands/test_raw_git.py` | tooling | +147/-0 |
| `dev/scripts/devctl/tests/platform/test_system_picture.py` | tooling | +2/-2 |
| `dev/scripts/devctl/tests/review_channel/test_event_projection_push.py` | tooling | +170/-0 |
| `dev/scripts/devctl/tests/review_channel/test_projection_bundle.py` | tooling | +47/-0 |
| `dev/scripts/devctl/tests/review_channel/test_status_bundle_runtime_addenda.py` | tooling | +38/-0 |
| `dev/scripts/devctl/tests/runtime/test_agent_loop_decision.py` | tooling | +55/-0 |
| _9 more files trimmed_ | | |

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

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-45ca2ef576a5` binds this file to HEAD `e83e34c4cb26`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
