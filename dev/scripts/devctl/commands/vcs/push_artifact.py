"""Managed latest-push artifact helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...common_io import display_path, read_json_object, resolve_repo_path
from ...config import REPO_ROOT
from ...repo_packs import active_path_config


def resolve_push_report_artifact_path(*, repo_root: Path = REPO_ROOT) -> Path:
    """Return the managed latest-push artifact path for the active repo pack."""
    return resolve_repo_path(active_path_config().push_report_rel, repo_root=repo_root)


def latest_push_report_relpath(*, repo_root: Path = REPO_ROOT) -> str:
    """Return the repo-relative path for the managed latest-push artifact."""
    return display_path(resolve_push_report_artifact_path(repo_root=repo_root), repo_root=repo_root)


def load_latest_push_report(*, repo_root: Path = REPO_ROOT) -> dict[str, Any] | None:
    """Load the managed latest-push artifact when it exists and is valid JSON."""
    payload, error = read_json_object(
        resolve_push_report_artifact_path(repo_root=repo_root),
        missing_message="",
        invalid_message="",
        object_message="",
        reject_duplicate_keys=True,
    )
    if error:
        return None
    return payload


def serialize_push_report(report: dict[str, Any]) -> str:
    """Render the canonical persisted JSON payload for the latest-push artifact."""
    return json.dumps(report, indent=2) + "\n"
