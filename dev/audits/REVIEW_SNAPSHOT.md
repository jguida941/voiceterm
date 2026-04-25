# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `f68c4ad9bd06` — Checkpoint S0 connectivity foundation + integration cleanup (rev_pkt_1843)
- Tree hash: `6c85f8e7b968`
- Generation stamp: `snap-0864527d074c`
- Generated at (UTC): 2026-04-25T14:50:30Z
- Push decision: `await_review` — review_pending_before_push
- Reviewer mode: `active_dual_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 198 files, +14856/-4824
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
- HEAD SHA: `f68c4ad9bd064399d69f8d2030df0ee354f548aa`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-25T10:50:19-04:00

## 2. Governance state

### Push decision
- action: `await_review`
- reason: review_pending_before_push
- push_eligible_now: False
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: recommended
- publication_guidance: 2 local commit(s) waiting for governed push once review is accepted.

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

Range: last 24 commits ending at `f68c4ad9bd06`

- commits: 24
- files changed: 198
- insertions: +14856
- deletions: -4824
- bundle classes touched: docs, tooling
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 20 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `f68c4ad9` | Checkpoint S0 connectivity foundation + integration cleanup… | 147 | +8481/-2967 | tooling | Parser / ANSI boundary |
| 2 | `5d1c0ccf` | Checkpoint actor-authority liveness slice (rev_pkt_1818) | 15 | +1767/-60 | tooling |  |
| 3 | `30fb4c55` | Refresh external review snapshot for 75d4bf8f | 1 | +6/-6 | docs |  |
| 4 | `75d4bf8f` | Refresh external review snapshot for 71385e9d | 2 | +71/-73 | docs |  |
| 5 | `71385e9d` | Add inactivity-watchdog to conductor wrapper (path 1 fix) | 5 | +382/-163 | tooling |  |
| 6 | `442aa2c3` | Refresh external review snapshot for 61224a5a | 1 | +1/-1 | docs |  |
| 7 | `61224a5a` | Refresh external review snapshot for eafea93b | 2 | +78/-78 | docs |  |
| 8 | `eafea93b` | Fix codex portability findings: 3.10 datetime.UTC + venv in… | 9 | +133/-107 | tooling |  |
| 9 | `411cb262` | Refresh external review snapshot for 6432db5a | 1 | +6/-6 | docs |  |
| 10 | `6432db5a` | Refresh external review snapshot for a75d0d33 | 2 | +87/-85 | docs |  |
| 11 | `a75d0d33` | Refresh external review snapshot for af4a23b3 | 1 | +5/-5 | docs |  |
| 12 | `af4a23b3` | Refresh external review snapshot for c3229f22 | 1 | +10/-10 | docs |  |
| 13 | `c3229f22` | Slice 1+2 rev 12 + install-hooks fix + code-shape modulariz… | 30 | +1579/-311 | tooling |  |
| 14 | `9d6f1eb6` | Repair review surface bootstrap contracts | 10 | +165/-74 | tooling |  |
| 15 | `e66c68e3` | Refresh external review snapshot for 68dbe112 | 1 | +1/-1 | docs |  |
| 16 | `68dbe112` | Refresh external review snapshot for e7211799 | 2 | +64/-64 | docs |  |
| 17 | `e7211799` | chore(push): auto-commit preflight-generated changes | 11 | +202/-90 | tooling |  |
| 18 | `e3ebc4ef` | Refresh external review snapshot for 653beda0 | 1 | +3/-3 | docs |  |
| 19 | `653beda0` | chore(push): auto-commit preflight-generated changes | 1 | +79/-74 | tooling |  |
| 20 | `4ba95539` | Route remote-control staging handoffs | 28 | +1094/-439 | tooling |  |
| 21 | `cf61d131` | Refresh external review snapshot for ddafb608 | 1 | +1/-1 | docs |  |
| 22 | `ddafb608` | Refresh external review snapshot for 415674d0 | 2 | +66/-66 | docs |  |
| 23 | `415674d0` | Add managed projection receipt push cleanup | 14 | +500/-70 | tooling |  |
| 24 | `fd11a448` | Refresh external review snapshot for 0ec1b679 | 2 | +75/-70 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +15/-5 |
| `bridge.md` | docs | +82/-80 |
| `dev/active/MASTER_PLAN.md` | tooling | +67/-7 |
| `dev/active/ai_governance_platform.md` | tooling | +94/-10 |
| `dev/active/remote_commit_pipeline.md` | tooling | +18/-1 |
| `dev/active/remote_control_runtime.md` | tooling | +7/-2 |
| `dev/active/review_channel.md` | tooling | +10/-0 |
| `dev/audits/AUTOMATION_DEBT_REGISTER.md` | tooling | +3/-3 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1053/-1039 |
| `dev/config/devctl_repo_policy.json` | tooling | +16/-0 |
| `dev/config/git_hooks/post-commit-review-snapshot.sh` | tooling | +18/-3 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +23/-8 |
| `dev/config/git_hooks/pre-push-governed-push.sh` | tooling | +19/-3 |
| `dev/guides/DEVELOPMENT.md` | docs | +41/-15 |
| `dev/guides/SYSTEM_MAP.md` | docs | +74/-11 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +249/-3 |
| `dev/scripts/README.md` | tooling | +71/-27 |
| `dev/scripts/checks/code_shape/code_shape_policy.py` | tooling | +4/-6 |
| `dev/scripts/checks/package_layout/instruction_surface_sync.py` | tooling | +1/-1 |
| `dev/scripts/checks/platform_contract_closure/emitter_parity_contract_checks.py` | tooling | +17/-10 |
| `dev/scripts/checks/platform_contract_closure/field_routes.py` | tooling | +16/-31 |
| `dev/scripts/checks/platform_contract_closure/field_routes_control_plane.py` | tooling | +203/-0 |
| `dev/scripts/checks/platform_contract_closure/field_routes_surface_state.py` | tooling | +0/-182 |
| `dev/scripts/checks/platform_contract_closure/support.py` | tooling | +6/-0 |
| `dev/scripts/checks/platform_contract_closure/typed_state_writer_authority.py` | tooling | +268/-0 |
| `dev/scripts/checks/review_channel_bridge/report.py` | tooling | +9/-5 |
| `dev/scripts/checks/review_surface_consistency/parity.py` | tooling | +34/-0 |
| `dev/scripts/checks/review_surface_consistency/proof_tick.py` | tooling | +0/-2 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +9/-1 |
| `dev/scripts/devctl/cli_parser/pipeline.py` | tooling | +5/-4 |
| `dev/scripts/devctl/commands/governance/install_git_hooks.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/governance/install_git_hooks_support.py` | tooling | +31/-1 |
| `dev/scripts/devctl/commands/governance/session_resume_authority_payload.py` | tooling | +6/-3 |
| `dev/scripts/devctl/commands/governance/session_resume_cache_packet_builder.py` | tooling | +123/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_packet.py` | tooling | +7/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_render.py` | tooling | +28/-129 |
| `dev/scripts/devctl/commands/governance/session_resume_render_role_sections.py` | tooling | +253/-8 |
| `dev/scripts/devctl/commands/governance/session_resume_render_sections.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_source_helpers.py` | tooling | +26/-12 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +135/-142 |
| _158 more files trimmed_ | | |

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

- **risk**: Parser / ANSI boundary — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actions.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_targets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_metadata.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_parser.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actor_authority.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/governance/doc_authority_models.py`) — Commit f68c4ad9 changed dev/scripts/devctl/governance/doc_authority_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/connectivity_registry_models.py`) — Commit f68c4ad9 changed dev/scripts/devctl/platform/connectivity_registry_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit f68c4ad9 changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/system_map_models.py`) — Commit f68c4ad9 changed dev/scripts/devctl/platform/system_map_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/ack_contract.py`) — Commit f68c4ad9 changed dev/scripts/devctl/review_channel/ack_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/pending_packet_models.py`) — Commit f68c4ad9 changed dev/scripts/devctl/review_channel/pending_packet_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Commit f68c4ad9 changed dev/scripts/devctl/review_channel/reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/pipeline_auto_recovery_contracts.py`) — Commit f68c4ad9 changed dev/scripts/devctl/runtime/pipeline_auto_recovery_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Commit f68c4ad9 changed dev/scripts/devctl/runtime/remote_commit_pipeline_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_collaboration_models.py`) — Commit f68c4ad9 changed dev/scripts/devctl/runtime/review_state_collaboration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit f68c4ad9 changed dev/scripts/devctl/runtime/review_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/review_channel/test_ack_contract.py`) — Commit f68c4ad9 changed dev/scripts/devctl/tests/review_channel/test_ack_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_pipeline_auto_recovery_contracts.py`) — Commit f68c4ad9 changed dev/scripts/devctl/tests/runtime/test_pipeline_auto_recovery_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit 4ba95539 changed dev/scripts/devctl/review_channel/packet_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`f68c4ad9`** — Checkpoint S0 connectivity foundation + integration cleanup (rev_pkt_1843)
  - Broader scope than rev_pkt_1831 P1-P3 plan: stashing unstaged-only work proved
  - infeasible due to closed-import-graph requirements (S0 connectivity registry,
  - S1 writer-authority guard, S0 pipeline auto-recovery support files have inter-
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-0864527d074c` binds this file to HEAD `f68c4ad9bd06`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
