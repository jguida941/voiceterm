"""Shared platform policy path resolution helpers."""

from __future__ import annotations

from pathlib import Path


def resolve_repo_policy_path(
    *,
    repo_root: Path,
    policy_path: str | Path | None,
) -> Path:
    if policy_path is not None:
        candidate = Path(policy_path)
        return candidate if candidate.is_absolute() else repo_root / candidate
    return repo_root / "dev/config/devctl_repo_policy.json"
