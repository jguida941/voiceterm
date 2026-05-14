# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `2d494215923d` — MP377: add boot card role discovery
- Tree hash: `c9b676cb56e1`
- Generation stamp: `snap-b78e3aa6fd20`
- Generated at (UTC): 2026-05-14T06:37:09Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 45 files, +2326/-1039
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
- HEAD SHA: `2d494215923d292157fb25f373f9c316ac6ea75b`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-14T02:36:25-04:00

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
- publication_guidance: 33 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `2d494215923d`

- commits: 24
- files changed: 45
- insertions: +2326
- deletions: -1039
- bundle classes touched: docs, tooling

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `2d494215` | MP377: add boot card role discovery | 11 | +154/-18 | tooling |  |
| 2 | `e0ed1503` | Refresh external review snapshot for 7f5eef7e | 2 | +47/-47 | docs |  |
| 3 | `7f5eef7e` | Refresh bridge projection after progress packet | 1 | +3/-3 | docs |  |
| 4 | `7f43ac95` | Refresh external review snapshot for 252ca280 | 2 | +56/-58 | docs |  |
| 5 | `252ca280` | MP377: close automation opportunity packet slice | 3 | +4/-1 | tooling |  |
| 6 | `d799f7b0` | Refresh external review snapshot for ca3766c2 | 2 | +65/-61 | docs |  |
| 7 | `ca3766c2` | MP377: add automation opportunity packet kind | 8 | +163/-1 | tooling |  |
| 8 | `f5359bf3` | Refresh external review snapshot for 81f814f7 | 2 | +54/-60 | docs |  |
| 9 | `81f814f7` | MP377: close AutoInval producer wiring slice | 3 | +3/-1 | tooling |  |
| 10 | `76e9c859` | Refresh external review snapshot for 68d7def8 | 2 | +47/-47 | docs |  |
| 11 | `68d7def8` | MP377: avoid invalidation payload dict literal | 1 | +9/-10 | tooling |  |
| 12 | `aa63e907` | Refresh external review snapshot for 05d5d555 | 2 | +62/-62 | docs |  |
| 13 | `05d5d555` | MP377: type invalidation helper inputs | 7 | +174/-134 | tooling |  |
| 14 | `07afcf41` | Refresh external review snapshot for 56e25deb | 2 | +54/-55 | docs |  |
| 15 | `56e25deb` | MP377: refresh invalidation ground truth receipt | 1 | +2/-0 | tooling |  |
| 16 | `23755276` | Refresh external review snapshot for 5332adba | 2 | +59/-59 | docs |  |
| 17 | `5332adba` | MP377: remove invalidation facade wrappers | 7 | +70/-142 | tooling |  |
| 18 | `b03c5495` | Refresh external review snapshot for 24910ea9 | 2 | +68/-71 | docs |  |
| 19 | `24910ea9` | MP377: wire derived-state invalidation producers | 20 | +495/-32 | tooling |  |
| 20 | `8c3b1123` | Refresh external review snapshot for cc29a3ff | 2 | +57/-58 | docs |  |
| 21 | `cc29a3ff` | Mark AutoInval subscriber slice complete | 3 | +3/-1 | tooling |  |
| 22 | `544dafdb` | Refresh external review snapshot for 5e817ddd | 2 | +61/-59 | docs |  |
| 23 | `5e817ddd` | MP377: add remote evidence queue path freshness | 19 | +560/-3 | tooling |  |
| 24 | `7e828e51` | Refresh external review snapshot for 2d9a8e2c | 2 | +56/-56 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +15/-6 |
| `bridge.md` | docs | +36/-36 |
| `dev/active/MASTER_PLAN.md` | tooling | +27/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +54/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +653/-660 |
| `dev/config/devctl_repo_policy.json` | tooling | +12/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +39/-4 |
| `dev/guides/SYSTEM_MAP.md` | docs | +3/-3 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +89/-0 |
| `dev/scripts/README.md` | tooling | +41/-5 |
| `dev/scripts/checks/check_agents_contract.py` | tooling | +16/-0 |
| `dev/scripts/devctl/commands/development/plan_intake_receipts.py` | tooling | +49/-20 |
| `dev/scripts/devctl/commands/review_channel/event_post_wake_reports.py` | tooling | +35/-35 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +31/-2 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows.py` | tooling | +5/-0 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows_commit.py` | tooling | +5/-1 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_plan_intake.py` | tooling | +10/-0 |
| `dev/scripts/devctl/remote_evidence_queue/__init__.py` | tooling | +23/-0 |
| `dev/scripts/devctl/remote_evidence_queue/models.py` | tooling | +115/-0 |
| `dev/scripts/devctl/remote_evidence_queue/path_freshness.py` | tooling | +114/-0 |
| `dev/scripts/devctl/review_channel/packet_contract.py` | tooling | +3/-0 |
| `dev/scripts/devctl/review_channel/packet_debt_remediation.py` | tooling | +36/-13 |
| `dev/scripts/devctl/review_channel/packet_target_validation.py` | tooling | +1/-1 |
| `dev/scripts/devctl/review_channel/packet_transition_events.py` | tooling | +72/-30 |
| `dev/scripts/devctl/review_channel/session_liveness_events.py` | tooling | +31/-12 |
| `dev/scripts/devctl/runtime/action_contracts.py` | tooling | +2/-0 |
| `dev/scripts/devctl/runtime/commit_receipt.py` | tooling | +18/-0 |
| `dev/scripts/devctl/runtime/derived_state_invalidation.py` | tooling | +320/-181 |
| `dev/scripts/devctl/runtime/plan_intent_ingestion.py` | tooling | +3/-1 |
| `dev/scripts/devctl/tests/checks/test_check_agents_contract.py` | tooling | +18/-0 |
| `dev/scripts/devctl/tests/commands/test_development_command.py` | tooling | +9/-0 |
| `dev/scripts/devctl/tests/governance/test_render_surfaces.py` | tooling | +12/-0 |
| `dev/scripts/devctl/tests/remote_evidence_queue/test_path_freshness.py` | tooling | +190/-0 |
| `dev/scripts/devctl/tests/review_channel/test_ack_cli_e2e.py` | tooling | +4/-0 |
| `dev/scripts/devctl/tests/review_channel/test_event_post_action.py` | tooling | +23/-0 |
| `dev/scripts/devctl/tests/review_channel/test_event_post_wake.py` | tooling | +2/-0 |
| `dev/scripts/devctl/tests/review_channel/test_plan_packets.py` | tooling | +95/-0 |
| `dev/scripts/devctl/tests/review_channel/test_session_liveness_events.py` | tooling | +6/-0 |
| `dev/scripts/devctl/tests/runtime/test_action_contracts.py` | tooling | +2/-0 |
| `dev/scripts/devctl/tests/runtime/test_commit_receipt.py` | tooling | +3/-0 |
| _5 more files trimmed_ | | |

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

- **contract_mutation**: Contract / typed model mutated (`dev/scripts/checks/check_agents_contract.py`) — Commit 2d494215 changed dev/scripts/checks/check_agents_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_check_agents_contract.py`) — Commit 2d494215 changed dev/scripts/devctl/tests/checks/test_check_agents_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit ca3766c2 changed dev/scripts/devctl/review_channel/packet_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_identity_contract_rows.py`) — Commit 5e817ddd changed dev/scripts/devctl/platform/runtime_identity_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/action_contracts.py`) — Commit 5e817ddd changed dev/scripts/devctl/runtime/action_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_action_contracts.py`) — Commit 5e817ddd changed dev/scripts/devctl/tests/runtime/test_action_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`24910ea9`** — MP377: wire derived-state invalidation producers
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`8c3b1123`** — Refresh external review snapshot for cc29a3ff
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`cc29a3ff`** — Mark AutoInval subscriber slice complete
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`544dafdb`** — Refresh external review snapshot for 5e817ddd
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`5e817ddd`** — MP377: add remote evidence queue path freshness
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`7e828e51`** — Refresh external review snapshot for 2d9a8e2c
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-b78e3aa6fd20` binds this file to HEAD `2d494215923d`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
