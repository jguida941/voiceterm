"""Common git helpers for worktree-orphan inventory scans."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .vcs import run_git_capture


def git_output(repo_root: Path, args: list[str]) -> str:
    code, output, _ = run_git_capture(args, repo_root=repo_root)
    return output.strip() if code == 0 else ""


def repo_identity(origin_or_path: str) -> str:
    digest = hashlib.sha256(origin_or_path.encode("utf-8")).hexdigest()
    return f"repo:sha256:{digest}"


def checkout_fingerprint(path: Path) -> str:
    resolved = str(path.resolve(strict=False))
    digest = hashlib.sha256(resolved.encode("utf-8")).hexdigest()
    return f"checkout:sha256:{digest}"


__all__ = ["checkout_fingerprint", "git_output", "repo_identity"]
