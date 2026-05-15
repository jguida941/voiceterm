# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `644389cd4193` — Refresh external review snapshot for 9272e871
- Tree hash: `a78acdabcfce`
- Generation stamp: `snap-654e3ef9d451`
- Generated at (UTC): 2026-05-15T01:53:29Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 541 files, +13726/-1075
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
- HEAD SHA: `644389cd41937b01b55452364e051de53f71850d`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-14T20:21:15-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 16
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report_state: `post_push_green` (push_completed)
- publication_backlog: none

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
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `644389cd4193`

- commits: 24
- files changed: 541
- insertions: +13726
- deletions: -1075
- bundle classes touched: docs, tooling
- authority surfaces touched: 5 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `644389cd` | Refresh external review snapshot for 9272e871 | 2 | +63/-63 | docs |  |
| 2 | `9272e871` | MP381: stabilize push authorization during preflight | 12 | +270/-124 | tooling |  |
| 3 | `b049ba3a` | Refresh external review snapshot for 868e35c9 | 2 | +72/-77 | docs |  |
| 4 | `868e35c9` | MP381: read canonical push authorization | 14 | +223/-64 | tooling |  |
| 5 | `aee417b6` | Refresh external review snapshot for 866ce516 | 2 | +61/-65 | docs |  |
| 6 | `866ce516` | MP381: fix review-channel self-stop preflight | 12 | +177/-61 | tooling |  |
| 7 | `ff501228` | Refresh external review snapshot for d3b7a100 | 2 | +72/-68 | docs |  |
| 8 | `d3b7a100` | MP381: ingest R98 governance findings | 490 | +10105/-155 | tooling |  |
| 9 | `92488df1` | MP377: checkpoint packet-pressure bridge refresh | 1 | +1/-1 | docs |  |
| 10 | `ec6f330e` | MP378: summarize locked review events | 4 | +244/-53 | tooling |  |
| 11 | `e991f288` | MP377: checkpoint packet-pressure reductions | 3 | +3/-1 | tooling |  |
| 12 | `744a4aa9` | MP378: stream review-channel event reads | 5 | +93/-43 | tooling |  |
| 13 | `5fed0004` | MP377: checkpoint reviewer-mode packet reduction | 3 | +4/-2 | tooling |  |
| 14 | `8bd100f9` | MP377: checkpoint packet queue reductions | 3 | +9/-6 | tooling |  |
| 15 | `22cfecd2` | MP377: checkpoint repair field and portability guard | 38 | +1154/-51 | tooling |  |
| 16 | `d0b53c26` | MP378: close packet binding guard plan row | 4 | +5/-0 | tooling |  |
| 17 | `94db6e01` | Refresh external review snapshot for 03379dd7 | 2 | +68/-65 | docs |  |
| 18 | `03379dd7` | MP378: guard task packet binding completeness | 21 | +863/-5 | tooling |  |
| 19 | `7bafd1e7` | Refresh external review snapshot for 7f29e975 | 2 | +63/-65 | docs |  |
| 20 | `7f29e975` | MP378: record human-summary packet binding | 2 | +2/-0 | tooling |  |
| 21 | `58ad460a` | Refresh external review snapshot for 6aaaacf7 | 2 | +45/-45 | docs |  |
| 22 | `6aaaacf7` | MP378: close raw-git hook receipt plan row | 3 | +3/-0 | tooling |  |
| 23 | `c891ec57` | Refresh external review snapshot for 209c52fe | 2 | +59/-59 | docs |  |
| 24 | `209c52fe` | MP378: fix raw git hook receipt target | 2 | +67/-2 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +2/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +6/-0 |
| `bridge.md` | docs | +52/-52 |
| `dev/active/MASTER_PLAN.md` | tooling | +55/-2 |
| `dev/active/ai_governance_platform.md` | tooling | +57/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +758/-753 |
| `dev/audits/r98_packet_4030_4038_plan_capture.md` | tooling | +75/-0 |
| `dev/audits/r98_push_authorization_projection_path.md` | tooling | +31/-0 |
| `dev/audits/r98_push_preflight_review_channel_timeout.md` | tooling | +23/-0 |
| `dev/config/devctl_repo_policy.json` | tooling | +34/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +39/-1 |
| `dev/guides/SYSTEM_MAP.md` | docs | +41/-38 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +145/-0 |
| `dev/scripts/README.md` | tooling | +27/-3 |
| `dev/scripts/checks/check_packet_pkt_bind_completeness.py` | tooling | +19/-0 |
| `dev/scripts/checks/check_plan_index_commit_continuity.py` | tooling | +29/-17 |
| `dev/scripts/checks/check_substrate_is_repo_portable.py` | tooling | +10/-0 |
| `dev/scripts/checks/packet_pkt_bind_completeness/__init__.py` | tooling | +6/-0 |
| `dev/scripts/checks/packet_pkt_bind_completeness/command.py` | tooling | +52/-1 |
| `dev/scripts/checks/packet_pkt_bind_completeness/constants.py` | tooling | +29/-2 |
| `dev/scripts/checks/packet_pkt_bind_completeness/core.py` | tooling | +217/-12 |
| `dev/scripts/checks/packet_pkt_bind_completeness/models.py` | tooling | +34/-0 |
| `dev/scripts/checks/packet_pkt_bind_completeness/readers.py` | tooling | +134/-0 |
| `dev/scripts/checks/packet_pkt_bind_completeness/render.py` | tooling | +65/-0 |
| `dev/scripts/checks/packet_pkt_bind_completeness/time_support.py` | tooling | +39/-0 |
| `dev/scripts/checks/repo_portability/__init__.py` | tooling | +5/-0 |
| `dev/scripts/checks/repo_portability/command.py` | tooling | +376/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/raw_git.py` | tooling | +25/-2 |
| `dev/scripts/devctl/commands/review_channel/_stop.py` | tooling | +14/-0 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +9/-10 |
| `dev/scripts/devctl/commands/vcs/governed_executor.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +17/-66 |
| `dev/scripts/devctl/commands/vcs/push_publication_gate.py` | tooling | +115/-0 |
| `dev/scripts/devctl/governance/push_state_authorization.py` | tooling | +3/-8 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +2/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows.py` | tooling | +4/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_governance_proposed.py` | tooling | +335/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_pipeline.py` | tooling | +5/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_review_core.py` | tooling | +45/-0 |
| _501 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/remote_commit_pipeline_artifact.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit d3b7a100 changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/governance_proposed_contracts.py`) — Commit d3b7a100 changed dev/scripts/devctl/runtime/governance_proposed_contracts.py
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
- **`d0b53c26`** — MP378: close packet binding guard plan row
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`94db6e01`** — Refresh external review snapshot for 03379dd7
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`03379dd7`** — MP378: guard task packet binding completeness
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`7bafd1e7`** — Refresh external review snapshot for 7f29e975
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`7f29e975`** — MP378: record human-summary packet binding
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`58ad460a`** — Refresh external review snapshot for 6aaaacf7
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`6aaaacf7`** — MP378: close raw-git hook receipt plan row
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`c891ec57`** — Refresh external review snapshot for 209c52fe
  - evolution: The R98 reviewer-loop handoff exposed nine live review packets (`rev_pkt_4030` through `rev_pkt_4038`) that were still PKT-BIND-only intake. The closure published the pending 80-commit wall first, read the packet bodies…
- **`209c52fe`** — MP378: fix raw git hook receipt target
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
- checkpoint_before_continue: staged_index_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-654e3ef9d451` binds this file to HEAD `644389cd4193`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
