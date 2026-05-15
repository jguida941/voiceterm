# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `722ee4ec1266` — MP-NEW-P198-S2: add file-hash finding applicability
- Tree hash: `1ff211f9090b`
- Generation stamp: `snap-beb06d32787a`
- Generated at (UTC): 2026-05-15T11:10:43Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 87 files, +4886/-816
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
- HEAD SHA: `722ee4ec1266990520135124b46a4b1d0c76b513`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-15T07:09:36-04:00

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
- publication_guidance: 26 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 25 commits ending at `722ee4ec1266`

- commits: 25
- files changed: 87
- insertions: +4886
- deletions: -816
- bundle classes touched: docs, tooling

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `722ee4ec` | MP-NEW-P198-S2: add file-hash finding applicability | 24 | +798/-31 | tooling |  |
| 2 | `368cdc3c` | Refresh external review snapshot for 61069b1f | 2 | +62/-58 | docs |  |
| 3 | `61069b1f` | MP378-S7: add operator command wrappers | 12 | +371/-28 | tooling |  |
| 4 | `8b430a4a` | Refresh external review snapshot for 40689268 | 2 | +51/-51 | docs |  |
| 5 | `40689268` | MP378-S5: add provider-neutral role reset action | 5 | +114/-6 | tooling |  |
| 6 | `4e0f0759` | Refresh external review snapshot for fce1ff08 | 2 | +61/-61 | docs |  |
| 7 | `fce1ff08` | MP378-S6: keep bypass lifecycle store local | 14 | +417/-13 | tooling |  |
| 8 | `e94ef530` | Refresh external review snapshot for 85c11e92 | 2 | +59/-59 | docs |  |
| 9 | `85c11e92` | MP378-P4: add typed namespace composition guard | 29 | +737/-8 | tooling |  |
| 10 | `581f1432` | Refresh external review snapshot for 22833c80 | 2 | +50/-50 | docs |  |
| 11 | `22833c80` | MP378-P5: report authority contract registry gaps | 2 | +262/-0 | tooling |  |
| 12 | `606db95e` | Refresh external review snapshot for b0e6e5ff | 2 | +57/-57 | docs |  |
| 13 | `b0e6e5ff` | MP378-P3: add commit body packet anchor guard | 10 | +353/-25 | tooling |  |
| 14 | `8f15df5c` | Refresh external review snapshot for 77bbcd00 | 2 | +57/-57 | docs |  |
| 15 | `77bbcd00` | MP378-P7: add task started ADR precedent guard | 10 | +567/-8 | tooling |  |
| 16 | `4b2f1fd5` | Refresh external review snapshot for 8d188534 | 2 | +61/-64 | docs |  |
| 17 | `8d188534` | MP-GUARD-REGISTRY-S1: register guard contracts | 3 | +115/-29 | tooling |  |
| 18 | `95e759dc` | Refresh external review snapshot for 87460712 | 2 | +60/-57 | docs |  |
| 19 | `87460712` | MP193-S1: add check_action_result_status_domain guard (P193) | 1 | +210/-0 | tooling |  |
| 20 | `c2c4149e` | Refresh policy-owned generated surfaces for 57a978d7 | 1 | +1/-1 | docs |  |
| 21 | `57a978d7` | Refresh external review snapshot for c5219b9a | 2 | +58/-58 | docs |  |
| 22 | `c5219b9a` | MP-NEW-P200-S1: add operator directive role enum | 2 | +27/-0 | tooling |  |
| 23 | `2644aff7` | Refresh external review snapshot for f078228a | 2 | +86/-93 | docs |  |
| 24 | `f078228a` | MP-CONTROL-PLANE-S1: extend control_plane_quality preflight… | 2 | +62/-2 | tooling |  |
| 25 | `23d481ad` | MP181-S1: add check_context_graph_snapshot_freshness guard… | 3 | +190/-0 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +4/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +12/-0 |
| `bridge.md` | docs | +41/-41 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +621/-624 |
| `dev/config/devctl_repo_policy.json` | tooling | +20/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +124/-122 |
| `dev/scripts/checks/check_action_result_status_domain.py` | tooling | +210/-0 |
| `dev/scripts/checks/check_commit_body_packet_anchors.py` | tooling | +213/-0 |
| `dev/scripts/checks/check_context_graph_snapshot_freshness.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_runtime_state_ignore_posture.py` | tooling | +219/-0 |
| `dev/scripts/checks/check_task_started_adr_precedent_linking.py` | tooling | +330/-0 |
| `dev/scripts/checks/check_typed_namespace_composition.py` | tooling | +247/-0 |
| `dev/scripts/checks/context_graph_snapshot_freshness/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/context_graph_snapshot_freshness/command.py` | tooling | +177/-0 |
| `dev/scripts/checks/systemmap_covers_contract_registry/command.py` | tooling | +212/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +4/-0 |
| `dev/scripts/devctl/commands/development/models.py` | tooling | +16/-0 |
| `dev/scripts/devctl/commands/development/operator_command_wrappers.py` | tooling | +75/-0 |
| `dev/scripts/devctl/commands/development/plan_intake_phase0.py` | tooling | +2/-7 |
| `dev/scripts/devctl/commands/development/render.py` | tooling | +20/-0 |
| `dev/scripts/devctl/commands/development/report_assembly.py` | tooling | +90/-10 |
| `dev/scripts/devctl/commands/review_channel/__init__.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/review_channel/_reset_implementer.py` | tooling | +18/-5 |
| `dev/scripts/devctl/commands/review_channel_command/constants.py` | tooling | +1/-0 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +7/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows.py` | tooling | +2/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_development.py` | tooling | +32/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_plan_intake.py` | tooling | +237/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_quality_repair.py` | tooling | +133/-0 |
| `dev/scripts/devctl/review_channel/parser.py` | tooling | +1/-0 |
| `dev/scripts/devctl/runtime/control_plane_quality.py` | tooling | +20/-2 |
| `dev/scripts/devctl/runtime/file_hashes.py` | tooling | +27/-0 |
| `dev/scripts/devctl/runtime/quality_repair_scheduler.py` | tooling | +161/-0 |
| `dev/scripts/devctl/runtime/role_profile.py` | tooling | +14/-0 |
| `dev/scripts/devctl/runtime/session_liveness_reconciler.py` | tooling | +3/-0 |
| `dev/scripts/devctl/tests/checks/test_check_commit_body_packet_anchors.py` | tooling | +61/-0 |
| `dev/scripts/devctl/tests/checks/test_check_runtime_state_ignore_posture.py` | tooling | +92/-0 |
| `dev/scripts/devctl/tests/checks/test_check_systemmap_covers_contract_registry.py` | tooling | +50/-0 |
| `dev/scripts/devctl/tests/checks/test_check_task_started_adr_precedent_linking.py` | tooling | +163/-0 |
| `dev/scripts/devctl/tests/checks/test_check_typed_namespace_composition.py` | tooling | +89/-0 |
| _47 more files trimmed_ | | |

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

- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit 722ee4ec changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit 722ee4ec changed dev/scripts/devctl/tests/platform/test_platform_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`722ee4ec`** — MP-NEW-P198-S2: add file-hash finding applicability
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`368cdc3c`** — Refresh external review snapshot for 61069b1f
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`61069b1f`** — MP378-S7: add operator command wrappers
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`8b430a4a`** — Refresh external review snapshot for 40689268
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`40689268`** — MP378-S5: add provider-neutral role reset action
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`4e0f0759`** — Refresh external review snapshot for fce1ff08
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`fce1ff08`** — MP378-S6: keep bypass lifecycle store local
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`e94ef530`** — Refresh external review snapshot for 85c11e92
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`85c11e92`** — MP378-P4: add typed namespace composition guard
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`581f1432`** — Refresh external review snapshot for 22833c80
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`22833c80`** — MP378-P5: report authority contract registry gaps
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`606db95e`** — Refresh external review snapshot for b0e6e5ff
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`b0e6e5ff`** — MP378-P3: add commit body packet anchor guard
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`8f15df5c`** — Refresh external review snapshot for 77bbcd00
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`77bbcd00`** — MP378-P7: add task started ADR precedent guard
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`4b2f1fd5`** — Refresh external review snapshot for 8d188534
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`8d188534`** — MP-GUARD-REGISTRY-S1: register guard contracts
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`95e759dc`** — Refresh external review snapshot for 87460712
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`87460712`** — MP193-S1: add check_action_result_status_domain guard (P193)
  - Scans repo for status= keyword literals NOT in ActionOutcome.ALL =
  - {pass, fail, unknown, defer}. Surfaces the canonical 'typed boundary
  - lie' from GUARD_AUDIT_FINDINGS.md — declared closed domain + emitted
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`c2c4149e`** — Refresh policy-owned generated surfaces for 57a978d7
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`57a978d7`** — Refresh external review snapshot for c5219b9a
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`c5219b9a`** — MP-NEW-P200-S1: add operator directive role enum
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`2644aff7`** — Refresh external review snapshot for f078228a
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`f078228a`** — MP-CONTROL-PLANE-S1: extend control_plane_quality preflight handling
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`23d481ad`** — MP181-S1: add check_context_graph_snapshot_freshness guard (P181)
  - Mirrors check_review_snapshot_freshness package pattern. Validates
  - that the latest ContextGraphSnapshot in dev/reports/graph_snapshots/
  - matches current HEAD commit hash; reports drift in report-only mode.
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-beb06d32787a` binds this file to HEAD `722ee4ec1266`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
