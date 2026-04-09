# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `a60f14703ea9` — Refresh external review snapshot for 69317302
- Tree hash: `48c15d392933`
- Generation stamp: `snap-c5bd9693ad9c`
- Generated at (UTC): 2026-04-09T13:26:08Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `single_agent`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 174 files, +12750/-4355
- Governance findings: 39 open / 68 fixed / 121 total
- Probe hints: 0 total across 0 files scanned

## 1. Identity

- Repository: **VoiceTerm**
- Product thesis: This is the product thesis for the governance stack in this repository.
Absorb these four commitments before engaging with SOP, guard, routing,
or plan detail — they explain why the process exists.

This repo builds a portable AI governance platform proven through one
production client (VoiceTerm, a Rust voice-first terminal overlay for AI
CLIs). The product thesis is that executable local control — guards,
probes, typed actions, deterministic policy resolution — is what makes
AI-assisted engineering reliable, not prompt instructions alone.

**Mission**: Ship a reusable governance stack that any repo can adopt by
installing the platform and selecting a repo pack, without forking
VoiceTerm-specific code.

**Proof obligation**: Every claim about quality, safety, or process
compliance must be backed by a repo-owned executable artifact (guard
script, probe, typed action, CI workflow) that produces the same result
regardless of which AI model or operator runs it. Prompt-only governance
is not accepted as proof.

**Platform boundaries**: VoiceTerm is one client of the platform; portable
governance layers must not hardcode repo names, bridge paths, plan doc
locations, or product-specific defaults. Repo-local assumptions belong in
the repo pack, not in the platform core. MCP servers, operator consoles,
mobile surfaces, and overlay/TUI adapters are clients, not authority.

**Current priority**: Harden the governance stack for multi-repo adoption —
remove VoiceTerm-local assumptions from portable layers, stabilize the
typed contract surface (ProjectGovernance, StartupContext, ReviewState,
TypedAction → ActionResult → RunRecord), and close the remaining probe
and guard gaps so the platform proves its own thesis before external
adopters arrive.
- Remote: `https://github.com/jguida941/voiceterm.git`
- Default branch: `master`
- Current branch: `feature/governance-quality-sweep`
- HEAD SHA: `a60f14703ea9f69a84217155260012faef69d40b`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-09T09:00:03-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 13
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `published_remote` (post_push_bundle_failed)
- publication_backlog: none

### Reviewer runtime
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `single_agent`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **Master Plan (Active, Unified)**
- plan path: `dev/active/MASTER_PLAN.md`
- active MP scope: all active MP execution state
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `a60f14703ea9`

- commits: 25
- files changed: 174
- insertions: +12750
- deletions: -4355
- bundle classes touched: tooling, docs
- authority surfaces touched: 27 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `a60f1470` | Refresh external review snapshot for 69317302 | 1 | +52/-49 | tooling |  |
| 2 | `69317302` | fix: support coderabbit gate script imports | 3 | +82/-65 | tooling |  |
| 3 | `bc1a40ec` | Refresh external review snapshot for 013e15f6 | 1 | +63/-66 | tooling |  |
| 4 | `013e15f6` | fix: defer coderabbit gates until publish | 11 | +380/-178 | tooling |  |
| 5 | `46de6f81` | Refresh external review snapshot for 4c8aeb5b | 1 | +63/-70 | tooling |  |
| 6 | `4c8aeb5b` | chore: route release checks and review commands | 13 | +285/-61 | tooling |  |
| 7 | `a3fd3393` | Refresh external review snapshot for 38535f77 | 1 | +63/-62 | tooling |  |
| 8 | `38535f77` | chore: wire mutation bypass guard into shared lanes | 14 | +146/-63 | tooling |  |
| 9 | `0a194dfe` | Refresh external review snapshot for a547a2be | 1 | +59/-65 | tooling |  |
| 10 | `a547a2be` | refactor: move path audit behind compatibility shim | 9 | +528/-417 | tooling |  |
| 11 | `d094550c` | chore: register mutation guard and unify bootstrap catalog | 27 | +1108/-432 | tooling |  |
| 12 | `dacb1a26` | Refresh external review snapshot for 67ec68f7 | 1 | +52/-51 | tooling |  |
| 13 | `67ec68f7` | test: pin single-agent interaction mode resolution | 3 | +83/-65 | tooling |  |
| 14 | `1c70b2c5` | checkpoint: capture governance and review-channel batch | 27 | +976/-194 | tooling |  |
| 15 | `47d483b4` | Harden governed push and typed review-state reads | 89 | +4035/-993 | tooling |  |
| 16 | `6eb4945b` | Refresh external review snapshot for 73908286 | 1 | +63/-95 | tooling |  |
| 17 | `73908286` | docs: align graph-backed convergence plan | 6 | +510/-86 | tooling |  |
| 18 | `516e839c` | Refresh external review snapshot for c1a1ee28 | 1 | +96/-69 | tooling |  |
| 19 | `c1a1ee28` | Advance typed authority convergence across mutation and con… | 59 | +3285/-956 | tooling |  |
| 20 | `1c74c07f` | Refresh external review snapshot for f294de63 | 1 | +68/-59 | tooling |  |
| 21 | `f294de63` | Operator-directed commit+push: F1 parity flake fix + bridge… | 5 | +116/-41 | tooling |  |
| 22 | `ed23ac62` | LIVE_RUN: Q61 typed state lies about PID liveness + Q62 err… | 2 | +147/-54 | tooling |  |
| 23 | `839ee400` | Refresh external review snapshot for 9109ae4e | 1 | +57/-53 | tooling |  |
| 24 | `9109ae4e` | Preserve Claude-CLI session 7 WIP before solo-Codex test | 4 | +179/-69 | tooling |  |
| 25 | `8330b1d9` | LIVE_RUN: Q58 autonomy-swarm discoverability + full system… | 2 | +254/-42 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `AGENTS.md` | docs | +65/-10 |
| `bridge.md` | docs | +44/-41 |
| `dev/active/MASTER_PLAN.md` | tooling | +172/-7 |
| `dev/active/ai_governance_platform.md` | tooling | +223/-1 |
| `dev/active/platform_authority_loop.md` | tooling | +236/-2 |
| `dev/active/portable_code_governance.md` | tooling | +86/-2 |
| `dev/active/remote_commit_pipeline.md` | tooling | +175/-22 |
| `dev/active/remote_control_runtime.md` | tooling | +222/-27 |
| `dev/active/review_channel.md` | tooling | +9/-0 |
| `dev/active/review_probes.md` | tooling | +40/-1 |
| `dev/audits/AUTOMATION_DEBT_REGISTER.md` | tooling | +1/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +307/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1488/-1448 |
| `dev/config/git_hooks/pre-push-governed-push.sh` | tooling | +32/-0 |
| `dev/config/quality_presets/portable_python.json` | tooling | +1/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +33/-9 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +219/-1 |
| `dev/scripts/README.md` | tooling | +46/-12 |
| `dev/scripts/checks/check_architecture_surface_sync.py` | tooling | +19/-1 |
| `dev/scripts/checks/check_mutation_bypass_graph_closure.py` | tooling | +12/-0 |
| `dev/scripts/checks/coderabbit_gate_core.py` | tooling | +71/-90 |
| `dev/scripts/checks/coderabbit_gate_core/__init__.py` | tooling | +6/-37 |
| `dev/scripts/checks/coderabbit_gate_support.py` | tooling | +181/-0 |
| `dev/scripts/checks/mutation_bypass_graph_closure/__init__.py` | tooling | +2/-0 |
| `dev/scripts/checks/mutation_bypass_graph_closure/command.py` | tooling | +105/-0 |
| `dev/scripts/checks/startup_authority_contract/command.py` | tooling | +8/-0 |
| `dev/scripts/checks/startup_authority_contract/runtime_checks.py` | tooling | +12/-13 |
| `dev/scripts/checks/tandem_consistency/report.py` | tooling | +19/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/check/__init__.py` | tooling | +30/-2 |
| `dev/scripts/devctl/commands/check/process_sweep.py` | tooling | +50/-2 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +74/-56 |
| `dev/scripts/devctl/commands/dashboard_builders.py` | tooling | +56/-153 |
| `dev/scripts/devctl/commands/dashboard_people.py` | tooling | +113/-0 |
| `dev/scripts/devctl/commands/dashboard_render/__init__.py` | tooling | +9/-3 |
| `dev/scripts/devctl/commands/dashboard_render/control_plane.py` | tooling | +103/-0 |
| `dev/scripts/devctl/commands/dashboard_typed_state.py` | tooling | +5/-7 |
| `dev/scripts/devctl/commands/discover/__init__.py` | tooling | +5/-2 |
| _134 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 121
- open: 39
- fixed: 68
- false positives: 0

Recent findings:
- `agent_checkpoint_contract_ignorance` — `dev/scripts/devctl/review_channel/bridge_sanitize.py` (n/a, verdict=`confirmed_issue`)
- `claude_uses_osascript_not_typed_system` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `push_invalidation_head_equality` — `dev/scripts/devctl/review_channel/push_state.py` (n/a, verdict=`confirmed_issue`)
- `reviewer_truth_distributed_no_owner` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `startup_surface_tokens_unpopulated` — `dev/scripts/devctl/runtime/startup_context.py` (n/a, verdict=`confirmed_issue`)
- `terminal_window_id_not_captured` — `dev/scripts/devctl/review_channel/terminal_app.py` (n/a, verdict=`confirmed_issue`)
- `bridge_projection_drops_operator_direction` — `dev/scripts/devctl/review_channel/bridge_projection_state.py` (n/a, verdict=`confirmed_issue`)
- `bridge_still_active_gate_not_projection` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `need_review_channel_doctor_surface` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `reviewer_runtime_contract_needed` — `dev/scripts/devctl/platform/runtime_state_contract_rows.py` (n/a, verdict=`confirmed_issue`)

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
| `ActionResult` | `governance_runtime` | `n/a` | status |
| `ArtifactStore` | `governance_runtime` | `n/a` | root |
| `AutoModeState` | `governance_runtime` | `n/a` | phase |
| `CallerAuthorityPolicy` | `governance_runtime` | `n/a` | caller_id |
| `CheckResult` | `governance_runtime` | `n/a` | success |
| `ControlPlaneReadModel` | `governance_runtime` | `n/a` | push_eligible |
| `ControlState` | `governance_runtime` | `n/a` | approvals |
| `CoordinationSnapshot` | `governance_core` | `n/a` | current_slice |
| `DecisionPacket` | `governance_runtime` | `n/a` | decision_mode |
| `FailurePacket` | `governance_runtime` | `n/a` | runner |
| `Finding` | `governance_runtime` | `n/a` | check_id |
| `LocalServiceEndpoint` | `governance_runtime` | `n/a` | service_id |
| `ProviderAdapter` | `governance_adapters` | `n/a` | provider_id |
| `PushAuthorizationRecord` | `governance_runtime` | `n/a` | authorization_id |
| `RemoteCommitPipelineContract` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:RemoteCommitPipelineContract` | snapshot_id |
| `RepoPack` | `repo_packs` | `n/a` | pack_id |
| `ReviewCandidateRecord` | `governance_runtime` | `n/a` | candidate_id |
| `ReviewState` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewState` | snapshot_id |
| `ReviewerRuntimeContract` | `governance_runtime` | `n/a` | reviewer_mode |
| `RunRecord` | `governance_runtime` | `n/a` | run_id |
| `SessionCachePacket` | `governance_commands` | `n/a` | last_reviewed_sha |
| `TypedAction` | `governance_runtime` | `n/a` | action_id |
| `WorkflowAdapter` | `governance_adapters` | `n/a` | adapter_id |

### Key documents

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`

## 6. Reviewer hints — please verify

### Targeted hints

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_handler.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_checks.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_launch_control.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_field_access.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_phases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_push.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_models_core.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_render.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_push_decision.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_receipt.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_project_governance.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_receipt.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actions.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/governance/system_catalog_models.py`) — Commit d094550c changed dev/scripts/devctl/governance/system_catalog_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/context_graph/_codeshape_models.py`) — Commit 47d483b4 changed dev/scripts/devctl/context_graph/_codeshape_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/governance/push_state_models.py`) — Commit 47d483b4 changed dev/scripts/devctl/governance/push_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Commit 47d483b4 changed dev/scripts/devctl/tests/checks/test_startup_authority_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit c1a1ee28 changed dev/scripts/devctl/runtime/review_state_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`a60f1470`** — Refresh external review snapshot for 69317302
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`69317302`** — fix: support coderabbit gate script imports
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`bc1a40ec`** — Refresh external review snapshot for 013e15f6
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`013e15f6`** — fix: defer coderabbit gates until publish
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`46de6f81`** — Refresh external review snapshot for 4c8aeb5b
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`4c8aeb5b`** — chore: route release checks and review commands
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`a3fd3393`** — Refresh external review snapshot for 38535f77
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`38535f77`** — chore: wire mutation bypass guard into shared lanes
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`0a194dfe`** — Refresh external review snapshot for a547a2be
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`a547a2be`** — refactor: move path audit behind compatibility shim
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`d094550c`** — chore: register mutation guard and unify bootstrap catalog
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`dacb1a26`** — Refresh external review snapshot for 67ec68f7
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`67ec68f7`** — test: pin single-agent interaction mode resolution
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`1c70b2c5`** — checkpoint: capture governance and review-channel batch
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`47d483b4`** — Harden governed push and typed review-state reads
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`6eb4945b`** — Refresh external review snapshot for 73908286
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`73908286`** — docs: align graph-backed convergence plan
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`516e839c`** — Refresh external review snapshot for c1a1ee28
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`c1a1ee28`** — Advance typed authority convergence across mutation and control-plane
  - evolution: Fact: the governed push lane exposed a second publication-honesty gap after remote publication was already recorded. Preflight correctly resolved a branch-aware `since_ref`, but the post-push bundle still fell back to t…
- **`1c74c07f`** — Refresh external review snapshot for f294de63
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`f294de63` | markers: F1** — Operator-directed commit+push: F1 parity flake fix + bridge state + 4hr session unblock
  - Claude-CLI (session 9, PID 89248) authored F1 parity flake fix on
  - instruction revision 7f94c6cae1a6 from Codex:
  - - dev/scripts/devctl/runtime/startup_context.py
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`ed23ac62`** — LIVE_RUN: Q61 typed state lies about PID liveness + Q62 error system too coarse
  - Operator directly caught two compound findings while reviewing the
  - dashboard data:
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`839ee400`** — Refresh external review snapshot for 9109ae4e
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`9109ae4e`** — Preserve Claude-CLI session 7 WIP before solo-Codex test
  - Session 7 reached 19 min before Codex (PID 31108) died; Claude-CLI
  - (PID 31148) remained productive in hybrid_claude_only mode, writing
  - the F1 continuation:
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`8330b1d9`** — LIVE_RUN: Q58 autonomy-swarm discoverability + full system test plan (6 tests)
  - Operator asked 'what is the best way to test all of this system and
  - make sure it is fully connected?' — and mentioned 'saved cards for
  - this.' The saved-cards answer is devctl autonomy-swarm, a
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
### Active MP scope (from MASTER_PLAN.md)

- `dev/active/devctl_reporting_upgrade.md` is the phased `devctl` reporting/CIHub specification, but not a separate execution tracker; implementation tasks stay in this file under `MP-297..MP-300`, `MP-303`, `MP-306`, `MP…
- `dev/active/autonomous_control_plane.md` is the autonomous loop + mobile control-plane execution spec; implementation tasks stay in this file under `MP-325..MP-338, MP-340`.
- `dev/active/loop_chat_bridge.md` is the loop artifact-to-chat suggestion coordination runbook; execution evidence and operator handoffs for this path stay there under `MP-338`.
- `dev/active/naming_api_cohesion.md` is the naming/API cohesion execution spec; implementation tasks stay in this file under `MP-267`.
- `dev/active/ide_provider_modularization.md` is the IDE/provider adapter modularization execution spec; implementation tasks stay in this file under `MP-346`, `MP-354`.
- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/ralph_guardrail_control_plane.md` is the Ralph guardrail control plane execution spec; implementation tasks stay in this file under `MP-360..MP-367`.
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- architecture plan for the extracted AI-governance system under `MP-377`.

## 8. Known gaps and open items

- open governance findings: 39

### Startup advisories
- checkpoint_before_continue: staged_index_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/review_channel/bridge_sanitize.py`): agent_checkpoint_contract_ignorance: 
- **governance_open** (`dev/scripts/devctl/review_channel/state.py`): claude_uses_osascript_not_typed_system: 
- **governance_open** (`dev/scripts/devctl/review_channel/push_state.py`): push_invalidation_head_equality: 
- **governance_open** (`dev/scripts/devctl/review_channel/state.py`): reviewer_truth_distributed_no_owner: 
- **governance_open** (`dev/scripts/devctl/runtime/startup_context.py`): startup_surface_tokens_unpopulated: 
- **governance_open** (`dev/scripts/devctl/review_channel/terminal_app.py`): terminal_window_id_not_captured: 
- **governance_open** (`dev/scripts/devctl/review_channel/bridge_projection_state.py`): bridge_projection_drops_operator_direction: 
- **governance_open** (`dev/scripts/devctl/review_channel/state.py`): bridge_still_active_gate_not_projection: 

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-c5bd9693ad9c` binds this file to HEAD `a60f14703ea9`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
