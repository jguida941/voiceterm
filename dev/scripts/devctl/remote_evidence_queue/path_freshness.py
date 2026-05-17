"""Resolve whether remote finding evidence still applies to the current tree."""

from __future__ import annotations

from pathlib import Path

from ..publication_sync.git import list_changed_paths, run_git
from ..runtime.finding_contracts import FindingRecord
from .models import AffectedPathPresence, RemoteEvidenceFreshness


def find_finding_affected_paths_in_current_tree(
    finding: FindingRecord,
    applies_to_tree: str,
    current_tree: str,
    *,
    repo_root: Path,
) -> AffectedPathPresence:
    """Determine whether a finding's path still exists in the current tree.

    This is the minimal "working backward" primitive for stale remote proof:
    evidence from an older tree can remain actionable when the affected path
    still exists or was renamed in the current tree.
    """
    path = _normalize_path(finding.file_path)
    if not path:
        return "absent"
    source_ref = _normalize_ref(applies_to_tree)
    target_ref = _normalize_ref(current_tree)
    if _path_exists_at_ref(repo_root, target_ref, path):
        # Keep the changed-path query in the decision path so callers can rely
        # on one substrate for both "changed since proof" and presence checks.
        list_changed_paths(repo_root, source_ref, target_ref)
        return "present"
    if _renamed_path_exists(repo_root, source_ref, target_ref, path):
        return "moved"
    return "absent"


def freshness_for_finding_in_current_tree(
    finding: FindingRecord,
    applies_to_tree: str,
    current_tree: str,
    *,
    repo_root: Path,
) -> RemoteEvidenceFreshness:
    """Project path presence into RemoteValidationReceipt freshness."""
    source_ref = _normalize_ref(applies_to_tree)
    target_ref = _normalize_ref(current_tree)
    presence = find_finding_affected_paths_in_current_tree(
        finding,
        source_ref,
        target_ref,
        repo_root=repo_root,
    )
    if presence == "absent":
        return "stale_and_superseded"
    if source_ref == target_ref:
        return "current"
    return "stale_but_relevant"


def _path_exists_at_ref(repo_root: Path, ref: str, path: str) -> bool:
    try:
        run_git(repo_root, "cat-file", "-e", f"{ref}:{path}")
    except ValueError:
        return False
    return True


def _renamed_path_exists(
    repo_root: Path,
    source_ref: str,
    target_ref: str,
    old_path: str,
) -> bool:
    try:
        output = run_git(
            repo_root,
            "diff",
            "--name-status",
            "--find-renames",
            f"{source_ref}..{target_ref}",
            "--",
        )
    except ValueError:
        return False
    for line in output.splitlines():
        parts = [part.strip() for part in line.split("\t") if part.strip()]
        if len(parts) < 3 or not parts[0].startswith("R"):
            continue
        if parts[1] == old_path and _path_exists_at_ref(repo_root, target_ref, parts[2]):
            return True
    return False


def _normalize_path(value: str) -> str:
    path = str(value or "").strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path.strip("/")


def _normalize_ref(value: str) -> str:
    ref = str(value or "").strip()
    if not ref:
        raise ValueError("tree ref is required")
    return ref


__all__ = [
    "find_finding_affected_paths_in_current_tree",
    "freshness_for_finding_in_current_tree",
]
