"""Artifact discovery helpers for Operator Console review quick actions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_BRIDGE_REL = "code_audit.md"
DEFAULT_OPERATOR_DECISION_REL = "dev/reports/review_channel/operator_decisions/latest.md"
DEFAULT_ROLLOVER_ROOT_REL = "dev/reports/review_channel/rollovers"


@dataclass(frozen=True)
class ArtifactPreview:
    """Resolved artifact target for the quick-view button."""

    label: str
    path: Path


def resolve_primary_artifact_preview(repo_root: Path) -> ArtifactPreview | None:
    """Return the most relevant current artifact preview target."""
    latest_decision = repo_root / DEFAULT_OPERATOR_DECISION_REL
    if latest_decision.exists():
        return ArtifactPreview("Latest Operator Decision", latest_decision)

    latest_rollover = _latest_rollover_handoff(repo_root)
    if latest_rollover is not None:
        return ArtifactPreview("Latest Rollover Handoff", latest_rollover)

    bridge_path = repo_root / DEFAULT_BRIDGE_REL
    if bridge_path.exists():
        return ArtifactPreview("Live Code Audit", bridge_path)
    return None


def _latest_rollover_handoff(repo_root: Path) -> Path | None:
    rollover_root = repo_root / DEFAULT_ROLLOVER_ROOT_REL
    if not rollover_root.exists():
        return None
    candidates = sorted(
        (
            child / "handoff.md"
            for child in rollover_root.iterdir()
            if child.is_dir() and (child / "handoff.md").exists()
        ),
        reverse=True,
    )
    return candidates[0] if candidates else None
