"""Shared test helpers for typed PlanRegistry fixtures."""

from __future__ import annotations

from types import SimpleNamespace

from dev.scripts.devctl.runtime.project_governance import (
    PlanRegistry,
    PlanRegistryEntry,
)


def plan_registry_entry(
    path: str,
    scope: str,
    *,
    role: str = "spec",
    authority: str = "mirrored in MASTER_PLAN",
    when_agents_read: str = "always",
) -> PlanRegistryEntry:
    return PlanRegistryEntry(
        path=path,
        role=role,
        authority=authority,
        scope=scope,
        when_agents_read=when_agents_read,
    )


def governance_with_entries(*entries: PlanRegistryEntry) -> SimpleNamespace:
    return SimpleNamespace(
        plan_registry=PlanRegistry(
            registry_path="dev/active/INDEX.md",
            tracker_path="dev/active/MASTER_PLAN.md",
            index_path="dev/active/INDEX.md",
            entries=entries,
        )
    )


__all__ = ["governance_with_entries", "plan_registry_entry"]
