# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `22833c80c1c4` — MP378-P5: report authority contract registry gaps
- Tree hash: `1d20ee4b452c`
- Generation stamp: `snap-cfacd906e652`
- Generated at (UTC): 2026-05-15T09:54:49Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 45 files, +3135/-932
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
- HEAD SHA: `22833c80c1c48738a28a35de1346fc5726cf35fc`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-15T05:53:47-04:00

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
- publication_guidance: 16 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `22833c80c1c4`

- commits: 24
- files changed: 45
- insertions: +3135
- deletions: -932
- bundle classes touched: tooling, docs

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `22833c80` | MP378-P5: report authority contract registry gaps | 2 | +262/-0 | tooling |  |
| 2 | `606db95e` | Refresh external review snapshot for b0e6e5ff | 2 | +57/-57 | docs |  |
| 3 | `b0e6e5ff` | MP378-P3: add commit body packet anchor guard | 10 | +353/-25 | tooling |  |
| 4 | `8f15df5c` | Refresh external review snapshot for 77bbcd00 | 2 | +57/-57 | docs |  |
| 5 | `77bbcd00` | MP378-P7: add task started ADR precedent guard | 10 | +567/-8 | tooling |  |
| 6 | `4b2f1fd5` | Refresh external review snapshot for 8d188534 | 2 | +61/-64 | docs |  |
| 7 | `8d188534` | MP-GUARD-REGISTRY-S1: register guard contracts | 3 | +115/-29 | tooling |  |
| 8 | `95e759dc` | Refresh external review snapshot for 87460712 | 2 | +60/-57 | docs |  |
| 9 | `87460712` | MP193-S1: add check_action_result_status_domain guard (P193) | 1 | +210/-0 | tooling |  |
| 10 | `c2c4149e` | Refresh policy-owned generated surfaces for 57a978d7 | 1 | +1/-1 | docs |  |
| 11 | `57a978d7` | Refresh external review snapshot for c5219b9a | 2 | +58/-58 | docs |  |
| 12 | `c5219b9a` | MP-NEW-P200-S1: add operator directive role enum | 2 | +27/-0 | tooling |  |
| 13 | `2644aff7` | Refresh external review snapshot for f078228a | 2 | +86/-93 | docs |  |
| 14 | `f078228a` | MP-CONTROL-PLANE-S1: extend control_plane_quality preflight… | 2 | +62/-2 | tooling |  |
| 15 | `23d481ad` | MP181-S1: add check_context_graph_snapshot_freshness guard… | 3 | +190/-0 | tooling |  |
| 16 | `b9359b7b` | MP122-S1: add check_plan_row_contract_refs_resolve guard (P… | 1 | +207/-0 | tooling |  |
| 17 | `94f106ca` | Refresh policy-owned generated surfaces for a0c651e6 | 1 | +1/-1 | docs |  |
| 18 | `a0c651e6` | Refresh external review snapshot for 2a767eba | 2 | +61/-61 | docs |  |
| 19 | `2a767eba` | Layout: convert crowded roots to shims | 5 | +119/-123 | tooling |  |
| 20 | `e0d2bb56` | Refresh external review snapshot for 895c1f0d | 2 | +57/-59 | docs |  |
| 21 | `895c1f0d` | Fixtures: cover new schema contracts | 16 | +350/-64 | tooling |  |
| 22 | `0df3d73c` | Refresh external review snapshot for a87c21a7 | 2 | +55/-55 | docs |  |
| 23 | `a87c21a7` | Receipt: refresh ground-truth probe preflight | 2 | +59/-58 | tooling |  |
| 24 | `65b42f88` | Refresh external review snapshot for eb5dbc30 | 2 | +60/-60 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +2/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +6/-0 |
| `bridge.md` | docs | +41/-41 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +756/-764 |
| `dev/config/devctl_repo_policy.json` | tooling | +10/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +63/-62 |
| `dev/scripts/checks/check_action_result_status_domain.py` | tooling | +210/-0 |
| `dev/scripts/checks/check_commit_body_packet_anchors.py` | tooling | +213/-0 |
| `dev/scripts/checks/check_context_graph_snapshot_freshness.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_plan_row_contract_refs_resolve.py` | tooling | +207/-0 |
| `dev/scripts/checks/check_runtime_bridge_projection_separation.py` | tooling | +1/-26 |
| `dev/scripts/checks/check_task_started_adr_precedent_linking.py` | tooling | +330/-0 |
| `dev/scripts/checks/context_graph_snapshot_freshness/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/context_graph_snapshot_freshness/command.py` | tooling | +177/-0 |
| `dev/scripts/checks/runtime_bridge_projection_separation/command.py` | tooling | +18/-1 |
| `dev/scripts/checks/systemmap_covers_contract_registry/command.py` | tooling | +212/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/quality_policy.py` | tooling | +6/-34 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +5/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_plan_intake.py` | tooling | +175/-0 |
| `dev/scripts/devctl/quality_policy/command.py` | tooling | +32/-0 |
| `dev/scripts/devctl/runtime/control_plane_quality.py` | tooling | +20/-2 |
| `dev/scripts/devctl/runtime/role_profile.py` | tooling | +14/-0 |
| `dev/scripts/devctl/tests/checks/test_check_commit_body_packet_anchors.py` | tooling | +61/-0 |
| `dev/scripts/devctl/tests/checks/test_check_systemmap_covers_contract_registry.py` | tooling | +50/-0 |
| `dev/scripts/devctl/tests/checks/test_check_task_started_adr_precedent_linking.py` | tooling | +163/-0 |
| `dev/scripts/devctl/tests/runtime/test_control_plane_read_model.py` | tooling | +42/-0 |
| `dev/scripts/devctl/tests/runtime/test_role_profile.py` | tooling | +13/-0 |
| `dev/state/contract_registry.jsonl` | tooling | +7/-2 |
| `dev/state/ground_truth_probe_receipts.jsonl` | tooling | +1/-0 |
| `dev/test_data/schema_fixtures/AffectedTestSelection/1/invalid/missing-required-field.json` | tooling | +19/-0 |
| `dev/test_data/schema_fixtures/AffectedTestSelection/1/invalid/schema-version-mismatch.json` | tooling | +20/-0 |
| `dev/test_data/schema_fixtures/AffectedTestSelection/1/valid/registry-row.json` | tooling | +18/-0 |
| `dev/test_data/schema_fixtures/BridgeSeparationGuard/1/invalid/missing-required-field.json` | tooling | +19/-0 |
| `dev/test_data/schema_fixtures/BridgeSeparationGuard/1/invalid/schema-version-mismatch.json` | tooling | +20/-0 |
| `dev/test_data/schema_fixtures/BridgeSeparationGuard/1/valid/registry-row.json` | tooling | +18/-0 |
| `dev/test_data/schema_fixtures/IngestionProvenance/1/invalid/missing-required-field.json` | tooling | +19/-0 |
| `dev/test_data/schema_fixtures/IngestionProvenance/1/invalid/schema-version-mismatch.json` | tooling | +20/-0 |
| `dev/test_data/schema_fixtures/IngestionProvenance/1/valid/registry-row.json` | tooling | +18/-0 |
| `dev/test_data/schema_fixtures/RoleCommandEnvelope/1/invalid/missing-required-field.json` | tooling | +19/-0 |
| _5 more files trimmed_ | | |

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
- **`b9359b7b`** — MP122-S1: add check_plan_row_contract_refs_resolve guard (P122)
  - Validates plan_index PlanRow contract refs resolve in contract_registry.
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`94f106ca`** — Refresh policy-owned generated surfaces for a0c651e6
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`a0c651e6`** — Refresh external review snapshot for 2a767eba
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`2a767eba`** — Layout: convert crowded roots to shims
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`e0d2bb56`** — Refresh external review snapshot for 895c1f0d
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`895c1f0d`** — Fixtures: cover new schema contracts
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`0df3d73c`** — Refresh external review snapshot for a87c21a7
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`a87c21a7`** — Receipt: refresh ground-truth probe preflight
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`65b42f88`** — Refresh external review snapshot for eb5dbc30
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-cfacd906e652` binds this file to HEAD `22833c80c1c4`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
