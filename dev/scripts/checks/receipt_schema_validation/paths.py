"""Path resolution and feature-proof receipt discovery."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .git_status import git_changed_paths


def feature_proof_paths_for_scope(
    *,
    feature_proof_dir: Path,
    repo_root: Path,
    scope: str,
    changed_paths: Sequence[str | Path] | None,
    warnings: list[str],
) -> tuple[Path, ...]:
    if scope == "all":
        return feature_proof_paths(feature_proof_dir, warnings)
    if scope != "changed":
        warnings.append(f"unknown scope {scope!r}; defaulting to changed")
    paths = (
        tuple(Path(path) for path in changed_paths)
        if changed_paths is not None
        else git_changed_paths(repo_root, warnings)
    )
    return changed_feature_proof_paths(
        paths,
        feature_proof_dir=feature_proof_dir,
        repo_root=repo_root,
    )


def feature_proof_paths(root: Path, warnings: list[str]) -> tuple[Path, ...]:
    if not root.exists():
        warnings.append(f"feature proof directory missing: {root}")
        return ()
    return tuple(sorted(path for path in root.glob("*.json") if path.is_file()))


def changed_feature_proof_paths(
    changed_paths: Sequence[Path],
    *,
    feature_proof_dir: Path,
    repo_root: Path,
) -> tuple[Path, ...]:
    resolved_dir = feature_proof_dir.resolve()
    paths: list[Path] = []
    for changed_path in changed_paths:
        candidate = changed_path if changed_path.is_absolute() else repo_root / changed_path
        try:
            resolved = candidate.resolve()
            resolved.relative_to(resolved_dir)
        except (OSError, ValueError):
            continue
        if resolved.suffix == ".json" and resolved.is_file():
            paths.append(resolved)
    return tuple(sorted(set(paths)))


def repo_relative(path: Path, repo_root: Path) -> Path:
    try:
        return path.resolve().relative_to(repo_root.resolve())
    except (OSError, ValueError):
        return path
