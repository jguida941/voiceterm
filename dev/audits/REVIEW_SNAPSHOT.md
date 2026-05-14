# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `5e817ddddf46` — MP377: add remote evidence queue path freshness
- Tree hash: `3d7a7ad5f6d8`
- Generation stamp: `snap-0413bbb95f49`
- Generated at (UTC): 2026-05-14T02:53:43Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 69 files, +3481/-806
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
- HEAD SHA: `5e817ddddf46052e010390418792b701771dfb44`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-13T22:53:06-04:00

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
- publication_guidance: 11 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `5e817ddddf46`

- commits: 24
- files changed: 69
- insertions: +3481
- deletions: -806
- bundle classes touched: tooling, docs
- authority surfaces touched: 2 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `5e817ddd` | MP377: add remote evidence queue path freshness | 19 | +560/-3 | tooling |  |
| 2 | `7e828e51` | Refresh external review snapshot for 2d9a8e2c | 2 | +56/-56 | docs |  |
| 3 | `2d9a8e2c` | Record rev_pkt_3996 plan binding | 2 | +2/-0 | tooling |  |
| 4 | `9ae876bd` | Refresh external review snapshot for 96cf64af | 2 | +48/-47 | docs |  |
| 5 | `96cf64af` | Record rev_pkt_3992 plan binding | 2 | +2/-0 | tooling |  |
| 6 | `1165d1fa` | Refresh external review snapshot for d64ce27f | 2 | +63/-70 | docs |  |
| 7 | `d64ce27f` | MP377: record packet arrival derived-state invalidation | 11 | +192/-6 | tooling |  |
| 8 | `c94d3155` | Refresh external review snapshot for 8568a49a | 2 | +54/-54 | docs |  |
| 9 | `8568a49a` | Record MP377 reviewer-mode slice closure | 5 | +19/-1 | tooling |  |
| 10 | `8636cd93` | Refresh external review snapshot for df5b66a9 | 2 | +64/-66 | docs |  |
| 11 | `df5b66a9` | MP377: make reviewer mode role binding symmetric | 11 | +269/-23 | tooling |  |
| 12 | `00b3fb70` | Refresh external review snapshot for eb040912 | 2 | +67/-67 | docs |  |
| 13 | `eb040912` | Record rev_pkt_3983 plan binding | 2 | +2/-0 | tooling |  |
| 14 | `5b36477a` | Refresh external review snapshot for 524dc68b | 2 | +51/-51 | docs |  |
| 15 | `524dc68b` | MP377: add agent supervise execute bridge | 13 | +365/-5 | tooling |  |
| 16 | `4af60318` | Refresh external review snapshot for e5640356 | 2 | +60/-61 | docs |  |
| 17 | `e5640356` | MP377: add bilateral protocol contract | 16 | +668/-7 | tooling |  |
| 18 | `ee14ad16` | Refresh external review snapshot for 2d9b07bf | 2 | +54/-55 | docs |  |
| 19 | `2d9b07bf` | MP377: close adopter pilot gate proof | 8 | +67/-11 | tooling |  |
| 20 | `cbb63aed` | Refresh external review snapshot for 98b40dcc | 2 | +59/-56 | docs |  |
| 21 | `98b40dcc` | P102: surface typed gate failures | 21 | +433/-21 | tooling |  |
| 22 | `14b4c55b` | Refresh external review snapshot for 915ca48d | 2 | +58/-57 | docs |  |
| 23 | `915ca48d` | P102: fix lifecycle state resolvers | 13 | +214/-35 | tooling |  |
| 24 | `fa1b6698` | Refresh external review snapshot for f5c7778f | 2 | +54/-54 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +44/-44 |
| `codesmells.md` | docs | +29/-0 |
| `dev/active/MASTER_PLAN.md` | tooling | +57/-5 |
| `dev/active/ai_governance_platform.md` | tooling | +80/-4 |
| `dev/active/portable_code_governance.md` | tooling | +23/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +644/-650 |
| `dev/guides/DEVELOPMENT.md` | docs | +47/-1 |
| `dev/guides/SYSTEM_MAP.md` | docs | +10/-10 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +144/-1 |
| `dev/scripts/README.md` | tooling | +43/-3 |
| `dev/scripts/checks/review_probes/probe_event_field_naming_consistency.py` | tooling | +2/-4 |
| `dev/scripts/devctl/commands/development/final_response_gate.py` | tooling | +47/-1 |
| `dev/scripts/devctl/commands/development/final_response_gate_agent_loop.py` | tooling | +5/-1 |
| `dev/scripts/devctl/commands/development/orchestration_agent_loop_parse.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/development/orchestration_models.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/development/render.py` | tooling | +20/-1 |
| `dev/scripts/devctl/commands/governance/startup_context_render.py` | tooling | +17/-6 |
| `dev/scripts/devctl/commands/governance/startup_context_summary.py` | tooling | +35/-0 |
| `dev/scripts/devctl/commands/review_channel/event_post_wake.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/event_post_wake_reports.py` | tooling | +62/-0 |
| `dev/scripts/devctl/commands/runtime/agent_supervise.py` | tooling | +35/-1 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows.py` | tooling | +118/-0 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows_commit.py` | tooling | +5/-1 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_bypass_lifecycle.py` | tooling | +2/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_governed_exception_core.py` | tooling | +41/-0 |
| `dev/scripts/devctl/remote_evidence_queue/__init__.py` | tooling | +23/-0 |
| `dev/scripts/devctl/remote_evidence_queue/models.py` | tooling | +115/-0 |
| `dev/scripts/devctl/remote_evidence_queue/path_freshness.py` | tooling | +114/-0 |
| `dev/scripts/devctl/review_channel/event_projection_bridge_state.py` | tooling | +7/-13 |
| `dev/scripts/devctl/review_channel/event_render.py` | tooling | +32/-0 |
| `dev/scripts/devctl/review_channel/status_projection_bridge_state.py` | tooling | +4/-0 |
| `dev/scripts/devctl/runtime/action_contracts.py` | tooling | +2/-0 |
| `dev/scripts/devctl/runtime/agent_loop_bilateral_protocol.py` | tooling | +275/-0 |
| `dev/scripts/devctl/runtime/agent_loop_decision_builder.py` | tooling | +58/-0 |
| `dev/scripts/devctl/runtime/agent_loop_decision_models.py` | tooling | +3/-0 |
| `dev/scripts/devctl/runtime/agent_supervise_driver.py` | tooling | +94/-1 |
| `dev/scripts/devctl/runtime/bypass_lifecycle_evaluation.py` | tooling | +5/-4 |
| `dev/scripts/devctl/runtime/bypass_lifecycle_models.py` | tooling | +61/-18 |
| `dev/scripts/devctl/runtime/commit_receipt.py` | tooling | +18/-0 |
| `dev/scripts/devctl/runtime/governed_transitions.py` | tooling | +11/-5 |
| _29 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 42
- open: 42
- fixed: 0
- false positives: 0

Recent findings:
- `review_channel.command_latency_under_fanout` — `dev/scripts/devctl/commands/review_channel` (high, verdict=`confirmed_issue`)
- `work_board.rows_duplication` — `dev/scripts/devctl/runtime/agent_dispatch_router.py` (high, verdict=`confirmed_issue`)
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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_gate.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_identity_contract_rows.py`) — Commit 5e817ddd changed dev/scripts/devctl/platform/runtime_identity_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/action_contracts.py`) — Commit 5e817ddd changed dev/scripts/devctl/runtime/action_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_action_contracts.py`) — Commit 5e817ddd changed dev/scripts/devctl/tests/runtime/test_action_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit e5640356 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/development/orchestration_models.py`) — Commit 98b40dcc changed dev/scripts/devctl/commands/development/orchestration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/agent_loop_decision_models.py`) — Commit 98b40dcc changed dev/scripts/devctl/runtime/agent_loop_decision_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/bypass_lifecycle_models.py`) — Commit 915ca48d changed dev/scripts/devctl/runtime/bypass_lifecycle_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`5e817ddd`** — MP377: add remote evidence queue path freshness
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`7e828e51`** — Refresh external review snapshot for 2d9a8e2c
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`2d9a8e2c`** — Record rev_pkt_3996 plan binding
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`9ae876bd`** — Refresh external review snapshot for 96cf64af
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`96cf64af`** — Record rev_pkt_3992 plan binding
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`1165d1fa`** — Refresh external review snapshot for d64ce27f
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`d64ce27f`** — MP377: record packet arrival derived-state invalidation
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`c94d3155`** — Refresh external review snapshot for 8568a49a
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`8568a49a`** — Record MP377 reviewer-mode slice closure
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`8636cd93`** — Refresh external review snapshot for df5b66a9
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`df5b66a9`** — MP377: make reviewer mode role binding symmetric
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`00b3fb70`** — Refresh external review snapshot for eb040912
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`eb040912`** — Record rev_pkt_3983 plan binding
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`5b36477a`** — Refresh external review snapshot for 524dc68b
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`524dc68b`** — MP377: add agent supervise execute bridge
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`4af60318`** — Refresh external review snapshot for e5640356
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`e5640356`** — MP377: add bilateral protocol contract
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`ee14ad16`** — Refresh external review snapshot for 2d9b07bf
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`2d9b07bf`** — MP377: close adopter pilot gate proof
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`cbb63aed`** — Refresh external review snapshot for 98b40dcc
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`98b40dcc`** — P102: surface typed gate failures
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`14b4c55b`** — Refresh external review snapshot for 915ca48d
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`915ca48d`** — P102: fix lifecycle state resolvers
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`fa1b6698`** — Refresh external review snapshot for f5c7778f
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
- **governance_open** (`dev/scripts/devctl/commands/review_channel`): review_channel.command_latency_under_fanout: source_packet_ids=rev_pkt_2704,rev_pkt_2705; review-channel post and startup-context can hang under multi-agent load, tied to process-cleanup and detached sleep pressure. Durable owner: MP377-GUARDIR-FANOUT-COMMAND-HANGS.
- **governance_open** (`dev/scripts/devctl/runtime/agent_dispatch_router.py`): work_board.rows_duplication: source_packet_ids=rev_pkt_2700,rev_pkt_2705; _work_board_rows logic is duplicated between packet_route_resolution.py and agent_dispatch_router.py. Durable owner: MP377-GUARDIR-WORK-BOARD-ROUTE-DEDUP.
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-0413bbb95f49` binds this file to HEAD `5e817ddddf46`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
