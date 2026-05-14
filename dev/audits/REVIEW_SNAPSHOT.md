# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `03d25016ff0a` — Add P102 BypassLifecycle bootstrap helper + launch wrapper
- Tree hash: `f0ba30e01550`
- Generation stamp: `snap-dcdb71ae41b1`
- Generated at (UTC): 2026-05-14T11:53:31Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 33 files, +1584/-1173
- Governance findings: 42 open / 0 fixed / 42 total
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
- HEAD SHA: `03d25016ff0ae08a2c0c497b6f22b18998b8171a`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-14T07:52:48-04:00

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
- publication_guidance: 39 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `03d25016ff0a`

- commits: 24
- files changed: 33
- insertions: +1584
- deletions: -1173
- bundle classes touched: docs, tooling

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `03d25016` | Add P102 BypassLifecycle bootstrap helper + launch wrapper | 4 | +136/-2 | tooling |  |
| 2 | `663147f9` | Refresh external review snapshot for b5d809fa | 2 | +50/-50 | docs |  |
| 3 | `b5d809fa` | MP377: deduplicate agents contract entrypoint | 1 | +9/-7 | tooling |  |
| 4 | `4c950e45` | Refresh external review snapshot for db6b6ba6 | 2 | +62/-70 | docs |  |
| 5 | `db6b6ba6` | MP377: package agents contract guard | 4 | +170/-156 | tooling |  |
| 6 | `5fe9282f` | Refresh external review snapshot for 2d494215 | 2 | +63/-58 | docs |  |
| 7 | `2d494215` | MP377: add boot card role discovery | 11 | +154/-18 | tooling |  |
| 8 | `e0ed1503` | Refresh external review snapshot for 7f5eef7e | 2 | +47/-47 | docs |  |
| 9 | `7f5eef7e` | Refresh bridge projection after progress packet | 1 | +3/-3 | docs |  |
| 10 | `7f43ac95` | Refresh external review snapshot for 252ca280 | 2 | +56/-58 | docs |  |
| 11 | `252ca280` | MP377: close automation opportunity packet slice | 3 | +4/-1 | tooling |  |
| 12 | `d799f7b0` | Refresh external review snapshot for ca3766c2 | 2 | +65/-61 | docs |  |
| 13 | `ca3766c2` | MP377: add automation opportunity packet kind | 8 | +163/-1 | tooling |  |
| 14 | `f5359bf3` | Refresh external review snapshot for 81f814f7 | 2 | +54/-60 | docs |  |
| 15 | `81f814f7` | MP377: close AutoInval producer wiring slice | 3 | +3/-1 | tooling |  |
| 16 | `76e9c859` | Refresh external review snapshot for 68d7def8 | 2 | +47/-47 | docs |  |
| 17 | `68d7def8` | MP377: avoid invalidation payload dict literal | 1 | +9/-10 | tooling |  |
| 18 | `aa63e907` | Refresh external review snapshot for 05d5d555 | 2 | +62/-62 | docs |  |
| 19 | `05d5d555` | MP377: type invalidation helper inputs | 7 | +174/-134 | tooling |  |
| 20 | `07afcf41` | Refresh external review snapshot for 56e25deb | 2 | +54/-55 | docs |  |
| 21 | `56e25deb` | MP377: refresh invalidation ground truth receipt | 1 | +2/-0 | tooling |  |
| 22 | `23755276` | Refresh external review snapshot for 5332adba | 2 | +59/-59 | docs |  |
| 23 | `5332adba` | MP377: remove invalidation facade wrappers | 7 | +70/-142 | tooling |  |
| 24 | `b03c5495` | Refresh external review snapshot for 24910ea9 | 2 | +68/-71 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +15/-6 |
| `bridge.md` | docs | +39/-39 |
| `dev/active/MASTER_PLAN.md` | tooling | +11/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +6/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +653/-664 |
| `dev/config/devctl_repo_policy.json` | tooling | +12/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +14/-4 |
| `dev/guides/SYSTEM_MAP.md` | docs | +1/-1 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +43/-0 |
| `dev/scripts/README.md` | tooling | +17/-5 |
| `dev/scripts/bootstrap_bypass_lifecycle.py` | tooling | +113/-0 |
| `dev/scripts/checks/agents_contract/command.py` | tooling | +169/-7 |
| `dev/scripts/checks/check_agents_contract.py` | tooling | +23/-153 |
| `dev/scripts/devctl/commands/development/plan_intake_receipts.py` | tooling | +33/-19 |
| `dev/scripts/devctl/commands/review_channel/event_post_wake_reports.py` | tooling | +24/-10 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +31/-2 |
| `dev/scripts/devctl/review_channel/packet_contract.py` | tooling | +3/-0 |
| `dev/scripts/devctl/review_channel/packet_debt_remediation.py` | tooling | +25/-13 |
| `dev/scripts/devctl/review_channel/packet_target_validation.py` | tooling | +1/-1 |
| `dev/scripts/devctl/review_channel/packet_transition_events.py` | tooling | +47/-26 |
| `dev/scripts/devctl/review_channel/session_liveness_events.py` | tooling | +23/-12 |
| `dev/scripts/devctl/runtime/derived_state_invalidation.py` | tooling | +64/-181 |
| `dev/scripts/devctl/tests/checks/test_check_agents_contract.py` | tooling | +20/-2 |
| `dev/scripts/devctl/tests/governance/test_render_surfaces.py` | tooling | +12/-0 |
| `dev/scripts/devctl/tests/review_channel/test_event_post_action.py` | tooling | +23/-0 |
| `dev/scripts/devctl/tests/review_channel/test_plan_packets.py` | tooling | +95/-0 |
| `dev/scripts/devctl/tests/runtime/test_derived_state_invalidation.py` | tooling | +37/-25 |
| `dev/scripts/launch_codex_with_bootstrap_receipt.sh` | tooling | +20/-0 |
| `dev/state/bypass_lifecycles.jsonl` | tooling | +1/-0 |
| `dev/state/ground_truth_probe_receipts.jsonl` | tooling | +2/-0 |
| `dev/state/plan_index.jsonl` | tooling | +2/-2 |
| `dev/state/plan_ingestion_receipts.jsonl` | tooling | +3/-0 |
| `dev/state/plan_source_snapshots.jsonl` | tooling | +2/-0 |

## 4. Quality signals

### Governance review
- total findings: 42
- open: 42
- fixed: 0
- false positives: 0

Recent findings:
- `work_board.rows_duplication` — `dev/scripts/devctl/runtime/agent_dispatch_router.py` (high, verdict=`confirmed_issue`)
- `dogfood.command.tandem-validate` — `dev/scripts/devctl/commands/governance/simple_lanes.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.pipeline` — `dev/scripts/devctl/commands/pipeline/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-audit` — `dev/scripts/devctl/commands/process/audit.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.check-router` — `dev/scripts/devctl/commands/check/router.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.push` — `dev/scripts/devctl/commands/vcs/push.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_tests.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_test_runner/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-cleanup` — `dev/scripts/devctl/commands/process/cleanup.py` (n/a, verdict=`confirmed_issue`)

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

- **contract_mutation**: Contract / typed model mutated (`dev/scripts/checks/check_agents_contract.py`) — Commit db6b6ba6 changed dev/scripts/checks/check_agents_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_check_agents_contract.py`) — Commit db6b6ba6 changed dev/scripts/devctl/tests/checks/test_check_agents_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit ca3766c2 changed dev/scripts/devctl/review_channel/packet_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`7f43ac95`** — Refresh external review snapshot for 252ca280
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`252ca280`** — MP377: close automation opportunity packet slice
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`d799f7b0`** — Refresh external review snapshot for ca3766c2
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`ca3766c2`** — MP377: add automation opportunity packet kind
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`f5359bf3`** — Refresh external review snapshot for 81f814f7
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`81f814f7`** — MP377: close AutoInval producer wiring slice
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`76e9c859`** — Refresh external review snapshot for 68d7def8
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`68d7def8`** — MP377: avoid invalidation payload dict literal
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`aa63e907`** — Refresh external review snapshot for 05d5d555
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`05d5d555`** — MP377: type invalidation helper inputs
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`07afcf41`** — Refresh external review snapshot for 56e25deb
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`56e25deb`** — MP377: refresh invalidation ground truth receipt
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`23755276`** — Refresh external review snapshot for 5332adba
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`5332adba`** — MP377: remove invalidation facade wrappers
  - evolution: Review-channel now has a dedicated `automation_opportunity` packet kind for automation candidates discovered from plan sections, packet bodies, and guard evidence. The kind composes with existing packet transport: posts…
- **`b03c5495`** — Refresh external review snapshot for 24910ea9
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- 2026-05-11 slice 18 fix arc + bilateral protocol consolidation (MP-377):
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b ev…
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:

## 8. Known gaps and open items

- open governance findings: 42

### Startup advisories
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/runtime/agent_dispatch_router.py`): work_board.rows_duplication: source_packet_ids=rev_pkt_2700,rev_pkt_2705; _work_board_rows logic is duplicated between packet_route_resolution.py and agent_dispatch_router.py. Durable owner: MP377-GUARDIR-WORK-BOARD-ROUTE-DEDUP.
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

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-dcdb71ae41b1` binds this file to HEAD `03d25016ff0a`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
