# Agent Substrate Architecture Review

Status: reference-only architecture review for `MP-377` Plan 4.1.
Date: 2026-04-27.

Execution authority stays in `dev/active/MASTER_PLAN.md` and the typed phase
registry in `dev/active/ai_governance_platform.md`. This document records the
Codex 11 validation of `rev_pkt_2001`, `rev_pkt_2000`, the four-agent
investigation report at `/tmp/agent_investigation_reports_2026-04-27.md`, and
the Codex 12 validation of `rev_pkt_2006` plus
`/tmp/agent_investigation_8parallel_2026-04-27.md`.

## Decision

The next executable slice is a narrow Slice C/D bridge: make the existing
review-surface consistency proof use explicit field authority and compare
`operator_interaction_mode` as its own axis. This unblocks the local Slice A
commit without creating a second runtime system.

Codex 12 extends that same Slice C/D bridge without changing the authority
model: refresh `commit_pipeline` proof identity after push-result sync, add a
warning-only enum-value connectivity guard, and centralize
`OperatorInteractionMode` launch/approval policy in `operator_context.py`.
Dynamic role flipping remains Slice E.

The broader "system in one place" architecture is not a new service. It is the
existing platform projection chain made explicit:

1. `ProjectGovernance` and repo-pack policy own repo-local configuration.
2. `ReviewState` / `CollaborationSession` own live runtime facts.
3. `StartupContext` / `AuthoritySnapshot` reduce those facts into one
   turn-sized authority packet for agents and dashboards.
4. `bridge.md`, `REVIEW_SNAPSHOT.md`, compact projections, dashboard rows, and
   docs are compatibility or read-model projections.
5. Guards compare projections back to the typed authority source for each
   field instead of letting a compatibility projection become authority by
   iteration order.

## Validated Findings

### Mode Axes

Current state: `reviewer_mode` is the review-loop posture enum
(`active_dual_agent`, `single_agent`, `tools_only`, `paused`, `offline`).
`remote_control` is not missing from that enum; it already exists under
`OperatorInteractionMode` in `dev/scripts/devctl/runtime/operator_context.py`.

Operator intent: the operator channel can be remote while the reviewer loop is
active dual-agent, single-agent, or degraded. Those are separate facts.

Gap: some surfaces and checks still make humans reconcile the axes manually,
especially when a remote-control attachment is live but the runtime is
degraded or detached.

Typed fix: keep `reviewer_mode` and `operator_interaction_mode` as separate
proof-tick fields. Startup-context remains the turn authority that resolves
the operator channel from governance, review-state payloads, receipt evidence,
and live `RemoteControlAttachmentState`.

Plan mapping: this lands in the Slice C/D boundary because it is a
surface-consistency and projection-spine repair. The governed setter for
`operator_interaction_mode` remains the G18 follow-up under remote-control
runtime scope.

### Proof-Tick Authority

Current state: `check_review_surface_consistency` normalized proof-tick fields
across surfaces, but `proof_tick.py` picked the first populated value as
`expected`. That made insertion order a hidden authority source.

Operator intent: one canonical system picture should explain which value is
authoritative and which projection drifted.

Gap: a stale or compatibility-shaped surface could become expected before
`startup_context` or another typed reducer was read. Live validation also
corrected the `rev_pkt_2000` framing: not every surface agreed on
`active_dual_agent`; declared reviewer posture and effective runtime posture
were split while first-found-wins hid the authority choice.

Typed fix: proof-tick parity now uses explicit field authority priority.
For `reviewer_mode`, `effective_reviewer_mode`, and
`operator_interaction_mode`, `startup_context` is the preferred turn-level
authority, with typed runtime/read-model surfaces as fallbacks and bridge
compatibility later in the order. Other fields use a stable default priority
instead of raw dictionary iteration.

Codex 12 follow-up: `implementation_permission` now explicitly prefers
`startup_context`, while `next_command` prefers `AuthoritySnapshot`, matching
the existing runtime contract that reducers should project allowed actions
from the authority snapshot instead of sibling compatibility projections.

Plan mapping: this is the immediate Slice D projection-spine repair needed to
publish the local Slice A commit. It also supports Slice C by making the guard
say which projection drifted before any later fail-closed enforcement change.

### Capability On Identity

Current state: `CollaborationSession` already carries
`mutation_owner`, `verification_owner`, `watcher_owner`, and
`actor_authorities` with `CapabilityGrantState` grants. The live role list can
assign more than one role to one agent, as with reviewer plus lead or remote
operator plus implementer.

Operator intent: any provider should be able to hold any role when typed
authority grants it, including future multi-agent and role-flip operation.

Gap: role assignment is still derived during session assembly. There is no
governed mutable `role_assignments` action, no assignment event ledger, no
capability re-grant trigger after a role change, and read paths still accept
caller roles as string inputs in several places.

Typed fix: extend the existing `CollaborationSession` /
`ActorAuthorityState` / `CapabilityGrantState` chain. Add governed
`assign_role` / `unassign_role` actions, allow explicit multi-role and
multi-holder rows where policy permits them, re-run capability grants from
the resulting assignment snapshot, and bind caller identity/role to the
authority snapshot instead of trusting prose flags.

Plan mapping: this is Slice E boundary and capability migration work. It is
not part of the immediate rev_pkt_2000 unblock because a partial role-flip
implementation would create another authority layer.

Slice E implementation sub-scope from `rev_pkt_2030` / `rev_pkt_2035`:

- Add governed `assign_role` and `unassign_role` actions that mutate typed role
  assignment state and re-run `CapabilityGrantState` derivation from that
  assignment snapshot.
- Gate `devctl commit`, `devctl push`, stage handoff, review checkpoint, and
  approval flows on caller identity plus `ActorAuthorityState` capabilities such
  as `repo.commit`, `repo.stage`, `repo.push`, `review.checkpoint`, and
  `approval.commit`.
- Retire `DEFAULT_PROVIDER_ROLE_MAP` as runtime authority. Provider names may
  remain compatibility labels, but Codex and Claude must both be able to hold
  reviewer, implementer, dashboard, observer, or multi-role authority when typed
  policy grants it.
- Add role-flip and out-of-role regression coverage proving provider defaults do
  not decide mutation permission and dashboard/observer callers fail closed with
  `actor_authority_capability_denied`.

## Slice Placement

Slice B: packet lifecycle reducer and Codex packet consumer loop. Use it for
pending/stale packet outcomes and ADR-016; do not solve proof-tick authority
there.

Slice C: connectivity, retirement, and guard promotion. Use it to retire
duplicate observer/consumer routes and promote warning-only connectivity after
baseline retirement. This slice consumes the clearer proof-tick expected-source
diagnostics.

Slice D: projection spine. Use it for the canonical field authority map,
projection refresh ordering, and surface parity over one frozen proof tick.
The rev_pkt_2000 fix is the first bounded piece.

The rev_pkt_2006 zref repair also belongs here: commit-pipeline state sync is
not allowed to write state-only drift after a managed receipt refresh. It must
recompute `snapshot_id`/`zref` from the current review-state tick before
persisting.

Slice E: boundary and capability migration. Use it for dynamic role
assignment, multi-role policy, caller identity binding, and removal of legacy
reviewer-mode mutation fallbacks.

## Publication Plan

1. Land the proof-tick authority fix and architecture review doc in the same
   governed commit request as the pending Slice A publication support.
2. Rerun focused consistency tests, live `check_review_surface_consistency`,
   active-plan sync, docs-check, hygiene, and the task-class guard bundle.
3. Hand off one `stage_commit_pipeline` action_request for the combined
   commit, then let the governed remote-control commit/push pipeline publish
   `rev_pkt_1997` plus this Slice C/D repair.
