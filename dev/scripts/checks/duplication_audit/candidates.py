"""Candidate-path helpers for the duplication-audit script."""

from __future__ import annotations

import subprocess
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import REPO_ROOT


def _normalize_candidate_paths(explicit_paths: list[str] | None) -> list[Path]:
    if not explicit_paths:
        return []
    return sorted(Path(path) for path in explicit_paths)


def _discover_new_paths(
    *,
    since_ref: str | None,
    head_ref: str,
) -> tuple[list[Path], list[str]]:
    errors: list[str] = []
    paths: set[Path] = set()
    diff_cmd = ["git", "diff", "--name-only", "--diff-filter=A"]
    if since_ref:
        diff_cmd.extend([since_ref, head_ref])
    else:
        diff_cmd.append("HEAD")
    diff_proc = subprocess.run(
        diff_cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if diff_proc.returncode != 0:
        errors.append(diff_proc.stderr.strip() or "git diff failed")
    else:
        paths.update(Path(line.strip()) for line in diff_proc.stdout.splitlines() if line.strip())

    untracked_proc = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if untracked_proc.returncode != 0:
        errors.append(untracked_proc.stderr.strip() or "git ls-files failed")
    else:
        paths.update(
            Path(line.strip()) for line in untracked_proc.stdout.splitlines() if line.strip()
        )
    return sorted(paths), errors


def _shared_logic_candidate_paths(args) -> tuple[list[Path], list[str]]:
    explicit_paths = _normalize_candidate_paths(args.paths)
    if explicit_paths:
        return explicit_paths, []
    return _discover_new_paths(since_ref=args.since_ref, head_ref=args.head_ref)


def _should_require_duplication_report(args, report_path: Path) -> bool:
    if args.check_shared_logic and not args.run_jscpd and not report_path.exists():
        return False
    return True
