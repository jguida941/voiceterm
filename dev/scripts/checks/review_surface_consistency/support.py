"""Shared filesystem and JSON helpers for review-surface consistency."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.runtime.governance_scan import scan_repo_governance_safely
from dev.scripts.devctl.runtime.review_state_locator import resolve_review_state_path


def surface_path(repo_root: Path, filename: str) -> Path:
    review_state_path = resolve_review_state_path(
        repo_root,
        governance=scan_repo_governance_safely(repo_root),
    )
    if review_state_path is None:
        return repo_root / filename
    return review_state_path.parent / filename


def load_review_state_payload(repo_root: Path) -> dict[str, object]:
    review_state_path = resolve_review_state_path(
        repo_root,
        governance=scan_repo_governance_safely(repo_root),
    )
    return _load_json(review_state_path)


def load_disk_review_state(repo_root: Path) -> dict[str, object]:
    candidates = [
        surface_path(repo_root, "review_state.json"),
        repo_root / "dev" / "reports" / "review_channel" / "latest" / "review_state.json",
    ]
    for candidate in candidates:
        payload = _load_json(candidate)
        if payload:
            return payload
    return {}


def _load_json(path: Path | None) -> dict[str, object]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _nested(payload: object, *keys: str) -> str:
    current = payload
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return str(current or "").strip()
