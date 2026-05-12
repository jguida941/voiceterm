# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `42683c3f7457` — Refresh external review snapshot for c8cf1c84
- Tree hash: `57f5b1fad1f6`
- Generation stamp: `snap-f1b07a6838d3`
- Generated at (UTC): 2026-05-12T20:38:17Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 240 files, +21013/-1838
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
- HEAD SHA: `42683c3f74576b09b7d4b6d9286fc0c861ff62f8`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-12T15:30:28-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 9
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: urgent
- publication_guidance: 7 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_before_continue` — dirty_after_local_checkpoint

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `42683c3f7457`

- commits: 24
- files changed: 240
- insertions: +21013
- deletions: -1838
- bundle classes touched: docs, tooling
- authority surfaces touched: 14 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `42683c3f` | Refresh external review snapshot for c8cf1c84 | 2 | +49/-48 | docs |  |
| 2 | `c8cf1c84` | Post-commit working tree cleanup: bridge heartbeat + codesm… | 4 | +39/-3 | docs |  |
| 3 | `e76ed6f3` | Refresh external review snapshot for eb336244 | 2 | +82/-76 | docs |  |
| 4 | `eb336244` | Land MP377 BypassLifecycle composability + charter addition… | 48 | +2199/-407 | tooling |  |
| 5 | `b331baa1` | Refresh external review snapshot for 0352553b | 2 | +85/-78 | docs |  |
| 6 | `0352553b` | Checkpoint MP377-P0-CHECKPOINT-AUTOMATION-S1 slice work (cl… | 60 | +3582/-139 | tooling |  |
| 7 | `0928a483` | Stage agent_supervise import set + adapter wiring (recover… | 8 | +808/-2 | tooling |  |
| 8 | `28bcafdd` | Refresh policy-owned generated surfaces for 87554eb9 | 1 | +16/-16 | docs |  |
| 9 | `87554eb9` | Refresh external review snapshot for 9249e17c | 2 | +138/-85 | docs |  |
| 10 | `9249e17c` | Land MP-377 typed governance work-in-progress (multi-slice) | 176 | +12985/-235 | tooling |  |
| 11 | `771a7fa5` | Refresh external review snapshot for 73417c6a | 2 | +71/-72 | docs |  |
| 12 | `73417c6a` | Stop push preflight projection receipt loops | 5 | +138/-53 | tooling |  |
| 13 | `fd9ed509` | Refresh external review snapshot for c9616cfe | 2 | +55/-55 | docs |  |
| 14 | `c9616cfe` | Fix push bridge sync test mocks | 4 | +51/-56 | tooling |  |
| 15 | `170167c1` | Refresh external review snapshot for fe5b9538 | 2 | +66/-65 | docs |  |
| 16 | `fe5b9538` | Fix startup reviewer mode authority | 5 | +95/-60 | tooling |  |
| 17 | `18685099` | Refresh external review snapshot for c4e50e10 | 2 | +40/-40 | docs |  |
| 18 | `c4e50e10` | Refresh external review snapshot for 1036a84b | 2 | +64/-64 | docs |  |
| 19 | `1036a84b` | Document push preflight projection policy | 9 | +94/-55 | tooling |  |
| 20 | `8b8900d6` | Refresh external review snapshot for 0fa60654 | 2 | +64/-62 | docs |  |
| 21 | `0fa60654` | Fix push preflight audit routing | 8 | +185/-59 | tooling |  |
| 22 | `5b5c0d06` | Refresh external review snapshot for 9aba52e2 | 1 | +40/-40 | tooling |  |
| 23 | `9aba52e2` | Refresh policy-owned generated surfaces for 905794d7 | 1 | +1/-1 | docs |  |
| 24 | `905794d7` | Refresh external review snapshot for 5068dcf7 | 2 | +66/-67 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.claude/commands/develop.md` | docs | +3/-1 |
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `AGENTS.md` | docs | +10/-1 |
| `bridge.md` | docs | +97/-97 |
| `codesmells.md` | docs | +902/-0 |
| `dev/active/MASTER_PLAN.md` | tooling | +137/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +40/-2 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1081/-1018 |
| `dev/guides/DEVELOPMENT.md` | docs | +41/-7 |
| `dev/guides/SYSTEM_MAP.md` | docs | +23/-23 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +147/-0 |
| `dev/scripts/README.md` | tooling | +36/-4 |
| `dev/scripts/checks/check_checkpoint_budget_shape.py` | tooling | +11/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth.py` | tooling | +98/-1 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop.py` | tooling | +20/-3 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_instruction.py` | tooling | +155/-0 |
| `dev/scripts/checks/startup_authority_contract/checkpoint_budget_shape_command.py` | tooling | +79/-0 |
| `dev/scripts/checks/startup_authority_contract/command.py` | tooling | +24/-2 |
| `dev/scripts/checks/startup_authority_contract/runtime_checks.py` | tooling | +318/-9 |
| `dev/scripts/devctl/approval_mode.py` | tooling | +30/-1 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/cli.py` | tooling | +14/-1 |
| `dev/scripts/devctl/cli_parser/agent_supervise.py` | tooling | +12/-0 |
| `dev/scripts/devctl/cli_parser/artifact_suppression.py` | tooling | +0/-1 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +5/-0 |
| `dev/scripts/devctl/commands/demo.py` | tooling | +43/-2 |
| `dev/scripts/devctl/commands/development/command.py` | tooling | +12/-0 |
| `dev/scripts/devctl/commands/development/continuation.py` | tooling | +107/-5 |
| `dev/scripts/devctl/commands/development/final_response_gate.py` | tooling | +283/-13 |
| `dev/scripts/devctl/commands/development/models.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/development/next_slice_blockers.py` | tooling | +19/-0 |
| `dev/scripts/devctl/commands/development/orchestration_agent_loop.py` | tooling | +21/-1 |
| `dev/scripts/devctl/commands/development/orchestration_agent_loop_parse.py` | tooling | +34/-0 |
| `dev/scripts/devctl/commands/development/orchestration_agent_loop_rows.py` | tooling | +40/-1 |
| `dev/scripts/devctl/commands/development/orchestration_agent_supervise.py` | tooling | +118/-0 |
| `dev/scripts/devctl/commands/development/orchestration_inputs.py` | tooling | +23/-1 |
| `dev/scripts/devctl/commands/development/orchestration_models.py` | tooling | +17/-0 |
| `dev/scripts/devctl/commands/development/packet_attention.py` | tooling | +18/-4 |
| `dev/scripts/devctl/commands/development/packet_attention_commands.py` | tooling | +10/-4 |
| _200 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 43
- open: 43
- fixed: 0
- false positives: 0

Recent findings:
- `dogfood.command.integrations-import` — `dev/scripts/devctl/commands/integrations_import.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.governance-export` — `dev/scripts/devctl/commands/governance/export.py` (n/a, verdict=`confirmed_issue`)
- `packet.transition_session_disambiguation` — `dev/scripts/devctl/review_channel/instruction_transitions.py` (critical, verdict=`confirmed_issue`)
- `packet.durable_ingestion_before_ttl` — `dev/scripts/devctl/runtime/packet_carry_forward.py` (critical, verdict=`confirmed_issue`)
- `agent_sync.ambiguity_projection` — `dev/scripts/checks/multi_agent_sync` (high, verdict=`confirmed_issue`)
- `review_channel.command_latency_under_fanout` — `dev/scripts/devctl/commands/review_channel` (high, verdict=`confirmed_issue`)
- `work_board.rows_duplication` — `dev/scripts/devctl/runtime/agent_dispatch_router.py` (high, verdict=`confirmed_issue`)
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_tests.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_test_runner/command.py` (n/a, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_handler.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_launch_control.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/checkpoint_budget_shape_command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_checks.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_parser.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/bypass_lifecycle_models.py`) — Commit eb336244 changed dev/scripts/devctl/runtime/bypass_lifecycle_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/startup_context_models.py`) — Commit eb336244 changed dev/scripts/devctl/runtime/startup_context_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit eb336244 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/development/orchestration_models.py`) — Commit 0352553b changed dev/scripts/devctl/commands/development/orchestration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_identity_contract_rows.py`) — Commit 9249e17c changed dev/scripts/devctl/platform/runtime_identity_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit 9249e17c changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit 9249e17c changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit 9249e17c changed dev/scripts/devctl/review_channel/packet_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/action_contracts.py`) — Commit 9249e17c changed dev/scripts/devctl/runtime/action_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/check_result_models.py`) — Commit 9249e17c changed dev/scripts/devctl/runtime/check_result_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/finding_contracts.py`) — Commit 9249e17c changed dev/scripts/devctl/runtime/finding_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/finding_payload_contracts.py`) — Commit 9249e17c changed dev/scripts/devctl/runtime/finding_payload_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/guard_finding_contracts.py`) — Commit 9249e17c changed dev/scripts/devctl/runtime/guard_finding_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_packet_models.py`) — Commit 9249e17c changed dev/scripts/devctl/runtime/review_state_packet_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit 9249e17c changed dev/scripts/devctl/runtime/reviewer_runtime_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/validation_contracts.py`) — Commit 9249e17c changed dev/scripts/devctl/runtime/validation_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Commit 9249e17c changed dev/scripts/devctl/tests/checks/test_startup_authority_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_action_contracts.py`) — Commit 9249e17c changed dev/scripts/devctl/tests/runtime/test_action_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_finding_contracts.py`) — Commit 9249e17c changed dev/scripts/devctl/tests/runtime/test_finding_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_governed_exception_contracts.py`) — Commit 9249e17c changed dev/scripts/devctl/tests/runtime/test_governed_exception_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`42683c3f`** — Refresh external review snapshot for c8cf1c84
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`c8cf1c84`** — Post-commit working tree cleanup: bridge heartbeat + codesmells.md cycle 8 + MASTER_PLAN/plan_index auto-gen refresh
  - Cleans working tree before codex re-launch per operator directive 19:32Z.
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`e76ed6f3`** — Refresh external review snapshot for eb336244
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`eb336244`** — Land MP377 BypassLifecycle composability + charter additions P88-P93 (claude-mutation-lane handoff)
  - Codex landed full BypassLifecycle typed runtime in claude's mutation lane per codex
  - gate diagnostic 2026-05-12T18:52Z: "Claude's lane has stage/commit capabilities;
  - current loop pinned to rev_pkt_3736."
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`b331baa1`** — Refresh external review snapshot for 0352553b
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`0352553b`** — Checkpoint MP377-P0-CHECKPOINT-AUTOMATION-S1 slice work (claude-mutation-lane handoff)
  - Stages and commits codex's in-flight slice work that rev_pkt_3839 handed off to
  - the claude mutation lane: CheckpointBudgetShape classifier wiring, agent-supervise
  - driver consumer integration, AnchorScope + ReviewerResponseShape updates,
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`0928a483`** — Stage agent_supervise import set + adapter wiring (recover from smell #058 layer-e)
  - Stages the 4 untracked agent_supervise files (driver + parser adapter +
  - orchestration consumer + test) plus the 3 modified files that wire them into
  - cli.py / entrypoint.py / orchestration_inputs.py. Closes startup-authority
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`28bcafdd`** — Refresh policy-owned generated surfaces for 87554eb9
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`87554eb9`** — Refresh external review snapshot for 9249e17c
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`9249e17c` | MPs: MP-377** — Land MP-377 typed governance work-in-progress (multi-slice)
  - Multi-slice landing of in-flight typed governance work. Closes
  - smell #058 layer-a (continuation_anchor cross-session bypass) via
  - paired anchor scope + body-observation oracle extended to all 3
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Review-channel dogfood found that remote-control launch recovery still had a raw trusted-mode hole: the system could emit provider dangerous/no-prompt flags without proving a current typed bypass lifecycle. That made bl…
- **`771a7fa5`** — Refresh external review snapshot for 73417c6a
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`73417c6a`** — Stop push preflight projection receipt loops
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`fd9ed509`** — Refresh external review snapshot for c9616cfe
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`c9616cfe`** — Fix push bridge sync test mocks
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`170167c1`** — Refresh external review snapshot for fe5b9538
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`fe5b9538`** — Fix startup reviewer mode authority
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`18685099`** — Refresh external review snapshot for c4e50e10
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`c4e50e10`** — Refresh external review snapshot for 1036a84b
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`1036a84b`** — Document push preflight projection policy
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`8b8900d6`** — Refresh external review snapshot for 0fa60654
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`0fa60654`** — Fix push preflight audit routing
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`5b5c0d06`** — Refresh external review snapshot for 9aba52e2
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`9aba52e2`** — Refresh policy-owned generated surfaces for 905794d7
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`905794d7`** — Refresh external review snapshot for 5068dcf7
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
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

- open governance findings: 43

### Startup advisories
- checkpoint_before_continue: dirty_after_local_checkpoint

### Stale warnings
- Relaunch the reviewer loop immediately.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/integrations_import.py`): dogfood.command.integrations-import: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/export.py`): dogfood.command.governance-export: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/review_channel/instruction_transitions.py`): packet.transition_session_disambiguation: source_packet_ids=rev_pkt_2691,rev_pkt_2696,rev_pkt_2705; Claude beta finding: transition_packet ack/apply/dismiss paths bypass session disambiguation, allowing cross-session packet actions. Durable owner: MP377-GUARDIR-TRANSITION-DISAMBIGUATION.
- **governance_open** (`dev/scripts/devctl/runtime/packet_carry_forward.py`): packet.durable_ingestion_before_ttl: source_packet_ids=rev_pkt_2691,rev_pkt_2696,rev_pkt_2697,rev_pkt_2699,rev_pkt_2700,rev_pkt_2701,rev_pkt_2702,rev_pkt_2704,rev_pkt_2705; packets are transport/provenance only, so packet-carried work must be promoted into PlanRow/FindingReview/GuardPromotionCandidate/knowledge state before TTL expiry. Durable owner: MP377-GUARDIR-PACKET-DURABLE-INGESTION.
- **governance_open** (`dev/scripts/checks/multi_agent_sync`): agent_sync.ambiguity_projection: source_packet_ids=rev_pkt_2697,rev_pkt_2705; canonical_active_packet_ambiguity can render empty while ambiguity exists, and expired-but-pending split state creates carry-forward debt. Durable owner: MP377-GUARDIR-AGENT-SYNC-AMBIGUITY-CARRYFORWARD.
- **governance_open** (`dev/scripts/devctl/commands/review_channel`): review_channel.command_latency_under_fanout: source_packet_ids=rev_pkt_2704,rev_pkt_2705; review-channel post and startup-context can hang under multi-agent load, tied to process-cleanup and detached sleep pressure. Durable owner: MP377-GUARDIR-FANOUT-COMMAND-HANGS.
- **governance_open** (`dev/scripts/devctl/runtime/agent_dispatch_router.py`): work_board.rows_duplication: source_packet_ids=rev_pkt_2700,rev_pkt_2705; _work_board_rows logic is duplicated between packet_route_resolution.py and agent_dispatch_router.py. Durable owner: MP377-GUARDIR-WORK-BOARD-ROUTE-DEDUP.
- **governance_open** (`dev/scripts/devctl/commands/reports_cleanup.py`): dogfood.command.reports-cleanup: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-f1b07a6838d3` binds this file to HEAD `42683c3f7457`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
