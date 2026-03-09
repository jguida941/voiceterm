"""Git-diff-based targeting for mutation testing."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

# Wire repo root so devctl config imports resolve from sibling context.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dev.scripts.devctl.config import SRC_DIR, resolve_src_dir  # noqa: E402

from mutants_config import CHANGED_EXCLUDE_GLOBS, DEFAULT_BASE_BRANCH  # noqa: E402


def git_changed_rs_files(
    repo_root: Path,
    base_branch: str = DEFAULT_BASE_BRANCH,
    workspace_dir: Optional[Path] = None,
) -> list[str]:
    """Find .rs source files changed on the current branch vs *base_branch*.

    Returns paths relative to the Cargo workspace root (e.g.
    ``src/pty_session/pty.rs``), excluding test-only binaries and hardware
    drivers listed in :data:`CHANGED_EXCLUDE_GLOBS`.
    """
    ws = workspace_dir or resolve_src_dir(repo_root)
    merge_base = _resolve_merge_base(repo_root, base_branch)

    committed = _diff_names(repo_root, merge_base, "HEAD")
    dirty = _diff_names(repo_root, "HEAD")
    all_paths = committed | dirty

    ws_prefix = _workspace_prefix(repo_root, ws)
    return _filter_rs_sources(all_paths, ws_prefix)


def _resolve_merge_base(repo_root: Path, base_branch: str) -> str:
    try:
        return subprocess.run(
            ["git", "merge-base", base_branch, "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        print(f"Warning: could not find merge-base with {base_branch}, falling back to {base_branch}")
        return base_branch


def _diff_names(repo_root: Path, *refs: str) -> set[str]:
    """Return changed file names between refs (or HEAD vs working tree)."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", *refs],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout.strip()
    return set(output.splitlines()) if output else set()


def _workspace_prefix(repo_root: Path, workspace_dir: Path) -> str:
    ws_rel = workspace_dir.resolve().relative_to(repo_root.resolve())
    return str(ws_rel) + "/"


def _filter_rs_sources(all_paths: set[str], ws_prefix: str) -> list[str]:
    rs_files = []
    for path in sorted(all_paths):
        if not path.endswith(".rs"):
            continue
        if not path.startswith(ws_prefix):
            continue
        rel = path[len(ws_prefix):]
        if rel in CHANGED_EXCLUDE_GLOBS:
            continue
        if "/tests/" in rel or rel.endswith("/tests.rs"):
            continue
        rs_files.append(rel)
    return rs_files
