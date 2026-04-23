# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `4ba95539c603` — Route remote-control staging handoffs
- Tree hash: `eb42a30536ed`
- Generation stamp: `snap-262478f0c6c4`
- Generated at (UTC): 2026-04-23T13:33:40Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 118 files, +8291/-2071
- Governance findings: 112 open / 86 fixed / 212 total
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
- HEAD SHA: `4ba95539c6032065ede4e433e38ea84fc3c8fcf8`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-23T09:25:47-04:00

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
- latest_push_report_state: `post_push_green` (push_completed)
- current_push_authorization: `push-auth-20260423T132522272297Z` (valid=True)
- authorized_head_commit: `4ba95539c6032065ede4e433e38ea84fc3c8fcf8`
- approved_target_identity: `tree-receipt-20260423T132522272297Z:eb42a30536edb994c0adffb41eaf4e9d7a381e29`
- publication_backlog: queued
- publication_guidance: 1 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

### Reviewer runtime
- reviewer_mode: `single_agent`
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
- advisory: `checkpoint_before_continue` — dirty_after_local_checkpoint

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `4ba95539c603`

- commits: 24
- files changed: 118
- insertions: +8291
- deletions: -2071
- bundle classes touched: docs, tooling
- authority surfaces touched: 15 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `4ba95539` | Route remote-control staging handoffs | 28 | +1094/-439 | tooling |  |
| 2 | `cf61d131` | Refresh external review snapshot for ddafb608 | 1 | +1/-1 | docs |  |
| 3 | `ddafb608` | Refresh external review snapshot for 415674d0 | 2 | +66/-66 | docs |  |
| 4 | `415674d0` | Add managed projection receipt push cleanup | 14 | +500/-70 | tooling |  |
| 5 | `fd11a448` | Refresh external review snapshot for 0ec1b679 | 2 | +75/-70 | docs |  |
| 6 | `0ec1b679` | Classify managed bridge projection drift | 31 | +647/-135 | tooling |  |
| 7 | `c03ce187` | Refresh external review snapshot for 41783001 | 2 | +54/-57 | docs |  |
| 8 | `41783001` | Align observer review surface next-command parity | 4 | +71/-57 | tooling |  |
| 9 | `6bd851e9` | Refresh external review snapshot for 42376bb0 | 2 | +73/-73 | docs |  |
| 10 | `42376bb0` | Add read-only advisory next-command filter | 27 | +367/-126 | tooling |  |
| 11 | `6505342a` | Refresh external review snapshot for d340497e | 2 | +71/-71 | docs |  |
| 12 | `d340497e` | Add pipeline auto-recover for stale governed commits | 17 | +1340/-88 | tooling |  |
| 13 | `5553d4f0` | Refresh external review snapshot for 49d0b13c | 2 | +55/-54 | docs |  |
| 14 | `49d0b13c` | Record post-push bridge and publish automation debt | 3 | +54/-50 | tooling |  |
| 15 | `1339466e` | Refresh external review snapshot for 86adf8b2 | 2 | +78/-80 | docs |  |
| 16 | `86adf8b2` | Add external repo path for orphan inventory and staged-scop… | 19 | +351/-103 | tooling |  |
| 17 | `a3299c78` | Add external repo path for orphan inventory proof | 1 | +58/-51 | tooling |  |
| 18 | `041293c2` | Refresh external review snapshot for 71f7bcf2 | 2 | +58/-58 | docs |  |
| 19 | `71f7bcf2` | Fix review surface receipt parity and observer resume routi… | 7 | +161/-73 | tooling |  |
| 20 | `daf8f389` | Refresh external review snapshot for 5d439f50 | 2 | +68/-65 | docs |  |
| 21 | `5d439f50` | Add advisory orphan snapshot projection | 21 | +692/-68 | tooling |  |
| 22 | `6ebcddfd` | Refresh external review snapshot for dc82fbf1 | 2 | +71/-81 | docs |  |
| 23 | `dc82fbf1` | Add report-only worktree orphan inventory scan | 36 | +2221/-61 | tooling |  |
| 24 | `b6aa8c9f` | Refresh external review snapshot for ccb68067 | 2 | +65/-74 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +31/-13 |
| `bridge.md` | docs | +36/-36 |
| `dev/active/MASTER_PLAN.md` | tooling | +65/-5 |
| `dev/active/ai_governance_platform.md` | tooling | +84/-5 |
| `dev/active/portable_code_governance.md` | tooling | +13/-1 |
| `dev/active/remote_commit_pipeline.md` | tooling | +13/-1 |
| `dev/audits/AI_GOVERNANCE_PLATFORM_PROOF_LEDGER.md` | tooling | +7/-0 |
| `dev/audits/AUTOMATION_DEBT_REGISTER.md` | tooling | +12/-6 |
| `dev/audits/LIVE_RUN.md` | tooling | +29/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1403/-1412 |
| `dev/guides/DEVELOPMENT.md` | docs | +45/-13 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +270/-1 |
| `dev/scripts/README.md` | tooling | +67/-20 |
| `dev/scripts/checks/code_shape/code_shape_policy.py` | tooling | +0/-12 |
| `dev/scripts/checks/review_surface_consistency/command.py` | tooling | +14/-1 |
| `dev/scripts/checks/review_surface_consistency/proof_tick.py` | tooling | +6/-3 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +10/-0 |
| `dev/scripts/devctl/cli_parser/pipeline.py` | tooling | +6/-2 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +20/-6 |
| `dev/scripts/devctl/commands/governance/orphan_inventory.py` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/governance/orphan_inventory_parser.py` | tooling | +42/-0 |
| `dev/scripts/devctl/commands/governance/orphan_inventory_render.py` | tooling | +92/-0 |
| `dev/scripts/devctl/commands/governance/orphan_inventory_run.py` | tooling | +36/-1 |
| `dev/scripts/devctl/commands/governance/session_resume_role_projection.py` | tooling | +43/-21 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +13/-11 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +10/-1 |
| `dev/scripts/devctl/commands/governance/startup_context_push_render.py` | tooling | +6/-0 |
| `dev/scripts/devctl/commands/governance/startup_context_summary.py` | tooling | +23/-0 |
| `dev/scripts/devctl/commands/mobile_status.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/pipeline/auto_recover_action.py` | tooling | +350/-2 |
| `dev/scripts/devctl/commands/pipeline/auto_recover_result.py` | tooling | +210/-0 |
| `dev/scripts/devctl/commands/pipeline/command.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/pipeline/head_movement.py` | tooling | +103/-0 |
| `dev/scripts/devctl/commands/pipeline/recover_action.py` | tooling | +14/-2 |
| `dev/scripts/devctl/commands/pipeline/refresh_authorization_action.py` | tooling | +14/-2 |
| `dev/scripts/devctl/commands/pipeline/status_action.py` | tooling | +21/-5 |
| `dev/scripts/devctl/commands/pipeline/support.py` | tooling | +13/-10 |
| `dev/scripts/devctl/commands/vcs/commit_preflight.py` | tooling | +18/-8 |
| `dev/scripts/devctl/commands/vcs/commit_preflight_approval_packets.py` | tooling | +124/-0 |
| `dev/scripts/devctl/commands/vcs/commit_preflight_validators.py` | tooling | +46/-113 |
| _78 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 212
- open: 112
- fixed: 86
- false positives: 0

Recent findings:
- `dogfood_finding_id_instability` — `dev/scripts/devctl/runtime/dogfood_log.py` (n/a, verdict=`confirmed_issue`)
- `dogfood_read_only_registration_missing` — `dev/scripts/devctl/cli_parser/entrypoint.py` (n/a, verdict=`confirmed_issue`)
- `finding_backlog_writer_closure_broken` — `dev/scripts/devctl/runtime/finding_backlog.py` (n/a, verdict=`confirmed_issue`)
- `dogfood_governance_pipeline_missing` — `dev/scripts/devctl/runtime/dogfood_log.py` (n/a, verdict=`confirmed_issue`)
- `bridge_authority_conflict` — `bridge.md` (n/a, verdict=`confirmed_issue`)
- `plan_markdown_projection_missing` — `dev/scripts/devctl/platform/planning_ir_models.py` (n/a, verdict=`confirmed_issue`)
- `plan_authority_gap` — `dev/active/MASTER_PLAN.md` (n/a, verdict=`confirmed_issue`)
- `bridge_metadata_parsed_as_authority` — `dev/scripts/devctl/review_channel/handoff.py` (n/a, verdict=`confirmed_issue`)
- `authority_snapshot_3_fields_missing` — `dev/scripts/devctl/runtime/startup_context.py` (n/a, verdict=`fixed`)
- `dogfood.command.startup-context` — `dev/scripts/devctl/commands/governance/startup_context.py` (n/a, verdict=`confirmed_issue`)

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
| `ArtifactStore` | `governance_runtime` | `n/a` | root, managed_kinds |
| `AutoModeState` | `governance_runtime` | `n/a` | phase, next_transition |
| `CallerAuthorityPolicy` | `governance_runtime` | `n/a` | caller_id, allowed_actions |
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

- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_targets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_push.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_push_counts.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_push_projection.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_push_decision.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_phases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_stage_snapshot.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit 4ba95539 changed dev/scripts/devctl/review_channel/packet_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/pipeline_auto_recovery_contracts.py`) — Commit 4ba95539 changed dev/scripts/devctl/runtime/pipeline_auto_recovery_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_pipeline_auto_recovery_contracts.py`) — Commit 4ba95539 changed dev/scripts/devctl/tests/runtime/test_pipeline_auto_recovery_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/governance/push_state_models.py`) — Commit 0ec1b679 changed dev/scripts/devctl/governance/push_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit 0ec1b679 changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/worktree_orphan_contracts.py`) — Commit 5d439f50 changed dev/scripts/devctl/runtime/worktree_orphan_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_worktree_orphan_contracts.py`) — Commit 5d439f50 changed dev/scripts/devctl/tests/runtime/test_worktree_orphan_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/worktree_orphan_contract_rows.py`) — Commit dc82fbf1 changed dev/scripts/devctl/platform/worktree_orphan_contract_rows.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`c03ce187`** — Refresh external review snapshot for 41783001
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`41783001`** — Align observer review surface next-command parity
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`6bd851e9`** — Refresh external review snapshot for 42376bb0
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`42376bb0`** — Add read-only advisory next-command filter
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`6505342a`** — Refresh external review snapshot for d340497e
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`d340497e`** — Add pipeline auto-recover for stale governed commits
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`5553d4f0`** — Refresh external review snapshot for 49d0b13c
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`49d0b13c`** — Record post-push bridge and publish automation debt
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`1339466e`** — Refresh external review snapshot for 86adf8b2
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`86adf8b2`** — Add external repo path for orphan inventory and staged-scope guard
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`a3299c78`** — Add external repo path for orphan inventory proof
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`041293c2`** — Refresh external review snapshot for 71f7bcf2
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`71f7bcf2`** — Fix review surface receipt parity and observer resume routing
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`daf8f389`** — Refresh external review snapshot for 5d439f50
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`5d439f50`** — Add advisory orphan snapshot projection
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`6ebcddfd`** — Refresh external review snapshot for dc82fbf1
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`dc82fbf1`** — Add report-only worktree orphan inventory scan
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`b6aa8c9f`** — Refresh external review snapshot for ccb68067
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

- open governance findings: 112

### Startup advisories
- checkpoint_before_continue: dirty_after_local_checkpoint

### Stale warnings
- Relaunch the reviewer loop immediately.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/runtime/dogfood_log.py`): dogfood_finding_id_instability: 
- **governance_open** (`dev/scripts/devctl/cli_parser/entrypoint.py`): dogfood_read_only_registration_missing: 
- **governance_open** (`dev/scripts/devctl/runtime/finding_backlog.py`): finding_backlog_writer_closure_broken: 
- **governance_open** (`dev/scripts/devctl/runtime/dogfood_log.py`): dogfood_governance_pipeline_missing: 
- **governance_open** (`bridge.md`): bridge_authority_conflict: 
- **governance_open** (`dev/scripts/devctl/platform/planning_ir_models.py`): plan_markdown_projection_missing: 
- **governance_open** (`dev/active/MASTER_PLAN.md`): plan_authority_gap: 
- **governance_open** (`dev/scripts/devctl/review_channel/handoff.py`): bridge_metadata_parsed_as_authority: 

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-262478f0c6c4` binds this file to HEAD `4ba95539c603`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
