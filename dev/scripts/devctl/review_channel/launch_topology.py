"""Typed conductor-launch roster helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..runtime.role_profile import normalize_role_id, role_capability_classes

if TYPE_CHECKING:
    from .core import LaneAssignment


@dataclass(frozen=True, slots=True)
class ConductorLaunchSpec:
    """One provider-backed conductor session requested by the launcher."""

    provider: str
    provider_name: str
    counterpart_provider: str
    counterpart_name: str
    role: str
    lanes: tuple["LaneAssignment", ...]
    requested_worker_budget: int


def build_conductor_launch_specs(
    *,
    provider_lane_map: Mapping[str, Sequence["LaneAssignment"]],
    requested_worker_budgets: Mapping[str, int | None] | None = None,
    providers_to_launch: Sequence[str] | None = None,
) -> tuple[ConductorLaunchSpec, ...]:
    """Build launch specs from the typed provider/lane map instead of fixed slots."""
    budgets = {
        _normalize_provider(provider): _coerce_budget(value)
        for provider, value in (requested_worker_budgets or {}).items()
    }
    lane_map = {
        provider: tuple(lanes)
        for provider, lanes in (
            (_normalize_provider(provider), tuple(rows))
            for provider, rows in provider_lane_map.items()
        )
        if provider and (lanes or provider in budgets)
    }
    role_map = _provider_role_map(lane_map)
    providers = _ordered_providers(
        lane_map=lane_map,
        role_map=role_map,
        providers_to_launch=providers_to_launch,
    )
    if not providers:
        return ()

    reviewer_provider = next(
        (
            provider
            for provider in providers
            if _provider_has_capability(provider, role_map, {"review", "test", "architecture", "governance", "research", "intake"})
        ),
        None,
    )
    implementer_provider = next(
        (
            provider
            for provider in providers
            if _provider_has_capability(provider, role_map, {"implementation", "mutation"})
        ),
        None,
    )
    specs: list[ConductorLaunchSpec] = []
    for provider in providers:
        spec_lanes = lane_map.get(provider, ())
        spec_budget = budgets.get(provider, 0) or 0
        # rev_pkt_2923 MP377-P0-T22AN-L: do not generate a conductor script
        # for a provider with zero lanes AND zero worker budget. Without this
        # filter, callers that strip `claude_lanes=[]` (e.g., the reviewer-only
        # launch path that bridge_action_support.is_reviewer_only_launch_scope
        # produces) still emit a `claude-conductor.sh` script because the
        # legacy provider_lane_map keeps an empty `claude` entry. The script
        # then gets spawned by the supervision loop, which is exactly the
        # rogue-claude-conductor recurrence (Finding X) operator's been
        # killing all session.
        if not spec_lanes and spec_budget <= 0:
            continue
        role = _provider_role(provider, role_map) or "unbound"
        counterpart_provider = _counterpart_provider(
            provider=provider,
            role_map=role_map,
            reviewer_provider=reviewer_provider,
            implementer_provider=implementer_provider,
        )
        specs.append(
            ConductorLaunchSpec(
                provider=provider,
                provider_name=provider.title(),
                counterpart_provider=counterpart_provider,
                counterpart_name=counterpart_provider.title(),
                role=role,
                lanes=spec_lanes,
                requested_worker_budget=spec_budget,
            )
        )
    return tuple(specs)


def _ordered_providers(
    *,
    lane_map: Mapping[str, tuple["LaneAssignment", ...]],
    role_map: Mapping[str, tuple[str, ...]],
    providers_to_launch: Sequence[str] | None,
) -> tuple[str, ...]:
    providers = list(lane_map)
    if providers_to_launch is not None:
        selected = {
            _normalize_provider(provider)
            for provider in providers_to_launch
            if _normalize_provider(provider)
        }
        providers = [provider for provider in providers if provider in selected]
    providers.sort(key=lambda provider: _provider_sort_key(provider, role_map))
    return tuple(providers)


def _provider_sort_key(
    provider: str,
    role_map: Mapping[str, tuple[str, ...]],
) -> tuple[int, str]:
    role_classes = _provider_capability_classes(provider, role_map)
    if role_classes & {"review", "test", "architecture", "governance", "research", "intake"}:
        return (0, provider)
    if role_classes & {"implementation", "mutation"}:
        return (1, provider)
    if role_classes & {"control", "observe"}:
        return (2, provider)
    return (3, provider)


def _counterpart_provider(
    *,
    provider: str,
    role_map: Mapping[str, tuple[str, ...]],
    reviewer_provider: str | None,
    implementer_provider: str | None,
) -> str:
    role_classes = _provider_capability_classes(provider, role_map)
    if role_classes & {"review", "test", "architecture", "governance", "research", "intake"}:
        return implementer_provider or "implementer"
    if role_classes & {"implementation", "mutation"}:
        return reviewer_provider or "reviewer"
    return reviewer_provider or implementer_provider or "operator"


def _provider_role(
    provider: str,
    role_map: Mapping[str, tuple[str, ...]],
) -> str:
    roles = role_map.get(provider, ())
    return roles[0] if roles else ""


def _provider_has_capability(
    provider: str,
    role_map: Mapping[str, tuple[str, ...]],
    capability_classes: set[str],
) -> bool:
    return bool(_provider_capability_classes(provider, role_map) & capability_classes)


def _provider_capability_classes(
    provider: str,
    role_map: Mapping[str, tuple[str, ...]],
) -> set[str]:
    classes: set[str] = set()
    for role in role_map.get(provider, ()):
        classes.update(role_capability_classes(role))
    return classes


def _provider_role_map(
    lane_map: Mapping[str, tuple["LaneAssignment", ...]],
) -> dict[str, tuple[str, ...]]:
    role_map: dict[str, tuple[str, ...]] = {}
    for provider, lanes in lane_map.items():
        lane_roles = tuple(
            dict.fromkeys(
                resolved_role
                for lane in lanes
                if (
                    resolved_role := normalize_role_id(getattr(lane, "role", ""))
                )
            )
        )
        if lane_roles:
            role_map[provider] = lane_roles
    return role_map


def _normalize_provider(provider: object) -> str:
    return str(provider or "").strip().lower()


def _coerce_budget(value: int | None) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0
