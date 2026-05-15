# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `a76b9b88dec0` — master-state-red: fix schema fixtures + dedup + system map refresh
- Tree hash: `3b0511979f57`
- Generation stamp: `snap-74c5eeb84fa8`
- Generated at (UTC): 2026-05-15T17:14:09Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 111 files, +5465/-970
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
- HEAD SHA: `a76b9b88dec0a6a610abd707a19357d4105bafa8`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-15T13:13:17-04:00

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
- publication_guidance: 44 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `a76b9b88dec0`

- commits: 24
- files changed: 111
- insertions: +5465
- deletions: -970
- bundle classes touched: tooling, docs
- authority surfaces touched: 2 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `a76b9b88` | master-state-red: fix schema fixtures + dedup + system map… | 29 | +796/-50 | tooling |  |
| 2 | `bfbcfe48` | Refresh external review snapshot for 7ebc3232 | 2 | +64/-62 | docs |  |
| 3 | `7ebc3232` | MP-NEW-P203: add decided packet debt triage | 27 | +660/-24 | tooling |  |
| 4 | `ded04ead` | Refresh external review snapshot for 7e366df7 | 2 | +57/-57 | docs |  |
| 5 | `7e366df7` | MP-NEW-P202: harden boot-card instruction sync | 9 | +117/-5 | tooling |  |
| 6 | `d2f2128d` | Refresh external review snapshot for 6b2937ef | 2 | +82/-82 | docs |  |
| 7 | `6b2937ef` | MP-NEW-P188-BRIDGE-GUARD-S2: expand bridge separation scope | 8 | +89/-10 | tooling |  |
| 8 | `be1ae2c4` | Refresh external review snapshot for ea2b4491 | 2 | +59/-59 | docs |  |
| 9 | `ea2b4491` | MP-NEW-P188-S4: quiet benign CLI health probe | 2 | +60/-1 | tooling |  |
| 10 | `a33e004f` | Refresh external review snapshot for 00ecc940 | 2 | +64/-79 | docs |  |
| 11 | `00ecc940` | MP-NEW-P188-S4: add CLI health recovery probe | 13 | +533/-14 | tooling |  |
| 12 | `330f1936` | Refresh external review snapshot for f3ac84bc | 2 | +64/-64 | docs |  |
| 13 | `f3ac84bc` | MP-NEW-P188-S3: add extension discipline guard-run check | 10 | +447/-13 | tooling |  |
| 14 | `b86a2a0a` | Refresh external review snapshot for f4ea765b | 2 | +60/-59 | docs |  |
| 15 | `f4ea765b` | MP-NEW-P188-S2: add implementer ack freshness check | 12 | +458/-2 | tooling |  |
| 16 | `bfff8e8e` | Refresh external review snapshot for 98e5e5de | 2 | +79/-85 | docs |  |
| 17 | `98e5e5de` | MP-NEW-P188-S1: keep implementer ack typed | 8 | +261/-14 | tooling |  |
| 18 | `f5cee955` | Refresh external review snapshot for 722ee4ec | 2 | +58/-55 | docs |  |
| 19 | `722ee4ec` | MP-NEW-P198-S2: add file-hash finding applicability | 24 | +798/-31 | tooling |  |
| 20 | `368cdc3c` | Refresh external review snapshot for 61069b1f | 2 | +62/-58 | docs |  |
| 21 | `61069b1f` | MP378-S7: add operator command wrappers | 12 | +371/-28 | tooling |  |
| 22 | `8b430a4a` | Refresh external review snapshot for 40689268 | 2 | +51/-51 | docs |  |
| 23 | `40689268` | MP378-S5: add provider-neutral role reset action | 5 | +114/-6 | tooling |  |
| 24 | `4e0f0759` | Refresh external review snapshot for fce1ff08 | 2 | +61/-61 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +3/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +9/-0 |
| `AGENTS.md` | docs | +2/-0 |
| `bridge.md` | docs | +92/-92 |
| `dev/active/MASTER_PLAN.md` | tooling | +13/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +15/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +707/-703 |
| `dev/guides/DEVELOPMENT.md` | docs | +34/-4 |
| `dev/guides/SYSTEM_MAP.md` | docs | +89/-88 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +129/-0 |
| `dev/scripts/README.md` | tooling | +27/-6 |
| `dev/scripts/checks/_ast_helpers.py` | tooling | +20/-0 |
| `dev/scripts/checks/check_action_result_status_domain.py` | tooling | +30/-17 |
| `dev/scripts/checks/runtime_bridge_projection_separation/command.py` | tooling | +30/-15 |
| `dev/scripts/checks/schema_fixture_handshake/command.py` | tooling | +36/-0 |
| `dev/scripts/checks/schema_fixture_handshake/git_tracking.py` | tooling | +38/-0 |
| `dev/scripts/devctl/cli_parser/hygiene.py` | tooling | +11/-0 |
| `dev/scripts/devctl/commands/development/models.py` | tooling | +16/-0 |
| `dev/scripts/devctl/commands/development/operator_command_wrappers.py` | tooling | +75/-0 |
| `dev/scripts/devctl/commands/development/plan_intake_phase0.py` | tooling | +2/-7 |
| `dev/scripts/devctl/commands/development/render.py` | tooling | +20/-0 |
| `dev/scripts/devctl/commands/development/report_assembly.py` | tooling | +90/-10 |
| `dev/scripts/devctl/commands/guard_run.py` | tooling | +30/-0 |
| `dev/scripts/devctl/commands/review_channel/__init__.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/review_channel/_reset_implementer.py` | tooling | +18/-5 |
| `dev/scripts/devctl/commands/review_channel/bridge_render.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/review_channel/cli_health_probe.py` | tooling | +320/-1 |
| `dev/scripts/devctl/commands/review_channel/event_ack_freshness_action.py` | tooling | +35/-0 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/review_channel/status.py` | tooling | +8/-2 |
| `dev/scripts/devctl/commands/review_channel_command/constants.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/review_channel_command/validation.py` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py` | tooling | +6/-0 |
| `dev/scripts/devctl/extend_discipline.py` | tooling | +274/-0 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +16/-1 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +6/-0 |
| `dev/scripts/devctl/governance/surface_instruction_runtime.py` | tooling | +34/-3 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows.py` | tooling | +2/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_development.py` | tooling | +32/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_development_roles.py` | tooling | +30/-0 |
| _71 more files trimmed_ | | |

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
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/governance_proposed_contracts.py`) — Commit a76b9b88 changed dev/scripts/devctl/runtime/governance_proposed_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_debt_remediation_contracts.py`) — Commit 7ebc3232 changed dev/scripts/devctl/review_channel/packet_debt_remediation_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/packet_debt_remediation_contracts.py`) — Commit 7ebc3232 changed dev/scripts/devctl/runtime/packet_debt_remediation_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/review_channel/test_ack_contract.py`) — Commit f4ea765b changed dev/scripts/devctl/tests/review_channel/test_ack_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit 722ee4ec changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit 722ee4ec changed dev/scripts/devctl/tests/platform/test_platform_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`a76b9b88`** — master-state-red: fix schema fixtures + dedup + system map refresh
  - - Add OperatorDirectivePacket fixture roots
  - - Dedup _call_name across check_action_result_status_domain + runtime_bridge_projection_separation
  - - Refresh SYSTEM_MAP via render-surfaces for new contracts
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`bfbcfe48`** — Refresh external review snapshot for 7ebc3232
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`7ebc3232`** — MP-NEW-P203: add decided packet debt triage
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`ded04ead`** — Refresh external review snapshot for 7e366df7
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`7e366df7`** — MP-NEW-P202: harden boot-card instruction sync
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`d2f2128d`** — Refresh external review snapshot for 6b2937ef
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`6b2937ef`** — MP-NEW-P188-BRIDGE-GUARD-S2: expand bridge separation scope
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`be1ae2c4`** — Refresh external review snapshot for ea2b4491
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`ea2b4491`** — MP-NEW-P188-S4: quiet benign CLI health probe
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`a33e004f`** — Refresh external review snapshot for 00ecc940
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`00ecc940`** — MP-NEW-P188-S4: add CLI health recovery probe
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`330f1936`** — Refresh external review snapshot for f3ac84bc
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`f3ac84bc`** — MP-NEW-P188-S3: add extension discipline guard-run check
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`b86a2a0a`** — Refresh external review snapshot for f4ea765b
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`f4ea765b`** — MP-NEW-P188-S2: add implementer ack freshness check
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`bfff8e8e`** — Refresh external review snapshot for 98e5e5de
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`98e5e5de`** — MP-NEW-P188-S1: keep implementer ack typed
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`f5cee955`** — Refresh external review snapshot for 722ee4ec
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`722ee4ec`** — MP-NEW-P198-S2: add file-hash finding applicability
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`368cdc3c`** — Refresh external review snapshot for 61069b1f
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`61069b1f`** — MP378-S7: add operator command wrappers
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`8b430a4a`** — Refresh external review snapshot for 40689268
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`40689268`** — MP378-S5: add provider-neutral role reset action
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
- **`4e0f0759`** — Refresh external review snapshot for fce1ff08
  - evolution: The P188 bridge-retirement work needed the report-only projection-authority guard to expose bridge-reader debt outside `dev/scripts/devctl/runtime/`. Before strict enforcement, the guard now scans runtime, review-channe…
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-74c5eeb84fa8` binds this file to HEAD `a76b9b88dec0`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
