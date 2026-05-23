"""Typed topology authority facts for v4.55.3 (rev_pkt_4772).

This module exposes pure typed-fact helpers that controller decisions
should consume INSTEAD of branching directly on legacy topology label
strings (`single_agent`, `dual_agent`, `multi_agent_active`,
`tools_only`, `active_dual_agent`, `multiple_agents`).

The legacy labels remain visible in projection/migration output for
operator continuity, but they MUST NOT grant or block runtime
authority on their own. Authority decisions read typed
`CollaborationSessionState.role_assignments` here.

Reuses `_live_role_totals` semantics from
`control_topology_runtime_counts.py` to keep one canonical
typed-reducer rule: an assignment counts as live presence only when
`live=True` and the provider isn't dominated by non-tandem presence.
"""

from __future__ import annotations

from collections.abc import Mapping

from .reviewer_mode import ReviewerMode
from .role_profile import normalize_role_id, role_capability_classes


_REVIEW_CAPABILITY_CLASSES = frozenset(
    {"review", "test", "architecture", "governance", "research", "intake"}
)
_IMPLEMENTATION_CAPABILITY_CLASSES = frozenset({"implementation", "mutation"})
_CONTROL_CAPABILITY_CLASSES = frozenset({"control", "observe"})


def live_reviewer_present(
    collaboration: Mapping[str, object] | None,
    *,
    legacy_label: str = "",
) -> bool:
    """Return whether typed state shows at least one live reviewer.

    `collaboration` is the typed CollaborationSessionState mapping
    (with `role_assignments` and `participants` keys). `legacy_label`
    is the migration string (e.g. "active_dual_agent"); it is recorded
    for diagnostic/migration purposes only and MUST NOT change the
    authority answer. A controller that needs to know "is a reviewer
    live" calls this function with the typed collaboration; a missing
    or non-typed collaboration mapping yields False even when the
    legacy label says otherwise.
    """
    return _live_capability_count(
        collaboration,
        capability_classes=_REVIEW_CAPABILITY_CLASSES,
    ) > 0


def live_implementer_present(
    collaboration: Mapping[str, object] | None,
    *,
    legacy_label: str = "",
) -> bool:
    """Typed companion to `live_reviewer_present` for the implementer
    lane. Same rule: typed `role_assignments` wins; legacy labels are
    diagnostic only."""
    return _live_capability_count(
        collaboration,
        capability_classes=_IMPLEMENTATION_CAPABILITY_CLASSES,
    ) > 0


def live_implementer_provider(
    collaboration: Mapping[str, object] | None,
    *,
    legacy_label: str = "",
) -> str:
    """Return the typed live implementer's provider, or empty string.

    v4.55 continuation (rev_pkt_4788): controller surfaces that
    previously hardcoded ``"claude"`` as the implementer-owner literal
    (e.g. ``startup_blocker_decision._STARTUP_AUTHORITY_REPAIR_DIRECTIVES``)
    should call this helper with the typed
    ``CollaborationSessionState`` and use the returned provider as the
    authoritative owner identity. Callers fall back to the legacy
    literal only when this returns "" — i.e. when no typed
    `coding_agent` is live.

    Provider names are returned lowercased and stripped to match the
    canonical actor-id casing used across review-channel posts.
    """
    return _live_capability_provider(
        collaboration,
        capability_classes=_IMPLEMENTATION_CAPABILITY_CLASSES,
    )


def live_reviewer_provider(
    collaboration: Mapping[str, object] | None,
    *,
    legacy_label: str = "",
) -> str:
    """Typed companion to `live_implementer_provider` for the reviewer
    lane. Same v4.55 contract: returns the live `review_agent`
    provider, or empty string when no typed reviewer is live.
    """
    return _live_capability_provider(
        collaboration,
        capability_classes=_REVIEW_CAPABILITY_CLASSES,
    )


def live_provider_has_role(
    collaboration: Mapping[str, object] | None,
    *,
    role_id: str,
    provider: str,
) -> bool:
    """Return whether one provider/actor has the requested live typed role.

    Presence of some other actor in the role is not authority for the current
    actor. The comparison accepts either provider or agent_id because runtime
    surfaces use both identifiers as actor keys.
    """
    normalized_provider = _normalize_actor(provider)
    normalized_role = _normalize_role_id(role_id)
    if not normalized_provider or not normalized_role:
        return False
    requested_classes = _role_request_capability_classes(normalized_role)
    for row in _live_role_rows(collaboration, role_id=normalized_role):
        if normalized_provider in {
            _normalize_actor(row.get("provider")),
            _normalize_actor(row.get("agent_id")),
        }:
            return True
    if requested_classes:
        for row in _live_capability_rows(
            collaboration,
            capability_classes=requested_classes,
        ):
            if normalized_provider in {
                _normalize_actor(row.get("provider")),
                _normalize_actor(row.get("agent_id")),
            }:
                return True
    return False


def typed_collaboration_from_review_state(
    review_state_payload: object,
) -> Mapping[str, object] | None:
    """Extract the typed `collaboration` mapping from a review-state
    payload. Returns None when the payload is missing, not a mapping,
    or carries no `collaboration` key. Centralizing this lookup lets
    production builders (e.g. `resolve_control_plane_context`,
    `auto_mode_status.inputs_from_read_model`) consistently feed typed
    collaboration into `AutoModeInputs` instead of relying on legacy
    `reviewer_mode` strings.
    """
    if not isinstance(review_state_payload, Mapping):
        return None
    candidate = review_state_payload.get("collaboration")
    if isinstance(candidate, Mapping):
        return candidate
    return None


def legacy_label_is_authority_evidence_only(label: str) -> bool:
    """True for every legacy topology label this module retires from
    runtime authority. A controller seeing one of these labels in
    isolation MUST NOT use it to gate decisions; the label is
    migration evidence, not a typed fact.
    """
    text = (label or "").strip().lower()
    return text in {
        # The historical ``single_agent`` topology label string survives
        # here only as a recognizer — its authority-mode meaning lives in
        # ``ReviewerMode.SINGLE_AGENT``; its topology meaning has been
        # retired in favor of ``single_implementer_single_reviewer``.
        ReviewerMode.SINGLE_AGENT.value,
        "dual_agent",
        "multi_agent_active",
        "multi_agent_orchestrated",
        "active_dual_agent",
        "multiple_agents",
        "tools_only",
    }


def _live_capability_count(
    collaboration: Mapping[str, object] | None,
    *,
    capability_classes: frozenset[str],
) -> int:
    return len(
        {
            provider
            for row in _live_capability_rows(
                collaboration,
                capability_classes=capability_classes,
            )
            if (provider := _row_provider(row))
        }
    )


def _live_capability_provider(
    collaboration: Mapping[str, object] | None,
    *,
    capability_classes: frozenset[str],
) -> str:
    providers = {
        provider
        for row in _live_capability_rows(
            collaboration,
            capability_classes=capability_classes,
        )
        if (provider := _row_provider(row))
    }
    if not providers:
        return ""
    return sorted(providers)[0]


def _live_role_rows(
    collaboration: Mapping[str, object] | None,
    *,
    role_id: str,
) -> tuple[Mapping[str, object], ...]:
    if not isinstance(collaboration, Mapping):
        return ()
    rows = collaboration.get("role_assignments")
    if not isinstance(rows, (list, tuple)):
        return ()
    matched: list[Mapping[str, object]] = []
    normalized_role = _normalize_role_id(role_id)
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if not _truthy(row.get("live")):
            continue
        if _normalize_role_id(row.get("role_id") or row.get("role")) != normalized_role:
            continue
        matched.append(row)
    return tuple(matched)


def _live_capability_rows(
    collaboration: Mapping[str, object] | None,
    *,
    capability_classes: frozenset[str],
) -> tuple[Mapping[str, object], ...]:
    if not isinstance(collaboration, Mapping):
        return ()
    rows = collaboration.get("role_assignments")
    if not isinstance(rows, (list, tuple)):
        return ()
    matched: list[Mapping[str, object]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if not _truthy(row.get("live")):
            continue
        role_id = _normalize_role_id(row.get("role_id") or row.get("role"))
        if set(role_capability_classes(role_id)) & capability_classes:
            matched.append(row)
    return tuple(matched)


def _row_provider(row: Mapping[str, object]) -> str:
    for key in ("provider", "agent_id"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return ""


def _role_request_capability_classes(role_id: str) -> frozenset[str]:
    if role_id in {"lead_agent", "review_agent"}:
        return _REVIEW_CAPABILITY_CLASSES
    if role_id == "coding_agent":
        return _IMPLEMENTATION_CAPABILITY_CLASSES
    if role_id == "operator_agent":
        return _CONTROL_CAPABILITY_CLASSES
    classes = frozenset(role_capability_classes(role_id))
    return classes


def _normalize_actor(value: object) -> str:
    return str(value or "").strip().lower()


def _normalize_role_id(value: object) -> str:
    normalized = normalize_role_id(value)
    return {
        "lead_agent": "orchestrator",
        "review_agent": "architecture_review",
        "coding_agent": "implementation",
        "operator_agent": "operator",
    }.get(normalized, normalized)


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y", "on"}
    return False


__all__ = [
    "legacy_label_is_authority_evidence_only",
    "live_implementer_present",
    "live_implementer_provider",
    "live_provider_has_role",
    "live_reviewer_present",
    "live_reviewer_provider",
    "typed_collaboration_from_review_state",
]
