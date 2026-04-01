"""Typed conductor-launch roster helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..runtime.role_profile import TandemRole, role_for_provider

if TYPE_CHECKING:
    from .core import LaneAssignment


@dataclass(frozen=True, slots=True)
class ConductorLaunchSpec:
    """One provider-backed conductor session requested by the launcher."""

    provider: str
    provider_name: str
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
    providers = _ordered_providers(
        lane_map=lane_map,
        providers_to_launch=providers_to_launch,
    )
    if not providers:
        return ()

    reviewer_provider = _provider_for_role(providers, TandemRole.REVIEWER)
    implementer_provider = _provider_for_role(providers, TandemRole.IMPLEMENTER)
    specs: list[ConductorLaunchSpec] = []
    for provider in providers:
        role = role_for_provider(provider).value
        specs.append(
            ConductorLaunchSpec(
                provider=provider,
                provider_name=provider.title(),
                counterpart_name=_counterpart_name(
                    provider=provider,
                    reviewer_provider=reviewer_provider,
                    implementer_provider=implementer_provider,
                ),
                role=role,
                lanes=lane_map.get(provider, ()),
                requested_worker_budget=budgets.get(provider, 0),
            )
        )
    return tuple(specs)


def _ordered_providers(
    *,
    lane_map: Mapping[str, tuple["LaneAssignment", ...]],
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
    providers.sort(key=_provider_sort_key)
    return tuple(providers)


def _provider_sort_key(provider: str) -> tuple[int, str]:
    role = role_for_provider(provider)
    if role == TandemRole.REVIEWER:
        return (0, provider)
    if role == TandemRole.IMPLEMENTER:
        return (1, provider)
    if role == TandemRole.OPERATOR:
        return (2, provider)
    return (3, provider)


def _provider_for_role(
    providers: Sequence[str],
    role: TandemRole,
) -> str | None:
    return next(
        (provider for provider in providers if role_for_provider(provider) == role),
        None,
    )


def _counterpart_name(
    *,
    provider: str,
    reviewer_provider: str | None,
    implementer_provider: str | None,
) -> str:
    role = role_for_provider(provider)
    if role == TandemRole.REVIEWER:
        return (implementer_provider or "implementer").title()
    if role == TandemRole.IMPLEMENTER:
        return (reviewer_provider or "reviewer").title()
    return (reviewer_provider or implementer_provider or "operator").title()


def _normalize_provider(provider: object) -> str:
    return str(provider or "").strip().lower()


def _coerce_budget(value: int | None) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0
