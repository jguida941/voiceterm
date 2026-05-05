"""Typed operator-interaction mode authority for governance pipeline decisions.

OperatorInteractionMode captures how the human operator connects to the
system (local keyboard, remote phone, dual-agent bridge, or single-AI auto).
ReviewerMode remains the review-loop posture axis; this module owns the
operator-channel axis and the small decision matrix that tells launch,
approval, recovery, and dashboard reducers which local prompts, headless
handoffs, and self-approval paths are valid for each mode. Runtime facts such
as RemoteControlAttachmentState can resolve the channel, but they do not
replace this mode policy.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, NamedTuple

from .enum_compat import StrEnum
from .value_coercion import (
    coerce_mapping as _mapping,
    coerce_string as _string,
    coerce_string,
)

if TYPE_CHECKING:
    from .project_governance_contract import ProjectGovernance


class OperatorInteractionMode(StrEnum):
    """How the human operator interacts with the governance pipeline."""

    LOCAL_TERMINAL = "local_terminal"      # human at keyboard, Terminal prompts OK
    REMOTE_CONTROL = "remote_control"      # operator on phone, route to bridge/dashboard
    DUAL_AGENT = "dual_agent"              # Codex reviews + Claude codes, bridge coordination
    SINGLE_AGENT = "single_agent"          # one AI, full auto
    UNRESOLVED = "unresolved"              # mode not yet determined — fail closed


class OperatorModePolicy(NamedTuple):
    """One explicit decision row for an operator interaction mode."""

    mode: str
    local_prompts_allowed: bool
    headless_required: bool
    remote_handoff_allowed: bool
    commit_self_approval: bool
    collaboration_topology: str
    mutation_policy: str


_MODE_POLICY_BY_MODE: Mapping[str, OperatorModePolicy] = {
    OperatorInteractionMode.LOCAL_TERMINAL.value: OperatorModePolicy(
        mode=OperatorInteractionMode.LOCAL_TERMINAL.value,
        local_prompts_allowed=True,
        headless_required=False,
        remote_handoff_allowed=False,
        commit_self_approval=True,
        collaboration_topology="local_operator",
        mutation_policy="local_operator_approval",
    ),
    OperatorInteractionMode.REMOTE_CONTROL.value: OperatorModePolicy(
        mode=OperatorInteractionMode.REMOTE_CONTROL.value,
        local_prompts_allowed=False,
        headless_required=True,
        remote_handoff_allowed=True,
        commit_self_approval=False,
        collaboration_topology="remote_operator",
        mutation_policy="remote_operator_delegate_required",
    ),
    OperatorInteractionMode.DUAL_AGENT.value: OperatorModePolicy(
        mode=OperatorInteractionMode.DUAL_AGENT.value,
        local_prompts_allowed=False,
        headless_required=True,
        remote_handoff_allowed=True,
        commit_self_approval=False,
        collaboration_topology="reviewer_and_implementer",
        mutation_policy="typed_capability_grant_required",
    ),
    OperatorInteractionMode.SINGLE_AGENT.value: OperatorModePolicy(
        mode=OperatorInteractionMode.SINGLE_AGENT.value,
        local_prompts_allowed=True,
        headless_required=False,
        remote_handoff_allowed=False,
        commit_self_approval=True,
        collaboration_topology="single_actor",
        mutation_policy="single_actor_self_approval",
    ),
    OperatorInteractionMode.UNRESOLVED.value: OperatorModePolicy(
        mode=OperatorInteractionMode.UNRESOLVED.value,
        local_prompts_allowed=False,
        headless_required=True,
        remote_handoff_allowed=False,
        commit_self_approval=False,
        collaboration_topology="unknown",
        mutation_policy="fail_closed",
    ),
}


# Modes that represent a resolved operator state (safe to act on).
RESOLVED_MODES: frozenset[str] = frozenset(
    m.value for m in OperatorInteractionMode if m is not OperatorInteractionMode.UNRESOLVED
)

# Modes where the operator is NOT at a local keyboard.
REMOTE_MODES: frozenset[str] = frozenset({
    OperatorInteractionMode.REMOTE_CONTROL.value,
    OperatorInteractionMode.DUAL_AGENT.value,
})


def resolve_operator_interaction_mode(raw: str) -> OperatorInteractionMode:
    """Map a raw string to a typed operator interaction mode.

    Fails closed: unknown or empty values resolve to UNRESOLVED instead of
    silently defaulting to LOCAL_TERMINAL.
    """
    normalized = (raw or "").strip().lower()
    if not normalized:
        return OperatorInteractionMode.UNRESOLVED
    try:
        return OperatorInteractionMode(normalized)
    except ValueError:
        return OperatorInteractionMode.UNRESOLVED


def is_remote_mode(mode: str) -> bool:
    """Return True when the operator is NOT at a local keyboard."""
    return operator_mode_policy(mode).remote_handoff_allowed


def is_resolved(mode: str) -> bool:
    """Return True when the mode is known and safe to act on."""
    return mode in RESOLVED_MODES


def operator_mode_policy(raw: str) -> OperatorModePolicy:
    """Return the explicit decision policy for one operator mode."""
    resolved = resolve_operator_interaction_mode(raw).value
    return _MODE_POLICY_BY_MODE[resolved]


def operator_mode_allows_local_prompts(raw: str) -> bool:
    """Return True when local Terminal/app prompts are visible to the operator."""
    return operator_mode_policy(raw).local_prompts_allowed


def operator_mode_requires_headless(raw: str) -> bool:
    """Return True when launch/recovery must avoid local-only terminal prompts."""
    return operator_mode_policy(raw).headless_required


def operator_mode_allows_commit_self_approval(raw: str) -> bool:
    """Return True when commit approval can be satisfied without packet handoff."""
    return operator_mode_policy(raw).commit_self_approval


@dataclass(frozen=True, slots=True)
class OperatorContext:
    """Typed operator-presence metadata for mode-aware decisions."""

    interaction_mode: str = OperatorInteractionMode.UNRESOLVED.value
    device: str = "desktop"                # desktop, phone, tablet
    operator_available: bool = True
    notification_channel: str = "terminal" # terminal, dashboard, bridge


def operator_context_from_mapping(value: object) -> OperatorContext:
    """Deserialize an OperatorContext from a mapping.

    Fails closed: missing interaction_mode resolves to UNRESOLVED.
    """
    mapping = _mapping(value)
    raw_mode = _string(mapping.get("interaction_mode"))
    resolved = resolve_operator_interaction_mode(raw_mode)
    return OperatorContext(
        interaction_mode=resolved.value,
        device=_string(mapping.get("device")) or "desktop",
        operator_available=bool(mapping.get("operator_available", True)),
        notification_channel=(
            _string(mapping.get("notification_channel")) or "terminal"
        ),
    )


def _nested_get(mapping: Mapping[str, Any] | None, *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _governance_interaction_mode(governance: "ProjectGovernance | None") -> str:
    if governance is None:
        return ""
    return coerce_string(
        getattr(getattr(governance, "bridge_config", None), "operator_interaction_mode", "")
    )


def derive_operator_interaction_mode(
    *,
    governance: "ProjectGovernance | None",
    review_state_payload: Mapping[str, Any] | None,
    receipt: Mapping[str, Any] | None,
    reviewer_mode: str,
) -> str:
    """Canonical operator_interaction_mode derivation (rev_pkt_0463).

    Single shared reducer used by startup-context, control-plane read model,
    launcher discipline, ensure-follow, and reviewer-supervisor autostart
    so they cannot silently diverge. Iterates all typed sources and prefers
    any non-``local_terminal`` resolved value before falling back to
    attachment override and then to the explicit ``local_terminal`` default.
    Reviewer-mode derivation is the final fallback.

    Deferred imports avoid a circular dependency between this module and
    ``runtime.reviewer_runtime_models`` / ``runtime.conductor_capability``.
    """
    from .reviewer_runtime_models import (
        has_active_remote_control_attachment,
        remote_control_attachment_from_mapping,
    )
    from .conductor_capability import normalize_reviewer_mode

    attachment = remote_control_attachment_from_mapping(
        _nested_get(review_state_payload, "reviewer_runtime", "remote_control_attachment")
    )
    attachment_active = has_active_remote_control_attachment(attachment)
    candidates = (
        _governance_interaction_mode(governance),
        coerce_string(_nested_get(review_state_payload, "collaboration", "operator_interaction_mode")),
        coerce_string(_nested_get(review_state_payload, "reviewer_runtime", "operator_interaction_mode")),
        coerce_string((receipt or {}).get("operator_interaction_mode")),
    )
    saw_local_terminal = False
    for candidate in candidates:
        resolved = resolve_operator_interaction_mode(candidate)
        if resolved.value == "remote_control" and not attachment_active:
            continue
        if is_resolved(resolved.value) and resolved.value != "local_terminal":
            return resolved.value
        if resolved.value == "local_terminal":
            saw_local_terminal = True

    if attachment_active:
        return "remote_control"

    if saw_local_terminal:
        return "local_terminal"

    normalized = normalize_reviewer_mode(reviewer_mode)
    if normalized == "active_dual_agent":
        return "dual_agent"
    if normalized == "single_agent":
        return "single_agent"
    return "unresolved"
