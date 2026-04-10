"""Observed control-topology derivation for startup authority."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from .control_topology_bridge_counts import bridge_provider_count, boolish
from .control_topology_numeric import (
    count,
    int_value,
    supervised_conductor_count as resolve_supervised_conductor_count,
)
from .control_topology_runtime_counts import (
    startup_bridge_liveness,
    startup_runtime_counts,
)

ObservedControlTopology = Literal[
    "single_implementer_single_reviewer",
    "dual_implementer",
    "implementer_without_reviewer",
    "reviewer_only",
    "no_live_agents",
]
ImplementationPermission = Literal["active", "suspended", "blocked"]


def derive_observed_control_topology(
    live_reviewer_count: int | None = None,
    live_implementer_count: int | None = None,
    supervised_conductor_count: int | None = None,
    *,
    bridge_liveness: Mapping[str, object] | None = None,
    runtime_counts: Mapping[str, object] | None = None,
) -> ObservedControlTopology:
    """Derive live control topology from role counts and supervision evidence."""
    bridge = bridge_liveness if isinstance(bridge_liveness, Mapping) else {}
    counts = runtime_counts if isinstance(runtime_counts, Mapping) else {}
    active_conductors = resolve_supervised_conductor_count(
        supervised_conductor_count_value=supervised_conductor_count,
        runtime_counts=counts,
    )
    reviewer_count = max(
        int_value(live_reviewer_count),
        count(counts, "live_reviewer_count", "live_reviewer_total"),
        bridge_provider_count(bridge, "codex"),
        int(boolish(bridge.get("codex_conductor_active"))),
    )
    implementer_count = max(
        int_value(live_implementer_count),
        count(counts, "live_implementer_count", "live_implementer_total"),
        bridge_provider_count(bridge, "claude"),
        int(boolish(bridge.get("claude_conductor_active"))),
    )

    if active_conductors <= 0:
        reviewer_count = 0
    elif reviewer_count > active_conductors:
        reviewer_count = active_conductors

    if implementer_count >= 2:
        return "dual_implementer"
    if reviewer_count > 0 and implementer_count > 0:
        return "single_implementer_single_reviewer"
    if implementer_count > 0:
        return "implementer_without_reviewer"
    if reviewer_count > 0:
        return "reviewer_only"
    if _has_role_evidence(
        live_reviewer_count=live_reviewer_count,
        live_implementer_count=live_implementer_count,
        runtime_counts=counts,
        bridge_liveness=bridge,
    ):
        return "no_live_agents"
    if active_conductors >= 2:
        return "single_implementer_single_reviewer"
    if active_conductors == 1:
        return "reviewer_only"
    return "no_live_agents"


def derive_implementation_permission(
    topology: ObservedControlTopology | str,
) -> ImplementationPermission:
    """Return the implementation permission implied by observed topology."""
    if topology == "single_implementer_single_reviewer":
        return "active"
    if topology in {"dual_implementer", "implementer_without_reviewer"}:
        return "suspended"
    return "blocked"


def derive_startup_control_truth(
    review_state: object | None,
) -> tuple[ObservedControlTopology, ImplementationPermission]:
    """Return startup-facing topology and permission from typed review state."""
    bridge = startup_bridge_liveness(review_state)
    runtime_counts = startup_runtime_counts(review_state, bridge_liveness=bridge)
    topology = derive_observed_control_topology(
        supervised_conductor_count=runtime_counts.get("active_conductor_count", 0),
        bridge_liveness=bridge,
        runtime_counts=runtime_counts,
    )
    return topology, derive_implementation_permission(topology)


def _has_role_evidence(
    *,
    live_reviewer_count: int | None,
    live_implementer_count: int | None,
    runtime_counts: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
) -> bool:
    if live_reviewer_count is not None or live_implementer_count is not None:
        return True
    if any(
        key in runtime_counts
        for key in (
            "live_reviewer_count",
            "live_reviewer_total",
            "live_implementer_count",
            "live_implementer_total",
        )
    ):
        return True
    return any(
        key in bridge_liveness
        for key in (
            "codex_conductor_active",
            "claude_conductor_active",
            "active_conductor_providers",
        )
    )

__all__ = [
    "ImplementationPermission",
    "ObservedControlTopology",
    "derive_implementation_permission",
    "derive_observed_control_topology",
    "derive_startup_control_truth",
]
