"""Round-trip proof helpers for event-backed review-state emitter parity."""

from __future__ import annotations

from dataclasses import asdict

from dev.scripts.devctl.runtime.review_bridge_field_authority import (
    event_bridge_field_authority,
    event_bridge_roundtrip_required_fields,
)


def check_bridge_state_parser_roundtrip(
    *,
    synthetic: dict[str, object],
    bridge_state: dict[str, object],
    bridge_liveness: dict[str, object],
    contract_fields: frozenset[str],
) -> list[tuple[dict[str, object], dict[str, object] | None]]:
    """Verify emitted bridge_state survives the typed parser without drift."""
    from dev.scripts.devctl.runtime.review_state_parser import review_state_from_payload

    parsed = review_state_from_payload({
        "schema_version": 1,
        "command": "review-channel",
        "action": "status",
        "timestamp": str(synthetic.get("timestamp") or ""),
        "ok": True,
        "review_state": {
            "review": dict(_mapping(synthetic.get("review"))),
            "queue": dict(_mapping(synthetic.get("queue"))),
            "current_session": dict(_mapping(synthetic.get("current_session"))),
            "collaboration": dict(_mapping(synthetic.get("collaboration"))),
            "bridge": dict(bridge_state),
            "packets": list(_sequence(synthetic.get("packets"))),
        },
        "bridge_liveness": dict(bridge_liveness),
    })
    coverage: dict[str, object] = {
        "kind": "emitter_parity",
        "contract_id": "ReviewState",
        "check": "bridge_state_parser_roundtrip",
        "ok": True,
    }
    if parsed is None:
        coverage["ok"] = False
        coverage["detail"] = "Parser returned no ReviewState for emitted bridge payload."
        return [(coverage, {
            "kind": "emitter_parity",
            "contract_id": "ReviewState",
            "rule": "bridge-parser-roundtrip-gap",
            "detail": coverage["detail"],
        })]

    parsed_bridge = asdict(parsed.bridge)
    drift: list[str] = []
    for field_name in sorted(contract_fields & event_bridge_roundtrip_required_fields()):
        if parsed_bridge.get(field_name) != bridge_state.get(field_name):
            authority = event_bridge_field_authority(field_name)
            drift.append(
                f"{authority}.{field_name}: emitted={bridge_state.get(field_name)!r} "
                f"parsed={parsed_bridge.get(field_name)!r}"
            )
    if not drift:
        coverage["detail"] = (
            "Event-backed bridge_state round-trips through ReviewBridgeState."
        )
        return [(coverage, None)]

    detail = "bridge_state parser round-trip drift: " + "; ".join(drift)
    coverage["ok"] = False
    coverage["detail"] = detail
    return [(coverage, {
        "kind": "emitter_parity",
        "contract_id": "ReviewState",
        "rule": "bridge-parser-roundtrip-drift",
        "detail": detail,
    })]


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _sequence(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []
