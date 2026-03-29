"""Baseline-debt enforcement helpers for `check_package_layout.py`."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BaselineDebtSnapshot:
    """Resolved baseline-debt state for one package-layout report."""

    detected: bool
    roots: list[str] | None
    crowded_directories: list[dict]
    crowded_namespace_families: list[dict]


def _filter_baseline_debt_by_roots(
    crowded_directories: list[dict],
    crowded_namespace_families: list[dict],
    roots: list[str],
) -> tuple[list[dict], list[dict]]:
    """Return only crowded entries whose root matches one of the filter roots."""
    filtered_dirs = [item for item in crowded_directories if item["root"] in roots]
    filtered_families = [
        item for item in crowded_namespace_families if item["root"] in roots
    ]
    return filtered_dirs, filtered_families


def _changed_paths_touch_roots(
    changed_paths: list[object],
    *,
    repo_root: Path,
    roots: list[str],
) -> bool:
    """Return True when any changed path lives under one of the selected roots."""
    root_paths = tuple(repo_root / Path(root) for root in roots)
    for changed_path in changed_paths:
        path = changed_path if isinstance(changed_path, Path) else Path(str(changed_path))
        path_abs = path if path.is_absolute() else repo_root / path
        if any(path_abs == root or root in path_abs.parents for root in root_paths):
            return True
    return False


def resolve_baseline_debt_enforcement(
    *,
    repo_root: Path,
    changed_paths: list[object],
    fail_on_baseline_debt: bool,
    snapshot: BaselineDebtSnapshot,
) -> tuple[bool, list[dict], list[dict]]:
    """Return whether baseline debt should hard-fail plus the enforced entries."""
    if not fail_on_baseline_debt or not snapshot.detected:
        return False, [], []

    if not snapshot.roots:
        return bool(
            snapshot.crowded_directories or snapshot.crowded_namespace_families
        ), snapshot.crowded_directories, snapshot.crowded_namespace_families

    enforced_dirs, enforced_families = _filter_baseline_debt_by_roots(
        snapshot.crowded_directories,
        snapshot.crowded_namespace_families,
        snapshot.roots,
    )
    if not (enforced_dirs or enforced_families):
        return False, [], []
    if changed_paths and not _changed_paths_touch_roots(
        changed_paths,
        repo_root=repo_root,
        roots=snapshot.roots,
    ):
        return False, [], []
    return True, enforced_dirs, enforced_families
