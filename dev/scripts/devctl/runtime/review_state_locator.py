"""Shared review-state discovery helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..repo_packs import active_path_config, active_path_config_is_overridden

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
        elif active_path_config_is_overridden():
            for candidate in active_path_config().review_state_candidates:
                _append_candidate(candidates, candidate)
    elif active_path_config_is_overridden():
        for candidate in active_path_config().review_state_candidates:
            _append_candidate(candidates, candidate)
    return tuple(candidates)


def resolve_review_state_path(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
) -> Path | None:
    """Return the first existing typed review-state projection path."""
    resolved_governance = _resolve_governance(repo_root, governance=governance)
    for candidate in review_state_relative_candidates(governance=resolved_governance):
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
    return _load_payload_from_path(path)


def load_current_review_state_payload(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
) -> dict[str, object] | None:
    """Load the freshest typed review-state payload available for live consumers."""
    resolved_governance = _resolve_governance(repo_root, governance=governance)
    refreshed = _refresh_bridge_backed_review_state_payload(
        repo_root,
        governance=resolved_governance,
    )
    if refreshed is not None:
        return refreshed
    return load_review_state_payload(repo_root, governance=resolved_governance)


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


def load_current_review_state(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
) -> "ReviewState | None":
    """Load the freshest typed review-state projection for live consumers."""
    payload = load_current_review_state_payload(repo_root, governance=governance)
    if payload is None:
        return None
    from .review_state_parser import review_state_from_payload

    return review_state_from_payload(payload)


def _append_candidate(candidates: list[str], candidate: Any) -> None:
    text = str(candidate or "").strip()
    if text and text not in candidates:
        candidates.append(text)


def _load_payload_from_path(path: Path | None) -> dict[str, object] | None:
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def _refresh_bridge_backed_review_state_payload(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None",
) -> dict[str, object] | None:
    bridge_path = _governed_existing_path(
        repo_root,
        governance=governance,
        relative_path=(
            str(governance.bridge_config.bridge_path or "").strip()
            if governance is not None
            else ""
        ),
    )
    review_channel_path = _governed_existing_path(
        repo_root,
        governance=governance,
        relative_path=(
            str(governance.bridge_config.review_channel_path or "").strip()
            if governance is not None
            else ""
        ),
    )
    output_root = _review_status_output_root(repo_root, governance=governance)
    if bridge_path is None or review_channel_path is None or output_root is None:
        return None
    try:
        from ..review_channel.state import refresh_status_snapshot

        snapshot = refresh_status_snapshot(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=output_root,
        )
    except (ImportError, OSError, ValueError):
        return None
    return _load_payload_from_path(Path(snapshot.projection_paths.review_state_path))


def _governed_existing_path(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None",
    relative_path: str,
) -> Path | None:
    if governance is None:
        return None
    candidate = relative_path.strip()
    if not candidate:
        return None
    path = repo_root / candidate
    return path if path.is_file() else None


def _review_status_output_root(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None",
) -> Path | None:
    if governance is not None:
        review_root = str(governance.artifact_roots.review_root or "").strip()
        if review_root:
            return repo_root / review_root
    if active_path_config_is_overridden():
        return repo_root / active_path_config().review_status_dir_rel
    return None


def _resolve_governance(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
) -> "ProjectGovernance | None":
    if governance is not None:
        return governance
    try:
        from ..governance.draft import scan_repo_governance
    except ImportError:
        return None
    try:
        return scan_repo_governance(repo_root)
    except (OSError, ValueError):
        return None


__all__ = [
    "load_current_review_state",
    "load_current_review_state_payload",
    "load_review_state",
    "load_review_state_payload",
    "resolve_review_state_path",
    "resolved_review_state_relative_path",
    "review_state_relative_candidates",
]
