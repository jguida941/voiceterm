"""Architecture, reviewer-hint, reasoning, and known-gap dataclasses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContractOwnershipRow:
    """One contract row from StartupContext.contract_ownership_map."""

    contract_id: str = ""
    owner_layer: str = ""
    runtime_model: str = ""
    startup_surface_tokens: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class HotspotRow:
    """One hotspot from the context-graph bootstrap payload."""

    path: str = ""
    risk_level: str = ""
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SnapshotArchitecture:
    """Slim architecture surface: contracts, hotspots, graph metrics, plans."""

    contract_ownership_map: tuple[ContractOwnershipRow, ...] = ()
    hotspots: tuple[HotspotRow, ...] = ()
    active_plans: tuple[str, ...] = ()
    graph_node_count: int = 0
    graph_edge_count: int = 0
    graph_source_mode: str = ""
    key_doc_paths: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReviewerHintRow:
    """One curated hint derived from the delta + risk classification."""

    kind: str = ""
    label: str = ""
    detail: str = ""
    reference: str = ""


@dataclass(frozen=True, slots=True)
class SnapshotReviewerHints:
    """Typed reviewer-action surface: what to verify and how to verify it."""

    hints: tuple[ReviewerHintRow, ...] = ()
    suggested_commands: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WhyRecord:
    """Structured 'why' for one commit: MP refs, plan links, evolution notes."""

    commit_sha: str = ""
    commit_sha_short: str = ""
    subject: str = ""
    mp_refs: tuple[str, ...] = ()
    checkpoint_markers: tuple[str, ...] = ()
    body_excerpt: str = ""
    linked_plan_docs: tuple[str, ...] = ()
    evolution_rationale: str = ""
    summary: str = ""


@dataclass(frozen=True, slots=True)
class SnapshotReasoning:
    """Why the delta landed, stitched across commits, plans, and evolution."""

    commit_why_records: tuple[WhyRecord, ...] = ()
    active_mp_summaries: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class KnownGapRow:
    """One known unresolved gap, blocker, or advisory warning."""

    kind: str = ""
    summary: str = ""
    reference: str = ""


@dataclass(frozen=True, slots=True)
class SnapshotKnownGaps:
    """Open findings, MP blockers, startup advisories, and stale warnings."""

    open_governance_findings: int = 0
    open_mp_blockers: tuple[str, ...] = ()
    startup_action_advisories: tuple[str, ...] = ()
    stale_warnings: tuple[str, ...] = ()
    gaps: tuple[KnownGapRow, ...] = ()


__all__ = [
    "ContractOwnershipRow",
    "HotspotRow",
    "KnownGapRow",
    "ReviewerHintRow",
    "SnapshotArchitecture",
    "SnapshotKnownGaps",
    "SnapshotReasoning",
    "SnapshotReviewerHints",
    "WhyRecord",
]
