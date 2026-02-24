"""Shared git path-diff helpers for check scripts."""

from __future__ import annotations

from pathlib import Path


def list_changed_paths_with_base_map(run_git, since_ref: str | None, head_ref: str) -> tuple[list[Path], dict[Path, Path]]:
    """Return changed paths and baseline-path mapping with rename awareness.

    The returned mapping maps each current path to the path that should be used
    for baseline comparisons (`old -> new` for renames/copies, identity
    otherwise).
    """
    if since_ref:
        diff_cmd = [
            "git",
            "diff",
            "--name-status",
            "--find-renames=50%",
            "--diff-filter=ACMR",
            since_ref,
            head_ref,
        ]
    else:
        diff_cmd = [
            "git",
            "diff",
            "--name-status",
            "--find-renames=50%",
            "--diff-filter=ACMR",
            "HEAD",
        ]

    changed: set[Path] = set()
    base_map: dict[Path, Path] = {}

    for raw_line in run_git(diff_cmd).stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue

        status = parts[0]
        if status.startswith(("R", "C")) and len(parts) >= 3:
            base_path = Path(parts[1].strip())
            current_path = Path(parts[2].strip())
        else:
            base_path = Path(parts[1].strip())
            current_path = base_path

        changed.add(current_path)
        base_map[current_path] = base_path

    if since_ref is None:
        untracked = run_git(["git", "ls-files", "--others", "--exclude-standard"])
        for line in untracked.stdout.splitlines():
            if line.strip():
                path = Path(line.strip())
                changed.add(path)
                base_map.setdefault(path, path)

    return sorted(changed), base_map
