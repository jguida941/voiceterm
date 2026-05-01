# Agents

This file is the canonical SDLC, release, and AI execution policy for this repo.
If any process docs conflict, follow `AGENTS.md` first.

## Purpose

VoiceTerm is a polished, voice-first overlay for AI CLIs.
Primary support: **Codex** and **Claude Code**.
Gemini CLI remains experimental.

Goal of this file: give agents one repeatable process so every task follows the
same execution path with minimal ambiguity.

Architectural scope rule: this repo contains the VoiceTerm product, but the
active platform target is the portable AI-governance system tracked under
`MP-377`. Treat VoiceTerm as a first-party adopter/client of that platform,
not the hidden default authority for shared runtime, startup, review-channel,
or governance layers. New shared code, prompts, guards, and docs must resolve
repo-local behavior through `ProjectGovernance`, repo-pack policy, and typed
runtime contracts rather than VoiceTerm-specific literals.

Portable-platform rule:
- The product direction under `MP-377` is a reusable AI-governance platform
  that should work across arbitrary repositories. VoiceTerm is the first
  client/integration layer, not the hidden default authority for portable
  runtime/tooling code. In portable layers, do not hardcode VoiceTerm repo
  names, fixed `dev/active/*` / `dev/reports/*` paths, `bridge.md`, or
  `VOICETERM_PATH_CONFIG` fallbacks as universal truth; resolve authority
  through `ProjectGovernance` / repo-pack state or fail closed.
- Generated bootstrap/instruction surfaces must render that same boundary
  explicitly: the current repo is a first-party client/product integration
  over the portable governance platform, while repo packs and typed runtime
  contracts remain backend authority for arbitrary repos.
- Review-channel launch surfaces must treat the markdown lane table as planned
  topology only. The runtime participant registry is provider/session-backed
  typed state, and the default requested worker fanout is zero unless a launch
  explicitly requests more. `bridge.md` stays a compatibility projection until
  native `CollaborationSession` / worker-topology authority lands, and any
  repo-owned bridge repair/write path must recover blank `Last Codex poll`
  metadata from typed bridge state plus normalize fractional-second typed poll
  timestamps back to the canonical whole-second bridge format before
  `check_review_channel_bridge.py` or governed push can trust the projection.
  Event-backed review-channel projections must not let detached daemon
  lifecycle rows override an explicit reviewer-owned bridge mode; prefer the
  fresh bridge snapshot, ignore stopped daemon mode hints, and treat a fresh
  reviewer heartbeat/checkpoint as the source that updates typed
  `current_session` state rather than reverse-reprojecting stale session state
  back into `bridge.md`.
  The same contract applies to prepared launch authority after launch:
  remote-control continuity must be derived from typed governance/review-state
  evidence rather than launcher env vars alone, so receipt commits do not make
  different runtime readers disagree about whether the loop is still valid.
  When typed liveness proves an attached remote-control provider, status/doctor
  recovery commands must stay headless (`--terminal none`), and launch/recover
  paths must fail closed before any local Terminal.app prompt or profile lookup
  that the remote operator cannot see.
- Collaboration-role posture must also stay on typed runtime authority:
  `CollaborationSession` / `AuthoritySnapshot` decide mutation, verification,
  and watcher/dashboard ownership. `devctl dogfood` remains development-only
  evidence capture layered on top of that runtime truth; it is not the
  universal role-selection mode for arbitrary repos.
  Mutation authority is identity-bound: consumers should prefer
  `CollaborationSession.actor_authorities` / `AuthoritySnapshot.actor_authorities`
  grants such as `repo.commit` and `repo.stage` over reviewer-mode labels, and
  keep `approval.commit` separate from repo mutation authority.
  `SessionPosture` is the canonical proof-tick producer for
  `interaction_mode`, `reviewer_mode`, and `actors[].occupied_lane`.
  Status, startup, dashboard, and bootstrap renderers must consume that
  posture instead of recomputing contradictory mode/role/lane values; capability
  grants such as `repo.commit` may appear on an actor without changing the
  current occupied lane. When `SessionPosture.interaction_mode` is
  `remote_control`, fresh bootstrap/routing text must state that local
  GUI/process intervention, ad hoc kill commands, and local commit/push
  authority are unavailable; privileged, commit, and push work routes through
  typed `action_request` packets or bounded repo commands.
  Dashboard and control-plane readers must thread repo governance plus the
  current typed `ReviewState` through `ControlPlaneReadModel` rather than
  reloading an independent bridge snapshot, and conductor liveness may only be
  promoted from typed bridge/posture evidence bounded by fresh poll/session
  state.
- Worktree-orphan prevention is part of the same portable runtime contract.
  Dirty/unpublished work must not be proven only for the current checkout.
  The durable model is a report-first `OrphanInventoryReport` feeding a typed
  `OrphanSnapshot` plus `CheckoutInventory`, `WorkPublicationLedger`,
  `SessionLease`, `WorktreeBaseline`, and `OrphanReconciliationDecision`
  family that can represent the current checkout, registered worktrees,
  planned delegated worker roots, unregistered sibling clones, deep-scan
  repos, prunable/missing worktrees, stashes, CI roots, and latent state.
  `python3 dev/scripts/devctl.py orphan-inventory --format md` is the bounded
  report-only scan for this evidence; add `--repo-path <path>` only for external
  pilot proof, and never fire launch, push, or fanout gates until gates consume it.
  `compute_orphan_snapshot()` is the read-side projection over that report:
  startup-context emits it as typed `orphan_snapshot` evidence, while governed
  commit/push preflight may only consume it as advisory warning state until
  the executor and gate slices land.
  These contracts live under
  `dev/scripts/devctl/runtime/worktree_orphan_*` and are registered in the
  platform `ContractSpec` surface; future launch/push/fanout gates must use
  that typed inventory/reconciliation trail rather than treating chat memory,
  `git worktree list` alone, or the active `bridge.md` projection as sufficient
  evidence.

Documentation-boundary rule:
- Keep VoiceTerm product docs (`README.md`, `QUICK_START.md`, `guides/*`)
  user-facing. Shared governance/runtime/AI authority rules belong in
  maintainer docs (`AGENTS.md`, `dev/guides/DEVELOPMENT.md`,
  `dev/scripts/README.md`, `dev/history/ENGINEERING_EVOLUTION.md`), active
  `MP-377` owner docs, or generated repo-pack/bootstrap surfaces. When a
  tooling/process/governance change triggers maintainer-doc updates, do not
  satisfy that requirement by editing product docs unless shipped end-user
  VoiceTerm behavior changed too.
- Operator-side memory files are short-term continuity only. They may carry
  recent packet ids, current HEADs, cadence preferences, or session notes, but
  they are not load-bearing architectural authority. If an AI/process rule,
  runtime invariant, or governance pattern needs to persist, encode it in the
  codebase through `AGENTS.md`, maintainer docs, active `MP-377` owner docs,
  repo-pack policy, typed contracts, or guards. Do not create or update memory
  markdown as the durable home for architecture rules.

Shared-backlog rule:
- `backlog.md` is the repo-visible shared backlog surface for humans and AI.
  It may appear in governed startup/work-intake warm refs and writeback
  sinks, but it is not active execution authority. Promote items into
  `dev/active/MASTER_PLAN.md` plus the owning active plan before treating
  them as in-flight work. Keep local-only scratch backlog in
  `dev/deferred/LOCAL_BACKLOG.md`.

Package-layout truth rule:
- Treat `check_package_layout.py` as a two-layer self-hosting signal: blocking
  violations still decide command failure, but freeze-mode crowded roots or
  namespace families are still active organization debt and must not be
  described as structurally clean. Maintain the explicit report state
  (`status`, `layout_clean`, `baseline_layout_debt_detected`) so the repo does
  not confuse "no new drift in this edit" with "the layout is healthy." The
  same guard now also emits advisory organization-role state
  (`organization_review_clean`, `organization_role_debt_detected`) so a root
  can still report helper-drawer debt even when current crowding budgets stay
  green. When compatibility shims carry `shim-target`, keep the emitted
  `compatibility_redirects` map truthful too so agents can see where moved
  entrypoints now resolve without guessing from stale paths. When
  `--fail-on-baseline-debt` is scoped with `--baseline-debt-root`, dirty
  working-tree and commit-range runs should only hard-fail when the current
  diff touches one of those selected roots; clean-worktree and adoption-scan
  runs still enforce the targeted roots globally so release/self-hosting truth
  does not silently degrade.
- If a documented root helper wrapper is intended to remain a stable public
  seam after package extraction, declare it in repo policy
  `probe_compatibility_shims.allowed_public_shims` in the same change.
  Package-README prose alone is not enough; otherwise adoption-scan will keep
  classifying that wrapper as temporary shim debt and surface stale
  `remove-now` guidance.
- When decomposing a crowded flat root or namespace family, keep required
  compatibility files as explicit thin shims only. Accepted shim shapes include
  direct re-export wrappers and module-alias wrappers that preserve stable
  import/patch paths, but they must stay metadata-bearing, auditable, and small
  enough for package-layout validation to count them as compatibility seams
  rather than fresh implementation growth.
- When a public `dev/scripts/checks/check_*.py`, `probe_*.py`, or `run_*.py`
  entrypoint moves behind a package seam, keep the legacy root shim executable
  in direct script mode as well as import/package mode. Treat that shim path as
  part of the contract and rerun the root entrypoint plus the owning bundle
  before handoff so package-only unit coverage does not hide broken script
  imports. That same contract includes repo-package imports such as
  `dev.scripts.checks.<shim>` too; a shim that only works when
  `dev/scripts/checks` happens to be on `sys.path` is still broken.
- When adding or promoting a public `dev/scripts/checks/check_*.py`,
  `probe_*.py`, or `run_*.py` entrypoint, land the self-hosting closure in the
  same change: register the script catalog row, wire a typed quality-policy or
  direct bundle/workflow enforcement lane (or explicit exemption), update the
  maintainer docs, and keep `check_guard_enforcement_inventory.py` plus
  `check_bundle_workflow_parity.py` green.

Top-level enforcement rule: every time an agent creates a file or edits an
existing file, it must run the relevant repo guard/check scripts before
handoff to catch bad practices, policy drift, and structural regressions. This
is mandatory even for small patches. At minimum, run the task-class bundle plus
any touched risk-matrix add-ons, then follow the concrete post-edit check
inventory in `dev/guides/DEVELOPMENT.md` (`What checks protect us` and
`After file edits`).

Direct post-edit enforcement link:
- After every file create/edit, follow
  `dev/guides/DEVELOPMENT.md#after-file-edits` before handoff.

Release-governance note:
- When preparing a release, treat `bundle.release` as the blocking source of
  truth and make sure maintainer docs (`AGENTS.md`,
  `dev/guides/DEVELOPMENT.md`, `dev/active/MASTER_PLAN.md`,
  `dev/history/ENGINEERING_EVOLUTION.md`) plus canonical user docs
  (`README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`,
  `guides/INSTALL.md`, `guides/TROUBLESHOOTING.md`) reflect the shipped
  behavior. Recent control-plane/mobile changes also require the
  `check_mobile_relay_protocol.py` guard to stay green in runtime and release
  bundles.

## Source-of-truth map

| Question | Canonical source |
|---|---|
| What are we executing now? | `dev/active/MASTER_PLAN.md` |
| What active docs exist and what role does each play? | `dev/active/INDEX.md` |
| Where is active-doc execution authority vs reference-only scope defined? | `dev/active/INDEX.md` (`Role`, `Execution authority`, `When agents read`) |
| Where is consolidated Theme Studio + overlay visual planning context? | `dev/active/theme_upgrade.md` |
| Where is long-range phase-2 research context? | `dev/deferred/phase2.md` (bridge at `dev/active/phase2.md`) |
| Where is the `devctl` reporting + CIHub integration roadmap? | `dev/active/devctl_reporting_upgrade.md` |
| Where is the autonomous loop + mobile control-plane execution spec? | `dev/active/autonomous_control_plane.md` |
| Where is the shared review-channel + dual-agent shared-screen execution plan? | `dev/active/review_channel.md` |
| Where is the host-process hygiene + Activity Monitor automation plan? | `dev/active/host_process_hygiene.md` |
| Where is the continuous local Codex-reviewer / Claude-coder loop hardening and later template-extraction plan? | `dev/active/continuous_swarm.md` |
| Where is the bounded loop-v2 convergence plan that composes startup/work-intake, planning, auto-mode, monitor, graph discovery, and guard-promotion into one autonomous controller? | `dev/active/autonomous_governance_loop_v2.md` (subordinate `MP-377` execution spec; read after `dev/active/ai_governance_platform.md` and `dev/active/platform_authority_loop.md`) |
| Where is the optional VoiceTerm Operator Console plan? | `dev/active/operator_console.md` |
| Where is the typed remote-session commit/push pipeline design for phone-steered sessions, including worktree-bound approval for worker vs control lanes? | `dev/active/remote_commit_pipeline.md` |
| Where is the primary read-only review-channel readiness surface for that remote commit/push lane documented? | `dev/scripts/README.md` (`review-channel --action doctor`) for command semantics, plus `dev/active/remote_commit_pipeline.md` for lifecycle authority |
| Where is the typed review-channel approval-packet vocabulary for that remote commit/push lane documented? | `dev/active/remote_commit_pipeline.md` for contract semantics, plus `dev/scripts/README.md` for `review-channel --action post --kind commit_approval` flag usage |
| Where is the operator-facing read-only packet queue surface for that same typed lane documented? | `dev/scripts/README.md` for `review-channel --action operator-inbox` semantics, plus `dev/active/review_channel.md` for the review-channel contract that keeps operator reads on the existing packet transport without mutating delivery receipts |
| Where is portable typed master-plan authority, ingestion, and explain-back documented? | `dev/scripts/devctl/runtime/master_plan_contract.py` for `MasterPlan` / `PlanRow` / `LinkedDoc` / `PlanProposal` / `ExplainBackReceipt`, `dev/scripts/devctl/runtime/master_plan_parse.py` for coercion from repo-pack JSON, `dev/scripts/devctl/governance/master_plan_ingestion.py` for repo-agnostic markdown/prose ingestion adapters, `dev/scripts/devctl/runtime/master_plan_store.py` for the JSONL authority store, and `ProjectGovernance.master_plan` for repo-pack path authority. VoiceTerm currently projects that authority through `dev/active/MASTER_PLAN.md` and the default typed store `dev/state/plan_index.jsonl`; portable layers must resolve these paths through governance instead of hardcoding them. |
| Where is the typed review-packet lifecycle/disposition surface documented? | `dev/scripts/README.md` for `review-channel --action history --include-outcomes` and evidence-bound `review-channel --action apply` semantics, `dev/scripts/devctl/review_channel/packet_lifecycle.py` for `PacketLifecycleHistory` / `PacketDisposition`, `dev/scripts/devctl/review_channel/packet_attestation.py` for `PacketGuardAttestation`, `dev/scripts/devctl/review_channel/packet_plan_integration.py` for plan-target apply rows, `dev/scripts/devctl/review_channel/packet_outcomes.py` for the bounded `PacketOutcomeLedger` classifier, and `dev/active/ai_governance_platform.md` `MP377-P0-T08A..T08E` for the plan-integrated deferred queue. Clock-expired pending packets must classify as archived audit rows, not silently lost live intent, and `packet_applied` work claims must carry matching guard/run/action evidence rather than relying on ACK state. |
| Where is the packet-backed bridge Action Requests contract documented? | `dev/active/remote_control_runtime.md` for lifecycle authority, plus `dev/scripts/README.md` for `review-channel --action post --kind action_request` runtime-binding flag usage |
| Where is the 2026-04-29 typed runtime-authority evidence closure for action requests documented? | `dev/scripts/devctl/review_channel/events.py::_runtime_authority_evidence_for_request` attaches `ActionRequestRuntimeAuthorityEvidence` on executable packet posts, while `dev/scripts/devctl/commands/vcs/commit_action_request_authority.py` and `commit_action_request_evidence.py` derive missing caller role, target actor identity, capability, live pipeline generation, and staged snapshot facts from typed state only; see `dev/scripts/README.md` and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-29 entry "Action-request checkpoint authority now derives missing evidence from typed state". |
| Where is the 2026-04-23 remote-control pre-pipeline commit staging handoff documented (`git_index_write_blocked` becomes `requested_action=stage_commit_pipeline` to the attached provider instead of a local prompt)? | `dev/active/remote_commit_pipeline.md` and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-23 entry "Remote-control commit staging now hands sandbox prompts to Claude"; runtime behavior lives in `dev/scripts/devctl/commands/vcs/commit_preflight_validators.py`, `dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py`, `dev/scripts/devctl/commands/vcs/governed_executor_packets.py`, and `dev/scripts/devctl/review_channel/packet_contract.py`. |
| Where is the action-request-first priority selection + `current_session.current_instruction` control-path integration documented? | `dev/scripts/devctl/review_channel/packet_control_loop.py` for the `select_priority_pending_packet` + `action_request_control_state` implementation, plus `dev/history/ENGINEERING_EVOLUTION.md` entry on the priority selector feeding `current_session.current_instruction` |
| Which modules own remote-control reviewer wake, dashboard conductor liveness without a PID, and `pending_action_requests` truth? | `dev/scripts/devctl/review_channel/follow_controller.py::maybe_wake_waiting_reviewer_conductor` orchestrates the bounded reviewer wake, `dev/scripts/devctl/review_channel/reviewer_follow_guard.py` owns the reusable launch/runtime helpers, `dev/scripts/devctl/runtime/control_plane_resolve.py::resolve_pending_packets` counts only live pending `kind="action_request"` packets, and `dev/scripts/devctl/commands/dashboard_render/{terminal,markdown}.py` keep repo-owned conductor rows in `RUNNING` when typed session state says `alive=true` even if `pid` is unavailable. |
| Where is the remote-control reviewer/runtime closure plan for typed operator mode, packet-backed action requests, dashboard convergence, and auto-polling? | `dev/active/remote_control_runtime.md` (subordinate `MP-377` execution spec; read after `dev/active/remote_commit_pipeline.md`) |
| Where is the 2026-04-09 F1/F2/F3 reviewer-follow-up closure documented (`devctl commit` remote-control approval boundary restored, `process_sweep` supervisor-backed liveness fallback, and `rollout-tail` Claude auto-discovery narrowed)? | `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-09 entry "Remote-control commit now waits for typed approval; process_sweep and rollout-tail narrow their trust boundaries" |
| Where is the 2026-04-20 headless-remote-control approval-mode auto-elevation + inbox-drain prompt + typed conductor stall diagnostics documented? | `dev/scripts/devctl/approval_mode.py::auto_elevated_approval_mode` for the shared elevation helper, `dev/scripts/devctl/review_channel/prompt.py` for the post-bootstrap inbox-drain section, `dev/scripts/devctl/review_channel/stall_diagnostics.py` for the typed `ConductorStallDiagnosis` reader, plus `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-20 entry "Headless remote-control launches auto-elevate approval-mode and conductor stalls become typed" |
| Where is the 2026-04-20 reviewer-wake auto-elevation closure + payload-shape stall diagnostic follow-up documented? | `dev/scripts/devctl/review_channel/reviewer_follow_guard.py::_resolved_wake_approval_mode` for the reviewer-wake elevation seam, `dev/scripts/devctl/review_channel/stall_diagnostics.py` for the payload-nested rollout parsing + escalation-deadlock gate fix, plus `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-20 entry "Reviewer-wake auto-elevation closure plus payload-shape stall diagnostics". The 2026-04-21 `rev_pkt_1529` follow-up in the same diagnostic keeps explicit replacement-session evidence ahead of stale escalation-deadlock classification so relaunched conductors stop surfacing as wedged. |
| Where is the 2026-04-10 P1/P2 reviewer-follow-up closure documented (`pipeline refresh-authorization` stale-HEAD refusal and `agent-mind --since-cursor` non-lossy rollout polling)? | `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-10 entry "Pipeline refresh and agent-mind cursor polling now fail closed on stale authority" |
| Where is the 2026-04-10 Q47/Q45/Q43 deterministic action-routing closure documented (`startup-context` action routing, typed `agent_lane`, and `devctl commit` `CommitPermissionDecision` hard block on `implementation_permission`)? | `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-10 entry "Startup action routing and commit permission now make blocked implementation authority explicit" |
| Where is the 2026-04-10 Q40/Q42 lane-edit and destructive-recovery authority closure documented (`lane_edit_gate`, `recovery_action`, `recovery_basis`, and `recovery_scope`)? | `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-10 entry "Lane edit gates and destructive recovery now require typed startup authority" |
| Where is the 2026-04-15 governed publication closure documented (`devctl commit` `operator_approval_pending` short-circuit plus ReviewSnapshot receipt commits that may refresh `bridge.md` as well as `REVIEW_SNAPSHOT.md`)? | `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-15 entry "Governed commit approval windows and ReviewSnapshot receipt commits now stay bound to the parent code state" |
| Where is the 2026-04-18 remote-control delegated commit-approval closure documented (governed `devctl commit` auto-satisfies approval only when typed runtime proves an active operator-role `remote_control_attachment`)? | `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-18 entry "Remote-control operator delegation now auto-satisfies governed commit approval when typed runtime proves the operator role" |
| Where is the 2026-04-18 staged-intent commit/push closure documented (`devctl push` ignores staged-only next-commit content, governed stage fails closed if ReviewSnapshot refresh drops user-staged paths, and commit reports distinguish content vs receipt SHA)? | `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-18 entry "Governed commit/push now preserve staged intent and separate receipt reporting from content commits" |
| Where is the 2026-04-17 commit/push next-command convergence closure documented (same-HEAD active pipeline blocks auto-refresh authorization, commit preflight emits exact next commands, and commit permission reports project recovery fields at top level)? | `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-17 entry "Active commit/push pipeline blocks now self-heal same-HEAD authorization and project exact next commands" |
| Where is the 2026-04-22 stale-pipeline auto-recovery closure documented (`devctl pipeline --action auto-recover` classifies abandon/recover/refresh/no-op/ambiguous and writes `PipelineAutoRecoveryReceipt`)? | `dev/scripts/devctl/commands/pipeline/auto_recover_action.py` and `dev/scripts/devctl/commands/pipeline/auto_recover_result.py` for runtime behavior, `dev/scripts/devctl/runtime/pipeline_auto_recovery_contracts.py` for typed contracts, plus `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-22 entry "Pipeline auto-recover removes stale-pipeline manual selection" |
| Where is the 2026-04-23 ADR-008 governed projection cleanup closure documented (`devctl push` commits bridge-only managed projection drift as a receipt before publication, and pipeline status treats that receipt HEAD as managed movement)? | `dev/scripts/devctl/commands/vcs/push_projection_receipt.py` for the narrow receipt helper, `dev/scripts/devctl/runtime/review_snapshot_refresh.py` for bridge-only receipt recognition, `dev/scripts/devctl/commands/pipeline/head_movement.py` / `status_action.py` for receipt-aware pipeline HEAD movement, and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-23 entries "Governed push now receipts managed bridge projection drift before publication" and "Pipeline status now distinguishes managed receipt HEAD movement" |
| Where is the 2026-04-26 governed-push receipt-chain closure documented (`devctl push`, pipeline status, startup push state, push authorization, and ReviewSnapshot freshness all accept contiguous managed bridge/ReviewSnapshot receipt commits above the authorized content commit and refresh typed projection bundles after receipt movement)? | `dev/scripts/devctl/runtime/review_snapshot_refresh.py` for receipt-chain detection, `dev/scripts/devctl/runtime/push_authorization.py` / `dev/scripts/devctl/governance/push_state_authorization.py` for authorization matching, `dev/scripts/checks/review_snapshot_freshness/command.py` for freshness-chain acceptance, `dev/scripts/devctl/commands/vcs/push_preflight_projection.py` for post-receipt projection and snapshot receipt refresh, and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-26 entry "Governed push accepts managed receipt chains before publication" |
| Where is the 2026-04-27 governed-push generated-surface receipt closure documented (`devctl push` runs `render-surfaces --write` before routed preflight, commits tracked non-local repo-pack surfaces such as `AGENTS.md` / `SYSTEM_MAP.md` as a managed receipt, and keeps staged-only intent out of that receipt)? | `dev/scripts/devctl/commands/vcs/push_preflight_projection.py` for preflight orchestration, `push_render_surface_sync.py` for the `render-surfaces --write` phase, `push_projection_runtime_refresh.py` for post-receipt proof refresh, `push_preflight_commit.py` / `push_projection_receipt.py` for pathscoped receipt commits that preserve staged-only intent, `dev/scripts/devctl/runtime/review_snapshot_refresh.py` for receipt-chain acceptance of policy-owned generated surfaces, and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-27 entry "Governed push receipts policy-owned generated surfaces before docs gates" |
| Where is the 2026-04-27 startup push-state managed-receipt classification closure documented (`push_enforcement` excludes the same bridge/ReviewSnapshot receipt artifacts as governed push and reports source-vs-managed-receipt ahead counts)? | `dev/scripts/devctl/governance/push_state.py` for push-state projection, `dev/scripts/devctl/governance/push_state_receipts.py` for managed receipt dirty-path and ahead-count classification, `dev/scripts/devctl/runtime/review_snapshot_refresh.py` for the shared receipt classifier, `dev/scripts/devctl/runtime/project_governance_push.py` / `project_governance_push_ahead.py` for the typed `PushEnforcement` fields, and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-27 entry "Startup push-state now shares governed receipt projection classification" |
| Where is the 2026-04-27 governed-push typed `next=` recovery-loop automation documented (`pre_validation_recovery_loop_repair` consumes bounded startup-context review-loop repair commands instead of making AI/operators run them manually)? | `dev/scripts/devctl/commands/vcs/push_recovery_loop_repair.py` for the bounded `vcs.recovery_loop_repair` phase, `push_projection_runtime_refresh.py` / `push_preflight_projection.py` for managed-receipt deferral into that phase, `push.py` / `push_report.py` / `governed_executor_push_result.py` for push phase/report wiring, and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-27 entry "Governed push now auto-runs bounded startup next recovery" |
| Where is the 2026-04-28 completed-handoff session-outcome closure documented (`stage_commit_pipeline` with full guard evidence emits `AgentSessionOutcome(outcome=completed_handoff)`, `CollaborationSession.session_outcomes` projects it, and governed push waives reviewer-loop repair only when the receipt matches the current prepared session or the metadata-free same-head / full managed-receipt source chain back to the handoff parent)? | `dev/scripts/devctl/runtime/agent_session_outcome.py` for the typed contract, `dev/scripts/devctl/review_channel/agent_session_outcome_events.py` / `events.py` for event emission, `dev/scripts/devctl/review_channel/collaboration_session.py` for projection, `dev/scripts/devctl/commands/vcs/push_recovery_loop_repair.py` / `push_recovery_loop_handoff.py` for the guarded bypass, receipt-chain traversal, and 180-second repair budget, plus `dev/active/ai_governance_platform.md` `MP377-P0-T20` and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-28 entry "Governed push now treats completed handoff as typed session outcome" |
| Where is the 2026-04-28 hook-time generated-surface receipt extension documented (`DEVCTL_MANAGED_PROJECTION_RECEIPT_COMMIT=1` lets the pre-commit hook consume completed-handoff authority only for staged managed projection receipts, while source commits and stale/mismatched handoffs still fail closed)? | `dev/scripts/devctl/runtime/commit_permission_hook.py` for hook-time gating, `dev/scripts/devctl/commands/vcs/push_preflight_commit.py` for the generated-surface receipt marker, `dev/scripts/devctl/runtime/completed_handoff_authority.py` for source-chain handoff target resolution, `dev/scripts/devctl/runtime/review_snapshot_refresh.py` for managed receipt path classification, plus `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-28 entry "Completed-handoff publication authority now reaches hook-time generated receipts" |
| Where is the 2026-04-28 DashboardSnapshot v3 / typed-next / bridge-freshness closure documented (`dashboard --follow`, `claude-loop`, mobile/Operator Console v3 consumption, typed `last_codex_poll_*` + `ack_freshness_authority`, and safe system-to-Claude `stage_commit_pipeline` auto-apply/dedupe)? | `dev/scripts/devctl/runtime/dashboard_snapshot_authority.py` for the shared `DashboardSnapshot` v3 contract, `dev/scripts/checks/review_channel_bridge/report.py` / `dev/scripts/devctl/review_channel/bridge_validation.py` for typed bridge freshness and ACK checks, `dev/scripts/devctl/review_channel/events.py` plus `dev/scripts/devctl/commands/vcs/governed_executor_packets.py` / `governed_executor_commit_runtime.py` for safe auto-apply and dedupe, `dev/scripts/devctl/commands/reporting/claude_loop.py` for the read-only loop surface, and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-28 entry "DashboardSnapshot v3 and typed bridge freshness unblock push-v14 gates" |
| Where is the 2026-04-27 governed-push stale reviewer-heartbeat self-heal documented (`devctl push` auto-runs one bounded `reviewer-heartbeat` before routed preflight when active dual-agent `Last Codex poll` is older than the bridge freshness threshold)? | `dev/scripts/devctl/commands/vcs/push_projection_runtime_refresh.py::refresh_stale_reviewer_heartbeat_before_publication` for the typed bridge-liveness read and one-shot heartbeat action, `dev/scripts/devctl/commands/vcs/push_preflight_projection.py` for pre-validation phase wiring, and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-27 entry "Governed push now refreshes stale reviewer heartbeat before preflight" |
| Where is the 2026-04-27 governed-push execution-truth invariant documented (`vcs.push` branch identity comes from live git, approved target identity comes from live authorization, and `published_remote` requires subprocess plus remote-ref proof)? | `dev/scripts/devctl/commands/vcs/push.py` for live branch and approved-target binding, `push_findings.py` for `BranchIdentityViolation` / `ApprovedTargetIdentityViolation`, `push_flow.py` for post-push remote-ref proof, `push_snapshot.py` / `governed_executor_push_result.py` for `SilentPushFailure` report downgrades, and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-27 entry "Governed push reports now require live branch and remote proof" |
| Where is the 2026-04-28 governed-push stage-aware execution-truth closure documented (`published_remote` in-flight snapshots require fetch/preflight/push plus remote-ref proof, while terminal post-push states require `post_push_steps`, and root report booleans mirror `push_stages`)? | `dev/scripts/devctl/commands/vcs/push_snapshot.py` for stage-aware `SilentPushFailure` enforcement, `dev/scripts/devctl/commands/vcs/push_report.py` for root `published_remote` / `post_push_green` serialization, `dev/scripts/devctl/tests/vcs/test_push_report_does_not_lie_about_remote_state.py` and `test_push_report.py` for regressions, plus `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-28 entry "Governed push execution-truth now distinguishes in-flight publication from terminal post-push evidence" |
| Where is the 2026-04-28 governed-commit explicit path-selection closure documented (`devctl commit --paths ...` feeds the existing `vcs.stage` selected-path action so remote-control lanes no longer need raw `git add` to stage real work)? | `dev/scripts/devctl/commands/vcs/parser.py` for the CLI flag, `dev/scripts/devctl/commands/vcs/commit_preflight_validators.py` for the path-scoped `vcs.stage` handoff, `dev/scripts/devctl/commands/vcs/governed_executor_phases.py` / `governed_executor_stage_index.py` for selected-path staging and dirty-outside-scope enforcement, `dev/scripts/devctl/tests/vcs/test_commit_gate.py` for regressions, plus `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-28 entry "Governed commit now accepts explicit path-scoped staging" |
| Where is the 2026-04-28 Plan 4.1 dogfood cleanup closure documented (effective reviewer-mode projection, typed packet queue counts, delivery-receipt exclusion, post idempotency, uniform packet-kind schema, context-graph bootstrap wording, tandem dry-run rendering, mutation shim import compatibility, process-sweep opt-in, and unresolved session outcomes)? | `dev/scripts/devctl/review_channel/bridge_projection_metadata.py` / `bridge_projection_state.py` for effective-vs-declared mode rendering, `dev/scripts/devctl/runtime/review_packet_inbox.py` and `dev/scripts/devctl/review_channel/action_request.py` for typed packet queue projection, `dev/scripts/devctl/review_channel/event_store.py` / `packet_post_idempotency.py` and `packet_contract.py` for packet post dedupe/schema, `dev/scripts/devctl/context_graph/query.py` and `dev/scripts/devctl/commands/governance/simple_lanes.py` for command rendering, `dev/scripts/checks/mutation_outcome_parse.py` plus `dev/scripts/devctl/commands/check/__init__.py` for fragile-surface cleanup, `dev/scripts/devctl/runtime/agent_session_outcome.py` / `collaboration_session.py` for unresolved outcomes, and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-28 entry "Plan 4.1 dogfood cleanup collapses review surfaces onto typed authority" |
| Where is the 2026-04-27 governed-commit self-resolution closure documented (`devctl commit` auto-runs one bounded host-process age-out retry, shared git helpers back off transient `.git/index.lock` races, and `ActionResult` carries structured `errors` / `reason_chain` / `remediation` / `auto_executable` fields)? | `dev/scripts/devctl/commands/vcs/commit_guard_bundle.py` for the guard-bundle retry, `dev/scripts/devctl/runtime/vcs.py` for bounded index-lock backoff, `dev/scripts/devctl/runtime/action_contracts.py` for the expanded result envelope, `dev/scripts/devctl/commands/vcs/governed_executor_phases.py` / `governed_executor_commit_phase.py` for structured stage/commit index failures, and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-27 entry "Governed commit now self-resolves host cleanup age-out and transient index locks" |
| Where is the 2026-04-26/27 governed-commit attention-staleness closure documented (`devctl commit` refreshes the startup receipt before failing on packet `attention_revision_stale`, and treats non-zero-but-parseable startup advisory output as a successful refresh rather than `startup_context_refresh_failed`)? | `dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py` for the shared preflight refresh helper/advisory-output classifier, `dev/scripts/devctl/commands/vcs/governed_executor_stage_attention.py` / `governed_executor_commit_phase.py` for the stage/commit consumers, and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-26 entry "Governed commit refreshes startup attention before stale gates" plus 2026-04-27 entry "Startup refresh treats typed advisory output as success" |
| Where is the 2026-04-27 push-failure state-machine closure documented (non-destructive push failures auto-transition a landed commit to `delivered_locally_pending_publish`, destructive remote rejection/conflict evidence stays `push_blocked`, and `mark-delivered-local` remains the explicit operator override)? | `dev/scripts/devctl/runtime/remote_commit_pipeline_state.py` for failure classification, `dev/scripts/devctl/commands/vcs/governed_executor_push_result.py` / `push_pipeline_state_sync.py` for transition projection and persistence, `dev/scripts/devctl/commands/vcs/commit_pipeline_blocking.py` for legacy stuck-pipeline self-heal during commit preflight, and `dev/history/ENGINEERING_EVOLUTION.md` 2026-04-27 entry "Push failure state now frees safely landed local commits" |
| Where is the Ralph guardrail remediation/control-plane plan? | `dev/active/ralph_guardrail_control_plane.md` |
| Where is the heuristic review-probe execution plan? | `dev/active/review_probes.md` |
| Where is the code-shape expansion research companion (readability, coupling, AI-specific, information-theoretic probes/guards)? | `dev/active/code_shape_expansion.md` (subordinate evidence/calibration companion feeding `dev/active/review_probes.md` Phase 5b+, not a second execution authority) |
| Where is the portable code-governance engine / multi-repo portability and measurement plan? | `dev/active/portable_code_governance.md` (engine/adoption companion and owner reference for the portable-proof phase; live execution order stays in the typed phase/task registry in `dev/active/ai_governance_platform.md`) |
| Where is the full reusable AI governance platform / package-extraction architecture plan? | `dev/active/ai_governance_platform.md` (the only main active architecture plan for this product scope; its typed phase/task registry at the top of `## Execution Checklist` is the live execution authority for `MP-377`) |
| Where is the 2026-04-27 agent-substrate architecture review for proof-tick authority, mode-axis separation, and any-agent-any-role migration? | `dev/active/agent_substrate_architecture_review.md` (reference-only Plan 4.1 review; execution order stays in `dev/active/ai_governance_platform.md`) |
| Which guard catches typed enum values that are declared but never consumed by a decision branch, policy map, comparison, or typed reference? | `dev/scripts/checks/check_typed_enum_connectivity.py` (warning-only first; registered in shared governance bundles, with ADR-021 tracking later Slice C baseline retirement and `--fail-on-disconnected` promotion) |
| Where is the issue-to-guard/probe promotion queue owned? | `dev/active/ai_governance_platform.md` for the `FindingReview -> GuardPromotionCandidate` contract, `dev/active/portable_code_governance.md` for repo-pack path portability, and `dev/scripts/README.md` for `governance-review` queue behavior |
| Where is the current `MP-377` startup-authority / repo-pack / typed-plan-registry / runtime-evidence-context closure plan? | `dev/active/platform_authority_loop.md` (subordinate `MP-377` owner reference; read after `dev/active/ai_governance_platform.md` only when the active typed phase/task route names it) |
| Where is the scheduler-facing planning reducer for multi-agent slice routing documented? | `dev/active/ai_governance_platform.md` for execution authority, plus `dev/scripts/README.md` for the maintainer-facing `PlanningIRSnapshot` module surface |
| Where is the bounded coordination/topology reducer for live roster, ownership posture, fanout safety, worktree isolation, and resync state documented? | `dev/active/ai_governance_platform.md` for execution authority, plus `dev/scripts/README.md` for the maintainer-facing `CoordinationSnapshot` / `CoordinationTopologySnapshot` module surfaces |
| Which module is the canonical shared loader every coordination read surface (startup-context, session-resume, dashboard/`ControlPlaneReadModel`) must route through so they cannot silently disagree on `observed_topology`/`ownership_status`/`resync_reasons`? | `dev/scripts/devctl/runtime/coordination_loader.py::load_coordination_snapshot`; see the MP-384/MP-387 parity regression in `dev/scripts/devctl/tests/runtime/test_coordination_loader_wiring.py` |
| Which module derives startup-facing observed control topology and implementation permission from live reviewer/implementer runtime evidence instead of planned bridge topology? | `dev/scripts/devctl/runtime/control_topology.py`; startup-context projects `observed_control_topology` and `implementation_permission` through summary, markdown, and machine-summary output |
| Which modules promote `active_target` from live plan/finding state so startup-context, session-resume, and dashboard do not regress to stale continuity targets? | `dev/scripts/devctl/runtime/work_intake.py::build_work_intake_packet`, `dev/scripts/devctl/runtime/work_intake_selection.py::promote_active_plan_entry`, and `dev/scripts/devctl/platform/coordination_snapshot.py::build_coordination_snapshot_for_review_state` |
| Which helper projects persisted `PlanRegistry` authority into legacy MP/path/router views for context-graph, review-channel promotion, tracker-plan resolution, and `ReviewSnapshot` consumers? | `dev/scripts/devctl/runtime/plan_registry_projection.py`; authority readers should prefer this typed projection over reparsing raw `INDEX.md`, leaving markdown parsing as compatibility fallback only. |
| Which helper is the canonical source for SYSTEM_MAP typed contract/writer/reader connectivity across context-graph, startup-context, session-resume, render-surfaces, and platform closure guards? | `dev/scripts/devctl/platform/connectivity_registry.py::build_connectivity_registry_snapshot` plus `summarize_connectivity_registry`; consumers should reuse the bounded `ConnectivityRegistrySnapshot` / summary instead of inventing parallel field-reader maps. |
| Which reducer collapses coordination posture, reviewer-handshake state, packet target, next command, and allowed actions into one turn-sized runtime contract for startup-context, session-resume, and review-channel status/doctor? | `dev/scripts/devctl/runtime/authority_snapshot.py::build_authority_snapshot` / `project_authority_snapshot`; the emitted `AuthoritySnapshot` is the preferred reduced surface for `coordination_state`, `root_cause`, `required_action`, `next_command`, and `safe_to_continue` |
| Which helper keeps observer/dashboard advisory next-command surfaces from emitting mutating implementer commands? | `dev/scripts/devctl/runtime/advisory_next_action_role_filter.py::project_next_command_for_role`; startup action routing, `AuthoritySnapshot`, `ControlPlaneReadModel`, `session-resume`, and `dashboard --role dashboard\|observer` must project mutating commit/push/pipeline commands to the read-only review-channel status command for read-only callers. |
| Which helper attaches proof-tick producer provenance to nested runtime authority payloads? | `dev/scripts/devctl/runtime/surface_provenance.py::attach_surface_provenance`; `AuthoritySnapshot` and `CoordinationSnapshot` must preserve `snapshot_id`, `zref`, `source_identity`, `source_contract`, `source_command`, `observed_fields`, and `inferred_fields` from their producer payloads so startup, session-resume, dashboard, and review-channel readers can prove which source generated a nested contract. |
| Which helper must both bridge-backed and event-backed review-state producers call before classifying attention so `review-channel status`, `startup-context`, `session-resume`, and `dashboard` cannot split on reviewer-runtime vs checkpoint priority? | `dev/scripts/devctl/review_channel/status_projection_helpers.py::attach_conductor_session_state`; `refresh_status_snapshot()` and `event_projection_assembly.enrich_event_review_state_impl()` must attach the same `session_output_root` conductor state before `build_recovery_assessment()` computes `launch_truth`, `effective_reviewer_mode`, and downstream `AuthoritySnapshot`/dashboard attention. |
| Where is the shared repo-visible backlog intake for humans + AI? | `backlog.md` (shared intake only; promote items into `dev/active/MASTER_PLAN.md` plus the owning active plan before execution) |
| Where is the governed active-plan markdown contract used by docs-governance and future `PlanRegistry` work? | `dev/active/PLAN_FORMAT.md` (reference-only companion for plan-doc schema/self-hosting) |
| Where is the durable reusable AI governance platform thesis/architecture guide? | `dev/guides/AI_GOVERNANCE_PLATFORM.md` (durable companion to the active platform plan) |
| Where is the platform-owned Python architecture guide and decision tree for contract-first tooling/runtime design? | `dev/guides/PYTHON_ARCHITECTURE.md` (durable companion for `MP-377` Python modeling/composition choices) |
| Where is the loop-output-to-chat coordination runbook? | `dev/active/loop_chat_bridge.md` |
| Where is the completed Rust workspace path/layout migration record? | `dev/archive/2026-03-07-rust-workspace-layout-migration.md` |
| Where is the naming/API cohesion execution plan? | `dev/active/naming_api_cohesion.md` |
| Where is the IDE/provider adapter modularization execution plan? | `dev/active/ide_provider_modularization.md` |
| Where is the pre-release architecture/tooling cleanup execution plan? | `dev/active/pre_release_architecture_audit.md` |
| Where is the consolidated full-surface audit evidence used by that plan? | `dev/active/audit.md` (reference-only) |
| Where is the raw multi-agent audit merge transcript for that evidence set? | `dev/active/move.md` (reference-only supporting evidence) |
| Where are federated internal repo links/import rules (`code-link-ide`, `ci-cd-hub`)? | `dev/integrations/EXTERNAL_REPOS.md` |
| Where do we track repeated manual friction and automation debt? | `dev/audits/AUTOMATION_DEBT_REGISTER.md` |
| Where is the baseline full-surface audit runbook/checklist? | `dev/audits/2026-02-24-autonomy-baseline-audit.md` |
| Where are audit metrics definitions (AI vs script share, automation coverage, charts)? | `dev/audits/METRICS_SCHEMA.md` |
| How do we run the current parallel Codex/Claude markdown swarm cycle? | `dev/active/review_channel.md` |
| Where is the local-first continuous swarm execution contract (next-task promotion, peer liveness, context rotation)? | `dev/active/continuous_swarm.md` |
| Where are `devctl` command semantics and examples? | `dev/scripts/README.md` |
| Where is the repo-local phone-steered Claude remote-control bridge wrapper documented? | `dev/scripts/README.md` for wrapper usage/limits, plus `dev/active/continuous_swarm.md` for the live `MP-358` execution state |
| Where is the plain-language `devctl` system architecture map, including portable naming/map direction? | `dev/guides/DEVCTL_ARCHITECTURE.md` |
| Where is the devctl automation playbook? | `dev/guides/DEVCTL_AUTOGUIDE.md` |
| Where is MCP-to-devctl architecture alignment and extension policy? | `dev/guides/MCP_DEVCTL_ALIGNMENT.md` |
| Where is the portable-governance engine boundary, export flow, and benchmark/evaluation guide? | `dev/guides/PORTABLE_CODE_GOVERNANCE.md` (engine/adoption companion guide) |
| Where is repo-local / portable guard-probe policy and repo-pack surface generation? | `dev/config/devctl_repo_policy.json`, `dev/config/quality_presets/`, and the `dev/scripts/devctl/quality_policy*.py` resolver stack |
| Where is the remediation scaffold template used by guard-driven Rust audits? | `dev/config/templates/rust_audit_findings_template.md` |
| What user behavior is current? | `guides/USAGE.md`, `guides/CLI_FLAGS.md` |
| What flags are actually supported? | `rust/src/bin/voiceterm/config/cli.rs`, `rust/src/config/mod.rs` |
| How do we build/test/release? | `dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md` |
| Where is the developer lifecycle quick guide? | `dev/guides/DEVELOPMENT.md` (`End-to-end lifecycle flow`, `What checks protect us`, `When to push where`) |
| Where are clean-code and Rust-reference rules defined? | `AGENTS.md` (`Engineering quality contract`), `dev/guides/DEVELOPMENT.md` (`Engineering quality review protocol`) |
| What process is mandatory? | `AGENTS.md` |
| What architecture/lifecycle is current? | `dev/guides/ARCHITECTURE.md` |
| Where are CI lane implementations and release publishers? | `.github/workflows/` |
| Where is the plain-language workflow guide? | `.github/workflows/README.md` |
| Where is process history tracked? | `dev/history/ENGINEERING_EVOLUTION.md` |

## Instruction scope and precedence

When multiple instruction sources exist, apply this precedence:

1. Session-level system/developer/user instructions.
2. The nearest `AGENTS.md` to the files being edited.
3. Ancestor `AGENTS.md` files (including repo root).
4. Linked owner docs from the source-of-truth map.

If subtrees require different workflows, add nested `AGENTS.md` files and keep
them scoped to that subtree.

## Autonomous execution route (required)

Use this route to run end-to-end without ambiguity:

1. Load `dev/active/INDEX.md`, then `dev/active/MASTER_PLAN.md`.
2. Use `INDEX.md` role/authority fields to decide which active docs are required:
   - `tracker` is execution authority.
   - `spec` is read when matching MP scope is in play.
   - `runbook` is read for active multi-agent cycles.
   - `reference` is context-only; do not treat as execution state.
3. Select task class in the router table and run the matching command bundle.
4. Apply risk-matrix add-ons for touched runtime risk classes.
5. Run docs-governance/self-review/end-of-session checklist before handoff.

## Mandatory 12-step SOP (always)

Run this sequence for every task. Do not skip steps.

1. Run session bootstrap checks and load `dev/active/INDEX.md` (`bundle.bootstrap`).
   For any implementation, validation, or repo-owned launcher session, treat
   `python3 dev/scripts/devctl.py startup-context --format summary` as Step 0,
   not optional escalation. The compact summary is the default human-facing
   receipt for AI bootstrap; the typed JSON receipt/artifacts still write
   silently under the repo-owned reports root. If it exits non-zero,
   checkpoint or repair the repo state before editing files or starting
   guarded launcher/mutation commands. Use
   `python3 dev/scripts/devctl.py startup-context --repair --apply-safe-fixes --format md`
   for repo-owned safe local repair before escalating to operator prompts; it
   still fails closed on checkpoint/publish/launch approval boundaries and
   applies at most one deterministic safe fix per invocation. User summaries,
   stale chat continuity, or remembered prior state are not a substitute for
   this Step 0 receipt.
   Repair mode now also treats typed `AuthoritySnapshot` /
   `CoordinationSnapshot` blockers as first-class startup issues, so a receipt
   that still says `coordination_resync_required` must not be treated as
   healthy just because review attention stayed `healthy`.
   The same repair path now resolves the governed review-channel
   `rollover_dir` sibling from the managed review root before dispatching
   repo-owned review-channel repair actions, so command-package refactors do
   not strand startup repair on missing runtime-path assertions.
   Do not replay bootstrap packets into chat by default; keep any chat
   acknowledgement to blocker state plus next step unless the user asks for
   the detailed packet.
   The compact summary now also surfaces unpublished stack depth
   (`ahead_of_upstream_commits`) plus governed-push timing guidance when the
   branch still has remote work to publish, so fresh sessions can answer
   "when do we push?" without manual `git` inspection or spelunking through
   typed JSON fields.
   Managed compatibility-projection dirt such as `bridge.md` must stay
   explicit: `startup-context` / context-graph / dashboard surfaces may exclude
   those paths from source-work checkpoint budgets, but they must still render
   `managed_projection_drift` and `managed_projection_dirty_paths` so raw git
   dirt never appears to contradict typed clean-source state.
   That typed startup receipt now emits a bounded `WorkIntakePacket`
   (selected `PlanTargetRef`, typed continuity, routing hints, and bounded
   `session_pacing` research guidance derived from planning/graph evidence),
   writes a managed startup receipt under the repo-owned reports root,
   prefers the persisted repo-owned `PlanRegistry` / `PlanTargetRef`
   artifact under the governed reports root before reparsing mutable plan
   markdown on every read, and
   exits non-zero when checkpoint budget or startup-authority truth says
   another implementation slice is not allowed yet. The scoped startup gate
   (`startup_gate.py`) reads `StartupReceipt.advisory_action` as a typed
   attribute and handles a missing receipt without crashing. The
   reviewer-loop relaxation for `launch`/`rollover` is handled by the
   `reviewer_bootstrap` intent in the authority system, so `enforce_startup_gate`
   has no separate repair bypass — receipt freshness, checkpoint, and all
   non-reviewer-loop authority checks always apply.
   The same startup/tandem path now
   resolves typed `review_state.json` through repo-pack/governance candidate
   authority instead of assuming one fixed `dev/reports/.../latest` path.
   Startup quality signals follow the same rule and load emitted probe
   artifacts from the managed `latest` root rather than an ad hoc sibling
   summary path.
   After that, run
   `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`
   for a slim startup context with active plans, hotspots, and deep links.
   The live graph now also carries first-pass `guards` / `scoped_by`
   relations, so file/path queries can answer "what guards protect this?" and
   "what plan scope owns this?" from the same generated surface before the
   workflow expands into deeper reads. Query mode now suppresses generic
   guard-edge fan-out unless you asked about a guard directly, and current
   `scoped_by` coverage comes from docs-policy rules rather than raw
   substring adjacency. That bootstrap command now also
   persists a typed `ContextGraphSnapshot` artifact under
   `dev/reports/graph_snapshots/`; when `DEVCTL_NO_ARTIFACT_WRITES=1` the
   bootstrap auto-save is suppressed so read-only surfaces (MCP adapters,
   containers) never attempt incidental writes, but explicit `--save-snapshot`
   still writes regardless. Use `--save-snapshot` to capture the same
   versioned graph artifact from other `context-graph` modes too, and use
   `python3 dev/scripts/devctl.py context-graph --mode diff --from previous --to latest --format md`
   when the slice needs a typed delta/trend read over saved graph baselines.
   Follow the deep links when the task requires full authority from the
   canonical docs (`AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`).
   Keep that bootstrap packet small by default and expand with
   `context-graph --query '<term>'` when the task needs more context (the
   query renderer suppresses the global Hot Index Summary on zero-match
   results to avoid misleading evidence). The
   generated `CLAUDE.md` bootstrap surface is the first-hop AI awareness
   layer: keep it synchronized via `render-surfaces` so it advertises live
   governance capabilities (`ai_instruction`, `decision_mode`,
   `governance-review --record`, packet-level operational feedback, and saved
   `ContextGraphSnapshot` baselines) and points agents at
   `dev/guides/DEVELOPMENT.md` plus `dev/scripts/README.md` for the canonical
   "which tool do I run when?" guidance. That rendered bootstrap surface must
   also state the compiler-style system model for AI work plus the
   `TypedAction -> ActionResult -> RunRecord` execution path, and it must
   project first-hop launch authority (`startup-context` `action` / `reason`,
   `interaction_mode`, `push_decision`, and typed reviewer
   `conductor_visibility` / `session_visibility`) so launchers start from
   repo-owned authority rather than chat-local lore or hidden headless
   defaults.
2. Decide scope (`develop` work or `master` release work).
3. Classify task using the task router table.
4. Load only the required context pack listed for your task class.
5. Link or confirm MP scope in `dev/active/MASTER_PLAN.md` before edits.
6. Implement changes and tests.
7. Run the bundle required by your task class.
8. Run matrix tests required by touched risk classes.
9. Update docs/screenshots/ADRs required by governance.
10. Self-review security, memory, errors, concurrency, performance, and style.
11. Push through branch policy and run post-push audit (`bundle.post-push`).
12. Capture handoff summary using `dev/guides/DEVELOPMENT.md` template.

## Execution-plan traceability (required)

For non-trivial work (runtime/tooling/process/CI/release), execution must be
anchored in an active tracked plan doc under `dev/active/`.

1. Create or update the relevant execution-plan doc before implementation
   (for example `dev/active/autonomous_control_plane.md`).
2. Execution-plan docs must include the marker line:
   `Execution plan contract: required`.
3. Execution-plan docs must include these sections:
   - `## Scope`
   - `## Execution Checklist`
   - `## Progress Log`
   - `## Session Resume`
   - `## Audit Evidence`
3.1 Execution-plan docs must expose one parseable metadata header near the top
    of the file. Follow `dev/active/PLAN_FORMAT.md` when editing or creating
    governed plan markdown.
4. The associated MP scope must be present in both `dev/active/INDEX.md` and
   `dev/active/MASTER_PLAN.md`.
4.1 In multi-agent runs, progress/decisions must be written into the active
    plan markdown and/or `MASTER_PLAN` updates; hidden memory-only coordination
    is not acceptable execution state.
4.2 For substantive AI sessions, keep restart state in the active plan's
    `Session Resume` and `Progress Log`. Structured JSONL audit/event logs are
    for machine-readable execution evidence, metrics, and later database/ML
    ingestion, not prose session handoff.
4.3 Do not hand-edit command audit JSONL logs. `python3 dev/scripts/devctl.py`
    commands auto-emit machine-readable event rows; use
    `python3 dev/scripts/devctl.py governance-review --record ...` only for
    adjudicated guard/probe outcomes. If meaningful non-`devctl` work happened
    outside that telemetry path, call out the coverage gap in handoff notes.
5. `python3 dev/scripts/checks/check_active_plan_sync.py` is the enforcement
   gate and must pass before merge.

## Continuous improvement loop (required)

Use a repeat-to-automate loop so the toolchain gets stronger after every run.

1. Record friction points in the active-plan progress log and/or handoff notes
   for every non-trivial execution session.
2. If the same workaround/manual step repeats 2+ times in the same MP scope,
   resolve it before closure by:
   - automating it as a guarded `devctl` command/workflow/check with tests, or
   - logging it as explicit debt in `dev/audits/AUTOMATION_DEBT_REGISTER.md`
     with owner, risk, and exit criteria.
2.1 If `python3 dev/scripts/devctl.py process-cleanup --verify --format md`
    or `python3 dev/scripts/devctl.py process-audit --strict --format md`
    finds a new leaked-process shape, extend the cleanup/audit automation in
    the same MP scope before closure or log explicit debt with the missed
    process shape and the guard path needed to catch it next time.
2.2 When a real issue is found by audit/review/manual use and the current
    tooling did not catch it, first decide whether the miss belongs in an
    existing guard/probe/runtime contract or should become a new reusable,
    low-noise modular enforcement path. Prefer fixing the detection gap over
    landing a one-off patch without a corresponding enforcement follow-up, and
    keep that decision in repo-visible plan state before closure.
2.2.1 Missing enforcement-lane wiring counts as the same class of escaped
    defect. If a new public guard/probe exists in script catalog or docs but
    is absent from typed quality policy, bundle/workflow parity, or hook-owned
    launch surfaces, close that registration gap before calling the slice done;
    do not waive it as "just config drift."
2.3 No important issue is complete until it has been evaluated for
    architectural absorption. For any non-trivial bug, review finding,
    runtime failure, audit issue, or docs/process miss, classify whether it is
    a local defect, contract mismatch, missing guard, missing probe, authority
    boundary failure, workflow/process gap, or documentation/plan drift. Then
    either encode the prevention path in an approved surface (guard, probe,
    contract, authority rule, parity check, regression test, docs update) or
    record an explicit waiver with reason. Do not silently close meaningful
    findings as patch-only work.
2.3.1 Apply the same closure rule to performance/pathology misses in
    governance tooling. If a path-scoped predicate or commit-range command
    (`docs-check`, router helpers, startup scans, etc.) keeps rebuilding the
    same authority/policy state inside a loop, treat that as a real escaped
    defect: resolve the contract once per repo/policy context, reuse it inside
    the loop, and add regression proof so the slowdown does not silently
    return.
3. "Cannot automate yet" is acceptable only with a documented reason and a
   guard path (checklist/runbook entry that prevents unsafe execution).
4. When automation lands, update command/docs surfaces in the same change
   (`AGENTS.md`, `dev/scripts/README.md`, `dev/guides/DEVCTL_AUTOGUIDE.md` as needed).
4.1 During staged Python module splits or relocations under `dev/scripts/**`,
    preserve stable compatibility re-exports or aliases in the old module in
    the same change until all repo importers, tests, workflows, and
    pre-commit hooks have been migrated. Treat those compatibility seams as
    part of the maintainer-facing contract, not as disposable cleanup.
5. Baseline full-surface audit execution starts from
   `dev/audits/2026-02-24-autonomy-baseline-audit.md` and should be copied
   forward for each new audit cycle.
6. Audit cycles should emit quantitative metrics from event logs
   (`automation_coverage_pct`, `script_only_pct`, `ai_assisted_pct`,
   `human_manual_pct`, `success_rate_pct`) and chart outputs via
   `python3 dev/scripts/audits/audit_metrics.py`.

## AI operating contract (required)

Use the compiler-style governance framing from
`dev/guides/AI_GOVERNANCE_PLATFORM.md` and
`dev/active/ai_governance_platform.md` when reasoning about this system. The
AI is a probabilistic proposer inside repo-owned deterministic passes:
`startup-context`, guards, probes, and policy resolution lower repo state into
typed control objects, and only governed execution turns that into
`TypedAction -> ActionResult -> RunRecord`. Do not treat the repo as a
checklist plus chat memory.

1. Be autonomous by default: implement, test, docs, and validation end-to-end.
2. Ask only when required: ambiguous UX/product intent, destructive actions,
   credentials/publishing/tagging, or conflicting policy signals. Branch-
   mutating checkpoint/commit/push actions still follow the explicit approval
   and review gates in the Branch policy section below.
3. Stay guarded: do not invent behavior, do not skip required checks.
4. After any file create/edit, run the applicable repo guard/check scripts
   before handoff; do not leave changed files unvalidated. Follow
   `dev/guides/DEVELOPMENT.md#after-file-edits`. After complex edits
   (new modules, multi-file refactors, or business-logic changes), also run
   the review probe suite to catch design-quality regressions early:
   `python3 dev/scripts/devctl.py check --profile ci` (includes probes).
4.1 Keep tooling dry-run/report-only paths portable: script-generation,
    dry-run launch, and local preflight flows must not depend on provider CLIs
    or GitHub API reachability unless the action actually needs live
    execution. Preserve explicit strict failure paths separately for real
    launch/fix execution and focused tests.
4.2 When a guard intentionally relaxes live-review freshness on GitHub-hosted
    CI, do not reuse that relaxed guard output as the only trigger for stale
    bridge auto-repair. Auto-refresh helpers must derive stale/missing
    heartbeat repairability from the bridge snapshot itself so CI parity stays
    aligned with the real launch/status contract.
4.3 Any CI job that invokes compile-time Rust guards (for example
    `check_rust_compiler_warnings.py`) must provision the repo Rust toolchain
    plus required platform headers first; tooling/docs workflows cannot assume
    those prerequisites are inherited just because the dedicated Rust CI lane
    already installs them.
4.4 In live review-channel mode, treat
    `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
    as the canonical checkpoint-budget read too. If
    `attention.status=checkpoint_required` or
    `push_enforcement.safe_to_continue_editing=false`, stop widening the
    slice and cut a checkpoint before further edits or any raw push attempt.
    When both checkpoint and review follow-up are needed, the attention
    system prioritizes `review_follow_up_required` so the reviewer-turn
    signal is not hidden behind the generic checkpoint state.
    Fresh repo-owned `review-channel --action launch|rollover` starts must
    treat that same checkpoint state as a hard launch blocker, not as
    advisory status to be ignored while starting another implementation loop.
    After that checkpoint-budget gate, those actions use reviewer-bootstrap
    receipt semantics instead of implementation-strict freshness: branch
    mismatch and non-reviewer authority failures still block, but plain HEAD
    drift only blocks when the diff since the receipt touches guarded
    quality-scope roots.
    Fresh reviewer bootstrap still starts with
    `python3 dev/scripts/devctl.py startup-context --role reviewer --format summary`,
    then `python3 dev/scripts/devctl.py session-resume --role reviewer --format json`
    to get the typed reviewer bootstrap packet with `head_sha`,
    `last_reviewed_sha`, current blockers, exact next guard bundle, and any
    ready `review_candidate`. When a valid `review_candidate` is present,
    the reviewer must inspect that frozen target first, including its
    `candidate_id`, changed-path scope, and dirty-tree `worktree_hash`;
    fall back to raw `last_reviewed_sha..head_sha` review only when no
    candidate exists. If implementer-complete status/ACK claims a finished
    slice but the typed state has no valid candidate, fail closed and repair
    the handoff before review instead of inferring from bridge prose or HEAD
    alone.
    That same status/doctor family now hoists one top-level
    `recommended_command`, preferring typed recovery commands and otherwise
    reusing `push_decision.next_step_command`, so hooks/launchers should read
    that field before spelunking nested compatibility projections. Apply the
    same rule to diff-sensitive follow-up: hook/launcher shims should reuse
    repo-owned push/startup diff-base truth instead of recomputing branch
    literals such as `origin/develop`. When that field resolves only to a
    typed decision id (for example `resume_live_review_loop`) instead of an
    executable shell command, treat it as repo-owned decision state and fall
    back to the sanctioned command for that state; do not auto-execute raw
    ids as if they were commands.
    The same release-lane bootstrap truth is now publication-aware on
    feature branches: local governed pre-push CodeRabbit gates may treat
    "current SHA not present in any local remote-tracking ref yet" as a
    non-blocking unpublished-commit state, but once the SHA is published or
    the configured release branch is in play the gate remains strict.
    Before any launch/recover choice, read that bootstrap packet's
    `interaction_mode` plus typed reviewer visibility. In `local_terminal`,
    prefer visible `review-channel --action launch|rollover --terminal terminal-app`;
    use `--terminal none` only for explicit headless starts, dry-run/script
    generation, governed `remote_control`, or recovery of an already-headless
    parent session. Visible local launch/recover must also originate from a
    stable repo-managed root: repo-owned `terminal-app` launch now fails
    closed for transient temp clones/worktrees so provider directory-trust
    prompts cannot stall local automation before the conductor starts. Treat
    `--terminal none` as a real headless background conductor, not a
    report-only preview.
    A non-zero startup receipt with `action=continue_editing` /
    `reason=review_pending` or `action=await_review` /
    `reason=review_pending_before_push` is still a normal reviewer-owned
    bootstrap state while the loop is live. In that case, continue into
    `review-channel --action status` plus the required reviewer heartbeat /
    bridge refresh instead of escalating into generic repair. Treat only
    `action=repair_reviewer_loop`, checkpoint/budget blockers, or typed
    stale/non-live reviewer runtime as the relaunch/repair boundary.
    The narrower stale-implementer replacement path is now
    `python3 dev/scripts/devctl.py review-channel --action recover --recover-provider <provider>`;
    it replaces only the stale implementer conductor for the requested
    provider and now requires the current repo-owned reviewer provider session
    to already be live. If the reviewer side is not already live, fail closed
    and use `launch|rollover` to relaunch the pair instead of drifting into a
    hybrid provider loop.
    In governed `remote_control`, `recover --terminal none` is a real detached
    relaunch path, not a report-only preview: it must route through the same
    headless proof-of-life launch discipline as other headless review-channel
    starts and wait for the current implementer ACK before claiming success.
    Session/bootstrap consumers must also keep caller-threaded typed
    `ReviewState` authoritative over stale compact/current-session artifacts
    so recover/startup/session-resume do not disagree on the live instruction.
4.4.1 In that same active review-channel loop, detached publisher/supervisor
    heartbeats are not proof the dual-agent session is still alive. If
    `reviewer_mode=active_dual_agent` but repo-owned conductor sessions are
    missing, treat the state as a bridge-contract error and relaunch the
    pair instead of trusting stale "fresh" status. Reviewer-follow recovery
    must obey the typed recovery contract here too: when
    `recovery_action_allowed` / `recovery_assessment.decision.command` says
    `launch`, do not silently degrade to peer-stale `rollover`. Auto-relaunch
    is only allowed when the typed decision marks the relaunch auto-fixable;
    otherwise fail closed and use the queued reviewer-turn packet / explicit
    launch path.
    Recovery precedence is fail-closed too: when typed `current_session`
    already shows a current Claude ACK but `launch_truth` falls to
    `detached_runtime_only`, `automation_only`, or `hybrid_claude_only`,
    classify the state as `review_loop_relaunch_required` and use the
    reviewer-owned `launch|rollover` path. `reset-implementer-state` is
    reserved for stale implementer bridge sections while the repo-owned
    reviewer loop is still otherwise live.
4.4.2 Claude-side waiting is also fail-closed now: use the repo-owned
    `review-channel --action implementer-wait` path only under an explicit
    reviewer-owned wait state. If `Current Instruction For Claude` still
    assigns active work, `Claude Status` / `Claude Ack` updates must name
    concrete files, subsystems, findings, or one concrete blocker/question;
    `No change. Continuing.`, `instruction unchanged`, `Codex should review`,
    and raw shell `sleep` loops are contract violations.
4.4.3 Fresh launch validation now treats the canonical reviewer-reset
    implementer placeholder (`Claude Status: - pending`, `Claude Ack:
    - pending`) as launchable state for a new instruction revision. The same
    reviewer-owned instruction reset must clear stale `Claude Questions`
    alongside status/ack so compatibility-bridge handoff text does not carry
    forward dead blockers from the previous instruction tranche. Use
    `python3 dev/scripts/devctl.py review-channel --action reset-implementer-state --terminal none --format md`
    for that repo-owned reset path when live status/attention says the
    implementer side should return to canonical pending state; it refreshes
    the typed projection too, and it does not replace a reviewer checkpoint.
4.4.4 The launch-wait helper (`observe_launch_state`) now reads the bridge
    snapshot and conductor session probes directly instead of round-tripping
    through the full `refresh_snapshot_fn` status path. This makes launch-time
    polling lighter and avoids re-running the entire status pipeline on every
    observation tick. OSError during direct read falls back to the original
    full-snapshot path for resilience.
4.4.5 The Codex-poll-refresh waiter (`wait_for_codex_poll_refresh`) now
    distinguishes two satisfaction paths: (a) status-observed, where the
    reviewer-owned `Poll Status` prose changed and is not an automation-only
    heartbeat refresh; (b) launch-confirmed, where the `Last Codex poll`
    timestamp advanced past the pre-launch baseline AND typed session probes
    confirm both conductors are live. Neither path accepts both an unchanged
    timestamp and unchanged status text, preserving the fail-closed guard
    against authority-bypass scenarios.
4.4.6 `ReviewState.attention` is now a deterministic projection of the typed
    `recovery_assessment` (diagnosis + decision pair) when both are present.
    Reviewer runtime doctor snapshots and status surfaces prefer this typed
    projection over stale raw attention values. The parity guard
    `check_review_surface_consistency.py` enforces the contract: if
    `recovery_assessment` exists, `review_state.attention` must match the
    canonical projection fields (`status`, `owner`, `summary`,
    `recommended_action`, `recommended_command`). Drift between raw attention
    and the projected values is a CI-blocking error, not silent state
    corruption.
4.4.7 Bridge rendering portability: the markdown bridge compatibility
    projection now derives display timezone, local-state hash exclusion
    prefix, and review-channel plan path from `RepoPathConfig` instead of
    hardcoding VoiceTerm-specific values. Another repo can override
    `display_timezone`, `local_state_prefix_rel`, and `review_channel_rel`
    via `set_active_path_config()` and the bridge rendering, heartbeat
    refresh, and worktree hash computation will follow the config without
    code changes. Bridge metadata regexes now match any timezone label
    instead of requiring `America/New_York`.
    Implementer bridge state remains compatibility-shaped too: legacy
    `Claude Status` / `Claude Questions` / `Claude Ack` headings are aliases,
    not provider truth, and live readers/guards must treat neutral
    implementer-heading aliases plus typed `implementer_*` state as the
    authority boundary.
4.4.8 Event-backed `current_session` authority is fail-closed on explicit
    packet truth, not on missing packet surfaces. If queue instruction text is
    blank and no live `packets` / persisted `packet_inbox` authority is
    present, preserve the prior typed instruction instead of clearing it by
    assumption. Only queue rows whose
    `derived_next_instruction_source.to_agent` is blank or `claude` may feed
    `current_session.current_instruction`; reviewer-targeted (`codex`) queue
    instructions remain attention/open-findings only. The same fail-closed
    rule applies to mutation authority: missing or empty typed
    `implementation_permission` is a hard block in
    `ImplementationAdmissibility`, not an implicit allow.
4.4.9 Runtime proof-tick parity is producer-owned. `ControlPlaneReadModel`
    and `SessionCachePacket` carry the shared `SurfaceProvenance` tuple from
    the typed review-state producer, and review-channel derived projections
    copy that same tuple instead of reconstructing identity from surrounding
    prose. `check_review_surface_consistency.py` now compares the frozen
    proof-tick fields across coordination, authority, control-plane,
    startup-context, session-resume, review-channel status, persisted
    review-state, registry, and bridge-compat surfaces. For one proof tick,
    `reviewer_mode`, `effective_reviewer_mode`,
    `operator_interaction_mode`, `observed_control_topology`,
    `current_instruction_revision`,
    `ownership_status`, `implementation_permission`, `next_command`,
    `snapshot_id`, `generation_id`, `head_sha`, `worktree_hash`, and `zref`
    must agree wherever a surface exposes them.
    The expected value must come from the field's typed authority priority,
    not from first populated surface order. `reviewer_mode` and
    `effective_reviewer_mode` remain review-loop posture fields, while
    `operator_interaction_mode` is checked as the separate operator-channel
    axis.
    `observed_control_topology` is the explicit control-posture field; do
    not infer it from `CoordinationSnapshot.observed_topology`, because the
    coordination topology may describe planned/live multi-agent structure
    while the active remote-control lane remains single-agent.
4.5 In that same live review-channel mode, treat
    `dev/reports/review_channel/latest/review_state.json` (and the mirrored
    `compact.json` projection) `current_session` block as the canonical typed
    current-status read for live instruction / implementer ACK state. While
    the bridge migration remains in progress, `bridge.md` is a compatibility
    projection and handoff surface, not the preferred source for current-
    status reads. Startup/tandem/push consumers that read live freshness from
    that projection must refresh the bridge-backed typed snapshot through the
    repo-owned status path before trusting `current_session` fields. The same
    typed artifact now carries reviewer hash truth in `bridge` too:
    `bridge.reviewed_hash_current` / `bridge.review_needed` are the canonical
    booleans for "does Codex still owe review?" while `current_session`
    remains intentionally narrow to instruction / ACK state. The same typed
    `bridge` block now also carries `effective_reviewer_mode` for live-
    authority consumers: keep the declared bridge `reviewer_mode` for
    provenance, but prefer `bridge.effective_reviewer_mode` when deciding
    whether `active_dual_agent` is actually live enough to grant reviewer/
    implementer loop authority. Apply that same precedence to governed
    commit/push lane selection too: when a writable conductor capability must
    be synthesized, `bridge.effective_reviewer_mode` outranks stale declared
    collaboration topology so local `single_agent` takeover cannot silently
    hand commit execution back to the implementer lane.
    Governed push and hook-owned preflights that trust or stage `bridge.md`
    must refresh the typed review-state/status projection first and then
    reproject the compatibility bridge from that typed state instead of
    trusting stale bridge prose.
    The same typed
    contract now owns semantic implementer ACK parsing too: accepted
    `Claude Ack` phrasings include both legacy `instruction-rev:` bullets and
    semantic forms such as `Acknowledged instruction revision <rev>`, but live
    machine consumers should still refresh/read typed `current_session` /
    `bridge` state instead of reparsing bridge prose ad hoc.
    In Codex-only local-review mode, `single_agent` is the sanctioned reviewer
    state and the repo-owned `reviewer-heartbeat` / `reviewer-checkpoint` path
    remains the authority for review truth; when the typed `current_session`
    ACK state is unknown, fall back to `bridge.claude_ack_current` before
    reading bridge prose. Prefer provider-neutral bridge aliases
    (`implementer_ack*`, `implementer_status`, `reviewer_poll_state`,
    `last_reviewer_poll_*`) when present; the legacy `claude_*` /
    `codex_*` fields remain compatibility projections for bridge/render
    parity only. Startup/coordination consumers must also treat that
    sanctioned local `single_agent` takeover as active local implementation
    authority when no typed remote-control attachment is live, rather than
    misclassifying the repo as governed `remote_control` just because no live
    dual-agent pair is running. In governed remote-control `single_agent`
    lanes, bridge-backed status and `ControlPlaneReadModel` must also keep the
    attached remote provider live from typed `remote_control_attachment`
    authority instead of dropping Claude solely because recent typed packet
    activity aged past the reviewer-session freshness window. A deliberate
    `reviewer-heartbeat --reviewer-mode single_agent` takeover must also
    retire the detached publisher/reviewer-supervisor runtime so stale
    dual-agent heartbeats cannot silently restore `active_dual_agent`
    metadata after the reviewer has reclaimed authority. When that
    `single_agent` or remote-control lane stays attached to a phone/dashboard
    session, keep the primary worktree as the control/dashboard lane and route
    mutating implementation into reusable isolated worker worktrees; the
    operator should see typed lane state, not manage git worktree details by
    hand.
    If an `active_dual_agent` reviewer session is interrupted, no repo-owned
    Codex conductor remains live, or the loop degrades into a Claude-only /
    hybrid state, stop the detached reviewer daemons through the repo-owned
    `review-channel --action stop --daemon-kind all` path and cut back to
    sanctioned local takeover with
    `review-channel --action reviewer-heartbeat --reviewer-mode single_agent`
    before reviewing or repairing code locally. Do not keep coding against a
    stale `active_dual_agent` bridge contract.
    The same typed status artifact now also carries `reviewer_runtime` as the
    single owner of reviewer lifecycle truth: reviewer mode/effective mode,
    freshness, stale reason, last poll, rollover state, session owner,
    allowed recovery action, review acceptance, and publish-clear state.
    Bridge `review_accepted` and doctor surfaces are compatibility
    projections over that contract, not parallel authority. That same
    contract now also owns `implementer_ack_current`,
    `implementation_blocked`, and `implementation_block_reason`; startup,
    status, and push consumers must read those typed fields instead of
    recomputing implementation-blocked truth from bridge-liveness prose.
    `check_review_surface_consistency.py` now also proves disk parity between
    the persisted `review_state` artifact and the computed turn-authority /
    bridge-poll projection, so review-surface reads cannot drift silently from
    the on-disk review snapshot.
    When persisted typed review state exists, bridge-backed status and
    compatibility projection must also prefer typed `current_session` plus
    typed `reviewer_runtime.review_acceptance` for live instruction / ACK /
    verdict / findings truth. Raw `bridge.md` verdict and findings prose
    remains compatibility or drift evidence only.
4.6 Treat `startup-context` the same way: prefer typed
    `review_state.json` fields such as
    `reviewer_runtime.review_acceptance.review_accepted` and
    `reviewer_runtime.publish_clear` as the canonical startup reviewer/publish
    gate authority. `bridge.review_accepted` remains a compatibility
    projection over that same runtime contract, and `bridge.md` is now a
    compatibility projection and handoff surface, not a startup-authority
    fallback when typed review state is missing. Advisory
    checkpoint-budget accounting may exclude policy-declared compatibility
    projections such as `bridge.md`, but canonical git/review truth still
    comes from the real worktree plus reviewer-owned state. Shared startup /
    escalation packets now also carry bounded decision constraints plus
    watchdog and command-reliability summaries; use those typed packet fields
    before reaching back to raw ledgers. Empty `memory_roots` placeholders are
    not authority and should not be resurrected in downstream JSON/rendering.
    `check_startup_authority_contract.py` is the fail-closed proof for this
    path: it must reject startup-authority states that are already over the
    checkpoint budget and Python module splits whose imports only resolve from
    worktree-on-disk files instead of the git index, while also proving the
    committed `HEAD` tree stays internally coherent. Fresh repos without a
    first commit skip that committed-tree layer until `HEAD` exists.
    The `startup-context` command itself now uses that same typed checkpoint
    truth as a fail-closed receipt: it still emits the packet, but returns
    non-zero when another implementation slice should not start yet. That same
    packet now carries the bounded `WorkIntakePacket` startup projection, so
    `startup_order`, typed plan continuity, and routing defaults travel
    together with one bounded coordination answer too: Step 0 summary now
    surfaces declared/observed/recommended topology, fanout safety,
    `resync_required`, `current_slice`, and `active_target`, and it treats
    coordination resync as a real startup/launch blocker instead of leaving
    that truth only in markdown/bootstrap renderers.
    through one startup-family surface instead of staying report-only.
    That same startup family now separates non-destructive routing recovery
    from destructive runtime recovery: use `control_recovery_action` for
    refresh/report/escalation guidance, and only treat `recovery_action` as
    relaunch or termination authority when paired with a proven
    `recovery_basis` and bounded `recovery_scope`. Dashboard/observer lanes
    must also honor `lane_edit_gate`: when another live agent owns the
    implementation lane, they may write findings or packets only, not
    implementation files.
    Read the action-routing packet in two layers: `allowed_actions` is the
    effective post-gate action set, while `intrinsic_allowed_actions`
    preserves the lane's underlying capability when checkpoint budget,
    resync, or implementation authority temporarily blocks mutation.
    `implementation_admissibility` is the shared mutability reducer for
    startup/status/monitor consumers; prefer it over inferring editability
    from scattered booleans.
    Current limitation: when another agent edits the repo outside the
    repo-owned checkpoint/review flow, startup/status still surface the result
    as a generic dirty-tree / checkpoint-budget blocker instead of a distinct
    concurrent-writer authority condition. Treat that as authority drift and
    reconcile the worktree before widening the slice.
    Startup recovery now also reads the managed latest-push artifact at
    `dev/reports/push/latest.json`: `devctl push --execute` now writes
    phase-aware snapshots from `push_preflight_running` through
    `push_pending`, then writes a `published_remote` snapshot as soon as
    `git push` succeeds, all keyed to the current branch and HEAD commit.
    Startup treats a current-head in-flight push receipt as "wait for the
    running governed push" and treats a persisted current-HEAD publication
    record as canonical even if local upstream divergence still looks stale
    until the next fetch. When a governed remote
    commit pipeline is active, the same recovery path now keys approval
    identity to the reviewer-owned tree receipt
    (`current_approved_target_identity` /
    `latest_push_report_approved_target_identity`) instead of raw HEAD
    equality alone. So
    `published_remote=true` plus a matching current HEAD means post-push
    repair/status work, not another push attempt. Reviewer/readiness
    projections must preserve that same publish truth too: `review-channel
    --action status|doctor` may not collapse a matching latest-push artifact
    back to generic `pipeline_unavailable` / unresolved push state just
    because no remote commit pipeline is active or the post-push bundle
    failed after publication. Blank approved-target identities are a valid
    current-target match for ordinary branch pushes, and doctor/status should
    expose when latest-push artifact truth is the source behind
    `published_remote` / `post_push_green`. The current publication target
    also includes the tracked upstream remote when one exists (otherwise the
    repo-policy default remote), and human-facing startup/status push
    sections must render effective current-target truth instead of replaying
    stale raw `latest_push_report_*` booleans as if they still describe the
    active branch/HEAD.
4.6.1 Read-only artifact handling: `startup-context`,
    `context-graph --mode bootstrap`, and other read-only status commands set
    `DEVCTL_NO_ARTIFACT_WRITES` via the read-only command dispatcher in
    `cli.py`.  `startup-context` always attempts the receipt write because the
    launcher validates it to gate subsequent actions; on intentional read-only
    mounts the write degrades gracefully on `OSError`, while other write
    failures propagate normally.  Bootstrap `context-graph` skips the automatic
    snapshot save when that env var is active. Explicit `--save-snapshot` still
    forces a write. The lightweight
    `observe_launch_state()` optimization in `bridge_launch_control.py` uses
    the same principle: launch-poll iterations now read bridge metadata and
    session state directly instead of forcing a full status refresh, keeping
    the read-only bootstrap path fast.
4.6.2 Launch-confirmed ACK path: `wait_for_codex_poll_refresh()` in
    `handoff.py` now has two satisfaction paths for the post-launch gate.
    Primary: reviewer-owned `Poll Status` text must change. Launch-confirmed:
    `Last Codex poll` timestamp must advance past the pre-launch baseline AND
    typed session probes must confirm both conductors are live. Neither path
    accepts BOTH unchanged timestamp AND unchanged status text. Timestamp
    advance alone (without typed live proof) fails closed.
4.7 Treat governed-markdown authority the same way: prefer typed
    `ProjectGovernance` outputs such as `doc_policy`, `doc_registry`, and
    parsed `plan_registry` entries when those projections are available, but
    keep the reviewed markdown `## Session Resume` content as the canonical
    restart surface. `startup-context` / `WorkIntakePacket` may consume typed
    `SessionResumeState` for one selected plan target, but that projection is
    a bounded startup read, not a replacement for the reviewed markdown
    authority itself.
4.7.0 Docs-routing follows that same rule now: `check-router` /
    `docs-check` should classify governed markdown from typed doc authority
    (`DocRegistry` plus repo-owned surface context) before falling back to
    generic path buckets. The governed-doc routing helper should also prefer
    typed `ProjectGovernance` doc paths (`docs_authority`, `DocRegistry`,
    `PathRoots`, tracker/index roots) for maintainer docs before it consults
    surface-generation context fallbacks, and empty `docs_check` policy
    sections must not silently recreate VoiceTerm maintainer-doc
    requirements in another repo.
4.7.1 Preserve the product boundary while doing that work: in portable
    runtime/tooling layers, treat VoiceTerm as a consumer of the governance
    platform rather than the universal repo shape. New portable code should
    resolve docs, plans, artifact roots, bridge/review state, and generated
    AI bootstrap instructions through `ProjectGovernance` / repo-pack
    authority. If that authority is missing, fail closed or stay in explicit
    compatibility mode; do not silently revive VoiceTerm defaults.
4.7.2 Apply the same fail-closed rule to typed runtime parsing: partial
    `ProjectGovernance` payloads and startup receipt helpers must preserve
    empty doc/plan/report roots unless real governance or an explicitly
    activated repo pack supplied them, rather than materializing
    `AGENTS.md`, `dev/active/*`, or `dev/reports/*` as hidden defaults.
4.7.3 Treat deterministic validation contracts the same way: the portable
    authority is a runner-agnostic validator contract, not one repo's test
    runner. This repo may use pytest-first adapters for Python slices, but
    the shared architecture must stay open to `cargo test`, JS runners, and
    other deterministic validators through typed validator refs. Passing
    validators may widen weaker automation modes only inside the exact
    finding-scoped validation plan; repo-wide coverage percentages or generic
    green suites are weighting signals, not the autonomy gate, and they must
    never override explicit human `approval_required`.
4.8 After fixing a meaningful issue, verify both levels before handoff: the
    local defect must be fixed, and the chosen prevention/absorption path must
    either be landed and validated or explicitly deferred/waived with the
    reason recorded in repo-visible state. Passing tests alone is not
    sufficient closure when the issue exposed a reusable architecture gap.
5. Keep changes scoped: ignore unrelated diffs unless user asks.

## Prerequisites

Required tools (install before running any bundle):

- **Rust toolchain**: `rustup` with `1.88.0+` (`rustup update stable`)
- **Python**: `3.11+` (`python3 --version`)
- **cargo-deny**: `cargo install cargo-deny --locked`
- **markdownlint-cli**: `npm install -g markdownlint-cli@0.45.0`
- **GitHub CLI**: `gh auth status -h github.com`
- **jscpd** (optional, duplication audits): `npm install -g jscpd`

Interpreter note:
- `devctl` now keeps repo-owned Python subprocesses on the interpreter that
  launched `dev/scripts/devctl.py` (checks, probes, and `guard-run`
  follow-ups). If local `python3` is older than the repo requirement, invoke
  `python3.11 dev/scripts/devctl.py ...` so nested guard runs stay on the same
  runtime.

Verify with: `python3 dev/scripts/devctl.py list` (exits non-zero if critical
tools are missing).

## Error recovery protocol

When a bundle command fails mid-run:

1. **Read the failure output** — identify which check failed and why.
2. **Fix the root cause** — do not skip or retry blindly.
3. **Re-run only the failed command** to confirm the fix, then re-run the full
   bundle from the start to catch cascading issues.
4. **If the fix is non-trivial**, create an MP item and document the failure in
   the active plan's progress log before continuing.
5. **Never use `--no-verify`, `set +e`, or manual workarounds** to bypass a
   failing gate without an explicit waiver recorded in the checkpoint log.
6. **AI-operated raw `cargo test` / manual test-binary runs must prefer**
   `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test ...`
   so the post-run sweep happens automatically. If a direct/raw invocation has
   already happened, immediately execute:
   `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel --with-process-sweep-cleanup`
   and confirm the `process-sweep-pre/process-sweep-post` plus
   `host-process-cleanup-post` steps report no orphaned/stale repo-related host
   processes. Without `--with-process-sweep-cleanup`, `quick` / `fast` still
   run host-side `process-cleanup --verify` by default unless
   `--no-host-process-cleanup` is passed and explicitly justified.
7. **When host process access is available**, run:
   `python3 dev/scripts/devctl.py process-cleanup --verify --format md`
   after manual tooling bundles and before handoff so
   Activity Monitor-visible repo leftovers are cleaned and re-checked against the full host
   process table. Use `python3 dev/scripts/devctl.py process-audit --strict --format md`
   when a read-only host inspection is needed or cleanup must be intentionally skipped. If verify stays red only because recent active local work is still running, rerun the cleanup/audit once that local work finishes; freshly detached repo-related helpers now keep strict audit/verify red immediately even before they age into the orphan bucket.
   Registered review-channel conductors are different: session-registry
   authority keeps them in supervised-conductor state even when headless launch
   wrappers intentionally reparent to PID 1; unregistered detached helpers
   still fail strict audit/verify.
7.1 **When reproducing or watching long-running local host leaks**, run:
    `python3 dev/scripts/devctl.py process-watch --cleanup --strict --stop-on-clean --iterations <n> --interval-seconds <s> --format md`
    so the host table is re-audited on a cadence until zero repo-related
    processes remain; this watcher now exits zero once it actually recovers to
    a clean host snapshot.

## Engineering quality contract (required)

For non-trivial Rust runtime/tooling changes, contributors must:

1. Validate design/implementation against official references before coding:
   - Rust Book: `https://doc.rust-lang.org/book/`
   - Rust Reference: `https://doc.rust-lang.org/reference/`
   - Rust API Guidelines: `https://rust-lang.github.io/api-guidelines/`
   - Rustonomicon (unsafe/FFI): `https://doc.rust-lang.org/nomicon/`
   - Standard library docs: `https://doc.rust-lang.org/std/`
   - Clippy lint index: `https://rust-lang.github.io/rust-clippy/master/`
2. Keep naming and ownership explicit: names should describe behavior, modules
   should keep one responsibility, and public APIs should expose stable
   intent-based contracts.
3. Treat technical debt as explicit debt: `#[allow(...)]`, non-test
   `unwrap/expect`, and oversized files/functions require documented rationale
   and a follow-up MP item when not resolved immediately.
4. Enforce function size limits: Rust functions must stay under **100 lines**,
   Python functions under **150 lines** (`code_shape` guard). Existing
   exceptions are tracked in `code_shape_policy.py` with expiry dates; new
   oversized functions require a `FunctionShapeException` with owner, expiry,
   and decomposition reason before merge.
   When a module exceeds the file soft limit (Python 350, Rust 900), split
   private helper clusters into a sibling module and re-export public symbols
   from the original path for backward compatibility.
5. Prefer consolidation over duplication: extract shared helpers instead of
   repeating logic across overlays/themes/settings/status surfaces. The
   `function_duplication` guard blocks new identical function bodies (>= 6
   lines) across different files; if you need the same logic in two places,
   extract it to a shared module and import.
6. Keep subprocess semantics explicit in repo-owned Python tooling/app code:
   every `subprocess.run(...)` call must pass `check=` intentionally instead of
   relying on the default.
7. Broad Python exception handlers in repo-owned tooling/app code require an
   explicit nearby rationale comment
   (`broad-except: allow reason=...`) instead of silent fail-soft behavior.
8. Record references consulted in handoff for non-trivial Rust changes.

## Review probe suite — AI design-quality enforcement (required)

Review probes are heuristic scanners that detect design-quality regressions
commonly produced by AI agents. Unlike hard guards (exit 0/1), probes always
exit 0 and emit structured `risk_hints` in JSON format. They are the
**second layer** of quality enforcement:

| Layer | Purpose | Exit behavior | Registration |
|---|---|---|---|
| **A — Hard guards** | Block regressions | exit 1 on violation | `quality_policy.py` built-in guard registry + `dev/config/devctl_repo_policy.json` enablement |
| **B — Review probes** | Surface design smells | always exit 0 | `quality_policy.py` built-in probe registry + `dev/config/devctl_repo_policy.json` enablement |
| **C — AI investigative review** | Deep contextual analysis | advisory | manual / future |

### Active probes

| Probe | Detects | Python | Rust |
|---|---|---|---|
| `probe_concurrency` | Nested lock acquisition, mutex+spawn without Arc, relaxed atomics with multi-flag, poison recovery | — | yes |
| `probe_design_smells` | Excessive `getattr()` density, untyped `object` params with attribute access, format helper sprawl | yes | — |
| `probe_boolean_params` | Functions with 3+ boolean parameters (unreadable call sites) | yes | yes |
| `probe_stringly_typed` | String-literal dispatch chains that should be enums | yes | yes |
| `probe_blank_line_frequency` | Excessive blank-line gaps that make function or module logic read as fragmented instead of cohesive | yes | yes |
| `probe_identifier_density` | Dense short or opaque identifier mixes that usually signal unreadable local naming | yes | yes |
| `probe_term_consistency` | Legacy public words and mixed term families inside configured repo-owned code/docs surfaces | yes | — |
| `probe_cognitive_complexity` | Branch-heavy control flow that is hard to review, test, or safely modify | yes | yes |
| `probe_fan_out` | Functions or modules touching too many collaborators, suggesting orchestration sprawl | yes | yes |
| `probe_unwrap_chains` | `.unwrap()`/`.expect()` chains in production code (should use `?` operator) | — | yes |
| `probe_clone_density` | Excessive `.clone()` calls suggesting ownership confusion (Arc::clone excluded) | — | yes |
| `probe_type_conversions` | Redundant type conversion chains (`.as_str().to_string()` round-trips) | — | yes |
| `probe_magic_numbers` | Unnamed numeric literals in slice operations that should be named constants | yes | — |
| `probe_dict_as_struct` | Functions returning dicts with 5+ keys that should be dataclasses/TypedDict | yes | — |
| `probe_unnecessary_intermediates` | Assign-then-return patterns with generic variable names (`result`, `ret`, `output`) | yes | — |
| `probe_vague_errors` | `bail!()`/`anyhow!()` error messages without runtime context variables | — | yes |
| `probe_side_effect_mixing` | Python functions that mix orchestration or mutation with value-shaping logic in one body | yes | — |
| `probe_defensive_overchecking` | 3+ consecutive `isinstance()` checks on the same variable | yes | — |
| `probe_single_use_helpers` | Private functions (`_name`) called only once in the file (indirection without reuse) | yes | — |
| `probe_exception_quality` | Suppressive broad handlers and generic exception translation without runtime context | yes | — |
| `probe_compatibility_shims` | Missing/expired shim metadata, unresolved shim targets, and shim-heavy roots/families | yes | — |
| `probe_tuple_return_complexity` | Functions returning tuples with 3+ elements that should become named structs | — | yes |
| `probe_mutable_parameter_density` | Rust functions carrying too many mutable parameters, indicating ownership or orchestration overload | — | yes |
| `probe_match_arm_complexity` | Rust `match` arms with too much inline logic instead of extracted helpers or richer types | — | yes |

### When agents must run probes

Run probes after **any** of these events:
1. Creating a new module or file with business logic.
2. Refactoring or restructuring existing code (module splits, API changes).
3. Adding new function signatures with 3+ parameters.
4. Introducing string-based dispatch (`match`, `if/elif` chains on strings).
5. Writing concurrent/async code with shared mutable state.

Quick command: `python3 dev/scripts/devctl.py check --profile ci` runs all
hard guards **and** review probes. `python3 dev/scripts/devctl.py probe-report --format md`
is the canonical aggregated probe surface when an agent needs ranked cleanup
order, topology context, or a self-contained handoff packet. It refreshes
`review_targets.json`, `file_topology.json`, `review_packet.{json,md}`, and
hotspot `hotspots.{mmd,dot}` artifacts under `dev/reports/probes/latest/`.
Repo-root `.probe-allowlist.json` entries apply to that canonical `devctl`
path too: `design_decision` entries stay visible in a typed decision-packet
bucket instead of active debt. Matching is by `file` + `symbol` + `probe`
when the allowlist entry declares a probe id; omit `probe` only when the same
decision intentionally applies across all probes for that symbol. The root
payload may carry `schema_version: 1` and
`contract_id: "ProbeAllowlist"`. Those packets are for AI agents and human
reviewers alike; `decision_mode` only controls whether the agent may
auto-apply, should recommend, or must explain and wait for approval.
When the guard/probe surface itself changes (new `probe_*.py` or `check_*.py`
entrypoints, `script_catalog.py`, `quality_policy_defaults.py`,
`dev/config/quality_presets/*.json`, or `dev/config/devctl_repo_policy.json`),
also run `python3 dev/scripts/devctl.py quality-policy --format md` plus
`python3 dev/scripts/devctl.py render-surfaces --format md`; use `--write`
when the policy-owned AI/dev instruction surfaces need regeneration.
When the platform contract surface itself changes (`dev/scripts/devctl/platform/**`,
shared runtime contract models, probe/report schema constants, or
`repo_governance.surface_generation` contract-routing text), also run
`python3 dev/scripts/checks/check_platform_contract_closure.py` plus
`python3 dev/scripts/devctl.py platform-contracts --format md`. The same
closure path now also includes `python3 dev/scripts/checks/check_contract_connectivity.py`
and `python3 dev/scripts/checks/check_governance_closure.py` when the slice
widens typed planning/backlog contracts or other consumer-route proof
surfaces, because `PlanPhase`, `PlanTask`, and `FindingBacklog` are now part
of the AST-backed field-route inventory and dead typed contracts must fail the
self-governance lane too.
Use `python3 dev/scripts/devctl.py system-picture --format md` when that same
platform/governance change should refresh the generated external-review proof
reducer or its tracked proof-ledger projection.
The same platform layer now also owns the scheduler-facing planning reducer:
`dev/scripts/devctl/platform/planning_ir.py` builds `PlanningIRSnapshot`
beside `SystemPicture` by joining typed plan ownership, recent
governance-review findings, context-graph `scoped_by` edges, and
review/work-intake runtime state into bounded scheduling outputs
(`next_best_slices`, `concurrent_writer_conflicts`, `unowned_hot_paths`,
`plan_finding_mismatches`). Treat that reducer as the authoritative
multi-agent scheduling seam; do not reconstruct the same state from
`bridge.md` prose or ad hoc startup-summary parsing.
The same platform layer also owns bounded coordination/topology reducers for
live multi-agent posture. `coordination_snapshot.py` is the first repo-visible
projection consumed by `system-picture`; it joins startup/work-intake posture,
review-state collaboration, delegated-worktree receipts, ready gates, and
conflict summaries into one answer for declared-vs-observed topology, fanout
posture, worktree strategy, and resync requirement. The adjacent
`coordination_topology.py` contract is the richer shared topology surface for
participant rows, delegated worktrees, ready gates, fanout safety, and
resync command. Prefer those typed reducers over recomputing the same answers
from `runtime_counts`, `reviewer_runtime`, bridge markdown, or startup-summary
prose in each consumer.
Keep `startup_surface_tokens` populated on every current platform contract row
so `platform-contracts`, startup surfaces, and closure guards keep projecting
the same contract inventory.
For probes only:
```bash
# Canonical aggregated probe packet:
python3 dev/scripts/devctl.py probe-report --format md
python3 dev/scripts/devctl.py probe-report --format terminal

# Direct script entrypoint (fallback):
python3 dev/scripts/checks/run_probe_report.py --format md
python3 dev/scripts/checks/run_probe_report.py --format terminal

# Individual probes:
python3 dev/scripts/checks/probe_concurrency.py
python3 dev/scripts/checks/probe_design_smells.py
python3 dev/scripts/checks/probe_boolean_params.py
python3 dev/scripts/checks/probe_stringly_typed.py
python3 dev/scripts/checks/probe_blank_line_frequency.py
python3 dev/scripts/checks/probe_identifier_density.py
python3 dev/scripts/checks/probe_term_consistency.py
python3 dev/scripts/checks/probe_cognitive_complexity.py
python3 dev/scripts/checks/probe_fan_out.py
python3 dev/scripts/checks/probe_unwrap_chains.py
python3 dev/scripts/checks/probe_clone_density.py
python3 dev/scripts/checks/probe_type_conversions.py
python3 dev/scripts/checks/probe_magic_numbers.py
python3 dev/scripts/checks/probe_dict_as_struct.py
python3 dev/scripts/checks/probe_unnecessary_intermediates.py
python3 dev/scripts/checks/probe_vague_errors.py
python3 dev/scripts/checks/probe_side_effect_mixing.py
python3 dev/scripts/checks/probe_defensive_overchecking.py
python3 dev/scripts/checks/probe_single_use_helpers.py
python3 dev/scripts/checks/probe_exception_quality.py
python3 dev/scripts/checks/probe_compatibility_shims.py
python3 dev/scripts/checks/probe_tuple_return_complexity.py
python3 dev/scripts/checks/probe_mutable_parameter_density.py
python3 dev/scripts/checks/probe_match_arm_complexity.py
```

Default AI operating rule:
- Run `python3 dev/scripts/devctl.py check --profile ci` after those changes.
- Run `python3 dev/scripts/devctl.py probe-report --format md` when the change
  needs prioritization, human handoff, or AI follow-up packets.
- Use `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test ...`
  for raw Rust tests / test binaries so post-run hygiene is enforced
  automatically.

### Acting on probe findings

When a probe emits risk hints, agents MUST:
1. Read the `ai_instruction` field — it contains targeted remediation guidance.
2. Fix `high` severity hints before handoff (these are unambiguous smells).
2.1 When a live AI consumer attaches probe guidance (for example Ralph or an
    autonomy `loop-packet` draft), treat that guidance as the default repair
    plan unless you can justify waiving it with a concrete reason. Keep the
    resulting guidance disposition visible in the route's report/packet
    surface so adoption is measurable, and use
    `governance-review --record --guidance-id ... --guidance-followed ...`
    when the finding is adjudicated so the adoption signal survives outside
    the prompt text. If the matched carried decision packet sets
    `decision_mode=approval_required`, do not mutate through that route until
    the approval step is explicit in the packet/report surface.
3. Document `medium` severity hints in handoff notes if not fixed immediately.
4. Record adjudicated probe/guard outcomes with
   `python3 dev/scripts/devctl.py governance-review --record ...` when a hint
   is confirmed, fixed, deferred, waived, or judged false-positive so the repo
   maintains a durable finding-quality ledger before handoff.
4.1 Treat every recorded `false_positive` verdict as a rule-quality defect to
    investigate. Before closing the slice, document why the signal was wrong
    and whether the fix belongs in rule narrowing, richer context capture,
    severity demotion, repo-pack policy tuning, or explicit allowlisting.
5. Never suppress probe output — probes are advisory but findings are real.

### Adding new probes

New probes must follow the established pattern:
1. Create `dev/scripts/checks/probe_<name>.py` using `probe_bootstrap.py`.
2. Register in `script_catalog.py::PROBE_SCRIPT_FILES`.
3. Register built-in probe metadata in `dev/scripts/devctl/quality_policy_defaults.py` and enable it in the relevant preset/policy file (`dev/config/quality_presets/*.json`, `dev/config/devctl_repo_policy.json`) when this repo should run it by default.
4. Include per-signal `AI_INSTRUCTIONS` dict for targeted remediation.
5. Always exit 0 — probes emit hints, never block CI.
6. Skip test files (`_is_test_path`) — test code has different design rules.

Portable policy note:
- Built-in guard/probe capability metadata now lives in
  `dev/scripts/devctl/quality_policy_defaults.py`, with resolution/inheritance
  handled by the rest of the `quality_policy*.py` stack.
- Built-in portable presets now live in `dev/config/quality_presets/*.json`.
- Repo-local enablement/default arguments live in
  `dev/config/devctl_repo_policy.json`.
- The repo policy file and any touched preset JSON files are committed source
  of truth, not local-only scratch config. If local validation depends on a
  policy/preset change, commit those `dev/config/**` files in the same slice so
  CI resolves the same guard/probe surface.
- Use `python3 dev/scripts/devctl.py quality-policy --format md` to inspect the
  resolved active guard/probe set, scopes, and warnings before reusing the
  engine somewhere else.
- Use `python3 dev/scripts/devctl.py render-surfaces --format md` to inspect
  policy-owned instruction/starter surfaces from
  `repo_governance.surface_generation`, and `--write` to regenerate them after
  template or context changes.
- Use `python3 dev/scripts/checks/check_platform_contract_closure.py` when the
  shared platform blueprint, runtime contract models, artifact schema
  metadata, or startup-surface routing changes so `platform-contracts`,
  emitted packet metadata, and AI/dev startup surfaces cannot drift apart.
- When a platform contract row is widened or added, keep
  `startup_surface_tokens` current on that row and keep compatibility
  projections explicit so startup/status consumers do not grow a second
  authority path.
- When a critical contract field gains a live consumer route (for example
  `Finding.ai_instruction` flowing from probe artifacts into the Ralph prompt),
  extend `check_platform_contract_closure.py` with a deterministic field-route
  proof so produced-but-unconsumed regressions fail before handoff. The
  field-route helper `_source_contains_any` in
  `dev/scripts/checks/platform_contract_closure/field_routes_surface_state.py`
  is AST-backed as of 2026-04-06: it parses candidate modules, strips
  docstrings, and matches exact identifier, attribute, dotted-chain, or
  string-literal references so a module docstring mention or prefix
  substring overlap can never satisfy the proof. New field-route tokens
  must be enumerated explicitly if a consumer surface uses a renamed
  projection (for example `push_eligible_now` beside `push_eligible`).
- The control-plane parity guard
  (`dev/scripts/checks/platform_contract_closure/field_routes_parity.py`)
  is the cross-surface "all 5 surfaces agree" proof for
  `ControlPlaneReadModel`. As of 2026-04-07 `PARITY_FIELDS` also covers
  the remote-control mode signals `reviewer_mode` and
  `operator_interaction_mode`, and `_extract_from_auto_mode` reads
  `next_action` straight from `inputs.push_decision_action` without
  falling back to `model.next_action`. A regression test pins that a
  broken `inputs_from_read_model` mapping surfaces as a typed
  `next_action` divergence instead of a silent green pass. When you
  touch a governance surface that exposes either mode signal, mirror
  the field on the surface's `_control_plane_section` (or equivalent
  extractor) so the comparator catches mode-field drift; the
  `SessionCachePacket` projection used by session-resume intentionally
  omits `reviewer_mode` because it has no direct slot for it, and the
  comparator skips absent fields.
- Shared `ViolationRecord` convergence for non-check signal sources lives
  in `dev/scripts/devctl/runtime/` alongside `check_result_models.py`.
  As of 2026-04-06 two one-way, non-mutating adapters project
  domain-specific findings onto the shared contract:
  `probe_report_violations.probe_report_to_violations(report)` maps
  enriched `probe-report` `risk_hints` into
  `tuple[ViolationRecord, ...]`, and
  `governance_review_violations.governance_review_recent_to_violations(report)`
  projects the **recent window** of `governance-review` findings
  (from `report["recent_findings"]`, not the full live open-governance
  set) with the default include verdict `("confirmed_issue",)`. Both
  adapters share
  `dev/scripts/devctl/runtime/violation_adapter_support.py` helpers
  (`coerce_stripped_str`, `coerce_positive_int`, `build_bounded_summary`)
  so dashboard, startup summary, and operator surfaces can render
  probe and governance findings through the same
  `render_check_result_text` / `render_check_result_md` path without a
  domain-specific renderer.
- Once a field has more than one declared live consumer, keep that same guard
  honest at the family level too: record the expected route family and fail if
  any declared consumer disappears, not only when the first surviving route
  still passes.
- When that new route still needs a compatibility seam, keep one canonical
  artifact authority and structured routing keys. Do not let AI consumers
  silently negotiate between multiple artifacts or depend on prose-derived
  matching once typed fields exist; track any temporary fallback in the active
  plan and extend the relevant guard/probe so the seam cannot become
  permanent by accident.
- Use `python3 dev/scripts/devctl.py governance-export --format md` when the
  whole governance stack, latest reports, and policy/templates need to be
  handed to another repo or model outside this checkout.
- Use `python3 dev/scripts/devctl.py governance-review --format md` to inspect
  the current adjudicated finding ledger, and `--record` to append one reviewed
  guard/probe outcome before the summary is regenerated.
- When `governance-review --record` uses `--prevention-surface guard` or
  `--prevention-surface probe`, the command also appends a
  `GuardPromotionCandidate` row to the repo-pack-resolved promotion queue.
  Inspect the queue file directly, and use the `--record` JSON summary's
  candidate id/path metadata for the row just recorded instead of carrying
  those follow-up candidates only in audit prose or chat notes.
- `devctl` command telemetry is auto-emitted to
  `dev/reports/audits/devctl_events.jsonl`; do not hand-edit that ledger.
  The operator rule is:
  - use `devctl` commands for work that should land in command telemetry,
  - use `governance-review --record` for adjudicated finding outcomes,
  - use active-plan markdown for prose session continuity and handoff state.
- Use `python3 dev/scripts/devctl.py governance-bootstrap --target-repo <path> --format md`
  before first-run pilots against copied repos or submodule snapshots that may
  carry broken `.git` indirection.
- `check`, `probe-report`, and `governance-export` accept `--adoption-scan`
  for full current-worktree onboarding scans when a repo has no trustworthy
  baseline yet.
- External-adopter proof is a closure loop, not a one-pass findings dump:
  bootstrap the copied repo, run `orphan-inventory --repo-path` for scanner
  proof in scope, then `probe-report` / `check` with `--repo-path --adoption-scan`,
  and classify the first failure before
  widening scope. If the run crashes, leaks this repo's paths, or assumes
  VoiceTerm-only policy/layout, treat that as a governance-engine bug and fix
  it here before importing adopter debt. After the run is honest, import raw
  target-repo findings with `governance-import-findings`, record adjudicated
  outcomes with `governance-review --record`, and keep closure ordering in the
  owning active plan so "engine bug", "confirmed adopter issue", "false
  positive", and "workflow gap" do not collapse into one backlog bucket.
  Do not widen the pilot corpus while the current proof set still exposes
  unfixed engine bugs unless the deferral plus exit criteria are written into
  the owning active plan.
- Keep the external-adopter evidence surfaces split by role:
  `governance-import-findings` owns the append-only raw import stream under
  managed `dev/reports/governance/external_*.jsonl` / summary roots,
  `governance-review` owns adjudicated verdicts for the findings that were
  actually reviewed, and `governance-quality-feedback` is the rollup surface
  that tells us whether imported findings are becoming accurate policy signal
  instead of a growing pile of unreviewed rows.
- `startup-context` and governed `push` are still target-local authority
  surfaces today, not generic `--repo-path` scans. When external proof needs
  honest startup/push validation, run it from a target repo that contains the
  exported governance stack (or explicitly track the missing adopter-startup
  contract in the active plan) instead of pretending an engine-checkout
  `startup-context` receipt proved the target repo.
- `check`, `probe-report`, `status --probe-report`, `report --probe-report`,
  `triage --probe-report`, and `render-surfaces` accept
  `--quality-policy <path>`, and
  `DEVCTL_QUALITY_POLICY` provides the same override through the environment.
- When a repo-local policy path becomes a repeated operator workflow, add a
  short wrapper command instead of forcing maintainers to keep using the raw
  policy-path form. Current examples: `launcher-check`,
  `launcher-probes`, and `launcher-policy`.
- To reuse this system in another repo, prefer swapping the repo-policy file
  over editing `check` or `probe-report` orchestration code.

## Cross-architecture quality enforcement (required)

All quality guard tooling MUST align across the three codebase architectures.
The same enforcement patterns apply everywhere — no architecture gets a pass.
Tandem-consistency checks (`check_tandem_consistency.py`) prefer typed
`review_state.json` authority when available; bridge-text fallback is used
only for checks without a typed equivalent (`reviewed_hash_honesty`,
`plan_alignment`, `launch_truth`). When those checks need live review-channel
freshness they must refresh the bridge-backed typed projection before reading
`current_session`, so stale on-disk snapshots do not outrank the repo-owned
status writer.

| Architecture | Language | Guard entry point | CI workflow |
|---|---|---|---|
| **voiceterm binary** | Rust | `devctl check --profile ci` (clippy, code-shape, serde, panic-policy, security-footguns) | `rust_ci.yml` |
| **operator console** | Python/PyQt6 | `devctl check --profile ci` (facade-wrappers, god-class, nesting-depth, global-mutable, dict-schema, structural-similarity) | `tooling_control_plane.yml` |
| **devctl tooling** | Python | `devctl check --profile ci` (all Python guards) | `tooling_control_plane.yml` |
| **iOS mobile app** | Swift | `devctl mobile-status` + Xcode build verification | `tooling_control_plane.yml` |

### Ralph loop: AI-driven remediation across all architectures

The Ralph loop (`coderabbit_ralph_loop.yml`) is the closed-loop remediation
pipeline. When CodeRabbit flags issues, AI evaluates each finding, filters
false positives, and fixes real issues — then re-runs CodeRabbit to verify.

**Loop flow:**
1. CodeRabbit reviews code → produces `backlog-medium.json` (medium/high findings)
2. Ralph loop reads backlog → invokes `ralph_ai_fix.py` (the AI fix wrapper)
3. AI fix wrapper feeds findings to Claude Code → AI evaluates + fixes valid issues
4. AI fix wrapper runs architecture-specific validation (Rust tests, Python tests, etc.)
5. AI fix wrapper commits + pushes → CodeRabbit re-reviews the new SHA
6. Ralph loop checks new backlog → repeats until clean or max attempts reached
7. If unresolved after max attempts → escalation comment requests human review

**AI fix wrapper** (`dev/scripts/coderabbit/ralph_ai_fix.py`):
- Reads `RALPH_BACKLOG_DIR/backlog-medium.json`
- Reads canonical probe guidance from `dev/reports/probes/review_targets.json`
  when probe artifacts are available; `review_packet.json` remains a separate
  artifact for other consumers, not a second Ralph guidance authority
- Maps finding categories to architectures (Rust, PyQt6, devctl, iOS)
- Invokes Claude Code with structured prompt including false-positive filtering
- Runs architecture-specific checks before committing
- Prefer structured backlog `path` / `line` fields for matching probe
  guidance to CodeRabbit items; summary-string parsing is compatibility-only
  for older backlog payloads
- Policy-gated via `control_plane_policy.json` allowlist

**Cross-architecture guard alignment rules:**
1. Every new guard script MUST be registered in the script catalog and wired
   through either typed quality-policy or a direct bundle/workflow enforcement
   lane when this repo should run it by default.
2. Every repo-enabled hard guard MUST have a step in `tooling_control_plane.yml`.
   The current Phase 3/4 remote-commit surface-convergence closure keeps
   `check_review_snapshot_freshness.py` and
   `check_review_surface_consistency.py` in both
   `tooling_control_plane.yml` and `release_preflight.yml`. The snapshot
   freshness guard intentionally accepts a trailing ReviewSnapshot receipt
   chain when the embedded snapshot binds to that receipt commit's parent code
   state or to any ancestor in a contiguous managed bridge/ReviewSnapshot
   receipt chain; the governed receipt may refresh
   `dev/audits/REVIEW_SNAPSHOT.md` alone, atomically with the generated
   `bridge.md` compatibility projection, or as a pathscoped
   policy-owned generated-surface receipt from `render-surfaces --write`
   before the docs gates run. Any other HEAD drift still fails closed. The
   managed `install-git-hooks`
   surface now installs the pre-commit projection hook, the post-commit
   receipt hook that delegates to `devctl review-snapshot --write
   --receipt-commit`, and a blocking pre-push hook that refuses raw `git push`
   unless the nested push came from `devctl push --execute`, so raw commits
   still produce the same receipt shape while raw publication stays on the
   governed path. The governed push path accepts that receipt shape when the
   receipt HEAD, or any contiguous managed bridge/ReviewSnapshot receipt
   ancestor above it, leads back to the active `PushAuthorizationRecord`;
   stale detached pipeline records are ignored in `single_agent` mode, while
   active dual-agent and current pipeline targets still require exact typed
   authorization. After a managed receipt moves HEAD, `devctl push` runs
   `render-surfaces --write` for tracked non-local repo-pack outputs and
   `review-snapshot --write --receipt-commit` inside the same preflight
   autocommit batch, then refreshes the event-backed review-channel projection
   bundle plus startup/context-graph surfaces before trusting preflight or
   publication authorization. The selected receipt commit pathspec must
   preserve staged-only next-commit intent. The typed ReviewSnapshot surface
   now also carries first-class probe run-state/artifact refs plus current
   push receipt/authorization refs so external review consumers can cite
   emitted evidence instead of command-only prose.
3. Guard output format MUST support `--since-ref`/`--head-ref` for growth-based gating.
4. The Ralph AI fix wrapper MUST run architecture-specific validation after fixes.
5. No architecture may bypass the Ralph loop — all CodeRabbit findings across Rust,
   Python, and iOS are processed through the same pipeline.

**Configuration:**
- Policy file: `dev/config/control_plane_policy.json`
- Fix command allowlist: `triage_loop.allowed_fix_command_prefixes`
- Autonomy gate: `AUTONOMY_MODE=operate` required for fix execution
- Branch gate: only `develop` branch is allowlisted for automated fixes

## Branch policy (required)

- `develop`: integration branch for normal feature/fix/docs work.
- `master`: release/tag branch and rare hotfix branch.

Non-release work flow:

1. `git fetch origin`
2. `git checkout develop`
3. `git pull --ff-only origin develop`
4. `git checkout -b feature/<topic>` or `git checkout -b fix/<topic>`
5. Implement and run required checks.
6. Require user local validation before push:
   - Ask the user to test locally and confirm go-ahead before any non-release
     `git push`.
   - If the user asks to test before commit, keep changes uncommitted until
     that local validation completes.
7. Commit the bounded slice/checkpoint only after explicit user approval.
8. Push the short-lived branch only after explicit user approval, a current
   review gate, and a green `python3 dev/scripts/devctl.py push` validation.
9. Merge short-lived branch into `develop` only after required checks pass.

Routine helper:

- `python3 dev/scripts/devctl.py push` runs the canonical non-mutating
  branch-push validation path from repo policy (`repo_governance.push`) and
  now reports typed push stages (`validation_ready`, `published_remote`,
  `post_push_green`) without mutating git state. The same command also
  persists a managed latest-push artifact at `dev/reports/push/latest.json`
  so later startup/recovery can read the last typed push truth instead of
  inferring state from chat or process lifetime.
- `python3 dev/scripts/devctl.py push --execute` runs the same preflight,
  performs the current short-lived branch push, and then executes the
  configured post-push bundle. `--skip-preflight` / `--skip-post-push` are
  policy-gated under `repo_governance.push.bypass`; the repo-owned default
  should keep `allow_skip_preflight` closed unless a narrowly-scoped
  temporary override is explicitly being landed and then reverted in the same
  tracked lane. A remote update is not the
  same state as post-push green. When the persisted artifact says
  `published_remote=true` and `post_push_green=false`, treat remote
  publication as settled and repair the post-push follow-up instead of
  pushing again. Interactive runs now also emit stderr progress when remote
  publication is recorded and before each post-push step so a long post-push
  bundle does not look like "push still unresolved" to humans or AI. If a
  branch-aware diff base was resolved during preflight, the governed push path
  must carry that same `since_ref` into diff-sensitive post-push commands
  instead of resetting follow-up checks to `origin/develop`.
  Hooks/launchers should consume that typed diff base from repo-owned state,
  not recompute it independently.
  If a
  later rerun fetches the tracked branch and proves `ahead == 0`, `devctl
  push` now exits with the existing `branch_already_pushed` /
  `published_remote` receipt before router preflight so a clean already-
  published branch cannot be misclassified into a zero-diff docs lane. That
  no-op receipt must not reconstruct a stale `push_blocked` commit-pipeline
  artifact into `push_completed`; read-side publication truth comes from the
  current persisted push artifact instead.
- Shared `devctl` command execution now follows the parent command lifetime:
  inherited stdout pipes from detached descendants must not keep a completed
  governed push session open after the parent push/post-push step exits.
- A local checkpoint / clean worktree is not sufficient push proof by itself;
  the review gate and the governed `devctl push` path decide remote readiness.
- Read the typed startup/review decision, not just raw dirty-tree booleans:
  `startup-context` / `review-channel status` may now surface a four-state
  `push_decision` (`await_checkpoint`, `await_review`, `run_devctl_push`,
  `no_push_needed`).
- After any bounded checkpoint/commit, rerun
  `python3 dev/scripts/devctl.py startup-context --format summary` and follow
  that `push_decision` exactly: wait if it says `await_review`, run
  `python3 dev/scripts/devctl.py push --execute` only when it says
  `run_devctl_push`, and stop when it says `no_push_needed`.
- Governed mutation stays fail-closed on typed operator mode. `devctl commit`
  may auto-apply typed approval only in resolved `local_terminal` or
  `single_agent` modes; `unresolved`, `remote_control`, and `dual_agent`
  must post or reuse approval packets and block until an applied decision
  exists. In `remote_control` / unresolved approval mode, the governed command
  must stop at `operator_approval_pending` before it enters `vcs.commit`;
  posting the approval request is not itself permission to keep the same run
  alive past the approval boundary. Before staging or running guards, `devctl
  commit` must also honor the typed `CommitPermissionDecision`: explicit
  `implementation_permission=blocked|suspended` blocks `vcs.stage`,
  `vcs.commit`, and raw `git commit` until the routed startup/review recovery
  command is run. The one allowed exception is executor-scoped checkpoint
  authority: when startup explicitly says `advisory_action=checkpoint_allowed`
  and `push_decision=await_checkpoint` with `reviewer_gate.checkpoint_permitted=true`,
  `devctl commit` may still advance the governed checkpoint path, but raw
  `git commit` remains blocked until broader implementation authority is
  repaired. `devctl push` must reuse the repo-policy/default remote for any
  active governed pipeline and must not treat a degraded `tools_only`
  reviewer runtime as license to skip exact-head publication authorization.
  Push cleanliness now blocks only on unstaged or untracked dirty paths:
  staged-only "next commit" intent must not deadlock `devctl push` or its
  preflight auto-commit repair path. Governed stage also fails closed if the
  managed ReviewSnapshot refresh drops previously staged user content, and
  governed commit reports may now surface the approved content SHA separately
  from a trailing ReviewSnapshot receipt SHA.
  Governed push also treats a receipt commit that refreshes
  `dev/audits/REVIEW_SNAPSHOT.md` plus governed `bridge.md` as still bound to
  the parent approved code commit or another ancestor in a contiguous managed
  receipt chain; it must not force a second authorization or freshness-repair
  round just because receipt commits advanced `HEAD`.
  Governed commit/push approval is also worktree-bound now: the staged
  pipeline contract, persisted push authorization, latest-push artifact, and
  current checkout must agree on `worktree_identity`. If startup or
  `devctl push` reports a worktree mismatch, resume the owning worker lane or
  recover/restage there before asking for a fresh approval.
- If the governed push path blocks, stop at that typed decision surface. Do
  not treat a push block as a cue to substitute raw `git push`; any later
  human exception should remain a repo-owned typed override path.
- Pending packet cleanup is apply-bound, not ack-bound. Only an applied
  `commit_approval` decision may clear the live approval request queue;
  `acked` decisions and unrelated stale/history packets remain non-
  authoritative and must not collapse live packet counts on dashboard,
  status, doctor, or startup surfaces.
- The default repo quality lane now mirrors that same checkpoint discipline:
  VoiceTerm's resolved `python3 dev/scripts/devctl.py check --profile ci`
  policy includes `check_startup_authority_contract.py`, so once a local
  checkpoint exists (`ahead_of_upstream_commits > 0`), fresh dirty-worktree
  state is a blocking guard failure instead of a push-only surprise.
- Repo policy may also declare non-authoritative scratch/reference paths such
  as `convo.md` so local advisory context does not keep a reviewed branch from
  reaching the governed push path.
- `python3 dev/scripts/devctl.py sync --push` can audit/sync `develop` +
  `master` + current branch with clean-tree and fast-forward guards.

Release promotion flow:

1. Ensure `develop` checks are green.
2. Merge `develop` into `master`.
3. Tag from `master`.

If a hotfix lands on `master`, back-merge `master` to `develop` promptly.

## Dirty-tree protocol (required)

When `git status --short` is not clean:

1. Do not discard unrelated edits.
2. Edit only files needed for the current task.
3. Use commit-range checks carefully (`--since-ref`) only when the range is
   valid for current branch/repo state.
4. Note unrelated pre-existing changes in handoff when they affect confidence.

## Active-plan onboarding (adding files under `dev/active/`)

When adding any new markdown file under `dev/active/`, this sequence is required:

1. Add an entry in `dev/active/INDEX.md` with:
   - path
   - role (`tracker` | `spec` | `runbook` | `reference`)
   - execution authority
   - MP scope
   - when agents should read it
2. If the file carries execution state, reflect that scope in
   `dev/active/MASTER_PLAN.md` (the only tracker authority).
2.1 If the file is an execution plan, include marker
    `Execution plan contract: required`, one parseable metadata header, and
    sections `Scope`, `Execution Checklist`, `Progress Log`,
    `Session Resume`, and `Audit Evidence`. Follow
    `dev/active/PLAN_FORMAT.md`.
3. Update discovery links in `AGENTS.md` and `dev/README.md`
   if navigation/ownership changed.
3.1 For new active-plan/check-script/devctl-command/app/workflow surfaces, run
    `python3 dev/scripts/checks/check_architecture_surface_sync.py` before
    closing the slice.
4. Run `python3 dev/scripts/checks/check_active_plan_sync.py`.
5. Run `python3 dev/scripts/checks/check_multi_agent_sync.py`.
6. Run `python3 dev/scripts/devctl.py docs-check --strict-tooling`.
7. Run `python3 dev/scripts/devctl.py hygiene`.
8. Commit file + index + governance docs in one change.

## Task router (pick one class)

Canonical task-router authority lives in
`dev/scripts/devctl/governance/task_router_contract.py`.
The table below is a human-readable reference and must stay aligned with that
typed router.

| User story | Task class | Required bundle |
|---|---|---|
| Changed runtime behavior under `rust/src/**` | Runtime feature/fix | `bundle.runtime` |
| Changed HUD/layout/controls/flags/UI text | HUD/overlay/controls/flags | `bundle.runtime` |
| Touched perf/latency/wake/threading/unsafe/parser boundaries | Risk-sensitive runtime | `bundle.runtime` |
| Changed only user-facing docs | Docs-only | `bundle.docs` |
| Changed tooling/process/CI/governance surfaces | Tooling/process/CI | `bundle.tooling` |
| Preparing/publishing release | Release/tag/distribution | `bundle.release` |

## Context packs (load only what class needs)

### Runtime pack

- `rust/src/bin/voiceterm/main.rs`
- `rust/src/bin/voiceterm/event_loop.rs`
- `rust/src/bin/voiceterm/event_state.rs`
- `rust/src/bin/voiceterm/status_line/`
- `rust/src/bin/voiceterm/hud/`
- `dev/guides/ARCHITECTURE.md`
- `guides/USAGE.md`
- `guides/CLI_FLAGS.md`

### Voice pack

- `rust/src/bin/voiceterm/voice_control/`
- `rust/src/audio/`
- `rust/src/stt.rs`
- `rust/src/bin/voiceterm/wake_word.rs`

### PTY/lifecycle pack

- `rust/src/pty_session/`
- `rust/src/ipc/`
- `rust/src/terminal_restore.rs`

### Tooling/process pack

- `AGENTS.md`
- `dev/active/INDEX.md`
- `dev/active/review_channel.md`
- `dev/guides/DEVELOPMENT.md`
- `dev/guides/MCP_DEVCTL_ALIGNMENT.md`
- `dev/scripts/README.md`
- `dev/history/ENGINEERING_EVOLUTION.md`
- `.github/workflows/`
- `dev/scripts/devctl/commands/`

### Release pack

- `rust/Cargo.toml`
- `pypi/pyproject.toml`
- `app/macos/VoiceTerm.app/Contents/Info.plist`
- `dev/CHANGELOG.md`
- `dev/scripts/README.md`

## Command bundles (rendered reference)

Canonical command authority lives in `dev/scripts/devctl/bundle_registry.py`.
The bundle blocks below are rendered reference for human read-through and must
stay aligned with the registry.

### `bundle.bootstrap`

```bash
git status --short
git branch --show-current
git remote -v
git log --oneline --decorate -n 10
sed -n '1,220p' dev/active/INDEX.md
python3 dev/scripts/devctl.py list
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.runtime`

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py process-cleanup --verify --format md
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_system_picture_freshness.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_package_layout.py
python3 dev/scripts/checks/check_python_subprocess_policy.py
python3 dev/scripts/checks/check_mutation_bypass_graph_closure.py
python3 dev/scripts/checks/check_workflow_shell_hygiene.py
python3 dev/scripts/checks/check_workflow_action_pinning.py
python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations
python3 dev/scripts/checks/check_compat_matrix.py
python3 dev/scripts/checks/compat_matrix_smoke.py
python3 dev/scripts/checks/check_naming_consistency.py
python3 dev/scripts/checks/check_rust_test_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
python3 dev/scripts/checks/check_rust_compiler_warnings.py
python3 dev/scripts/checks/check_serde_compatibility.py
python3 dev/scripts/checks/check_rust_runtime_panic_policy.py
python3 dev/scripts/checks/check_facade_wrappers.py
python3 dev/scripts/checks/check_god_class.py
python3 dev/scripts/checks/check_mobile_relay_protocol.py
python3 dev/scripts/checks/check_daemon_state_parity.py
python3 dev/scripts/checks/check_nesting_depth.py
python3 dev/scripts/checks/check_parameter_count.py
python3 dev/scripts/checks/check_python_dict_schema.py
python3 dev/scripts/checks/check_python_typed_seams.py
python3 dev/scripts/checks/check_python_global_mutable.py
python3 dev/scripts/checks/check_python_design_complexity.py
python3 dev/scripts/checks/check_python_cyclic_imports.py
python3 dev/scripts/checks/check_python_suppression_debt.py
python3 dev/scripts/checks/check_structural_similarity.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.docs`

```bash
python3 dev/scripts/devctl.py docs-check --user-facing --since-ref origin/develop
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_system_picture_freshness.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_package_layout.py
python3 dev/scripts/checks/check_python_subprocess_policy.py
python3 dev/scripts/checks/check_mutation_bypass_graph_closure.py
python3 dev/scripts/checks/check_workflow_shell_hygiene.py
python3 dev/scripts/checks/check_workflow_action_pinning.py
python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations
python3 dev/scripts/checks/check_compat_matrix.py
python3 dev/scripts/checks/compat_matrix_smoke.py
python3 dev/scripts/checks/check_naming_consistency.py
python3 dev/scripts/checks/check_rust_test_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
python3 dev/scripts/checks/check_rust_compiler_warnings.py
python3 dev/scripts/checks/check_serde_compatibility.py
python3 dev/scripts/checks/check_rust_runtime_panic_policy.py
python3 dev/scripts/checks/check_facade_wrappers.py
python3 dev/scripts/checks/check_god_class.py
python3 dev/scripts/checks/check_mobile_relay_protocol.py
python3 dev/scripts/checks/check_daemon_state_parity.py
python3 dev/scripts/checks/check_nesting_depth.py
python3 dev/scripts/checks/check_parameter_count.py
python3 dev/scripts/checks/check_python_dict_schema.py
python3 dev/scripts/checks/check_python_typed_seams.py
python3 dev/scripts/checks/check_python_global_mutable.py
python3 dev/scripts/checks/check_python_design_complexity.py
python3 dev/scripts/checks/check_python_cyclic_imports.py
python3 dev/scripts/checks/check_python_suppression_debt.py
python3 dev/scripts/checks/check_structural_similarity.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.tooling`

```bash
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene --strict-warnings --ignore-warning-source mutation_badge --ignore-warning-source publications
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md
python3 dev/scripts/checks/check_agents_contract.py
python3 dev/scripts/checks/check_release_version_parity.py
python3 dev/scripts/checks/check_repo_url_parity.py
python3 dev/scripts/checks/check_guard_enforcement_inventory.py
python3 dev/scripts/checks/check_architecture_surface_sync.py
python3 dev/scripts/checks/check_review_snapshot_freshness.py
python3 dev/scripts/checks/check_guide_contract_sync.py
python3 dev/scripts/checks/check_instruction_surface_sync.py
python3 dev/scripts/checks/check_bundle_registry_dry.py
python3 dev/scripts/checks/check_bundle_workflow_parity.py
python3 dev/scripts/checks/check_platform_layer_boundaries.py
python3 dev/scripts/checks/check_platform_contract_closure.py
python3 dev/scripts/checks/check_contract_connectivity.py
python3 dev/scripts/checks/check_typed_enum_connectivity.py
python3 dev/scripts/checks/check_platform_contract_sync.py
python3 dev/scripts/checks/check_review_channel_bridge.py
python3 dev/scripts/checks/check_startup_authority_contract.py
python3 dev/scripts/checks/check_review_surface_consistency.py
python3 dev/scripts/checks/check_tandem_consistency.py
python3 dev/scripts/checks/check_governance_closure.py
python3 dev/scripts/checks/check_package_layout.py --fail-on-baseline-debt --baseline-debt-root dev/scripts/devctl/commands
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_system_picture_freshness.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_package_layout.py
python3 dev/scripts/checks/check_python_subprocess_policy.py
python3 dev/scripts/checks/check_mutation_bypass_graph_closure.py
python3 dev/scripts/checks/check_workflow_shell_hygiene.py
python3 dev/scripts/checks/check_workflow_action_pinning.py
python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations
python3 dev/scripts/checks/check_compat_matrix.py
python3 dev/scripts/checks/compat_matrix_smoke.py
python3 dev/scripts/checks/check_naming_consistency.py
python3 dev/scripts/checks/check_rust_test_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
python3 dev/scripts/checks/check_rust_compiler_warnings.py
python3 dev/scripts/checks/check_serde_compatibility.py
python3 dev/scripts/checks/check_rust_runtime_panic_policy.py
python3 dev/scripts/checks/check_facade_wrappers.py
python3 dev/scripts/checks/check_god_class.py
python3 dev/scripts/checks/check_mobile_relay_protocol.py
python3 dev/scripts/checks/check_daemon_state_parity.py
python3 dev/scripts/checks/check_nesting_depth.py
python3 dev/scripts/checks/check_parameter_count.py
python3 dev/scripts/checks/check_python_dict_schema.py
python3 dev/scripts/checks/check_python_typed_seams.py
python3 dev/scripts/checks/check_python_global_mutable.py
python3 dev/scripts/checks/check_python_design_complexity.py
python3 dev/scripts/checks/check_python_cyclic_imports.py
python3 dev/scripts/checks/check_python_suppression_debt.py
python3 dev/scripts/checks/check_structural_similarity.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
python3 -m pytest app/operator_console/tests/ -q --tb=short
python3 dev/scripts/devctl.py process-cleanup --verify --format md
```

### `bundle.release`

```bash
python3 dev/scripts/devctl.py check --profile release
python3 dev/scripts/devctl.py docs-check --user-facing --strict-release
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene --strict-release-warnings
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md
python3 dev/scripts/checks/check_agents_contract.py
python3 dev/scripts/checks/check_release_version_parity.py
python3 dev/scripts/checks/check_repo_url_parity.py
python3 dev/scripts/checks/check_guard_enforcement_inventory.py
python3 dev/scripts/checks/check_architecture_surface_sync.py
python3 dev/scripts/checks/check_review_snapshot_freshness.py
python3 dev/scripts/checks/check_guide_contract_sync.py
python3 dev/scripts/checks/check_instruction_surface_sync.py
python3 dev/scripts/checks/check_bundle_registry_dry.py
python3 dev/scripts/checks/check_bundle_workflow_parity.py
python3 dev/scripts/checks/check_platform_layer_boundaries.py
python3 dev/scripts/checks/check_platform_contract_closure.py
python3 dev/scripts/checks/check_contract_connectivity.py
python3 dev/scripts/checks/check_typed_enum_connectivity.py
python3 dev/scripts/checks/check_platform_contract_sync.py
python3 dev/scripts/checks/check_review_channel_bridge.py
python3 dev/scripts/checks/check_startup_authority_contract.py
python3 dev/scripts/checks/check_review_surface_consistency.py
python3 dev/scripts/checks/check_tandem_consistency.py
python3 dev/scripts/checks/check_governance_closure.py
python3 dev/scripts/checks/check_package_layout.py --fail-on-baseline-debt --baseline-debt-root dev/scripts/devctl/commands
python3 dev/scripts/checks/check_publication_sync.py --release-branch-aware
CI=1 python3 dev/scripts/checks/check_coderabbit_gate.py --branch master
CI=1 python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_system_picture_freshness.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_package_layout.py
python3 dev/scripts/checks/check_python_subprocess_policy.py
python3 dev/scripts/checks/check_mutation_bypass_graph_closure.py
python3 dev/scripts/checks/check_workflow_shell_hygiene.py
python3 dev/scripts/checks/check_workflow_action_pinning.py
python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations
python3 dev/scripts/checks/check_compat_matrix.py
python3 dev/scripts/checks/compat_matrix_smoke.py
python3 dev/scripts/checks/check_naming_consistency.py
python3 dev/scripts/checks/check_rust_test_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
python3 dev/scripts/checks/check_rust_compiler_warnings.py
python3 dev/scripts/checks/check_serde_compatibility.py
python3 dev/scripts/checks/check_rust_runtime_panic_policy.py
python3 dev/scripts/checks/check_facade_wrappers.py
python3 dev/scripts/checks/check_god_class.py
python3 dev/scripts/checks/check_mobile_relay_protocol.py
python3 dev/scripts/checks/check_daemon_state_parity.py
python3 dev/scripts/checks/check_nesting_depth.py
python3 dev/scripts/checks/check_parameter_count.py
python3 dev/scripts/checks/check_python_dict_schema.py
python3 dev/scripts/checks/check_python_typed_seams.py
python3 dev/scripts/checks/check_python_global_mutable.py
python3 dev/scripts/checks/check_python_design_complexity.py
python3 dev/scripts/checks/check_python_cyclic_imports.py
python3 dev/scripts/checks/check_python_suppression_debt.py
python3 dev/scripts/checks/check_structural_similarity.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
python3 dev/scripts/devctl.py process-cleanup --verify --format md
```

### `bundle.post-push`

```bash
git status
git log --oneline --decorate -n 10
python3 dev/scripts/devctl.py status --ci --require-ci --format md
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md
python3 dev/scripts/devctl.py docs-check --user-facing --since-ref origin/develop
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_review_channel_bridge.py
python3 dev/scripts/checks/check_system_picture_freshness.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop
python3 dev/scripts/checks/check_package_layout.py --since-ref origin/develop
python3 dev/scripts/checks/check_python_subprocess_policy.py --since-ref origin/develop
python3 dev/scripts/checks/check_mutation_bypass_graph_closure.py
python3 dev/scripts/checks/check_workflow_shell_hygiene.py
python3 dev/scripts/checks/check_workflow_action_pinning.py
python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations
python3 dev/scripts/checks/check_compat_matrix.py
python3 dev/scripts/checks/compat_matrix_smoke.py
python3 dev/scripts/checks/check_naming_consistency.py
python3 dev/scripts/checks/check_rust_test_shape.py --since-ref origin/develop
python3 dev/scripts/checks/check_rust_lint_debt.py --since-ref origin/develop
python3 dev/scripts/checks/check_rust_best_practices.py --since-ref origin/develop
python3 dev/scripts/checks/check_rust_compiler_warnings.py --since-ref origin/develop
python3 dev/scripts/checks/check_serde_compatibility.py --since-ref origin/develop
python3 dev/scripts/checks/check_rust_runtime_panic_policy.py --since-ref origin/develop
python3 dev/scripts/checks/check_facade_wrappers.py --since-ref origin/develop
python3 dev/scripts/checks/check_god_class.py --since-ref origin/develop
python3 dev/scripts/checks/check_mobile_relay_protocol.py --since-ref origin/develop
python3 dev/scripts/checks/check_daemon_state_parity.py
python3 dev/scripts/checks/check_nesting_depth.py --since-ref origin/develop
python3 dev/scripts/checks/check_parameter_count.py --since-ref origin/develop
python3 dev/scripts/checks/check_python_dict_schema.py --since-ref origin/develop
python3 dev/scripts/checks/check_python_typed_seams.py --since-ref origin/develop
python3 dev/scripts/checks/check_python_global_mutable.py --since-ref origin/develop
python3 dev/scripts/checks/check_python_design_complexity.py --since-ref origin/develop
python3 dev/scripts/checks/check_python_cyclic_imports.py --since-ref origin/develop
python3 dev/scripts/checks/check_python_suppression_debt.py --since-ref origin/develop
python3 dev/scripts/checks/check_structural_similarity.py --since-ref origin/develop
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
python3 dev/scripts/devctl.py process-cleanup --verify --format md
```

## Runtime risk matrix (required add-ons)

- Overlay/input/status/HUD changes:
  - `python3 dev/scripts/devctl.py check --profile ci`
  - `cd rust && cargo test --bin voiceterm`
  - preferred AI/raw-test path: `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm`
  - required post-run follow-up (if `cargo test` was run directly and orphan sweep is needed): `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel --with-process-sweep-cleanup` (includes opt-in process sweep plus host-side `process-cleanup --verify`)
- Performance/latency-sensitive changes:
  - `python3 dev/scripts/devctl.py check --profile prepush`
  - `./dev/scripts/tests/measure_latency.sh --voice-only --synthetic`
  - `./dev/scripts/tests/measure_latency.sh --ci-guard`
  - `dev/scripts/tests/measure_latency.sh` auto-detects `rust/` workspace paths and falls back to legacy `src/` layouts
  - `dev/scripts/tests/measure_latency.sh` now uses `set -u`-safe empty-array
    expansion so voice-only/CI synthetic modes do not raise `unbound variable`
    errors when optional arg arrays are empty
  - when host process access is available: `python3 dev/scripts/devctl.py process-cleanup --verify --format md`
- Wake-word runtime/detection changes:
  - `bash dev/scripts/tests/wake_word_guard.sh`
  - `python3 dev/scripts/devctl.py check --profile release`
  - when host process access is available: `python3 dev/scripts/devctl.py process-cleanup --verify --format md`
- Threading/lifecycle/memory changes:
  - `cd rust && cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture`
  - preferred AI/raw-test path: `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture`
  - required post-run follow-up (if `cargo test` was run directly and orphan sweep is needed): `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel --with-process-sweep-cleanup` (includes opt-in process sweep plus host-side `process-cleanup --verify`)
- Unsafe/FFI lifecycle changes:
  - Update `dev/security/unsafe_governance.md`
  - `cd rust && cargo test pty_session::tests::pty_cli_session_drop_terminates_descendants_in_process_group -- --nocapture`
  - `cd rust && cargo test pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group -- --nocapture`
  - `cd rust && cargo test stt::tests::transcriber_restores_stderr_after_failed_model_load -- --nocapture`
  - preferred AI/raw-test path: `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group -- --nocapture`
  - required post-run follow-up (if `cargo test` was run directly and orphan sweep is needed): `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel --with-process-sweep-cleanup` (includes opt-in process sweep plus host-side `process-cleanup --verify`)
- Parser/ANSI boundary hardening changes:
  - `cd rust && cargo test pty_session::tests::prop_find_csi_sequence_respects_bounds -- --nocapture`
  - `cd rust && cargo test pty_session::tests::prop_find_osc_terminator_respects_bounds -- --nocapture`
  - `cd rust && cargo test pty_session::tests::prop_split_incomplete_escape_preserves_original_bytes -- --nocapture`
  - preferred AI/raw-test path: `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test pty_session::tests::prop_find_csi_sequence_respects_bounds -- --nocapture`
  - required post-run follow-up (if `cargo test` was run directly and orphan sweep is needed): `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel --with-process-sweep-cleanup` (includes opt-in process sweep plus host-side `process-cleanup --verify`)
- Mutation-hardening work:
  - `python3 dev/scripts/devctl.py mutation-score --threshold 0.80 --max-age-hours 72`
  - optional: `python3 dev/scripts/devctl.py mutants --module overlay`
- Macro/wizard onboarding changes:
  - `./scripts/macros.sh list`
  - `./scripts/macros.sh install --pack safe-core --project-dir . --overwrite`
  - `./scripts/macros.sh validate --output ./.voiceterm/macros.yaml --project-dir .`
  - Validate `gh auth status -h github.com` behavior when GH macros are included
- Dependency/security-hardening changes:
  - `python3 dev/scripts/devctl.py security`
  - optional strict workflow scan: `python3 dev/scripts/devctl.py security --with-zizmor --require-optional-tools`
  - fallback manual path:
    `cargo install cargo-audit --locked`,
    `cd rust && (cargo audit --json > ../rustsec-audit.json || true)`,
    `python3 dev/scripts/checks/check_rustsec_policy.py --input rustsec-audit.json --min-cvss 7.0 --fail-on-kind yanked --fail-on-kind unsound --allowlist-file dev/security/rustsec_allowlist.md`

## Release SOP (master only)

Use this exact sequence:

1. Confirm `git checkout master` and clean working tree.
2. Verify version parity:
   - `python3 dev/scripts/checks/check_release_version_parity.py`
   - `rust/Cargo.toml` has `version = X.Y.Z`
   - `pypi/pyproject.toml` has `[project].version = X.Y.Z`
   - `app/macos/VoiceTerm.app/Contents/Info.plist` has
     `CFBundleShortVersionString = X.Y.Z` and `CFBundleVersion = X.Y.Z`
   - `dev/CHANGELOG.md` has release heading for `X.Y.Z`
   - `dev/active/MASTER_PLAN.md` Status Snapshot has
     `Last tagged release: vX.Y.Z` and `Current release target: post-vX.Y.Z planning`
3. Verify release prerequisites:
   - `gh auth status -h github.com`
   - `CI=1 python3 dev/scripts/devctl.py release-gates --branch master --sha "$(git rev-parse HEAD)" --skip-preflight --wait-seconds 1800 --poll-seconds 20 --format md`
   - GitHub Actions secret `PYPI_API_TOKEN` exists for `.github/workflows/publish_pypi.yml`
   - GitHub Actions secret `HOMEBREW_TAP_TOKEN` exists for `.github/workflows/publish_homebrew.yml`
   - Optional local fallback: Homebrew tap path is resolvable (`HOMEBREW_VOICETERM_PATH` or `brew --repo`)
4. Run `bundle.release`.
5. Run and wait for same-SHA `release_preflight.yml` success:

   ```bash
   gh workflow run release_preflight.yml -f version=<version>
   gh run list --workflow release_preflight.yml --limit 1
   # gh run watch <run-id>
   ```

   - `release_preflight.yml` must provide `GH_TOKEN` to steps that invoke
     `gh` inside `devctl check --profile release`; workflow uses
     `${{ github.token }}` for this wiring.
   - `release_preflight.yml` job must grant `security-events: write` so the
     zizmor SARIF upload step can publish scan results without permission
     failures.
   - `release_preflight.yml` uses `online-audits: false` for zizmor so
     cross-repo compare API restrictions do not hard-fail preflight in CI.
   - `release_preflight.yml` release security step must use
     `--python-scope changed` with the same resolved `--since-ref/--head-ref`
     range as AI-guard checks; do not run full-repo Python format/import scans
     in this lane.
   - `release_preflight.yml` release security step should not hard-block on
     repository-wide open CodeQL backlog (`--with-codeql-alerts`); keep CodeQL
     alert enforcement in dedicated security lanes and triage workflows.
   - In `release_preflight.yml`, `cargo deny` remains the blocking security
     gate; `devctl security` report output is retained as advisory evidence.

6. Run release tagging and notes:

   ```bash
   # Optional one-step metadata prep (Cargo/PyPI/app plist/changelog):
   python3 dev/scripts/devctl.py ship --version <version> --prepare-release
   python3 dev/scripts/devctl.py release --version <version>
   gh release create v<version> --title "v<version>" --notes-file /tmp/voiceterm-release-v<version>.md
   # PyPI publish runs automatically via .github/workflows/publish_pypi.yml.
   gh run list --workflow publish_pypi.yml --limit 1
   # Homebrew publish runs automatically via .github/workflows/publish_homebrew.yml.
   gh run list --workflow publish_homebrew.yml --limit 1
   # Native release binaries publish via .github/workflows/publish_release_binaries.yml.
   gh run list --workflow publish_release_binaries.yml --limit 1
   # Release source provenance attestations run via .github/workflows/release_attestation.yml.
   gh run list --workflow release_attestation.yml --limit 1
   # gh run watch <run-id>
   curl -fsSL https://pypi.org/pypi/voiceterm/<version>/json
   # Local fallback (if workflow is unavailable):
   python3 dev/scripts/devctl.py homebrew --version <version>
   ```

7. Run `bundle.post-push`.

Unified control plane alternatives:

```bash
# Workflow-first release convenience (only after same-SHA preflight success)
gh workflow run release_preflight.yml -f version=<version>
gh run list --workflow release_preflight.yml --limit 1
# gh run watch <run-id>
python3 dev/scripts/devctl.py ship --version <version> --verify --tag --notes --github --yes
# Workflow-first release path with auto metadata prep
python3 dev/scripts/devctl.py ship --version <version> --prepare-release --verify --tag --notes --github --yes
gh run list --workflow publish_pypi.yml --limit 1
gh run list --workflow publish_homebrew.yml --limit 1
gh run list --workflow publish_release_binaries.yml --limit 1
gh run list --workflow release_attestation.yml --limit 1

# Manual fallback (run PyPI/Homebrew locally)
python3 dev/scripts/devctl.py ship --version <version> --pypi --verify-pypi --homebrew --yes
```

## CI workflow dependency graph

Release pipeline flow (trigger order):

```
push to master
  └─> release_preflight.yml ─── (must pass before tagging)
        └─> gh release create vX.Y.Z
              ├─> publish_pypi.yml        (on: release published)
              ├─> publish_homebrew.yml     (on: release published)
              ├─> publish_release_binaries.yml (on: release published)
              └─> release_attestation.yml (on: release published)
```

Development pipeline flow (parallel on push/PR):

```
push to develop / PR
  ├─> rust_ci.yml            (compile + test + clippy + AI guards)
  ├─> voice_mode_guard.yml   (send/transcript delivery)
  ├─> wake_word_guard.yml    (detection accuracy)
  ├─> perf_smoke.yml         (latency bounds)
  ├─> memory_guard.yml       (thread lifecycle)
  ├─> security_guard.yml     (cargo-deny + advisories)
  ├─> workflow_lint.yml      (actionlint syntax)
  ├─> coverage.yml           (Codecov upload)
  ├─> docs_lint.yml          (markdownlint)
  ├─> tooling_control_plane.yml (shape + governance)
  └─> dependency_review.yml  (PR-only, manifest diff)
```

Scheduled / on-demand:

```
schedule / workflow_dispatch
  ├─> mutation-testing.yml       (cargo-mutants)
  ├─> scorecard.yml              (OpenSSF)
  ├─> coderabbit_triage.yml      (finding rollups)
  ├─> coderabbit_ralph_loop.yml  (bounded remediation)
  ├─> autonomy_controller.yml    (bounded loop)
  ├─> autonomy_run.yml           (plan-scoped swarm)
  ├─> mutation_ralph_loop.yml    (mutation remediation)
  ├─> failure_triage.yml         (non-success run triage)
  └─> orchestrator_watchdog.yml  (stale lane alerts)
```

## CI lane mapping (what must be green)

| Change signal | Lanes to verify |
|---|---|
| `rust/src/**` runtime changes | `rust_ci.yml` (Ubuntu main lane + MSRV `1.88.0` check + feature-mode matrix + macOS runtime smoke lane + high-signal Clippy lint-baseline gate) |
| Send mode/macros/transcript delivery | `voice_mode_guard.yml` |
| Wake-word runtime/detection | `wake_word_guard.yml` |
| Perf-sensitive paths | `perf_smoke.yml`, `latency_guard.yml` |
| Long-running worker/thread lifecycle | `memory_guard.yml` |
| Parser/ANSI/OSC boundary logic | `parser_fuzz_guard.yml` |
| Dependency/security policy changes | `security_guard.yml` |
| Dependency manifest/lockfile deltas in PRs | `dependency_review.yml` |
| Workflow syntax + policy drift | `workflow_lint.yml` |
| AI PR review signal ingestion and owner/severity rollups | `coderabbit_triage.yml` |
| Bounded AI remediation loop for CodeRabbit medium/high backlog | `coderabbit_ralph_loop.yml` |
| Bounded autonomous controller loop (checkpoint packets + queue artifacts + optional promote PR) | `autonomy_controller.yml` |
| Guarded plan-scoped autonomy swarm pipeline (scope load + swarm + reviewer + governance + plan evidence append) | `autonomy_run.yml` |
| Bounded mutation remediation loop (report-only default, optional policy-gated fix mode) | `mutation_ralph_loop.yml` |
| Release commit guard for unresolved CodeRabbit medium/high findings | `coderabbit_triage.yml`, `coderabbit_ralph_loop.yml`, `release_preflight.yml`, `publish_pypi.yml`, `publish_homebrew.yml`, `publish_release_binaries.yml`, `release_attestation.yml` |
| Supply-chain posture drift | `scorecard.yml` |
| Coverage reporting / Codecov badge freshness | `coverage.yml` (runs on every push to `develop`/`master` so branch-head badges do not go `unknown` after non-runtime commits) |
| Rust/Python source-file shape drift (God-file growth) | `tooling_control_plane.yml` |
| Multi-agent instruction/ack timers and stale-lane accountability | `tooling_control_plane.yml`, `orchestrator_watchdog.yml` |
| User docs/markdown changes | `docs_lint.yml` |
| Release preflight verification bundle | `release_preflight.yml` |
| GitHub release publication / PyPI distribution | `publish_pypi.yml` |
| GitHub release publication / Homebrew distribution | `publish_homebrew.yml` |
| GitHub release publication / native binaries | `publish_release_binaries.yml` |
| Release source provenance attestation | `release_attestation.yml` |
| Any non-success CI workflow run in watched lanes | `failure_triage.yml` (workflow-run triage bundle + artifact upload for high-signal failures in watched lanes; trusted same-repo events only, branch allowlist defaults to `develop,master` and can be overridden with repo variable `FAILURE_TRIAGE_BRANCHES`) |
| Tooling/process/docs governance surfaces (`dev/scripts/**`, `scripts/macro-packs/**`, `.github/workflows/**`, `AGENTS.md`, `dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md`, `Makefile`) | `tooling_control_plane.yml` |
| Mutation-hardening work | `mutation-testing.yml` (scheduled; threshold is advisory/report-only across branches) plus local mutation-score evidence |

Runner-label note:
- Keep `publish_release_binaries.yml` on actionlint-supported macOS labels (`macos-15-intel` for darwin/amd64, `macos-14` for darwin/arm64).

Workflow hardening note:
- Keep `.github/workflows/scorecard.yml` workflow-level permissions read-only; set `id-token: write` and `security-events: write` at the job level so OpenSSF result publishing passes workflow verification.
- Keep GitHub-owned actions pinned to valid 40-character commit SHAs (for example `actions/attest-build-provenance` and `github/codeql-action/upload-sarif`).

## Documentation governance

Always evaluate:

- `dev/CHANGELOG.md` (required for user-facing behavior changes)
- `dev/active/INDEX.md`
- `dev/active/MASTER_PLAN.md`
- `README.md`
- `QUICK_START.md`
- `guides/USAGE.md`
- `guides/CLI_FLAGS.md`
- `guides/INSTALL.md`
- `guides/TROUBLESHOOTING.md`
- `dev/guides/ARCHITECTURE.md`
- `dev/guides/DEVELOPMENT.md`
- `dev/scripts/README.md`
- `.github/workflows/README.md`
- `dev/audits/README.md`
- `dev/audits/AUTOMATION_DEBT_REGISTER.md`
- `dev/audits/METRICS_SCHEMA.md`
- `dev/integrations/EXTERNAL_REPOS.md`
- `dev/history/ENGINEERING_EVOLUTION.md` (required for tooling/process/CI shifts)

Plain-language rule for docs updates:

- For user/developer docs (`README.md`, `QUICK_START.md`, `guides/*`, `dev/*`), prefer plain language over policy-heavy wording.
- For workflow docs (`.github/workflows/README.md` + workflow header comments), explain purpose and trigger behavior in plain language.
- Use short, direct sentences and concrete commands.
- Keep technical accuracy, but avoid unnecessary jargon.

Update flow:

1. Link/adjust MP item in `dev/active/MASTER_PLAN.md`.
2. Update `dev/CHANGELOG.md` for user-facing behavior.
3. Update user docs for behavior/flag/UI changes.
4. Update developer docs for architecture/workflow/tooling changes.
5. Update screenshots/tables when UI output changes.
6. Add/update ADR when architecture decisions change.

Enforcement commands:

```bash
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py docs-check --user-facing --strict-release
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/checks/check_agents_contract.py
python3 dev/scripts/checks/check_agents_bundle_render.py
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_workflow_shell_hygiene.py
python3 dev/scripts/checks/check_workflow_action_pinning.py
python3 dev/scripts/checks/check_bundle_workflow_parity.py
python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations
python3 dev/scripts/checks/check_compat_matrix.py
python3 dev/scripts/checks/compat_matrix_smoke.py
python3 dev/scripts/checks/check_naming_consistency.py
python3 dev/scripts/checks/check_rust_test_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
python3 dev/scripts/checks/check_rust_compiler_warnings.py
python3 dev/scripts/checks/check_rust_runtime_panic_policy.py
```

## Tooling inventory

Canonical tool: `python3 dev/scripts/devctl.py ...`

Core commands:

- `check` (`ci`, `prepush`, `release`, `maintainer-lint`, `pedantic`, `quick`, `fast`, `ai-guard`)
  - Runs setup gates (`fmt`, `clippy`, AI guard scripts) and test/build phases in parallel batches by default.
  - Use `--parallel-workers <n>` to tune worker count, or `--no-parallel` to force sequential execution.
  - Adds orphaned/stale repo-related process cleanup before/after checks only when `--with-process-sweep-cleanup` is passed (matched VoiceTerm PTY/test trees, repo-runtime cargo/target trees, repo-tooling wrappers, and descendant PTY/helper children such as leaked `cat` harnesses or stale repo-cwd helpers; detached `PPID=1` and stale active runners aged `>=600s` are cleanup targets).
  - `--no-process-sweep-cleanup` remains as an explicit compatibility spelling for preserving the default no-sweep behavior.
  - `quick` / `fast` keep AI-guard scripts enabled by default (while still skipping test/build lanes) and also run host-side `process-cleanup --verify --format md`; use `--no-host-process-cleanup` only when a live process tree must be preserved and the exception is recorded.
  - `pedantic` is an advisory maintainer lane for intentional lint-hardening sweeps; it is opt-in and not part of required bundles or release gates.
  - `check --profile pedantic` writes structured artifacts to `dev/reports/check/clippy-pedantic-summary.json` and `dev/reports/check/clippy-pedantic-lints.json`; consume them through `report --pedantic` or `triage --pedantic` instead of making ad hoc decisions from raw terminal output.
  - Structured `check` output timestamps are UTC for stable cross-run correlation.
- `check-router` (path-aware lane selector that maps changed files to `bundle.docs|bundle.runtime|bundle.tooling|bundle.release`, reports required risk add-ons, and can execute the routed command set with `--execute`)
- `compat-matrix` (single-view host/provider compatibility matrix summary and policy validation surface)
  - Matrix checks now include a minimal no-dependency YAML fallback parser so
    tooling lanes remain deterministic when `PyYAML` is unavailable.
  - Malformed inline collection scalars in fallback mode now fail closed (no
    silent coercion), preserving guard reliability.
- `mcp` (optional read-only MCP adapter for allowlisted `devctl` tools/resources plus stdio transport; additive transport only, not a second enforcement authority)
- `docs-check`
  - `--strict-tooling` also runs active-plan + multi-agent sync gates, markdown metadata-header checks, workflow-shell hygiene checks, bundle/workflow parity checks, plus stale-path audit so tooling/process changes cannot bypass active-doc/lane governance.
  - Check-script moves must be reflected in `dev/scripts/devctl/script_catalog.py` so strict-tooling path audits stay canonical. Stable public seams such as `script_catalog.py` and `path_audit.py` may stay as thin compatibility shims when the implementation moves under support packages, but the root import/command paths remain the authority surfaces.
- `hygiene` (archive/ADR/scripts governance plus orphaned/stale repo-related host-process sweep, including VoiceTerm PTY/test trees, repo-runtime cargo/target trees, repo-tooling wrappers, and repo-cwd background helpers such as `python3 -m unittest`, direct `bash dev/scripts/...` wrappers, or `qemu/node/make` descendants that outlive their repo-owned parent; report-retention drift warnings for stale managed `dev/reports/**` run artifacts, and tracked external-publication drift warnings when watched repo paths outpace synced papers/sites; optional `--fix` removes detected `dev/scripts/**/__pycache__` directories)
- `process-cleanup` (host-side cleanup for orphaned/stale repo-related process trees; expands cleanup roots to full descendant trees so leaked PTY children, repo-cwd background helpers, and orphaned tooling descendants are reaped with their parent wrappers when possible, skips recent active processes by default, preserves registry-backed running review-channel conductor PIDs even when prepared authority has gone stale, and `--verify` reruns strict host audit after cleanup)
- `process-audit` (host-side Activity Monitor equivalent for repo-related runtime/tooling process trees; reports matched roots plus descendants, includes repo-cwd runtime/tooling helpers that would otherwise look generic in Activity Monitor, fails fast if `ps` is unavailable, preserves registered review-channel conductors as supervised even when headless wrappers reparent to PID 1, and `--strict` turns leftover runtime/test trees or stale/orphaned repo-related helpers into a blocking failure before handoff)
- `process-watch` (bounded periodic host-process monitor that reruns the same audit logic on a cadence, optionally performs orphan/stale cleanup before each pass, and stops only when zero repo-related host processes remain if `--stop-on-clean` is set)
- `publication-sync` (tracked external publication report/record surface that compares watched repo paths against the last synced source commit for papers/sites and can record a new baseline after external publish)
- `push` (policy-driven guarded push surface for the current branch; validates repo-owned branch/remote rules plus configured preflight, defaults to non-mutating validation, and uses the configured post-push bundle after `--execute`)
- `path-audit` (stale-reference scan for legacy check-script paths; excludes `dev/archive/`)
- `path-rewrite` (auto-rewrite legacy check-script paths to canonical registry targets; use `--dry-run` first)
- `sync` (branch-sync automation with clean-tree, remote-ref, and `--ff-only` pull guards; optional `--push` for ahead branches)
- `integrations-sync` (policy-guarded sync/status for pinned federated sources under `integrations/`; supports remote update and audit logging)
- `integrations-import` (allowlisted selective importer from pinned federated sources into controlled destination roots with JSONL audit records)
- `cihub-setup` (allowlisted CIHub setup runner with preview/apply modes, capability probing, and strict unsupported-step gating)
- `security` (RustSec policy gate with optional workflow scan support via `--with-zizmor`, optional GitHub code-scanning alert gate via `--with-codeql-alerts`, and Python scope control via `--python-scope auto|changed|all`)
- `mutation-score` (reports outcomes source freshness; strict by default, or non-blocking reminders with `--report-only`; optional stale-data gate via `--max-age-hours`)
- `mutants`
- `release`
- `release-gates` (shared same-SHA release policy gate for CodeRabbit triage + release-preflight + Ralph checks; use `--skip-preflight` when running inside `release_preflight.yml`)
- `release-notes`
- `ship` (release-version reads now use TOML parsing for `[package]`/`[project]` with Python 3.10 fallback parsing)
- `pypi`
- `homebrew` (tap formula URL/version/checksum updates, canonical `desc` sync, and Cargo manifest-path migration sync to `libexec/rust/Cargo.toml` when legacy formulas still reference `libexec/src/Cargo.toml`)
- `status` (supports optional guarded Dev Mode log summaries via `--dev-logs`)
- `orchestrate-status` (single-view orchestrator summary for active-plan sync + multi-agent coordination guard state)
- `orchestrate-watch` (SLA watchdog for stale agent updates and overdue instruction ACKs)
- `report` (supports optional guarded Dev Mode log summaries via `--dev-logs`)
- `dashboard` (governance dashboard snapshot from existing artifacts; views: `overview`, `dev`, `analytics`, `quality`, `audit`, `publication`, `health`; renders sparkline charts and repo-state summaries in `terminal`, `md`, or `json` format; accepts `--role dashboard|observer` for read-only advisory next-command projection; reads `dev/reports/` artifacts only, no side-effect writes)
- `monitor` (canonical single-pass remote-phone monitor over typed startup/control-plane state; emits mobile-safe `state / main_problem / can_work_continue / can_code_be_pushed / who_needs_to_act / what_should_happen_next / confidence` output, classifies authority/telemetry/projection/diagnostic sources, supports local NDJSON follow mode via `--follow --interval <Ns|Nm|Nh>`, and the detached review-channel publisher now writes the same `monitor_snapshot.{json,md}` bundle into the governed review-status root on its normal cadence)
- `data-science` (builds one rolling telemetry snapshot from devctl audit events plus autonomy swarm/benchmark history, folds in governance-review false-positive/cleanup metrics, emits `summary.{md,json}` + SVG charts under `dev/reports/data_science/latest/`, and supports source/output overrides for experiments; devctl also auto-refreshes this snapshot after each command unless `DEVCTL_DATA_SCIENCE_DISABLE=1`)
- `dogfood` (explicit dev-mode coverage ledger over live commands, guards, probes, and role lanes; `--record` appends one repo-owned row to `dev/reports/dogfood/runs.jsonl`, plain `--report` refreshes `dev/reports/dogfood/latest/summary.{md,json}`, coverage derives from the live command/script catalog instead of fixed counts, `--record-governance` closes the same run through `PlatformFindingIngest` into the canonical `signal_type=dogfood` governance-review / `FindingBacklog` spine with stable ids plus live target-path defaults, and campaign/system-test runs may also carry `--campaign-id`, `--scenario-id`, `--repo-scope`, `--repo-label`, `--repo-path`, `--topology`, `--lane-role`, `--live-run-ref`, and `--governance-finding-id`; failed non-read-only devctl commands now run the fail-open Slice A report-only finalization hook by default after audit emission, while `DEVCTL_PLATFORM_FINDING_INGEST_AUTO_RECORD=0` is the compatibility opt-out and `DEVCTL_PLATFORM_FINDING_INGEST_DISABLE=1` is the kill switch)
- `tandem-validate` (repo-owned tandem-session validator that resolves the real lane and risk add-ons through `check-router`, executes the routed bundle, then rechecks review-channel and tandem consistency at the end)
- `doc-authority` (read-only governed-markdown authority scan that derives the current doc registry, plan metadata, and owner/classification signals from the reviewed markdown set)
- `governance-draft` (deterministic governed-doc discovery and starter surface that should stay aligned with the live CLI inventory and maintainer docs before write-mode governance changes)
- `governance-import-findings` (imports external review findings into the repo-owned governance ledger with normalized metadata and auditable append-only records; `--input-format md` reuses the `LIVE_RUN.md` parser and emits repo-scoped `<repo_name>:Q-ID` sync ids so compatibility markdown stays a mirror, not a second canonical backlog)
- `governance-quality-feedback` (rolls adjudicated findings and probe guidance into a reusable quality-feedback summary for policy tuning and platform evidence)
- `governance-review` (records adjudicated guard/probe findings to
  `dev/reports/governance/finding_reviews.jsonl`, writes
  `dev/reports/governance/latest/review_summary.{md,json}`, and gives the repo
  a durable false-positive / cleanup-rate ledger; `--record` now also accepts
  `signal_type=observer` plus optional `finding_type`, and still accepts
  optional `guidance_id` / `guidance_followed` fields so probe-guidance
  adoption can be measured in the same ledger as verdict/fix outcomes; rows
  with `prevention_surface=guard|probe` also queue `GuardPromotionCandidate`
  follow-up records and include the candidate id/path in the refreshed JSON
  summary for that recorded row)
- `findings-priority` (ranks canonical backlog findings from `FindingBacklog` / `governance-review` state by shared triage severity ordering plus context-graph import fan-out; `LIVE_RUN.md` is compatibility evidence only, not the ranking authority. Use `--format md --top-n <n>` for a bounded priority list)
- `graph-walk` (read-only cited traversal over the generated context graph; it
  helps humans and AI navigate typed plan, packet, finding, receipt, test,
  workflow, and contract evidence, but it never replaces deterministic guards,
  packet lifecycle checks, or typed runtime authority)
- `triage` (human/AI triage output with optional CIHub artifact ingestion/bundle emission for owner/risk routing; report timestamps are UTC)
- `triage-loop` (bounded CodeRabbit medium/high loop with mode controls: `report-only`, `plan-then-fix`, `fix-only`; fix execution is policy-gated via `AUTONOMY_MODE`, branch allowlist, and command-prefix allowlist; emits md/json bundles plus a bounded structured backlog slice for downstream autonomy consumers, optional MASTER_PLAN proposal artifacts, and review-escalation comment upserts when attempts exhaust unresolved backlog)
- `loop-packet` (builds a guarded terminal feedback packet from triage/loop JSON sources for dev-mode draft injection with freshness/risk/auto-send-eligibility gates; `triage-loop` sources now also carry a bounded structured backlog slice so autonomy drafts can inject canonical `review_targets.json` probe guidance, mark when guidance adoption is required, and keep that contract in packet JSON instead of hidden prompt-only text; the active implementation now lives under `dev/scripts/devctl/commands/packets/loop_packet.py`, while the flat `dev/scripts/devctl/commands/loop_packet.py` path remains the compatibility shim that package-layout and import/patch smoke tests must still prove)
- `autonomy-loop` (bounded controller loop that orchestrates triage-loop + loop-packet rounds, emits checkpoint packets/queue artifacts, writes phone-ready status snapshots under `dev/reports/autonomy/queue/phone/`, and enforces policy-driven stop reasons; non-dry-run write modes require `AUTONOMY_MODE=operate`)
- `autonomy-benchmark` (active-plan-scoped swarm matrix runner for tactic/swarm-size tradeoff analysis; executes `autonomy-swarm` batches across configurable count/tactic grids, emits per-swarm and per-scenario productivity metrics, and writes benchmark bundles under `dev/reports/autonomy/benchmarks/<label>/`; non-report modes require `--fix-command`)
- `swarm_run` (guarded plan-scoped autonomy pipeline that derives next unchecked plan steps, runs `autonomy-swarm` with reviewer + post-audit defaults, executes governance checks (`check_active_plan_sync`, `check_multi_agent_sync`, `docs-check --strict-tooling`, `orchestrate-status/watch`), and appends run evidence to plan-doc `Progress Log` + `Audit Evidence`; supports optional multi-cycle execution (`--continuous --continuous-max-cycles`) to keep processing plan checklist scope until failure/limit; non-report modes require `--fix-command`)
- `autonomy-report` (builds a human-readable autonomy digest bundle from loop/watch artifacts under `dev/reports/autonomy/library/<label>` with summary markdown/json, copied sources, and optional matplotlib charts)
- `phone-status` (renders iPhone/SSH-safe autonomy status projections from `dev/reports/autonomy/queue/phone/latest.json` with selectable views `full|compact|trace|actions` and optional projection bundle emission: `full.json`, `compact.json`, `trace.ndjson`, `actions.json`, `latest.md`)
- `mobile-app` (wrapper over the first-party iPhone/iPad app flow; supports simulator demo, repo-backed live-review refresh before launch, physical-device install guidance, and real signed device install/launch when Apple signing is configured)
- `controller-action` (policy-gated operator action surface for `refresh-status`, `dispatch-report-only`, `pause-loop`, and `resume-loop`; dispatch and mode writes are bounded by workflow/branch allowlists and autonomy mode gates, with optional dry-run and mode-state artifact output)
- `ralph-status` (Ralph guardrail analytics surface; aggregates `ralph-report*.json` artifacts into fix/open counts, architecture breakdowns, guidance adoption/waiver metrics, and optional chart outputs for CLI/mobile/operator surfaces)
- `review-channel` (current bridge-gated review-swarm bootstrap surface; it resolves the review plan, compatibility bridge, and status root through `ProjectGovernance` / repo-pack state, with VoiceTerm currently mapping those to `dev/active/review_channel.md`, `bridge.md`, and `dev/reports/review_channel/latest/`; `--action launch` emits Codex/Claude conductor launch scripts, defaults live macOS launches to an `auto-dark` Terminal profile when available, auto-starts the repo-owned ensure-follow publisher from the actual live launch/rollover router, fails closed if that detached publisher does not come up, and still fails closed when the markdown bridge is inactive; local-terminal relaunch/recover guidance now defaults back to visible `--terminal terminal-app`, while governed `remote_control` recovery stays headless with `--terminal none`; fresh launch/recovery decisions should read `startup-context.action`, `interaction_mode`, `reviewer_runtime.conductor_visibility`, and `reviewer_runtime.session_owner.session_visibility` before choosing visible vs headless posture; the publisher remains the persistent service and reclaims the detached reviewer-supervisor runtime on its normal cadence, while the repo now also ships a checked-in launchd template/wrapper pair under `dev/config/launchd/` for login-time restart/backoff semantics outside the live launch path; `--action status`, `--action ensure`, `--action reviewer-heartbeat`, and `--action reviewer-checkpoint` now also emit machine-readable `reviewer_worker` state plus the typed `current_session` live-status block so current instruction / ACK reads no longer depend on append-only bridge prose, preserve shared-context `guidance_refs` when probe guidance is in scope, and keep those refs visible to downstream packet/prompt consumers, while `ensure --follow` frames carry `review_needed` without claiming semantic review completion and also reclaim a missing detached reviewer supervisor in active dual-agent mode; bridge-backed `status` also emits a typed `_compat.bridge_projection` payload so repo-owned bridge repair can rebuild the compatibility projection from typed state instead of reparsing `bridge.md`, bridge/status poll surfaces now also emit `implementer_state_hash` so reviewer-side stale-reader checks can fail closed on Claude-owned state drift, and typed runtime/doctor output now carries explicit conductor visibility (`reviewer_runtime.conductor_visibility`) plus reviewer session visibility (`reviewer_runtime.session_owner.session_visibility`) so headless vs visible vs mixed loops are no longer inferred from raw `terminal_window_id`; detached repo-owned `ensure --follow` / `reviewer-heartbeat --follow` launches pin `--follow-inactivity-timeout-seconds 0`, `--action stop --daemon-kind <publisher|reviewer_supervisor|all>` is the repo-owned daemon reclaim path, and repo-owned reviewer writes now treat `Poll Status` as current-state-only reviewer authority and replace stale reviewer prose instead of stacking fresh heartbeat/checkpoint notes on older revision bullets; `--action doctor` is the compact readiness surface for phone/remote-control clients and now carries publisher/supervisor running state plus the last heartbeat/stop-reason projection alongside `reviewer_runtime` and `commit_pipeline`; active reviewer checkpoints should prefer one typed `--checkpoint-payload-file` or the existing per-section `--*-file` flags for AI-generated markdown / shell-sensitive content instead of inline shell bodies, and `active_dual_agent` writes must carry the live `--expected-instruction-revision` plus `--expected-implementer-state-hash`; the repo-owned wait paths are `--action implementer-wait` for Claude-side bounded waiting and `--action reviewer-wait` for the symmetric Codex-side bounded wait over `reviewer_worker` hash truth plus projected `current_session` ACK/status state from `review_state.json`, not ad hoc shell sleep loops or invented top-level status payload blocks, and Claude-side wait is only valid under an explicit reviewer-owned wait state because low-information updates such as `No change. Continuing.` or `Codex should review` are now contract violations while work is still assigned; `--action recover --recover-provider claude` is the narrower stale-implementer replacement path, but it now fails closed unless a live repo-owned Codex conductor session is already present, and `reviewer-heartbeat --follow` now auto-escalates repeated unchanged stale-implementer state through that repo-owned recovery command instead of sitting forever on polling prose; the same reviewer-follow loop now also auto-escalates repeated unchanged stale reviewer/runtime states through the repo-owned `--action rollover` path so remote-control recovery reuses the structured handoff bundle plus visible ACK contract instead of ad hoc Codex restarts; `--action status` also treats a Claude-only repo-owned session as a hybrid-loop error and `active_dual_agent` with no repo-owned conductors as a bridge-contract error instead of healthy live state; `--action rollover` writes a repo-visible handoff bundle, relaunches fresh conductors before compaction, and can wait for visible ACK lines in `bridge.md`; the ensure orchestration delegates heartbeat refresh, detail assembly, and report construction to `_ensure_helpers.py` so each function stays focused on one concern)
- `review-channel` (current bridge-gated review-swarm bootstrap surface; it resolves the review plan, compatibility bridge, and status root through `ProjectGovernance` / repo-pack state, with VoiceTerm currently mapping those to `dev/active/review_channel.md`, `bridge.md`, and `dev/reports/review_channel/latest/`; `--action launch` emits Codex/Claude conductor launch scripts, defaults live macOS launches to an `auto-dark` Terminal profile when available, auto-starts the repo-owned ensure-follow publisher from the actual live launch/rollover router, fails closed if that detached publisher does not come up, and still fails closed when the markdown bridge is inactive; local-terminal relaunch/recover guidance now defaults back to visible `--terminal terminal-app`, while governed `remote_control` recovery stays headless with `--terminal none`; fresh launch/recovery decisions should read `startup-context.action`, `interaction_mode`, `reviewer_runtime.conductor_visibility`, and `reviewer_runtime.session_owner.session_visibility` before choosing visible vs headless posture; the publisher remains the persistent service and reclaims the detached reviewer-supervisor runtime on its normal cadence, while the repo now also ships a checked-in launchd template/wrapper pair under `dev/config/launchd/` for login-time restart/backoff semantics outside the live launch path; `--action status`, `--action ensure`, `--action reviewer-heartbeat`, and `--action reviewer-checkpoint` now also emit machine-readable `reviewer_worker` state plus the typed `current_session` live-status block so current instruction / ACK reads no longer depend on append-only bridge prose, preserve shared-context `guidance_refs` when probe guidance is in scope, and keep those refs visible to downstream packet/prompt consumers, while `ensure --follow` frames carry `review_needed` without claiming semantic review completion and also reclaim a missing detached reviewer supervisor in active dual-agent mode; bridge-backed `status` also emits a typed `_compat.bridge_projection` payload so repo-owned bridge repair can rebuild the compatibility projection from typed state instead of reparsing `bridge.md`, and the status-driven sync path may now refresh `bridge.md` from that typed payload even while pending reviewer-targeted packets still exist; strict `render-bridge` remains fail-closed on those pending packets. Bridge/status poll surfaces now also emit `implementer_state_hash` so reviewer-side stale-reader checks can fail closed on Claude-owned state drift, and typed runtime/doctor output now carries explicit conductor visibility (`reviewer_runtime.conductor_visibility`) plus reviewer session visibility (`reviewer_runtime.session_owner.session_visibility`) so headless vs visible vs mixed loops are no longer inferred from raw `terminal_window_id`; detached repo-owned `ensure --follow` / `reviewer-heartbeat --follow` launches pin `--follow-inactivity-timeout-seconds 0`, `--action stop --daemon-kind <publisher|reviewer_supervisor|all>` is the repo-owned daemon reclaim path, and repo-owned reviewer writes now treat `Poll Status` as current-state-only reviewer authority and replace stale reviewer prose instead of stacking fresh heartbeat/checkpoint notes on older revision bullets; `--action doctor` is the compact readiness surface for phone/remote-control clients and now carries publisher/supervisor running state plus the last heartbeat/stop-reason projection alongside `reviewer_runtime` and `commit_pipeline`; active reviewer checkpoints should prefer one typed `--checkpoint-payload-file` or the existing per-section `--*-file` flags for AI-generated markdown / shell-sensitive content instead of inline shell bodies, and `active_dual_agent` writes must carry the live `--expected-instruction-revision` plus `--expected-implementer-state-hash`; the repo-owned wait paths are `--action implementer-wait` for Claude-side bounded waiting and `--action reviewer-wait` for the symmetric Codex-side bounded wait over `reviewer_worker` hash truth plus projected `current_session` ACK/status state from `review_state.json`, not ad hoc shell sleep loops or invented top-level status payload blocks, and Claude-side wait is only valid under an explicit reviewer-owned wait state because low-information updates such as `No change. Continuing.` or `Codex should review` are now contract violations while work is still assigned; `--action recover --recover-provider claude` is the narrower stale-implementer replacement path, but it now fails closed unless a live repo-owned Codex conductor session is already present, and `reviewer-heartbeat --follow` now auto-escalates repeated unchanged stale-implementer state through that repo-owned recovery command instead of sitting forever on polling prose; the same reviewer-follow loop now also auto-escalates repeated unchanged stale reviewer/runtime states through the repo-owned `--action rollover` path so remote-control recovery reuses the structured handoff bundle plus visible ACK contract instead of ad hoc Codex restarts; `--action status` also treats a Claude-only repo-owned session as a hybrid-loop error and `active_dual_agent` with no repo-owned conductors as a bridge-contract error instead of healthy live state; `--action rollover` writes a repo-visible handoff bundle, relaunches fresh conductors before compaction, and can wait for visible ACK lines in `bridge.md`; the ensure orchestration delegates heartbeat refresh, detail assembly, and report construction to `_ensure_helpers.py` so each function stays focused on one concern)
  - Promotion/follow automation must treat reviewer prose as compatibility text, not free-form authority. Readiness checks may only trust explicit primary state markers (for example the first verdict bullet, explicit idle findings, or typed `current_session` truth), never substring hits like `accepted`, `resolved`, or `none` embedded later inside explanatory findings or active instructions.
  - Live launch/replay must bind to typed authority rather than compatibility bridge prose. Resolve operator interaction mode once through governance/startup authority, pass that value through session preparation and the dispatcher gate, and keep generated conductor scripts bound to prepared HEAD, current instruction revision, and the typed `review_state.json` turn/session token; stale prepared authority must exit non-restartably before provider start.
  - Reviewer-supervisor implicit restarts must honor non-restartable lifecycle state too. If the repo-owned heartbeat state records `stop_reason=manual_stop` or `stop_reason=completed`, `ensure` and reviewer-heartbeat auto-start paths must leave the detached reviewer supervisor stopped until an explicit launch/rollover/follow command restores it. The launchd publisher wrapper must also map the stale launch-authority exit code `82` to a no-restart service exit.
  - Launch/session metadata now derives conductor rosters from a typed provider/lane map and records conductor role metadata, so the launcher no longer has to synthesize a fixed reviewer/provider tuple locally before it can write session truth.
  - Live Terminal.app launch now also records the returned `terminal_window_id` in conductor session metadata, and rollover snapshots the retiring session pid plus that window id before rewriting the live files so cleanup can kill the old conductor first and only then close the empty Terminal window.
  - Session-state hints must distinguish fresh launch warmup from a real manual-input stall. Do not classify a visible conductor as `waiting_for_user_input` just because the terminal renders a prompt during active `esc to interrupt` progress or within the first warmup window after launch/recover; recover/relaunch escalation should only key off a true idle prompt with no active-progress marker.
  - Event-backed packet actor/target validation is runtime-owned now: parser arguments stay unbounded text, while `post` / `ack` / `dismiss` / `apply` validate against typed collaboration/runtime state or repo-owned session metadata instead of a parser-hardcoded `codex|claude|operator|system` roster.
  - Bridge `## Action Requests` are projection-only over event-backed `PacketPostRequest(kind="action_request")` packets. Bridge-executable runtime actions (`commit`, `run_check`, `push`, `kill_process`, `stage_commit_pipeline`) must carry typed runtime target metadata before projection: `run_check` / `kill_process` / `stage_commit_pipeline` require target ref and revision, while `commit` / `push` also require remote-commit pipeline generation, staged snapshot hash, and guard summary. Do not rely on free-form packet body prose as executable authority.
  - Event-backed action-request receipts are part of the same runtime contract now. `post` seeds `delivery_emitted_at_utc`, actor-matched `inbox` / `watch` polls stamp `delivery_observed_at_utc` / `delivery_observed_by`, and `ack` / `apply` stamp `execution_started_at_utc` / `execution_started_by`; dashboard/status/phone consumers should read those typed fields instead of inferring delivery or execution only from queue depth.
  - Queue-derived next-step truth must stay action-request-first and receipt-aware. If a live `action_request` packet is still pending, `queue.derived_next_instruction` should prefer it over later findings or commentary, and `derived_next_instruction_source` must preserve `selection_policy`, `control_state`, `wake_required`, and `delivery_required` based on hydrated receipt state. Recompute queue metadata after receipt hydration so the same inbox tick can advance a packet from `delivery_pending` to `execution_pending`.
  - Semantic `Claude Ack` phrasing is now part of that same typed contract: validators, bridge-backed `current_session`, and `bridge-poll` accept both legacy `instruction-rev:` bullets and semantic acknowledgements such as `Acknowledged instruction revision <rev>`, while `bridge-poll` refreshes the typed `review_state` projection before deciding live ACK freshness.
  - Shared runtime consumers must use the repo-owned typed review-state loader
    order too: prefer canonical event-backed state first, then an already-
    written typed projection, and only then fall back to bridge-backed status
    refresh. Do not reintroduce bridge refresh as the default live read path
    once typed authority already exists on disk.
    The 2026-04-21 `rev_pkt_1503` follow-up makes this ordering explicit for
    contract-drift repair too: event-backed
    `projections/latest/review_state.json` payloads must return before
    bridge-contract-drift checks can trigger a bridge-backed refresh.
  - Event-backed review-state compat payloads must keep bridge parity alive
    too: when persisted `_compat.bridge_projection` is missing, rebuild it
    from typed bridge/current-session/runtime state in the same reducer tick
    instead of assuming a prior bridge-backed status refresh already wrote it.
    `check_review_surface_consistency.py` reads
    `review_state_bridge_projection` from the event-backed
    `projections/latest/review_state.json`; a bridge-backed-only compat bridge
    projection is still contract drift.
  - Reviewer/implementer startup role commands plus explicit reviewer takeover are runtime-owned `ConductorCapabilityState` facts now. Prompt/bootstrap/bridge projection surfaces must consume that typed owner contract instead of inventing fallback policy text locally, and `check_platform_layer_boundaries.py` now fails closed if startup-authority/runtime capability modules import `dev.scripts.devctl.review_channel` orchestration directly.
  - Repo-owned reviewer heartbeat refresh must preserve a real reviewer checkpoint `Poll Status` instead of overwriting it with automation-only heartbeat text, and reviewer-owned hold-steady / checkpoint / governed-push-pending state counts as a valid Claude-side wait reason. In those states, conductors should keep polling repo-owned status/wait paths rather than asking the operator to choose between polling, pushing, or side work.
  - `--action reset-implementer-state` is the repo-owned repair path when live attention says implementer-owned sections must return to canonical pending state; it rewrites `Claude Status`, `Claude Questions`, and `Claude Ack`, then refreshes the typed review-channel projection.
  - Dashboard/control-plane observability must consume the same repo-owned
    runtime owners as review-channel status. Prefer shared `session_probe`
    conductor liveness before static `*-conductor.json.session_pid`, preserve
    `implementer_session_state` / `implementer_session_hint` in event-backed
    `current_session`, and keep pending-vs-stale packet counts expiry-aware so
    inbox, status, doctor, and dashboard surfaces agree on queue truth.
  - Instruction-shaped bridge and event-backed projection fields must stay flat markdown only; full `Context Recovery Packet` bodies belong in source metadata and prompt surfaces, not inside `Current Instruction For Claude`, `derived_next_instruction`, or other fixed-section compatibility projections.
- `autonomy-swarm` (adaptive multi-agent orchestration wrapper with metadata-driven worker sizing, optional `--plan-only` allocation mode, bounded per-agent autonomy-loop fanout, default reserved `AGENT-REVIEW` lane for post-audit review when execution runs with more than one lane, per-run swarm summary bundles under `dev/reports/autonomy/swarms/<label>/`, and default post-audit digest bundles under `dev/reports/autonomy/library/<label>-digest/`; disable with `--no-post-audit` and/or `--no-reviewer-lane`; non-report modes require `--fix-command` plus `CoordinationSnapshot.safe_to_fanout=true`, while `--plan-only` and `--mode report-only` remain the safe read-only review/allocation paths)
- `mutation-loop` (bounded mutation remediation loop with mode controls: `report-only`, `plan-then-fix`, `fix-only`; emits md/json/playbook bundles and supports policy-gated fix execution)
- `failure-cleanup` (guarded cleanup for local failure triage bundles under `dev/reports/failures`; default path-root guard, optional `--allow-outside-failure-root` constrained to `dev/reports/**`, CI-green gating with optional `--ci-branch`/`--ci-workflow`/`--ci-event`/`--ci-sha` filters, plus `--dry-run` and confirmation)
- `reports-cleanup` (retention-based cleanup for stale run artifacts under managed `dev/reports/**` roots with protected-path exclusions, dry-run preview, and explicit confirmation/`--yes` delete flow)
- `audit-scaffold`
  - Builds/updates `dev/reports/audits/RUST_AUDIT_FINDINGS.md` from Rust/Python guard failures.
  - Auto-runs when AI-guard checks fail.
  - Run manually when you want a fresh findings file or a commit-range scoped view.
- `session-resume` (typed reviewer/implementer bootstrap packet built from `ControlPlaneReadModel` and repo artifacts; emits `SessionCachePacket` with `head_sha`, `last_reviewed_sha`, optional frozen `review_candidate`, blockers, interaction mode, key rules, and a reduced `authority_snapshot` contract so fresh sessions start from typed state instead of re-reading the repo. It must pass caller-threaded governance and frozen review-state inputs into `ControlPlaneReadModelOptions`, reuse the same promoted `active_target` / `CoordinationSnapshot` path as `startup-context` and dashboard so stale continuity targets cannot diverge from live plan routing or finding pressure, and the same `AuthoritySnapshot` reduction must agree with startup/status on handshake state and next action. Implementer bootstrap is inbox-first too: when `Pending Inbox` / typed packet state already names a Claude-targeted packet or required command, the next bounded action is `review-channel --action inbox --target claude --actor claude --status pending --format md`, not another operator question.)
- `discover` (static capability inventory of commands, guards, probes, and surfaces from existing registries; read-only, never mutates state)
- `view` (thin presentation adapter over typed artifacts with `--surface ai|cli|phone` and `--mode slim|summary`; read-only renderer dispatch, not execution or state mutation)
- `list`

### Quick command intent (plain language)

| Command | Run it when | Why |
|---|---|---|
| `python3 dev/scripts/devctl.py check --profile fast` | while iterating locally | fast local sanity lane (alias of `quick`) that keeps AI-guard scripts on; never a substitute for required pre-push bundles |
| `python3 dev/scripts/devctl.py check --profile pedantic` | you are intentionally doing a broader lint-hardening sweep, usually after a large refactor or as optional pre-release cleanup | runs advisory `clippy::pedantic`, writes structured artifacts under `dev/reports/check/`, and stays out of required merge/release flow |
| `python3 dev/scripts/devctl.py report --pedantic --pedantic-refresh --format json` | you want one command that refreshes the advisory sweep and emits a structured repo-owned summary | reruns pedantic artifact generation, then reads those artifacts plus `dev/config/clippy/pedantic_policy.json` for review/AI consumption |
| `python3 dev/scripts/devctl.py report --rust-audits --with-charts --emit-bundle --format md` | you want one readable Rust guard audit pack with charts, stats, and file hotspots | runs the Rust best-practices, lint-debt, and runtime-panic guards together, explains why the reported patterns are risky, and writes `.md` + `.json` bundle artifacts with optional matplotlib charts |
| `python3 dev/scripts/devctl.py triage --pedantic --no-cihub --emit-bundle --format md` | you want an AI-friendly pedantic cleanup packet without creating a second triage system | folds the saved pedantic artifacts into normal `triage` output and bundle files; add `--pedantic-refresh` only when you intentionally want triage to regenerate the artifacts inline |
| `python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute` | before push when scope spans docs/runtime/tooling/release surfaces | auto-selects the stricter required lane, includes risk add-ons, and runs the routed bundle commands |
| `python3 dev/scripts/devctl.py check --profile ci` | before a normal push | catches compile/test/lint issues early |
| `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm ...` | an AI/dev session needs to run raw Rust tests or test binaries directly | runs the command without a shell wrapper, then automatically executes the required post-test hygiene follow-up so stale host processes do not accumulate |
| `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel --with-process-sweep-cleanup` | right after raw `cargo test` / manual test-binary runs when orphan sweep is needed | runs the AI-guard script pack plus opt-in process sweep and host-side `process-cleanup --verify`, so stale repo-related host trees and structural regressions are caught before later runs |
| `python3 dev/scripts/devctl.py process-cleanup --verify --format md` | after PTY/runtime tests, manual tooling bundles, or before handoff when host access is available | safely kills orphaned/stale repo-related host process trees, including descendant PTY children, repo-cwd background helpers, and orphaned tooling descendants, preserves registry-backed running review-channel conductor PIDs even when prepared authority has gone stale, then reruns strict host audit |
| `python3 dev/scripts/devctl.py process-audit --strict --format md` | when you need read-only host diagnosis or cleanup was intentionally skipped | audits the real host process table for repo leftovers visible in Activity Monitor, including descendant PTY children and repo-cwd runtime/tooling helpers that would otherwise look generic |
| `python3 dev/scripts/devctl.py process-watch --cleanup --strict --stop-on-clean --iterations 6 --interval-seconds 15 --format md` | you are reproducing a host leak or running long-lived local work and want periodic checks instead of one final sweep | reruns the host audit/cleanup loop on a cadence and stops only after the host process table is clean |
| `python3 dev/scripts/devctl.py check --profile release` | before release/tag validation on `master`, or when a feature-branch diff routes through `bundle.release` | adds strict remote CI-status + CodeRabbit/Ralph release gates on top of local checks, with mutation-score surfaced as non-blocking reminder output; off the configured release branch it resolves the active branch and allows commit fallback instead of hardcoding `master` |
| `python3 dev/scripts/devctl.py docs-check --user-facing` | user behavior/docs changed | keeps user docs aligned with behavior |
| `python3 dev/scripts/devctl.py docs-check --strict-tooling` | tooling/process/CI changed | enforces governance and active-plan sync |
| `python3 dev/scripts/devctl.py tandem-validate --format md` | a Codex/Claude tandem slice needs one canonical validator instead of a hand-written checklist | resolves the real lane through `check-router`, runs the routed bundle plus risk add-ons, then rechecks review-channel and tandem consistency |
| `python3 dev/scripts/devctl.py doc-authority --format md` | you need the current governed-markdown authority set before changing docs, plans, or startup surfaces | scans the reviewed markdown roots and emits the typed registry/metadata view the rest of the governance stack should consume |
| `python3 dev/scripts/devctl.py governance-draft --format md` | you need the deterministic governed-doc discovery surface before a write-mode governance/docs change | renders the repo-owned starter/governed-doc packet that should stay aligned with CLI inventory and maintainer docs |
| `python3 dev/scripts/devctl.py render-surfaces --format md` | repo-pack templates/policy changed or you need to inspect governed instruction/starter surfaces | previews the current sync state for policy-owned generated surfaces; add `--write` to regenerate drifted outputs |
| `python3 dev/scripts/devctl.py system-map --format md` | you need the generated SYSTEM_MAP typed connectivity snapshot without writing docs | renders `SystemMapSnapshot` plus the shared `ConnectivityRegistrySnapshot` used by context-graph, startup-context, session-resume, render-surfaces, and closure guards |
| `python3 dev/scripts/devctl.py publication-sync --format md` | external paper/site content depends on repo evidence and you need drift visibility | reports watched-path changes since the last recorded sync and shows how to record a new baseline after publish |
| `python3 dev/scripts/devctl.py data-science --format md` | you want one fresh telemetry + agent-sizing snapshot | summarizes command productivity, success/latency stats, and recommended swarm size from historical runs |
| `python3 dev/scripts/devctl.py governance-review --format md` | you want the current false-positive / cleanup scoreboard for adjudicated guard and probe findings | reads the governance review JSONL log, rolls up latest verdicts per finding, and writes refreshed `review_summary.{md,json}` artifacts |
| `python3 dev/scripts/devctl.py governance-import-findings --input <path> --format md` | you need to bring external review findings into the repo-owned ledger instead of carrying them in ad hoc notes | normalizes external finding metadata, appends auditable records, and also accepts `--input-format md` for `LIVE_RUN.md` compatibility intake with repo-scoped `Q-ID` sync identity |
| `python3 dev/scripts/devctl.py governance-quality-feedback --format md` | you want one current view of guidance adoption and quality-policy feedback signals | summarizes adjudicated findings and probe-guidance follow-through for policy tuning and platform evidence |
| `python3 dev/scripts/devctl.py mcp --tool status_snapshot --format json` | an MCP client needs a read-only contract snapshot without changing `devctl` governance authority | exposes allowlisted tools/resources and optional stdio transport while keeping enforcement ownership in `devctl` |
| `python3 dev/scripts/devctl.py integrations-sync --status-only --format md` | you want current federated source pins (`code-link-ide`, `ci-cd-hub`) before import/sync work | gives auditable source SHA + status visibility in one command |
| `python3 dev/scripts/devctl.py integrations-import --list-profiles --format md` | you want to import reusable upstream surfaces safely | shows allowlisted source/profile mappings before any file writes |
| `python3 dev/scripts/devctl.py triage-loop --branch develop --mode plan-then-fix --max-attempts 3 --format md` | you want bounded CodeRabbit remediation automation with artifacts | runs report/fix loop under policy gates, writes actionable loop evidence plus the bounded backlog slice used by autonomy `loop-packet`, and can auto-publish review escalation comments when retries exhaust |
| `python3 dev/scripts/devctl.py loop-packet --format json` | you want one guarded packet for terminal draft injection from loop/triage evidence | builds a risk-scored packet with draft text and auto-send eligibility metadata |
| `python3 dev/scripts/devctl.py autonomy-loop --plan-id <id> --branch-base develop --mode report-only --max-rounds 6 --max-hours 4 --max-tasks 24 --format json` | you want a bounded autonomy-controller run with checkpoint packets and queue artifacts | orchestrates triage-loop/loop-packet rounds with policy-gated stop reasons, run-scoped outputs, and phone-ready `latest.json`/`latest.md` status snapshots |
| `python3 dev/scripts/devctl.py phone-status --view compact --format md` | you want one fast iPhone/SSH-safe controller snapshot from loop artifacts | loads `queue/phone/latest.json`, renders a compact/trace/actions/full view, and can emit controller-state projection files for downstream clients |
| `python3 dev/scripts/devctl.py mobile-app --action simulator-demo --format md` | you want the real iPhone app built, installed into the simulator, and launched against the live repo bundle | runs the guided simulator flow over the first-party mobile app and prints the real bundle/app paths instead of sample-only data |
| `python3 dev/scripts/devctl.py controller-action --action dispatch-report-only --repo <owner/repo> --branch develop --dry-run --format md` | you want one guarded remote-control action surface without ad-hoc shell steps | validates policy allowlists/mode gates, then executes or previews bounded dispatch/pause/resume/status actions with auditable output |
| `python3 dev/scripts/devctl.py ralph-status --report-dir dev/reports/ralph --format md` | you want one current view of Ralph guardrail progress before wiring phone or PyQt surfaces on top | aggregates Ralph report artifacts into fix/open counts, architecture breakdowns, and guidance-adoption state for downstream consumers |
| `python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format md` | you want to bootstrap the current Codex-reviewer / Claude-coder 8+8 markdown swarm from a fresh conversation | validates that the markdown bridge is still active, refuses launch when typed checkpoint budget says another implementation slice would exceed the continuation budget, reads the merged lane table from `dev/active/review_channel.md`, generates conductor launch scripts, and shows the exact bootstrap before opening any terminals |
| `python3 dev/scripts/devctl.py review-channel --action rollover --rollover-threshold-pct 20 --await-ack-seconds 180 --format md` | the active conductor is nearing compaction and needs a clean relaunch instead of relying on recovery summaries | writes a repo-visible handoff bundle, relaunches fresh Codex/Claude conductors, and waits for visible rollover ACK lines in `bridge.md` before the retiring session exits |
| `python3 dev/scripts/devctl.py review-channel --action render-bridge --terminal none --format md` | the live markdown bridge has drifted into transcript/history junk and needs a repo-owned rebuild | rewrites `bridge.md` from the typed `review_state` compatibility projection payload plus sanitized fixed sections, rejects embedded markdown headings in flat bridge sections fail-closed, refuses to overwrite reviewer-owned sections while pending reviewer-targeted packets still exist, drops unsupported headings/report blobs, refreshes review-channel projections, and leaves stale ACK/review truth explicit instead of preserving a 4000-line mixed transcript |
| `python3 dev/scripts/devctl.py autonomy-benchmark --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --swarm-counts 10,15,20,30,40 --tactics uniform,specialized,research-first,test-first --dry-run --format md` | you want measurable swarm tradeoff data before scaling live worker runs | validates active-plan scope, runs tactic/swarm-size matrix batches, and emits one benchmark report with per-scenario productivity metrics/charts |
| `python3 dev/scripts/devctl.py swarm_run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --mode report-only --run-label <label> --format md` | you want one fully-guarded plan-scoped swarm run without manual glue steps | loads active-plan scope, executes swarm with reviewer+post-audit defaults, runs governance checks, and appends progress/audit evidence to the plan doc |
| `python3 dev/scripts/devctl.py autonomy-report --source-root dev/reports/autonomy --library-root dev/reports/autonomy/library --run-label <label> --format md` | you want one operator-readable autonomy digest | assembles latest loop/watch artifacts into a dated bundle with markdown/json summary and chart outputs |
| `python3 dev/scripts/devctl.py autonomy-swarm --question-file <plan.md> --adaptive --min-agents 4 --max-agents 20 --plan-only --format md` | you want one governed worker-allocation decision before launching Claude/Codex lanes | computes metadata-driven agent sizing with rationale and emits a deterministic swarm plan artifact |
| `python3 dev/scripts/devctl.py autonomy-swarm --agents 10 --question-file <plan.md> --mode report-only --run-label <label> --format md` | you want one-command live swarm execution with built-in review lane and digest | runs bounded worker fanout, reserves default `AGENT-REVIEW` when possible, and auto-runs post-audit digest artifacts |
| `python3 dev/scripts/devctl.py mutation-loop --branch develop --mode report-only --threshold 0.80 --max-attempts 3 --format md` | you want bounded mutation remediation automation with hotspot evidence | runs report/fix loop and writes actionable mutation artifacts |
| `python3 dev/scripts/devctl.py reports-cleanup --dry-run` | hygiene warns report artifacts are stale/heavy | previews retention cleanup candidates under managed `dev/reports/**` roots |
| `python3 dev/scripts/devctl.py session-resume --role reviewer --format bootstrap` | fresh reviewer/implementer session start or session rollover | canonical role-first bootstrap packet; use `--role reviewer` or `--role implementer` so either provider can start from the typed `head_sha`, `last_reviewed_sha`, frozen `review_candidate` when dirty-tree review is ready, blockers, and exact next guard bundle instead of re-reading the repo |
| `python3 dev/scripts/devctl.py security` | deps or security-sensitive code changed | catches policy/advisory issues |
| `python3 dev/scripts/devctl.py audit-scaffold --force --yes --format md` | guard failures need a fix plan | creates one shared remediation file |

Implementation note for maintainers:

- Shared internals in `devctl` are intentional and should stay centralized:
  `dev/scripts/devctl/process_sweep/` (process parsing/cleanup package),
  `dev/scripts/devctl/security/parser.py` (security CLI parser wiring),
  `dev/scripts/devctl/security/codeql.py` (CodeQL alert-fetch wiring for security gate),
  `dev/scripts/devctl/security/python_scope.py` (Python changed/all scope resolution + core scanner targets),
  `dev/scripts/devctl/audit_events.py` (auto-emitted per-command audit-metrics event logging),
  `dev/scripts/devctl/autonomy/report_helpers.py` (autonomy-report source discovery + summarization helpers),
  `dev/scripts/devctl/autonomy/report_render.py` (autonomy-report markdown/chart renderer helpers),
  `dev/scripts/devctl/autonomy/swarm_helpers.py` (adaptive swarm metadata scoring + sizing + report renderer helpers),
  `dev/scripts/devctl/autonomy/swarm_post_audit.py` (shared autonomy-swarm post-audit payload + digest helpers),
  `dev/scripts/devctl/autonomy/loop_helpers.py` (shared autonomy-loop packet/policy/render helper logic),
  `dev/scripts/devctl/autonomy/phone_status.py` (phone-ready autonomy status payload/render helpers),
  `dev/scripts/devctl/phone_status_views.py` (phone-status projection/render helpers and projection-bundle writer),
  `dev/scripts/devctl/autonomy/status_parsers.py` (shared parser wiring for autonomy-report + phone-status),
  `dev/scripts/devctl/controller_action_parser.py` (`controller-action` parser wiring),
  `dev/scripts/devctl/controller_action_support.py` (`controller-action` policy/mode/dispatch helper logic),
  `dev/scripts/devctl/sync_parser.py` (sync CLI parser wiring),
  `dev/scripts/devctl/integrations_sync_parser.py` (`integrations-sync` parser wiring),
  `dev/scripts/devctl/integrations_import_parser.py` (`integrations-import` parser wiring),
  `dev/scripts/devctl/cihub_setup_parser.py` (`cihub-setup` parser wiring),
  `dev/scripts/devctl/integration_federation_policy.py` (external federation policy + allowlist helpers),
  `dev/scripts/devctl/orchestrate_parser.py` (orchestrator CLI parser wiring),
  `dev/scripts/devctl/script_catalog.py` (canonical check-script path registry),
  `dev/scripts/devctl/path_audit_parser.py` (path-audit/path-rewrite parser wiring),
  `dev/scripts/devctl/path_audit.py` (shared stale-path scanner + rewrite engine via stable shim),
  `dev/scripts/devctl/path_audit_support/core.py` (path-audit legacy-scan + rewrite helpers),
  `dev/scripts/devctl/path_audit_support/workspace.py` (workspace-contract path-audit helpers),
  `dev/scripts/devctl/triage/parser.py` (triage parser wiring),
  `dev/scripts/devctl/triage/loop_parser.py` (triage-loop parser wiring),
  `dev/scripts/devctl/loop_fix_policy.py` (shared fix-policy engine used by both triage-loop and mutation-loop policy wrappers),
  `dev/scripts/devctl/triage/loop_policy.py` (triage-loop fix policy evaluation),
  `dev/scripts/devctl/triage/loop_escalation.py` (triage-loop escalation comment helper logic),
  `dev/scripts/devctl/triage/loop_support.py` (triage-loop connectivity/comment/bundle helper logic),
  `dev/scripts/devctl/loop_packet_parser.py` (loop-packet parser wiring),
  `dev/scripts/devctl/autonomy/loop_parser.py` (autonomy-loop parser wiring),
  `dev/scripts/devctl/autonomy/benchmark_parser.py` (autonomy-benchmark parser wiring),
  `dev/scripts/devctl/autonomy/run_parser.py` (`swarm_run` parser wiring),
  `dev/scripts/devctl/autonomy/benchmark_helpers.py` (autonomy-benchmark scenario orchestration + metrics helpers),
  `dev/scripts/devctl/autonomy/benchmark_matrix.py` (autonomy-benchmark matrix planner/execution helpers),
  `dev/scripts/devctl/autonomy/benchmark_runner.py` (autonomy-benchmark scenario runner + per-scenario bundle helpers),
  `dev/scripts/devctl/autonomy/benchmark_render.py` (autonomy-benchmark markdown/chart renderer),
  `dev/scripts/devctl/autonomy/run_helpers.py` (`swarm_run` shared scope/prompt/governance/plan-update helpers),
  `dev/scripts/devctl/autonomy/run_render.py` (`swarm_run` markdown renderer),
  `dev/scripts/devctl/failure_cleanup_parser.py` (failure-cleanup parser wiring),
  `dev/scripts/devctl/reports_cleanup_parser.py` (reports-cleanup parser wiring),
  `dev/scripts/devctl/reports_retention.py` (shared report-retention planner used by hygiene + reports-cleanup),
  `dev/scripts/devctl/commands/audit_scaffold.py` (guard-to-remediation scaffold generation),
  `dev/scripts/devctl/triage/support.py` (triage rendering + bundle helpers),
  `dev/scripts/devctl/triage/enrich.py` (triage owner/category/severity enrichment),
  `dev/scripts/devctl/commands/triage_loop.py` (bounded CodeRabbit loop command),
  `dev/scripts/devctl/commands/controller_action.py` (policy-gated controller action command),
  `dev/scripts/devctl/commands/loop_packet.py` (guarded loop-to-terminal packet builder),
  `dev/scripts/devctl/commands/autonomy_loop.py` (bounded autonomy controller loop command + checkpoint queue artifacts),
  `dev/scripts/devctl/commands/autonomy_benchmark.py` (active-plan-scoped swarm matrix benchmark command),
  `dev/scripts/devctl/commands/autonomy_run.py` (guarded plan-scoped `swarm_run` pipeline command),
  `dev/scripts/devctl/commands/autonomy_report.py` (human-readable autonomy digest command),
  `dev/scripts/devctl/commands/autonomy_swarm.py` (adaptive swarm planner/executor with per-agent autonomy-loop fanout),
  `dev/scripts/devctl/commands/autonomy_loop_support.py` (autonomy-loop validation + policy-deny report helpers),
  `dev/scripts/devctl/commands/autonomy_loop_rounds.py` (autonomy-loop round executor helper),
  `dev/scripts/devctl/commands/docs_check_support.py` (docs-check policy + failure-action helper builders),
  `dev/scripts/devctl/commands/docs_check_render.py` (docs-check markdown renderer helpers),
  `dev/scripts/devctl/commands/check_profile.py` (check profile normalization),
  `dev/scripts/devctl/policy_gate.py` (shared JSON policy gate runner),
  `dev/scripts/devctl/status_report.py` (status/report payload + markdown
  rendering), `dev/scripts/devctl/commands/security.py` (local security gate
  orchestration + optional scanner policy),
  `dev/scripts/devctl/commands/integrations_sync.py` (policy-guarded external-source sync/status command),
  `dev/scripts/devctl/commands/integrations_import.py` (allowlisted selective external-source importer + audit log),
  `dev/scripts/devctl/commands/cihub_setup.py` (allowlisted CIHub setup command implementation),
  `dev/scripts/devctl/commands/failure_cleanup.py` (guarded failure-artifact cleanup),
  `dev/scripts/devctl/commands/reports_cleanup.py` (retention-based stale report cleanup),
  and `dev/scripts/devctl/commands/ship_common.py` /
  `dev/scripts/devctl/commands/ship_steps.py` (release-step helpers), plus
  `dev/scripts/devctl/common.py` for shared command-execution failure handling.
  Keep new logic in these helpers to avoid command drift.

Supporting scripts:

- `dev/scripts/checks/check_agents_contract.py`
- `dev/scripts/checks/check_agents_bundle_render.py`
- `dev/scripts/checks/check_active_plan_sync.py`
- `dev/scripts/checks/check_architecture_surface_sync.py`
- `dev/scripts/checks/check_review_channel_bridge.py`
- `dev/scripts/checks/check_multi_agent_sync.py`
- `dev/scripts/checks/check_cli_flags_parity.py`
- `dev/scripts/checks/check_release_version_parity.py`
- `dev/scripts/checks/check_coderabbit_gate.py`
- `dev/scripts/checks/check_coderabbit_ralph_gate.py`
- `dev/scripts/checks/check_screenshot_integrity.py`
- `dev/scripts/checks/check_code_shape.py`
- `dev/scripts/checks/check_workflow_shell_hygiene.py`
- `dev/scripts/checks/check_workflow_action_pinning.py`
- `dev/scripts/checks/check_bundle_workflow_parity.py`
- `dev/scripts/checks/check_ide_provider_isolation.py`
- `dev/scripts/checks/check_compat_matrix.py`
- `dev/scripts/checks/compat_matrix_smoke.py`
- `dev/scripts/checks/check_naming_consistency.py`
- `dev/scripts/checks/check_rust_test_shape.py`
- `dev/scripts/checks/check_rust_lint_debt.py`
- `dev/scripts/checks/check_rust_best_practices.py`
- `dev/scripts/checks/check_rust_compiler_warnings.py`
- `dev/scripts/checks/check_serde_compatibility.py`
- `dev/scripts/checks/check_rust_runtime_panic_policy.py`
- `dev/scripts/checks/check_rust_security_footguns.py`
- `dev/scripts/checks/check_clippy_high_signal.py`
- `dev/scripts/checks/check_mutation_score.py`
- `dev/scripts/checks/check_rustsec_policy.py`
- `dev/scripts/checks/run_coderabbit_ralph_loop.py`
- `dev/scripts/checks/mutation_ralph_loop_core.py`
- `dev/scripts/checks/workflow_loop_utils.py`
- `dev/scripts/audits/audit_metrics.py`
- `dev/scripts/tests/measure_latency.sh`
- `dev/scripts/tests/wake_word_guard.sh`
- `dev/scripts/workflow_bridge/shell.py`
- `scripts/macros.sh`

`check_code_shape.py` enforces both language-level limits and path-level
hotspot budgets, adds targeted function-length guardrails for dispatcher/
pipeline hotspots, and flags stale loose path overrides when files remain below
language soft limits for the configured review window.
`check_workflow_shell_hygiene.py` blocks fragile inline workflow shell patterns
(`find ... | head -n 1`, inline Python snippets) so helper bridges stay the
canonical workflow logic path.
`check_workflow_action_pinning.py` blocks non-SHA and dynamic `uses:` refs so
workflow actions stay pinned to immutable commits.
`check_agents_bundle_render.py` blocks drift between AGENTS rendered bundle
reference docs and canonical registry output; run with `--write` to regenerate
the section from `dev/scripts/devctl/bundle_registry.py`.
`check_architecture_surface_sync.py` blocks newly added active-plan docs,
check scripts, devctl commands, app surfaces, and workflow files from landing
without their owning authority wiring (index/plan/docs/bundle/workflow README
references).
`check_python_subprocess_policy.py` blocks repo-owned Python tooling and
Operator Console code from calling `subprocess.run(...)` without an explicit
`check=` keyword.
`check_command_source_validation.py` blocks launcher/package Python entrypoints
from rebuilding unsafe command sources (`shlex.split(...)` on CLI/env/config
input, raw `sys.argv` forwarding, env-controlled command argv without
validation); during the pilot it is intentionally scoped through the selectable
launcher lane rather than the full default repo policy.
`check_python_broad_except.py` blocks newly added `except Exception` /
`except BaseException` handlers in repo-owned Python tooling/app code unless a
nearby `broad-except: allow reason=...` comment documents the fail-soft path.
`check_bundle_workflow_parity.py` blocks registry/workflow command-bundle drift
by verifying `bundle.tooling` and `bundle.release` commands from
`dev/scripts/devctl/bundle_registry.py` still appear in their owning workflows.
`check_ide_provider_isolation.py` now runs in blocking mode by default and
allows mixed host/provider statements only in explicitly allowlisted policy
owner files.
`check_compat_matrix.py` + `compat_matrix_smoke.py` enforce machine-readable
host/provider compatibility metadata coverage and runtime enum smoke parity.
`check_naming_consistency.py` enforces canonical host/provider token alignment
across runtime enums, backend registry IDs, compatibility matrix policy sets,
and IDE/provider isolation token patterns.
`check_rust_test_shape.py` enforces non-regressive growth controls for Rust
test hotspots (`tests.rs` / `tests/**`) with path-specific budgets for known
large suites.
`check_active_plan_sync.py` enforces active-doc index/spec parity, mirrored-spec
phase heading and `MASTER_PLAN` link contracts, and `MASTER_PLAN` Status
Snapshot release freshness (branch policy + release-tag consistency).
`check_review_channel_bridge.py` enforces the temporary markdown review bridge
contract so `bridge.md` remains a valid fresh-conversation bootstrap
artifact for the current Codex-reviewer / Claude-coder loop, including the
required authority bootstrap order, section ownership, local+UTC heartbeat
header, and operator-visible reviewer chat ping requirement.
`check_multi_agent_sync.py` enforces dynamic multi-agent coordination parity
between the `MASTER_PLAN` board and the runbook (lane/MP/worktree/branch alignment,
instruction/ack protocol validation, lane-lock + MP-collision handoff checks,
status/date format checks, ledger traceability, and end-of-cycle signoff when
all agent lanes are marked merged). When typed `review_state` exists, it also
fails closed if planned `AGENT-*` rows leak into live collaboration
participants or the runtime registry without live delegated-worker receipts.
`check_rust_lint_debt.py` enforces non-regressive growth for `#[allow(...)]`
and non-test `unwrap/expect` call-sites in changed Rust files.
`check_rust_best_practices.py` blocks non-regressive growth of reason-less
`#[allow(...)]`, undocumented `unsafe { ... }` blocks, public `unsafe fn`
surfaces without `# Safety` docs, and `std::mem::forget`/`mem::forget` usage
in changed Rust files, plus `Result<_, String>` surfaces, suppressed
channel-send and event-emitter results, bare detached `thread::spawn(...)`
statements without a nearby `detached-thread: allow reason=...` note,
`unwrap()/expect()` on `join`/`recv` paths, and suspicious
`OpenOptions::new().create(true)` chains that do not make overwrite semantics
explicit via `append(true)`, `truncate(...)`, or `create_new(true)`, plus
direct `==` / `!=` comparisons against float literals, plus app-owned
persistent TOML writes that still use direct overwrite helpers instead of a
temp-file swap, plus hand-rolled persistent TOML parsers where the standard
`toml` crate should be used instead.
`check_rust_compiler_warnings.py` runs a no-run JSON `cargo test` compile and
fails when rustc warnings resolve to changed repo-owned `.rs` files, so
warning-only debt such as `unused_imports` gets a dedicated changed-file gate
instead of hiding behind broader Clippy/best-practices checks.
`check_serde_compatibility.py` blocks newly introduced internally or
adjacently tagged Rust `Deserialize` enums unless they either define a
`#[serde(other)]` fallback variant or document intentional fail-closed
behavior with a nearby `serde-compat: allow reason=...` comment.
`check_rust_runtime_panic_policy.py` blocks non-regressive growth of runtime
`panic!` call-sites unless the new panic path is explicitly allowlisted with
`panic-policy: allow reason=...` rationale comments, and it supports
`--absolute` for full-tree Rust panic audits.
`check_rust_security_footguns.py` also blocks non-regressive growth of
`unreachable!()` in runtime hot paths in addition to the existing shell-spawn,
weak-crypto, permissive-mode, PID-cast, and syscall-cast checks.
`check_guard_enforcement_inventory.py` blocks cataloged check scripts from
drifting out of real bundle/workflow enforcement lanes unless they are
explicitly marked helper-only, manual-only, or temporary advisory backlog
exemptions.
Public `dev/scripts/checks/check_*.py` entrypoints are also self-hosting
authority surfaces: every new guard or compatibility shim must be registered
in `dev/scripts/devctl/script_catalog.py` and documented in
`dev/scripts/README.md` in the same change, or hygiene/governed-push
preflight should fail closed before publication.
`check_clippy_high_signal.py` enforces baseline ceilings for selected
high-signal Clippy lints using lint-code histogram JSON from
`collect_clippy_warnings.py`.

## CI workflows (reference)

- `rust_ci.yml`
- `voice_mode_guard.yml`
- `wake_word_guard.yml`
- `perf_smoke.yml`
- `latency_guard.yml`
- `memory_guard.yml`
- `mutation-testing.yml`
- `security_guard.yml`
- `dependency_review.yml`
- `workflow_lint.yml`
- `coderabbit_triage.yml`
- `scorecard.yml`
- `parser_fuzz_guard.yml`
- `coverage.yml`
- `docs_lint.yml`
- `lint_hardening.yml`
- `coderabbit_ralph_loop.yml`
- `autonomy_controller.yml`
- `autonomy_run.yml`
- `release_preflight.yml`
- `release_attestation.yml`
- `tooling_control_plane.yml`
- `orchestrator_watchdog.yml`
- `failure_triage.yml`
- `publish_pypi.yml`
- `publish_homebrew.yml`
- `publish_release_binaries.yml`

## CI expansion policy

Add or extend CI when new risk classes are introduced:

- New latency-sensitive logic -> perf/latency guard coverage
- New long-running threads/workers -> memory loop/soak coverage
- New release/distribution mechanics -> release/homebrew/pypi validation
- New user modes/flags -> at least one integration lane exercises them
- New dependency/supply-chain exposure -> security policy coverage
- New parser/control-sequence boundary logic -> property-fuzz coverage
- New/edited workflows must keep action refs SHA-pinned (`uses: org/action@<40-hex>`)
  and declare explicit `permissions:` + `concurrency:` blocks.

## Mandatory self-review checklist

Before calling implementation done, review for:

- Security: injection, unsafe input handling, secret exposure
- Memory: unbounded buffers, leaks, large allocations
- Error handling: unwrap/expect in non-test code, missing failure paths
- Concurrency: deadlocks, races, lock contention
- Performance: unnecessary allocations, blocking in hot paths
- Style/maintenance: clippy warnings, naming, dead code
- API/docs alignment: Rust reference checks captured for non-trivial changes
- CI supply chain: workflow refs pinned, permissions least-privilege, concurrency set
- CI runtime hardening: workflows define explicit `timeout-minutes` budgets for long-running/security-sensitive jobs

## Handoff paper trail protocol

For substantive sessions, use `dev/guides/DEVELOPMENT.md` -> `Handoff paper trail template`.
Include:

- exact commands run
- docs decisions (`updated` or `no change needed`)
- screenshot decisions
- Rust references consulted (for non-trivial Rust changes)
- follow-up MP IDs

## Archive and ADR policy

- Keep `dev/archive/` immutable (no deletions/rewrites).
- Keep active execution in `dev/active/MASTER_PLAN.md`.
- Use `dev/adr/` for architecture decisions.
- Keep ADR numbering governance metadata current in `dev/adr/README.md`
  (`Retired ADR IDs`, `Reserved ADR IDs`, and `next: NNNN`).
- Supersede ADRs with new ADRs; do not rewrite old ADR history.

## End-of-session checklist

- [ ] Mandatory SOP steps were completed.
- [ ] Verification commands passed for scope.
- [ ] When host process access was available and PTY/runtime tests, manual tooling bundles, or other orphan-risk local work ran, `python3 dev/scripts/devctl.py process-cleanup --verify --format md` passed or the limitation was recorded; if cleanup was intentionally skipped, `python3 dev/scripts/devctl.py process-audit --strict --format md` passed or the limitation was recorded.
- [ ] Docs updated per governance checklist.
- [ ] `dev/CHANGELOG.md` updated if behavior is user-facing.
- [ ] `dev/active/MASTER_PLAN.md` updated.
- [ ] Repeat-to-automate outcomes captured (new automation or debt-register entry).
- [ ] Follow-up work captured as MP items.
- [ ] Handoff summary captured.
- [ ] Root `--*` artifact check run and clean.
- [ ] Git state is clean or intentionally staged/committed.

## Notes

- `dev/archive/2026-01-29-claudeaudit-completed.md` contains the production readiness checklist.
- Prefer editing existing files over creating new ones.
