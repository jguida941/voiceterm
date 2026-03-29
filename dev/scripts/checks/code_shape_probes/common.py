"""Shared helpers for the code-shape probe package."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from check_bootstrap import REPO_ROOT, is_under_target_roots
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, is_under_target_roots


def extract_rust_signature(lines: list[str], func: dict[str, Any]) -> str:
    """Extract a multi-line Rust function signature through the opening brace."""
    start = int(func["start_line"]) - 1
    sig_lines: list[str] = []
    for index in range(start, min(start + 15, len(lines))):
        sig_lines.append(lines[index])
        if "{" in lines[index]:
            break
    return " ".join(sig_lines)


def should_scan_python_probe_path(
    path: Path,
    *,
    target_roots: tuple[Path, ...],
    is_review_probe_test_path,
) -> bool:
    """Return whether a Python path is in-scope for a review probe."""
    if path.suffix != ".py":
        return False
    if not is_under_target_roots(path, repo_root=REPO_ROOT, target_roots=target_roots):
        return False
    return not is_review_probe_test_path(path)


def load_probe_text(
    path: Path,
    *,
    guard,
    since_ref: str | None,
    head_ref: str,
) -> str | None:
    """Read probe input text from the current worktree or a comparison ref."""
    if since_ref:
        return guard.read_text_from_ref(path, head_ref)
    return guard.read_text_from_worktree(path)
