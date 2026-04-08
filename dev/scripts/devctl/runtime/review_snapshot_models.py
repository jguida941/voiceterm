"""Typed dataclasses for the ReviewSnapshot projection surface.

Deterministic projection of repo state for external reviewers, written at
the path resolved from ``ProjectGovernance.artifact_roots.review_snapshot_path``
(default ``dev/audits/REVIEW_SNAPSHOT.md``). Every field is sourced from an
existing typed builder. JSON serialisation helpers live in
``review_snapshot_serialize``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .review_snapshot_models_core import (
    CommitRow,
    FileStatRow,
    SnapshotDelta,
    SnapshotGovernanceState,
    SnapshotIdentity,
)
from .review_snapshot_models_quality import (
    GovernanceFindingRow,
    GuardResultRow,
    ProbeFindingRow,
    SnapshotQualitySignals,
)
from .review_snapshot_models_sections import (
    ContractOwnershipRow,
    HotspotRow,
    KnownGapRow,
    ReviewerHintRow,
    SnapshotArchitecture,
    SnapshotKnownGaps,
    SnapshotReasoning,
    SnapshotReviewerHints,
    WhyRecord,
)

REVIEW_SNAPSHOT_CONTRACT_ID = "ReviewSnapshot"
REVIEW_SNAPSHOT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class ReviewSnapshot:
    """Canonical typed projection of repo state for the external review surface."""

    schema_version: int = REVIEW_SNAPSHOT_SCHEMA_VERSION
    contract_id: str = REVIEW_SNAPSHOT_CONTRACT_ID
    identity: SnapshotIdentity = field(default_factory=SnapshotIdentity)
    governance_state: SnapshotGovernanceState = field(
        default_factory=SnapshotGovernanceState
    )
    delta: SnapshotDelta = field(default_factory=SnapshotDelta)
    quality: SnapshotQualitySignals = field(default_factory=SnapshotQualitySignals)
    architecture: SnapshotArchitecture = field(default_factory=SnapshotArchitecture)
    reviewer_hints: SnapshotReviewerHints = field(
        default_factory=SnapshotReviewerHints
    )
    reasoning: SnapshotReasoning = field(default_factory=SnapshotReasoning)
    known_gaps: SnapshotKnownGaps = field(default_factory=SnapshotKnownGaps)

    def to_dict(self) -> dict[str, object]:
        """Render the typed snapshot into a JSON-serialisable mapping."""
        # Late import avoids a circular dependency: review_snapshot_serialize
        # imports the dataclasses from this module.
        from .review_snapshot_serialize import (
            architecture_to_dict,
            delta_to_dict,
            governance_state_to_dict,
            known_gaps_to_dict,
            quality_to_dict,
            reasoning_to_dict,
            reviewer_hints_to_dict,
        )

        return {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "identity": asdict(self.identity),
            "governance_state": governance_state_to_dict(self.governance_state),
            "delta": delta_to_dict(self.delta),
            "quality": quality_to_dict(self.quality),
            "architecture": architecture_to_dict(self.architecture),
            "reviewer_hints": reviewer_hints_to_dict(self.reviewer_hints),
            "reasoning": reasoning_to_dict(self.reasoning),
            "known_gaps": known_gaps_to_dict(self.known_gaps),
        }


__all__ = [
    "REVIEW_SNAPSHOT_CONTRACT_ID",
    "REVIEW_SNAPSHOT_SCHEMA_VERSION",
    "CommitRow",
    "ContractOwnershipRow",
    "FileStatRow",
    "GovernanceFindingRow",
    "GuardResultRow",
    "HotspotRow",
    "KnownGapRow",
    "ProbeFindingRow",
    "ReviewSnapshot",
    "ReviewerHintRow",
    "SnapshotArchitecture",
    "SnapshotDelta",
    "SnapshotGovernanceState",
    "SnapshotIdentity",
    "SnapshotKnownGaps",
    "SnapshotQualitySignals",
    "SnapshotReasoning",
    "SnapshotReviewerHints",
    "WhyRecord",
]
