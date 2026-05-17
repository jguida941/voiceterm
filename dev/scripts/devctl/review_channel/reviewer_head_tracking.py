"""Git HEAD tracking and review-range detection for reviewer checkpoints.

Provides ``current_head_sha`` to resolve the current commit and
``compute_review_range`` to detect when HEAD has drifted from the
last reviewer-checkpoint commit.  Both the checkpoint write path
and the follow-loop tick use these to record and surface the
reviewed commit range.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .handoff import extract_bridge_snapshot


def current_head_sha(repo_root: Path) -> str:
    """Return the full HEAD SHA, or empty string when git is unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def compute_review_range(
    *,
    repo_root: Path,
    bridge_path: Path,
) -> dict[str, object] | None:
    """Detect HEAD drift from the last reviewed commit.

    Reads ``head_at_push_time`` from bridge metadata (the SHA recorded at
    the last reviewer checkpoint) and compares it to the current HEAD.
    Returns a dict with ``last_reviewed_sha``, ``head_sha``, and a
    ``range`` string suitable for ``git diff`` / ``git log``.
    Returns None when no drift is detected or when the data is unavailable.
    """
    if not bridge_path.exists():
        return None
    bridge_text = bridge_path.read_text(encoding="utf-8")
    snapshot = extract_bridge_snapshot(bridge_text)
    last_reviewed_sha = (snapshot.metadata.get("head_at_push_time") or "").strip()
    if not last_reviewed_sha:
        return None
    head_sha = current_head_sha(repo_root)
    if not head_sha:
        return None
    if head_sha == last_reviewed_sha:
        return None
    return {
        "last_reviewed_sha": last_reviewed_sha,
        "head_sha": head_sha,
        "range": f"{last_reviewed_sha}..{head_sha}",
    }
