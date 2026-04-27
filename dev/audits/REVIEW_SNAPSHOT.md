# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `f4f7b4e009a6` — Add render-surfaces auto-handle as first-class push preflight phase + generated-surface managed receipts (rev_pkt_1988; closes rev_pkt_1983; generalizes pattern across 9 tracked render targets)
- Tree hash: `5cb8f5d4364f`
- Generation stamp: `snap-876d670645f6`
- Generated at (UTC): 2026-04-27T02:37:57Z
- Push decision: `await_review` — checkpoint_required
- Reviewer mode: `active_dual_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 51 files, +5325/-1676
- Governance findings: 116 open / 88 fixed / 218 total
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
- HEAD SHA: `f4f7b4e009a626006f611dde33e30dfb067aa7fd`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-26T22:37:46-04:00

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
- latest_push_report_state: `published_remote` (post_push_bundle_pending)
- publication_backlog: urgent
- publication_guidance: 6 local commit(s) waiting for governed push once review is accepted.

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

Range: last 24 commits ending at `f4f7b4e009a6`

- commits: 24
- files changed: 51
- insertions: +5325
- deletions: -1676
- bundle classes touched: docs, tooling
- authority surfaces touched: 12 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `f4f7b4e0` | Add render-surfaces auto-handle as first-class push preflig… | 20 | +972/-239 | tooling |  |
| 2 | `c43aad75` | Refresh external review snapshot for a941f874 | 2 | +50/-50 | docs |  |
| 3 | `a941f874` | Refresh external review snapshot for c691f08f | 2 | +53/-50 | docs |  |
| 4 | `c691f08f` | Refresh external review snapshot for 74f06e13 | 2 | +93/-81 | docs |  |
| 5 | `74f06e13` | Combine push pipeline phase split + non-destructive push-fa… | 31 | +1506/-134 | tooling |  |
| 6 | `64ac3101` | Fix governed commit attention refresh — auto-refresh startu… | 11 | +409/-96 | tooling |  |
| 7 | `73121da5` | Refresh external review snapshot for e9dd172c | 2 | +53/-54 | docs |  |
| 8 | `e9dd172c` | Refresh external review snapshot for 0c4aca39 | 1 | +4/-4 | docs |  |
| 9 | `0c4aca39` | Refresh external review snapshot for 3a4504a2 | 2 | +50/-50 | docs |  |
| 10 | `3a4504a2` | Refresh external review snapshot for 82e5fb81 | 2 | +52/-49 | docs |  |
| 11 | `82e5fb81` | Refresh external review snapshot for 7b23aced | 2 | +65/-74 | docs |  |
| 12 | `7b23aced` | Extend managed-receipt-chain classifier to SystemPicture fr… | 5 | +236/-64 | tooling |  |
| 13 | `1d0076e0` | Refresh external review snapshot for b3b8e523 | 2 | +46/-55 | docs |  |
| 14 | `b3b8e523` | Refresh external review snapshot for cf5cd0db | 1 | +3/-3 | docs |  |
| 15 | `cf5cd0db` | Refresh external review snapshot for 32864af3 | 2 | +42/-42 | docs |  |
| 16 | `32864af3` | Refresh external review snapshot for 2e1fe033 | 2 | +55/-52 | docs |  |
| 17 | `2e1fe033` | Refresh external review snapshot for 1109ff46 | 2 | +73/-74 | docs |  |
| 18 | `1109ff46` | Extend receipt-chain semantics to snapshot freshness gate +… | 15 | +514/-115 | tooling |  |
| 19 | `8369fea6` | Refresh external review snapshot for 36ba30c7 | 2 | +50/-51 | docs |  |
| 20 | `36ba30c7` | Refresh external review snapshot for 992d1514 | 1 | +3/-3 | docs |  |
| 21 | `992d1514` | Refresh external review snapshot for 4439f76e | 2 | +49/-46 | docs |  |
| 22 | `4439f76e` | Refresh external review snapshot for bbd8deaa | 2 | +78/-66 | docs |  |
| 23 | `bbd8deaa` | Fix governed-push receipt-chain authorization for managed b… | 20 | +867/-222 | tooling |  |
| 24 | `a63ca2ed` | Refresh external review snapshot for bc3ef241 | 1 | +2/-2 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +36/-20 |
| `README.md` | docs | +1/-0 |
| `bridge.md` | docs | +118/-118 |
| `dev/active/MASTER_PLAN.md` | tooling | +40/-4 |
| `dev/active/ai_governance_platform.md` | tooling | +53/-8 |
| `dev/active/remote_commit_pipeline.md` | tooling | +4/-3 |
| `dev/audits/AUTOMATION_DEBT_REGISTER.md` | tooling | +5/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1074/-1048 |
| `dev/guides/DEVELOPMENT.md` | docs | +25/-12 |
| `dev/guides/SYSTEM_MAP.md` | docs | +1/-1 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +132/-2 |
| `dev/scripts/README.md` | tooling | +42/-27 |
| `dev/scripts/checks/review_snapshot_freshness/command.py` | tooling | +56/-20 |
| `dev/scripts/devctl/commands/pipeline/head_movement.py` | tooling | +13/-3 |
| `dev/scripts/devctl/commands/vcs/commit_pipeline_blocking.py` | tooling | +86/-0 |
| `dev/scripts/devctl/commands/vcs/commit_preflight_validators.py` | tooling | +32/-1 |
| `dev/scripts/devctl/commands/vcs/commit_visibility.py` | tooling | +12/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor.py` | tooling | +5/-8 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py` | tooling | +50/-39 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py` | tooling | +126/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_push_result.py` | tooling | +125/-3 |
| `dev/scripts/devctl/commands/vcs/governed_executor_stage_attention.py` | tooling | +33/-0 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +44/-39 |
| `dev/scripts/devctl/commands/vcs/push_flow.py` | tooling | +20/-7 |
| `dev/scripts/devctl/commands/vcs/push_pipeline_state_sync.py` | tooling | +53/-14 |
| `dev/scripts/devctl/commands/vcs/push_preflight_commit.py` | tooling | +179/-3 |
| `dev/scripts/devctl/commands/vcs/push_preflight_projection.py` | tooling | +309/-124 |
| `dev/scripts/devctl/commands/vcs/push_projection_receipt.py` | tooling | +75/-24 |
| `dev/scripts/devctl/commands/vcs/push_projection_runtime_refresh.py` | tooling | +115/-0 |
| `dev/scripts/devctl/commands/vcs/push_render_surface_sync.py` | tooling | +143/-0 |
| `dev/scripts/devctl/commands/vcs/push_report.py` | tooling | +13/-0 |
| `dev/scripts/devctl/commands/vcs/push_snapshot.py` | tooling | +10/-0 |
| `dev/scripts/devctl/commands/vcs/push_worktree_changes.py` | tooling | +10/-0 |
| `dev/scripts/devctl/commands/vcs/startup_context_refresh.py` | tooling | +79/-0 |
| `dev/scripts/devctl/governance/push_state.py` | tooling | +29/-17 |
| `dev/scripts/devctl/governance/push_state_authorization.py` | tooling | +23/-11 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_pipeline.py` | tooling | +10/-0 |
| `dev/scripts/devctl/platform/system_picture.py` | tooling | +46/-2 |
| `dev/scripts/devctl/platform/system_picture_models.py` | tooling | +38/-0 |
| `dev/scripts/devctl/platform/system_picture_sections.py` | tooling | +17/-8 |
| _11 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 218
- open: 116
- fixed: 88
- false positives: 0

Recent findings:
- `plan_authority_gap` — `dev/active/MASTER_PLAN.md` (n/a, verdict=`confirmed_issue`)
- `bridge_metadata_parsed_as_authority` — `dev/scripts/devctl/review_channel/handoff.py` (n/a, verdict=`confirmed_issue`)
- `authority_snapshot_3_fields_missing` — `dev/scripts/devctl/runtime/startup_context.py` (n/a, verdict=`fixed`)
- `dogfood.command.startup-context` — `dev/scripts/devctl/commands/governance/startup_context.py` (n/a, verdict=`confirmed_issue`)
- `agents_md_dual_purpose_conflict` — `AGENTS.md` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.dogfood` — `dev/scripts/devctl/commands/reporting/dogfood.py` (n/a, verdict=`fixed`)
- `dogfood.code_shape_push_regression` — `dev/scripts/devctl/commands/vcs/push.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.review_channel_post_timeout` — `dev/scripts/devctl/commands/review_channel/event_handler.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.review_channel_post_timeout` — `dev/scripts/devctl/review_channel/event_projection_queue.py` (n/a, verdict=`fixed`)
- `portability_python_310` — `dev/scripts/devctl/runtime/worktree_orphan_inventory_support.py` (p0, verdict=`confirmed_issue`)

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
- **`992d1514`** — Refresh external review snapshot for 4439f76e
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`4439f76e`** — Refresh external review snapshot for bbd8deaa
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`bbd8deaa`** — Fix governed-push receipt-chain authorization for managed bridge/ReviewSnapshot commits (rev_pkt_1951; closes rev_pkt_1947 Issue 1)
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`a63ca2ed`** — Refresh external review snapshot for bc3ef241
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

- open governance findings: 116

### Startup advisories
- repair_reviewer_loop: checkpoint_required

### Stale warnings
- Cut a checkpoint before doing anything else.

### Open gap rows
- **governance_open** (`dev/active/MASTER_PLAN.md`): plan_authority_gap: 
- **governance_open** (`dev/scripts/devctl/review_channel/handoff.py`): bridge_metadata_parsed_as_authority: 
- **governance_open** (`dev/scripts/devctl/commands/governance/startup_context.py`): dogfood.command.startup-context: 
- **governance_open** (`AGENTS.md`): agents_md_dual_purpose_conflict: 
- **governance_open** (`dev/scripts/devctl/commands/vcs/push.py`): dogfood.code_shape_push_regression: Push preflight bridge sync expanded push.py beyond the hard limit.
- **governance_open** (`dev/scripts/devctl/commands/review_channel/event_handler.py`): dogfood.review_channel_post_timeout: Timed out after 20s while posting review-channel --action post --kind action_request for the staged dogfood/governance handoff.

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-876d670645f6` binds this file to HEAD `f4f7b4e009a6`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
