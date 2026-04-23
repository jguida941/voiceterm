# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `417830019ab8` — Align observer review surface next-command parity
- Tree hash: `bb6a5e06ddce`
- Generation stamp: `snap-018ca858e694`
- Generated at (UTC): 2026-04-23T01:04:54Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 94 files, +8442/-1699
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
- HEAD SHA: `417830019ab8903ca952ced1c7f793bdc2cecad1`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-22T21:04:42-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: recommended
- publication_guidance: 3 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `417830019ab8`

- commits: 24
- files changed: 94
- insertions: +8442
- deletions: -1699
- bundle classes touched: tooling, docs
- authority surfaces touched: 5 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `41783001` | Align observer review surface next-command parity | 4 | +71/-57 | tooling |  |
| 2 | `6bd851e9` | Refresh external review snapshot for 42376bb0 | 2 | +73/-73 | docs |  |
| 3 | `42376bb0` | Add read-only advisory next-command filter | 27 | +367/-126 | tooling |  |
| 4 | `6505342a` | Refresh external review snapshot for d340497e | 2 | +71/-71 | docs |  |
| 5 | `d340497e` | Add pipeline auto-recover for stale governed commits | 17 | +1340/-88 | tooling |  |
| 6 | `5553d4f0` | Refresh external review snapshot for 49d0b13c | 2 | +55/-54 | docs |  |
| 7 | `49d0b13c` | Record post-push bridge and publish automation debt | 3 | +54/-50 | tooling |  |
| 8 | `1339466e` | Refresh external review snapshot for 86adf8b2 | 2 | +78/-80 | docs |  |
| 9 | `86adf8b2` | Add external repo path for orphan inventory and staged-scop… | 19 | +351/-103 | tooling |  |
| 10 | `a3299c78` | Add external repo path for orphan inventory proof | 1 | +58/-51 | tooling |  |
| 11 | `041293c2` | Refresh external review snapshot for 71f7bcf2 | 2 | +58/-58 | docs |  |
| 12 | `71f7bcf2` | Fix review surface receipt parity and observer resume routi… | 7 | +161/-73 | tooling |  |
| 13 | `daf8f389` | Refresh external review snapshot for 5d439f50 | 2 | +68/-65 | docs |  |
| 14 | `5d439f50` | Add advisory orphan snapshot projection | 21 | +692/-68 | tooling |  |
| 15 | `6ebcddfd` | Refresh external review snapshot for dc82fbf1 | 2 | +71/-81 | docs |  |
| 16 | `dc82fbf1` | Add report-only worktree orphan inventory scan | 36 | +2221/-61 | tooling |  |
| 17 | `b6aa8c9f` | Refresh external review snapshot for ccb68067 | 2 | +65/-74 | docs |  |
| 18 | `ccb68067` | Refine worktree orphan reconciliation parsers | 3 | +85/-76 | tooling |  |
| 19 | `549e0cef` | Refresh external review snapshot for c3a2d9a7 | 2 | +93/-96 | docs |  |
| 20 | `c3a2d9a7` | Add worktree orphan governance contracts | 22 | +2148/-52 | tooling |  |
| 21 | `362dbdb9` | Refresh external review snapshot for c08d18c4 | 2 | +67/-76 | docs |  |
| 22 | `c08d18c4` | Refresh bridge ack projection | 2 | +61/-60 | docs |  |
| 23 | `3f4ef1a8` | Refresh external review snapshot for 2aa7c916 | 2 | +54/-54 | docs |  |
| 24 | `2aa7c916` | Align startup authority push next command | 4 | +80/-52 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +36/-12 |
| `bridge.md` | docs | +74/-74 |
| `dev/active/MASTER_PLAN.md` | tooling | +44/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +65/-2 |
| `dev/active/portable_code_governance.md` | tooling | +13/-1 |
| `dev/audits/AI_GOVERNANCE_PLATFORM_PROOF_LEDGER.md` | tooling | +7/-0 |
| `dev/audits/AUTOMATION_DEBT_REGISTER.md` | tooling | +8/-2 |
| `dev/audits/LIVE_RUN.md` | tooling | +29/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1450/-1446 |
| `dev/guides/DEVELOPMENT.md` | docs | +41/-7 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +206/-1 |
| `dev/scripts/README.md` | tooling | +41/-4 |
| `dev/scripts/checks/code_shape/code_shape_policy.py` | tooling | +0/-12 |
| `dev/scripts/checks/review_surface_consistency/command.py` | tooling | +14/-1 |
| `dev/scripts/checks/review_surface_consistency/proof_tick.py` | tooling | +6/-3 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +10/-0 |
| `dev/scripts/devctl/cli_parser/pipeline.py` | tooling | +6/-2 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +9/-4 |
| `dev/scripts/devctl/commands/governance/orphan_inventory.py` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/governance/orphan_inventory_parser.py` | tooling | +42/-0 |
| `dev/scripts/devctl/commands/governance/orphan_inventory_render.py` | tooling | +92/-0 |
| `dev/scripts/devctl/commands/governance/orphan_inventory_run.py` | tooling | +36/-1 |
| `dev/scripts/devctl/commands/governance/session_resume_role_projection.py` | tooling | +43/-21 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +13/-11 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +10/-1 |
| `dev/scripts/devctl/commands/mobile_status.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/pipeline/auto_recover_action.py` | tooling | +321/-0 |
| `dev/scripts/devctl/commands/pipeline/auto_recover_result.py` | tooling | +208/-0 |
| `dev/scripts/devctl/commands/pipeline/command.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/vcs/commit_preflight.py` | tooling | +5/-2 |
| `dev/scripts/devctl/commands/vcs/commit_preflight_validators.py` | tooling | +12/-5 |
| `dev/scripts/devctl/commands/vcs/governed_executor_phases.py` | tooling | +49/-2 |
| `dev/scripts/devctl/commands/vcs/governed_executor_stage_snapshot.py` | tooling | +19/-4 |
| `dev/scripts/devctl/commands/vcs/orphan_snapshot_advisory.py` | tooling | +45/-0 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +6/-0 |
| `dev/scripts/devctl/platform/runtime_contract_rows.py` | tooling | +6/-1 |
| `dev/scripts/devctl/platform/system_picture.py` | tooling | +8/-3 |
| `dev/scripts/devctl/platform/worktree_orphan_contract_rows.py` | tooling | +154/-0 |
| `dev/scripts/devctl/runtime/README.md` | tooling | +3/-0 |
| `dev/scripts/devctl/runtime/action_routing.py` | tooling | +6/-1 |
| _54 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_phases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_stage_snapshot.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/pipeline_auto_recovery_contracts.py`) — Commit d340497e changed dev/scripts/devctl/runtime/pipeline_auto_recovery_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_pipeline_auto_recovery_contracts.py`) — Commit d340497e changed dev/scripts/devctl/tests/runtime/test_pipeline_auto_recovery_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/worktree_orphan_contracts.py`) — Commit 5d439f50 changed dev/scripts/devctl/runtime/worktree_orphan_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_worktree_orphan_contracts.py`) — Commit 5d439f50 changed dev/scripts/devctl/tests/runtime/test_worktree_orphan_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/worktree_orphan_contract_rows.py`) — Commit dc82fbf1 changed dev/scripts/devctl/platform/worktree_orphan_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_contract_rows.py`) — Commit c3a2d9a7 changed dev/scripts/devctl/platform/runtime_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/checkout_inventory_contracts.py`) — Commit c3a2d9a7 changed dev/scripts/devctl/runtime/checkout_inventory_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/session_lease_contracts.py`) — Commit c3a2d9a7 changed dev/scripts/devctl/runtime/session_lease_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_publication_ledger_contracts.py`) — Commit c3a2d9a7 changed dev/scripts/devctl/runtime/work_publication_ledger_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`ccb68067`** — Refine worktree orphan reconciliation parsers
  - evolution: Fact: after `AuthoritySnapshot` and `CoordinationSnapshot` started carrying producer provenance, the remaining read-side surfaces could still diverge for the same proof tick. `ControlPlaneReadModel` and `SessionCachePac…
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
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-018ca858e694` binds this file to HEAD `417830019ab8`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
