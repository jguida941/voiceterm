"""Coordination-posture section builder for the system-picture snapshot."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from ..common_io import display_path
from .coordination_snapshot_models import CoordinationSnapshot
from .system_picture_sections import _build_section

_REVIEW_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json"
)


@dataclass(frozen=True, slots=True)
class CoordinationSectionSummary:
    """Typed summary row for the system-picture coordination section."""

    declared_topology: str
    observed_topology: str
    recommended_topology: str
    fanout_posture: str
    safe_to_fanout: bool
    worktree_strategy: str
    resync_required: bool
    observed_active_participant_count: int
    declared_participant_count: int
    planned_delegated_worker_count: int
    live_delegated_worker_count: int
    duplicate_worktree_count: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_coordination_section(
    *,
    repo_root: Path,
    snapshot: CoordinationSnapshot,
    review_state_path: Path | None,
) -> object:
    """Build the bounded coordination/topology section for system-picture."""
    notes: list[str] = list(snapshot.resync_reasons[:3])
    for row in snapshot.conflict_summaries[:2]:
        if row and row not in notes:
            notes.append(row)
    summary = CoordinationSectionSummary(
        declared_topology=snapshot.declared_topology,
        observed_topology=snapshot.observed_topology,
        recommended_topology=snapshot.recommended_topology,
        fanout_posture=snapshot.fanout_posture,
        safe_to_fanout=snapshot.safe_to_fanout,
        worktree_strategy=snapshot.worktree_strategy,
        resync_required=snapshot.resync_required,
        observed_active_participant_count=snapshot.observed_active_participant_count,
        declared_participant_count=snapshot.declared_participant_count,
        planned_delegated_worker_count=snapshot.planned_delegated_worker_count,
        live_delegated_worker_count=snapshot.live_delegated_worker_count,
        duplicate_worktree_count=len(snapshot.duplicate_worktrees),
    ).to_dict()
    return _build_section(
        section_id="coordination",
        title="Coordination Posture",
        status="current",
        summary=summary,
        source_path=(
            display_path(review_state_path, repo_root=repo_root)
            if review_state_path is not None
            else ""
        ),
        source_command=_REVIEW_STATUS_COMMAND,
        generated_at_utc=snapshot.generated_at_utc,
        notes=tuple(notes),
    )


__all__ = ["build_coordination_section"]
