"""Role-count budget resolution for collaboration profiles."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .development_collaboration_modes import (
    DevelopCollaborationModeSpec,
    RoleCountBudget,
)


def resolved_role_budgets(
    *,
    requests: tuple[object, ...],
    selected_mode: DevelopCollaborationModeSpec | None,
    live_capacity_by_role: Mapping[str, int],
    resolved_budget_type: Any,
) -> tuple[object, ...]:
    budget_by_role = budget_by_role_for_mode(selected_mode)
    rows: list[object] = []
    for request in requests:
        budget = budget_by_role.get(request.role, fallback_budget(request.role))
        status = "ok"
        reasons: list[str] = []
        resolved_count = request.requested_count
        if request.requested_count > budget.max_count:
            status = "capped"
            reasons.append("requested count exceeds selected mode policy")
            resolved_count = budget.max_count
        live_capacity = int(live_capacity_by_role.get(request.role, -1))
        if live_capacity >= 0 and request.requested_count > live_capacity:
            status = "capacity_limited"
            reasons.append("requested count exceeds live topology capacity")
            resolved_count = min(resolved_count, live_capacity)
        rows.append(
            resolved_budget_type(
                role=request.role,
                requested_count=request.requested_count,
                resolved_count=resolved_count,
                max_count=budget.max_count,
                live_capacity=live_capacity,
                capacity_source="resolve_role_topology" if live_capacity >= 0 else "",
                mutable_lane_limit=budget.mutable_lane_limit,
                budget_kind=budget.budget_kind,
                status=status,
                reasons=tuple(reasons),
            )
        )
    return tuple(rows)


def budget_by_role_for_mode(
    selected_mode: DevelopCollaborationModeSpec | None,
) -> dict[str, RoleCountBudget]:
    if selected_mode is None:
        return {}
    return {budget.role: budget for budget in selected_mode.role_count_budgets}


def fallback_budget(role: str) -> RoleCountBudget:
    return RoleCountBudget(role=role, max_count=1, budget_kind="read_only")


def resolved_count_for(budgets: tuple[object, ...], role: str) -> int:
    for budget in budgets:
        if budget.role == role:
            return budget.resolved_count
    return 0
