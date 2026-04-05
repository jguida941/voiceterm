"""Typed conductor-launch roster helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..runtime.role_profile import TandemRole, normalize_tandem_role, role_for_provider

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
            if role_map.get(provider, role_for_provider(provider))
            == TandemRole.REVIEWER
        ),
        None,
    )
    implementer_provider = next(
        (
            provider
            for provider in providers
            if role_map.get(provider, role_for_provider(provider))
            == TandemRole.IMPLEMENTER
        ),
        None,
    )
    specs: list[ConductorLaunchSpec] = []
    for provider in providers:
        role = role_map.get(provider, role_for_provider(provider)).value
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
                lanes=lane_map.get(provider, ()),
                requested_worker_budget=budgets.get(provider, 0),
            )
        )
    return tuple(specs)


def _ordered_providers(
    *,
    lane_map: Mapping[str, tuple["LaneAssignment", ...]],
    role_map: Mapping[str, TandemRole],
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
    role_map: Mapping[str, TandemRole],
) -> tuple[int, str]:
    role = role_map.get(provider, role_for_provider(provider))
    if role == TandemRole.REVIEWER:
        return (0, provider)
    if role == TandemRole.IMPLEMENTER:
        return (1, provider)
    if role == TandemRole.OPERATOR:
        return (2, provider)
    return (3, provider)


def _counterpart_provider(
    *,
    provider: str,
    role_map: Mapping[str, TandemRole],
    reviewer_provider: str | None,
    implementer_provider: str | None,
) -> str:
    role = role_map.get(provider, role_for_provider(provider))
    if role == TandemRole.REVIEWER:
        return implementer_provider or "implementer"
    if role == TandemRole.IMPLEMENTER:
        return reviewer_provider or "reviewer"
    return reviewer_provider or implementer_provider or "operator"


def _provider_role_map(
    lane_map: Mapping[str, tuple["LaneAssignment", ...]],
) -> dict[str, TandemRole]:
    role_map: dict[str, TandemRole] = {}
    for provider, lanes in lane_map.items():
        lane_roles = {
            resolved_role
            for lane in lanes
            if (
                resolved_role := normalize_tandem_role(getattr(lane, "role", ""))
            )
            is not None
        }
        if len(lane_roles) > 1:
            roles = ", ".join(sorted(role.value for role in lane_roles))
            raise ValueError(
                f"Provider `{provider}` has conflicting planned lane roles: {roles}"
            )
        if lane_roles:
            role_map[provider] = next(iter(lane_roles))
    return role_map


def _normalize_provider(provider: object) -> str:
    return str(provider or "").strip().lower()


def _coerce_budget(value: int | None) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0
