"""Backward-compat support surface for broad-except helpers."""

from __future__ import annotations

try:
    from .broad_except_contracts import has_fallback_contract, has_rationale
    from .broad_except_diff import diff_added_lines
    from .broad_except_paths import collect_python_paths
except ImportError:  # pragma: no cover
    from broad_except_contracts import has_fallback_contract, has_rationale
    from broad_except_diff import diff_added_lines
    from broad_except_paths import collect_python_paths

__all__ = [
    "collect_python_paths",
    "diff_added_lines",
    "has_fallback_contract",
    "has_rationale",
]
