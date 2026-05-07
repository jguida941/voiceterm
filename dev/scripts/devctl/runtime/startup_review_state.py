"""Startup-specific review-state loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .review_state_locator import load_current_review_state

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance
    from .review_state_models import ReviewState


def load_startup_review_state(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None",
    review_state: "ReviewState | None",
    review_status_dir: Path | None,
) -> "ReviewState | None":
    """Return the frozen review-state snapshot for this startup tick."""
    if review_state is not None:
        return review_state
    return load_current_review_state(
        repo_root,
        governance=governance,
        review_status_dir=review_status_dir,
        prefer_cached_projection=False,
    )
