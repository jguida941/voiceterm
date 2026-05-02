# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `3b643953720c` — Refresh managed projection surfaces (post-9537766e follow-up)
- Tree hash: `ae92b3461138`
- Generation stamp: `snap-49d351885ba3`
- Generated at (UTC): 2026-05-02T17:02:01Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 467 files, +59295/-4901
- Governance findings: 152 open / 88 fixed / 254 total
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
- HEAD SHA: `3b643953720c8d49cbab38a130dd638f7aa1b422`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-02T12:51:27-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 2
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260502T165027278457Z` (valid=True)
- authorized_head_commit: `3b643953720c8d49cbab38a130dd638f7aa1b422`
- approved_target_identity: `tree-receipt-20260502T165027278457Z:ae92b3461138e036b38fe3543551118bdc00e50a`
- publication_backlog: urgent
- publication_guidance: 6 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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

Range: last 24 commits ending at `3b643953720c`

- commits: 24
- files changed: 467
- insertions: +59295
- deletions: -4901
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 21 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `3b643953` | Refresh managed projection surfaces (post-9537766e follow-u… | 3 | +61/-54 | tooling |  |
| 2 | `a8a150d1` | Refresh external review snapshot for 9537766e | 2 | +60/-59 | docs |  |
| 3 | `9537766e` | Refresh managed projection surfaces (post-7f4b5bf4 follow-u… | 3 | +61/-56 | tooling |  |
| 4 | `08d33a43` | Refresh policy-owned generated surfaces for 4fc6a797 | 1 | +1/-1 | docs |  |
| 5 | `4fc6a797` | Refresh external review snapshot for 7f4b5bf4 | 2 | +68/-64 | docs |  |
| 6 | `7f4b5bf4` | Wake-binding slice + auto-dispatcher prep refactor (T22AN-C… | 29 | +1824/-171 | tooling |  |
| 7 | `b06b38b4` | Refresh policy-owned generated surfaces for e61fdda3 | 1 | +1/-1 | docs |  |
| 8 | `e61fdda3` | Refresh external review snapshot for 1fcceafa | 2 | +76/-90 | docs |  |
| 9 | `1fcceafa` | Protect review-channel monitors from cleanup | 11 | +440/-57 | tooling |  |
| 10 | `4a77272a` | Refresh external review snapshot for 05425b97 | 2 | +45/-45 | docs |  |
| 11 | `05425b97` | Refresh external review snapshot for 2dc272ea | 1 | +64/-63 | tooling |  |
| 12 | `2dc272ea` | Refresh policy-owned generated surfaces for 00e74e7c | 2 | +6/-4 | docs |  |
| 13 | `00e74e7c` | Refresh external review snapshot for e83a5e75 | 2 | +80/-78 | docs |  |
| 14 | `e83a5e75` | Add typed develop orchestration controller | 109 | +7827/-787 | tooling | Parser / ANSI boundary |
| 15 | `e6c5cdf4` | Checkpoint typed projection drift after rev_pkt_2716 binding | 3 | +69/-74 | tooling |  |
| 16 | `dd4d7897` | Add typed develop controller and packet binding | 45 | +3059/-1059 | tooling | Parser / ANSI boundary |
| 17 | `4f589933` | WIP checkpoint: multi-agent /develop slice + Claude-tester… | 301 | +34713/-731 | tooling | Parser / ANSI boundary |
| 18 | `924ba57d` | Snapshot for ChatGPT Pro Slice 4.1 deep-dive context | 20 | +1669/-132 | tooling |  |
| 19 | `105c6b6a` | Refresh external review snapshot for 7404cc42 | 1 | +54/-51 | tooling |  |
| 20 | `7404cc42` | Refresh projections after 9f492c39 | 3 | +97/-83 | docs |  |
| 21 | `9f492c39` | WIP snapshot: Slice A.5 lifecycle unification + connectivit… | 140 | +8870/-1093 | tooling | Parser / ANSI boundary |
| 22 | `07ac1bd3` | Refresh external review snapshot for 6902e3c8 | 1 | +52/-52 | tooling |  |
| 23 | `6902e3c8` | Refresh external review snapshot for ee2ee1b1 | 2 | +50/-54 | docs |  |
| 24 | `ee2ee1b1` | Refresh external review snapshot for afb62cdf | 1 | +48/-42 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.claude/commands/develop.md` | docs | +22/-2 |
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `.gitignore` | tooling | +4/-1 |
| `AGENTS.md` | docs | +24/-1 |
| `bridge.md` | docs | +83/-81 |
| `dev/active/MASTER_PLAN.md` | tooling | +894/-9 |
| `dev/active/ai_governance_platform.md` | tooling | +1844/-2 |
| `dev/active/autonomous_governance_loop_v2.md` | tooling | +132/-4 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1357/-1335 |
| `dev/config/quality_presets/portable_python.json` | tooling | +8/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +43/-3 |
| `dev/guides/PLATFORM_GUIDE.md` | docs | +544/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +37/-21 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +351/-2 |
| `dev/scripts/README.md` | tooling | +146/-19 |
| `dev/scripts/checks/check_orchestration_recommendation_closure.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_provider_list_parity_graph.py` | tooling | +13/-0 |
| `dev/scripts/checks/check_registry_path_integrity.py` | tooling | +13/-0 |
| `dev/scripts/checks/check_runtime_spine_closure.py` | tooling | +13/-0 |
| `dev/scripts/checks/governance_closure/command.py` | tooling | +1/-0 |
| `dev/scripts/checks/multi_agent_sync/report.py` | tooling | +61/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth.py` | tooling | +94/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop.py` | tooling | +177/-2 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_attention.py` | tooling | +56/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_instruction.py` | tooling | +75/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_packet_attention.py` | tooling | +54/-0 |
| `dev/scripts/checks/mutation_outcome_parse.py` | tooling | +4/-1 |
| `dev/scripts/checks/orchestration_recommendation_closure/README.md` | tooling | +5/-0 |
| `dev/scripts/checks/orchestration_recommendation_closure/__init__.py` | tooling | +2/-0 |
| `dev/scripts/checks/orchestration_recommendation_closure/command.py` | tooling | +171/-0 |
| `dev/scripts/checks/package_layout/shim_validation.py` | tooling | +38/-1 |
| `dev/scripts/checks/probe_command_result_contract.py` | tooling | +12/-0 |
| `dev/scripts/checks/probe_event_field_naming_consistency.py` | tooling | +12/-0 |
| `dev/scripts/checks/probe_event_id_uniqueness.py` | tooling | +12/-0 |
| `dev/scripts/checks/probe_inter_agent_communication_lag.py` | tooling | +12/-0 |
| `dev/scripts/checks/probe_packet_carry_forward_debt.py` | tooling | +12/-0 |
| `dev/scripts/checks/provider_list_parity_graph/__init__.py` | tooling | +2/-0 |
| `dev/scripts/checks/provider_list_parity_graph/command.py` | tooling | +150/-0 |
| `dev/scripts/checks/registry_path_integrity/__init__.py` | tooling | +2/-0 |
| _427 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 254
- open: 152
- fixed: 88
- false positives: 0

Recent findings:
- `dogfood.command.status` — `dev/scripts/devctl/commands/reporting/status.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.render-surfaces` — `dev/scripts/devctl/commands/governance/render_surfaces.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-loop` — `dev/scripts/devctl/commands/reporting/claude_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-mind` — `dev/scripts/devctl/commands/agent_mind/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.governance-bootstrap` — `dev/scripts/devctl/commands/governance/bootstrap.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.orchestrate-status` — `dev/scripts/devctl/commands/reporting/orchestrate_status.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.orchestrate-watch` — `dev/scripts/devctl/commands/governance/orchestrate_watch.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.integrations-import` — `dev/scripts/devctl/commands/integrations_import.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.governance-export` — `dev/scripts/devctl/commands/governance/export.py` (n/a, verdict=`confirmed_issue`)
- `packet.transition_session_disambiguation` — `dev/scripts/devctl/review_channel/instruction_transitions.py` (critical, verdict=`confirmed_issue`)

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

- **risk**: Parser / ANSI boundary — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_launch_headless.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/remote_commit_pipeline_artifact.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_file.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/control_plane_startup_authority.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_parser.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_receipt.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actions.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_parser_state_rows.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit 7f4b5bf4 changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/wake_receipt_models.py`) — Commit 7f4b5bf4 changed dev/scripts/devctl/review_channel/wake_receipt_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/development/collaboration_models.py`) — Commit e83a5e75 changed dev/scripts/devctl/commands/development/collaboration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/development/orchestration_models.py`) — Commit e83a5e75 changed dev/scripts/devctl/commands/development/orchestration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit e83a5e75 changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_creation_binding_contracts.py`) — Commit e83a5e75 changed dev/scripts/devctl/review_channel/packet_creation_binding_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_debt_remediation_contracts.py`) — Commit e83a5e75 changed dev/scripts/devctl/review_channel/packet_debt_remediation_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/packet_debt_remediation_contracts.py`) — Commit e83a5e75 changed dev/scripts/devctl/runtime/packet_debt_remediation_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit e83a5e75 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/checks/probe_command_result_contract.py`) — Commit 4f589933 changed dev/scripts/checks/probe_command_result_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/checks/review_probes/probe_command_result_contract.py`) — Commit 4f589933 changed dev/scripts/checks/review_probes/probe_command_result_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit 4f589933 changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/agent_sync_models.py`) — Commit 4f589933 changed dev/scripts/devctl/review_channel/agent_sync_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/agent_work_board_models.py`) — Commit 4f589933 changed dev/scripts/devctl/review_channel/agent_work_board_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit 4f589933 changed dev/scripts/devctl/review_channel/packet_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Commit 4f589933 changed dev/scripts/devctl/review_channel/reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/agent_dispatch_router_models.py`) — Commit 4f589933 changed dev/scripts/devctl/runtime/agent_dispatch_router_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/agent_loop_decision_models.py`) — Commit 4f589933 changed dev/scripts/devctl/runtime/agent_loop_decision_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/dogfood_models.py`) — Commit 4f589933 changed dev/scripts/devctl/runtime/dogfood_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/dogfood_scenario_models.py`) — Commit 4f589933 changed dev/scripts/devctl/runtime/dogfood_scenario_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_collaboration_models.py`) — Commit 4f589933 changed dev/scripts/devctl/runtime/review_state_collaboration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit 4f589933 changed dev/scripts/devctl/runtime/review_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_packet_models.py`) — Commit 4f589933 changed dev/scripts/devctl/runtime/review_state_packet_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit 4f589933 changed dev/scripts/devctl/runtime/reviewer_runtime_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/startup_context_models.py`) — Commit 4f589933 changed dev/scripts/devctl/runtime/startup_context_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_probe_command_result_contract.py`) — Commit 4f589933 changed dev/scripts/devctl/tests/checks/test_probe_command_result_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py`) — Commit 4f589933 changed dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/coordination_snapshot_models.py`) — Commit 9f492c39 changed dev/scripts/devctl/platform/coordination_snapshot_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_intake_models.py`) — Commit 9f492c39 changed dev/scripts/devctl/runtime/work_intake_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`3b643953` | MPs: MP-377** — Refresh managed projection surfaces (post-9537766e follow-up)
  - Standard auto-regenerated drift cleanup per typed
  - recommended_action=commit_before_push. Unblocks fresh Codex
  - session launch so his investigation agents can pick up rev_pkt_2779
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`a8a150d1`** — Refresh external review snapshot for 9537766e
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`9537766e` | MPs: MP-377** — Refresh managed projection surfaces (post-7f4b5bf4 follow-up)
  - Auto-regenerated after the wake-binding slice + auto-dispatcher prep
  - refactor commit. Per startup-authority typed gate
  - recommended_action=commit_before_push, committing these projection
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`08d33a43`** — Refresh policy-owned generated surfaces for 4fc6a797
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`4fc6a797`** — Refresh external review snapshot for 7f4b5bf4
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`7f4b5bf4` | MPs: MP-377** — Wake-binding slice + auto-dispatcher prep refactor (T22AN-C/F + plan revision r2 prep)
  - Operator-authorized scope: 'commit and push the wake-binding slice from the
  - dashboard' (2026-05-02T14:35Z) + 'Codex reviews and you code' role flip.
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`b06b38b4`** — Refresh policy-owned generated surfaces for e61fdda3
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`e61fdda3`** — Refresh external review snapshot for 1fcceafa
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`1fcceafa`** — Protect review-channel monitors from cleanup
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`4a77272a`** — Refresh external review snapshot for 05425b97
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`05425b97`** — Refresh external review snapshot for 2dc272ea
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`2dc272ea`** — Refresh policy-owned generated surfaces for 00e74e7c
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`00e74e7c`** — Refresh external review snapshot for e83a5e75
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`e83a5e75`** — Add typed develop orchestration controller
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`e6c5cdf4`** — Checkpoint typed projection drift after rev_pkt_2716 binding
  - Reducer-owned diff:
  - - bridge.md: poll timestamp + worktree hash + open-findings count (7->8)
  -   + reviewer-owned instruction now 'Await reviewer instruction refresh'
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`dd4d7897`** — Add typed develop controller and packet binding
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`4f589933` | MPs: MP-377** — WIP checkpoint: multi-agent /develop slice + Claude-tester verification cycle
  - Operator-authorized raw commit (--no-verify) to safe-up local work
  - mid-slice. Bundles A through AA filed via review-channel during the
  - session; Codex slice work in flight on /develop controller, agent
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`924ba57d`** — Snapshot for ChatGPT Pro Slice 4.1 deep-dive context
  - Push so external review (ChatGPT Pro deep-dive on Rust strengthening for
  - Slice 4.1 Graph Health) sees full local context, not the stale GitHub HEAD.
  - This is in-flight Codex slice-close work — NOT a clean checkpoint.
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`105c6b6a`** — Refresh external review snapshot for 7404cc42
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`7404cc42`** — Refresh projections after 9f492c39
  - Auto-regenerated projection receipts captured by post-commit hooks after
  - the Slice A.5 WIP snapshot:
  - - bridge.md: Codex poll timestamp + worktree hash rotation,
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`9f492c39`** — WIP snapshot: Slice A.5 lifecycle unification + connectivity progress
  - Save in-flight work-in-progress before continuing GuardIR plan 4.1+ V2.1
  - Slice A.5 / runtime-agreement / connectivity sweep. Includes:
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`07ac1bd3`** — Refresh external review snapshot for 6902e3c8
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`6902e3c8`** — Refresh external review snapshot for ee2ee1b1
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`ee2ee1b1`** — Refresh external review snapshot for afb62cdf
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/autonomous_governance_loop_v2.md` MP-377): headless
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b ev…
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:

## 8. Known gaps and open items

- open governance findings: 152

### Startup advisories
- checkpoint_before_continue: dirty_after_local_checkpoint

### Stale warnings
- Relaunch the reviewer loop immediately.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/reporting/status.py`): dogfood.command.status: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/render_surfaces.py`): dogfood.command.render-surfaces: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/reporting/claude_loop.py`): dogfood.command.agent-loop: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/agent_mind/command.py`): dogfood.command.agent-mind: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/bootstrap.py`): dogfood.command.governance-bootstrap: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/reporting/orchestrate_status.py`): dogfood.command.orchestrate-status: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/orchestrate_watch.py`): dogfood.command.orchestrate-watch: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/integrations_import.py`): dogfood.command.integrations-import: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-49d351885ba3` binds this file to HEAD `3b643953720c`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
