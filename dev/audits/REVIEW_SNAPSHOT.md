# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `eb871172360b` — MP378: add plan-index commit continuity guard
- Tree hash: `adde5393d4a2`
- Generation stamp: `snap-c3b565ae625e`
- Generated at (UTC): 2026-05-14T16:06:28Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 83 files, +6086/-833
- Governance findings: 43 open / 0 fixed / 43 total
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
- HEAD SHA: `eb871172360ba7410a4506e335d63caea3151ef2`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-14T12:05:38-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report_state: `blocked` (push_preflight_running)
- publication_backlog: urgent
- publication_guidance: 54 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `eb871172360b`

- commits: 24
- files changed: 83
- insertions: +6086
- deletions: -833
- bundle classes touched: tooling, docs
- authority surfaces touched: 2 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `eb871172` | MP378: add plan-index commit continuity guard | 17 | +763/-10 | tooling |  |
| 2 | `1dc4bd2c` | Refresh external review snapshot for 7357c966 | 2 | +64/-65 | docs |  |
| 3 | `7357c966` | Record S4 review acceptance packet binding | 3 | +7/-5 | tooling |  |
| 4 | `c30ba06f` | Refresh external review snapshot for 8b4e647e | 1 | +104/-94 | tooling |  |
| 5 | `8b4e647e` | MP378: add session liveness reconciler | 22 | +989/-14 | tooling |  |
| 6 | `39216f9d` | MP378: enforce system map contract coverage | 20 | +533/-5 | tooling |  |
| 7 | `9fd28931` | MP378: close classifier attestation plan row | 3 | +3/-1 | tooling |  |
| 8 | `1b33360d` | MP378: add classifier safety attestation | 19 | +938/-12 | tooling |  |
| 9 | `68dc3810` | MP378: close session status plan row | 3 | +3/-1 | tooling |  |
| 10 | `50cdb5a7` | MP378: add session status projection | 25 | +1294/-12 | tooling |  |
| 11 | `89b08bd5` | Refresh external review snapshot for 9a5ac82b | 2 | +50/-51 | docs |  |
| 12 | `9a5ac82b` | MP378: close bypass grant plan row | 4 | +7/-5 | tooling |  |
| 13 | `9c944574` | Refresh external review snapshot for f5e91409 | 2 | +71/-64 | docs |  |
| 14 | `f5e91409` | MP378: add bypass grant CLI | 15 | +501/-15 | tooling |  |
| 15 | `9fa76099` | Refresh external review snapshot for 03d25016 | 2 | +65/-68 | docs |  |
| 16 | `03d25016` | Add P102 BypassLifecycle bootstrap helper + launch wrapper | 4 | +136/-2 | tooling |  |
| 17 | `663147f9` | Refresh external review snapshot for b5d809fa | 2 | +50/-50 | docs |  |
| 18 | `b5d809fa` | MP377: deduplicate agents contract entrypoint | 1 | +9/-7 | tooling |  |
| 19 | `4c950e45` | Refresh external review snapshot for db6b6ba6 | 2 | +62/-70 | docs |  |
| 20 | `db6b6ba6` | MP377: package agents contract guard | 4 | +170/-156 | tooling |  |
| 21 | `5fe9282f` | Refresh external review snapshot for 2d494215 | 2 | +63/-58 | docs |  |
| 22 | `2d494215` | MP377: add boot card role discovery | 11 | +154/-18 | tooling |  |
| 23 | `e0ed1503` | Refresh external review snapshot for 7f5eef7e | 2 | +47/-47 | docs |  |
| 24 | `7f5eef7e` | Refresh bridge projection after progress packet | 1 | +3/-3 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/README.md` | tooling | +2/-2 |
| `.github/workflows/release_preflight.yml` | tooling | +2/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +6/-0 |
| `AGENTS.md` | docs | +15/-6 |
| `bridge.md` | docs | +45/-44 |
| `dev/active/MASTER_PLAN.md` | tooling | +76/-6 |
| `dev/active/ai_governance_platform.md` | tooling | +49/-5 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +551/-542 |
| `dev/config/devctl_repo_policy.json` | tooling | +12/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +37/-7 |
| `dev/guides/SYSTEM_MAP.md` | docs | +61/-24 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +142/-0 |
| `dev/scripts/README.md` | tooling | +48/-6 |
| `dev/scripts/bootstrap_bypass_lifecycle.py` | tooling | +113/-0 |
| `dev/scripts/checks/agents_contract/command.py` | tooling | +169/-7 |
| `dev/scripts/checks/check_agents_contract.py` | tooling | +23/-153 |
| `dev/scripts/checks/check_plan_index_commit_continuity.py` | tooling | +379/-0 |
| `dev/scripts/checks/check_systemmap_covers_contract_registry.py` | tooling | +12/-0 |
| `dev/scripts/checks/systemmap_covers_contract_registry/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/systemmap_covers_contract_registry/command.py` | tooling | +226/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +2/-0 |
| `dev/scripts/devctl/cli.py` | tooling | +15/-13 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/bypass/__init__.py` | tooling | +7/-0 |
| `dev/scripts/devctl/commands/bypass/command.py` | tooling | +445/-2 |
| `dev/scripts/devctl/commands/governance/session.py` | tooling | +46/-1 |
| `dev/scripts/devctl/commands/governance/session_reconcile.py` | tooling | +152/-0 |
| `dev/scripts/devctl/commands/listing.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/listing/__init__.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/review_channel/status_runtime_projection.py` | tooling | +1/-0 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +31/-2 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +5/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_bypass_lifecycle.py` | tooling | +58/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_review_core.py` | tooling | +128/-0 |
| `dev/scripts/devctl/platform/system_map.py` | tooling | +56/-1 |
| `dev/scripts/devctl/platform/system_map_models.py` | tooling | +2/-0 |
| `dev/scripts/devctl/review_channel/README.md` | tooling | +3/-1 |
| `dev/scripts/devctl/review_channel/agent_loop_decision_route_scope.py` | tooling | +4/-0 |
| `dev/scripts/devctl/review_channel/event_projection_assembly.py` | tooling | +18/-0 |
| _43 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 43
- open: 43
- fixed: 0
- false positives: 0

Recent findings:
- `dogfood.command.tandem-validate` — `dev/scripts/devctl/commands/governance/simple_lanes.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.pipeline` — `dev/scripts/devctl/commands/pipeline/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-audit` — `dev/scripts/devctl/commands/process/audit.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.check-router` — `dev/scripts/devctl/commands/check/router.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.push` — `dev/scripts/devctl/commands/vcs/push.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_tests.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_test_runner/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-cleanup` — `dev/scripts/devctl/commands/process/cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/system_map_models.py`) — Commit 39216f9d changed dev/scripts/devctl/platform/system_map_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit 50cdb5a7 changed dev/scripts/devctl/runtime/review_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/checks/check_agents_contract.py`) — Commit db6b6ba6 changed dev/scripts/checks/check_agents_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_check_agents_contract.py`) — Commit db6b6ba6 changed dev/scripts/devctl/tests/checks/test_check_agents_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`eb871172`** — MP378: add plan-index commit continuity guard
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`1dc4bd2c`** — Refresh external review snapshot for 7357c966
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`7357c966`** — Record S4 review acceptance packet binding
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`c30ba06f`** — Refresh external review snapshot for 8b4e647e
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`8b4e647e`** — MP378: add session liveness reconciler
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`39216f9d`** — MP378: enforce system map contract coverage
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`9fd28931`** — MP378: close classifier attestation plan row
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`1b33360d`** — MP378: add classifier safety attestation
  - Decision: .claude/settings.local.json stays gitignored operator-local projection state; BypassLifecycle/BypassReceipt remain the durable authority. Decision: if Bash(*) already dominates the provider classifier allow-list, project the receipt-scoped rules but emit classifier_dominated_by_bash_wildcard in the projection result/settings bridge so S3 does not imply narrower operational effect until a later hardening slice removes the wildcard. Adds direct runtime tests plus CLI lockstep tests, platform contract registry/fixtures, docs, and generated surface refresh.
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`68dc3810`** — MP378: close session status plan row
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`50cdb5a7`** — MP378: add session status projection
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`89b08bd5`** — Refresh external review snapshot for 9a5ac82b
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`9a5ac82b`** — MP378: close bypass grant plan row
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`9c944574`** — Refresh external review snapshot for f5e91409
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`f5e91409`** — MP378: add bypass grant CLI
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`9fa76099`** — Refresh external review snapshot for 03d25016
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`03d25016`** — Add P102 BypassLifecycle bootstrap helper + launch wrapper
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`663147f9`** — Refresh external review snapshot for b5d809fa
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`b5d809fa`** — MP377: deduplicate agents contract entrypoint
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`4c950e45`** — Refresh external review snapshot for db6b6ba6
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`db6b6ba6`** — MP377: package agents contract guard
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`5fe9282f`** — Refresh external review snapshot for 2d494215
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`2d494215`** — MP377: add boot card role discovery
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`e0ed1503`** — Refresh external review snapshot for 7f5eef7e
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`7f5eef7e`** — Refresh bridge projection after progress packet
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
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

- open governance findings: 43

### Startup advisories
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/governance/simple_lanes.py`): dogfood.command.tandem-validate: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
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

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-c3b565ae625e` binds this file to HEAD `eb871172360b`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
