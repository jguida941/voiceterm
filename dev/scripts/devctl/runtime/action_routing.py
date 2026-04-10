"""Typed action-routing decisions for startup and mutation boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field

from .action_routing_coordination import (
    active_implementation_owner,
    coordination_state,
)
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
class LaneEditGateDecision:
    """Hard pre-edit gate for the active implementation lane."""

    schema_version: int = 1
    contract_id: str = "LaneEditGate"
    status: str = "implementation_allowed"
    edit_allowed: bool = True
    active_implementation_owner: str = ""
    allowed_outputs: tuple[str, ...] = ("implementation_patch",)
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["allowed_outputs"] = list(self.allowed_outputs)
        return payload


@dataclass(frozen=True, slots=True)
class AgentLaneDecision:
    """Current agent lane and hard permissions for this control tick."""

    schema_version: int = 1
    contract_id: str = "AgentLane"
    lane: str = "implementer"
    permissions: tuple[str, ...] = ()
    blocked_permissions: tuple[str, ...] = ()
    source: str = "startup-context"
    edit_gate: LaneEditGateDecision = field(default_factory=LaneEditGateDecision)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["permissions"] = list(self.permissions)
        payload["blocked_permissions"] = list(self.blocked_permissions)
        payload["edit_gate"] = self.edit_gate.to_dict()
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
    active_implementation_owner: object = "",
) -> AgentLaneDecision:
    """Return lane permissions from typed caller role, not chat prose."""
    lane = normalize_agent_lane(caller_role)
    owner = str(active_implementation_owner or "").strip()
    if lane in {"dashboard", "observer"}:
        return AgentLaneDecision(
            lane=lane,
            permissions=(*_READ_ACTIONS, *_FINDING_ACTIONS),
            blocked_permissions=_MUTATING_ACTIONS,
            edit_gate=LaneEditGateDecision(
                status="findings_only",
                edit_allowed=False,
                active_implementation_owner=owner,
                allowed_outputs=("finding_packet", "action_request_packet"),
                reason=(
                    "active_implementation_lane_owned_by_other_agent"
                    if owner
                    else "observer_dashboard_lane_read_only"
                ),
            ),
        )
    if lane == "reviewer" and not reviewer_override:
        return AgentLaneDecision(
            lane=lane,
            permissions=(*_READ_ACTIONS, *_FINDING_ACTIONS, "review.checkpoint"),
            blocked_permissions=_IMPLEMENTATION_ACTIONS,
            edit_gate=LaneEditGateDecision(
                status="review_findings_only",
                edit_allowed=False,
                active_implementation_owner=owner,
                allowed_outputs=("finding_packet", "review_checkpoint"),
                reason="reviewer_lane_requires_override_for_implementation",
            ),
        )
    return AgentLaneDecision(
        lane=lane,
        permissions=(*_READ_ACTIONS, *_FINDING_ACTIONS, *_IMPLEMENTATION_ACTIONS),
        blocked_permissions=(),
        edit_gate=LaneEditGateDecision(
            active_implementation_owner=owner,
        ),
    )


def build_startup_action_routing(
    ctx_payload: Mapping[str, object],
    *,
    next_command: str,
    caller_role: object = "",
    reviewer_override: bool = False,
) -> ActionRoutingDecision:
    """Build the startup control decision consumed by hooks and agents."""
    resolved_coordination = coordination_state(ctx_payload)
    lane = build_agent_lane_decision(
        caller_role=caller_role,
        reviewer_override=reviewer_override,
        active_implementation_owner=active_implementation_owner(
            resolved_coordination,
            ctx_payload,
        ),
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

    if resolved_coordination is not None and resolved_coordination.resync_required:
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
    payload["control_recovery_action"] = decision.recovery_action
    payload.setdefault("recovery_action", decision.recovery_action)
    payload["escalation_action"] = decision.escalation_action
    payload["agent_lane"] = decision.agent_lane.to_dict()
    payload["lane_edit_gate"] = decision.agent_lane.edit_gate.to_dict()
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
    "LaneEditGateDecision",
    "build_agent_lane_decision",
    "build_commit_permission_decision",
    "build_commit_permission_decision_for_executor",
    "build_startup_action_routing",
    "normalize_agent_lane",
    "project_startup_action_routing",
]
