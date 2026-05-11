"""Thin read-only helpers that wrap review-channel internals for commands.

Commands should import from this module (or ``repo_packs``) instead of
reaching into ``review_channel.events``, ``review_channel.event_store``,
or ``review_channel.state`` directly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .review_cache import cache_is_fresh, projection_dependency_paths


@dataclass
class MobileReviewStateResult:
    """Return value from :func:`load_mobile_review_state`.

    Encapsulates the review payload, projection file paths, the full
    projection path, and any warnings/errors collected during loading.
    """

    review_payload: dict[str, Any] = field(default_factory=dict)
    review_projection_files: dict[str, str] | None = None
    review_full_path: Path | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _load_payload_from_path(
    input_path: Path,
    *,
    label: str,
) -> tuple[dict[str, Any], list[str]]:
    """Load and validate a JSON payload from *input_path*."""
    errors: list[str] = []
    if not input_path.exists():
        errors.append(f"{label} not found: {input_path}")
        return {}, errors
    try:
        loaded = json.loads(input_path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(str(exc))
        return {}, errors
    except json.JSONDecodeError as exc:
        errors.append(f"invalid json in {label} ({exc})")
        return {}, errors
    if not isinstance(loaded, dict):
        errors.append(f"expected top-level object in {label}")
        return {}, errors
    return loaded, []


def _existing_projection_payload(
    review_status_dir: Path,
    *,
    freshness_paths: tuple[Path, ...],
) -> tuple[dict[str, Any], dict[str, str] | None, Path | None, list[str]]:
    """Return the existing full projection bundle when it is already present."""
    projection_root = _projection_root_for_status_root(review_status_dir)
    full_path = projection_root / "full.json"
    if not cache_is_fresh(full_path, freshness_paths=freshness_paths):
        return {}, None, None, ["review status projection is stale"]
    payload, errors = _load_payload_from_path(
        full_path,
        label="review status projection",
    )
    if errors:
        return {}, None, None, errors
    projection_files = {
        "root_dir": str(projection_root),
        "review_state_path": str(projection_root / "review_state.json"),
        "compact_path": str(projection_root / "compact.json"),
        "full_path": str(full_path),
        "actions_path": str(projection_root / "actions.json"),
        "trace_path": str(projection_root / "trace.ndjson"),
        "latest_markdown_path": str(projection_root / "latest.md"),
        "agent_registry_path": str(projection_root / "registry" / "agents.json"),
        "commit_pipeline_path": str(projection_root / "commit_pipeline.json"),
    }
    return payload, projection_files, full_path, []


def _existing_review_state_payload(
    review_status_dir: Path,
    *,
    freshness_paths: tuple[Path, ...],
) -> tuple[dict[str, Any], dict[str, str] | None, Path | None, list[str]]:
    """Return the existing typed review-state payload when it is already present."""
    projection_root = _projection_root_for_status_root(review_status_dir)
    review_state_path = projection_root / "review_state.json"
    if not cache_is_fresh(review_state_path, freshness_paths=freshness_paths):
        return {}, None, None, ["typed review_state projection is stale"]
    payload, errors = _load_payload_from_path(
        review_state_path,
        label="typed review_state projection",
    )
    if errors:
        return {}, None, None, ["typed review_state projection unavailable"]
    projection_files = {
        "root_dir": str(projection_root),
        "review_state_path": str(review_state_path),
        "compact_path": "",
        "full_path": str(review_state_path),
        "actions_path": "",
        "trace_path": "",
        "latest_markdown_path": "",
        "agent_registry_path": "",
        "commit_pipeline_path": "",
    }
    review_payload = {
        "review_state": payload,
        "bridge_liveness": payload.get("bridge", {}),
    }
    return review_payload, projection_files, review_state_path, []


def _projection_root_for_status_root(review_status_dir: Path) -> Path:
    if (
        review_status_dir.name == "latest"
        and review_status_dir.parent.name != "projections"
    ):
        return review_status_dir.parent / "projections" / review_status_dir.name
    return review_status_dir


def _review_freshness_paths(
    repo_root: Path,
    *,
    bridge_path: Path,
    review_channel_path: Path,
) -> tuple[Path, ...]:
    from . import active_path_config

    return projection_dependency_paths(
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        push_report_path=repo_root / active_path_config().push_report_rel,
    )


def _should_use_event_path(
    *,
    execution_mode: str,
    bridge_active: bool,
    artifact_paths,
    event_state_exists_fn,
) -> bool:
    return bool(
        execution_mode != "markdown-bridge"
        and not (execution_mode == "auto" and bridge_active)
        and event_state_exists_fn(artifact_paths)
    )


def _reuse_existing_projection(
    result: MobileReviewStateResult,
    *,
    review_status_dir: Path,
    freshness_paths: tuple[Path, ...],
    fallback_warning: str | None,
) -> bool:
    if result.review_full_path is not None:
        return False
    existing_payload, existing_projection_files, existing_full_path, existing_errors = (
        _existing_projection_payload(
            review_status_dir,
            freshness_paths=freshness_paths,
        )
    )
    if not existing_errors:
        if fallback_warning is not None:
            result.warnings.append(fallback_warning)
        result.review_payload = existing_payload
        result.review_projection_files = existing_projection_files
        result.review_full_path = existing_full_path
        return True
    existing_review_state_payload, existing_review_state_projection_files, existing_review_state_path, existing_review_state_errors = _existing_review_state_payload(
        review_status_dir,
        freshness_paths=freshness_paths,
    )
    if existing_review_state_errors:
        return False
    if fallback_warning is not None:
        result.warnings.append(fallback_warning)
    result.review_payload = existing_review_state_payload
    result.review_projection_files = existing_review_state_projection_files
    result.review_full_path = existing_review_state_path
    return True


def load_mobile_review_state(
    repo_root: Path,
    *,
    bridge_path: Path,
    review_channel_path: Path,
    review_status_dir: Path,
    execution_mode: str = "auto",
) -> MobileReviewStateResult:
    """Load review-channel state for the mobile-status command.

    Handles the event-path vs bridge-path branching, fallback, and
    projection loading that ``mobile_status.run`` previously owned
    inline.  Returns a single :class:`MobileReviewStateResult` so the
    command module never touches review-channel internals directly.
    """
    from ..review_channel.events import (
        event_state_exists,
        load_or_refresh_event_bundle,
        resolve_artifact_paths,
    )
    from ..review_channel.event_store import (
        build_bridge_status_fallback_warning,
        summarize_review_state_errors,
    )
    from ..review_channel.state import (
        projection_paths_to_dict,
        refresh_status_snapshot,
    )

    result = MobileReviewStateResult()
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    bridge_active = bridge_path.exists()
    freshness_paths = _review_freshness_paths(
        repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
    )

    use_event_path = _should_use_event_path(
        execution_mode=execution_mode,
        bridge_active=bridge_active,
        artifact_paths=artifact_paths,
        event_state_exists_fn=event_state_exists,
    )

    fallback_warning: str | None = None

    if use_event_path:
        try:
            bundle = load_or_refresh_event_bundle(
                repo_root=repo_root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
            )
        except (ValueError, OSError) as exc:
            fallback_warning = build_bridge_status_fallback_warning(str(exc))
        else:
            state_errors = summarize_review_state_errors(bundle.review_state)
            if state_errors is None:
                result.warnings.extend(bundle.review_state.get("warnings", []))
                result.review_projection_files = projection_paths_to_dict(
                    bundle.projection_paths
                )
                result.review_full_path = Path(bundle.projection_paths.full_path)
                review_payload, load_errors = _load_payload_from_path(
                    result.review_full_path,
                    label="review status projection",
                )
                if load_errors:
                    result.review_payload = {}
                    result.review_projection_files = None
                    result.review_full_path = None
                    fallback_warning = build_bridge_status_fallback_warning(
                        "; ".join(load_errors)
                    )
                else:
                    result.review_payload = review_payload
            else:
                fallback_warning = build_bridge_status_fallback_warning(state_errors)

    # Prefer an already-written projection bundle over triggering another
    # bridge-backed refresh path. This keeps thin clients aligned with a shared
    # status tick when another surface already refreshed the review bundle.
    if _reuse_existing_projection(
        result,
        review_status_dir=review_status_dir,
        freshness_paths=freshness_paths,
        fallback_warning=fallback_warning,
    ):
        return result

    # Bridge-backed fallback when the event path was skipped or failed
    if result.review_full_path is None:
        try:
            status_snapshot = refresh_status_snapshot(
                repo_root=repo_root,
                bridge_path=bridge_path,
                review_channel_path=review_channel_path,
                output_root=review_status_dir,
            )
        except (ValueError, OSError) as exc:
            if fallback_warning is not None:
                result.errors.append(fallback_warning)
                result.errors.append(f"Markdown-bridge fallback unavailable: {exc}")
            else:
                result.errors.append(str(exc))
        else:
            if fallback_warning is not None:
                result.warnings.append(fallback_warning)
            result.warnings.extend(status_snapshot.warnings)
            result.review_projection_files = projection_paths_to_dict(
                status_snapshot.projection_paths
            )
            result.review_full_path = Path(
                status_snapshot.projection_paths.full_path
            )
            review_payload, load_errors = _load_payload_from_path(
                result.review_full_path,
                label="review status projection",
            )
            result.errors.extend(load_errors)
            result.review_payload = review_payload

    return result
