"""Repo-wide source file counter for governance-quality density metrics.

Intentionally independent from Halstead analysis so the denominator used
by ``finding_density`` stays stable regardless of Halstead sample caps.
"""

from __future__ import annotations

from pathlib import Path


def count_source_files(
    root: Path,
    *,
    extensions: tuple[str, ...] = (".py", ".rs"),
    exclude_patterns: tuple[str, ...] = ("__pycache__", ".git", "target", "node_modules"),
) -> int:
    """Count repo source files eligible for governance-quality density metrics.

    This function intentionally has no ``max_files`` parameter.  The count
    must remain a stable repo-wide total so ``finding_density`` uses a
    consistent denominator regardless of Halstead sample caps.
    """
    count = 0
    for ext in extensions:
        for path in sorted(root.rglob(f"*{ext}")):
            if any(part in exclude_patterns for part in path.parts):
                continue
            count += 1
    return count
