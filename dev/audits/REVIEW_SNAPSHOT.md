# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `a9f1a42fa797` — Refresh external review snapshot for d2d91aaf
- Tree hash: `187e318f8def`
- Generation stamp: `snap-476bb605638c`
- Generated at (UTC): 2026-04-16T14:56:08Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 74 files, +6040/-2401
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
- HEAD SHA: `a9f1a42fa797395f526fd9003780c37e56007968`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-16T10:03:13-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 5
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `published_remote` (post_push_bundle_pending)
- publication_backlog: urgent
- publication_guidance: 18 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `local_terminal`
- implementation_blocked: yes — runtime_missing

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `repair_reviewer_loop` — runtime_missing

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `a9f1a42fa797`

- commits: 24
- files changed: 74
- insertions: +6040
- deletions: -2401
- bundle classes touched: docs, tooling
- authority surfaces touched: 10 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `a9f1a42f` | Refresh external review snapshot for d2d91aaf | 2 | +66/-64 | docs |  |
| 2 | `d2d91aaf` | Unify commit-gate caller policy across governed + receipt p… | 8 | +218/-145 | tooling |  |
| 3 | `7c1562f3` | Refresh external review snapshot for dae1df84 | 2 | +65/-65 | docs |  |
| 4 | `dae1df84` | Make reviewer turn runner governance-shaped instead of brid… | 3 | +138/-50 | tooling |  |
| 5 | `b627c135` | Unify target resolver + fail-closed on unresolved target +… | 5 | +110/-118 | tooling |  |
| 6 | `4c01b779` | Add fail-closed commit gate on pending reviewer packets | 6 | +622/-49 | tooling |  |
| 7 | `6221bc32` | Refresh external review snapshot for f4c3a335 | 2 | +63/-61 | docs |  |
| 8 | `f4c3a335` | Fix Codex review findings: revert premature follow wiring +… | 6 | +66/-64 | tooling |  |
| 9 | `26e8730a` | Refresh external review snapshot for d08407ca | 1 | +67/-75 | tooling |  |
| 10 | `4d2c991c` | Refresh external review snapshot for d08407ca | 2 | +66/-63 | docs |  |
| 11 | `d08407ca` | Add portable controller-owned reviewer turn runner + public… | 9 | +1129/-65 | tooling |  |
| 12 | `eea5abf5` | Refresh external review snapshot for bf0c0d90 | 2 | +56/-54 | docs |  |
| 13 | `bf0c0d90` | Fix test_implementer_stall import after event_projection re… | 2 | +59/-60 | tooling |  |
| 14 | `0e0b3288` | Refresh external review snapshot for 7ef603c1 | 2 | +57/-54 | docs |  |
| 15 | `7ef603c1` | Block stale bridge instruction fallback on explicit typed c… | 3 | +112/-61 | tooling |  |
| 16 | `9fb25fcd` | Drop zref from snapshot hash inputs + fix bridge instructio… | 4 | +99/-57 | tooling |  |
| 17 | `d2171db6` | Refresh external review snapshot for 3187f7ce | 2 | +77/-78 | docs |  |
| 18 | `3187f7ce` | Fix zref regression + contract parity + focused tests | 26 | +552/-211 | tooling |  |
| 19 | `09ef6ccc` | Refresh external review snapshot for a0686d76 | 2 | +62/-66 | docs |  |
| 20 | `a0686d76` | Split loop-packet commands into packets package | 11 | +653/-581 | tooling |  |
| 21 | `1e54c022` | Refresh external review snapshot for 85b11941 | 2 | +58/-61 | docs |  |
| 22 | `85b11941` | Project typed plan authority and packet inbox state | 24 | +1116/-138 | tooling |  |
| 23 | `fa370be5` | Refresh external review snapshot for bc594104 | 2 | +65/-68 | docs |  |
| 24 | `bc594104` | Project plan authority readers from typed registry | 18 | +464/-93 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `0` | tooling | +0/-0 |
| `AGENTS.md` | docs | +8/-3 |
| `bridge.md` | docs | +37/-37 |
| `dev/active/MASTER_PLAN.md` | tooling | +33/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +75/-2 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1381/-1385 |
| `dev/guides/DEVELOPMENT.md` | docs | +16/-3 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +157/-0 |
| `dev/scripts/README.md` | tooling | +14/-2 |
| `dev/scripts/checks/python_analysis/cyclic_imports_graph.py` | tooling | +36/-69 |
| `dev/scripts/devctl/commands/governance/review_snapshot.py` | tooling | +47/-14 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +6/-0 |
| `dev/scripts/devctl/commands/loop_packet.py` | tooling | +8/-280 |
| `dev/scripts/devctl/commands/loop_packet_helpers.py` | tooling | +8/-215 |
| `dev/scripts/devctl/commands/packets/loop_packet.py` | tooling | +288/-0 |
| `dev/scripts/devctl/commands/packets/loop_packet_helpers.py` | tooling | +218/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py` | tooling | +34/-10 |
| `dev/scripts/devctl/context_graph/catalog_nodes.py` | tooling | +16/-2 |
| `dev/scripts/devctl/context_graph/traversal.py` | tooling | +60/-0 |
| `dev/scripts/devctl/governance/governed_doc_routing.py` | tooling | +93/-9 |
| `dev/scripts/devctl/governance_graph/mutation_bypass.py` | tooling | +35/-43 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_pipeline.py` | tooling | +5/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_review.py` | tooling | +5/-0 |
| `dev/scripts/devctl/platform/surface_state_contract_rows.py` | tooling | +4/-0 |
| `dev/scripts/devctl/probe_topology/python_modules.py` | tooling | +125/-0 |
| `dev/scripts/devctl/probe_topology/python_scan.py` | tooling | +27/-37 |
| `dev/scripts/devctl/review_channel/bridge_projection_metadata.py` | tooling | +4/-4 |
| `dev/scripts/devctl/review_channel/bridge_projection_sections.py` | tooling | +18/-9 |
| `dev/scripts/devctl/review_channel/current_session_attention.py` | tooling | +14/-14 |
| `dev/scripts/devctl/review_channel/event_projection_assembly.py` | tooling | +10/-2 |
| `dev/scripts/devctl/review_channel/event_projection_support.py` | tooling | +9/-0 |
| `dev/scripts/devctl/review_channel/event_store.py` | tooling | +59/-8 |
| `dev/scripts/devctl/review_channel/events.py` | tooling | +3/-19 |
| `dev/scripts/devctl/review_channel/plan_resolution.py` | tooling | +26/-30 |
| `dev/scripts/devctl/review_channel/projection_bundle.py` | tooling | +7/-3 |
| `dev/scripts/devctl/review_channel/promotion.py` | tooling | +14/-6 |
| `dev/scripts/devctl/review_channel/publication_ownership.py` | tooling | +164/-0 |
| `dev/scripts/devctl/review_channel/reviewer_follow.py` | tooling | +6/-6 |
| `dev/scripts/devctl/review_channel/reviewer_state.py` | tooling | +3/-4 |
| `dev/scripts/devctl/review_channel/reviewer_turn_runner.py` | tooling | +309/-14 |
| _34 more files trimmed_ | | |

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
| `ActionResult` | `governance_runtime` | `n/a` | status, reason |
| `ArtifactStore` | `governance_runtime` | `n/a` | root, managed_kinds |
| `AutoModeState` | `governance_runtime` | `n/a` | phase, next_transition |
| `CallerAuthorityPolicy` | `governance_runtime` | `n/a` | caller_id, allowed_actions |
| `CheckResult` | `governance_runtime` | `n/a` | success, total |
| `ControlPlaneReadModel` | `governance_runtime` | `n/a` | push_eligible, top_blocker |
| `ControlState` | `governance_runtime` | `n/a` | approvals, active_runs |
| `CoordinationSnapshot` | `governance_core` | `n/a` | current_slice, recommended_topology |
| `DecisionPacket` | `governance_runtime` | `n/a` | decision_mode, rule_summary |
| `FailurePacket` | `governance_runtime` | `n/a` | runner, status |
| `Finding` | `governance_runtime` | `n/a` | check_id, severity |
| `LocalServiceEndpoint` | `governance_runtime` | `n/a` | service_id, discovery_fields |
| `ProviderAdapter` | `governance_adapters` | `n/a` | provider_id, capabilities |
| `PushAuthorizationRecord` | `governance_runtime` | `n/a` | authorization_id, authorized_head_sha |
| `RemoteCommitPipelineContract` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:RemoteCommitPipelineContract` | snapshot_id, state |
| `RepoPack` | `repo_packs` | `n/a` | pack_id, policy_path |
| `ReviewCandidateRecord` | `governance_runtime` | `n/a` | candidate_id, artifact_kind |
| `ReviewState` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewState` | snapshot_id, bridge |
| `ReviewerRuntimeContract` | `governance_runtime` | `n/a` | reviewer_mode, reviewer_freshness |
| `RunRecord` | `governance_runtime` | `n/a` | run_id, status |
| `SessionCachePacket` | `governance_commands` | `n/a` | last_reviewed_sha, advisory_action |
| `TypedAction` | `governance_runtime` | `n/a` | action_id, repo_pack_id |
| `WorkflowAdapter` | `governance_adapters` | `n/a` | adapter_id, transport |

### Key documents

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`

## 6. Reviewer hints — please verify

### Targeted hints

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_sections.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_metadata.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_why.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_review_snapshot_why.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Commit d08407ca changed dev/scripts/devctl/runtime/remote_commit_pipeline_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit 3187f7ce changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit 3187f7ce changed dev/scripts/devctl/runtime/review_state_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`a9f1a42f`** — Refresh external review snapshot for d2d91aaf
- **`d2d91aaf`** — Unify commit-gate caller policy across governed + receipt paths
  - Both governed_executor_commit_phase and review_snapshot now call
  - check_commit_packet_gate() with identical load→resolve→skip→gate
  - semantics. Fixes rev_pkt_0728 finding: split caller policy where
- **`7c1562f3`** — Refresh external review snapshot for dae1df84
- **`dae1df84`** — Make reviewer turn runner governance-shaped instead of bridge-local
  - detect_reviewer_wake() and build_reviewer_turn_context() now accept
  - optional governance: ProjectGovernance parameter. When provided:
  - - bridge_path is resolved from governance.bridge_config.bridge_path
- **`b627c135`** — Unify target resolver + fail-closed on unresolved target + receipt tests
  - Addresses rev_pkt_0716 findings:
- **`4c01b779`** — Add fail-closed commit gate on pending reviewer packets
  - Shared lease-independent gate in runtime/commit_packet_gate.py blocks
  - both governed commit (commit_phase.py) and snapshot receipt-commit
  - (review_snapshot.py) when actionable reviewer packets exist.
- **`6221bc32`** — Refresh external review snapshot for f4c3a335
- **`f4c3a335`** — Fix Codex review findings: revert premature follow wiring + acked wake bug
  - 1. Revert reviewer_follow.py wiring — keep turn runner out of live
  -    follow/report path until core wake/context contract is accepted.
  - 2. Fix acked-status wake bug — only pending packets trigger reviewer
- **`26e8730a`** — Refresh external review snapshot for d08407ca
- **`4d2c991c`** — Refresh external review snapshot for d08407ca
- **`d08407ca`** — Add portable controller-owned reviewer turn runner + publication ownership
  - Cut 1: reviewer_turn_runner.py — typed contract for one bounded reviewer
  - turn without chat relay (ReviewerWakeSignal, ReviewerTurnContext,
  - ReviewerTurnResult). Builds on existing ReviewerTurnAuthority.
- **`eea5abf5`** — Refresh external review snapshot for bf0c0d90
- **`bf0c0d90`** — Fix test_implementer_stall import after event_projection restructuring
  - detect_event_implementer_stall moved from event_projection to
  - event_projection_bridge during the operator's module extraction.
  - Update test import path to match. 7/7 tests pass.
- **`0e0b3288`** — Refresh external review snapshot for 7ef603c1
- **`7ef603c1`** — Block stale bridge instruction fallback on explicit typed clear
  - bridge_projection_sections.py: when current_session explicitly contains
  - current_instruction (even if empty), do not fall back to bridge_state.
  - Only use bridge_state fallback when the key is entirely absent from
- **`9fb25fcd`** — Drop zref from snapshot hash inputs + fix bridge instruction-revision drift
  - - surface_snapshot.py: add 'zref' to drop_keys alongside 'snapshot_id' in
  -   build_surface_snapshot_id, attach_snapshot_id, and _normalize_push_decision
  -   so derived zref never creates self-referential snapshot hash drift.
- **`d2171db6`** — Refresh external review snapshot for 3187f7ce
- **`3187f7ce`** — Fix zref regression + contract parity + focused tests
  - - Safe getattr access for snapshot_id/zref on frozen review-state stubs
  -   (session_resume_support.py:299-300) — prevents AttributeError on legacy
  -   objects that lack these fields.
- **`09ef6ccc`** — Refresh external review snapshot for a0686d76
- **`a0686d76`** — Split loop-packet commands into packets package
- **`1e54c022`** — Refresh external review snapshot for 85b11941
- **`85b11941`** — Project typed plan authority and packet inbox state
- **`fa370be5`** — Refresh external review snapshot for bc594104
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`bc594104`** — Project plan authority readers from typed registry
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- architecture plan for the extracted AI-governance system under `MP-377`.
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b ev…
- 2026-04-11 remote-participant visibility follow-up in `MP-380..MP-387`
- the reopened MP-384/MP-387 F1 parity flake is now narrowed at the CLI edge
- Current 2026-04-05 reviewer-handoff closure inside that same lane: `MP-387`
- the `MP-381` field-route proof helper
- `MP-383` / `MP-381` packet-backed action-request and shared

## 8. Known gaps and open items

- open governance findings: 112

### Startup advisories
- repair_reviewer_loop: runtime_missing

### Stale warnings
- Cut a checkpoint before doing anything else.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-476bb605638c` binds this file to HEAD `a9f1a42fa797`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
