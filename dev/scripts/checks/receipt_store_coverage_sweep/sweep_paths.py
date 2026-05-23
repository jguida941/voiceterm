"""Path discovery helpers specific to the coverage-sweep guard.

The scope-dispatch outer body was extracted to
``dev/scripts/checks/_receipt_store_scope.resolve_store_paths_for_scope``
so this module only owns the sweep-specific ``all_*``/``changed_*`` and
``report_*`` helpers below.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

try:
    from ..receipt_store_consumer.git_status import git_changed_paths
except ImportError:
    from receipt_store_consumer.git_status import git_changed_paths  # type: ignore[no-redef]

try:
    from .._receipt_store_scope import resolve_store_paths_for_scope
except ImportError:  # pragma: no cover - direct-script fallback
    from _receipt_store_scope import resolve_store_paths_for_scope  # type: ignore[no-redef]


def store_paths_for_scope(*, repo_root: Path, scope: str, changed_paths: Sequence[str | Path] | None, warnings: list[str]) -> tuple[str, ...]:
    return resolve_store_paths_for_scope(repo_root=repo_root, scope=scope, changed_paths=changed_paths, warnings=warnings, all_paths_fn=all_receipt_store_paths, changed_paths_fn=changed_receipt_store_paths, git_changed_paths_fn=git_changed_paths)


def all_receipt_store_paths(repo_root: Path) -> tuple[str, ...]:
    paths: set[str] = set()
    state_dir = repo_root / "dev/state"
    if state_dir.exists():
        paths.update(repo_path(path, repo_root) for path in state_dir.glob("*.jsonl"))
    reports_dir = repo_root / "dev/reports"
    if reports_dir.exists():
        for path in reports_dir.rglob("*.jsonl"):
            paths.add(repo_path(path, repo_root))
        for directory in report_json_store_dirs(reports_dir):
            paths.add(repo_path(directory, repo_root))
    return tuple(sorted(paths))


def changed_receipt_store_paths(
    changed_paths: Sequence[Path],
    *,
    repo_root: Path,
) -> tuple[str, ...]:
    paths: set[str] = set()
    for changed_path in changed_paths:
        candidate = changed_path if changed_path.is_absolute() else repo_root / changed_path
        try:
            rel = repo_path(candidate, repo_root)
        except ValueError:
            continue
        if rel.startswith("dev/state/") and rel.endswith(".jsonl"):
            paths.add(rel)
        elif rel.startswith("dev/reports/") and rel.endswith(".jsonl"):
            paths.add(rel)
        elif rel.startswith("dev/reports/") and rel.endswith(".json"):
            paths.add(report_store_path_for_json(rel))
    return tuple(sorted(paths))


def report_json_store_dirs(reports_dir: Path) -> tuple[Path, ...]:
    dirs: set[Path] = set()
    for path in reports_dir.rglob("*.json"):
        rel_parts = path.relative_to(reports_dir).parts
        if not rel_parts:
            continue
        first = rel_parts[0]
        if "receipt" in first or first in {"dogfood", "push"}:
            dirs.add(reports_dir / first)
    return tuple(sorted(dirs))


def report_store_path_for_json(rel: str) -> str:
    parts = Path(rel).parts
    if len(parts) >= 3:
        return "/".join(parts[:3])
    return str(Path(rel).parent)


def repo_path(path: Path, repo_root: Path) -> str:
    return str(path.resolve().relative_to(repo_root.resolve()))
