"""Shared review-state discovery helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..repo_packs import active_path_config

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance
    from .review_state_models import ReviewState


def review_state_relative_candidates(
    *,
    governance: "ProjectGovernance | None" = None,
) -> tuple[str, ...]:
    """Return repo-relative review-state candidates in lookup order."""
    candidates: list[str] = []
    if governance is not None:
        review_root = str(governance.artifact_roots.review_root or "").strip()
        if review_root:
            _append_candidate(candidates, f"{review_root.rstrip('/')}/review_state.json")
    for candidate in active_path_config().review_state_candidates:
        _append_candidate(candidates, candidate)
    return tuple(candidates)


def resolve_review_state_path(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
) -> Path | None:
    """Return the first existing typed review-state projection path."""
    for candidate in review_state_relative_candidates(governance=governance):
        path = repo_root / candidate
        if path.is_file():
            return path
    return None


def resolved_review_state_relative_path(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
) -> str:
    """Return the resolved repo-relative review-state path when it exists."""
    path = resolve_review_state_path(repo_root, governance=governance)
    if path is None:
        return ""
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return ""


def load_review_state_payload(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
) -> dict[str, object] | None:
    """Load the raw typed review-state payload when one candidate exists."""
    path = resolve_review_state_path(repo_root, governance=governance)
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def load_review_state(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
) -> "ReviewState | None":
    """Load the typed review-state projection when it exists."""
    payload = load_review_state_payload(repo_root, governance=governance)
    if payload is None:
        return None
    from .review_state_parser import review_state_from_payload

    return review_state_from_payload(payload)


def _append_candidate(candidates: list[str], candidate: Any) -> None:
    text = str(candidate or "").strip()
    if text and text not in candidates:
        candidates.append(text)


__all__ = [
    "load_review_state",
    "load_review_state_payload",
    "resolve_review_state_path",
    "resolved_review_state_relative_path",
    "review_state_relative_candidates",
]
