"""Collaboration-session parsing helpers for runtime review-state payloads."""

from __future__ import annotations

from collections.abc import Mapping

from .control_state import _int, _mapping, _string
from .review_state_collaboration_fields import (
    _arbitration_state_from_mapping,
    _delegated_work_from_value,
    ownership_state_from_mapping,
    _participants_from_value,
    _peer_review_state_from_mapping,
    _ready_gates_from_value,
    _restart_state_from_mapping,
    _role_assignments_from_value,
)
from .review_state_collaboration_legacy import _legacy_collaboration_state
from .review_state_models import (
    AgentRegistryState,
    CollaborationSessionState,
    ReviewBridgeState,
    ReviewCurrentSessionState,
)


def collaboration_state_from_payload(
    *,
    collaboration: Mapping[str, object],
    review: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    bridge: ReviewBridgeState,
    registry: AgentRegistryState,
) -> CollaborationSessionState:
    if collaboration:
        return CollaborationSessionState(
            schema_version=_int(collaboration.get("schema_version")) or 1,
            contract_id=_string(collaboration.get("contract_id")) or "CollaborationSession",
            session_id=_string(collaboration.get("session_id"))
            or _string(review.get("session_id"))
            or "review-channel",
            plan_id=_string(collaboration.get("plan_id")) or _string(review.get("plan_id")),
            status=_string(collaboration.get("status")) or "inactive",
            reviewer_mode=_string(collaboration.get("reviewer_mode"))
            or bridge.effective_reviewer_mode
            or bridge.reviewer_mode,
            operator_mode=_string(collaboration.get("operator_mode")) or "manual",
            lead_agent=_string(collaboration.get("lead_agent")),
            review_agent=_string(collaboration.get("review_agent")),
            coding_agent=_string(collaboration.get("coding_agent")),
            current_slice=_string(collaboration.get("current_slice")),
            peer_review=_peer_review_state_from_mapping(
                _mapping(collaboration.get("peer_review")),
                current_session=current_session,
            ),
            arbitration=_arbitration_state_from_mapping(
                _mapping(collaboration.get("arbitration"))
            ),
            restart=_restart_state_from_mapping(
                _mapping(collaboration.get("restart")),
                bridge=bridge,
            ),
            ready_gates=_ready_gates_from_value(collaboration.get("ready_gates")),
            role_assignments=_role_assignments_from_value(
                collaboration.get("role_assignments")
            ),
            participants=_participants_from_value(collaboration.get("participants")),
            delegated_work=_delegated_work_from_value(
                collaboration.get("delegated_work")
            ),
            topology_mode=_string(collaboration.get("topology_mode")) or "single_agent",
            work_ownership_mode=(
                _string(collaboration.get("work_ownership_mode"))
                or "exclusive_slice"
            ),
            ownership=ownership_state_from_mapping(
                _mapping(collaboration.get("ownership"))
            ),
            mutation_owner=_string(collaboration.get("mutation_owner")),
            verification_owner=_string(collaboration.get("verification_owner")),
            verification_status=(
                _string(collaboration.get("verification_status")) or "inactive"
            ),
            watcher_owner=_string(collaboration.get("watcher_owner")),
            watcher_status=_string(collaboration.get("watcher_status")) or "inactive",
        )
    return _legacy_collaboration_state(
        review=review,
        current_session=current_session,
        bridge=bridge,
        registry=registry,
        string_fn=_string,
    )
