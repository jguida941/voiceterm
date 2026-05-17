"""Live role-capacity readers for collaboration profiles."""

from __future__ import annotations

from collections.abc import Mapping

from .role_topology import resolve_role_topology


def live_capacity_by_role(review_state: Mapping[str, object]) -> dict[str, int]:
    live_topology = resolve_role_topology(
        mapping(review_state.get("bridge_liveness")),
        include_runtime_presence=True,
    )
    capacity: dict[str, int] = {}
    if live_topology.live_reviewer_providers:
        capacity["reviewer"] = len(live_topology.live_reviewer_providers)
    if live_topology.live_implementer_providers:
        capacity["implementer"] = len(live_topology.live_implementer_providers)
    if live_topology.live_operator_providers:
        capacity["operator"] = len(live_topology.live_operator_providers)
    return capacity


def mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
