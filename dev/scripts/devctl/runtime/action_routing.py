"""Typed action-routing decisions for startup and mutation boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field

from .commit_permission import (
    CommitPermissionDecision,
    build_commit_permission_decision,
    build_commit_permission_decision_for_executor,
)

_LANES = frozenset({"dashboard", "implementer", "observer", "reviewer"})
_READ_ACTIONS = (
    "startup-context.summary",
    "review-channel.status",
    "context-graph.bootstrap",
)
_FINDING_ACTIONS = ("review-channel.post_finding",)
_IMPLEMENTATION_ACTIONS = ("implementation.edit", "vcs.stage", "vcs.commit")
_MUTATING_ACTIONS = (
    "implementation.edit",
    "vcs.stage",
    "vcs.commit",
    "vcs.push",
    "runtime.recover",
    "runtime.terminate",
)


@dataclass(frozen=True, slots=True)
class AgentLaneDecision:
    """Current agent lane and hard permissions for this control tick."""

    schema_version: int = 1
    contract_id: str = "AgentLane"
    lane: str = "implementer"
    permissions: tuple[str, ...] = ()
    blocked_permissions: tuple[str, ...] = ()
    source: str = "startup-context"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["permissions"] = list(self.permissions)
        payload["blocked_permissions"] = list(self.blocked_permissions)
        return payload


@dataclass(frozen=True, slots=True)
class ActionRoutingDecision:
    """Next legal command plus hard allowed/blocked action sets."""

    schema_version: int = 1
    contract_id: str = "ActionRoutingDecision"
    source_command: str = "startup-context"
    next_command: str = ""
    allowed_actions: tuple[str, ...] = ()
    blocked_actions: tuple[str, ...] = ()
    recovery_action: str = ""
    escalation_action: str = ""
    agent_lane: AgentLaneDecision = field(default_factory=AgentLaneDecision)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["allowed_actions"] = list(self.allowed_actions)
        payload["blocked_actions"] = list(self.blocked_actions)
        payload["agent_lane"] = self.agent_lane.to_dict()
        return payload


def normalize_agent_lane(value: object) -> str:
    """Return a closed agent lane value."""
    lane = str(value or "").strip().lower()
    return lane if lane in _LANES else "implementer"


def build_agent_lane_decision(
    *,
    caller_role: object = "",
    reviewer_override: bool = False,
) -> AgentLaneDecision:
    """Return lane permissions from typed caller role, not chat prose."""
    lane = normalize_agent_lane(caller_role)
    if lane in {"dashboard", "observer"}:
        return AgentLaneDecision(
            lane=lane,
            permissions=(*_READ_ACTIONS, *_FINDING_ACTIONS),
            blocked_permissions=_MUTATING_ACTIONS,
        )
    if lane == "reviewer" and not reviewer_override:
        return AgentLaneDecision(
            lane=lane,
            permissions=(*_READ_ACTIONS, *_FINDING_ACTIONS, "review.checkpoint"),
            blocked_permissions=_IMPLEMENTATION_ACTIONS,
        )
    return AgentLaneDecision(
        lane=lane,
        permissions=(*_READ_ACTIONS, *_FINDING_ACTIONS, *_IMPLEMENTATION_ACTIONS),
        blocked_permissions=(),
    )


def build_startup_action_routing(
    ctx_payload: Mapping[str, object],
    *,
    next_command: str,
    caller_role: object = "",
    reviewer_override: bool = False,
) -> ActionRoutingDecision:
    """Build the startup control decision consumed by hooks and agents."""
    lane = build_agent_lane_decision(
        caller_role=caller_role,
        reviewer_override=reviewer_override,
    )
    allowed = list(lane.permissions)
    blocked = list(lane.blocked_permissions)
    recovery_action = ""
    escalation_action = ""

    permission = str(ctx_payload.get("implementation_permission") or "").strip()
    if permission in {"blocked", "suspended"}:
        _append_unique(blocked, _IMPLEMENTATION_ACTIONS)
        _append_unique(allowed, _READ_ACTIONS)
        recovery_action = "refresh_startup_or_review_status"
        escalation_action = "operator_resync_required"

    coordination = _mapping(ctx_payload.get("coordination"))
    if bool(coordination.get("resync_required", False)):
        _append_unique(blocked, ("implementation.edit", "vcs.stage", "vcs.commit"))
        _append_unique(allowed, ("review-channel.status",))
        recovery_action = "coordination_resync"
        escalation_action = "operator_resume_review_loop"

    return ActionRoutingDecision(
        next_command=next_command,
        allowed_actions=tuple(allowed),
        blocked_actions=tuple(blocked),
        recovery_action=recovery_action,
        escalation_action=escalation_action,
        agent_lane=lane,
    )


def project_startup_action_routing(
    payload: dict[str, object],
    *,
    next_command: str,
    caller_role: object = "",
    reviewer_override: bool = False,
) -> ActionRoutingDecision:
    """Add the action-routing projection to an existing startup payload."""
    decision = build_startup_action_routing(
        payload,
        next_command=next_command,
        caller_role=caller_role,
        reviewer_override=reviewer_override,
    )
    payload["next_command"] = decision.next_command
    payload["allowed_actions"] = list(decision.allowed_actions)
    payload["blocked_actions"] = list(decision.blocked_actions)
    payload["recovery_action"] = decision.recovery_action
    payload["escalation_action"] = decision.escalation_action
    payload["agent_lane"] = decision.agent_lane.to_dict()
    payload["action_routing"] = decision.to_dict()
    return decision


def _append_unique(target: list[str], values: tuple[str, ...]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


__all__ = [
    "ActionRoutingDecision",
    "AgentLaneDecision",
    "CommitPermissionDecision",
    "build_agent_lane_decision",
    "build_commit_permission_decision",
    "build_commit_permission_decision_for_executor",
    "build_startup_action_routing",
    "normalize_agent_lane",
    "project_startup_action_routing",
]
