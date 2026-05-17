"""Extractors shared by Plan 4.1 dogfood scenario reducers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..governance.ledger_helpers import optional_text


def compact_router(router: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "contract_id": text(router.get("contract_id")),
        "schema_version": int(router.get("schema_version") or 0),
        "router_state": text(router.get("router_state")),
        "selected_route_id": text(router.get("selected_route_id")),
        "selected_route_ids": list_value(router.get("selected_route_ids")),
        "selection_reason": text(router.get("selection_reason")),
        "route_count": len(list_value(router.get("routes"))),
        "rejected_route_count": len(list_value(router.get("rejected_routes"))),
        "ambiguous_session_group_count": len(
            list_value(router.get("ambiguous_session_groups"))
        ),
        "governance_debt_count": len(list_value(router.get("governance_debt"))),
    }


def pending_packet_count(
    dashboard: Mapping[str, Any],
    review_state: Mapping[str, Any],
) -> int:
    packets = list_value(dashboard.get("pending_packets"))
    if packets:
        return len(packets)
    queue = mapping(review_state.get("queue"))
    for field in ("pending_total", "agent_sync_pending_total"):
        value = queue.get(field)
        if isinstance(value, int):
            return max(0, value)
    agent_sync = mapping(review_state.get("agent_sync"))
    return max(0, int(mapping(agent_sync.get("queue")).get("pending_total") or 0))


def text(value: object) -> str:
    return optional_text(value) or ""


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def list_value(value: object) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


__all__ = ["compact_router", "list_value", "mapping", "pending_packet_count", "text"]
