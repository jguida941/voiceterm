"""Intent-aware startup receipt freshness helpers."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import TYPE_CHECKING, Any

try:
    from check_bootstrap import is_under_target_roots, resolve_quality_scope_roots
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        is_under_target_roots,
        resolve_quality_scope_roots,
    )

from ..config import get_repo_root

if TYPE_CHECKING:
    from .startup_receipt import StartupReceipt

IMPLEMENTATION_STRICT_STARTUP_INTENT = "implementation_strict"
REVIEWER_BOOTSTRAP_STARTUP_INTENT = "reviewer_bootstrap"
_QUALITY_SCOPE_IDS = (
    "python_guard",
    "python_probe",
    "rust_guard",
    "rust_probe",
)


def startup_receipt_problems_for_intent(
    receipt: "StartupReceipt | None",
    *,
    repo_root: Path | None = None,
    intent: str = IMPLEMENTATION_STRICT_STARTUP_INTENT,
    authority_report: dict[str, Any] | None = None,
    git_stdout_fn=None,
) -> list[str]:
    """Return receipt freshness problems for one startup intent."""
    if receipt is None:
        return [
            "Startup receipt is missing. Run the repo's `startup-context` command before guarded launcher or mutation commands.",
        ]
    resolved_root = repo_root or get_repo_root()
    git_stdout = git_stdout_fn or _git_stdout
    current_branch = git_stdout(resolved_root, "branch", "--show-current")
    current_head = git_stdout(resolved_root, "rev-parse", "HEAD")
    problems: list[str] = []
    if (
        receipt.current_branch
        and current_branch
        and receipt.current_branch != current_branch
    ):
        problems.append(
            "Startup receipt is stale for the current branch "
            f"(`{receipt.current_branch}` -> `{current_branch}`)."
        )
    if intent == REVIEWER_BOOTSTRAP_STARTUP_INTENT:
        bootstrap_head_problem = _reviewer_bootstrap_head_problem(
            receipt,
            repo_root=resolved_root,
            current_head=current_head,
        )
        if bootstrap_head_problem:
            problems.append(bootstrap_head_problem)
        return problems
    if (
        receipt.head_commit_sha
        and current_head
        and receipt.head_commit_sha != current_head
    ):
        problems.append(
            "Startup receipt is stale for the current HEAD commit "
            f"(`{receipt.head_commit_sha[:12]}` -> `{current_head[:12]}`)."
        )
    if receipt.checkpoint_required or not receipt.safe_to_continue_editing:
        problems.append(
            "Latest startup receipt still requires a checkpoint before another implementation or launcher step."
        )
    if not receipt.startup_authority_ok:
        problems.append(
            "Latest startup receipt recorded startup-authority failures."
        )
    return problems


def _reviewer_bootstrap_head_problem(
    receipt: "StartupReceipt",
    *,
    repo_root: Path,
    current_head: str,
) -> str | None:
    previous_head = str(receipt.head_commit_sha or "").strip()
    if not previous_head or not current_head or previous_head == current_head:
        return None
    changed_paths = _changed_paths_since(repo_root, previous_head)
    if changed_paths is None:
        return (
            "Startup receipt is stale for reviewer bootstrap and the current "
            "HEAD drift could not be classified safely."
        )
    quality_scope_paths = _quality_scope_changed_paths(
        changed_paths,
        repo_root=repo_root,
    )
    if not quality_scope_paths:
        return None
    sample = ", ".join(path.as_posix() for path in quality_scope_paths[:3])
    return (
        "Startup receipt is stale for reviewer bootstrap because HEAD drift "
        "touches guarded quality-scope files"
        f" (`{previous_head[:12]}` -> `{current_head[:12]}`; {sample})."
    )


def _changed_paths_since(
    repo_root: Path,
    previous_head: str,
) -> tuple[Path, ...] | None:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{previous_head}..HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return tuple(
        Path(line.strip())
        for line in result.stdout.splitlines()
        if line.strip()
    )


def _quality_scope_changed_paths(
    changed_paths: tuple[Path, ...],
    *,
    repo_root: Path,
) -> tuple[Path, ...]:
    if not changed_paths:
        return ()
    target_roots = _quality_scope_roots(repo_root)
    if not target_roots:
        return changed_paths
    matches: list[Path] = []
    for path in changed_paths:
        if is_under_target_roots(path, repo_root=repo_root, target_roots=target_roots):
            matches.append(path)
    return tuple(matches)


def _quality_scope_roots(repo_root: Path) -> tuple[Path, ...]:
    roots: list[Path] = []
    for scope_id in _QUALITY_SCOPE_IDS:
        resolved_roots = _scope_roots_for_id(scope_id, repo_root=repo_root)
        if resolved_roots is None:
            return ()
        for root in resolved_roots:
            root_path = Path(root)
            if root_path not in roots:
                roots.append(root_path)
    return tuple(roots)


def _scope_roots_for_id(
    scope_id: str,
    *,
    repo_root: Path,
) -> tuple[Path, ...] | None:
    try:
        return tuple(resolve_quality_scope_roots(scope_id, repo_root=repo_root))
    except (KeyError, OSError, ValueError):
        return None


def _git_stdout(repo_root: Path, *cmd: str) -> str:
    try:
        result = subprocess.run(
            ["git", *cmd],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


__all__ = [
    "IMPLEMENTATION_STRICT_STARTUP_INTENT",
    "REVIEWER_BOOTSTRAP_STARTUP_INTENT",
    "startup_receipt_problems_for_intent",
]
