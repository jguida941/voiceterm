# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `549e0cef9dd0` — Refresh external review snapshot for c3a2d9a7
- Tree hash: `8a8f8db52bf4`
- Generation stamp: `snap-fc48edf4f1cc`
- Generated at (UTC): 2026-04-22T18:09:43Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 70 files, +6338/-1995
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
- HEAD SHA: `549e0cef9dd0d4db6d326bbb37613babac554e8d`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-22T13:45:17-04:00

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
- latest_push_report_state: `post_push_green` (push_completed)
- current_push_authorization: `push-auth-20260422T174451611499Z` (valid=True)
- authorized_head_commit: `549e0cef9dd0d4db6d326bbb37613babac554e8d`
- approved_target_identity: `tree-receipt-20260422T174451611499Z:f2bcf3ee41ff6873d8f6475327ad39edd9ab2b34`
- publication_backlog: none

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
- advisory: `checkpoint_allowed` — worktree_dirty_within_budget

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `549e0cef9dd0`

- commits: 25
- files changed: 70
- insertions: +6338
- deletions: -1995
- bundle classes touched: docs, tooling
- authority surfaces touched: 5 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `549e0cef` | Refresh external review snapshot for c3a2d9a7 | 2 | +93/-96 | docs |  |
| 2 | `c3a2d9a7` | Add worktree orphan governance contracts | 22 | +2148/-52 | tooling |  |
| 3 | `362dbdb9` | Refresh external review snapshot for c08d18c4 | 2 | +67/-76 | docs |  |
| 4 | `c08d18c4` | Refresh bridge ack projection | 2 | +61/-60 | docs |  |
| 5 | `3f4ef1a8` | Refresh external review snapshot for 2aa7c916 | 2 | +54/-54 | docs |  |
| 6 | `2aa7c916` | Align startup authority push next command | 4 | +80/-52 | tooling |  |
| 7 | `8ff2a6b5` | Refresh external review snapshot for 265e28f6 | 2 | +63/-64 | docs |  |
| 8 | `265e28f6` | Repair single-agent ownership topology | 9 | +299/-101 | tooling |  |
| 9 | `caed14d1` | Refresh external review snapshot for a3df69dd | 2 | +74/-76 | docs |  |
| 10 | `a3df69dd` | Close Phase 0 proof tick parity | 23 | +1003/-135 | tooling |  |
| 11 | `94e2378f` | Refresh external review snapshot for 9e7b1050 | 2 | +63/-63 | docs |  |
| 12 | `9e7b1050` | Doc drift sweep from prior sessions | 7 | +117/-70 | tooling |  |
| 13 | `2490f839` | Phase 0.c: preserve explicit reviewer mode over daemon-deri… | 8 | +244/-78 | tooling |  |
| 14 | `42fecac5` | Refresh external review snapshot for db210b73 | 2 | +76/-68 | docs |  |
| 15 | `db210b73` | Add authority snapshot provenance | 18 | +592/-187 | tooling |  |
| 16 | `c2eecb29` | Refresh external review snapshot for 7dd94280 | 2 | +71/-65 | docs |  |
| 17 | `7dd94280` | Require post-push-green proof before projecting push_comple… | 11 | +220/-154 | tooling |  |
| 18 | `bc0a31f7` | Refresh external review snapshot for 3625ecbb | 2 | +50/-50 | docs |  |
| 19 | `3625ecbb` | Refresh external review snapshot for 211b6094 | 2 | +77/-81 | docs |  |
| 20 | `211b6094` | Keep event-backed review state authoritative | 10 | +187/-79 | tooling |  |
| 21 | `9f69c9d2` | Keep event-backed review state authoritative | 1 | +61/-63 | tooling |  |
| 22 | `39816b18` | Refresh external review snapshot for be738893 | 2 | +73/-79 | docs |  |
| 23 | `be738893` | Fix stall_diagnostics replacement-session precedence (rev_p… | 9 | +157/-68 | tooling |  |
| 24 | `227ca27e` | Refresh external review snapshot for dbd0b7e2 | 2 | +67/-70 | docs |  |
| 25 | `dbd0b7e2` | Close reviewer-wake auto-elevation gap and align stall diag… | 10 | +341/-54 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +43/-5 |
| `bridge.md` | docs | +152/-152 |
| `dev/active/MASTER_PLAN.md` | tooling | +68/-6 |
| `dev/active/ai_governance_platform.md` | tooling | +52/-2 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1531/-1523 |
| `dev/guides/DEVELOPMENT.md` | docs | +63/-7 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +285/-6 |
| `dev/scripts/README.md` | tooling | +40/-4 |
| `dev/scripts/checks/review_surface_consistency/command.py` | tooling | +84/-6 |
| `dev/scripts/checks/review_surface_consistency/models.py` | tooling | +1/-0 |
| `dev/scripts/checks/review_surface_consistency/proof_tick.py` | tooling | +145/-0 |
| `dev/scripts/checks/review_surface_consistency/snapshot_fields.py` | tooling | +26/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_packet.py` | tooling | +12/-1 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +25/-0 |
| `dev/scripts/devctl/commands/review_channel/status.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/status_bridge_sync.py` | tooling | +8/-7 |
| `dev/scripts/devctl/commands/vcs/governed_executor_push_result.py` | tooling | +3/-10 |
| `dev/scripts/devctl/platform/coordination_snapshot.py` | tooling | +45/-7 |
| `dev/scripts/devctl/platform/coordination_snapshot_models.py` | tooling | +13/-3 |
| `dev/scripts/devctl/platform/coordination_snapshot_support.py` | tooling | +1/-1 |
| `dev/scripts/devctl/platform/runtime_contract_rows.py` | tooling | +6/-1 |
| `dev/scripts/devctl/platform/surface_state_contract_rows.py` | tooling | +29/-0 |
| `dev/scripts/devctl/platform/worktree_orphan_contract_rows.py` | tooling | +149/-0 |
| `dev/scripts/devctl/review_channel/collaboration_session_coordination.py` | tooling | +2/-1 |
| `dev/scripts/devctl/review_channel/collaboration_session_roster.py` | tooling | +12/-5 |
| `dev/scripts/devctl/review_channel/current_session_support.py` | tooling | +52/-0 |
| `dev/scripts/devctl/review_channel/event_projection_bridge.py` | tooling | +24/-3 |
| `dev/scripts/devctl/review_channel/projection_bundle.py` | tooling | +27/-49 |
| `dev/scripts/devctl/review_channel/projection_bundle_payloads.py` | tooling | +78/-0 |
| `dev/scripts/devctl/review_channel/projection_provenance.py` | tooling | +7/-1 |
| `dev/scripts/devctl/review_channel/reviewer_follow_guard.py` | tooling | +22/-1 |
| `dev/scripts/devctl/review_channel/reviewer_runtime_publication.py` | tooling | +2/-8 |
| `dev/scripts/devctl/review_channel/stall_diagnostics.py` | tooling | +37/-9 |
| `dev/scripts/devctl/review_channel/status_projection_bridge_state.py` | tooling | +4/-0 |
| `dev/scripts/devctl/review_channel/status_snapshot_authority.py` | tooling | +1/-0 |
| `dev/scripts/devctl/runtime/README.md` | tooling | +3/-0 |
| `dev/scripts/devctl/runtime/authority_snapshot_build.py` | tooling | +5/-7 |
| `dev/scripts/devctl/runtime/authority_snapshot_core.py` | tooling | +44/-61 |
| `dev/scripts/devctl/runtime/authority_snapshot_packet_target.py` | tooling | +43/-0 |
| `dev/scripts/devctl/runtime/authority_snapshot_provenance.py` | tooling | +60/-0 |
| _30 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_push_result.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_publication.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_contract_rows.py`) — Commit c3a2d9a7 changed dev/scripts/devctl/platform/runtime_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/worktree_orphan_contract_rows.py`) — Commit c3a2d9a7 changed dev/scripts/devctl/platform/worktree_orphan_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/checkout_inventory_contracts.py`) — Commit c3a2d9a7 changed dev/scripts/devctl/runtime/checkout_inventory_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/session_lease_contracts.py`) — Commit c3a2d9a7 changed dev/scripts/devctl/runtime/session_lease_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_publication_ledger_contracts.py`) — Commit c3a2d9a7 changed dev/scripts/devctl/runtime/work_publication_ledger_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/worktree_orphan_contracts.py`) — Commit c3a2d9a7 changed dev/scripts/devctl/runtime/worktree_orphan_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_worktree_orphan_contracts.py`) — Commit c3a2d9a7 changed dev/scripts/devctl/tests/runtime/test_worktree_orphan_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit a3df69dd changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/coordination_snapshot_models.py`) — Commit db210b73 changed dev/scripts/devctl/platform/coordination_snapshot_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`549e0cef`** — Refresh external review snapshot for c3a2d9a7
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`c3a2d9a7`** — Add worktree orphan governance contracts
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`362dbdb9`** — Refresh external review snapshot for c08d18c4
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`c08d18c4`** — Refresh bridge ack projection
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`3f4ef1a8`** — Refresh external review snapshot for 2aa7c916
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`2aa7c916`** — Align startup authority push next command
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`8ff2a6b5`** — Refresh external review snapshot for 265e28f6
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`265e28f6`** — Repair single-agent ownership topology
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`caed14d1`** — Refresh external review snapshot for a3df69dd
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`a3df69dd`** — Close Phase 0 proof tick parity
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
- **`94e2378f`** — Refresh external review snapshot for 9e7b1050
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`9e7b1050`** — Doc drift sweep from prior sessions
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`2490f839`** — Phase 0.c: preserve explicit reviewer mode over daemon-derived liveness (rev_pkt_1556)
  - Event-backed reviewer_mode projection now prefers explicit bridge metadata
  - before falling back to daemon lifecycle rows, and bridge-from-typed reverse
  - sync respects newer reviewer-owned checkpoint authority. Adds regression
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`42fecac5`** — Refresh external review snapshot for db210b73
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`db210b73`** — Add authority snapshot provenance
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`c2eecb29`** — Refresh external review snapshot for 7dd94280
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`7dd94280`** — Require post-push-green proof before projecting push_completed (rev_pkt_1502)
  - Close the heal-path regression codex self-identified earlier in this
  - sweep: `_push_report_completed` in `governed_executor_push_result.py`
  - was treating any `branch_already_pushed + published_remote=true` rerun
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`bc0a31f7`** — Refresh external review snapshot for 3625ecbb
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`3625ecbb`** — Refresh external review snapshot for 211b6094
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`211b6094`** — Keep event-backed review state authoritative
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`9f69c9d2`** — Keep event-backed review state authoritative
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`39816b18`** — Refresh external review snapshot for be738893
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`be738893`** — Fix stall_diagnostics replacement-session precedence (rev_pkt_1529)
  - The prior iteration removed the `and not task_complete_iso` gate on the
  - `escalation_deadlock` reason branch, but the check order stayed wrong:
  - the diagnostic reported `escalation_deadlock` before inspecting the
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`227ca27e`** — Refresh external review snapshot for dbd0b7e2
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
- **`dbd0b7e2`** — Close reviewer-wake auto-elevation gap and align stall diagnostics with real rollout shape
  - The 16c6f9ad batch covered launch / rollover / recover but the ensure-follow
  - reviewer-wake path in `reviewer_follow_guard.py::launch_waiting_reviewer_conductor`
  - still coerced the unset `--approval-mode` parser default to an empty string,
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
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
- checkpoint_allowed: worktree_dirty_within_budget

### Stale warnings
- Move straight to the governed push path.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-fc48edf4f1cc` binds this file to HEAD `549e0cef9dd0`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
