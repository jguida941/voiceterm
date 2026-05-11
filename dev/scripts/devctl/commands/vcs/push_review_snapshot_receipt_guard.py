"""Guards for ReviewSnapshot receipt auto-commit behavior."""

from __future__ import annotations

from pathlib import Path

from ...runtime.vcs import run_git_capture

EXTERNAL_REVIEW_SNAPSHOT_RECEIPT_PREFIX = "Refresh external review snapshot for "


def current_head_is_external_review_snapshot_receipt(*, repo_root: Path) -> bool:
    code, subject, _ = run_git_capture(
        ["show", "-s", "--format=%s", "HEAD"],
        repo_root=repo_root,
    )
    return code == 0 and str(subject or "").startswith(
        EXTERNAL_REVIEW_SNAPSHOT_RECEIPT_PREFIX
    )


__all__ = [
    "EXTERNAL_REVIEW_SNAPSHOT_RECEIPT_PREFIX",
    "current_head_is_external_review_snapshot_receipt",
]
