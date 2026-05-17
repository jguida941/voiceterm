"""Projection classification helpers for review-state loading."""

from __future__ import annotations

from pathlib import Path


def prefer_newer_typed_candidate(
    candidate_paths: tuple[Path, ...],
    *,
    preferred_path: Path | None,
    preferred_payload: dict[str, object] | None,
    repo_root: Path,
) -> tuple[Path | None, dict[str, object] | None]:
    """Preserve the event-backed bundle as canonical review-state authority."""
    del candidate_paths
    if preferred_path is None or preferred_payload is None:
        return preferred_path, preferred_payload
    if not is_event_backed_projection(
        preferred_path,
        preferred_payload,
        repo_root=repo_root,
    ):
        return preferred_path, preferred_payload
    return preferred_path, preferred_payload


def is_event_backed_projection(
    path: Path | None,
    payload: dict[str, object] | None,
    *,
    repo_root: Path,
) -> bool:
    if path is None:
        return False
    try:
        relative = path.relative_to(repo_root).as_posix()
    except ValueError:
        return False
    if not relative.endswith("/projections/latest/review_state.json"):
        return False
    review = payload.get("review") if isinstance(payload, dict) else None
    if not isinstance(review, dict):
        return False
    return str(review.get("surface_mode") or "").strip() == "event-backed"


__all__ = [
    "is_event_backed_projection",
    "prefer_newer_typed_candidate",
]
