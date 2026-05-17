"""Shared dirty-path filtering helpers for repo-owned git state consumers."""

from __future__ import annotations

from collections.abc import Sequence

from ..repo_packs import active_path_config


def ignored_dirty_path_prefixes() -> tuple[str, ...]:
    """Return repo-owned artifact prefixes excluded from dirty-path consumers."""
    config = active_path_config()
    prefixes = [
        config.review_status_dir_rel.strip("/"),
        config.review_artifact_root_rel.strip("/"),
        config.push_report_rel.strip("/"),
        *(
            str(rel).strip("/")
            for rel in getattr(config, "legacy_push_report_rels", ())
            if str(rel).strip("/")
        ),
        config.bridge_rel.strip("/"),
        "convo.md",
    ]
    return tuple(prefix for prefix in prefixes if prefix)


def path_is_ignored_for_dirty_paths(path: str, prefixes: Sequence[str]) -> bool:
    """Return True when a repo-relative path should be ignored in dirty views."""
    for prefix in prefixes:
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


__all__ = ["ignored_dirty_path_prefixes", "path_is_ignored_for_dirty_paths"]
