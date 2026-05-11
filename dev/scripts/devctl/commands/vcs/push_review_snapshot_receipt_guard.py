"""Guards for ReviewSnapshot receipt auto-commit behavior."""

from __future__ import annotations

from pathlib import Path

from ...runtime.review_snapshot_refresh import _RECEIPT_SUBJECT_PREFIXES
from ...runtime.vcs import run_git_capture

MANAGED_REVIEW_SNAPSHOT_RECEIPT_PREFIXES = _RECEIPT_SUBJECT_PREFIXES


def current_head_is_managed_review_snapshot_receipt(*, repo_root: Path) -> bool:
    code, subject, _ = run_git_capture(
        ["show", "-s", "--format=%s", "HEAD"],
        repo_root=repo_root,
    )
    subject_text = str(subject or "")
    return code == 0 and subject_text.startswith(
        MANAGED_REVIEW_SNAPSHOT_RECEIPT_PREFIXES
    )


__all__ = [
    "MANAGED_REVIEW_SNAPSHOT_RECEIPT_PREFIXES",
    "current_head_is_managed_review_snapshot_receipt",
]
