"""Helpers for reading repo-governance sections from the devctl policy file."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from ..config import REPO_ROOT
from ..quality_policy_loader import (
    DEFAULT_POLICY_RELATIVE_PATH,
    load_policy_payload,
    resolve_policy_path,
)

REPO_GOVERNANCE_KEY = "repo_governance"


@lru_cache(maxsize=None)
def _load_repo_policy_payload_cached(
    resolved_policy_path: str,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    warnings: list[str] = []
    payload = load_policy_payload(
        Path(resolved_policy_path),
        warnings=warnings,
        active_paths=set(),
    )
    if not isinstance(payload, dict):
        return {}, tuple(warnings)
    return payload, tuple(warnings)


def load_repo_policy_payload(
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
) -> tuple[dict[str, Any], tuple[str, ...], Path]:
    """Resolve and load the current repo policy payload."""
    default_policy_path = repo_root / DEFAULT_POLICY_RELATIVE_PATH
    resolved_policy_path = resolve_policy_path(
        repo_root=repo_root,
        policy_path=policy_path,
        default_policy_path=default_policy_path,
    )
    payload, warnings = _load_repo_policy_payload_cached(str(resolved_policy_path))
    return payload, warnings, resolved_policy_path


def load_repo_governance_section(
    section_name: str,
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
) -> tuple[dict[str, Any], tuple[str, ...], Path]:
    """Return one repo-governance section plus any policy warnings."""
    payload, warnings, resolved_policy_path = load_repo_policy_payload(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    governance_payload = payload.get(REPO_GOVERNANCE_KEY)
    if not isinstance(governance_payload, dict):
        return {}, warnings, resolved_policy_path
    section_payload = governance_payload.get(section_name)
    if not isinstance(section_payload, dict):
        return {}, warnings, resolved_policy_path
    return section_payload, warnings, resolved_policy_path
