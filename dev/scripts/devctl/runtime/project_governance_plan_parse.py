"""PlanRegistry mapping helpers."""

from __future__ import annotations

from collections.abc import Mapping

from .project_governance_contract import PlanRegistry, PlanRegistryEntry
from .value_coercion import coerce_bool, coerce_mapping_items, coerce_string


def plan_registry_entry_from_mapping(
    payload: Mapping[str, object],
) -> PlanRegistryEntry:
    entry = PlanRegistryEntry(
        path=coerce_string(payload.get("path")),
        role=coerce_string(payload.get("role")),
        authority=coerce_string(payload.get("authority")),
        scope=coerce_string(payload.get("scope")),
        when_agents_read=coerce_string(payload.get("when_agents_read")),
        title=coerce_string(payload.get("title")),
        owner=coerce_string(payload.get("owner")),
        lifecycle=coerce_string(payload.get("lifecycle")) or "unknown",
        has_execution_plan_contract=coerce_bool(
            payload.get("has_execution_plan_contract")
        ),
        has_session_resume=coerce_bool(payload.get("has_session_resume")),
    )
    return entry


def plan_registry_from_mapping(
    payload: Mapping[str, object],
) -> PlanRegistry:
    registry_path = (
        coerce_string(payload.get("registry_path")) or "dev/active/INDEX.md"
    )
    registry = PlanRegistry(
        registry_path=registry_path,
        tracker_path=coerce_string(payload.get("tracker_path"))
        or "dev/active/MASTER_PLAN.md",
        index_path=coerce_string(payload.get("index_path"))
        or "dev/active/INDEX.md",
        entries=tuple(
            plan_registry_entry_from_mapping(row)
            for row in coerce_mapping_items(payload.get("entries"))
        ),
    )
    return registry


def plan_registry_roots_from_mapping(
    payload: Mapping[str, object],
) -> PlanRegistry:
    """Backward-compatible wrapper for the richer PlanRegistry loader."""
    registry = plan_registry_from_mapping(payload)
    return registry


__all__ = [
    "plan_registry_entry_from_mapping",
    "plan_registry_from_mapping",
    "plan_registry_roots_from_mapping",
]
