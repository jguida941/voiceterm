"""Helper reductions for coordination/topology snapshot construction."""

from __future__ import annotations

from ..runtime.review_state_models import ReviewState
from ..runtime.role_topology import LiveRoleTopology, RoleOccupancy, resolve_role_topology
from ..runtime.work_intake_models import (
    WorkIntakeCoordinationState,
    WorkIntakeOwnershipState,
)
from .coordination_topology_models import (
    CoordinationParticipantRecord,
    CoordinationReadyGateRecord,
    DelegatedWorktreeRecord,
)

_REVIEW_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json"
)
_PUSH_EXECUTE_COMMAND = "python3 dev/scripts/devctl.py push --execute"


def runtime_provider_roles(review_state: ReviewState | None) -> dict[str, str]:
    """Return live provider roles from typed role topology."""
    topology = runtime_role_topology(review_state)
    active: dict[str, str] = {}
    for role, providers in topology.live_role_providers:
        for provider in providers:
            active[provider] = role
    return active


def runtime_role_topology(review_state: ReviewState | None) -> LiveRoleTopology:
    """Resolve the generic typed role occupancy model from review state."""
    if review_state is None:
        return resolve_role_topology({})
    return resolve_role_topology(
        {
            "active_conductor_providers": getattr(
                review_state.bridge,
                "active_conductor_providers",
                (),
            ),
            "session_liveness_signals": review_state.bridge.session_liveness_signals,
            "codex_conductor_active": review_state.bridge.codex_conductor_active,
            "claude_conductor_active": review_state.bridge.claude_conductor_active,
            "collaboration": {
                "actor_authorities": tuple(
                    _actor_authority_payload(row)
                    for row in review_state.collaboration.actor_authorities
                ),
                "participants": tuple(
                    {
                        "provider": row.provider,
                        "role": row.role,
                        "live": row.live,
                    }
                    for row in review_state.collaboration.participants
                ),
                "role_assignments": tuple(
                    {
                        "provider": row.provider,
                        "role_id": row.role_id,
                        "live": row.live,
                    }
                    for row in review_state.collaboration.role_assignments
                ),
            },
        },
        include_runtime_presence=True,
    )


def participant_records(
    *,
    review_state: ReviewState | None,
    active_provider_roles: dict[str, str],
    active_provider_ids: tuple[str, ...] = (),
    role_occupancies: tuple[RoleOccupancy, ...] = (),
) -> tuple[CoordinationParticipantRecord, ...]:
    """Build participant rows from collaboration plus bridge runtime fallback."""
    if review_state is None:
        return ()

    current_session = review_state.current_session
    rows: list[CoordinationParticipantRecord] = []
    seen_keys: set[tuple[str, str]] = set()
    live_occupancy_providers = {
        occupancy.provider for occupancy in role_occupancies if occupancy.live
    }
    for participant in review_state.collaboration.participants:
        key = (
            (participant.agent_id or participant.provider).strip(),
            participant.role.strip(),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        bridge_live = (
            participant.provider in active_provider_roles
            or participant.provider in active_provider_ids
            or participant.provider in live_occupancy_providers
        )
        rows.append(
            CoordinationParticipantRecord(
                agent_id=participant.agent_id or participant.provider,
                provider=participant.provider,
                role=participant.role,
                session_name=participant.session_name,
                live=bool(participant.live or bridge_live),
                live_source=live_source(
                    collaboration_live=participant.live,
                    bridge_live=bridge_live,
                ),
                status=participant.status,
                requested_worker_budget=max(participant.requested_worker_budget or 0, 0),
                planned_lane_count=max(participant.planned_lane_count, 0),
                session_state=session_state(
                    current_session=current_session,
                    role=participant.role,
                ),
                session_hint=session_hint(
                    current_session=current_session,
                    role=participant.role,
                ),
            )
        )

    for occupancy in role_occupancies:
        if not occupancy.live:
            continue
        actor_id = occupancy.actor_id or occupancy.provider
        key = (actor_id, occupancy.role_id)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        rows.append(
            CoordinationParticipantRecord(
                agent_id=actor_id,
                provider=occupancy.provider,
                role=occupancy.role_id,
                session_name=occupancy.session_id
                or runtime_session_name(review_state, provider=occupancy.provider),
                live=True,
                live_source="typed_role_topology",
                status="runtime_observed",
                session_state=session_state(
                    current_session=current_session,
                    role=occupancy.role_id,
                ),
                session_hint=session_hint(
                    current_session=current_session,
                    role=occupancy.role_id,
                ),
            )
        )

    for provider, role in active_provider_roles.items():
        key = (provider, role)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        rows.append(
            CoordinationParticipantRecord(
                agent_id=provider,
                provider=provider,
                role=role,
                session_name=runtime_session_name(review_state, provider=provider),
                live=True,
                live_source="bridge_runtime",
                status="runtime_observed",
                session_state=session_state(
                    current_session=current_session,
                    role=role,
                ),
                session_hint=session_hint(
                    current_session=current_session,
                    role=role,
                ),
            )
        )
    rows.sort(key=lambda row: (not row.live, row.role, row.agent_id))
    return tuple(rows)


def delegated_worktree_records(
    *,
    review_state: ReviewState | None,
    duplicate_worktrees: tuple[str, ...],
) -> tuple[DelegatedWorktreeRecord, ...]:
    """Build delegated worker/worktree rows from collaboration receipts."""
    if review_state is None:
        return ()
    duplicates = set(duplicate_worktrees)
    rows = [
        DelegatedWorktreeRecord(
            receipt_id=receipt.receipt_id,
            agent_id=receipt.agent_id,
            provider=receipt.provider,
            role=receipt.role,
            owner_session=receipt.owner_session,
            lane=receipt.lane,
            worktree=receipt.worktree,
            branch=receipt.branch,
            live=receipt.live,
            status=receipt.status,
            duplicate_worktree=receipt.worktree in duplicates if receipt.worktree else False,
        )
        for receipt in review_state.collaboration.delegated_work
    ]
    rows.sort(key=lambda row: (not row.live, row.worktree, row.agent_id))
    return tuple(rows)


def ready_gate_records(
    review_state: ReviewState | None,
) -> tuple[CoordinationReadyGateRecord, ...]:
    """Project ready-gate rows from collaboration state."""
    if review_state is None:
        return ()
    return tuple(
        CoordinationReadyGateRecord(
            gate_id=gate.gate_id,
            status=gate.status,
            summary=gate.summary,
        )
        for gate in review_state.collaboration.ready_gates
    )


def fanout_posture(
    *,
    review_state: ReviewState | None,
    coordination: WorkIntakeCoordinationState,
    ownership: WorkIntakeOwnershipState,
    ready_gates: tuple[CoordinationReadyGateRecord, ...],
    participants: tuple[CoordinationParticipantRecord, ...],
    delegated_worktrees: tuple[DelegatedWorktreeRecord, ...],
) -> tuple[str, bool, str]:
    """Reduce bounded participant/worktree state into a fanout decision."""
    requested_budget_total = sum(
        max(row.requested_worker_budget, 0) for row in participants
    )
    delegated_live = any(row.live for row in delegated_worktrees)
    fanout_requested = requested_budget_total > 0 or delegated_live
    if (
        coordination.work_ownership_mode == "concurrent_writer_conflict"
        or ownership.concurrent_writer_detected
        or coordination.duplicate_delegated_worktrees
    ):
        return "blocked_conflict", False, "role_authority_conflict"
    if runtime_blocks_fanout(
        review_state=review_state,
        ready_gates=ready_gates,
        fanout_requested=fanout_requested,
    ):
        return "blocked_resync", False, "role_authority_resync_required"
    if not fanout_requested:
        return "conductor_only", False, "typed_role_topology_conductor_only"
    return "fanout_ready", True, (
        coordination.collaboration_topology or "typed_role_topology_fanout_ready"
    )


def _actor_authority_payload(row) -> dict[str, object]:
    return {
        "actor_id": row.actor_id,
        "provider": row.provider,
        "role": row.role,
        "live": row.live,
        "grants": tuple(
            {
                "capability": grant.capability,
                "granted": grant.granted,
            }
            for grant in row.grants
        ),
    }


def runtime_blocks_fanout(
    *,
    review_state: ReviewState | None,
    ready_gates: tuple[CoordinationReadyGateRecord, ...],
    fanout_requested: bool,
) -> bool:
    """Return whether runtime truth blocks widening into fanout."""
    if review_state is None:
        return fanout_requested
    current_attention = attention_status(review_state)
    if current_attention in {
        "inactive",
        "repair_required",
        "review_follow_up_required",
        "checkpoint_required",
    }:
        return True
    if reviewer_freshness(review_state) in {"stale", "overdue"}:
        return True
    blocked_gates = {
        gate.gate_id
        for gate in ready_gates
        if gate.status == "blocked"
    }
    return bool(blocked_gates & {"runtime_truth", "review_truth", "delegated_work"})


def resync_posture(
    *,
    review_state: ReviewState | None,
    coordination: WorkIntakeCoordinationState,
) -> tuple[str, bool, str, str]:
    """Reduce runtime freshness and cadence into one resync posture."""
    if review_state is not None:
        attention = review_state.attention
        if attention is not None and attention.status not in {"healthy", ""}:
            command = (
                recovery_command(review_state)
                or attention.recommended_command
                or _REVIEW_STATUS_COMMAND
            )
            return (
                "runtime_repair",
                True,
                attention.summary or "review runtime is not healthy",
                command,
            )
        if review_state.reviewer_runtime.reviewer_freshness in {"stale", "overdue"}:
            return (
                "runtime_repair",
                True,
                review_state.reviewer_runtime.stale_reason or "reviewer freshness is stale",
                recovery_command(review_state) or _REVIEW_STATUS_COMMAND,
            )
    if coordination.sync_cadence_mode == "before_scope_change":
        return (
            "before_scope_change",
            True,
            "scope or ownership changed; refresh coordination before widening work",
            _REVIEW_STATUS_COMMAND,
        )
    if coordination.sync_cadence_mode == "before_publish":
        return (
            "before_publish",
            True,
            "publication is the next sync boundary for the current slice",
            _PUSH_EXECUTE_COMMAND,
        )
    if coordination.sync_cadence_mode == "checkpointed":
        return (
            "checkpoint_boundary",
            True,
            "checkpoint state is the next coordination boundary",
            _REVIEW_STATUS_COMMAND,
        )
    return "idle", False, "", ""


def topology_summary(
    *,
    active_participant_count: int,
    collaboration_topology: str,
    work_ownership_mode: str,
    fanout_posture: str,
    resync_posture: str,
) -> str:
    """Render the bounded coordination topology summary."""
    return (
        f"{active_participant_count} active participant(s); "
        f"{collaboration_topology}; {work_ownership_mode}; "
        f"fanout={fanout_posture}; resync={resync_posture}"
    )


def live_source(*, collaboration_live: bool, bridge_live: bool) -> str:
    """Explain why a participant row is considered live."""
    if collaboration_live:
        return "collaboration"
    if bridge_live:
        return "bridge_runtime"
    return "planned_only"


def runtime_session_name(review_state: ReviewState, *, provider: str) -> str:
    """Resolve the runtime session name for a provider fallback row."""
    session_owner = review_state.reviewer_runtime.session_owner
    if session_owner.provider == provider:
        return session_owner.session_name
    return f"{provider}-conductor"


def session_state(*, current_session, role: str) -> str:
    """Map a role to its bounded current-session state field."""
    if role == "implementer":
        return current_session.implementer_session_state
    if role == "reviewer":
        return current_session.implementer_ack_state
    return ""


def session_hint(*, current_session, role: str) -> str:
    """Map a role to its bounded current-session hint field."""
    if role == "implementer":
        return current_session.implementer_session_hint
    if role == "reviewer" and current_session.current_instruction_revision:
        return (
            "current instruction revision "
            f"{current_session.current_instruction_revision}"
        )
    return ""


def reviewer_freshness(review_state: ReviewState | None) -> str:
    """Return bounded reviewer freshness with an unknown fallback."""
    if review_state is None:
        return "unknown"
    return review_state.reviewer_runtime.reviewer_freshness or "unknown"


def attention_status(review_state: ReviewState | None) -> str:
    """Return bounded attention status with an inactive fallback."""
    if review_state is None or review_state.attention is None:
        return "inactive"
    return review_state.attention.status or "inactive"


def recovery_command(review_state: ReviewState) -> str:
    """Return the typed recovery command when recovery assessment exists."""
    assessment = review_state.recovery_assessment
    if assessment is None:
        return ""
    return assessment.decision.command
