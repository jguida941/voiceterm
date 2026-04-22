"""Shared support helpers for worktree-orphan inventory scans."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from ..repo_packs import active_path_config
from .value_coercion import coerce_mapping, coerce_string_items
from .worktree_orphan_snapshot import OrphanSnapshotStats, OrphanSource

DEFAULT_COMPATIBILITY_PROJECTION_PATHS = ("bridge.md",)


def inventory_stats(sources: list[OrphanSource]) -> OrphanSnapshotStats:
    return OrphanSnapshotStats(
        total_sources=len(sources),
        unresolved_sources=sum(1 for source in sources if source.status == "unresolved"),
        dirty_sources=sum(
            1
            for source in sources
            if source.dirty_path_count or source.untracked_path_count
        ),
        unpublished_sources=sum(
            1 for source in sources if source.unpublished_commit_shas
        ),
        prunable_sources=sum(
            1
            for source in sources
            if source.source_kind
            in {"prunable_or_missing_worktree", "prunable_ci_worktree_orphan"}
        ),
        load_bearing_sources=sum(
            1 for source in sources if source.classification.load_bearing
        ),
    )


def normalize_review_state(value: Mapping[str, object]) -> Mapping[str, object]:
    review_state = coerce_mapping(value.get("review_state"))
    return review_state if review_state else value


def load_review_state(repo_root: Path) -> Mapping[str, object]:
    config = active_path_config()
    for rel in config.review_full_candidates:
        path = repo_root / rel
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            continue

        mapping = coerce_mapping(payload)
        if mapping:
            return mapping

    return {}


def compatibility_projection_paths(repo_root: Path) -> tuple[str, ...]:
    path = repo_root / active_path_config().repo_policy_rel
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return DEFAULT_COMPATIBILITY_PROJECTION_PATHS

    checkpoint = coerce_mapping(
        coerce_mapping(
            coerce_mapping(payload.get("repo_governance")).get("push")
        ).get("checkpoint")
    )
    values = coerce_string_items(checkpoint.get("compatibility_projection_paths"))

    return values or DEFAULT_COMPATIBILITY_PROJECTION_PATHS


def stable_id(prefix: str, repo_root: Path, generated_at_utc: str) -> str:
    digest = hashlib.sha256(
        f"{repo_root.resolve(strict=False)}:{generated_at_utc}".encode("utf-8")
    ).hexdigest()[:12]
    return f"{prefix}-{digest}"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


__all__ = [
    "DEFAULT_COMPATIBILITY_PROJECTION_PATHS",
    "compatibility_projection_paths",
    "inventory_stats",
    "load_review_state",
    "normalize_review_state",
    "stable_id",
    "utc_now",
]
