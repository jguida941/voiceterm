"""Shared path filters used by review-probe scripts."""

from __future__ import annotations

from pathlib import Path

try:
    from rust_guard_common import is_test_path as is_rust_test_path
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.rust_guard_common import is_test_path as is_rust_test_path


def is_python_test_path(path: Path) -> bool:
    """Return True when a path is a Python test path."""
    normalized = f"/{path.as_posix().lstrip('/')}/"
    return path.name.startswith("test_") or "/tests/" in normalized or "/test/" in normalized


def is_review_probe_test_path(path: Path) -> bool:
    """Return True when a review probe should skip the path as test-only."""
    return is_python_test_path(path) or is_rust_test_path(path)
