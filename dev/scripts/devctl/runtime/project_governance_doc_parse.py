"""DocPolicy and DocRegistry mapping helpers."""

from __future__ import annotations

from collections.abc import Mapping

from .project_governance_contract import (
    DocBudget,
    DocPolicy,
    DocRegistry,
    DocRegistryEntry,
)
from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping_items,
    coerce_string,
    coerce_string_items,
)


def doc_budget_from_mapping(
    payload: Mapping[str, object],
) -> DocBudget:
    budget = DocBudget(
        doc_class=coerce_string(payload.get("doc_class")),
        soft_limit=coerce_int(payload.get("soft_limit")),
        hard_limit=coerce_int(payload.get("hard_limit")),
    )
    return budget


def doc_policy_from_mapping(
    payload: Mapping[str, object],
) -> DocPolicy:
    policy = DocPolicy(
        docs_authority_path=coerce_string(payload.get("docs_authority_path"))
        or "AGENTS.md",
        active_docs_root=coerce_string(payload.get("active_docs_root"))
        or "dev/active",
        guides_root=coerce_string(payload.get("guides_root")) or "dev/guides",
        governed_doc_roots=coerce_string_items(
            payload.get("governed_doc_roots")
        ),
        tracker_path=coerce_string(payload.get("tracker_path"))
        or "dev/active/MASTER_PLAN.md",
        index_path=coerce_string(payload.get("index_path"))
        or "dev/active/INDEX.md",
        bridge_path=coerce_string(payload.get("bridge_path")) or "bridge.md",
        allowed_doc_classes=coerce_string_items(
            payload.get("allowed_doc_classes")
        ),
        allowed_authorities=coerce_string_items(
            payload.get("allowed_authorities")
        ),
        allowed_lifecycles=coerce_string_items(
            payload.get("allowed_lifecycles")
        ),
        required_plan_sections=coerce_string_items(
            payload.get("required_plan_sections")
        ),
        budget_limits=tuple(
            doc_budget_from_mapping(row)
            for row in coerce_mapping_items(payload.get("budget_limits"))
        ),
    )
    return policy


def doc_registry_entry_from_mapping(
    payload: Mapping[str, object],
) -> DocRegistryEntry:
    entry = DocRegistryEntry(
        path=coerce_string(payload.get("path")),
        doc_class=coerce_string(payload.get("doc_class")),
        authority=coerce_string(payload.get("authority")),
        lifecycle=coerce_string(payload.get("lifecycle")),
        scope=coerce_string(payload.get("scope")),
        owner=coerce_string(payload.get("owner")),
        canonical_consumer=coerce_string(payload.get("canonical_consumer")),
        line_count=coerce_int(payload.get("line_count")),
        budget_status=coerce_string(payload.get("budget_status")) or "ok",
        budget_limit=coerce_int(payload.get("budget_limit")),
        registry_managed=coerce_bool(payload.get("registry_managed")),
        in_index=coerce_bool(payload.get("in_index")),
        issues=coerce_string_items(payload.get("issues")),
    )
    return entry


def doc_registry_from_mapping(
    payload: Mapping[str, object],
) -> DocRegistry:
    registry = DocRegistry(
        docs_authority_path=coerce_string(payload.get("docs_authority_path"))
        or "AGENTS.md",
        index_path=coerce_string(payload.get("index_path"))
        or "dev/active/INDEX.md",
        tracker_path=coerce_string(payload.get("tracker_path"))
        or "dev/active/MASTER_PLAN.md",
        entries=tuple(
            doc_registry_entry_from_mapping(row)
            for row in coerce_mapping_items(payload.get("entries"))
        ),
    )
    return registry


__all__ = [
    "doc_budget_from_mapping",
    "doc_policy_from_mapping",
    "doc_registry_entry_from_mapping",
    "doc_registry_from_mapping",
]
