"""Registry projection helpers for typed collaboration-session state."""

from __future__ import annotations

from .registry_context import AgentRegistryContext
from ..runtime.review_state_models import (
    AgentRegistryEntryState,
    AgentRegistryState,
    CollaborationParticipantState,
    CollaborationRoleAssignmentState,
    CollaborationSessionState,
)
from ..runtime.role_profile import normalize_role_id, role_capability_classes


def build_runtime_agent_registry_from_collaboration(
    *,
    collaboration: CollaborationSessionState,
    context: AgentRegistryContext,
) -> AgentRegistryState:
    participants = {
        participant.agent_id: participant for participant in collaboration.participants
    }
    agents: list[AgentRegistryEntryState] = []
    seen_agent_ids: set[str] = set()
    for assignment in collaboration.role_assignments:
        agent_id = assignment.agent_id or assignment.provider
        if agent_id in seen_agent_ids:
            continue
        seen_agent_ids.add(agent_id)
        participant = participants.get(agent_id)
        role = _assignment_role(assignment)
        agents.append(
            AgentRegistryEntryState(
                agent_id=agent_id,
                provider=assignment.provider or agent_id,
                display_name=assignment.display_name or agent_id,
                lane=assignment.provider or agent_id,
                lane_title=_default_lane_title(role),
                current_job=role,
                job_state=_job_state_from_collaboration(
                    role=role,
                    participant=participant,
                    collaboration=collaboration,
                ),
                waiting_on=_waiting_on_from_collaboration(
                    role=role,
                    collaboration=collaboration,
                ),
                last_packet_seen="",
                last_packet_applied="",
                script_profile=_script_profile(
                    participant=participant,
                    role=role,
                ),
                mp_scope=context.plan_id,
                worktree="",
                branch="",
                updated_at=context.timestamp,
            )
        )
    for receipt in collaboration.delegated_work:
        if not receipt.live or receipt.agent_id in seen_agent_ids:
            continue
        seen_agent_ids.add(receipt.agent_id)
        agents.append(
            AgentRegistryEntryState(
                agent_id=receipt.agent_id,
                provider=receipt.provider,
                display_name=receipt.agent_id,
                lane=receipt.agent_id,
                lane_title=receipt.lane or "Delegated Worker",
                current_job=receipt.role,
                job_state=receipt.status,
                waiting_on="",
                last_packet_seen="",
                last_packet_applied="",
                script_profile="delegated-worker",
                mp_scope=receipt.mp_scope or context.plan_id,
                worktree=receipt.worktree,
                branch=receipt.branch,
                updated_at=context.timestamp,
            )
        )
    return AgentRegistryState(
        timestamp=context.timestamp,
        agents=tuple(agents),
        snapshot_id=context.snapshot_id,
        zref=context.zref,
        source_identity=context.source_identity_dict(),
        source_contract=context.source_contract,
        source_command=context.source_command,
        observed_fields=context.observed_fields,
        inferred_fields=context.inferred_fields,
    )


def _assignment_role(assignment: CollaborationRoleAssignmentState) -> str:
    role_id = normalize_role_id(assignment.role_id)
    return {
        "lead_agent": "orchestrator",
        "review_agent": "architecture_review",
        "coding_agent": "implementation",
        "operator_agent": "operator",
    }.get(role_id, role_id)


def _job_state_from_collaboration(
    *,
    role: str,
    participant: CollaborationParticipantState | None,
    collaboration: CollaborationSessionState,
) -> str:
    capability_classes = set(role_capability_classes(role))
    if capability_classes & {"review", "test", "architecture", "governance", "research", "intake"}:
        if collaboration.reviewer_mode != "active_dual_agent" and participant is None:
            return "inactive"
        if _ready_gate_status(collaboration, "review_truth") == "blocked":
            return "review_needed"
        return "reviewing" if participant is None or participant.live else "inactive"
    if capability_classes & {"implementation", "mutation"}:
        implementer_status = collaboration.peer_review.implementer_status.strip()
        if implementer_status in {"", "(missing)"}:
            return "waiting" if collaboration.peer_review.current_instruction else "inactive"
        if collaboration.peer_review.implementer_ack_state == "current":
            return "implementing"
        if collaboration.peer_review.current_instruction:
            return "waiting_for_ack"
        return "inactive"
    if capability_classes & {"control", "observe"}:
        if collaboration.arbitration.status == "operator_attention":
            return "waiting"
        return "idle"
    return _default_job_state(role)


def _waiting_on_from_collaboration(
    *,
    role: str,
    collaboration: CollaborationSessionState,
) -> str:
    capability_classes = set(role_capability_classes(role))
    if capability_classes & {"review", "test", "architecture", "governance", "research", "intake"}:
        return "worktree" if _ready_gate_status(collaboration, "review_truth") == "blocked" else ""
    if capability_classes & {"implementation", "mutation"}:
        if _ready_gate_status(collaboration, "review_truth") == "blocked":
            return "reviewer"
        return ""
    if capability_classes & {"control", "observe"}:
        return "review" if collaboration.arbitration.status == "operator_attention" else ""
    return ""


def _ready_gate_status(
    collaboration: CollaborationSessionState,
    gate_id: str,
) -> str:
    for gate in collaboration.ready_gates:
        if gate.gate_id == gate_id:
            return gate.status
    return ""


def _default_lane_title(role: str) -> str:
    return normalize_role_id(role).replace("_", " ").title()


def _default_job_state(role: str) -> str:
    if set(role_capability_classes(role)) & {"control", "observe"}:
        return "idle"
    return "inactive"


def _default_script_profile(role: str) -> str:
    if set(role_capability_classes(role)) & {"control", "observe"}:
        return ""
    return "markdown-bridge-conductor"


def _script_profile(
    *,
    participant: CollaborationParticipantState | None,
    role: str,
) -> str:
    if participant is None:
        return _default_script_profile(role)
    if participant.capture_mode == "remote-control":
        return "remote-control"
    return "markdown-bridge-conductor"
