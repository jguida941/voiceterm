"""Observed control-topology derivation for startup authority."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from .conductor_capability import normalize_reviewer_mode
from .control_topology_bridge_counts import bridge_provider_count, boolish
from .control_topology_numeric import (
    count,
    int_value,
    supervised_conductor_count as resolve_supervised_conductor_count,
)
from .runtime_count_roles import provider_has_only_non_tandem_presence
from .control_topology_runtime_counts import (
    startup_bridge_liveness,
    startup_runtime_counts,
)

ObservedControlTopology = Literal[
    "single_implementer_single_reviewer",
    "single_agent",
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
    typed_participant_evidence = count(counts, "participants_total") > 0
    active_conductors = resolve_supervised_conductor_count(
        supervised_conductor_count_value=supervised_conductor_count,
        runtime_counts=counts,
    )
    control_presence_count = max(
        active_conductors,
        count(counts, "runtime_present_count", "runtime_present_participant_total"),
    )
    reviewer_count = max(
        int_value(live_reviewer_count),
        count(counts, "live_reviewer_count", "live_reviewer_total"),
        count(
            counts,
            "runtime_present_reviewer_count",
            "runtime_present_reviewer_total",
        ),
    )
    implementer_count = max(
        int_value(live_implementer_count),
        count(counts, "live_implementer_count", "live_implementer_total"),
        count(
            counts,
            "runtime_present_implementer_count",
            "runtime_present_implementer_total",
        ),
    )
    if not typed_participant_evidence:
        reviewer_count = max(
            reviewer_count,
            bridge_provider_count(bridge, "codex"),
            int(boolish(bridge.get("codex_conductor_active"))),
        )
        implementer_count = max(
            implementer_count,
            bridge_provider_count(bridge, "claude"),
            int(boolish(bridge.get("claude_conductor_active"))),
        )

    if control_presence_count <= 0:
        reviewer_count = 0
    elif reviewer_count > control_presence_count:
        reviewer_count = control_presence_count

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
    if control_presence_count >= 2:
        return "single_implementer_single_reviewer"
    if control_presence_count == 1:
        return "reviewer_only"
    return "no_live_agents"


def derive_implementation_permission(
    topology: ObservedControlTopology | str,
) -> ImplementationPermission:
    """Return the implementation permission implied by observed topology."""
    if topology in {"single_implementer_single_reviewer", "single_agent"}:
        return "active"
    if topology in {"dual_implementer", "implementer_without_reviewer"}:
        return "suspended"
    return "blocked"


def derive_startup_control_truth(
    review_state: object | None,
    *,
    reviewer_gate: object | None = None,
) -> tuple[ObservedControlTopology, ImplementationPermission]:
    """Return startup-facing topology and permission from typed review state."""
    bridge = startup_bridge_liveness(review_state)
    runtime_counts = startup_runtime_counts(review_state, bridge_liveness=bridge)
    topology = derive_observed_control_topology(
        supervised_conductor_count=runtime_counts.get("active_conductor_count", 0),
        bridge_liveness=bridge,
        runtime_counts=runtime_counts,
    )
    sanctioned_single_agent = is_sanctioned_single_agent_control(
        review_state,
        reviewer_gate=reviewer_gate,
    )
    typed_live_pair = _typed_live_reviewer_and_implementer_present(review_state)
    if sanctioned_single_agent and topology != "dual_implementer" and not typed_live_pair:
        return "single_agent", "active"
    return topology, derive_implementation_permission(topology)


def is_sanctioned_single_agent_control(
    review_state: object | None,
    *,
    reviewer_gate: object | None = None,
) -> bool:
    """Return whether runtime truth represents sanctioned single-agent authority."""
    reviewer_runtime = _field(review_state, "reviewer_runtime")
    bridge = _field(review_state, "bridge")
    effective_mode = (
        _text(_field(reviewer_gate, "effective_reviewer_mode"))
        or _text(_field(reviewer_gate, "reviewer_mode"))
        or _text(_field(reviewer_runtime, "effective_reviewer_mode"))
        or _text(_field(reviewer_runtime, "reviewer_mode"))
        or _text(_field(bridge, "effective_reviewer_mode"))
        or _text(_field(bridge, "reviewer_mode"))
    )
    if normalize_reviewer_mode(effective_mode) != "single_agent":
        return False

    interaction_mode = _text(_field(reviewer_gate, "operator_interaction_mode"))
    if interaction_mode and interaction_mode not in {
        "local_terminal",
        "single_agent",
        "remote_control",
    }:
        return False

    return True


def is_sanctioned_local_single_agent(
    review_state: object | None,
    *,
    reviewer_gate: object | None = None,
) -> bool:
    """Backward-compatible alias for sanctioned single-agent authority."""
    return is_sanctioned_single_agent_control(
        review_state,
        reviewer_gate=reviewer_gate,
    )


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


def _typed_live_reviewer_and_implementer_present(review_state: object | None) -> bool:
    collaboration = _field(review_state, "collaboration")
    participants = _sequence(_field(collaboration, "participants"))
    live_participants = tuple(
        row for row in participants if boolish(_field(row, "live"))
    )
    role_assignments = _sequence(_field(collaboration, "role_assignments"))
    review_agent_identities = _live_role_identities(
        role_assignments,
        role_id="review_agent",
        live_participants=live_participants,
    )
    coding_agent_identities = _live_role_identities(
        role_assignments,
        role_id="coding_agent",
        live_participants=live_participants,
    )
    if any(
        review_identity != coding_identity
        for review_identity in review_agent_identities
        for coding_identity in coding_agent_identities
    ):
        return True

    reviewer_live = any(
        _text(_field(row, "role")) == "reviewer"
        and boolish(_field(row, "live"))
        for row in participants
    )
    implementer_live = any(
        _text(_field(row, "role")) == "implementer"
        and boolish(_field(row, "live"))
        for row in participants
    )
    return reviewer_live and implementer_live


def _live_role_identities(
    rows: tuple[object, ...],
    *,
    role_id: str,
    live_participants: tuple[object, ...],
) -> tuple[str, ...]:
    identities: list[str] = []
    for row in rows:
        if _text(_field(row, "role_id")) != role_id or not boolish(_field(row, "live")):
            continue
        identity = _text(_field(row, "provider") or _field(row, "agent_id"))
        if not identity:
            continue
        if provider_has_only_non_tandem_presence(
            list(live_participants),
            identity,
            text_fn=_text,
        ):
            continue
        if identity not in identities:
            identities.append(identity)
    return tuple(identities)


def _sequence(value: object) -> tuple[object, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(value)


def _field(value: object, key: str) -> object:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None)


def _text(value: object) -> str:
    return str(value or "").strip().lower()

__all__ = [
    "ImplementationPermission",
    "ObservedControlTopology",
    "is_sanctioned_single_agent_control",
    "is_sanctioned_local_single_agent",
    "derive_implementation_permission",
    "derive_observed_control_topology",
    "derive_startup_control_truth",
]
