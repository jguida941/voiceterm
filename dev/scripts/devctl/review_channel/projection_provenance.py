"""Shared provenance constants/helpers for review-state projections."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.surface_provenance import build_surface_source_identity

_PROVENANCE_REQUIRED_OBSERVED_FIELDS = ("head_sha", "worktree_hash")
STATUS_SOURCE_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json"
)
REVIEW_STATE_SOURCE_CONTRACT = "ReviewState"
PROVENANCE_OBSERVED_FIELDS = (*_PROVENANCE_REQUIRED_OBSERVED_FIELDS, "generation_id")
PROVENANCE_INFERRED_FIELDS = ("snapshot_id", "zref")


def projection_source_identity(
    *,
    typed_bridge_liveness: Mapping[str, object],
    generation_id: str,
    head_sha: str,
) -> dict[str, str]:
    """Return the canonical provenance identity for review-state emitters."""
    push_enforcement = typed_bridge_liveness.get("push_enforcement")
    push_enforcement = push_enforcement if isinstance(push_enforcement, Mapping) else {}
    return build_surface_source_identity(
        generation_id=generation_id,
        head_sha=head_sha,
        worktree_hash=str(
            push_enforcement.get("current_worktree_identity")
            or typed_bridge_liveness.get("last_worktree_hash")
            or ""
        ),
    )


def projection_observed_fields(
    *,
    source_identity: Mapping[str, object],
) -> tuple[str, ...]:
    """Return the provenance fields this projection can prove in source identity."""
    observed = list(_PROVENANCE_REQUIRED_OBSERVED_FIELDS)
    if str(source_identity.get("generation_id") or "").strip():
        observed.append("generation_id")
    return tuple(observed)
