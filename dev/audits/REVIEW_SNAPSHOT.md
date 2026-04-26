# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `2e1fe0334fcb` — Refresh external review snapshot for 1109ff46
- Tree hash: `e57f08883f53`
- Generation stamp: `snap-c38e2e3a4fd1`
- Generated at (UTC): 2026-04-26T20:52:56Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `active_dual_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 38 files, +2894/-1421
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
- HEAD SHA: `2e1fe0334fcb9644c319155ba0f6b06357b2dbbc`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-26T16:30:38-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: False
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (push_preflight_running)
- current_push_authorization: `push-auth-20260426T203014149636Z` (valid=True)
- authorized_head_commit: `2e1fe0334fcb9644c319155ba0f6b06357b2dbbc`
- approved_target_identity: `tree-receipt-20260426T203014149636Z:db14fdcc9369b91b40c916363532bd812da30bff`
- publication_backlog: urgent
- publication_guidance: 73 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `active_dual_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `remote_control`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `await_review` — review_pending_before_push

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `2e1fe0334fcb`

- commits: 24
- files changed: 38
- insertions: +2894
- deletions: -1421
- bundle classes touched: docs, tooling
- authority surfaces touched: 8 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `2e1fe033` | Refresh external review snapshot for 1109ff46 | 2 | +73/-74 | docs |  |
| 2 | `1109ff46` | Extend receipt-chain semantics to snapshot freshness gate +… | 15 | +514/-115 | tooling |  |
| 3 | `8369fea6` | Refresh external review snapshot for 36ba30c7 | 2 | +50/-51 | docs |  |
| 4 | `36ba30c7` | Refresh external review snapshot for 992d1514 | 1 | +3/-3 | docs |  |
| 5 | `992d1514` | Refresh external review snapshot for 4439f76e | 2 | +49/-46 | docs |  |
| 6 | `4439f76e` | Refresh external review snapshot for bbd8deaa | 2 | +78/-66 | docs |  |
| 7 | `bbd8deaa` | Fix governed-push receipt-chain authorization for managed b… | 20 | +867/-222 | tooling |  |
| 8 | `a63ca2ed` | Refresh external review snapshot for bc3ef241 | 1 | +2/-2 | docs |  |
| 9 | `bc3ef241` | Refresh external review snapshot for 4865ff7a | 2 | +42/-42 | docs |  |
| 10 | `4865ff7a` | Refresh external review snapshot for 6891dc56 | 2 | +42/-42 | docs |  |
| 11 | `6891dc56` | Refresh external review snapshot for 15d0ac55 | 2 | +47/-53 | docs |  |
| 12 | `15d0ac55` | Refresh external review snapshot for a1def993 | 1 | +4/-4 | docs |  |
| 13 | `a1def993` | Refresh external review snapshot for cf808b89 | 2 | +51/-48 | docs |  |
| 14 | `cf808b89` | Refresh external review snapshot for f0f06bbf | 1 | +3/-3 | docs |  |
| 15 | `f0f06bbf` | Refresh external review snapshot for e2cb0860 | 1 | +47/-44 | tooling |  |
| 16 | `e2cb0860` | Refresh external review snapshot for 4a127654 | 2 | +55/-57 | docs |  |
| 17 | `4a127654` | Refresh SYSTEM_MAP.md devctl file count after Slice 0 commit | 2 | +54/-69 | tooling |  |
| 18 | `17e823af` | Refresh external review snapshot for 5d64e13b | 2 | +51/-45 | docs |  |
| 19 | `5d64e13b` | Refresh external review snapshot for 083f2ece | 2 | +77/-63 | docs |  |
| 20 | `083f2ece` | Fix review-channel recovery authority deadlock | 15 | +397/-132 | tooling |  |
| 21 | `1f3b6c89` | Refresh external review snapshot for 572d9aa6 | 2 | +53/-50 | docs |  |
| 22 | `572d9aa6` | Refresh external review snapshot for c5f0be73 | 2 | +59/-59 | docs |  |
| 23 | `c5f0be73` | Slice 0 reviewer acceptance convergence fix per Plan 4.1 (r… | 4 | +222/-76 | tooling |  |
| 24 | `4837fbd7` | Refresh external review snapshot for 3ed07cd2 | 2 | +54/-55 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +24/-15 |
| `bridge.md` | docs | +115/-115 |
| `dev/active/MASTER_PLAN.md` | tooling | +18/-2 |
| `dev/active/ai_governance_platform.md` | tooling | +34/-3 |
| `dev/audits/AUTOMATION_DEBT_REGISTER.md` | tooling | +4/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1026/-1005 |
| `dev/guides/DEVELOPMENT.md` | docs | +6/-5 |
| `dev/guides/SYSTEM_MAP.md` | docs | +1/-1 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +29/-1 |
| `dev/scripts/README.md` | tooling | +21/-16 |
| `dev/scripts/checks/review_snapshot_freshness/command.py` | tooling | +56/-20 |
| `dev/scripts/devctl/commands/pipeline/head_movement.py` | tooling | +13/-3 |
| `dev/scripts/devctl/commands/review_channel/bridge_support.py` | tooling | +32/-0 |
| `dev/scripts/devctl/commands/review_channel/status_bridge_sync.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +31/-25 |
| `dev/scripts/devctl/commands/vcs/push_flow.py` | tooling | +20/-7 |
| `dev/scripts/devctl/commands/vcs/push_pipeline_state_sync.py` | tooling | +16/-6 |
| `dev/scripts/devctl/commands/vcs/push_preflight_projection.py` | tooling | +213/-6 |
| `dev/scripts/devctl/governance/push_state.py` | tooling | +29/-17 |
| `dev/scripts/devctl/governance/push_state_authorization.py` | tooling | +23/-11 |
| `dev/scripts/devctl/review_channel/attention_classify.py` | tooling | +2/-1 |
| `dev/scripts/devctl/review_channel/attention_recovery_projection.py` | tooling | +20/-0 |
| `dev/scripts/devctl/review_channel/bridge_projection_instruction.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/bridge_projection_metadata.py` | tooling | +15/-5 |
| `dev/scripts/devctl/review_channel/conductor_authority.py` | tooling | +46/-0 |
| `dev/scripts/devctl/review_channel/launch_truth.py` | tooling | +6/-10 |
| `dev/scripts/devctl/review_channel/recover_support.py` | tooling | +2/-1 |
| `dev/scripts/devctl/review_channel/recovery_decision.py` | tooling | +36/-49 |
| `dev/scripts/devctl/review_channel/reviewer_runtime_contract.py` | tooling | +34/-12 |
| `dev/scripts/devctl/runtime/push_authorization.py` | tooling | +30/-19 |
| `dev/scripts/devctl/runtime/review_snapshot_refresh.py` | tooling | +51/-4 |
| `dev/scripts/devctl/tests/checks/test_check_review_snapshot_freshness.py` | tooling | +128/-0 |
| `dev/scripts/devctl/tests/review_channel/test_bridge_render.py` | tooling | +32/-4 |
| `dev/scripts/devctl/tests/review_channel/test_recovery_assessment.py` | tooling | +59/-0 |
| `dev/scripts/devctl/tests/review_channel/test_review_channel.py` | tooling | +84/-0 |
| `dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py` | tooling | +123/-0 |
| `dev/scripts/devctl/tests/runtime/test_push_authorization.py` | tooling | +111/-5 |
| `dev/scripts/devctl/tests/vcs/test_push.py` | tooling | +401/-52 |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/review_snapshot_freshness/command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_check_review_snapshot_freshness.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_instruction.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_metadata.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Commit c5f0be73 changed dev/scripts/devctl/review_channel/reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py`) — Commit c5f0be73 changed dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`bc3ef241`** — Refresh external review snapshot for 4865ff7a
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`4865ff7a`** — Refresh external review snapshot for 6891dc56
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`6891dc56`** — Refresh external review snapshot for 15d0ac55
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`15d0ac55`** — Refresh external review snapshot for a1def993
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`a1def993`** — Refresh external review snapshot for cf808b89
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`cf808b89`** — Refresh external review snapshot for f0f06bbf
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`f0f06bbf`** — Refresh external review snapshot for e2cb0860
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`e2cb0860`** — Refresh external review snapshot for 4a127654
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`4a127654`** — Refresh SYSTEM_MAP.md devctl file count after Slice 0 commit
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`17e823af`** — Refresh external review snapshot for 5d64e13b
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`5d64e13b`** — Refresh external review snapshot for 083f2ece
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`083f2ece`** — Fix review-channel recovery authority deadlock
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`1f3b6c89`** — Refresh external review snapshot for 572d9aa6
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`572d9aa6`** — Refresh external review snapshot for c5f0be73
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`c5f0be73`** — Slice 0 reviewer acceptance convergence fix per Plan 4.1 (rev_pkt_1926)
  - Per Codex's typed handoff (rev_pkt_1926 stage_commit_pipeline) addressing
  - the post-7fb219fa publication blocker: bridge.md carried fresh
  - reviewer-checkpoint accepted/no-findings state, but typed
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`4837fbd7`** — Refresh external review snapshot for 3ed07cd2
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
- await_review: review_pending_before_push

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/active/MASTER_PLAN.md`): plan_authority_gap: 
- **governance_open** (`dev/scripts/devctl/review_channel/handoff.py`): bridge_metadata_parsed_as_authority: 
- **governance_open** (`dev/scripts/devctl/commands/governance/startup_context.py`): dogfood.command.startup-context: 
- **governance_open** (`AGENTS.md`): agents_md_dual_purpose_conflict: 
- **governance_open** (`dev/scripts/devctl/commands/vcs/push.py`): dogfood.code_shape_push_regression: Push preflight bridge sync expanded push.py beyond the hard limit.
- **governance_open** (`dev/scripts/devctl/commands/review_channel/event_handler.py`): dogfood.review_channel_post_timeout: Timed out after 20s while posting review-channel --action post --kind action_request for the staged dogfood/governance handoff.

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-c38e2e3a4fd1` binds this file to HEAD `2e1fe0334fcb`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
