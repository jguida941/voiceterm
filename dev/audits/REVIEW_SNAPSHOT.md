# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `625580afd2c7` — Refresh policy-owned generated surfaces for c3adea3a
- Tree hash: `fcee6e103b60`
- Generation stamp: `snap-4ec1eba1ae61`
- Generated at (UTC): 2026-05-02T18:56:07Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 136 files, +11562/-2069
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
- HEAD SHA: `625580afd2c71a58e0f2ef42173f60be4f4a2fdb`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-02T14:51:50-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 1
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260502T185013018877Z` (valid=True)
- authorized_head_commit: `c3adea3a06ad2024a1bf09bd4d917d704d068b9c`
- approved_target_identity: `tree-receipt-20260502T185013018877Z:1b241a84985feaf5ba2459d351d58082aec46d79`
- publication_backlog: urgent
- publication_guidance: 15 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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

Range: last 24 commits ending at `625580afd2c7`

- commits: 24
- files changed: 136
- insertions: +11562
- deletions: -2069
- bundle classes touched: docs, tooling
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 3 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `625580af` | Refresh policy-owned generated surfaces for c3adea3a | 1 | +1/-1 | docs |  |
| 2 | `c3adea3a` | Refresh external review snapshot for ff9988fe | 2 | +57/-54 | docs |  |
| 3 | `ff9988fe` | Add failure packet router | 3 | +467/-57 | tooling |  |
| 4 | `11ede1db` | Refresh external review snapshot for 492a2f37 | 2 | +64/-78 | docs |  |
| 5 | `492a2f37` | drift before reviewer launch | 4 | +57/-49 | tooling |  |
| 6 | `be1a3a04` | Refresh external review snapshot for be2c47c0 | 2 | +58/-59 | docs |  |
| 7 | `be2c47c0` | Refresh managed projection surfaces (terminal-app launch pr… | 4 | +56/-51 | tooling |  |
| 8 | `dfeb010d` | Refresh external review snapshot for 007b574f | 2 | +59/-60 | docs |  |
| 9 | `007b574f` | Refresh managed projection surfaces (single_agent launch pr… | 4 | +60/-56 | tooling |  |
| 10 | `3b643953` | Refresh managed projection surfaces (post-9537766e follow-u… | 3 | +61/-54 | tooling |  |
| 11 | `a8a150d1` | Refresh external review snapshot for 9537766e | 2 | +60/-59 | docs |  |
| 12 | `9537766e` | Refresh managed projection surfaces (post-7f4b5bf4 follow-u… | 3 | +61/-56 | tooling |  |
| 13 | `08d33a43` | Refresh policy-owned generated surfaces for 4fc6a797 | 1 | +1/-1 | docs |  |
| 14 | `4fc6a797` | Refresh external review snapshot for 7f4b5bf4 | 2 | +68/-64 | docs |  |
| 15 | `7f4b5bf4` | Wake-binding slice + auto-dispatcher prep refactor (T22AN-C… | 29 | +1824/-171 | tooling |  |
| 16 | `b06b38b4` | Refresh policy-owned generated surfaces for e61fdda3 | 1 | +1/-1 | docs |  |
| 17 | `e61fdda3` | Refresh external review snapshot for 1fcceafa | 2 | +76/-90 | docs |  |
| 18 | `1fcceafa` | Protect review-channel monitors from cleanup | 11 | +440/-57 | tooling |  |
| 19 | `4a77272a` | Refresh external review snapshot for 05425b97 | 2 | +45/-45 | docs |  |
| 20 | `05425b97` | Refresh external review snapshot for 2dc272ea | 1 | +64/-63 | tooling |  |
| 21 | `2dc272ea` | Refresh policy-owned generated surfaces for 00e74e7c | 2 | +6/-4 | docs |  |
| 22 | `00e74e7c` | Refresh external review snapshot for e83a5e75 | 2 | +80/-78 | docs |  |
| 23 | `e83a5e75` | Add typed develop orchestration controller | 109 | +7827/-787 | tooling | Parser / ANSI boundary |
| 24 | `e6c5cdf4` | Checkpoint typed projection drift after rev_pkt_2716 binding | 3 | +69/-74 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.claude/commands/develop.md` | docs | +6/-2 |
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `AGENTS.md` | docs | +2/-0 |
| `bridge.md` | docs | +49/-51 |
| `dev/active/MASTER_PLAN.md` | tooling | +603/-4 |
| `dev/active/ai_governance_platform.md` | tooling | +7/-0 |
| `dev/active/autonomous_governance_loop_v2.md` | tooling | +25/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1149/-1158 |
| `dev/guides/DEVELOPMENT.md` | docs | +6/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +7/-7 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +56/-1 |
| `dev/scripts/README.md` | tooling | +61/-6 |
| `dev/scripts/checks/check_orchestration_recommendation_closure.py` | tooling | +12/-0 |
| `dev/scripts/checks/governance_closure/command.py` | tooling | +1/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop.py` | tooling | +16/-2 |
| `dev/scripts/checks/orchestration_recommendation_closure/README.md` | tooling | +5/-0 |
| `dev/scripts/checks/orchestration_recommendation_closure/__init__.py` | tooling | +2/-0 |
| `dev/scripts/checks/orchestration_recommendation_closure/command.py` | tooling | +171/-0 |
| `dev/scripts/checks/review_probes/probe_packet_carry_forward_debt.py` | tooling | +9/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/cli_parser/artifact_suppression.py` | tooling | +77/-0 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +6/-34 |
| `dev/scripts/devctl/commands/check/process_sweep.py` | tooling | +33/-1 |
| `dev/scripts/devctl/commands/development/actor_resolution.py` | tooling | +115/-4 |
| `dev/scripts/devctl/commands/development/collaboration_models.py` | tooling | +100/-0 |
| `dev/scripts/devctl/commands/development/continuation.py` | tooling | +74/-0 |
| `dev/scripts/devctl/commands/development/continuation_commands.py` | tooling | +49/-0 |
| `dev/scripts/devctl/commands/development/lifecycle.py` | tooling | +136/-0 |
| `dev/scripts/devctl/commands/development/lifecycle_commands.py` | tooling | +32/-0 |
| `dev/scripts/devctl/commands/development/lifecycle_packet_steps.py` | tooling | +42/-0 |
| `dev/scripts/devctl/commands/development/lifecycle_watch_steps.py` | tooling | +29/-0 |
| `dev/scripts/devctl/commands/development/lifecycle_workflow_steps.py` | tooling | +77/-0 |
| `dev/scripts/devctl/commands/development/models.py` | tooling | +69/-0 |
| `dev/scripts/devctl/commands/development/next_slice.py` | tooling | +99/-3 |
| `dev/scripts/devctl/commands/development/orchestration_agent_loop.py` | tooling | +64/-0 |
| `dev/scripts/devctl/commands/development/orchestration_agent_loop_parse.py` | tooling | +53/-0 |
| `dev/scripts/devctl/commands/development/orchestration_agent_loop_rows.py` | tooling | +46/-0 |
| `dev/scripts/devctl/commands/development/orchestration_agent_loop_state.py` | tooling | +66/-0 |
| `dev/scripts/devctl/commands/development/orchestration_inputs.py` | tooling | +89/-0 |
| _96 more files trimmed_ | | |

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
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit 7f4b5bf4 changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/wake_receipt_models.py`) — Commit 7f4b5bf4 changed dev/scripts/devctl/review_channel/wake_receipt_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/development/collaboration_models.py`) — Commit e83a5e75 changed dev/scripts/devctl/commands/development/collaboration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/development/orchestration_models.py`) — Commit e83a5e75 changed dev/scripts/devctl/commands/development/orchestration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit e83a5e75 changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_creation_binding_contracts.py`) — Commit e83a5e75 changed dev/scripts/devctl/review_channel/packet_creation_binding_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_debt_remediation_contracts.py`) — Commit e83a5e75 changed dev/scripts/devctl/review_channel/packet_debt_remediation_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/packet_debt_remediation_contracts.py`) — Commit e83a5e75 changed dev/scripts/devctl/runtime/packet_debt_remediation_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit e83a5e75 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`625580af`** — Refresh policy-owned generated surfaces for c3adea3a
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`c3adea3a`** — Refresh external review snapshot for ff9988fe
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`ff9988fe`** — Add failure packet router
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`11ede1db`** — Refresh external review snapshot for 492a2f37
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`492a2f37`** — drift before reviewer launch
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`be1a3a04`** — Refresh external review snapshot for be2c47c0
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`be2c47c0` | MPs: MP-377** — Refresh managed projection surfaces (terminal-app launch prep)
  - Anchors: section:MP-377
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`dfeb010d`** — Refresh external review snapshot for 007b574f
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`007b574f` | MPs: MP-377** — Refresh managed projection surfaces (single_agent launch prep)
  - Anchors: section:MP-377
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-4ec1eba1ae61` binds this file to HEAD `625580afd2c7`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
