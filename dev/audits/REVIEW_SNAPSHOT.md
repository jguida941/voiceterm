# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `e6c5cdf47d7b` — Checkpoint typed projection drift after rev_pkt_2716 binding
- Tree hash: `3e749f4a737b`
- Generation stamp: `snap-23aaa24e5033`
- Generated at (UTC): 2026-05-02T03:41:14Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 475 files, +58820/-4844
- Governance findings: 151 open / 88 fixed / 253 total
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
- HEAD SHA: `e6c5cdf47d7b556d6f3feed0b60b6babf133d799`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-01T20:10:59-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 107
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: recommended
- publication_guidance: 2 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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

Range: last 24 commits ending at `e6c5cdf47d7b`

- commits: 24
- files changed: 475
- insertions: +58820
- deletions: -4844
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary, Dependency / security
- authority surfaces touched: 26 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `e6c5cdf4` | Checkpoint typed projection drift after rev_pkt_2716 binding | 3 | +69/-74 | tooling |  |
| 2 | `dd4d7897` | Add typed develop controller and packet binding | 45 | +3059/-1059 | tooling | Parser / ANSI boundary |
| 3 | `4f589933` | WIP checkpoint: multi-agent /develop slice + Claude-tester… | 301 | +34713/-731 | tooling | Parser / ANSI boundary |
| 4 | `924ba57d` | Snapshot for ChatGPT Pro Slice 4.1 deep-dive context | 20 | +1669/-132 | tooling |  |
| 5 | `105c6b6a` | Refresh external review snapshot for 7404cc42 | 1 | +54/-51 | tooling |  |
| 6 | `7404cc42` | Refresh projections after 9f492c39 | 3 | +97/-83 | docs |  |
| 7 | `9f492c39` | WIP snapshot: Slice A.5 lifecycle unification + connectivit… | 140 | +8870/-1093 | tooling | Parser / ANSI boundary |
| 8 | `07ac1bd3` | Refresh external review snapshot for 6902e3c8 | 1 | +52/-52 | tooling |  |
| 9 | `6902e3c8` | Refresh external review snapshot for ee2ee1b1 | 2 | +50/-54 | docs |  |
| 10 | `ee2ee1b1` | Refresh external review snapshot for afb62cdf | 1 | +48/-42 | tooling |  |
| 11 | `afb62cdf` | Refresh external review snapshot for c2fcb696 | 2 | +61/-63 | docs |  |
| 12 | `c2fcb696` | Enforce typed authority provenance probe | 2 | +52/-52 | tooling |  |
| 13 | `b6cb7332` | Refresh external review snapshot for 3a874752 | 2 | +50/-51 | docs |  |
| 14 | `3a874752` | Refresh external review snapshot for cd57207f | 1 | +46/-46 | tooling |  |
| 15 | `cd57207f` | Refresh external review snapshot for ee7635ed | 2 | +52/-51 | docs |  |
| 16 | `ee7635ed` | Refresh external review snapshot for 0da0bfe1 | 1 | +58/-55 | tooling |  |
| 17 | `0da0bfe1` | Refresh policy-owned generated surfaces for eff73aad | 1 | +1/-1 | docs |  |
| 18 | `eff73aad` | Refresh external review snapshot for 8d31f774 | 2 | +106/-90 | docs |  |
| 19 | `8d31f774` | Implement typed governance continuation | 146 | +9271/-770 | tooling | Parser / ANSI boundary, Dependency / security |
| 20 | `0233390f` | Refresh external review snapshot for 39083dc8 | 2 | +48/-48 | docs |  |
| 21 | `39083dc8` | Refresh external review snapshot for 5af77734 | 1 | +50/-47 | tooling |  |
| 22 | `5af77734` | Refresh external review snapshot for f259c8eb | 2 | +69/-70 | docs |  |
| 23 | `f259c8eb` | Plan 4.1 / MP-377 Codex 42 slice — Layer H push-identity du… | 11 | +227/-81 | tooling |  |
| 24 | `00eb5fd7` | Refresh external review snapshot for cce19014 | 2 | +48/-48 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.claude/commands/develop.md` | docs | +16/-0 |
| `.github/workflows/README.md` | tooling | +1/-0 |
| `.github/workflows/adopter_portability.yml` | tooling | +74/-0 |
| `.gitignore` | tooling | +4/-1 |
| `AGENTS.md` | docs | +45/-13 |
| `bridge.md` | docs | +113/-111 |
| `dev/active/MASTER_PLAN.md` | tooling | +341/-14 |
| `dev/active/ai_governance_platform.md` | tooling | +1938/-4 |
| `dev/active/autonomous_governance_loop_v2.md` | tooling | +107/-4 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1465/-1429 |
| `dev/config/publication_sync_registry.json` | tooling | +1/-27 |
| `dev/config/quality_presets/portable_python.json` | tooling | +10/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +86/-23 |
| `dev/guides/PLATFORM_GUIDE.md` | docs | +544/-0 |
| `dev/guides/PORTABLE_GOVERNANCE_SETUP.md` | docs | +39/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +36/-20 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +510/-7 |
| `dev/scripts/README.md` | tooling | +146/-35 |
| `dev/scripts/checks/README.md` | tooling | +6/-0 |
| `dev/scripts/checks/architecture_probes/README.md` | tooling | +10/-0 |
| `dev/scripts/checks/architecture_probes/probe_architecture_connectivity.py` | tooling | +161/-0 |
| `dev/scripts/checks/architecture_probes/probe_typed_authority_provenance.py` | tooling | +201/-0 |
| `dev/scripts/checks/check_provider_list_parity_graph.py` | tooling | +13/-0 |
| `dev/scripts/checks/check_registry_path_integrity.py` | tooling | +13/-0 |
| `dev/scripts/checks/check_runtime_spine_closure.py` | tooling | +13/-0 |
| `dev/scripts/checks/contract_connectivity/inventory_helpers.py` | tooling | +2/-0 |
| `dev/scripts/checks/multi_agent_sync/report.py` | tooling | +61/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth.py` | tooling | +94/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop.py` | tooling | +161/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_attention.py` | tooling | +56/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_instruction.py` | tooling | +75/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_packet_attention.py` | tooling | +54/-0 |
| `dev/scripts/checks/mutation_outcome_parse.py` | tooling | +4/-1 |
| `dev/scripts/checks/package_layout/shim_validation.py` | tooling | +38/-1 |
| `dev/scripts/checks/probe_architecture_connectivity.py` | tooling | +12/-0 |
| `dev/scripts/checks/probe_command_result_contract.py` | tooling | +12/-0 |
| `dev/scripts/checks/probe_event_field_naming_consistency.py` | tooling | +12/-0 |
| `dev/scripts/checks/probe_event_id_uniqueness.py` | tooling | +12/-0 |
| `dev/scripts/checks/probe_inter_agent_communication_lag.py` | tooling | +12/-0 |
| `dev/scripts/checks/probe_packet_carry_forward_debt.py` | tooling | +12/-0 |
| _435 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 253
- open: 151
- fixed: 88
- false positives: 0

Recent findings:
- `dogfood.command.mutation-score` — `dev/scripts/devctl/commands/mutation_score.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.status` — `dev/scripts/devctl/commands/reporting/status.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.render-surfaces` — `dev/scripts/devctl/commands/governance/render_surfaces.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-loop` — `dev/scripts/devctl/commands/reporting/claude_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-mind` — `dev/scripts/devctl/commands/agent_mind/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.governance-bootstrap` — `dev/scripts/devctl/commands/governance/bootstrap.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.orchestrate-status` — `dev/scripts/devctl/commands/reporting/orchestrate_status.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.orchestrate-watch` — `dev/scripts/devctl/commands/governance/orchestrate_watch.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.integrations-import` — `dev/scripts/devctl/commands/integrations_import.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.governance-export` — `dev/scripts/devctl/commands/governance/export.py` (n/a, verdict=`confirmed_issue`)

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
- **risk**: Dependency / security — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_file.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/remote_commit_pipeline_artifact.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py`) — Review contract-level invariants for this file
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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_metadata.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_parse.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_remote_commit_pipeline_phases34.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit dd4d7897 changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_creation_binding_contracts.py`) — Commit dd4d7897 changed dev/scripts/devctl/review_channel/packet_creation_binding_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit dd4d7897 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/checks/probe_command_result_contract.py`) — Commit 4f589933 changed dev/scripts/checks/probe_command_result_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/checks/review_probes/probe_command_result_contract.py`) — Commit 4f589933 changed dev/scripts/checks/review_probes/probe_command_result_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit 4f589933 changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/agent_sync_models.py`) — Commit 4f589933 changed dev/scripts/devctl/review_channel/agent_sync_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/agent_work_board_models.py`) — Commit 4f589933 changed dev/scripts/devctl/review_channel/agent_work_board_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit 4f589933 changed dev/scripts/devctl/review_channel/event_models.py
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
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/agent_session_continuation_models.py`) — Commit 8d31f774 changed dev/scripts/devctl/runtime/agent_session_continuation_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/master_plan_contract.py`) — Commit 8d31f774 changed dev/scripts/devctl/runtime/master_plan_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Commit 8d31f774 changed dev/scripts/devctl/runtime/project_governance_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`afb62cdf`** — Refresh external review snapshot for c2fcb696
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`c2fcb696`** — Enforce typed authority provenance probe
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`b6cb7332`** — Refresh external review snapshot for 3a874752
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`3a874752`** — Refresh external review snapshot for cd57207f
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`cd57207f`** — Refresh external review snapshot for ee7635ed
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`ee7635ed`** — Refresh external review snapshot for 0da0bfe1
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`0da0bfe1`** — Refresh policy-owned generated surfaces for eff73aad
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`eff73aad`** — Refresh external review snapshot for 8d31f774
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`8d31f774`** — Implement typed governance continuation
  - evolution: Fact: the `rev_pkt_2223` checkpoint retry exposed an automation gap in the remote-control handoff path. The packet carried a valid `stage_commit_pipeline` target and full guard-bundle evidence, and Claude had acked it, …
- **`0233390f`** — Refresh external review snapshot for 39083dc8
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
- **`39083dc8`** — Refresh external review snapshot for 5af77734
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
- **`5af77734`** — Refresh external review snapshot for f259c8eb
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
- **`f259c8eb` | MPs: MP-377** — Plan 4.1 / MP-377 Codex 42 slice — Layer H push-identity duplicate-elimination via reuse of publication_authorization_decision chain-membership authority
  - Closes the 5th gate from this evening's prose-vs-typed-state pattern: governed push identity validation now consumes the same managed receipt-chain authority already proven by `publication_authorization_decision`, so receipt commits above an approved content commit do not trigger a duplicate `ApprovedTargetIdentityViolation`. Preserves fail-closed against fixture/stale/non-managed HEAD drift per memory rule feedback_branch_identity_invariant_required.md (Codex 18 escalation invariants).
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`00eb5fd7`** — Refresh external review snapshot for cce19014
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
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

- open governance findings: 151

### Startup advisories
- checkpoint_before_continue: staged_index_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/mutation_score.py`): dogfood.command.mutation-score: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
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

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-23aaa24e5033` binds this file to HEAD `e6c5cdf47d7b`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
