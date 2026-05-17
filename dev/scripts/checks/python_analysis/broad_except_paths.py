"""Path-selection helpers for the Python broad-except guard."""

from __future__ import annotations

from pathlib import Path


def is_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")


def collect_python_paths(
    *,
    repo_root: Path,
    candidate_paths: list[Path],
    target_roots,
    is_under_target_roots_fn,
) -> tuple[list[Path], int]:
    paths: set[Path] = set()
    skipped_tests = 0
    for candidate in candidate_paths:
        if candidate.suffix != ".py":
            continue
        if not is_under_target_roots_fn(
            candidate,
            repo_root=repo_root,
            target_roots=target_roots,
        ):
            continue
        relative = candidate.relative_to(repo_root) if candidate.is_absolute() else candidate
        if is_test_path(relative):
            skipped_tests += 1
            continue
        paths.add(repo_root / candidate if not candidate.is_absolute() else candidate)
    return sorted(paths), skipped_tests
