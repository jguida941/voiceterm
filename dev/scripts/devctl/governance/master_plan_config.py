"""ProjectGovernance master-plan defaults."""

from __future__ import annotations

from pathlib import Path

from ..runtime.master_plan_contract import (
    DEFAULT_MASTER_PLAN_STORE_REL,
    IngestionPolicy,
    LinkedDoc,
    MasterPlan,
)


def linked_docs_from_registry(plan_registry) -> tuple[LinkedDoc, ...]:
    tracker = str(getattr(plan_registry, "tracker_path", "") or "").strip()
    if not tracker:
        return ()
    return (
        LinkedDoc(
            path=tracker,
            role="tracker",
            sdlc_stage="impl",
            links_to_plan_row="",
        ),
    )


def master_plan_from_registry(repo_root: Path, repo_id: str, plan_registry) -> MasterPlan:
    tracker = str(getattr(plan_registry, "tracker_path", "") or "").strip()
    projection = tracker or "dev/active/MASTER_PLAN.md"
    status = (
        "committed"
        if (repo_root / projection).is_file()
        else "pending_explainback"
    )
    return MasterPlan(
        repo_id=repo_id,
        rows=(),
        linked_docs=linked_docs_from_registry(plan_registry),
        status=status,
        source_path=projection,
        typed_store_path=DEFAULT_MASTER_PLAN_STORE_REL,
        projection_path=projection,
    )


def ingestion_policy_from_roots(governed_doc_roots) -> IngestionPolicy:
    scan_roots = tuple(governed_doc_roots) or ("dev/active", "docs", "plans")
    return IngestionPolicy(scan_roots=scan_roots)


__all__ = [
    "ingestion_policy_from_roots",
    "linked_docs_from_registry",
    "master_plan_from_registry",
]
