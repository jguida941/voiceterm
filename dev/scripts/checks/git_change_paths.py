"""Shared git path-diff helpers for check scripts."""

from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess

try:
    from dev.scripts.devctl.quality_scan_mode import is_adoption_scan
except ModuleNotFoundError:  # pragma: no cover
    import sys

    try:
        from check_bootstrap import REPO_ROOT
    except ModuleNotFoundError:
        from dev.scripts.checks.check_bootstrap import REPO_ROOT
    repo_root_str = str(REPO_ROOT)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    from dev.scripts.devctl.quality_scan_mode import is_adoption_scan

try:
    from package_layout.compatibility_redirects import collect_compatibility_redirects
except ModuleNotFoundError:  # pragma: no cover - repo-package fallback
    from dev.scripts.checks.package_layout.compatibility_redirects import (
        collect_compatibility_redirects,
    )


def _resolve_repo_root(run_git) -> Path:
    result = run_git(["git", "rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip())


def _git_path_exists_at_ref(run_git, ref: str, path: Path) -> bool:
    spec = f"{ref}:{path.as_posix()}"
    result: CompletedProcess[str] = run_git(["git", "cat-file", "-e", spec], check=False)
    return result.returncode == 0


def _apply_compatibility_redirect_base_map(
    *,
    run_git,
    changed: set[Path],
    base_map: dict[Path, Path],
    since_ref: str | None,
    head_ref: str,
) -> None:
    if is_adoption_scan(since_ref=since_ref, head_ref=head_ref):
        return
    repo_root = _resolve_repo_root(run_git)
    base_ref = since_ref or "HEAD"
    for redirect in collect_compatibility_redirects(repo_root=repo_root):
        wrapper_path = Path(redirect["path"])
        target_text = str(redirect.get("resolved_target") or redirect.get("target") or "").strip()
        if not target_text:
            continue
        target_path = Path(target_text)
        if target_path not in changed:
            continue
        if base_map.get(target_path) not in {None, target_path}:
            continue
        if _git_path_exists_at_ref(run_git, base_ref, target_path):
            continue
        if not _git_path_exists_at_ref(run_git, base_ref, wrapper_path):
            continue
        base_map[target_path] = wrapper_path


def list_changed_paths_with_base_map(
    run_git, since_ref: str | None, head_ref: str
) -> tuple[list[Path], dict[Path, Path]]:
    """Return changed paths and baseline-path mapping with rename awareness.

    The returned mapping maps each current path to the path that should be used
    for baseline comparisons (`old -> new` for renames/copies, identity
    otherwise).
    """
    changed: set[Path] = set()
    base_map: dict[Path, Path] = {}

    if is_adoption_scan(since_ref=since_ref, head_ref=head_ref):
        tracked = run_git(["git", "ls-files"])
        untracked = run_git(["git", "ls-files", "--others", "--exclude-standard"])
        for result in (tracked, untracked):
            for line in result.stdout.splitlines():
                if line.strip():
                    path = Path(line.strip())
                    changed.add(path)
                    base_map.setdefault(path, path)
        return sorted(changed), base_map

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

    _apply_compatibility_redirect_base_map(
        run_git=run_git,
        changed=changed,
        base_map=base_map,
        since_ref=since_ref,
        head_ref=head_ref,
    )

    return sorted(changed), base_map
