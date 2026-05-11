"""ReviewSnapshot receipt refresh for governed push preflight."""

from __future__ import annotations

import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from ...common import run_cmd
from ...runtime.vcs import run_git_capture
from .push_receipt_failure import review_snapshot_receipt_failure_detail
from .push_review_snapshot_receipt_guard import (
    current_head_is_managed_review_snapshot_receipt,
)


@dataclass(frozen=True)
class ReviewSnapshotReceiptRefreshResult:
    """Report from the managed review-snapshot receipt refresh step."""

    ok: bool
    committed: bool
    commit_sha: str = ""
    reason: str | None = None
    step: object | None = None
    returncode: object | None = None
    error: str | None = None
    error_detail: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            key: value
            for key, value in asdict(self).items()
            if value is not None
        }


def auto_commit_review_snapshot_freshness_receipt(
    state,
    *,
    command_runner=run_cmd,
    repo_root: Path,
    next_step_label: str,
) -> dict[str, object]:
    """Run the governed snapshot receipt command after managed HEAD movement."""
    if current_head_is_managed_review_snapshot_receipt(repo_root=repo_root):
        return ReviewSnapshotReceiptRefreshResult(
            ok=True,
            committed=False,
            reason="already_managed_review_snapshot_receipt",
        ).to_dict()
    before_head = current_head_sha(repo_root=repo_root)
    step = command_runner(
        "push-refresh-review-snapshot-receipt",
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "review-snapshot",
            "--write",
            "--receipt-commit",
            "--format",
            "json",
        ],
        cwd=repo_root,
    )
    if step.get("returncode", 1) != 0:
        detail = review_snapshot_receipt_failure_detail(step)
        message = f"ReviewSnapshot receipt refresh failed before {next_step_label}"
        if detail:
            message = f"{message}: {detail}"
        state.errors.append(message)
        return ReviewSnapshotReceiptRefreshResult(
            ok=False,
            committed=False,
            step=step,
            returncode=step.get("returncode"),
            error=message,
            error_detail=detail,
        ).to_dict()

    after_head = current_head_sha(repo_root=repo_root)
    committed = bool(after_head and after_head != before_head)
    if committed:
        state.warnings.append(
            "Committed ReviewSnapshot freshness receipt "
            f"{after_head[:12]} before {next_step_label}."
        )
    return ReviewSnapshotReceiptRefreshResult(
        ok=True,
        committed=committed,
        commit_sha=after_head if committed else "",
        step=step,
    ).to_dict()


def current_head_sha(*, repo_root: Path) -> str:
    code, stdout, _ = run_git_capture(["rev-parse", "HEAD"], repo_root=repo_root)
    return stdout.strip() if code == 0 else ""


__all__ = [
    "auto_commit_review_snapshot_freshness_receipt",
    "current_head_sha",
]
