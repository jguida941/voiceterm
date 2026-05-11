"""Review-state candidate path selection."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..repo_packs import active_path_config, active_path_config_is_overridden

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance


def review_state_relative_candidates(
    *,
    governance: "ProjectGovernance | None" = None,
) -> tuple[str, ...]:
    """Return repo-relative review-state candidates in lookup order."""
    candidates: list[str] = []
    if governance is not None:
        review_root = str(governance.artifact_roots.review_root or "").strip()
        if review_root:
            _append_projection_sibling_candidate(candidates, review_root)
            if not legacy_review_status_root(review_root):
                _append_candidate(
                    candidates,
                    f"{review_root.rstrip('/')}/review_state.json",
                )
        elif active_path_config_is_overridden():
            _append_active_config_candidates(candidates)
    elif active_path_config_is_overridden():
        _append_active_config_candidates(candidates)
    return tuple(candidates)


def legacy_review_status_root(review_root: str) -> bool:
    root_path = Path(str(review_root).strip())
    return root_path.name == "latest" and root_path.parent.name != "projections"


def _append_active_config_candidates(candidates: list[str]) -> None:
    for candidate in active_path_config().review_state_candidates:
        _append_candidate(candidates, candidate)


def _append_candidate(candidates: list[str], candidate: Any) -> None:
    text = str(candidate or "").strip()
    if text and text not in candidates:
        candidates.append(text)


def _append_projection_sibling_candidate(
    candidates: list[str],
    review_root: str,
) -> None:
    """Route governed `latest` roots to the canonical projections sibling."""
    root_path = Path(str(review_root).strip())
    if root_path.name != "latest" or root_path.parent.name == "projections":
        return
    projection_root = root_path.parent / "projections" / root_path.name
    _append_candidate(candidates, projection_root.as_posix() + "/review_state.json")


__all__ = [
    "legacy_review_status_root",
    "review_state_relative_candidates",
]
