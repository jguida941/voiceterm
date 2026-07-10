"""Typed implementer-ACK freshness authority for review-channel consumers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ..runtime.review_state_models import ReviewCurrentSessionState
from ..runtime.review_state_parser_rows import current_session_state_from_payload
from .ack_contract import extract_implementer_ack_revision

_NON_CURRENT_ACK_STATES = frozenset({"missing", "pending", "unknown"})
ACK_FRESHNESS_TOGGLE_MODES = ("on_demand", "scheduled", "disabled")
ACK_FRESHNESS_TOGGLE_ID = "ImplementerAckFreshnessProjection"


def is_implementer_ack_current(cs: ReviewCurrentSessionState) -> bool:
    """Typed current-session ACK freshness predicate."""
    ack_state = _ack_state(cs)

    if ack_state == "current":
        return True

    if ack_state in _NON_CURRENT_ACK_STATES:
        return False

    return _ack_revision_matches_instruction(cs)


def current_session_from_mapping(
    value,
) -> ReviewCurrentSessionState:
    """Build a typed current-session row from a JSON-like mapping."""
    return current_session_state_from_payload(
        current_session=value if isinstance(value, dict) else {},
        bridge={},
        collaboration={},
    )


def build_implementer_ack_freshness_projection(
    *,
    review_state: Mapping[str, object],
    events: Sequence[Mapping[str, object]] = (),
    mode: str = "on_demand",
) -> dict[str, object]:
    """Return the typed implementer-ACK freshness view for command consumers."""
    normalized_mode = _normalize_mode(mode)
    review_state_payload = _review_state_payload(review_state)
    current_session = _mapping(review_state_payload.get("current_session"))
    current_revision = _text(current_session.get("current_instruction_revision"))
    typed_ack = _typed_ack_projection(
        review_state=review_state_payload,
        current_session=current_session,
        events=events,
        current_revision=current_revision,
    )
    bridge_ack = _bridge_ack_projection(
        review_state=review_state_payload,
        current_revision=current_revision,
    )
    status, ok, detail = _ack_freshness_status(
        mode=normalized_mode,
        current_revision=current_revision,
        typed_ack=typed_ack,
        bridge_ack=bridge_ack,
    )
    return {
        "schema_version": 1,
        "contract_id": ACK_FRESHNESS_TOGGLE_ID,
        "ok": ok,
        "status": status,
        "detail": detail,
        "current_instruction_revision": current_revision,
        "typed_ack": typed_ack,
        "bridge_visible_ack": bridge_ack,
        "automation": {
            "toggle_id": ACK_FRESHNESS_TOGGLE_ID,
            "mode": normalized_mode,
            "allowed_modes": list(ACK_FRESHNESS_TOGGLE_MODES),
        },
    }


def _typed_ack_projection(
    *,
    review_state: Mapping[str, object],
    current_session: Mapping[str, object],
    events: Sequence[Mapping[str, object]],
    current_revision: str,
) -> dict[str, object]:
    from .implementer_ack_events import latest_implementer_ack_payload

    event_rows = [dict(event) for event in events if isinstance(event, Mapping)]
    matching_event = (
        latest_implementer_ack_payload(
            event_rows,
            current_instruction_revision=current_revision,
        )
        if current_revision and event_rows
        else {}
    )
    latest_event = (
        latest_implementer_ack_payload(event_rows)
        if event_rows
        else {}
    )
    latest_projection = _matching_latest_projection(
        review_state=review_state,
        current_revision=current_revision,
    )
    payload = matching_event or latest_projection
    session_current = _session_ack_current(current_session)
    if payload:
        revision = _text(payload.get("current_instruction_revision"))
        ack = _text(payload.get("implementer_ack"))
        current = bool(current_revision and revision == current_revision and ack)
        return {
            "current": current,
            "source": (
                "implementer_ack_event"
                if matching_event
                else "latest_implementer_ack"
            ),
            "state": "current" if current else "stale",
            "revision": revision,
            "event_id": _text(payload.get("event_id")),
            "acknowledged_at_utc": _text(payload.get("acknowledged_at_utc")),
            "has_ack_text": bool(ack),
        }
    if session_current:
        return {
            "current": True,
            "source": "current_session",
            "state": "current",
            "revision": _text(current_session.get("implementer_ack_revision")),
            "event_id": "",
            "acknowledged_at_utc": "",
            "has_ack_text": bool(_text(current_session.get("implementer_ack"))),
        }
    stale_payload = latest_event or _mapping(review_state.get("latest_implementer_ack"))
    return {
        "current": False,
        "source": "none" if not stale_payload else "latest_implementer_ack",
        "state": _text(current_session.get("implementer_ack_state")) or "missing",
        "revision": (
            _text(stale_payload.get("current_instruction_revision"))
            or _text(current_session.get("implementer_ack_revision"))
        ),
        "event_id": _text(stale_payload.get("event_id")),
        "acknowledged_at_utc": _text(stale_payload.get("acknowledged_at_utc")),
        "has_ack_text": bool(
            _text(stale_payload.get("implementer_ack"))
            or _text(current_session.get("implementer_ack"))
        ),
    }


def _bridge_ack_projection(
    *,
    review_state: Mapping[str, object],
    current_revision: str,
) -> dict[str, object]:
    compat = _mapping(review_state.get("_compat"))
    projection = _mapping(compat.get("bridge_projection"))
    sections = _mapping(projection.get("sections"))
    ack_text = _text(
        sections.get("Implementer Ack")
        or sections.get("Claude Ack")
        or ""
    )
    revision = extract_implementer_ack_revision(ack_text)
    visible = _substantive_ack_text(ack_text)
    return {
        "visible": visible,
        "current": bool(visible and current_revision and revision == current_revision),
        "revision": revision,
        "has_revision": bool(revision),
        "section": "Implementer Ack" if "Implementer Ack" in sections else "Claude Ack",
        "has_ack_text": bool(ack_text),
    }


def _ack_freshness_status(
    *,
    mode: str,
    current_revision: str,
    typed_ack: Mapping[str, object],
    bridge_ack: Mapping[str, object],
) -> tuple[str, bool, str]:
    if mode == "disabled":
        return "disabled", True, "Implementer ACK freshness automation is disabled."
    if not current_revision:
        return "no_instruction", True, "No current instruction revision requires ACK."
    typed_current = bool(typed_ack.get("current"))
    bridge_visible = bool(bridge_ack.get("visible"))
    bridge_revision = _text(bridge_ack.get("revision"))
    typed_revision = _text(typed_ack.get("revision"))
    if bridge_visible and not typed_current:
        return (
            "bridge_only_drift",
            False,
            "Bridge-visible implementer ACK is not backed by typed ACK authority.",
        )
    if typed_current and bridge_visible and bridge_revision and bridge_revision != current_revision:
        return (
            "bridge_stale_drift",
            False,
            "Bridge-visible implementer ACK revision does not match the "
            "current typed instruction revision.",
        )
    if typed_current:
        return "current", True, "Typed implementer ACK is current."
    if typed_revision and typed_revision != current_revision:
        return "stale", False, "Typed implementer ACK is stale for the current instruction."
    state = _text(typed_ack.get("state")).lower() or "missing"
    return state, False, "Typed implementer ACK is not current."


def _same_revision(left: object, right: object) -> bool:
    left_text = _text(left)
    right_text = _text(right)

    return bool(left_text and right_text and left_text == right_text)


def _ack_state(cs: ReviewCurrentSessionState) -> str:
    return _text(cs.implementer_ack_state).lower()


def _ack_revision_matches_instruction(cs: ReviewCurrentSessionState) -> bool:
    return _same_revision(
        cs.implementer_ack_revision,
        cs.current_instruction_revision,
    )


def _session_ack_current(current_session: Mapping[str, object]) -> bool:
    return is_implementer_ack_current(
        current_session_from_mapping(dict(current_session))
    )


def _matching_latest_projection(
    *,
    review_state: Mapping[str, object],
    current_revision: str,
) -> Mapping[str, object]:
    latest = _mapping(review_state.get("latest_implementer_ack"))
    if not latest:
        return {}
    if _text(latest.get("current_instruction_revision")) != current_revision:
        return {}
    return latest


def _substantive_ack_text(value: object) -> bool:
    text = _text(value)
    normalized = text.lower().lstrip("- ").strip().rstrip(".")
    return bool(text and normalized not in {"missing", "pending", "(missing)"})


def _review_state_payload(review_state: Mapping[str, object]) -> Mapping[str, object]:
    nested = _mapping(review_state.get("review_state"))
    return nested or review_state


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _normalize_mode(value: object) -> str:
    text = _text(value) or "on_demand"
    if text in ACK_FRESHNESS_TOGGLE_MODES:
        return text
    return "on_demand"


def _text(value: object) -> str:
    if value is None:
        return ""

    return str(value).strip()


__all__ = [
    "ACK_FRESHNESS_TOGGLE_ID",
    "ACK_FRESHNESS_TOGGLE_MODES",
    "build_implementer_ack_freshness_projection",
    "current_session_from_mapping",
    "is_implementer_ack_current",
]
