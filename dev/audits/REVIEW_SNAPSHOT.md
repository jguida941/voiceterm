# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `9ae64f257a1f` — Refresh external review snapshot for cd177c3e
- Tree hash: `7ac453be7fda`
- Generation stamp: `snap-3a419271cc53`
- Generated at (UTC): 2026-05-15T05:11:57Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 47 files, +3001/-1526
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
- HEAD SHA: `9ae64f257a1f7b58929c7f9158173312fde7ac8c`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-15T00:55:05-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 3
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: urgent
- publication_guidance: 17 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_before_continue` — dirty_after_local_checkpoint

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `9ae64f257a1f`

- commits: 24
- files changed: 47
- insertions: +3001
- deletions: -1526
- bundle classes touched: docs, tooling
- authority surfaces touched: 2 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `9ae64f25` | Refresh external review snapshot for cd177c3e | 2 | +60/-61 | docs |  |
| 2 | `cd177c3e` | Docs: catalog runtime bridge separation guard | 2 | +53/-53 | tooling |  |
| 3 | `3c98c2ed` | Refresh external review snapshot for 372ea699 | 2 | +66/-68 | docs |  |
| 4 | `372ea699` | Docs: record governed push docs-check repair | 5 | +106/-56 | tooling |  |
| 5 | `b34748b3` | Refresh policy-owned generated surfaces for 8353fc05 | 1 | +28/-27 | docs |  |
| 6 | `8353fc05` | Refresh external review snapshot for e9aad0df | 2 | +62/-60 | docs |  |
| 7 | `e9aad0df` | MP188-S1.1: expand bridge guard FORBIDDEN_MODULE_FRAGMENTS… | 10 | +219/-88 | tooling |  |
| 8 | `1b42c70e` | Refresh external review snapshot for df492548 | 2 | +55/-55 | docs |  |
| 9 | `df492548` | MP197: ingest continuous proof scheduler plan | 5 | +160/-50 | tooling |  |
| 10 | `1ec9c8b1` | Refresh external review snapshot for dbd12b71 | 2 | +73/-75 | docs |  |
| 11 | `dbd12b71` | MP188: add runtime bridge separation guard | 14 | +472/-56 | tooling |  |
| 12 | `56d9ceb3` | Refresh external review snapshot for 8d406cee | 2 | +59/-59 | docs |  |
| 13 | `8d406cee` | MP189: ingest R127 wake continuity plan | 5 | +74/-50 | tooling |  |
| 14 | `c99b616c` | Refresh external review snapshot for 763075f1 | 2 | +67/-64 | docs |  |
| 15 | `763075f1` | MP188: register ingestion provenance | 11 | +142/-56 | tooling |  |
| 16 | `31dee106` | Refresh external review snapshot for b7b13c45 | 2 | +64/-64 | docs |  |
| 17 | `b7b13c45` | MP186: retarget R125 duplicate corrections | 18 | +303/-62 | tooling |  |
| 18 | `644389cd` | Refresh external review snapshot for 9272e871 | 2 | +63/-63 | docs |  |
| 19 | `9272e871` | MP381: stabilize push authorization during preflight | 12 | +270/-124 | tooling |  |
| 20 | `b049ba3a` | Refresh external review snapshot for 868e35c9 | 2 | +72/-77 | docs |  |
| 21 | `868e35c9` | MP381: read canonical push authorization | 14 | +223/-64 | tooling |  |
| 22 | `aee417b6` | Refresh external review snapshot for 866ce516 | 2 | +61/-65 | docs |  |
| 23 | `866ce516` | MP381: fix review-channel self-stop preflight | 12 | +177/-61 | tooling |  |
| 24 | `ff501228` | Refresh external review snapshot for d3b7a100 | 2 | +72/-68 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `bridge.md` | docs | +83/-83 |
| `dev/active/MASTER_PLAN.md` | tooling | +202/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +20/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1314/-1314 |
| `dev/audits/r98_push_authorization_projection_path.md` | tooling | +31/-0 |
| `dev/audits/r98_push_preflight_review_channel_timeout.md` | tooling | +23/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +20/-1 |
| `dev/guides/SYSTEM_MAP.md` | docs | +29/-28 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +83/-1 |
| `dev/scripts/README.md` | tooling | +23/-3 |
| `dev/scripts/checks/check_runtime_bridge_projection_separation.py` | tooling | +38/-1 |
| `dev/scripts/checks/runtime_bridge_projection_separation/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/runtime_bridge_projection_separation/command.py` | tooling | +228/-1 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/_stop.py` | tooling | +14/-0 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +17/-66 |
| `dev/scripts/devctl/commands/vcs/push_publication_gate.py` | tooling | +115/-0 |
| `dev/scripts/devctl/governance/push_state_authorization.py` | tooling | +3/-8 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +4/-0 |
| `dev/scripts/devctl/platform/contract_registry.py` | tooling | +2/-2 |
| `dev/scripts/devctl/platform/contract_registry_models.py` | tooling | +4/-2 |
| `dev/scripts/devctl/platform/contracts.py` | tooling | +2/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows.py` | tooling | +4/-2 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_plan_intake.py` | tooling | +49/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_review_pipeline.py` | tooling | +43/-0 |
| `dev/scripts/devctl/probe_report/artifacts.py` | tooling | +9/-0 |
| `dev/scripts/devctl/review_channel/action_request.py` | tooling | +2/-0 |
| `dev/scripts/devctl/review_channel/action_request_delivery.py` | tooling | +8/-0 |
| `dev/scripts/devctl/review_channel/remote_commit_pipeline_artifact.py` | tooling | +37/-0 |
| `dev/scripts/devctl/review_probe_report.py` | tooling | +4/-1 |
| `dev/scripts/devctl/runtime/evidence_receipts.py` | tooling | +21/-0 |
| `dev/scripts/devctl/runtime/governance_proposed_contracts.py` | tooling | +0/-1 |
| `dev/scripts/devctl/runtime/master_plan_contract.py` | tooling | +13/-0 |
| `dev/scripts/devctl/runtime/push_authorization.py` | tooling | +4/-6 |
| `dev/scripts/devctl/runtime/role_customization.py` | tooling | +11/-0 |
| `dev/scripts/devctl/tests/checks/test_check_runtime_bridge_projection_separation.py` | tooling | +95/-0 |
| `dev/scripts/devctl/tests/review_channel/test_review_channel.py` | tooling | +4/-4 |
| `dev/scripts/devctl/tests/review_channel/test_stop.py` | tooling | +47/-0 |
| _7 more files trimmed_ | | |

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
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/contract_registry_models.py`) — Commit 763075f1 changed dev/scripts/devctl/platform/contract_registry_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/contracts.py`) — Commit 763075f1 changed dev/scripts/devctl/platform/contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit 763075f1 changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/governance_proposed_contracts.py`) — Commit b7b13c45 changed dev/scripts/devctl/runtime/governance_proposed_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/master_plan_contract.py`) — Commit b7b13c45 changed dev/scripts/devctl/runtime/master_plan_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`9ae64f25`** — Refresh external review snapshot for cd177c3e
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`cd177c3e`** — Docs: catalog runtime bridge separation guard
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`3c98c2ed`** — Refresh external review snapshot for 372ea699
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`372ea699`** — Docs: record governed push docs-check repair
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`b34748b3`** — Refresh policy-owned generated surfaces for 8353fc05
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`8353fc05`** — Refresh external review snapshot for e9aad0df
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`e9aad0df`** — MP188-S1.1: expand bridge guard FORBIDDEN_MODULE_FRAGMENTS to commands/bridge_*
  - Adds 4 patterns to runtime bridge projection separation guard so future
  - commands/bridge_*.py modules cannot become an authority surface (per
  - ProjectionSurfaceAuthorityRule P191 + R130 TDD-Gap finding that the
  - evolution: The governed push dogfood run reached the release bundle but stopped before publication. `devctl push --execute` created the managed generated-surface receipt `b34748b32e5ee7c98eac34c38aa37a1659fc9d7f`, then blocked bec…
- **`1b42c70e`** — Refresh external review snapshot for df492548
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
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
- checkpoint_before_continue: dirty_after_local_checkpoint

### Stale warnings
- Relaunch the reviewer loop immediately.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-3a419271cc53` binds this file to HEAD `9ae64f257a1f`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
