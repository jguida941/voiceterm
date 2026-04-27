"""Shared helper for governed-executor snapshot refresh hooks.

Publish contract: the refresh runs *before* approval-bound staging in
``devctl commit``. The helper regenerates ``dev/audits/REVIEW_SNAPSHOT.md``
and auto-stages it via ``git add`` so the approved tree hash already includes
the refreshed projection. A post-commit *write* would only dirty the worktree
without publishing the file, so the post-commit publication path lives in
``devctl review-snapshot --receipt-commit`` and creates a snapshot-only
receipt commit instead.

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

import json
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from ..config import REPO_ROOT
from ..repo_packs import active_path_config

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance


_RECEIPT_SUBJECT_PREFIX = "Refresh external review snapshot for "
GENERATED_SURFACE_RECEIPT_SUBJECT_PREFIX = (
    "Refresh policy-owned generated surfaces for "
)
_RECEIPT_SUBJECT_PREFIXES = (
    _RECEIPT_SUBJECT_PREFIX,
    GENERATED_SURFACE_RECEIPT_SUBJECT_PREFIX,
)


class _ReviewSnapshotArtifactRoots(Protocol):
    review_snapshot_path: str


class _GovernanceWithArtifactRoots(Protocol):
    artifact_roots: _ReviewSnapshotArtifactRoots | None


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
    """Refresh the snapshot and ``git add`` it before approval-bound staging.

    This is the canonical governed-commit pre-stage hook: call it before the
    pipeline mints the staged tree hash and before remote/local approval binds
    that tree. Use ``review-snapshot --receipt-commit`` for the separate
    post-commit receipt path; a plain post-commit write is still invalid
    because the commit object is already sealed.

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


def _resolve_target(governance: "ProjectGovernance | None") -> str:
    """Return the repo-relative snapshot write path, with safe default."""
    default = "dev/audits/REVIEW_SNAPSHOT.md"
    if governance is None:
        return default
    value = str(governance.artifact_roots.review_snapshot_path or "").strip()
    return value or default


def receipt_commit_parent_sha(
    *,
    repo_root: Path = REPO_ROOT,
    current_head: str = "HEAD",
    governance: _GovernanceWithArtifactRoots | None = None,
) -> str:
    """Return the content parent behind governed receipt commits.

    Receipt commits may stack when push preflight refreshes bridge/snapshot
    projections more than once before publication. Treat the whole contiguous
    receipt chain as managed movement and return the first non-receipt parent.
    """
    ancestors = receipt_commit_ancestor_shas(
        repo_root=repo_root,
        current_head=current_head,
        governance=governance,
    )
    return ancestors[-1] if ancestors else ""


def receipt_commit_ancestor_shas(
    *,
    repo_root: Path = REPO_ROOT,
    current_head: str = "HEAD",
    governance: _GovernanceWithArtifactRoots | None = None,
) -> tuple[str, ...]:
    """Return each parent in a contiguous governed receipt chain."""
    target = str(current_head or "").strip() or "HEAD"
    seen: set[str] = set()
    ancestors: list[str] = []
    for _ in range(32):
        if target in seen:
            return tuple(ancestors)
        seen.add(target)
        next_parent = _single_receipt_commit_parent_sha(
            repo_root=repo_root,
            current_head=target,
            governance=governance,
        )
        if not next_parent:
            return tuple(ancestors)
        ancestors.append(next_parent)
        target = next_parent
    return tuple(ancestors)


def _single_receipt_commit_parent_sha(
    *,
    repo_root: Path,
    current_head: str,
    governance: _GovernanceWithArtifactRoots | None,
) -> str:
    """Return HEAD^ when one commit is a governed snapshot receipt."""
    try:
        from .vcs import run_git_capture
    # broad-except: allow reason=receipt-parent helper must fail closed when git runtime helpers are unavailable fallback=return empty parent SHA
    except Exception:
        return ""

    target = str(current_head or "").strip() or "HEAD"
    code, subject, _ = run_git_capture(
        ["show", "-s", "--format=%s", target],
        repo_root=repo_root,
    )
    if code != 0 or not str(subject or "").startswith(_RECEIPT_SUBJECT_PREFIXES):
        return ""

    allowlist = set(receipt_artifact_relpaths(governance))
    allowlist.update(_tracked_render_surface_relpaths(repo_root=repo_root))
    code, output, _ = run_git_capture(
        ["diff-tree", "--no-commit-id", "--name-only", "-r", target],
        repo_root=repo_root,
    )
    if code != 0:
        return ""
    changed_paths = {line.strip() for line in output.splitlines() if line.strip()}
    if not changed_paths:
        return ""
    if any(path not in allowlist for path in changed_paths):
        return ""

    parent_code, parent_sha, _ = run_git_capture(
        ["rev-parse", f"{target}^"],
        repo_root=repo_root,
    )
    if parent_code != 0:
        return ""
    return parent_sha.strip()


def receipt_artifact_relpaths(
    governance: _GovernanceWithArtifactRoots | None,
) -> tuple[str, ...]:
    """Return the governed artifact paths a receipt commit may touch."""
    snapshot_rel = _resolve_receipt_snapshot_target(governance)
    bridge_rel = str(active_path_config().bridge_rel or "").strip()
    paths = [snapshot_rel]
    if bridge_rel and bridge_rel != snapshot_rel:
        paths.append(bridge_rel)
    return tuple(paths)


def _tracked_render_surface_relpaths(*, repo_root: Path) -> tuple[str, ...]:
    """Return tracked repo-pack render targets accepted as managed receipts."""
    policy_path = repo_root / "dev/config/devctl_repo_policy.json"
    try:
        payload = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    governance = payload.get("repo_governance")
    if not isinstance(governance, dict):
        return ()
    surface_generation = governance.get("surface_generation")
    if not isinstance(surface_generation, dict):
        return ()
    surfaces = surface_generation.get("surfaces")
    if not isinstance(surfaces, list):
        return ()
    paths = [
        str(entry.get("output_path") or "").strip()
        for entry in surfaces
        if isinstance(entry, dict)
        and bool(entry.get("tracked", False))
        and not bool(entry.get("local_only", False))
    ]
    return tuple(dict.fromkeys(path for path in paths if path))


def _resolve_receipt_snapshot_target(
    governance: _GovernanceWithArtifactRoots | None,
) -> str:
    if governance is None:
        return "dev/audits/REVIEW_SNAPSHOT.md"
    artifact_roots = governance.artifact_roots
    if artifact_roots is None:
        return "dev/audits/REVIEW_SNAPSHOT.md"
    value = str(artifact_roots.review_snapshot_path or "").strip()
    return value or "dev/audits/REVIEW_SNAPSHOT.md"


__all__ = [
    "GENERATED_SURFACE_RECEIPT_SUBJECT_PREFIX",
    "receipt_commit_ancestor_shas",
    "receipt_artifact_relpaths",
    "receipt_commit_parent_sha",
    "refresh_and_stage_review_snapshot",
    "refresh_review_snapshot_file",
]
