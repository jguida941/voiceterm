"""Helpers for preparing copied repositories for portable-governance pilots."""

from __future__ import annotations

from dataclasses import dataclass
import subprocess
from pathlib import Path

from .time_utils import utc_timestamp


@dataclass(frozen=True, slots=True)
class GovernanceBootstrapResult:
    """Result payload for one pilot bootstrap run."""

    target_repo: str
    git_state: str
    repaired_git_file: bool
    initialized_git_repo: bool
    broken_gitdir_hint: str | None
    created_at_utc: str


def bootstrap_governance_pilot_repo(target_repo: str | Path) -> GovernanceBootstrapResult:
    """Repair broken copied-repo git state so governance tools can run locally."""
    repo_root = Path(target_repo).expanduser().resolve()
    if not repo_root.exists():
        raise ValueError(f"target repo does not exist: {repo_root}")
    if not repo_root.is_dir():
        raise ValueError(f"target repo is not a directory: {repo_root}")

    created_at = utc_timestamp()
    git_file = repo_root / ".git"
    repaired_git_file = False
    initialized_git_repo = False
    broken_gitdir_hint: str | None = None

    if _git_context_is_valid(repo_root):
        return GovernanceBootstrapResult(
            target_repo=str(repo_root),
            git_state="valid",
            repaired_git_file=False,
            initialized_git_repo=False,
            broken_gitdir_hint=None,
            created_at_utc=created_at,
        )

    if git_file.is_file():
        broken_gitdir_hint = git_file.read_text(encoding="utf-8", errors="replace").strip()
        git_file.unlink()
        repaired_git_file = True
    elif git_file.exists():
        raise ValueError(f"unsupported .git path shape in target repo: {git_file}")

    _run_git(repo_root, ["git", "init"])
    initialized_git_repo = True
    return GovernanceBootstrapResult(
        target_repo=str(repo_root),
        git_state="reinitialized",
        repaired_git_file=repaired_git_file,
        initialized_git_repo=initialized_git_repo,
        broken_gitdir_hint=broken_gitdir_hint,
        created_at_utc=created_at,
    )


def _git_context_is_valid(repo_root: Path) -> bool:
    try:
        _run_git(repo_root, ["git", "rev-parse", "--show-toplevel"])
    except RuntimeError:
        return False
    return True


def _run_git(repo_root: Path, cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip() or "git failed")
    return result.stdout.strip()
