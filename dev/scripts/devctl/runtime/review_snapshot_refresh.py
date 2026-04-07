"""Shared helper for governed-executor snapshot refresh hooks.

Publish contract: the refresh runs *before* the governed ``git commit``
inside ``governed_executor_phases.execute_commit``. The helper regenerates
``dev/audits/REVIEW_SNAPSHOT.md`` and auto-stages it via ``git add`` so the
committed tree — and therefore the pushed commit on GitHub — actually
contains the refreshed projection. A post-commit refresh would only dirty
the worktree without publishing the file, which is the bug this module is
explicitly designed to prevent.

Initialization contract: the refresh is a no-op when the configured
snapshot file does not yet exist. Fresh adopter repos opt in by running
``python3 dev/scripts/devctl.py review-snapshot --write`` once; from that
point on every governed commit auto-refreshes the file in place. This
prevents the hook from creating untracked worktree files during tests and
during the first governed commit on a freshly-cloned adopter repo.

Failure contract: every failure class is caught and returned as a warning
string. The governed commit is irreversible once ``git commit`` has run,
so the refresh can never be allowed to raise through the commit path.
Callers fold the warnings into their existing ``ActionResult.warnings``.
"""

from __future__ import annotations

from pathlib import Path

from ..config import REPO_ROOT


def refresh_review_snapshot_file(
    *,
    repo_root: Path = REPO_ROOT,
    previous_head_sha: str = "",
) -> list[str]:
    """Regenerate the configured ReviewSnapshot file — returns a warnings list.

    Write discipline: the helper only writes the file when it already exists
    AND the new content differs from what's on disk. This gives two important
    properties:

    1. Fresh adopter repos and test fixtures never get an auto-created file
       (the user opts in via the first manual ``devctl review-snapshot --write``).
       Without this, the governed executor would create an untracked file as
       part of its commit/push flow and break the clean-worktree invariant.

    2. Production repos never write identical content back, so the worktree
       stays clean when the typed projection hasn't actually changed.

    Callers fold non-empty warnings into their existing warnings surface.
    Failures here never block the commit/push — commit already landed.
    """
    try:
        from .governance_scan import scan_repo_governance_safely
        from .review_snapshot import build_review_snapshot
        from .review_snapshot_render import render_review_snapshot_markdown
    except Exception as exc:  # pragma: no cover - import-time safety net
        return [f"review_snapshot_refresh_import_failed: {exc}"]

    try:
        governance = scan_repo_governance_safely(repo_root)
    except Exception:
        governance = None

    target_rel = _resolve_target(governance)
    target = repo_root / target_rel

    # Skip auto-refresh on fresh repos where the file isn't initialized yet.
    if not target.is_file():
        return []

    try:
        snapshot = build_review_snapshot(
            repo_root=repo_root,
            previous_head_sha=previous_head_sha,
        )
        markdown = render_review_snapshot_markdown(snapshot)
    except Exception as exc:
        return [f"review_snapshot_build_failed: {exc}"]

    try:
        existing = target.read_text(encoding="utf-8")
    except OSError:
        existing = None
    if existing == markdown:
        return []

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        return [f"review_snapshot_write_failed: {target_rel}: {exc}"]

    return []


def refresh_and_stage_review_snapshot(
    *,
    repo_root: Path = REPO_ROOT,
    previous_head_sha: str = "",
) -> list[str]:
    """Refresh the snapshot and ``git add`` it so it lands in the next commit.

    This is the canonical governed-commit hook: call it *before* the
    governed executor runs ``git commit``, so the committed tree contains
    the refreshed snapshot and the pushed commit on GitHub actually shows
    the updated review surface. A post-commit refresh cannot achieve this
    because the commit object is already sealed by the time the refresh
    would run.

    Returns any warning strings from refresh or staging — callers fold them
    into their existing warnings surface. Never raises.
    """
    warnings = refresh_review_snapshot_file(
        repo_root=repo_root,
        previous_head_sha=previous_head_sha,
    )
    if warnings:
        return warnings

    # Look up the live target path the refresh actually wrote (or would
    # have written). If the file still doesn't exist, nothing to stage —
    # this is the fresh-repo no-op case and it's not an error.
    try:
        from .governance_scan import scan_repo_governance_safely
    except Exception as exc:  # pragma: no cover - import-time safety net
        return [f"review_snapshot_stage_import_failed: {exc}"]

    try:
        governance = scan_repo_governance_safely(repo_root)
    except Exception:
        governance = None
    target_rel = _resolve_target(governance)
    target = repo_root / target_rel
    if not target.is_file():
        return []

    try:
        from .vcs import run_git_capture
    except Exception as exc:  # pragma: no cover - import-time safety net
        return [f"review_snapshot_stage_import_failed: {exc}"]

    code, _, stderr = run_git_capture(
        ["add", "--", target_rel],
        repo_root=repo_root,
    )
    if code != 0:
        return [
            f"review_snapshot_stage_failed: git add {target_rel} exited {code}: {stderr}"
        ]
    return []


def _resolve_target(governance: object) -> str:
    """Return the repo-relative snapshot write path, with safe default."""
    default = "dev/audits/REVIEW_SNAPSHOT.md"
    if governance is None:
        return default
    artifact_roots = getattr(governance, "artifact_roots", None)
    if artifact_roots is None:
        return default
    value = str(getattr(artifact_roots, "review_snapshot_path", "") or "").strip()
    return value or default


__all__ = ["refresh_and_stage_review_snapshot", "refresh_review_snapshot_file"]
