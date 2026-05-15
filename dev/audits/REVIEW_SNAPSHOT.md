# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `bf73cf9b52b3` — MP377-P0: allow edit-only plan override and align review recovery projections
- Tree hash: `84854611003c`
- Generation stamp: `snap-cf6b96cfbb78`
- Generated at (UTC): 2026-05-15T19:30:37Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 108 files, +6339/-963
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
- HEAD SHA: `bf73cf9b52b3a561a3a0ded7105da52ee3ff452e`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-15T15:30:03-04:00

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

Range: last 24 commits ending at `bf73cf9b52b3`

- commits: 24
- files changed: 108
- insertions: +6339
- deletions: -963
- bundle classes touched: tooling, docs
- authority surfaces touched: 2 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `bf73cf9b` | MP377-P0: allow edit-only plan override and align review re… | 19 | +494/-35 | tooling |  |
| 2 | `881b1cb5` | Refresh external review snapshot for 69f6fe21 | 2 | +53/-51 | docs |  |
| 3 | `69f6fe21` | reconcile governance plan rows from rev_pkt_4128 | 4 | +55/-7 | tooling |  |
| 4 | `43607fa3` | Refresh external review snapshot for 35fbdaf0 | 2 | +104/-95 | docs |  |
| 5 | `35fbdaf0` | raw-git: emit feature proof receipts | 19 | +812/-11 | tooling |  |
| 6 | `c39b26ef` | ingest-plan: materialize MP-NEW packet closure rows | 12 | +367/-8 | tooling |  |
| 7 | `d6fbbf81` | MP-NEW-P207: add FeatureProofReceipt emission | 25 | +693/-23 | tooling |  |
| 8 | `81711617` | Refresh external review snapshot for a76b9b88 | 2 | +72/-67 | docs |  |
| 9 | `a76b9b88` | master-state-red: fix schema fixtures + dedup + system map… | 29 | +796/-50 | tooling |  |
| 10 | `bfbcfe48` | Refresh external review snapshot for 7ebc3232 | 2 | +64/-62 | docs |  |
| 11 | `7ebc3232` | MP-NEW-P203: add decided packet debt triage | 27 | +660/-24 | tooling |  |
| 12 | `ded04ead` | Refresh external review snapshot for 7e366df7 | 2 | +57/-57 | docs |  |
| 13 | `7e366df7` | MP-NEW-P202: harden boot-card instruction sync | 9 | +117/-5 | tooling |  |
| 14 | `d2f2128d` | Refresh external review snapshot for 6b2937ef | 2 | +82/-82 | docs |  |
| 15 | `6b2937ef` | MP-NEW-P188-BRIDGE-GUARD-S2: expand bridge separation scope | 8 | +89/-10 | tooling |  |
| 16 | `be1ae2c4` | Refresh external review snapshot for ea2b4491 | 2 | +59/-59 | docs |  |
| 17 | `ea2b4491` | MP-NEW-P188-S4: quiet benign CLI health probe | 2 | +60/-1 | tooling |  |
| 18 | `a33e004f` | Refresh external review snapshot for 00ecc940 | 2 | +64/-79 | docs |  |
| 19 | `00ecc940` | MP-NEW-P188-S4: add CLI health recovery probe | 13 | +533/-14 | tooling |  |
| 20 | `330f1936` | Refresh external review snapshot for f3ac84bc | 2 | +64/-64 | docs |  |
| 21 | `f3ac84bc` | MP-NEW-P188-S3: add extension discipline guard-run check | 10 | +447/-13 | tooling |  |
| 22 | `b86a2a0a` | Refresh external review snapshot for f4ea765b | 2 | +60/-59 | docs |  |
| 23 | `f4ea765b` | MP-NEW-P188-S2: add implementer ack freshness check | 12 | +458/-2 | tooling |  |
| 24 | `bfff8e8e` | Refresh external review snapshot for 98e5e5de | 2 | +79/-85 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +4/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +12/-0 |
| `AGENTS.md` | docs | +3/-0 |
| `bridge.md` | docs | +88/-88 |
| `dev/active/MASTER_PLAN.md` | tooling | +39/-2 |
| `dev/active/ai_governance_platform.md` | tooling | +43/-3 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +708/-695 |
| `dev/guides/DEVELOPMENT.md` | docs | +52/-4 |
| `dev/guides/SYSTEM_MAP.md` | docs | +71/-71 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +192/-0 |
| `dev/scripts/README.md` | tooling | +47/-3 |
| `dev/scripts/checks/_ast_helpers.py` | tooling | +20/-0 |
| `dev/scripts/checks/check_action_result_status_domain.py` | tooling | +30/-17 |
| `dev/scripts/checks/check_feature_has_proof_receipt.py` | tooling | +239/-0 |
| `dev/scripts/checks/runtime_bridge_projection_separation/command.py` | tooling | +30/-15 |
| `dev/scripts/checks/schema_fixture_handshake/command.py` | tooling | +36/-0 |
| `dev/scripts/checks/schema_fixture_handshake/git_tracking.py` | tooling | +38/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/cli_parser/hygiene.py` | tooling | +11/-0 |
| `dev/scripts/devctl/commands/development/plan_intake.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/development/plan_intake_decomposition.py` | tooling | +158/-1 |
| `dev/scripts/devctl/commands/development/plan_intake_rows.py` | tooling | +52/-0 |
| `dev/scripts/devctl/commands/guard_run.py` | tooling | +30/-0 |
| `dev/scripts/devctl/commands/raw_git.py` | tooling | +339/-1 |
| `dev/scripts/devctl/commands/review_channel/bridge_render.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/review_channel/cli_health_probe.py` | tooling | +320/-1 |
| `dev/scripts/devctl/commands/review_channel/event_ack_freshness_action.py` | tooling | +35/-0 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/review_channel/status.py` | tooling | +8/-2 |
| `dev/scripts/devctl/commands/review_channel_command/constants.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/review_channel_command/validation.py` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py` | tooling | +20/-0 |
| `dev/scripts/devctl/extend_discipline.py` | tooling | +274/-0 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +17/-1 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +7/-0 |
| `dev/scripts/devctl/governance/surface_instruction_runtime.py` | tooling | +34/-3 |
| `dev/scripts/devctl/platform/artifact_schema_rows.py` | tooling | +17/-0 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows_commit.py` | tooling | +81/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_development_roles.py` | tooling | +30/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_packet_debt.py` | tooling | +108/-0 |
| _68 more files trimmed_ | | |

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_render.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit d6fbbf81 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/governance_proposed_contracts.py`) — Commit a76b9b88 changed dev/scripts/devctl/runtime/governance_proposed_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_debt_remediation_contracts.py`) — Commit 7ebc3232 changed dev/scripts/devctl/review_channel/packet_debt_remediation_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/packet_debt_remediation_contracts.py`) — Commit 7ebc3232 changed dev/scripts/devctl/runtime/packet_debt_remediation_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/review_channel/test_ack_contract.py`) — Commit f4ea765b changed dev/scripts/devctl/tests/review_channel/test_ack_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`7ebc3232`** — MP-NEW-P203: add decided packet debt triage
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`ded04ead`** — Refresh external review snapshot for 7e366df7
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`7e366df7`** — MP-NEW-P202: harden boot-card instruction sync
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`d2f2128d`** — Refresh external review snapshot for 6b2937ef
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`6b2937ef`** — MP-NEW-P188-BRIDGE-GUARD-S2: expand bridge separation scope
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`be1ae2c4`** — Refresh external review snapshot for ea2b4491
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`ea2b4491`** — MP-NEW-P188-S4: quiet benign CLI health probe
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`a33e004f`** — Refresh external review snapshot for 00ecc940
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`00ecc940`** — MP-NEW-P188-S4: add CLI health recovery probe
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`330f1936`** — Refresh external review snapshot for f3ac84bc
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`f3ac84bc`** — MP-NEW-P188-S3: add extension discipline guard-run check
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`b86a2a0a`** — Refresh external review snapshot for f4ea765b
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`f4ea765b`** — MP-NEW-P188-S2: add implementer ack freshness check
  - evolution: The MP377 checkpoint automation slice exposed a reducer mismatch: an active edit-only operator override for a typed plan target could still return `wait_for_scoped_packet` when no scoped packet was claimable, making the…
- **`bfff8e8e`** — Refresh external review snapshot for 98e5e5de
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-cf6b96cfbb78` binds this file to HEAD `bf73cf9b52b3`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
