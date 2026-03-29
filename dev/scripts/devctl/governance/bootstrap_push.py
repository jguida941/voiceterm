"""Starter push-governance helpers for governance bootstrap."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StarterPushGovernance:
    """Repo-pack starter defaults for guarded push routing."""

    default_remote: str
    development_branch: str
    release_branch: str
    protected_branches: tuple[str, ...]
    allowed_branch_prefixes: tuple[str, ...]

    def to_policy_payload(self) -> dict[str, object]:
        """Render a starter repo-governance payload."""
        payload: dict[str, object] = {}
        payload["default_remote"] = self.default_remote
        payload["development_branch"] = self.development_branch
        payload["release_branch"] = self.release_branch
        payload["protected_branches"] = list(self.protected_branches)
        payload["allowed_branch_prefixes"] = list(self.allowed_branch_prefixes)
        payload["preflight"] = _build_preflight_payload()
        payload["post_push"] = _build_post_push_payload()
        return payload

    def surface_branch_policy(self) -> str:
        """Render branch-policy text for starter hook/instruction surfaces."""
        if self.development_branch == self.release_branch:
            return f"`{self.development_branch}` (default branch)"
        return (
            f"`{self.release_branch}` (release), "
            f"`{self.development_branch}` (dev work)"
        )


def build_starter_push_governance(repo_root: Path) -> StarterPushGovernance:
    """Detect conservative starter push defaults for one repo."""
    default_branch = _detect_default_branch(repo_root) or "main"
    return StarterPushGovernance(
        default_remote="origin",
        development_branch=default_branch,
        release_branch=default_branch,
        protected_branches=(default_branch,),
        allowed_branch_prefixes=("feature/", "fix/"),
    )


def _build_preflight_payload() -> dict[str, object]:
    payload: dict[str, object] = {}
    payload["command"] = "check-router"
    payload["since_ref_template"] = "{remote}/{development_branch}"
    payload["execute"] = True
    return payload


def _build_post_push_payload() -> dict[str, object]:
    payload: dict[str, object] = {}
    payload["bundle"] = "bundle.post-push"
    return payload


def _detect_default_branch(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD", "--short"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    default_branch = (result.stdout or "").strip()
    if default_branch.startswith("origin/"):
        return default_branch[len("origin/"):]
    return default_branch
