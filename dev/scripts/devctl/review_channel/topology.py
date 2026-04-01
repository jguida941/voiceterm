"""Shared topology helpers for review-channel runtime and planning surfaces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

from .collaboration_registry import build_runtime_agent_registry_from_collaboration
from ..runtime.review_state_models import (
    AgentRegistryEntryState,
    AgentRegistryState,
    CollaborationSessionState,
)
from ..runtime.role_profile import (
    TandemRole,
    build_default_tandem_profile,
    role_for_provider,
)
from .core import LaneAssignment


@dataclass(frozen=True, slots=True)
class PlannedTopologyProviderState:
    """One provider's planned-lane summary from the static review plan."""

    provider: str
    role: str
    planned_lane_count: int
    requested_worker_budget: int | None = None


@dataclass(frozen=True, slots=True)
class ReviewPlannedTopologyState:
    """Typed planned-topology companion for markdown-bridge compatibility."""

    schema_version: int
    contract_id: str
    timestamp: str
    mode: str
    plan_id: str
    source_path: str
    providers: tuple[PlannedTopologyProviderState, ...]
    lanes: tuple[LaneAssignment, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def agent_registry_to_dict(registry: AgentRegistryState) -> dict[str, object]:
    """Render a typed runtime registry to a JSON-friendly mapping."""
    return asdict(registry)


def build_runtime_agent_registry(
    *,
    timestamp: str,
    plan_id: str = "",
    collaboration: CollaborationSessionState | None = None,
    lanes: Sequence[LaneAssignment] = (),
    provider_state: Mapping[str, Mapping[str, object]] | None = None,
    active_conductor_providers: Sequence[str] = (),
) -> AgentRegistryState:
    """Build the canonical runtime participant registry.

    This registry describes live collaboration participants, not the static
    markdown lane plan. Planned lane capacity remains a separate topology
    surface until `CollaborationSession` grows a first-class worker registry.
    """
    if collaboration is not None:
        return build_runtime_agent_registry_from_collaboration(
            collaboration=collaboration,
            timestamp=timestamp,
            plan_id=plan_id,
        )

    normalized_state = {
        _normalize_provider(provider): state
        for provider, state in (provider_state or {}).items()
        if isinstance(state, Mapping)
    }
    providers = _runtime_provider_order(
        lanes=lanes,
        provider_state=normalized_state,
        active_conductor_providers=active_conductor_providers,
    )
    reviewer_provider = _first_provider_for_role(
        providers,
        TandemRole.REVIEWER,
        default="codex",
    )
    implementer_providers = tuple(
        provider
        for provider in providers
        if role_for_provider(provider) == TandemRole.IMPLEMENTER
    ) or ("claude",)
    operator_provider = _first_provider_for_role(
        providers,
        TandemRole.OPERATOR,
        default="operator",
    )
    profile = build_default_tandem_profile(
        reviewer_provider=reviewer_provider,
        implementer_providers=implementer_providers,
        operator_provider=operator_provider,
    )
    agents = tuple(
        _registry_entry(
            provider=role_profile.provider,
            role=role_profile.role,
            display_name=role_profile.display_name,
            plan_id=plan_id,
            timestamp=timestamp,
            provider_state=normalized_state.get(role_profile.provider, {}),
        )
        for role_profile in (
            profile.reviewer,
            *profile.implementers,
            profile.operator,
        )
    )
    return AgentRegistryState(timestamp=timestamp, agents=agents)

def build_planned_topology(
    *,
    lanes: Sequence[LaneAssignment],
    timestamp: str,
    plan_id: str = "",
    source_path: str = "",
    requested_worker_budgets: Mapping[str, int | None] | None = None,
) -> ReviewPlannedTopologyState:
    """Build the typed planned-lane topology from the static markdown plan."""

    provider_counts: dict[str, int] = {}
    provider_order: list[str] = []
    for lane in lanes:
        provider = _normalize_provider(lane.provider)
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
        if provider not in provider_order:
            provider_order.append(provider)
    budgets = {
        _normalize_provider(provider): _coerce_optional_int(value)
        for provider, value in (requested_worker_budgets or {}).items()
    }
    providers = tuple(
        PlannedTopologyProviderState(
            provider=provider,
            role=role_for_provider(provider).value,
            planned_lane_count=provider_counts[provider],
            requested_worker_budget=budgets.get(provider),
        )
        for provider in provider_order
    )
    return ReviewPlannedTopologyState(
        schema_version=1,
        contract_id="ReviewPlannedTopology",
        timestamp=timestamp,
        mode="markdown_bridge_static_plan",
        plan_id=plan_id,
        source_path=source_path,
        providers=providers,
        lanes=tuple(lanes),
    )


def _runtime_provider_order(
    *,
    lanes: Sequence[LaneAssignment],
    provider_state: Mapping[str, Mapping[str, object]],
    active_conductor_providers: Sequence[str],
) -> tuple[str, ...]:
    ordered: list[str] = []
    for lane in lanes:
        _append_provider(ordered, lane.provider)
    for provider in active_conductor_providers:
        _append_provider(ordered, provider)
    for provider, state in provider_state.items():
        if _provider_has_signal(state):
            _append_provider(ordered, provider)
    if not any(role_for_provider(provider) == TandemRole.REVIEWER for provider in ordered):
        ordered.insert(0, "codex")
    if not any(
        role_for_provider(provider) == TandemRole.IMPLEMENTER for provider in ordered
    ):
        ordered.append("claude")
    if not any(role_for_provider(provider) == TandemRole.OPERATOR for provider in ordered):
        ordered.append("operator")
    return tuple(ordered)


def _append_provider(ordered: list[str], provider: str) -> None:
    normalized = _normalize_provider(provider)
    if normalized and normalized not in ordered:
        ordered.append(normalized)


def _provider_has_signal(state: Mapping[str, object]) -> bool:
    return any(
        bool(str(state.get(field) or "").strip())
        for field in (
            "job_state",
            "waiting_on",
            "last_packet_seen",
            "last_packet_applied",
            "script_profile",
            "display_name",
        )
    )


def _first_provider_for_role(
    providers: Sequence[str],
    role: TandemRole,
    *,
    default: str,
) -> str:
    return next(
        (
            provider
            for provider in providers
            if role_for_provider(provider) == role
        ),
        default,
    )

def _registry_entry(
    *,
    provider: str,
    role: str,
    display_name: str,
    plan_id: str,
    timestamp: str,
    provider_state: Mapping[str, object],
) -> AgentRegistryEntryState:
    lane_title = _string(provider_state.get("lane_title")) or _default_lane_title(role)
    return AgentRegistryEntryState(
        agent_id=_string(provider_state.get("agent_id")) or provider,
        provider=provider,
        display_name=_string(provider_state.get("display_name")) or display_name,
        lane=_string(provider_state.get("lane")) or provider,
        lane_title=lane_title,
        current_job=_string(provider_state.get("current_job")) or role,
        job_state=_string(provider_state.get("job_state")) or _default_job_state(role),
        waiting_on=_string(provider_state.get("waiting_on")),
        last_packet_seen=_string(provider_state.get("last_packet_seen")),
        last_packet_applied=_string(provider_state.get("last_packet_applied")),
        script_profile=_string(provider_state.get("script_profile"))
        or _default_script_profile(role),
        mp_scope=_string(provider_state.get("mp_scope")) or plan_id,
        worktree=_string(provider_state.get("worktree")),
        branch=_string(provider_state.get("branch")),
        updated_at=timestamp,
    )


def _default_lane_title(role: str) -> str:
    if role == TandemRole.REVIEWER.value:
        return "Reviewer"
    if role == TandemRole.IMPLEMENTER.value:
        return "Implementer"
    if role == TandemRole.OPERATOR.value:
        return "Approver"
    return role.title()


def _default_job_state(role: str) -> str:
    if role == TandemRole.OPERATOR.value:
        return "idle"
    return "inactive"


def _default_script_profile(role: str) -> str:
    if role == TandemRole.OPERATOR.value:
        return ""
    return "markdown-bridge-conductor"


def _normalize_provider(provider: str) -> str:
    return str(provider or "").strip().lower()


def _string(value: object) -> str:
    return str(value or "").strip()


def _coerce_optional_int(value: object) -> int | None:
    if value is None:
        return None
    coerced = int(value)
    return max(coerced, 0)
