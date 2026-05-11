"""Typed operator override for scoped agent-loop edits."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .development_core_workstreams import BUILDER_WORKSTREAM
from .value_coercion import coerce_bool, coerce_text

_READ_ACTIONS = (
    "startup-context.summary",
    "review-channel.status",
    "review-channel.post_finding",
)
_EDIT_ACTIONS = ("implementation.edit",)
_BLOCKED_AFTER_EDIT_OVERRIDE = ("vcs.stage", "vcs.commit", "vcs.push")
DEFAULT_OPERATOR_OVERRIDE_REASON = "operator requested scoped edit-only repair"
EDIT_ONLY_OVERRIDE_SCOPE = "edit-only"
OPERATOR_OVERRIDE_REQUESTOR = "operator"
OPERATOR_OVERRIDE_SOURCE = "agent_loop_cli"
EDIT_ONLY_EFFECTIVE_ROLE = BUILDER_WORKSTREAM.runtime_role
EDIT_ONLY_EFFECTIVE_WORKSTREAM = BUILDER_WORKSTREAM.workstream_id
EDIT_ONLY_AUTHORITY_SOURCE = "operator_override_edit_only_repair"


@dataclass(frozen=True, slots=True)
class AgentLoopOperatorOverride:
    """Operator-scoped exception that can allow edits without publication."""

    schema_version: int = 1
    contract_id: str = "AgentLoopOperatorOverride"
    requested: bool = False
    active: bool = False
    state: str = "not_requested"
    source: str = ""
    requested_by: str = ""
    scope: str = ""
    reason: str = ""
    target_kind: str = ""
    target_ref: str = ""
    effective_actor_role: str = ""
    effective_workstream_id: str = ""
    effective_authority_source: str = ""
    allowed_actions: tuple[str, ...] = ()
    blocked_actions: tuple[str, ...] = ()
    expires_after_turn: bool = True
    requires_guard_replay: bool = True

    @property
    def edit_allowed(self) -> bool:
        return (
            self.requested
            and self.active
            and self.state == "active"
            and self.source == OPERATOR_OVERRIDE_SOURCE
            and self.requested_by == OPERATOR_OVERRIDE_REQUESTOR
            and self.scope == EDIT_ONLY_OVERRIDE_SCOPE
            and bool(self.reason)
            and bool(self.target_kind)
            and bool(self.target_ref)
            and "implementation.edit" in self.allowed_actions
            and self.effective_actor_role == EDIT_ONLY_EFFECTIVE_ROLE
            and self.effective_workstream_id == EDIT_ONLY_EFFECTIVE_WORKSTREAM
            and self.effective_authority_source == EDIT_ONLY_AUTHORITY_SOURCE
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["allowed_actions"] = list(self.allowed_actions)
        payload["blocked_actions"] = list(self.blocked_actions)
        return payload


def operator_override_from_request(
    *,
    requested: object = False,
    reason: object = "",
    scope: object = EDIT_ONLY_OVERRIDE_SCOPE,
    requested_by: object = OPERATOR_OVERRIDE_REQUESTOR,
    requested_plan_ref: object = "",
    requested_packet_id: object = "",
) -> AgentLoopOperatorOverride:
    """Build a typed, edit-only override from explicit loop input."""
    if not coerce_bool(requested):
        return AgentLoopOperatorOverride()
    normalized_scope = (
        coerce_text(scope).lower().replace("_", "-") or EDIT_ONLY_OVERRIDE_SCOPE
    )
    target_kind, target_ref = _target(
        requested_plan_ref=requested_plan_ref,
        requested_packet_id=requested_packet_id,
    )
    if normalized_scope != EDIT_ONLY_OVERRIDE_SCOPE:
        return _invalid(
            "unsupported_scope",
            scope=normalized_scope,
            reason=reason,
            requested_by=requested_by,
            target_kind=target_kind,
            target_ref=target_ref,
        )
    if not coerce_text(reason):
        return _invalid(
            "reason_required",
            scope=normalized_scope,
            reason=reason,
            requested_by=requested_by,
            target_kind=target_kind,
            target_ref=target_ref,
        )
    if not target_ref:
        return _invalid(
            "target_required",
            scope=normalized_scope,
            reason=reason,
            requested_by=requested_by,
            target_kind=target_kind,
            target_ref=target_ref,
        )
    return AgentLoopOperatorOverride(
        requested=True,
        active=True,
        state="active",
        source=OPERATOR_OVERRIDE_SOURCE,
        requested_by=coerce_text(requested_by) or OPERATOR_OVERRIDE_REQUESTOR,
        scope=normalized_scope,
        reason=coerce_text(reason),
        target_kind=target_kind,
        target_ref=target_ref,
        effective_actor_role=EDIT_ONLY_EFFECTIVE_ROLE,
        effective_workstream_id=EDIT_ONLY_EFFECTIVE_WORKSTREAM,
        effective_authority_source=EDIT_ONLY_AUTHORITY_SOURCE,
        allowed_actions=(*_READ_ACTIONS, *_EDIT_ACTIONS),
        blocked_actions=_BLOCKED_AFTER_EDIT_OVERRIDE,
    )


def apply_operator_override_actions(
    *,
    allowed_actions: tuple[str, ...],
    blocked_actions: tuple[str, ...],
    operator_override: AgentLoopOperatorOverride,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return effective action sets after a valid edit-only override."""
    if not operator_override.edit_allowed:
        return allowed_actions, blocked_actions
    allowed = [*allowed_actions]
    for action in operator_override.allowed_actions:
        if action not in allowed:
            allowed.append(action)
    blocked = [
        action
        for action in blocked_actions
        if action not in operator_override.allowed_actions
    ]
    for action in operator_override.blocked_actions:
        if action not in blocked:
            blocked.append(action)
    return tuple(allowed), tuple(blocked)


def operator_override_next_command(
    operator_override: AgentLoopOperatorOverride,
) -> str:
    if not operator_override.edit_allowed:
        return ""
    target = f"{operator_override.target_kind} {operator_override.target_ref}".strip()
    return (
        "operator override active: continue scoped implementation edits"
        + (f" for {target}" if target else "")
        + "; do not stage, commit, or push until startup/checkpoint guards pass"
    )


def _target(*, requested_plan_ref: object, requested_packet_id: object) -> tuple[str, str]:
    packet_id = coerce_text(requested_packet_id)
    if packet_id:
        return "packet", packet_id
    plan_ref = coerce_text(requested_plan_ref)
    if plan_ref:
        return "plan", plan_ref
    return "", ""


def _invalid(
    state: str,
    *,
    scope: str,
    reason: object,
    requested_by: object,
    target_kind: str,
    target_ref: str,
) -> AgentLoopOperatorOverride:
    return AgentLoopOperatorOverride(
        requested=True,
        active=False,
        state=state,
        source=OPERATOR_OVERRIDE_SOURCE,
        requested_by=coerce_text(requested_by) or OPERATOR_OVERRIDE_REQUESTOR,
        scope=scope,
        reason=coerce_text(reason),
        target_kind=target_kind,
        target_ref=target_ref,
    )


__all__ = [
    "AgentLoopOperatorOverride",
    "DEFAULT_OPERATOR_OVERRIDE_REASON",
    "EDIT_ONLY_OVERRIDE_SCOPE",
    "EDIT_ONLY_AUTHORITY_SOURCE",
    "EDIT_ONLY_EFFECTIVE_ROLE",
    "EDIT_ONLY_EFFECTIVE_WORKSTREAM",
    "OPERATOR_OVERRIDE_REQUESTOR",
    "OPERATOR_OVERRIDE_SOURCE",
    "apply_operator_override_actions",
    "operator_override_from_request",
    "operator_override_next_command",
]
