# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `9d6f1eb63880` — Repair review surface bootstrap contracts
- Tree hash: `377a81b38514`
- Generation stamp: `snap-76ba48e238db`
- Generated at (UTC): 2026-04-24T01:41:59Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 90 files, +5527/-1955
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
- HEAD SHA: `9d6f1eb63880ad54c499f9e9555d83dec59cb3ae`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-23T10:25:34-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 30
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: urgent
- publication_guidance: 7 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `9d6f1eb63880`

- commits: 24
- files changed: 90
- insertions: +5527
- deletions: -1955
- bundle classes touched: docs, tooling
- authority surfaces touched: 15 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `9d6f1eb6` | Repair review surface bootstrap contracts | 10 | +165/-74 | tooling |  |
| 2 | `e66c68e3` | Refresh external review snapshot for 68dbe112 | 1 | +1/-1 | docs |  |
| 3 | `68dbe112` | Refresh external review snapshot for e7211799 | 2 | +64/-64 | docs |  |
| 4 | `e7211799` | chore(push): auto-commit preflight-generated changes | 11 | +202/-90 | tooling |  |
| 5 | `e3ebc4ef` | Refresh external review snapshot for 653beda0 | 1 | +3/-3 | docs |  |
| 6 | `653beda0` | chore(push): auto-commit preflight-generated changes | 1 | +79/-74 | tooling |  |
| 7 | `4ba95539` | Route remote-control staging handoffs | 28 | +1094/-439 | tooling |  |
| 8 | `cf61d131` | Refresh external review snapshot for ddafb608 | 1 | +1/-1 | docs |  |
| 9 | `ddafb608` | Refresh external review snapshot for 415674d0 | 2 | +66/-66 | docs |  |
| 10 | `415674d0` | Add managed projection receipt push cleanup | 14 | +500/-70 | tooling |  |
| 11 | `fd11a448` | Refresh external review snapshot for 0ec1b679 | 2 | +75/-70 | docs |  |
| 12 | `0ec1b679` | Classify managed bridge projection drift | 31 | +647/-135 | tooling |  |
| 13 | `c03ce187` | Refresh external review snapshot for 41783001 | 2 | +54/-57 | docs |  |
| 14 | `41783001` | Align observer review surface next-command parity | 4 | +71/-57 | tooling |  |
| 15 | `6bd851e9` | Refresh external review snapshot for 42376bb0 | 2 | +73/-73 | docs |  |
| 16 | `42376bb0` | Add read-only advisory next-command filter | 27 | +367/-126 | tooling |  |
| 17 | `6505342a` | Refresh external review snapshot for d340497e | 2 | +71/-71 | docs |  |
| 18 | `d340497e` | Add pipeline auto-recover for stale governed commits | 17 | +1340/-88 | tooling |  |
| 19 | `5553d4f0` | Refresh external review snapshot for 49d0b13c | 2 | +55/-54 | docs |  |
| 20 | `49d0b13c` | Record post-push bridge and publish automation debt | 3 | +54/-50 | tooling |  |
| 21 | `1339466e` | Refresh external review snapshot for 86adf8b2 | 2 | +78/-80 | docs |  |
| 22 | `86adf8b2` | Add external repo path for orphan inventory and staged-scop… | 19 | +351/-103 | tooling |  |
| 23 | `a3299c78` | Add external repo path for orphan inventory proof | 1 | +58/-51 | tooling |  |
| 24 | `041293c2` | Refresh external review snapshot for 71f7bcf2 | 2 | +58/-58 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +24/-10 |
| `bridge.md` | docs | +40/-40 |
| `dev/active/MASTER_PLAN.md` | tooling | +63/-7 |
| `dev/active/ai_governance_platform.md` | tooling | +80/-11 |
| `dev/active/portable_code_governance.md` | tooling | +13/-1 |
| `dev/active/remote_commit_pipeline.md` | tooling | +13/-1 |
| `dev/active/remote_control_runtime.md` | tooling | +3/-2 |
| `dev/audits/AI_GOVERNANCE_PLATFORM_PROOF_LEDGER.md` | tooling | +7/-0 |
| `dev/audits/AUTOMATION_DEBT_REGISTER.md` | tooling | +12/-6 |
| `dev/audits/LIVE_RUN.md` | tooling | +29/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1306/-1303 |
| `dev/guides/DEVELOPMENT.md` | docs | +49/-19 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +271/-3 |
| `dev/scripts/README.md` | tooling | +74/-26 |
| `dev/scripts/checks/code_shape/code_shape_policy.py` | tooling | +0/-12 |
| `dev/scripts/checks/review_surface_consistency/command.py` | tooling | +1/-0 |
| `dev/scripts/checks/review_surface_consistency/proof_tick.py` | tooling | +0/-2 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +6/-0 |
| `dev/scripts/devctl/cli_parser/pipeline.py` | tooling | +6/-2 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +20/-6 |
| `dev/scripts/devctl/commands/governance/orphan_inventory_parser.py` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/governance/orphan_inventory_run.py` | tooling | +5/-1 |
| `dev/scripts/devctl/commands/governance/session_resume_role_projection.py` | tooling | +10/-21 |
| `dev/scripts/devctl/commands/governance/session_resume_source_helpers.py` | tooling | +5/-2 |
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
| `dev/scripts/devctl/commands/review_channel/event_watch_support.py` | tooling | +16/-1 |
| `dev/scripts/devctl/commands/vcs/commit_preflight.py` | tooling | +18/-8 |
| `dev/scripts/devctl/commands/vcs/commit_preflight_approval_packets.py` | tooling | +124/-0 |
| `dev/scripts/devctl/commands/vcs/commit_preflight_validators.py` | tooling | +40/-113 |
| _50 more files trimmed_ | | |

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

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-76ba48e238db` binds this file to HEAD `9d6f1eb63880`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
