# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `df5b66a9e657` — MP377: make reviewer mode role binding symmetric
- Tree hash: `0a2c0fbae1fe`
- Generation stamp: `snap-4efd924db56f`
- Generated at (UTC): 2026-05-14T01:47:45Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 73 files, +3593/-888
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
- HEAD SHA: `df5b66a9e657e9eb6320e3a0f4d5e6ff05ce35cb`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-13T21:47:14-04:00

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
- publication_backlog: queued
- publication_guidance: 1 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `df5b66a9e657`

- commits: 24
- files changed: 73
- insertions: +3593
- deletions: -888
- bundle classes touched: tooling, docs
- authority surfaces touched: 7 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `df5b66a9` | MP377: make reviewer mode role binding symmetric | 11 | +269/-23 | tooling |  |
| 2 | `00b3fb70` | Refresh external review snapshot for eb040912 | 2 | +67/-67 | docs |  |
| 3 | `eb040912` | Record rev_pkt_3983 plan binding | 2 | +2/-0 | tooling |  |
| 4 | `5b36477a` | Refresh external review snapshot for 524dc68b | 2 | +51/-51 | docs |  |
| 5 | `524dc68b` | MP377: add agent supervise execute bridge | 13 | +365/-5 | tooling |  |
| 6 | `4af60318` | Refresh external review snapshot for e5640356 | 2 | +60/-61 | docs |  |
| 7 | `e5640356` | MP377: add bilateral protocol contract | 16 | +668/-7 | tooling |  |
| 8 | `ee14ad16` | Refresh external review snapshot for 2d9b07bf | 2 | +54/-55 | docs |  |
| 9 | `2d9b07bf` | MP377: close adopter pilot gate proof | 8 | +67/-11 | tooling |  |
| 10 | `cbb63aed` | Refresh external review snapshot for 98b40dcc | 2 | +59/-56 | docs |  |
| 11 | `98b40dcc` | P102: surface typed gate failures | 21 | +433/-21 | tooling |  |
| 12 | `14b4c55b` | Refresh external review snapshot for 915ca48d | 2 | +58/-57 | docs |  |
| 13 | `915ca48d` | P102: fix lifecycle state resolvers | 13 | +214/-35 | tooling |  |
| 14 | `fa1b6698` | Refresh external review snapshot for f5c7778f | 2 | +54/-54 | docs |  |
| 15 | `f5c7778f` | Record rev_pkt_3970 and rev_pkt_3971 plan bindings | 2 | +4/-0 | tooling |  |
| 16 | `b6b50dbe` | Refresh external review snapshot for b05a8973 | 2 | +51/-51 | docs |  |
| 17 | `b05a8973` | P102: enforce governed transition states | 11 | +290/-2 | tooling |  |
| 18 | `d44a2588` | Refresh external review snapshot for 2db48c12 | 2 | +51/-56 | docs |  |
| 19 | `2db48c12` | Record rev_pkt_3968 plan binding | 2 | +2/-0 | tooling |  |
| 20 | `1e0ceffd` | Refresh external review snapshot for 94d2df5d | 2 | +68/-62 | docs |  |
| 21 | `94d2df5d` | Add delivery modes to governance runtime | 23 | +499/-78 | tooling |  |
| 22 | `66919658` | Refresh external review snapshot for 1cc7d657 | 2 | +59/-56 | docs |  |
| 23 | `1cc7d657` | Fix stale pending packet blocker normalization | 8 | +84/-19 | tooling |  |
| 24 | `0b7707c9` | Refresh external review snapshot for 35b5131c | 2 | +64/-61 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +41/-41 |
| `codesmells.md` | docs | +29/-0 |
| `dev/active/MASTER_PLAN.md` | tooling | +63/-5 |
| `dev/active/ai_governance_platform.md` | tooling | +104/-5 |
| `dev/active/portable_code_governance.md` | tooling | +23/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +655/-646 |
| `dev/guides/DEVELOPMENT.md` | docs | +44/-1 |
| `dev/guides/SYSTEM_MAP.md` | docs | +8/-8 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +144/-1 |
| `dev/scripts/README.md` | tooling | +41/-3 |
| `dev/scripts/checks/review_probes/probe_event_field_naming_consistency.py` | tooling | +2/-4 |
| `dev/scripts/devctl/commands/development/final_response_gate.py` | tooling | +47/-1 |
| `dev/scripts/devctl/commands/development/final_response_gate_agent_loop.py` | tooling | +5/-1 |
| `dev/scripts/devctl/commands/development/orchestration_agent_loop_parse.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/development/orchestration_models.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/development/render.py` | tooling | +20/-1 |
| `dev/scripts/devctl/commands/governance/startup_context_advisory_coherence.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/governance/startup_context_render.py` | tooling | +17/-6 |
| `dev/scripts/devctl/commands/governance/startup_context_summary.py` | tooling | +35/-0 |
| `dev/scripts/devctl/commands/runtime/agent_supervise.py` | tooling | +35/-1 |
| `dev/scripts/devctl/governance/draft_policy_scan.py` | tooling | +2/-0 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows.py` | tooling | +113/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_bypass_lifecycle.py` | tooling | +2/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_governed_exception_core.py` | tooling | +41/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_transitions.py` | tooling | +5/-0 |
| `dev/scripts/devctl/platform/surface_state_contract_rows.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/event_projection_bridge_state.py` | tooling | +7/-13 |
| `dev/scripts/devctl/review_channel/status_projection_bridge_state.py` | tooling | +4/-0 |
| `dev/scripts/devctl/runtime/agent_loop_bilateral_protocol.py` | tooling | +275/-0 |
| `dev/scripts/devctl/runtime/agent_loop_decision_builder.py` | tooling | +58/-0 |
| `dev/scripts/devctl/runtime/agent_loop_decision_models.py` | tooling | +3/-0 |
| `dev/scripts/devctl/runtime/agent_supervise_driver.py` | tooling | +94/-1 |
| `dev/scripts/devctl/runtime/auto_mode.py` | tooling | +52/-14 |
| `dev/scripts/devctl/runtime/bypass_lifecycle_evaluation.py` | tooling | +44/-4 |
| `dev/scripts/devctl/runtime/bypass_lifecycle_models.py` | tooling | +61/-18 |
| `dev/scripts/devctl/runtime/governed_transitions.py` | tooling | +91/-7 |
| `dev/scripts/devctl/runtime/operator_context.py` | tooling | +17/-13 |
| `dev/scripts/devctl/runtime/project_governance.py` | tooling | +12/-0 |
| `dev/scripts/devctl/runtime/project_governance_contract.py` | tooling | +68/-1 |
| `dev/scripts/devctl/runtime/project_governance_parse.py` | tooling | +15/-6 |
| _33 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 42
- open: 42
- fixed: 0
- false positives: 0

Recent findings:
- `agent_sync.ambiguity_projection` — `dev/scripts/checks/multi_agent_sync` (high, verdict=`confirmed_issue`)
- `review_channel.command_latency_under_fanout` — `dev/scripts/devctl/commands/review_channel` (high, verdict=`confirmed_issue`)
- `work_board.rows_duplication` — `dev/scripts/devctl/runtime/agent_dispatch_router.py` (high, verdict=`confirmed_issue`)
- `dogfood.command.pipeline` — `dev/scripts/devctl/commands/pipeline/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-audit` — `dev/scripts/devctl/commands/process/audit.py` (n/a, verdict=`confirmed_issue`)
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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_parse.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_project_governance.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_identity_contract_rows.py`) — Commit e5640356 changed dev/scripts/devctl/platform/runtime_identity_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit e5640356 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/development/orchestration_models.py`) — Commit 98b40dcc changed dev/scripts/devctl/commands/development/orchestration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/agent_loop_decision_models.py`) — Commit 98b40dcc changed dev/scripts/devctl/runtime/agent_loop_decision_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/bypass_lifecycle_models.py`) — Commit 915ca48d changed dev/scripts/devctl/runtime/bypass_lifecycle_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit 94d2df5d changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Commit 94d2df5d changed dev/scripts/devctl/runtime/project_governance_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`f5c7778f`** — Record rev_pkt_3970 and rev_pkt_3971 plan bindings
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`b6b50dbe`** — Refresh external review snapshot for b05a8973
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`b05a8973`** — P102: enforce governed transition states
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`d44a2588`** — Refresh external review snapshot for 2db48c12
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`2db48c12`** — Record rev_pkt_3968 plan binding
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`1e0ceffd`** — Refresh external review snapshot for 94d2df5d
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`94d2df5d`** — Add delivery modes to governance runtime
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`66919658`** — Refresh external review snapshot for 1cc7d657
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`1cc7d657`** — Fix stale pending packet blocker normalization
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`0b7707c9`** — Refresh external review snapshot for 35b5131c
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
- **governance_open** (`dev/scripts/checks/multi_agent_sync`): agent_sync.ambiguity_projection: source_packet_ids=rev_pkt_2697,rev_pkt_2705; canonical_active_packet_ambiguity can render empty while ambiguity exists, and expired-but-pending split state creates carry-forward debt. Durable owner: MP377-GUARDIR-AGENT-SYNC-AMBIGUITY-CARRYFORWARD.
- **governance_open** (`dev/scripts/devctl/commands/review_channel`): review_channel.command_latency_under_fanout: source_packet_ids=rev_pkt_2704,rev_pkt_2705; review-channel post and startup-context can hang under multi-agent load, tied to process-cleanup and detached sleep pressure. Durable owner: MP377-GUARDIR-FANOUT-COMMAND-HANGS.
- **governance_open** (`dev/scripts/devctl/runtime/agent_dispatch_router.py`): work_board.rows_duplication: source_packet_ids=rev_pkt_2700,rev_pkt_2705; _work_board_rows logic is duplicated between packet_route_resolution.py and agent_dispatch_router.py. Durable owner: MP377-GUARDIR-WORK-BOARD-ROUTE-DEDUP.
- **governance_open** (`dev/scripts/devctl/commands/pipeline/command.py`): dogfood.command.pipeline: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/process/audit.py`): dogfood.command.process-audit: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/vcs/push.py`): dogfood.command.push: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/reports_cleanup.py`): dogfood.command.reports-cleanup: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/python_tests.py`): dogfood.command.test-python: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-4efd924db56f` binds this file to HEAD `df5b66a9e657`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
