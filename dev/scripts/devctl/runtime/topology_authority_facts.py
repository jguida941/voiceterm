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
    return _live_role_count(collaboration, role_id="review_agent") > 0


def live_implementer_present(
    collaboration: Mapping[str, object] | None,
    *,
    legacy_label: str = "",
) -> bool:
    """Typed companion to `live_reviewer_present` for the implementer
    lane. Same rule: typed `role_assignments` wins; legacy labels are
    diagnostic only."""
    return _live_role_count(collaboration, role_id="coding_agent") > 0


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
    return _live_role_provider(collaboration, role_id="coding_agent")


def live_reviewer_provider(
    collaboration: Mapping[str, object] | None,
    *,
    legacy_label: str = "",
) -> str:
    """Typed companion to `live_implementer_provider` for the reviewer
    lane. Same v4.55 contract: returns the live `review_agent`
    provider, or empty string when no typed reviewer is live.
    """
    return _live_role_provider(collaboration, role_id="review_agent")


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
        "single_agent",
        "dual_agent",
        "multi_agent_active",
        "multi_agent_orchestrated",
        "active_dual_agent",
        "multiple_agents",
        "tools_only",
    }


def _live_role_count(
    collaboration: Mapping[str, object] | None,
    *,
    role_id: str,
) -> int:
    return len(_live_role_providers(collaboration, role_id=role_id))


def _live_role_provider(
    collaboration: Mapping[str, object] | None,
    *,
    role_id: str,
) -> str:
    """Return one live provider name for ``role_id``, or empty string.

    When multiple providers hold the role, the first stable-ordered
    provider is returned (sorted lowercased). Empty string means no
    live typed assignment exists for that role — caller falls back to
    legacy default.
    """
    providers = _live_role_providers(collaboration, role_id=role_id)
    if not providers:
        return ""
    return sorted(providers)[0]


def _live_role_providers(
    collaboration: Mapping[str, object] | None,
    *,
    role_id: str,
) -> set[str]:
    if not isinstance(collaboration, Mapping):
        return set()
    rows = collaboration.get("role_assignments")
    if not isinstance(rows, (list, tuple)):
        return set()
    providers: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if not _truthy(row.get("live")):
            continue
        actual_role = (row.get("role_id") or "").strip().lower() if isinstance(row.get("role_id"), str) else ""
        if actual_role != role_id:
            continue
        provider = ""
        for key in ("provider", "agent_id"):
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                provider = value.strip().lower()
                break
        if not provider:
            continue
        providers.add(provider)
    return providers


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
    "live_reviewer_present",
    "live_reviewer_provider",
    "typed_collaboration_from_review_state",
]
