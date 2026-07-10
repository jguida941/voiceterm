"""Required-anchor policy for retained plan source snapshots."""

from __future__ import annotations

from typing import NamedTuple

MP377_EXCEPTION_SLICE1_ROW_ID = "MP377-P0-EXC-S1"
MP377_EXCEPTION_SLICE1_REQUIRED_ANCHORS = (
    "Master architecture",
    "Master invariant",
    "Do not create",
    "Plan agreement and typed-state ingestion protocol",
    "Discovery before editing",
    "Governed Exception Lifecycle concept",
    "Core lifecycle",
    "Recurrence",
    "ReviewSnapshot push case",
    "Exception policy belongs in ProjectGovernance / RepoPack",
    "Auto-repair before exception",
    "Core typed objects",
    "GovernedExceptionLifecycle shape",
    "ResolutionReceipt shape",
    "Closure requires",
    "SYSTEM_MAP / ConnectivityRegistry requirements",
    "system-picture requirements",
    "DocPolicy / DocRegistry / generated MD classification",
    "SurfaceProvenance requirement",
    "Authority and capability requirements",
    "Worktree/orphan requirements",
    "RuntimeAgreementReport requirements",
    "Graph contradiction / authority leak detection",
    "Dogfood failure auto-ingest",
    "PlanRegistry / plan-index rules",
    "Protected retention",
    "Swarm/fanout safety",
    "First executable implementation",
    "Slice 1 acceptance",
    "Future slices",
    "Schema / contract registry rule",
    "Contract registration guard / schema registration guard",
)
MP377_EVIDENCE_LIFECYCLE_ARCHIVE_ROW_ID = "MP377-EVIDENCE-LIFECYCLE-ARCHIVE-S1"
MP377_EVIDENCE_LIFECYCLE_ARCHIVE_REQUIRED_ANCHORS = (
    "NEVER delete typed evidence",
    "Archive after typed lifecycle closure",
    "Variable retention policy",
    "Time-based fallback",
    "Receipt lookup must remain functional for archived receipts",
    "Manifest file at archive root for indexed retrieval",
    "Compressed archive subdir",
)
REQUIRED_FULL_PLAN_ANCHORS_BY_ROW_ID = {
    MP377_EXCEPTION_SLICE1_ROW_ID: MP377_EXCEPTION_SLICE1_REQUIRED_ANCHORS,
    MP377_EVIDENCE_LIFECYCLE_ARCHIVE_ROW_ID: (
        MP377_EVIDENCE_LIFECYCLE_ARCHIVE_REQUIRED_ANCHORS
    ),
}


class PlanSourceAnchorStatus(NamedTuple):
    """Required-anchor completeness status for a retained plan source."""

    status: str
    required_count: int
    matched_count: int
    missing_anchors: tuple[str, ...] = ()


def full_plan_anchor_status(row_id: str, source_text: str) -> PlanSourceAnchorStatus:
    """Return required-anchor completeness for retained full-plan rows."""
    required = REQUIRED_FULL_PLAN_ANCHORS_BY_ROW_ID.get(row_id, ())
    if not required:
        return PlanSourceAnchorStatus(
            status="not_required",
            required_count=0,
            matched_count=0,
        )
    missing = missing_required_plan_source_anchors(row_id, source_text)
    return PlanSourceAnchorStatus(
        status="full_plan_retained" if not missing else "missing_required_anchors",
        required_count=len(required),
        matched_count=len(required) - len(missing),
        missing_anchors=missing,
    )


def missing_required_plan_source_anchors(
    row_id: str,
    source_text: str,
) -> tuple[str, ...]:
    """Return required full-plan anchors absent from a retained source body."""
    required = REQUIRED_FULL_PLAN_ANCHORS_BY_ROW_ID.get(row_id, ())
    if not required:
        return ()
    return tuple(anchor for anchor in required if anchor not in source_text)


__all__ = [
    "MP377_EVIDENCE_LIFECYCLE_ARCHIVE_REQUIRED_ANCHORS",
    "MP377_EVIDENCE_LIFECYCLE_ARCHIVE_ROW_ID",
    "MP377_EXCEPTION_SLICE1_REQUIRED_ANCHORS",
    "MP377_EXCEPTION_SLICE1_ROW_ID",
    "PlanSourceAnchorStatus",
    "REQUIRED_FULL_PLAN_ANCHORS_BY_ROW_ID",
    "full_plan_anchor_status",
    "missing_required_plan_source_anchors",
]
