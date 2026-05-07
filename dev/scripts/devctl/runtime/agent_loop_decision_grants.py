"""Authority and capability readers for AgentLoopDecision."""

from __future__ import annotations

from collections.abc import Mapping

from .review_state_collaboration_models import (
    granted_capabilities_from_row,
)
from .agent_loop_decision_capabilities import (
    may_actor_mutate,
    reconcile_actions_with_capability_grants,
)
from .agent_loop_decision_remote_control import remote_control_checkpoint_capabilities
from .agent_loop_decision_rows import (
    actor_row_matches,
    authority_rows,
    posture_actor_rows,
    row_role_matches_requested_role,
)
from .agent_loop_decision_scoped import (
    scoped_session_mutation_mode_allows,
    scoped_work_board_capabilities,
)
from .agent_loop_decision_values import string_tuple
from .value_coercion import coerce_bool, coerce_mapping as _mapping, coerce_text as _text


def authority_snapshot(
    *, review_state: Mapping[str, object], dashboard: Mapping[str, object],
) -> Mapping[str, object]:
    return (
        _mapping(review_state.get("authority_snapshot"))
        or _mapping(dashboard.get("authority_snapshot"))
        or _action_routing(review_state)
        or _action_routing(dashboard)
    )


def action_routing_decision(
    *, review_state: Mapping[str, object], dashboard: Mapping[str, object],
) -> Mapping[str, object]:
    return _action_routing(review_state) or _action_routing(dashboard)


def granted_capabilities_for_actor(
    *,
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
    actor: str,
    role: str = "",
    session: str = "",
) -> tuple[str, ...]:
    capabilities: list[str] = []
    scoped_capabilities = scoped_work_board_capabilities(
        review_state=review_state,
        dashboard=dashboard,
        actor=actor,
        role=role,
        session=session,
    )
    if scoped_capabilities is not None:
        capabilities.extend(scoped_capabilities)

    role_scoped = scoped_capabilities is not None
    rows = (*authority_rows(review_state, dashboard), *posture_actor_rows(review_state, dashboard))
    for row in rows:
        if not actor_row_matches(row, actor):
            continue
        if not row_role_matches_requested_role(
            row,
            role=role,
            require_explicit_role=role_scoped,
        ):
            continue
        values = (
            *granted_capabilities_from_row(row),
            *string_tuple(row.get("granted_capabilities")),
        )
        for capability in values:
            if capability not in capabilities:
                capabilities.append(capability)
    for capability in remote_control_checkpoint_capabilities(
        review_state=review_state,
        dashboard=dashboard,
        actor=actor,
        role=role,
    ):
        if capability not in capabilities:
            capabilities.append(capability)
    return tuple(capabilities)


def merged_actions(*sources: Mapping[str, object], key: str) -> tuple[str, ...]:
    actions: list[str] = []
    for source in sources:
        for action in string_tuple(source.get(key)):
            if action not in actions:
                actions.append(action)
    return tuple(actions)


def lane_edit_allowed(
    *, review_state: Mapping[str, object], dashboard: Mapping[str, object],
) -> bool:
    gate = (
        _mapping(review_state.get("lane_edit_gate"))
        or _mapping(dashboard.get("lane_edit_gate"))
        or _mapping(_action_routing(review_state).get("agent_lane")).get("edit_gate")
        or _mapping(_action_routing(dashboard).get("agent_lane")).get("edit_gate")
    )
    gate_map = _mapping(gate)
    if not gate_map:
        return True
    return coerce_bool(gate_map.get("edit_allowed"))


def _action_routing(source: Mapping[str, object]) -> Mapping[str, object]:
    control_plane = _mapping(source.get("control_plane"))
    return _mapping(source.get("action_routing")) or _mapping(
        control_plane.get("action_routing")
    )


__all__ = [
    "action_routing_decision",
    "authority_snapshot",
    "granted_capabilities_for_actor",
    "lane_edit_allowed",
    "may_actor_mutate",
    "merged_actions",
    "reconcile_actions_with_capability_grants",
    "remote_control_checkpoint_capabilities",
    "scoped_session_mutation_mode_allows",
    "string_tuple",
]
