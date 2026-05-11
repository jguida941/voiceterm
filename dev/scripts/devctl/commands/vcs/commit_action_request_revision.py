"""Repository revision checks for commit action-request authority."""

from __future__ import annotations

from pathlib import Path

from .governed_executor_git import head_commit


def target_revision_freshness_block(
    *,
    repo_root: Path,
    grant: object,
) -> str:
    """Return a denial reason when packet revision evidence is stale."""
    head = _current_head(repo_root)
    target_ref = _text(getattr(grant, "target_ref", ""))
    target_revision = _text(getattr(grant, "target_revision", ""))
    target_ref_revision = target_ref.removeprefix("devctl_commit:")
    if target_revision and target_revision != head:
        return "action_request_target_revision_stale"
    if target_ref_revision and target_ref_revision != head:
        return "action_request_target_ref_stale"
    return ""


def _current_head(repo_root: Path) -> str:
    return head_commit(repo_root)


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["target_revision_freshness_block"]
