"""Shared test helpers for typed PlanRegistry fixtures."""

from __future__ import annotations

from types import SimpleNamespace

from dev.scripts.devctl.runtime.project_governance import (
    DocRegistry,
    DocRegistryEntry,
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


def doc_registry_entry(
    path: str,
    scope: str,
    *,
    doc_class: str = "reference",
    artifact_role: str = "reference",
    authority: str = "reference-only",
    authority_kind: str = "reference_only",
    consumer_scope: str = "on_demand",
) -> DocRegistryEntry:
    return DocRegistryEntry(
        path=path,
        doc_class=doc_class,
        artifact_role=artifact_role,
        authority_kind=authority_kind,
        consumer_scope=consumer_scope,
        authority=authority,
        lifecycle="active",
        scope=scope,
        in_index=True,
        registry_managed=True,
    )


def governance_with_entries(
    *entries: PlanRegistryEntry,
    doc_entries: tuple[DocRegistryEntry, ...] = (),
) -> SimpleNamespace:
    return SimpleNamespace(
        plan_registry=PlanRegistry(
            registry_path="dev/active/INDEX.md",
            tracker_path="dev/active/MASTER_PLAN.md",
            index_path="dev/active/INDEX.md",
            entries=entries,
        ),
        doc_registry=DocRegistry(
            index_path="dev/active/INDEX.md",
            tracker_path="dev/active/MASTER_PLAN.md",
            entries=doc_entries,
        ),
    )


__all__ = [
    "doc_registry_entry",
    "governance_with_entries",
    "plan_registry_entry",
]
