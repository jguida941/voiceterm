"""Shared review-state discovery helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..repo_packs import active_path_config, active_path_config_is_overridden
from ..repo_packs.review_cache import cache_is_fresh
from .review_state_refresh_support import (
    refresh_event_backed_review_state_payload,
    projection_freshness_paths,
    refresh_bridge_backed_review_state_payload,
)

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
            _append_projection_sibling_candidate(candidates, review_root)
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
    review_status_dir: Path | None = None,
    prefer_cached_projection: bool = True,
    allow_live_refresh: bool = True,
) -> dict[str, object] | None:
    """Load the freshest typed review-state payload available for live consumers.

    Reuse the already-written typed projection only when it is at least as
    fresh as the governing ``bridge.md`` / ``review_channel.md`` sources.
    Otherwise, refresh the bridge-backed projection so live consumers do not
    keep reading stale reviewer or coordination state after the bridge changed.
    Callers that need a live bridge-backed refresh may set
    ``prefer_cached_projection=False``; frozen-call-site parity should instead
    pass an already-loaded typed ``ReviewState`` object directly.

    Event-backed ``.../projections/latest/review_state.json`` bundles are an
    exception: when the governed resolver already selected that path, keep it
    authoritative regardless of ``prefer_cached_projection``. Downgrading those
    callers onto the legacy bridge-refresh compatibility root reintroduces
    stale current-slice / coordination text and breaks parity across startup,
    dashboard, and session-resume surfaces.

    Internal callers that need the freshest *prior* typed payload during an
    in-progress bridge-backed refresh may set ``allow_live_refresh=False``.
    That keeps the read on the already-written payload and avoids recursively
    re-entering ``refresh_status_snapshot()`` for the same output root.
    """
    resolved_governance = _resolve_governance(repo_root, governance=governance)
    candidate_paths = _existing_candidate_paths(
        repo_root,
        governance=resolved_governance,
    )
    typed_path = candidate_paths[0] if candidate_paths else None
    typed_payload = _load_payload_from_path(typed_path)
    typed_path, typed_payload = _prefer_newer_typed_candidate(
        candidate_paths,
        preferred_path=typed_path,
        preferred_payload=typed_payload,
        repo_root=repo_root,
    )
    freshness_paths = projection_freshness_paths(
        repo_root,
        governance=resolved_governance,
    )
    if typed_payload is not None and _is_event_backed_projection_path(
        typed_path,
        repo_root=repo_root,
    ):
        if allow_live_refresh and not prefer_cached_projection:
            refreshed_event_payload = refresh_event_backed_review_state_payload(
                repo_root,
                governance=resolved_governance,
            )
            if refreshed_event_payload is not None:
                return refreshed_event_payload
        return typed_payload
    if prefer_cached_projection and typed_payload is not None and (
        not freshness_paths
        or cache_is_fresh(typed_path, freshness_paths=freshness_paths)
    ):
        return typed_payload

    if allow_live_refresh:
        refreshed = refresh_bridge_backed_review_state_payload(
            repo_root,
            governance=resolved_governance,
            review_status_dir=review_status_dir,
        )
        if refreshed is not None:
            return refreshed

    if typed_payload is not None and not freshness_paths:
        return typed_payload

    if typed_payload is not None and not allow_live_refresh:
        return typed_payload

    if freshness_paths:
        return None
    return typed_payload


def live_review_state_freshness_paths(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
) -> tuple[Path, ...]:
    """Return live bridge-backed freshness dependencies for runtime loaders."""
    resolved_governance = _resolve_governance(repo_root, governance=governance)
    return projection_freshness_paths(
        repo_root,
        governance=resolved_governance,
    )


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
    review_status_dir: Path | None = None,
    prefer_cached_projection: bool = True,
) -> "ReviewState | None":
    """Load the freshest typed review-state projection for live consumers."""
    payload = load_current_review_state_payload(
        repo_root,
        governance=governance,
        review_status_dir=review_status_dir,
        prefer_cached_projection=prefer_cached_projection,
    )
    if payload is None:
        return None
    from .review_state_parser import review_state_from_payload

    return review_state_from_payload(payload)


def _append_candidate(candidates: list[str], candidate: Any) -> None:
    text = str(candidate or "").strip()
    if text and text not in candidates:
        candidates.append(text)


def _append_projection_sibling_candidate(
    candidates: list[str],
    review_root: str,
) -> None:
    """Prefer the event-backed projections root when governance points at `latest`.

    Portable repo packs still expose legacy `.../latest` compatibility roots in
    some trees, while the freshest typed ReviewState now lives under the sibling
    `.../projections/latest` bundle. Add that sibling first so live consumers
    read the event-backed projection when both paths exist, but keep the
    governed `review_root/review_state.json` path as a fallback for older repos.
    """
    root_path = Path(str(review_root).strip())
    if root_path.name != "latest" or root_path.parent.name == "projections":
        return
    projection_root = root_path.parent / "projections" / root_path.name
    _append_candidate(candidates, projection_root.as_posix() + "/review_state.json")


def _load_payload_from_path(path: Path | None) -> dict[str, object] | None:
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def _existing_candidate_paths(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
) -> tuple[Path, ...]:
    paths: list[Path] = []
    for candidate in review_state_relative_candidates(governance=governance):
        path = repo_root / candidate
        if path.is_file():
            paths.append(path)
    return tuple(paths)


def _prefer_newer_typed_candidate(
    candidate_paths: tuple[Path, ...],
    *,
    preferred_path: Path | None,
    preferred_payload: dict[str, object] | None,
    repo_root: Path,
) -> tuple[Path | None, dict[str, object] | None]:
    """Preserve the event-backed bundle as canonical review-state authority.

    A legacy bridge-refreshed compatibility mirror may be newer on disk, but
    it must not outrank the governed `projections/latest` payload for canonical
    runtime reads. Loader freshness and explicit event refresh are the only
    supported ways to advance the event-backed authority path.
    """
    del candidate_paths
    if preferred_path is None or preferred_payload is None:
        return preferred_path, preferred_payload
    if not _is_event_backed_projection_path(preferred_path, repo_root=repo_root):
        return preferred_path, preferred_payload
    return preferred_path, preferred_payload


def _payload_timestamp(payload: dict[str, object] | None) -> str:
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("timestamp") or "").strip()


def _is_event_backed_projection_path(path: Path | None, *, repo_root: Path) -> bool:
    if path is None:
        return False
    try:
        relative = path.relative_to(repo_root).as_posix()
    except ValueError:
        return False
    return relative.endswith("/projections/latest/review_state.json")


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
    "live_review_state_freshness_paths",
    "load_current_review_state",
    "load_current_review_state_payload",
    "load_review_state",
    "load_review_state_payload",
    "resolve_review_state_path",
    "resolved_review_state_relative_path",
    "review_state_relative_candidates",
]
