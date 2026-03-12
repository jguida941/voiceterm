"""Shared helpers for Rust guard scripts."""

from __future__ import annotations

import subprocess
from pathlib import Path

try:
    from git_change_paths import list_changed_paths_with_base_map
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.git_change_paths import list_changed_paths_with_base_map

try:
    from dev.scripts.devctl.quality_scan_mode import (
        is_adoption_base_ref,
        is_worktree_head_ref,
    )
except ModuleNotFoundError:  # pragma: no cover
    import sys

    REPO_ROOT = Path(__file__).resolve().parents[3]
    repo_root_str = str(REPO_ROOT)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    from dev.scripts.devctl.quality_scan_mode import (
        is_adoption_base_ref,
        is_worktree_head_ref,
    )


def run_git(
    repo_root: Path,
    args: list[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run git with a stable error contract used by guard scripts."""
    result = subprocess.run(
        args,
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip() or "git command failed")
    return result


def validate_ref(run_git_fn, ref: str) -> None:
    """Ensure a ref resolves before commit-range checks run."""
    if is_adoption_base_ref(ref) or is_worktree_head_ref(ref):
        return
    run_git_fn(["git", "rev-parse", "--verify", ref], check=True)


def is_test_path(path: Path) -> bool:
    """Return True when a Rust path is test-only."""
    normalized = f"/{path.as_posix()}/"
    name = path.name
    return "/tests/" in normalized or name == "tests.rs" or name.endswith("_test.rs") or name.endswith("_tests.rs")


def list_changed_paths(
    run_git_fn,
    since_ref: str | None,
    head_ref: str,
) -> list[Path]:
    """Return changed paths using the shared rename-aware git path helper."""
    changed_paths, _base_map = list_changed_paths_with_base_map(
        run_git_fn,
        since_ref,
        head_ref,
    )
    return changed_paths


def collect_rust_files(
    source_root: Path,
    *,
    include_tests: bool,
) -> tuple[list[Path], int]:
    """Collect Rust files under `source_root`, optionally excluding tests."""
    files: list[Path] = []
    skipped_tests = 0
    for path in source_root.rglob("*.rs"):
        relative = Path(path.relative_to(source_root.parent).as_posix())
        if not include_tests and is_test_path(relative):
            skipped_tests += 1
            continue
        files.append(path)
    return sorted(files), skipped_tests


def normalize_changed_rust_paths(
    changed_paths: list[Path],
    *,
    include_tests: bool,
) -> set[str]:
    """Normalize changed Rust source paths to `rust/src/...` string form."""
    normalized: set[str] = set()
    for path in changed_paths:
        if path.suffix != ".rs":
            continue
        if not path.as_posix().startswith("rust/src/"):
            continue
        if not include_tests and is_test_path(path):
            continue
        normalized.add(path.as_posix())
    return normalized


def read_text_from_ref(run_git_fn, path: Path, ref: str) -> str | None:
    """Read repo-relative file text from a git ref."""
    if is_adoption_base_ref(ref):
        return None
    if is_worktree_head_ref(ref):
        return read_text_from_worktree(Path.cwd(), path)
    spec = f"{ref}:{path.as_posix()}"
    result = run_git_fn(["git", "show", spec], check=False)
    if result.returncode == 0:
        return result.stdout

    stderr = result.stderr.strip().lower()
    missing_markers = ("does not exist in", "exists on disk, but not in", "fatal: path")
    if any(marker in stderr for marker in missing_markers):
        return None
    raise RuntimeError(result.stderr.strip() or f"failed to read {spec}")


def read_text_from_worktree(repo_root: Path, path: Path) -> str | None:
    """Read repo-relative file text from the worktree."""
    absolute = repo_root / path
    if not absolute.exists():
        return None
    return absolute.read_text(encoding="utf-8", errors="replace")


class GuardContext:
    """Bound repo-root context for guard scripts."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def run_git(self, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
        """Run git with this context's repo root."""
        return run_git(self.repo_root, args, check=check)

    def validate_ref(self, ref: str) -> None:
        """Ensure a ref resolves."""
        validate_ref(self.run_git, ref)

    def read_text_from_ref(self, path: Path, ref: str) -> str | None:
        """Read file text from a git ref."""
        if is_worktree_head_ref(ref):
            return read_text_from_worktree(self.repo_root, path)
        return read_text_from_ref(self.run_git, path, ref)

    def read_text_from_worktree(self, path: Path) -> str | None:
        """Read file text from the worktree."""
        return read_text_from_worktree(self.repo_root, path)
