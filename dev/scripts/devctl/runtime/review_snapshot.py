"""ReviewSnapshot builder - orchestrates typed sources into one projection.

This module keeps the public build entrypoint stable and delegates the shape
heavy helpers to sibling runtime modules so the review-snapshot surface stays
under the code-shape soft limit without changing behavior.
"""

from __future__ import annotations

from pathlib import Path

from ..config import REPO_ROOT
from .review_snapshot_git import commits_between
from .review_snapshot_models import ReviewSnapshot
from .review_snapshot_sections import (
    build_architecture,
    build_delta,
    build_known_gaps,
    build_quality,
    build_reasoning,
    build_reviewer_hints,
)
from .review_snapshot_sources import (
    safe_context_graph_bootstrap,
    safe_governance_report,
    safe_project_governance,
    safe_probe_report,
    safe_startup_context,
)
from .review_snapshot_state import (
    attach_generation_stamp,
    build_governance_state,
    build_identity,
)


def build_review_snapshot(
    *,
    repo_root: Path = REPO_ROOT,
    previous_head_sha: str = "",
    startup_payload: dict[str, object] | None = None,
    governance_payload: dict[str, object] | None = None,
    probe_payload: dict[str, object] | None = None,
    context_graph_payload: dict[str, object] | None = None,
    commit_limit: int = 25,
) -> ReviewSnapshot:
    """Return a typed ReviewSnapshot projecting current repo governance state."""
    startup = (
        startup_payload if startup_payload is not None else safe_startup_context(repo_root)
    )
    governance_contract = safe_project_governance(repo_root)
    governance_summary = (
        governance_payload
        if governance_payload is not None
        else safe_governance_report(repo_root, governance_contract)
    )
    probe_summary = (
        probe_payload if probe_payload is not None else safe_probe_report()
    )
    graph_bootstrap = (
        context_graph_payload
        if context_graph_payload is not None
        else safe_context_graph_bootstrap()
    )

    identity = build_identity(
        repo_root=repo_root,
        startup=startup,
        previous_head_sha=previous_head_sha,
    )
    governance_state = build_governance_state(startup=startup)
    raw_commits = commits_between(
        repo_root,
        from_sha=previous_head_sha or identity.previous_snapshot_head_sha,
        to_sha=identity.head_sha or "HEAD",
        limit=commit_limit,
    )
    delta = build_delta(
        repo_root=repo_root,
        raw_commits=raw_commits,
        identity=identity,
        previous_head_sha=previous_head_sha or identity.previous_snapshot_head_sha,
    )
    quality = build_quality(
        governance_summary=governance_summary,
        probe_summary=probe_summary,
    )
    architecture = build_architecture(
        startup=startup,
        graph_bootstrap=graph_bootstrap,
        governance_contract=governance_contract,
    )
    reviewer_hints = build_reviewer_hints(delta=delta)
    reasoning = build_reasoning(repo_root=repo_root, raw_commits=raw_commits)
    known_gaps = build_known_gaps(
        startup=startup,
        governance_summary=governance_summary,
        quality=quality,
    )
    identity = attach_generation_stamp(identity, governance_state, delta, quality)
    return ReviewSnapshot(
        identity=identity,
        governance_state=governance_state,
        delta=delta,
        quality=quality,
        architecture=architecture,
        reviewer_hints=reviewer_hints,
        reasoning=reasoning,
        known_gaps=known_gaps,
    )


__all__ = ["build_review_snapshot"]
