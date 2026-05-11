"""Baseline-debt enforcement helpers for `check_package_layout.py`."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

if __package__:
    from .bootstrap import STANDARD_SHIM_METADATA_FIELDS, detect_compatibility_shim
else:  # pragma: no cover - standalone script fallback
    from bootstrap import STANDARD_SHIM_METADATA_FIELDS, detect_compatibility_shim


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


def _changed_paths_worsen_layout_debt(
    changed_paths: list[object],
    *,
    repo_root: Path,
    crowded_directories: list[dict],
    crowded_namespace_families: list[dict],
) -> bool:
    """Return True when a changed path adds to an already-crowded flat surface."""
    crowded_roots = tuple(Path(item["root"]) for item in crowded_directories)
    crowded_families = tuple(
        (Path(item["root"]), str(item.get("flat_prefix") or ""))
        for item in crowded_namespace_families
    )
    for changed_path in changed_paths:
        path = changed_path if isinstance(changed_path, Path) else Path(str(changed_path))
        relative = path.relative_to(repo_root) if path.is_absolute() else path
        worktree_path = repo_root / relative
        if not worktree_path.exists():
            continue
        if detect_compatibility_shim(
            worktree_path,
            namespace_subdir="",
            shim_required_metadata_fields=STANDARD_SHIM_METADATA_FIELDS,
        ).is_valid:
            continue
        if any(relative.parent == root for root in crowded_roots):
            return True
        for root, flat_prefix in crowded_families:
            if relative.parent == root and relative.name.startswith(flat_prefix):
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
        if changed_paths and not _changed_paths_worsen_layout_debt(
            changed_paths,
            repo_root=repo_root,
            crowded_directories=snapshot.crowded_directories,
            crowded_namespace_families=snapshot.crowded_namespace_families,
        ):
            return False, [], []
        return (
            bool(snapshot.crowded_directories or snapshot.crowded_namespace_families),
            snapshot.crowded_directories,
            snapshot.crowded_namespace_families,
        )

    enforced_dirs, enforced_families = _filter_baseline_debt_by_roots(
        snapshot.crowded_directories,
        snapshot.crowded_namespace_families,
        snapshot.roots,
    )
    if not (enforced_dirs or enforced_families):
        return False, [], []
    if changed_paths and not _changed_paths_worsen_layout_debt(
        changed_paths,
        repo_root=repo_root,
        crowded_directories=enforced_dirs,
        crowded_namespace_families=enforced_families,
    ):
        return False, [], []
    return True, enforced_dirs, enforced_families
