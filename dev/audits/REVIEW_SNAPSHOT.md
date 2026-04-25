# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `5d1c0ccfe1f0` — Checkpoint actor-authority liveness slice (rev_pkt_1818)
- Tree hash: `b3be89a9ff6a`
- Generation stamp: `snap-150829e26338`
- Generated at (UTC): 2026-04-25T14:47:18Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `active_dual_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 105 files, +7022/-1992
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
- HEAD SHA: `5d1c0ccfe1f06d39d616c0b5ec184700ca613ad6`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-24T23:45:26-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 146
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: queued
- publication_guidance: 1 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `5d1c0ccfe1f0`

- commits: 24
- files changed: 105
- insertions: +7022
- deletions: -1992
- bundle classes touched: tooling, docs
- authority surfaces touched: 12 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `5d1c0ccf` | Checkpoint actor-authority liveness slice (rev_pkt_1818) | 15 | +1767/-60 | tooling |  |
| 2 | `30fb4c55` | Refresh external review snapshot for 75d4bf8f | 1 | +6/-6 | docs |  |
| 3 | `75d4bf8f` | Refresh external review snapshot for 71385e9d | 2 | +71/-73 | docs |  |
| 4 | `71385e9d` | Add inactivity-watchdog to conductor wrapper (path 1 fix) | 5 | +382/-163 | tooling |  |
| 5 | `442aa2c3` | Refresh external review snapshot for 61224a5a | 1 | +1/-1 | docs |  |
| 6 | `61224a5a` | Refresh external review snapshot for eafea93b | 2 | +78/-78 | docs |  |
| 7 | `eafea93b` | Fix codex portability findings: 3.10 datetime.UTC + venv in… | 9 | +133/-107 | tooling |  |
| 8 | `411cb262` | Refresh external review snapshot for 6432db5a | 1 | +6/-6 | docs |  |
| 9 | `6432db5a` | Refresh external review snapshot for a75d0d33 | 2 | +87/-85 | docs |  |
| 10 | `a75d0d33` | Refresh external review snapshot for af4a23b3 | 1 | +5/-5 | docs |  |
| 11 | `af4a23b3` | Refresh external review snapshot for c3229f22 | 1 | +10/-10 | docs |  |
| 12 | `c3229f22` | Slice 1+2 rev 12 + install-hooks fix + code-shape modulariz… | 30 | +1579/-311 | tooling |  |
| 13 | `9d6f1eb6` | Repair review surface bootstrap contracts | 10 | +165/-74 | tooling |  |
| 14 | `e66c68e3` | Refresh external review snapshot for 68dbe112 | 1 | +1/-1 | docs |  |
| 15 | `68dbe112` | Refresh external review snapshot for e7211799 | 2 | +64/-64 | docs |  |
| 16 | `e7211799` | chore(push): auto-commit preflight-generated changes | 11 | +202/-90 | tooling |  |
| 17 | `e3ebc4ef` | Refresh external review snapshot for 653beda0 | 1 | +3/-3 | docs |  |
| 18 | `653beda0` | chore(push): auto-commit preflight-generated changes | 1 | +79/-74 | tooling |  |
| 19 | `4ba95539` | Route remote-control staging handoffs | 28 | +1094/-439 | tooling |  |
| 20 | `cf61d131` | Refresh external review snapshot for ddafb608 | 1 | +1/-1 | docs |  |
| 21 | `ddafb608` | Refresh external review snapshot for 415674d0 | 2 | +66/-66 | docs |  |
| 22 | `415674d0` | Add managed projection receipt push cleanup | 14 | +500/-70 | tooling |  |
| 23 | `fd11a448` | Refresh external review snapshot for 0ec1b679 | 2 | +75/-70 | docs |  |
| 24 | `0ec1b679` | Classify managed bridge projection drift | 31 | +647/-135 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +16/-5 |
| `bridge.md` | docs | +68/-68 |
| `dev/active/MASTER_PLAN.md` | tooling | +56/-7 |
| `dev/active/ai_governance_platform.md` | tooling | +92/-9 |
| `dev/active/remote_commit_pipeline.md` | tooling | +13/-1 |
| `dev/active/remote_control_runtime.md` | tooling | +3/-2 |
| `dev/audits/AUTOMATION_DEBT_REGISTER.md` | tooling | +4/-4 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1048/-1035 |
| `dev/config/git_hooks/post-commit-review-snapshot.sh` | tooling | +18/-3 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +23/-8 |
| `dev/config/git_hooks/pre-push-governed-push.sh` | tooling | +19/-3 |
| `dev/guides/DEVELOPMENT.md` | docs | +33/-19 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +217/-2 |
| `dev/scripts/README.md` | tooling | +59/-28 |
| `dev/scripts/checks/code_shape/code_shape_policy.py` | tooling | +4/-6 |
| `dev/scripts/checks/platform_contract_closure/field_routes_control_plane.py` | tooling | +203/-0 |
| `dev/scripts/checks/review_channel_bridge/report.py` | tooling | +9/-5 |
| `dev/scripts/checks/review_surface_consistency/proof_tick.py` | tooling | +0/-2 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +11/-2 |
| `dev/scripts/devctl/commands/governance/install_git_hooks.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/governance/install_git_hooks_support.py` | tooling | +31/-1 |
| `dev/scripts/devctl/commands/governance/session_resume_cache_packet_builder.py` | tooling | +121/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_render.py` | tooling | +26/-128 |
| `dev/scripts/devctl/commands/governance/session_resume_render_role_sections.py` | tooling | +247/-7 |
| `dev/scripts/devctl/commands/governance/session_resume_source_helpers.py` | tooling | +5/-2 |
| `dev/scripts/devctl/commands/governance/startup_context_push_render.py` | tooling | +6/-0 |
| `dev/scripts/devctl/commands/governance/startup_context_summary.py` | tooling | +23/-0 |
| `dev/scripts/devctl/commands/pipeline/auto_recover_action.py` | tooling | +29/-2 |
| `dev/scripts/devctl/commands/pipeline/auto_recover_result.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/pipeline/head_movement.py` | tooling | +103/-0 |
| `dev/scripts/devctl/commands/pipeline/recover_action.py` | tooling | +14/-2 |
| `dev/scripts/devctl/commands/pipeline/refresh_authorization_action.py` | tooling | +14/-2 |
| `dev/scripts/devctl/commands/pipeline/status_action.py` | tooling | +21/-5 |
| `dev/scripts/devctl/commands/pipeline/support.py` | tooling | +13/-10 |
| `dev/scripts/devctl/commands/review_channel/event_watch_support.py` | tooling | +16/-1 |
| `dev/scripts/devctl/commands/vcs/commit_preflight.py` | tooling | +13/-6 |
| `dev/scripts/devctl/commands/vcs/commit_preflight_approval_packets.py` | tooling | +124/-0 |
| `dev/scripts/devctl/commands/vcs/commit_preflight_validators.py` | tooling | +34/-108 |
| `dev/scripts/devctl/commands/vcs/governed_executor_actor_authority.py` | tooling | +188/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py` | tooling | +46/-218 |
| _65 more files trimmed_ | | |

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
| `AcceptAllOrphansAction` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `AcceptAllOrphansReceipt` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `ActionResult` | `governance_runtime` | `n/a` | status, reason |
| `ActorAuthorityState` | `governance_runtime` | `n/a` | actor_id, role |
| `ArtifactStore` | `governance_runtime` | `n/a` | root, managed_kinds |
| `AutoModeState` | `governance_runtime` | `n/a` | phase, next_transition |
| `CallerAuthorityPolicy` | `governance_runtime` | `n/a` | caller_id, allowed_actions |
| `CapabilityGrantState` | `governance_runtime` | `n/a` | capability, granted |
| `CheckResult` | `governance_runtime` | `n/a` | success, total |
| `CheckoutInventory` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `CheckoutInventoryClassification` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `CheckoutInventoryRow` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `ControlPlaneReadModel` | `governance_runtime` | `n/a` | push_eligible, top_blocker |
| `ControlState` | `governance_runtime` | `n/a` | approvals, active_runs |
| `CoordinationSnapshot` | `governance_core` | `n/a` | current_slice, recommended_topology |
| `DecisionPacket` | `governance_runtime` | `n/a` | decision_mode, rule_summary |
| `FailurePacket` | `governance_runtime` | `n/a` | runner, status |
| `Finding` | `governance_runtime` | `n/a` | check_id, severity |
| `LocalServiceEndpoint` | `governance_runtime` | `n/a` | service_id, discovery_fields |
| `OrphanInventoryReport` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `OrphanReconciliationDecision` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `OrphanSnapshot` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `OrphanSnapshotStats` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `OrphanSource` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `OrphanSourceClassification` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `OrphanSourceDecision` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `ProviderAdapter` | `governance_adapters` | `n/a` | provider_id, capabilities |
| `PublicationEpisode` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `PushAuthorizationRecord` | `governance_runtime` | `n/a` | authorization_id, authorized_head_sha |
| `RemoteCommitPipelineContract` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:RemoteCommitPipelineContract` | snapshot_id, state |
| `RepoPack` | `repo_packs` | `n/a` | pack_id, policy_path |
| `ReviewCandidateRecord` | `governance_runtime` | `n/a` | candidate_id, artifact_kind |
| `ReviewState` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewState` | snapshot_id, bridge |
| `ReviewerRuntimeContract` | `governance_runtime` | `n/a` | reviewer_mode, reviewer_freshness |
| `RunRecord` | `governance_runtime` | `n/a` | run_id, status |
| `SessionCachePacket` | `governance_commands` | `n/a` | last_reviewed_sha, advisory_action |
| `SessionLease` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `TypedAction` | `governance_runtime` | `n/a` | action_id, repo_pack_id |
| `WorkPublicationLedger` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `WorkPublicationLedgerEvent` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `WorkPublicationLedgerHeader` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |
| `WorkflowAdapter` | `governance_adapters` | `n/a` | adapter_id, transport |
| `WorktreeBaseline` | `governance_runtime` | `n/a` | orphan-snapshot, checkout-inventory |

### Key documents

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`

## 6. Reviewer hints — please verify

### Targeted hints

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actor_authority.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_targets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_push.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_push_counts.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_push_projection.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_push_decision.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit 4ba95539 changed dev/scripts/devctl/review_channel/packet_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/pipeline_auto_recovery_contracts.py`) — Commit 4ba95539 changed dev/scripts/devctl/runtime/pipeline_auto_recovery_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_pipeline_auto_recovery_contracts.py`) — Commit 4ba95539 changed dev/scripts/devctl/tests/runtime/test_pipeline_auto_recovery_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/governance/push_state_models.py`) — Commit 0ec1b679 changed dev/scripts/devctl/governance/push_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit 0ec1b679 changed dev/scripts/devctl/platform/surface_state_contract_rows.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`5d1c0ccf`** — Checkpoint actor-authority liveness slice (rev_pkt_1818)
  - Codex architectural fix: typed authority surfaces now agree on
  - active_dual_agent when live remote-control plus reviewer activity prove
  - it, instead of trusting stale raw reviewer_mode=tools_only. Shared
  - evolution: Fact: the review-channel runtime already carried `mutation_owner`, but commit handoff code still had paths that reasoned from reviewer mode or stale capability projections. That kept the system vulnerable to the same cl…
- **`30fb4c55`** — Refresh external review snapshot for 75d4bf8f
  - evolution: Fact: the review-channel runtime already carried `mutation_owner`, but commit handoff code still had paths that reasoned from reviewer mode or stale capability projections. That kept the system vulnerable to the same cl…
- **`75d4bf8f`** — Refresh external review snapshot for 71385e9d
  - evolution: Fact: the review-channel runtime already carried `mutation_owner`, but commit handoff code still had paths that reasoned from reviewer mode or stale capability projections. That kept the system vulnerable to the same cl…
- **`71385e9d`** — Add inactivity-watchdog to conductor wrapper (path 1 fix)
  - Branch: feature/governance-quality-sweep
  - Operator-authorized commit at 2026-04-24T08:55Z (per-action scope: 'commit + push the watchdog slice (4 modified + 3 new files...) on feature/governance-quality-sweep, then rollover --recover-provider codex to verify the new conductor uses the watchdog template').
  - evolution: Fact: the review-channel runtime already carried `mutation_owner`, but commit handoff code still had paths that reasoned from reviewer mode or stale capability projections. That kept the system vulnerable to the same cl…
- **`442aa2c3`** — Refresh external review snapshot for 61224a5a
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`61224a5a`** — Refresh external review snapshot for eafea93b
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`eafea93b`** — Fix codex portability findings: 3.10 datetime.UTC + venv interpreter basename
  - Branch: feature/governance-quality-sweep
  - Operator-authorized commit at 2026-04-24T02:53Z (per-action scope: 'commit + push the codex portability fixes (F1 + F2, 8 files)').
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`411cb262`** — Refresh external review snapshot for 6432db5a
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`6432db5a`** — Refresh external review snapshot for a75d0d33
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`a75d0d33`** — Refresh external review snapshot for af4a23b3
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`af4a23b3`** — Refresh external review snapshot for c3229f22
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`c3229f22`** — Slice 1+2 rev 12 + install-hooks fix + code-shape modularization
  - CONTEXT FOR PERMISSION CLASSIFIER:
  - - Branch: feature/governance-quality-sweep (NOT master/main)
  - - Auth: operator broadened claude=coder/executor at 2026-04-24T01:23Z
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`9d6f1eb6`** — Repair review surface bootstrap contracts
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`e66c68e3`** — Refresh external review snapshot for 68dbe112
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`68dbe112`** — Refresh external review snapshot for e7211799
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`e7211799`** — chore(push): auto-commit preflight-generated changes
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`e3ebc4ef`** — Refresh external review snapshot for 653beda0
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`653beda0`** — chore(push): auto-commit preflight-generated changes
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`4ba95539`** — Route remote-control staging handoffs
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`cf61d131`** — Refresh external review snapshot for ddafb608
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`ddafb608`** — Refresh external review snapshot for 415674d0
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`415674d0`** — Add managed projection receipt push cleanup
  - evolution: Fact: the first ADR-008 slice made `bridge.md` drift visible as managed projection state, but a green push could still end with raw `git status` showing the tracked compatibility projection dirty. That left the operator…
- **`fd11a448`** — Refresh external review snapshot for 0ec1b679
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`0ec1b679`** — Classify managed bridge projection drift
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
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
- checkpoint_before_continue: staged_index_budget_exceeded

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-150829e26338` binds this file to HEAD `5d1c0ccfe1f0`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
