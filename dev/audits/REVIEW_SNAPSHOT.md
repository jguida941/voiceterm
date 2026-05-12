# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `9249e17cc896` — Land MP-377 typed governance work-in-progress (multi-slice)
- Tree hash: `6d51acf8e039`
- Generation stamp: `snap-3adf4e57ec61`
- Generated at (UTC): 2026-05-12T04:22:04Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 207 files, +15160/-1684
- Governance findings: 43 open / 0 fixed / 43 total
- Probe hints: 0 total across 0 files scanned

## 1. Identity

- Repository: **VoiceTerm**
- Product thesis: This is the product thesis for the governance stack in this repository.
Absorb these four commitments before engaging with SOP, guard, routing,
or plan detail — they explain why the process exists.

This repo builds a portable AI governance platform proven through one
production client (VoiceTerm, a Rust voice-first terminal overlay for AI
CLIs). The product thesis is that executable local control — guards,
probes, typed actions, deterministic policy resolution — is what m...
- Remote: `https://github.com/jguida941/voiceterm.git`
- Default branch: `master`
- Current branch: `feature/governance-quality-sweep`
- HEAD SHA: `9249e17cc8963eca6c6af744de4d6dff6dd6c9d9`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-12T00:21:12-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report_state: `published_remote` (post_push_bundle_failed)
- publication_backlog: queued
- publication_guidance: 1 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `tools_only`
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

Range: last 24 commits ending at `9249e17cc896`

- commits: 24
- files changed: 207
- insertions: +15160
- deletions: -1684
- bundle classes touched: docs, tooling
- authority surfaces touched: 13 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `9249e17c` | Land MP-377 typed governance work-in-progress (multi-slice) | 176 | +12985/-235 | tooling |  |
| 2 | `771a7fa5` | Refresh external review snapshot for 73417c6a | 2 | +71/-72 | docs |  |
| 3 | `73417c6a` | Stop push preflight projection receipt loops | 5 | +138/-53 | tooling |  |
| 4 | `fd9ed509` | Refresh external review snapshot for c9616cfe | 2 | +55/-55 | docs |  |
| 5 | `c9616cfe` | Fix push bridge sync test mocks | 4 | +51/-56 | tooling |  |
| 6 | `170167c1` | Refresh external review snapshot for fe5b9538 | 2 | +66/-65 | docs |  |
| 7 | `fe5b9538` | Fix startup reviewer mode authority | 5 | +95/-60 | tooling |  |
| 8 | `18685099` | Refresh external review snapshot for c4e50e10 | 2 | +40/-40 | docs |  |
| 9 | `c4e50e10` | Refresh external review snapshot for 1036a84b | 2 | +64/-64 | docs |  |
| 10 | `1036a84b` | Document push preflight projection policy | 9 | +94/-55 | tooling |  |
| 11 | `8b8900d6` | Refresh external review snapshot for 0fa60654 | 2 | +64/-62 | docs |  |
| 12 | `0fa60654` | Fix push preflight audit routing | 8 | +185/-59 | tooling |  |
| 13 | `5b5c0d06` | Refresh external review snapshot for 9aba52e2 | 1 | +40/-40 | tooling |  |
| 14 | `9aba52e2` | Refresh policy-owned generated surfaces for 905794d7 | 1 | +1/-1 | docs |  |
| 15 | `905794d7` | Refresh external review snapshot for 5068dcf7 | 2 | +66/-67 | docs |  |
| 16 | `5068dcf7` | Fix push preflight report backpressure | 6 | +264/-103 | tooling |  |
| 17 | `bc5bc45d` | Refresh external review snapshot for da712f39 | 1 | +52/-52 | tooling |  |
| 18 | `da712f39` | Refresh external review snapshot for c1d6f59f | 2 | +46/-47 | docs |  |
| 19 | `c1d6f59f` | Refresh external review snapshot for 35002759 | 2 | +72/-71 | docs |  |
| 20 | `35002759` | Fix review-channel declared mode authority | 21 | +378/-180 | tooling |  |
| 21 | `9318cfd0` | Refresh external review snapshot for d555dc0f | 1 | +54/-55 | tooling |  |
| 22 | `d555dc0f` | Refresh external review snapshot for df64f077 | 2 | +62/-62 | docs |  |
| 23 | `df64f077` | Keep communication-only packets out of instruction authority | 5 | +172/-85 | tooling |  |
| 24 | `f14b9338` | Refresh external review snapshot for 827ffafb | 2 | +45/-45 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.claude/commands/develop.md` | docs | +3/-1 |
| `AGENTS.md` | docs | +6/-1 |
| `bridge.md` | docs | +81/-81 |
| `codesmells.md` | docs | +356/-0 |
| `dev/active/MASTER_PLAN.md` | tooling | +107/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +4/-2 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1176/-1177 |
| `dev/guides/DEVELOPMENT.md` | docs | +13/-1 |
| `dev/guides/SYSTEM_MAP.md` | docs | +2/-2 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +59/-0 |
| `dev/scripts/README.md` | tooling | +15/-2 |
| `dev/scripts/checks/check_checkpoint_budget_shape.py` | tooling | +11/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth.py` | tooling | +98/-1 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_instruction.py` | tooling | +172/-1 |
| `dev/scripts/checks/startup_authority_contract/checkpoint_budget_shape_command.py` | tooling | +79/-0 |
| `dev/scripts/checks/startup_authority_contract/command.py` | tooling | +24/-2 |
| `dev/scripts/checks/startup_authority_contract/runtime_checks.py` | tooling | +318/-9 |
| `dev/scripts/devctl/cli_parser/artifact_suppression.py` | tooling | +0/-1 |
| `dev/scripts/devctl/commands/demo.py` | tooling | +43/-2 |
| `dev/scripts/devctl/commands/development/command.py` | tooling | +12/-0 |
| `dev/scripts/devctl/commands/development/continuation.py` | tooling | +72/-4 |
| `dev/scripts/devctl/commands/development/models.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/development/orchestration_models.py` | tooling | +4/-0 |
| `dev/scripts/devctl/commands/development/packet_attention.py` | tooling | +18/-4 |
| `dev/scripts/devctl/commands/development/packet_attention_commands.py` | tooling | +10/-4 |
| `dev/scripts/devctl/commands/development/packet_attention_support.py` | tooling | +122/-0 |
| `dev/scripts/devctl/commands/development/parser.py` | tooling | +47/-0 |
| `dev/scripts/devctl/commands/development/plan_intake_receipts.py` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/development/render.py` | tooling | +95/-0 |
| `dev/scripts/devctl/commands/development/report.py` | tooling | +112/-13 |
| `dev/scripts/devctl/commands/pipeline/status_action.py` | tooling | +13/-0 |
| `dev/scripts/devctl/commands/reporting/claude_loop_compact.py` | tooling | +5/-0 |
| `dev/scripts/devctl/commands/review_channel/_reviewer.py` | tooling | +120/-52 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +27/-0 |
| `dev/scripts/devctl/commands/review_channel/event_packet_transition_action.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/review_channel/event_post_action.py` | tooling | +67/-2 |
| `dev/scripts/devctl/commands/review_channel/event_watch_support.py` | tooling | +6/-0 |
| `dev/scripts/devctl/commands/review_channel/status_bridge_sync.py` | tooling | +4/-3 |
| `dev/scripts/devctl/commands/review_channel_command/constants.py` | tooling | +0/-1 |
| `dev/scripts/devctl/commands/review_channel_command/validation.py` | tooling | +17/-0 |
| _167 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/checkpoint_budget_shape_command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_checks.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_parser.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_metadata.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_follow_heartbeat_guard.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/development/orchestration_models.py`) — Commit 9249e17c changed dev/scripts/devctl/commands/development/orchestration_models.py
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
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit 9249e17c changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
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

- **`9249e17c` | MPs: MP-377** — Land MP-377 typed governance work-in-progress (multi-slice)
  - Multi-slice landing of in-flight typed governance work. Closes
  - smell #058 layer-a (continuation_anchor cross-session bypass) via
  - paired anchor scope + body-observation oracle extended to all 3
  - plan: `dev/active/ai_governance_platform.md`
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
- **`5068dcf7`** — Fix push preflight report backpressure
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`bc5bc45d`** — Refresh external review snapshot for da712f39
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`da712f39`** — Refresh external review snapshot for c1d6f59f
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`c1d6f59f`** — Refresh external review snapshot for 35002759
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`35002759`** — Fix review-channel declared mode authority
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`9318cfd0`** — Refresh external review snapshot for d555dc0f
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`d555dc0f`** — Refresh external review snapshot for df64f077
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`df64f077`** — Keep communication-only packets out of instruction authority
  - evolution: Live MP-377 dogfood exposed a second half of the TASK_COMPLETE continuation gap: `TaskCompleteDecision` could reject termination for an active `continuation_anchor`, but the review-channel post path still stamped the ge…
- **`f14b9338`** — Refresh external review snapshot for 827ffafb
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
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-3adf4e57ec61` binds this file to HEAD `9249e17cc896`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
