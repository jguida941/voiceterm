# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `8a361a428666` — Refresh external review snapshot for f510da77
- Tree hash: `75d4020f9377`
- Generation stamp: `snap-fc07b1e229bd`
- Generated at (UTC): 2026-05-02T19:50:47Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 43 files, +3957/-1496
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
- HEAD SHA: `8a361a428666c39a022fa6127c8ef96ad4d35320`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-02T15:18:40-04:00

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
- current_push_authorization: `push-auth-20260502T191754786452Z` (valid=False)
- authorized_head_commit: `8a361a428666c39a022fa6127c8ef96ad4d35320`
- approved_target_identity: `tree-receipt-20260502T191754786452Z:80514f8bcec194b235e49d003497f5f26a62e105`
- publication_backlog: urgent
- publication_guidance: 24 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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

Range: last 24 commits ending at `8a361a428666`

- commits: 24
- files changed: 43
- insertions: +3957
- deletions: -1496
- bundle classes touched: docs, tooling
- authority surfaces touched: 4 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `8a361a42` | Refresh external review snapshot for f510da77 | 2 | +65/-69 | docs |  |
| 2 | `f510da77` | Fix empty develop packet attention summary | 11 | +160/-83 | tooling |  |
| 3 | `5908bcd9` | Refresh external review snapshot for a2c85e4a | 2 | +47/-47 | docs |  |
| 4 | `a2c85e4a` | Refresh external review snapshot for 4baabf40 | 1 | +53/-50 | tooling |  |
| 5 | `4baabf40` | Refresh policy-owned generated surfaces for 2cc4bd10 | 1 | +1/-1 | docs |  |
| 6 | `2cc4bd10` | Refresh external review snapshot for 7a3579b1 | 2 | +66/-64 | docs |  |
| 7 | `7a3579b1` | Persist launcher discipline bypass receipts | 8 | +452/-119 | tooling |  |
| 8 | `3ff41ec7` | Refresh external review snapshot for 117ea0d3 | 2 | +58/-58 | docs |  |
| 9 | `117ea0d3` | Preserve single-agent topology mode | 2 | +101/-135 | tooling |  |
| 10 | `625580af` | Refresh policy-owned generated surfaces for c3adea3a | 1 | +1/-1 | docs |  |
| 11 | `c3adea3a` | Refresh external review snapshot for ff9988fe | 2 | +57/-54 | docs |  |
| 12 | `ff9988fe` | Add failure packet router | 3 | +467/-57 | tooling |  |
| 13 | `11ede1db` | Refresh external review snapshot for 492a2f37 | 2 | +64/-78 | docs |  |
| 14 | `492a2f37` | drift before reviewer launch | 4 | +57/-49 | tooling |  |
| 15 | `be1a3a04` | Refresh external review snapshot for be2c47c0 | 2 | +58/-59 | docs |  |
| 16 | `be2c47c0` | Refresh managed projection surfaces (terminal-app launch pr… | 4 | +56/-51 | tooling |  |
| 17 | `dfeb010d` | Refresh external review snapshot for 007b574f | 2 | +59/-60 | docs |  |
| 18 | `007b574f` | Refresh managed projection surfaces (single_agent launch pr… | 4 | +60/-56 | tooling |  |
| 19 | `3b643953` | Refresh managed projection surfaces (post-9537766e follow-u… | 3 | +61/-54 | tooling |  |
| 20 | `a8a150d1` | Refresh external review snapshot for 9537766e | 2 | +60/-59 | docs |  |
| 21 | `9537766e` | Refresh managed projection surfaces (post-7f4b5bf4 follow-u… | 3 | +61/-56 | tooling |  |
| 22 | `08d33a43` | Refresh policy-owned generated surfaces for 4fc6a797 | 1 | +1/-1 | docs |  |
| 23 | `4fc6a797` | Refresh external review snapshot for 7f4b5bf4 | 2 | +68/-64 | docs |  |
| 24 | `7f4b5bf4` | Wake-binding slice + auto-dispatcher prep refactor (T22AN-C… | 29 | +1824/-171 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +1/-0 |
| `bridge.md` | docs | +52/-54 |
| `dev/active/MASTER_PLAN.md` | tooling | +21/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +4/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1253/-1296 |
| `dev/guides/DEVELOPMENT.md` | docs | +4/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +3/-3 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +92/-1 |
| `dev/scripts/README.md` | tooling | +39/-2 |
| `dev/scripts/devctl/commands/development/actor_resolution.py` | tooling | +52/-4 |
| `dev/scripts/devctl/commands/development/models.py` | tooling | +6/-1 |
| `dev/scripts/devctl/commands/development/next_slice.py` | tooling | +17/-3 |
| `dev/scripts/devctl/commands/development/packet_attention.py` | tooling | +101/-6 |
| `dev/scripts/devctl/commands/development/render.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/review_channel/_recover.py` | tooling | +14/-2 |
| `dev/scripts/devctl/commands/review_channel/bridge_handler.py` | tooling | +10/-2 |
| `dev/scripts/devctl/commands/review_channel/bridge_launch_control.py` | tooling | +9/-2 |
| `dev/scripts/devctl/commands/review_channel/bridge_launch_headless.py` | tooling | +14/-0 |
| `dev/scripts/devctl/commands/review_channel/event_post_wake.py` | tooling | +39/-18 |
| `dev/scripts/devctl/commands/review_channel/launcher_discipline.py` | tooling | +68/-10 |
| `dev/scripts/devctl/commands/review_channel/launcher_discipline_receipts.py` | tooling | +81/-0 |
| `dev/scripts/devctl/commands/review_channel/wake_receipt_persistence.py` | tooling | +168/-0 |
| `dev/scripts/devctl/review_channel/agent_wake_dispatch.py` | tooling | +211/-0 |
| `dev/scripts/devctl/review_channel/collaboration_session_coordination.py` | tooling | +10/-8 |
| `dev/scripts/devctl/review_channel/event_models.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/event_packet_rows.py` | tooling | +23/-0 |
| `dev/scripts/devctl/review_channel/event_reducer.py` | tooling | +2/-0 |
| `dev/scripts/devctl/review_channel/event_render.py` | tooling | +52/-0 |
| `dev/scripts/devctl/review_channel/failure_packet_router.py` | tooling | +212/-0 |
| `dev/scripts/devctl/review_channel/follow_controller.py` | tooling | +24/-52 |
| `dev/scripts/devctl/review_channel/headless_delegate.py` | tooling | +69/-0 |
| `dev/scripts/devctl/review_channel/recover_support.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/reviewer_follow_guard.py` | tooling | +58/-28 |
| `dev/scripts/devctl/review_channel/wake_receipt_models.py` | tooling | +102/-0 |
| `dev/scripts/devctl/tests/commands/test_development_command.py` | tooling | +217/-0 |
| `dev/scripts/devctl/tests/review_channel/test_event_inbox_scoped_queue.py` | tooling | +47/-0 |
| `dev/scripts/devctl/tests/review_channel/test_event_post_wake.py` | tooling | +161/-4 |
| `dev/scripts/devctl/tests/review_channel/test_event_reducer_state.py` | tooling | +97/-0 |
| `dev/scripts/devctl/tests/review_channel/test_event_render_typed_sections.py` | tooling | +62/-0 |
| `dev/scripts/devctl/tests/review_channel/test_failure_packet_router.py` | tooling | +204/-0 |
| _3 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_handler.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_launch_control.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_launch_headless.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit 7f4b5bf4 changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/wake_receipt_models.py`) — Commit 7f4b5bf4 changed dev/scripts/devctl/review_channel/wake_receipt_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`8a361a42`** — Refresh external review snapshot for f510da77
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`f510da77`** — Fix empty develop packet attention summary
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`5908bcd9`** — Refresh external review snapshot for a2c85e4a
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`a2c85e4a`** — Refresh external review snapshot for 4baabf40
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`4baabf40`** — Refresh policy-owned generated surfaces for 2cc4bd10
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`2cc4bd10`** — Refresh external review snapshot for 7a3579b1
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`7a3579b1`** — Persist launcher discipline bypass receipts
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`3ff41ec7`** — Refresh external review snapshot for 117ea0d3
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`117ea0d3`** — Preserve single-agent topology mode
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`625580af`** — Refresh policy-owned generated surfaces for c3adea3a
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`c3adea3a`** — Refresh external review snapshot for ff9988fe
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`ff9988fe`** — Add failure packet router
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`11ede1db`** — Refresh external review snapshot for 492a2f37
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`492a2f37`** — drift before reviewer launch
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`be1a3a04`** — Refresh external review snapshot for be2c47c0
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`be2c47c0` | MPs: MP-377** — Refresh managed projection surfaces (terminal-app launch prep)
  - Anchors: section:MP-377
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`dfeb010d`** — Refresh external review snapshot for 007b574f
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
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
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`9537766e` | MPs: MP-377** — Refresh managed projection surfaces (post-7f4b5bf4 follow-up)
  - Auto-regenerated after the wake-binding slice + auto-dispatcher prep
  - refactor commit. Per startup-authority typed gate
  - recommended_action=commit_before_push, committing these projection
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`08d33a43`** — Refresh policy-owned generated surfaces for 4fc6a797
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`4fc6a797`** — Refresh external review snapshot for 7f4b5bf4
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`7f4b5bf4` | MPs: MP-377** — Wake-binding slice + auto-dispatcher prep refactor (T22AN-C/F + plan revision r2 prep)
  - Operator-authorized scope: 'commit and push the wake-binding slice from the
  - dashboard' (2026-05-02T14:35Z) + 'Codex reviews and you code' role flip.
  - plan: `dev/active/ai_governance_platform.md`
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-fc07b1e229bd` binds this file to HEAD `8a361a428666`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
