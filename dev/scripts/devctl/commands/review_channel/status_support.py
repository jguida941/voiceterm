"""Shared support helpers for the review-channel status command."""

from __future__ import annotations

from pathlib import Path

from ...repo_packs import active_path_config
from ..review_channel_command import RuntimePaths


def merge_status_messages(
    base_messages: object,
    refreshed_messages: list[str],
) -> list[str]:
    """Merge base and refreshed status messages without duplicates."""
    merged: list[str] = []
    if isinstance(base_messages, list):
        merged.extend(str(message) for message in base_messages)
    for message in refreshed_messages:
        if message not in merged:
            merged.append(message)
    return merged


def resolve_bridge_refresh_paths(
    *,
    repo_root: Path,
    paths: RuntimePaths,
) -> tuple[Path | None, Path | None]:
    """Resolve canonical review-channel status refresh paths."""
    config = active_path_config()
    review_channel_path = paths.review_channel_path
    if not isinstance(review_channel_path, Path):
        review_channel_path = repo_root / config.review_channel_rel
    status_dir = paths.status_dir
    if not isinstance(status_dir, Path):
        status_dir = repo_root / config.review_status_dir_rel
    return review_channel_path, status_dir
