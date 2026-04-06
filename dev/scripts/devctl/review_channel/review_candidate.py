"""Typed review-candidate builder for dirty-tree and commit-range handoff."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from ..runtime.review_state_models import (
    ReviewCandidateRecord,
    ReviewCurrentSessionState,
    review_candidate_from_mapping,
)
from ..runtime.review_state_semantics import is_pending_implementer_state
from ..time_utils import utc_timestamp
from .candidate_parse import (
    completion_claimed as _completion_claimed,
    extract_execution_commands as _extract_execution_commands,
    extract_scope_paths as _extract_scope_paths,
)
from .candidate_paths import resolve_changed_paths as _resolve_changed_paths
from .reviewer_head_tracking import current_head_sha


def build_review_candidate(
    *,
    repo_root: Path,
    current_session: ReviewCurrentSessionState,
    bridge_liveness: Mapping[str, object],
    prior_review_state: Mapping[str, object] | None,
) -> ReviewCandidateRecord | None:
    """Build the current frozen review target, invalidating stale prior targets."""
    prior_candidate = _prior_candidate(prior_review_state)
    artifact_kind, changed_paths = _resolve_changed_paths(
        repo_root=repo_root,
        base_sha=str(bridge_liveness.get("head_at_push_time") or "").strip(),
    )
    head_sha = current_head_sha(repo_root)
    worktree_hash = str(bridge_liveness.get("last_worktree_hash") or "").strip()
    implementer_status_written = _implementer_status_written(current_session)
    tests_run, guards_run = _extract_execution_commands(current_session)
    completion = _completion_claimed(
        current_session=current_session,
        tests_run=tests_run,
        guards_run=guards_run,
    )
    scope_paths = _extract_scope_paths(
        current_session.current_instruction,
        current_session.last_reviewed_scope,
    )
    missing_scope_paths = tuple(
        path for path in scope_paths if path not in set(changed_paths)
    )

    if prior_candidate is not None and _same_candidate_state(
        prior_candidate,
        current_session=current_session,
    ):
        if _target_drifted(
            prior_candidate,
            head_sha=head_sha,
            worktree_hash=worktree_hash,
            changed_paths=changed_paths,
        ):
            return replace(
                prior_candidate,
                ready_for_review=False,
                valid=False,
                invalidation_reason="worktree_drift_after_candidate",
                missing_scope_paths=missing_scope_paths,
            )
        return replace(
            prior_candidate,
            scope_paths=scope_paths,
            missing_scope_paths=missing_scope_paths,
        )

    if not completion:
        return None

    base_sha = str(bridge_liveness.get("head_at_push_time") or "").strip()
    candidate_id = _candidate_id(
        instruction_revision=current_session.current_instruction_revision,
        artifact_kind=artifact_kind,
        base_sha=base_sha,
        head_sha=head_sha,
        worktree_hash=worktree_hash,
        changed_paths=changed_paths,
        implementer_state_hash=current_session.implementer_state_hash,
    )
    valid, invalidation_reason = _validate_candidate(
        artifact_kind=artifact_kind,
        changed_paths=changed_paths,
        worktree_hash=worktree_hash,
        missing_scope_paths=missing_scope_paths,
    )
    return ReviewCandidateRecord(
        candidate_id=candidate_id,
        instruction_revision=current_session.current_instruction_revision,
        artifact_kind=artifact_kind,
        base_sha=base_sha,
        head_sha=head_sha,
        worktree_hash=worktree_hash,
        changed_paths=changed_paths,
        tests_run=tests_run,
        guards_run=guards_run,
        implementer_status_written=implementer_status_written,
        ready_for_review=valid,
        valid=valid,
        invalidation_reason=invalidation_reason,
        implementer_state_hash=current_session.implementer_state_hash,
        emitted_at_utc=utc_timestamp(),
        scope_paths=scope_paths,
        missing_scope_paths=missing_scope_paths,
    )


def review_candidate_error(
    *,
    current_session: ReviewCurrentSessionState,
    candidate: ReviewCandidateRecord | None,
) -> str | None:
    """Return a fail-closed bridge/runtime error for missing or stale review targets."""
    tests_run, guards_run = _extract_execution_commands(current_session)
    if not _completion_claimed(
        current_session=current_session,
        tests_run=tests_run,
        guards_run=guards_run,
    ):
        return None
    if candidate is None:
        return (
            "Claude Status/Ack claim a completed review-ready slice, but no typed "
            "`ReviewCandidateRecord` exists yet. Emit one frozen review target "
            "through the repo-owned status/session-resume path before reviewer "
            "bootstrap continues."
        )
    if candidate.valid:
        return None
    detail = candidate.invalidation_reason or "candidate_invalid"
    if candidate.missing_scope_paths:
        missing = ", ".join(f"`{path}`" for path in candidate.missing_scope_paths)
        return (
            "Current reviewer target is stale or wrong: the instruction names "
            f"scoped paths missing from the candidate diff ({missing})."
        )
    return (
        "Claude Status/Ack claim a completed review-ready slice, but the typed "
        f"`ReviewCandidateRecord` is invalid (`{detail}`)."
    )


def _prior_candidate(
    prior_review_state: Mapping[str, object] | None,
) -> ReviewCandidateRecord | None:
    if not isinstance(prior_review_state, Mapping):
        return None
    return review_candidate_from_mapping(prior_review_state.get("review_candidate"))


def _same_candidate_state(
    prior_candidate: ReviewCandidateRecord,
    *,
    current_session: ReviewCurrentSessionState,
) -> bool:
    return (
        prior_candidate.instruction_revision == current_session.current_instruction_revision
        and prior_candidate.implementer_state_hash
        == current_session.implementer_state_hash
    )


def _target_drifted(
    prior_candidate: ReviewCandidateRecord,
    *,
    head_sha: str,
    worktree_hash: str,
    changed_paths: tuple[str, ...],
) -> bool:
    if head_sha and prior_candidate.head_sha and head_sha != prior_candidate.head_sha:
        return True
    if worktree_hash and prior_candidate.worktree_hash and worktree_hash != prior_candidate.worktree_hash:
        return True
    return changed_paths != prior_candidate.changed_paths


def _implementer_status_written(current_session: ReviewCurrentSessionState) -> bool:
    if is_pending_implementer_state(
        implementer_status=current_session.implementer_status,
        implementer_ack=current_session.implementer_ack,
        implementer_ack_state=current_session.implementer_ack_state,
    ):
        return False
    return bool(current_session.implementer_status.strip())


def _validate_candidate(
    *,
    artifact_kind: str,
    changed_paths: tuple[str, ...],
    worktree_hash: str,
    missing_scope_paths: tuple[str, ...],
) -> tuple[bool, str]:
    if not changed_paths:
        return False, "missing_changed_paths"
    if artifact_kind == "dirty_tree" and not worktree_hash:
        return False, "missing_worktree_hash"
    if missing_scope_paths:
        return False, "scope_mismatch"
    return True, ""


def _candidate_id(
    *,
    instruction_revision: str,
    artifact_kind: str,
    base_sha: str,
    head_sha: str,
    worktree_hash: str,
    changed_paths: tuple[str, ...],
    implementer_state_hash: str,
) -> str:
    payload = "\0".join(
        (
            instruction_revision,
            artifact_kind,
            base_sha,
            head_sha,
            worktree_hash,
            "\n".join(changed_paths),
            implementer_state_hash,
        )
    )
    return f"review-candidate-{sha256(payload.encode('utf-8')).hexdigest()[:12]}"
