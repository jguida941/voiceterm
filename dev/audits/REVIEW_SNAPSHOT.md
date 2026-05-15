# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `df492548d630` — MP197: ingest continuous proof scheduler plan
- Tree hash: `75ee5b4c9516`
- Generation stamp: `snap-fe576b0ad0c9`
- Generated at (UTC): 2026-05-15T03:09:38Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 550 files, +13965/-1370
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
- HEAD SHA: `df492548d630a1c942528163ac80031095033842`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-14T23:09:00-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report_state: `post_push_green` (push_completed)
- publication_backlog: urgent
- publication_guidance: 9 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `df492548d630`

- commits: 24
- files changed: 550
- insertions: +13965
- deletions: -1370
- bundle classes touched: tooling, docs
- authority surfaces touched: 6 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `df492548` | MP197: ingest continuous proof scheduler plan | 5 | +160/-50 | tooling |  |
| 2 | `1ec9c8b1` | Refresh external review snapshot for dbd12b71 | 2 | +73/-75 | docs |  |
| 3 | `dbd12b71` | MP188: add runtime bridge separation guard | 14 | +472/-56 | tooling |  |
| 4 | `56d9ceb3` | Refresh external review snapshot for 8d406cee | 2 | +59/-59 | docs |  |
| 5 | `8d406cee` | MP189: ingest R127 wake continuity plan | 5 | +74/-50 | tooling |  |
| 6 | `c99b616c` | Refresh external review snapshot for 763075f1 | 2 | +67/-64 | docs |  |
| 7 | `763075f1` | MP188: register ingestion provenance | 11 | +142/-56 | tooling |  |
| 8 | `31dee106` | Refresh external review snapshot for b7b13c45 | 2 | +64/-64 | docs |  |
| 9 | `b7b13c45` | MP186: retarget R125 duplicate corrections | 18 | +303/-62 | tooling |  |
| 10 | `644389cd` | Refresh external review snapshot for 9272e871 | 2 | +63/-63 | docs |  |
| 11 | `9272e871` | MP381: stabilize push authorization during preflight | 12 | +270/-124 | tooling |  |
| 12 | `b049ba3a` | Refresh external review snapshot for 868e35c9 | 2 | +72/-77 | docs |  |
| 13 | `868e35c9` | MP381: read canonical push authorization | 14 | +223/-64 | tooling |  |
| 14 | `aee417b6` | Refresh external review snapshot for 866ce516 | 2 | +61/-65 | docs |  |
| 15 | `866ce516` | MP381: fix review-channel self-stop preflight | 12 | +177/-61 | tooling |  |
| 16 | `ff501228` | Refresh external review snapshot for d3b7a100 | 2 | +72/-68 | docs |  |
| 17 | `d3b7a100` | MP381: ingest R98 governance findings | 490 | +10105/-155 | tooling |  |
| 18 | `92488df1` | MP377: checkpoint packet-pressure bridge refresh | 1 | +1/-1 | docs |  |
| 19 | `ec6f330e` | MP378: summarize locked review events | 4 | +244/-53 | tooling |  |
| 20 | `e991f288` | MP377: checkpoint packet-pressure reductions | 3 | +3/-1 | tooling |  |
| 21 | `744a4aa9` | MP378: stream review-channel event reads | 5 | +93/-43 | tooling |  |
| 22 | `5fed0004` | MP377: checkpoint reviewer-mode packet reduction | 3 | +4/-2 | tooling |  |
| 23 | `8bd100f9` | MP377: checkpoint packet queue reductions | 3 | +9/-6 | tooling |  |
| 24 | `22cfecd2` | MP377: checkpoint repair field and portability guard | 38 | +1154/-51 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +2/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +6/-0 |
| `bridge.md` | docs | +75/-74 |
| `dev/active/MASTER_PLAN.md` | tooling | +209/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +53/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1033/-1025 |
| `dev/audits/r98_packet_4030_4038_plan_capture.md` | tooling | +75/-0 |
| `dev/audits/r98_push_authorization_projection_path.md` | tooling | +31/-0 |
| `dev/audits/r98_push_preflight_review_channel_timeout.md` | tooling | +23/-0 |
| `dev/config/devctl_repo_policy.json` | tooling | +34/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +33/-1 |
| `dev/guides/SYSTEM_MAP.md` | docs | +39/-36 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +126/-0 |
| `dev/scripts/README.md` | tooling | +26/-3 |
| `dev/scripts/checks/check_packet_pkt_bind_completeness.py` | tooling | +7/-0 |
| `dev/scripts/checks/check_plan_index_commit_continuity.py` | tooling | +29/-17 |
| `dev/scripts/checks/check_runtime_bridge_projection_separation.py` | tooling | +14/-0 |
| `dev/scripts/checks/check_substrate_is_repo_portable.py` | tooling | +10/-0 |
| `dev/scripts/checks/packet_pkt_bind_completeness/command.py` | tooling | +5/-1 |
| `dev/scripts/checks/packet_pkt_bind_completeness/constants.py` | tooling | +0/-2 |
| `dev/scripts/checks/packet_pkt_bind_completeness/core.py` | tooling | +19/-12 |
| `dev/scripts/checks/repo_portability/__init__.py` | tooling | +5/-0 |
| `dev/scripts/checks/repo_portability/command.py` | tooling | +376/-0 |
| `dev/scripts/checks/runtime_bridge_projection_separation/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/runtime_bridge_projection_separation/command.py` | tooling | +220/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/review_channel/_stop.py` | tooling | +14/-0 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +9/-10 |
| `dev/scripts/devctl/commands/vcs/governed_executor.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +17/-66 |
| `dev/scripts/devctl/commands/vcs/push_publication_gate.py` | tooling | +115/-0 |
| `dev/scripts/devctl/governance/push_state_authorization.py` | tooling | +3/-8 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +5/-0 |
| `dev/scripts/devctl/platform/contract_registry.py` | tooling | +2/-2 |
| `dev/scripts/devctl/platform/contract_registry_models.py` | tooling | +4/-2 |
| `dev/scripts/devctl/platform/contracts.py` | tooling | +2/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows.py` | tooling | +8/-2 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_governance_proposed.py` | tooling | +335/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_pipeline.py` | tooling | +5/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_plan_intake.py` | tooling | +25/-0 |
| _510 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/platform/contracts.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/remote_commit_pipeline_artifact.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/contract_registry_models.py`) — Commit 763075f1 changed dev/scripts/devctl/platform/contract_registry_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/contracts.py`) — Commit 763075f1 changed dev/scripts/devctl/platform/contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit 763075f1 changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/governance_proposed_contracts.py`) — Commit b7b13c45 changed dev/scripts/devctl/runtime/governance_proposed_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/master_plan_contract.py`) — Commit b7b13c45 changed dev/scripts/devctl/runtime/master_plan_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Commit 22cfecd2 changed dev/scripts/devctl/runtime/remote_commit_pipeline_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit 22cfecd2 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`df492548`** — MP197: ingest continuous proof scheduler plan
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`1ec9c8b1`** — Refresh external review snapshot for dbd12b71
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`dbd12b71`** — MP188: add runtime bridge separation guard
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`56d9ceb3`** — Refresh external review snapshot for 8d406cee
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`8d406cee`** — MP189: ingest R127 wake continuity plan
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`c99b616c`** — Refresh external review snapshot for 763075f1
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`763075f1`** — MP188: register ingestion provenance
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`31dee106`** — Refresh external review snapshot for b7b13c45
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`b7b13c45`** — MP186: retarget R125 duplicate corrections
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`644389cd`** — Refresh external review snapshot for 9272e871
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`9272e871`** — MP381: stabilize push authorization during preflight
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`b049ba3a`** — Refresh external review snapshot for 868e35c9
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`868e35c9`** — MP381: read canonical push authorization
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`aee417b6`** — Refresh external review snapshot for 866ce516
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`866ce516`** — MP381: fix review-channel self-stop preflight
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`ff501228`** — Refresh external review snapshot for d3b7a100
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`d3b7a100`** — MP381: ingest R98 governance findings
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`92488df1`** — MP377: checkpoint packet-pressure bridge refresh
  - Checkpoint bridge projection after dismissing stale May 9 packet-pressure owner gaps. No push per operator batch-push mandate.
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`ec6f330e`** — MP378: summarize locked review events
  - Avoid materializing the full review-channel trace during append_event. The locked append path now streams a bounded summary for id allocation, packet lifecycle idempotency, and lineage lookup. Focused review-channel tests pass, and review-channel status smoked against the live trace.
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`e991f288`** — MP377: checkpoint packet-pressure reductions
  - Record the current bridge hash and PKT-BIND-REV-PKT-4038 plan binding after dismissing stale May 9 packet-pressure owner gaps.
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`744a4aa9`** — MP378: stream review-channel event reads
  - Avoid full trace materialization in load_events and append_event locked reads. Adds focused regression coverage that fails if those paths call Path.read_text. Also checkpoints current packet-intake projections through rev_pkt_4037.
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`5fed0004`** — MP377: checkpoint reviewer-mode packet reduction
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`8bd100f9`** — MP377: checkpoint packet queue reductions
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`22cfecd2`** — MP377: checkpoint repair field and portability guard
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-fe576b0ad0c9` binds this file to HEAD `df492548d630`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
