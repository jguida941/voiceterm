"""Path resolution for the receipt-store consumer guard.

The scope-dispatch outer body was extracted to
``dev/scripts/checks/_receipt_store_scope.resolve_store_paths_for_scope`` so
the consumer and coverage-sweep guards share a single dispatcher even
though their scope-specific helpers differ.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .git_status import git_changed_paths

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
        for path in state_dir.glob("*.jsonl"):
            paths.add(repo_path(path, repo_root))
    feature_proof_dir = repo_root / "dev/reports/feature_proof_receipts"
    if feature_proof_dir.exists():
        paths.add("dev/reports/feature_proof_receipts")
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
        elif rel.startswith("dev/reports/feature_proof_receipts/") and rel.endswith(".json"):
            paths.add("dev/reports/feature_proof_receipts")
    return tuple(sorted(paths))


def repo_path(path: Path, repo_root: Path) -> str:
    return str(path.resolve().relative_to(repo_root.resolve()))
