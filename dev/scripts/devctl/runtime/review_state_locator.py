"""Shared review-state discovery helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from ..repo_packs import active_path_config, active_path_config_is_overridden
from ..repo_packs.review_cache import cache_is_fresh
from . import review_state_locator_candidates as _candidate_paths
from .review_state_contract_drift import (
    cached_projection_has_bridge_contract_drift as _cached_projection_has_bridge_contract_drift,
)
from .review_state_locator_projection import (
    is_event_backed_projection,
    prefer_newer_typed_candidate,
)
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
    _candidate_paths.active_path_config = active_path_config
    _candidate_paths.active_path_config_is_overridden = active_path_config_is_overridden
    return _candidate_paths.review_state_relative_candidates(governance=governance)


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
    typed_path, typed_payload = prefer_newer_typed_candidate(
        candidate_paths,
        preferred_path=typed_path,
        preferred_payload=typed_payload,
        repo_root=repo_root,
    )
    freshness_paths = projection_freshness_paths(
        repo_root,
        governance=resolved_governance,
    )
    if typed_payload is not None and is_event_backed_projection(
        typed_path,
        typed_payload,
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
    if typed_payload is not None and _cached_projection_has_bridge_contract_drift(
        payload=typed_payload,
        repo_root=repo_root,
        governance=resolved_governance,
    ):
        if allow_live_refresh:
            refreshed = refresh_bridge_backed_review_state_payload(
                repo_root,
                governance=resolved_governance,
                review_status_dir=review_status_dir,
            )
            if refreshed is not None:
                return refreshed
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
