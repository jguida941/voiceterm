# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `850b901508a6` — MP-NEW-P229-COMMIT-TO-PLAN-ROW-REDUCER-S1: persist plan-row closure proof
- Tree hash: `083caefa7427`
- Generation stamp: `snap-e4cbf06e02e0`
- Generated at (UTC): 2026-05-16T00:34:23Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 56 files, +5373/-2481
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
- HEAD SHA: `850b901508a6e36dfbd79bf9cb410ee78e777e35`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-15T20:33:36-04:00

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
- publication_backlog: recommended
- publication_guidance: 3 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `single_agent`
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

Range: last 25 commits ending at `850b901508a6`

- commits: 25
- files changed: 56
- insertions: +5373
- deletions: -2481
- bundle classes touched: tooling, docs

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `850b9015` | MP-NEW-P229-COMMIT-TO-PLAN-ROW-REDUCER-S1: persist plan-row… | 4 | +74/-1 | tooling |  |
| 2 | `9a3a0de4` | Refresh external review snapshot for 336c8c24 | 2 | +62/-63 | docs |  |
| 3 | `336c8c24` | MP-NEW-P229-COMMIT-TO-PLAN-ROW-REDUCER-S1: close plan rows… | 18 | +659/-32 | tooling |  |
| 4 | `fb449591` | Refresh external review snapshot for 051ac121 | 2 | +76/-72 | docs |  |
| 5 | `051ac121` | MP-NEW-P220-PHASE-0C-COMMIT-ANCHOR-REF-S1: add typed plan-r… | 32 | +2341/-1650 | tooling |  |
| 6 | `7bda6d5f` | Refresh external review snapshot for e83e34c4 | 2 | +64/-76 | docs |  |
| 7 | `e83e34c4` | MP-NEW-P223-WAKE-INTERVAL-TOGGLE-S1: ingest wake loop caden… | 3 | +18/-2 | tooling |  |
| 8 | `b28e1118` | Refresh external review snapshot for b0b79671 | 2 | +64/-67 | docs |  |
| 9 | `b0b79671` | MP-NEW-P220-PHASE-0B-PACKET-DECOMP-POLICY-S1: enforce packe… | 10 | +115/-5 | tooling |  |
| 10 | `31ed8016` | Refresh external review snapshot for bd560dd8 | 2 | +57/-51 | docs |  |
| 11 | `bd560dd8` | MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: harden commit row aut… | 10 | +190/-5 | tooling |  |
| 12 | `c5c10661` | Refresh external review snapshot for 5723a4dc | 2 | +60/-60 | docs |  |
| 13 | `5723a4dc` | MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: add row-id guard | 17 | +613/-26 | tooling |  |
| 14 | `de2facd0` | Refresh external review snapshot for 0acaba67 | 2 | +56/-55 | docs |  |
| 15 | `0acaba67` | MP-NEW-P220-S1: add TDD acceptance tests | 7 | +351/-1 | tooling |  |
| 16 | `5f6420b1` | Refresh external review snapshot for 71579a7e | 2 | +56/-55 | docs |  |
| 17 | `71579a7e` | MP-NEW-P220-S1: repair packet range title decomposition | 9 | +145/-20 | tooling |  |
| 18 | `1c0700a6` | Refresh external review snapshot for 55ee7b75 | 2 | +51/-49 | docs |  |
| 19 | `55ee7b75` | MP377-P0: close checkpoint automation plan row | 3 | +3/-1 | tooling |  |
| 20 | `431f8ee8` | Refresh external review snapshot for ef6b8496 | 2 | +61/-59 | docs |  |
| 21 | `ef6b8496` | PKT-BIND-REV-PKT-4132: ingest P219 system-map-first packet | 3 | +3/-0 | tooling |  |
| 22 | `07029b1e` | Refresh external review snapshot for 52f7c49f | 2 | +59/-58 | docs |  |
| 23 | `52f7c49f` | MP-NEW-P207-S4: fail closed on raw-git feature proof emissi… | 3 | +128/-11 | tooling |  |
| 24 | `023b3213` | Refresh external review snapshot for b14770b5 | 2 | +58/-58 | docs |  |
| 25 | `b14770b5` | MP377-P0: speed system-picture graph freshness | 2 | +9/-4 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `bridge.md` | docs | +48/-48 |
| `dev/active/MASTER_PLAN.md` | tooling | +30/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +60/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +676/-675 |
| `dev/config/devctl_repo_policy.json` | tooling | +24/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +33/-6 |
| `dev/guides/SYSTEM_MAP.md` | docs | +43/-42 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +93/-0 |
| `dev/scripts/README.md` | tooling | +12/-6 |
| `dev/scripts/checks/check_commit_message_row_id_resolves.py` | tooling | +512/-13 |
| `dev/scripts/devctl/commands/development/plan_intake.py` | tooling | +25/-8 |
| `dev/scripts/devctl/commands/development/plan_intake_decomposition.py` | tooling | +64/-13 |
| `dev/scripts/devctl/commands/development/plan_intake_rows.py` | tooling | +27/-15 |
| `dev/scripts/devctl/commands/raw_git.py` | tooling | +127/-19 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows_commit.py` | tooling | +42/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_plan_intake.py` | tooling | +53/-0 |
| `dev/scripts/devctl/platform/system_picture.py` | tooling | +7/-2 |
| `dev/scripts/devctl/review_channel/packet_plan_integration.py` | tooling | +26/-22 |
| `dev/scripts/devctl/runtime/commit_to_plan_row_reducer.py` | tooling | +333/-0 |
| `dev/scripts/devctl/runtime/feature_proof_receipt.py` | tooling | +5/-0 |
| `dev/scripts/devctl/runtime/master_plan_contract.py` | tooling | +86/-2 |
| `dev/scripts/devctl/runtime/master_plan_parse.py` | tooling | +10/-2 |
| `dev/scripts/devctl/tests/checks/test_check_commit_message_row_id_resolves.py` | tooling | +299/-5 |
| `dev/scripts/devctl/tests/checks/test_check_packet_decomposition_completeness.py` | tooling | +267/-6 |
| `dev/scripts/devctl/tests/commands/test_development_command.py` | tooling | +35/-0 |
| `dev/scripts/devctl/tests/commands/test_plan_intake_decomposition.py` | tooling | +62/-0 |
| `dev/scripts/devctl/tests/commands/test_raw_git.py` | tooling | +226/-0 |
| `dev/scripts/devctl/tests/platform/test_system_picture.py` | tooling | +2/-2 |
| `dev/scripts/devctl/tests/runtime/test_master_plan_contract_applied_commit_sha.py` | tooling | +75/-1 |
| `dev/state/contract_registry.jsonl` | tooling | +6/-4 |
| `dev/state/ground_truth_probe_receipts.jsonl` | tooling | +3/-0 |
| `dev/state/plan_index.jsonl` | tooling | +1621/-1589 |
| `dev/state/plan_ingestion_receipts.jsonl` | tooling | +36/-0 |
| `dev/state/plan_row_closure_receipts.jsonl` | tooling | +1/-0 |
| `dev/state/plan_source_snapshots.jsonl` | tooling | +57/-0 |
| `dev/test_data/schema_fixtures/AffectedTestSelection/2/invalid/missing-required-field.json` | tooling | +19/-0 |
| `dev/test_data/schema_fixtures/AffectedTestSelection/2/invalid/schema-version-mismatch.json` | tooling | +20/-0 |
| _16 more files trimmed_ | | |

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

- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/master_plan_contract.py`) — Commit 051ac121 changed dev/scripts/devctl/runtime/master_plan_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-e4cbf06e02e0` binds this file to HEAD `850b901508a6`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
