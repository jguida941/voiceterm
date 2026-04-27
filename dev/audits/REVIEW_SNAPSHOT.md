# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `2193afad28ba` — Plan 4.1 Slice A: PlatformFindingIngest default report-only + register 3 orphan contracts + ADR-019 (rev_pkt_1997; closes ADR-010; supersedes rev_pkt_1994)
- Tree hash: `86fe3b8cc822`
- Generation stamp: `snap-1990928924ad`
- Generated at (UTC): 2026-04-27T03:55:53Z
- Push decision: `await_review` — checkpoint_required
- Reviewer mode: `active_dual_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 51 files, +5069/-1655
- Governance findings: 118 open / 88 fixed / 220 total
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
- HEAD SHA: `2193afad28bac1d3a133715519c94620d78eca04`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-26T23:55:42-04:00

## 2. Governance state

### Push decision
- action: `await_review`
- reason: checkpoint_required
- push_eligible_now: False
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `post_push_green` (push_completed)
- publication_backlog: queued
- publication_guidance: 1 local commit(s) waiting for governed push once review is accepted.

### Reviewer runtime
- reviewer_mode: `active_dual_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `remote_control`
- implementation_blocked: yes — checkpoint_required

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `repair_reviewer_loop` — checkpoint_required

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `2193afad28ba`

- commits: 24
- files changed: 51
- insertions: +5069
- deletions: -1655
- bundle classes touched: docs, tooling
- authority surfaces touched: 12 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `2193afad` | Plan 4.1 Slice A: PlatformFindingIngest default report-only… | 14 | +555/-128 | tooling |  |
| 2 | `8c49ff54` | Refresh external review snapshot for 8b21a43e | 2 | +61/-61 | docs |  |
| 3 | `8b21a43e` | Refresh external review snapshot for 748fb4d8 | 1 | +50/-47 | tooling |  |
| 4 | `748fb4d8` | Refresh external review snapshot for f4f7b4e0 | 2 | +74/-79 | docs |  |
| 5 | `f4f7b4e0` | Add render-surfaces auto-handle as first-class push preflig… | 20 | +972/-239 | tooling |  |
| 6 | `c43aad75` | Refresh external review snapshot for a941f874 | 2 | +50/-50 | docs |  |
| 7 | `a941f874` | Refresh external review snapshot for c691f08f | 2 | +53/-50 | docs |  |
| 8 | `c691f08f` | Refresh external review snapshot for 74f06e13 | 2 | +93/-81 | docs |  |
| 9 | `74f06e13` | Combine push pipeline phase split + non-destructive push-fa… | 31 | +1506/-134 | tooling |  |
| 10 | `64ac3101` | Fix governed commit attention refresh — auto-refresh startu… | 11 | +409/-96 | tooling |  |
| 11 | `73121da5` | Refresh external review snapshot for e9dd172c | 2 | +53/-54 | docs |  |
| 12 | `e9dd172c` | Refresh external review snapshot for 0c4aca39 | 1 | +4/-4 | docs |  |
| 13 | `0c4aca39` | Refresh external review snapshot for 3a4504a2 | 2 | +50/-50 | docs |  |
| 14 | `3a4504a2` | Refresh external review snapshot for 82e5fb81 | 2 | +52/-49 | docs |  |
| 15 | `82e5fb81` | Refresh external review snapshot for 7b23aced | 2 | +65/-74 | docs |  |
| 16 | `7b23aced` | Extend managed-receipt-chain classifier to SystemPicture fr… | 5 | +236/-64 | tooling |  |
| 17 | `1d0076e0` | Refresh external review snapshot for b3b8e523 | 2 | +46/-55 | docs |  |
| 18 | `b3b8e523` | Refresh external review snapshot for cf5cd0db | 1 | +3/-3 | docs |  |
| 19 | `cf5cd0db` | Refresh external review snapshot for 32864af3 | 2 | +42/-42 | docs |  |
| 20 | `32864af3` | Refresh external review snapshot for 2e1fe033 | 2 | +55/-52 | docs |  |
| 21 | `2e1fe033` | Refresh external review snapshot for 1109ff46 | 2 | +73/-74 | docs |  |
| 22 | `1109ff46` | Extend receipt-chain semantics to snapshot freshness gate +… | 15 | +514/-115 | tooling |  |
| 23 | `8369fea6` | Refresh external review snapshot for 36ba30c7 | 2 | +50/-51 | docs |  |
| 24 | `36ba30c7` | Refresh external review snapshot for 992d1514 | 1 | +3/-3 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +28/-17 |
| `README.md` | docs | +1/-0 |
| `bridge.md` | docs | +115/-115 |
| `dev/active/MASTER_PLAN.md` | tooling | +45/-9 |
| `dev/active/ai_governance_platform.md` | tooling | +62/-15 |
| `dev/active/remote_commit_pipeline.md` | tooling | +4/-3 |
| `dev/audits/AUTOMATION_DEBT_REGISTER.md` | tooling | +5/-3 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1144/-1136 |
| `dev/guides/DEVELOPMENT.md` | docs | +31/-15 |
| `dev/guides/SYSTEM_MAP.md` | docs | +6/-6 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +135/-2 |
| `dev/scripts/README.md` | tooling | +41/-29 |
| `dev/scripts/checks/review_snapshot_freshness/command.py` | tooling | +56/-20 |
| `dev/scripts/devctl/commands/vcs/commit_pipeline_blocking.py` | tooling | +86/-0 |
| `dev/scripts/devctl/commands/vcs/commit_preflight_validators.py` | tooling | +32/-1 |
| `dev/scripts/devctl/commands/vcs/commit_visibility.py` | tooling | +12/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor.py` | tooling | +5/-8 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py` | tooling | +50/-39 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py` | tooling | +126/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_push_result.py` | tooling | +125/-3 |
| `dev/scripts/devctl/commands/vcs/governed_executor_stage_attention.py` | tooling | +33/-0 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +14/-15 |
| `dev/scripts/devctl/commands/vcs/push_flow.py` | tooling | +4/-4 |
| `dev/scripts/devctl/commands/vcs/push_pipeline_state_sync.py` | tooling | +37/-8 |
| `dev/scripts/devctl/commands/vcs/push_preflight_commit.py` | tooling | +179/-3 |
| `dev/scripts/devctl/commands/vcs/push_preflight_projection.py` | tooling | +191/-119 |
| `dev/scripts/devctl/commands/vcs/push_projection_receipt.py` | tooling | +75/-24 |
| `dev/scripts/devctl/commands/vcs/push_projection_runtime_refresh.py` | tooling | +115/-0 |
| `dev/scripts/devctl/commands/vcs/push_render_surface_sync.py` | tooling | +143/-0 |
| `dev/scripts/devctl/commands/vcs/push_report.py` | tooling | +13/-0 |
| `dev/scripts/devctl/commands/vcs/push_snapshot.py` | tooling | +10/-0 |
| `dev/scripts/devctl/commands/vcs/push_worktree_changes.py` | tooling | +10/-0 |
| `dev/scripts/devctl/commands/vcs/startup_context_refresh.py` | tooling | +79/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows.py` | tooling | +144/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_pipeline.py` | tooling | +10/-0 |
| `dev/scripts/devctl/platform/system_picture.py` | tooling | +46/-2 |
| `dev/scripts/devctl/platform/system_picture_models.py` | tooling | +38/-0 |
| `dev/scripts/devctl/platform/system_picture_sections.py` | tooling | +17/-8 |
| `dev/scripts/devctl/runtime/dogfood_render.py` | tooling | +72/-1 |
| `dev/scripts/devctl/runtime/platform_finding_ingest.py` | tooling | +56/-6 |
| _11 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 220
- open: 118
- fixed: 88
- false positives: 0

Recent findings:
- `authority_snapshot_3_fields_missing` — `dev/scripts/devctl/runtime/startup_context.py` (n/a, verdict=`fixed`)
- `dogfood.command.startup-context` — `dev/scripts/devctl/commands/governance/startup_context.py` (n/a, verdict=`confirmed_issue`)
- `agents_md_dual_purpose_conflict` — `AGENTS.md` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.dogfood` — `dev/scripts/devctl/commands/reporting/dogfood.py` (n/a, verdict=`fixed`)
- `dogfood.code_shape_push_regression` — `dev/scripts/devctl/commands/vcs/push.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.review_channel_post_timeout` — `dev/scripts/devctl/commands/review_channel/event_handler.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.review_channel_post_timeout` — `dev/scripts/devctl/review_channel/event_projection_queue.py` (n/a, verdict=`fixed`)
- `portability_python_310` — `dev/scripts/devctl/runtime/worktree_orphan_inventory_support.py` (p0, verdict=`confirmed_issue`)
- `bridge_content_loss_on_rollover` — `dev/scripts/devctl/review_channel/projections` (class1, verdict=`confirmed_issue`)
- `actor_template_missing` — `dev/scripts/devctl/runtime/review_packet_inbox.py` (medium, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_push_result.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_stage_attention.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/review_snapshot_freshness/command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_check_review_snapshot_freshness.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit 2193afad changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Commit 74f06e13 changed dev/scripts/devctl/runtime/remote_commit_pipeline_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/system_picture_models.py`) — Commit 7b23aced changed dev/scripts/devctl/platform/system_picture_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`2193afad`** — Plan 4.1 Slice A: PlatformFindingIngest default report-only + register 3 orphan contracts + ADR-019 (rev_pkt_1997; closes ADR-010; supersedes rev_pkt_1994)
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`8c49ff54`** — Refresh external review snapshot for 8b21a43e
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`8b21a43e`** — Refresh external review snapshot for 748fb4d8
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`748fb4d8`** — Refresh external review snapshot for f4f7b4e0
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`f4f7b4e0`** — Add render-surfaces auto-handle as first-class push preflight phase + generated-surface managed receipts (rev_pkt_1988; closes rev_pkt_1983; generalizes pattern across 9 tracked render targets)
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`c43aad75`** — Refresh external review snapshot for a941f874
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`a941f874`** — Refresh external review snapshot for c691f08f
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`c691f08f`** — Refresh external review snapshot for 74f06e13
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`74f06e13`** — Combine push pipeline phase split + non-destructive push-failure auto-transition + advisory-aware startup-context refresh (rev_pkt_1980; closes rev_pkt_1971 + rev_pkt_1974 + rev_pkt_1978)
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`64ac3101`** — Fix governed commit attention refresh — auto-refresh startup receipt before stale-attention check (rev_pkt_1968; closes rev_pkt_1966)
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`73121da5`** — Refresh external review snapshot for e9dd172c
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`e9dd172c`** — Refresh external review snapshot for 0c4aca39
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`0c4aca39`** — Refresh external review snapshot for 3a4504a2
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`3a4504a2`** — Refresh external review snapshot for 82e5fb81
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`82e5fb81`** — Refresh external review snapshot for 7b23aced
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`7b23aced`** — Extend managed-receipt-chain classifier to SystemPicture freshness sections (rev_pkt_1962; closes rev_pkt_1960; final Slice 0 cascade residual)
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`1d0076e0`** — Refresh external review snapshot for b3b8e523
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`b3b8e523`** — Refresh external review snapshot for cf5cd0db
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`cf5cd0db`** — Refresh external review snapshot for 32864af3
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`32864af3`** — Refresh external review snapshot for 2e1fe033
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`2e1fe033`** — Refresh external review snapshot for 1109ff46
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`1109ff46`** — Extend receipt-chain semantics to snapshot freshness gate + block push auto-commit-repair on failed validation (rev_pkt_1957; closes rev_pkt_1955)
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`8369fea6`** — Refresh external review snapshot for 36ba30c7
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`36ba30c7`** — Refresh external review snapshot for 992d1514
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
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

- open governance findings: 118

### Startup advisories
- repair_reviewer_loop: checkpoint_required

### Stale warnings
- Cut a checkpoint before doing anything else.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/governance/startup_context.py`): dogfood.command.startup-context: 
- **governance_open** (`AGENTS.md`): agents_md_dual_purpose_conflict: 
- **governance_open** (`dev/scripts/devctl/commands/vcs/push.py`): dogfood.code_shape_push_regression: Push preflight bridge sync expanded push.py beyond the hard limit.
- **governance_open** (`dev/scripts/devctl/commands/review_channel/event_handler.py`): dogfood.review_channel_post_timeout: Timed out after 20s while posting review-channel --action post --kind action_request for the staged dogfood/governance handoff.
- **governance_open** (`dev/scripts/devctl/runtime/worktree_orphan_inventory_support.py`): portability_python_310: from datetime import UTC requires Python 3.11+; operator default python3 is pyenv 3.10.4; every devctl call crashes at import on operator shell. Regression from commit dc82fbf1 2026-04-22. Fix: from datetime import datetime, timezone + timezone.utc.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-1990928924ad` binds this file to HEAD `2193afad28ba`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
