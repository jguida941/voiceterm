"""Collaboration-session parsing helpers for runtime review-state payloads."""

from __future__ import annotations

from collections.abc import Mapping

from .control_state import _int, _mapping, _string
from .review_state_parse_support import _bool
from .collaboration_wake_contract import (
    LoopAutonomyState,
    loop_autonomy_contract,
    wake_continuity_contract,
)
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
        participants = _participants_from_value(collaboration.get("participants"))
        reviewer_mode = (
            _string(collaboration.get("reviewer_mode"))
            or bridge.effective_reviewer_mode
            or bridge.reviewer_mode
        )
        mutation_owner = _string(collaboration.get("mutation_owner"))
        verification_owner = _string(collaboration.get("verification_owner"))
        watcher_owner = _string(collaboration.get("watcher_owner"))
        if participants:
            (
                derived_mutation_wake_mode,
                derived_verification_wake_mode,
                derived_watcher_wake_mode,
                derived_wake_continuity_ok,
                derived_wake_gap_summary,
            ) = wake_continuity_contract(
                reviewer_mode=reviewer_mode,
                mutation_owner=mutation_owner,
                verification_owner=verification_owner,
                watcher_owner=watcher_owner,
                participants=participants,
            )
            derived_loop_autonomy = loop_autonomy_contract(
                reviewer_mode=reviewer_mode,
                mutation_owner=mutation_owner,
                verification_owner=verification_owner,
                watcher_owner=watcher_owner,
                participants=participants,
            )
        else:
            derived_mutation_wake_mode = "unknown"
            derived_verification_wake_mode = "unknown"
            derived_watcher_wake_mode = "unknown"
            derived_wake_continuity_ok = True
            derived_wake_gap_summary = ""
            derived_loop_autonomy = LoopAutonomyState()
        return CollaborationSessionState(
            schema_version=_int(collaboration.get("schema_version")) or 1,
            contract_id=_string(collaboration.get("contract_id")) or "CollaborationSession",
            session_id=_string(collaboration.get("session_id"))
            or _string(review.get("session_id"))
            or "review-channel",
            plan_id=_string(collaboration.get("plan_id")) or _string(review.get("plan_id")),
            status=_string(collaboration.get("status")) or "inactive",
            reviewer_mode=reviewer_mode,
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
            participants=participants,
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
            mutation_owner=mutation_owner,
            verification_owner=verification_owner,
            verification_status=(
                _string(collaboration.get("verification_status")) or "inactive"
            ),
            watcher_owner=watcher_owner,
            watcher_status=_string(collaboration.get("watcher_status")) or "inactive",
            mutation_wake_mode=(
                _string(collaboration.get("mutation_wake_mode"))
                or derived_mutation_wake_mode
            ),
            verification_wake_mode=(
                _string(collaboration.get("verification_wake_mode"))
                or derived_verification_wake_mode
            ),
            watcher_wake_mode=(
                _string(collaboration.get("watcher_wake_mode"))
                or derived_watcher_wake_mode
            ),
            wake_continuity_ok=(
                _bool(collaboration.get("wake_continuity_ok"))
                if "wake_continuity_ok" in collaboration
                else derived_wake_continuity_ok
            ),
            wake_gap_summary=(
                _string(collaboration.get("wake_gap_summary"))
                or derived_wake_gap_summary
            ),
            loop_wake_mode=(
                _string(collaboration.get("loop_wake_mode"))
                or derived_loop_autonomy.loop_wake_mode
            ),
            loop_wake_interval_seconds=(
                _int(collaboration.get("loop_wake_interval_seconds"))
                if "loop_wake_interval_seconds" in collaboration
                else derived_loop_autonomy.loop_wake_interval_seconds
            ),
            loop_driver_agent=(
                _string(collaboration.get("loop_driver_agent"))
                or derived_loop_autonomy.loop_driver_agent
            ),
            loop_autonomy_ok=(
                _bool(collaboration.get("loop_autonomy_ok"))
                if "loop_autonomy_ok" in collaboration
                else derived_loop_autonomy.loop_autonomy_ok
            ),
            loop_gap_summary=(
                _string(collaboration.get("loop_gap_summary"))
                or derived_loop_autonomy.loop_gap_summary
            ),
        )
    return _legacy_collaboration_state(
        review=review,
        current_session=current_session,
        bridge=bridge,
        registry=registry,
        string_fn=_string,
    )
