"""Managed latest-push artifact helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ...common_io import display_path, read_json_object, resolve_repo_path
from ...config import REPO_ROOT
from ...repo_packs import active_path_config

_RECEIPT_HISTORY_DIR = "history"
_RECEIPT_HISTORY_FILE = "receipts.jsonl"


def resolve_push_report_artifact_path(*, repo_root: Path = REPO_ROOT) -> Path:
    """Return the managed latest-push artifact path for the active repo pack."""
    return resolve_repo_path(active_path_config().push_report_rel, repo_root=repo_root)


def _resolve_receipt_history_path(*, repo_root: Path = REPO_ROOT) -> Path:
    """Return the append-only JSONL receipt history path."""
    push_dir = resolve_push_report_artifact_path(repo_root=repo_root).parent
    return push_dir / _RECEIPT_HISTORY_DIR / _RECEIPT_HISTORY_FILE


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


def persist_latest_push_report(
    report: Mapping[str, Any],
    *,
    repo_root: Path = REPO_ROOT,
) -> str:
    """Write the managed latest-push artifact and return its repo-relative path."""
    path = resolve_push_report_artifact_path(repo_root=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_push_report(dict(report)), encoding="utf-8")
    return display_path(path, repo_root=repo_root)


def append_push_receipt(
    report: Mapping[str, Any],
    *,
    repo_root: Path = REPO_ROOT,
) -> Path:
    """Append one JSON line to the immutable push receipt history.

    Creates the history directory and file when they do not exist yet.
    Returns the absolute path to the JSONL file.
    """
    path = _resolve_receipt_history_path(repo_root=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(report), sort_keys=True) + "\n")
    return path


def lookup_push_receipt(
    *,
    branch: str,
    head_commit: str,
    repo_root: Path | None = None,
) -> dict[str, Any] | None:
    """Find the most recent receipt matching *branch* and *head_commit*.

    Reads the JSONL history from the end (most recent first) and returns
    the first line where both fields match.  Returns ``None`` when the
    file is missing or no line matches.
    """
    resolved_root = repo_root if repo_root is not None else REPO_ROOT
    path = _resolve_receipt_history_path(repo_root=resolved_root)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(entry, dict):
            continue
        if (
            str(entry.get("branch") or "").strip() == branch
            and str(entry.get("head_commit") or "").strip() == head_commit
        ):
            return entry
    return None
