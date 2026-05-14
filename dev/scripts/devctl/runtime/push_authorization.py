"""Publication-authorization helpers for governed push execution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path

from ..governance.draft import scan_repo_governance
from ..governance.push_state import current_head_commit_sha
from ..governance.push_state_support import is_expired
from ..review_channel.remote_commit_pipeline_artifact import (
    load_canonical_remote_commit_pipeline_contract,
)
from ..review_channel.service_identity import worktree_identity_for_repo
from .action_contracts import ActionOutcome
from .remote_commit_pipeline_models import (
    PushAuthorizationRecord,
    RemoteCommitPipelineContract,
)
from .role_topology import resolve_role_topology
from .review_snapshot_refresh import (
    receipt_commit_ancestor_shas,
    receipt_commit_parent_sha,
)
from .review_state_locator import load_review_state


@dataclass(frozen=True, slots=True)
class PublicationAuthorizationDecision:
    """Resolved publication gate for one push attempt."""

    authorization_required: bool
    authorized: bool
    reason: str
    summary: str
    push_authorization: PushAuthorizationRecord | None = None
    authorized_via_managed_receipt_chain: bool = False


def publication_authorization_decision(
    *,
    repo_root: Path,
) -> PublicationAuthorizationDecision:
    """Return whether the current repo state may publish through `devctl push`."""
    try:
        governance = scan_repo_governance(repo_root)
    except (OSError, ValueError):
        governance = None
    review_state = load_review_state(repo_root, governance=governance)
    pipeline = _load_pipeline(repo_root)
    authorization = pipeline.push_authorization
    current_head = current_head_commit_sha(repo_root=repo_root)
    current_worktree_identity = worktree_identity_for_repo(repo_root)
    snapshot_receipt_parent = _snapshot_only_receipt_parent_sha(
        repo_root=repo_root,
        current_head=current_head,
        governance=governance,
    )
    snapshot_receipt_ancestors = receipt_commit_ancestor_shas(
        repo_root=repo_root,
        current_head=current_head,
        governance=governance,
    )
    if snapshot_receipt_parent and not any(
        _same_commit(candidate, snapshot_receipt_parent)
        for candidate in snapshot_receipt_ancestors
    ):
        snapshot_receipt_ancestors = (
            *snapshot_receipt_ancestors,
            snapshot_receipt_parent,
        )
    authorization_required = _authorization_required(
        review_state=review_state,
        pipeline=pipeline,
        current_head=current_head,
        snapshot_receipt_ancestors=snapshot_receipt_ancestors,
    )
    if not authorization_required:
        return PublicationAuthorizationDecision(
            authorization_required=False,
            authorized=True,
            reason="authorization_not_required",
            summary=(
                "This push does not require a persisted publication authorization."
            ),
        )
    if authorization is None:
        return PublicationAuthorizationDecision(
            authorization_required=True,
            authorized=False,
            reason="push_authorization_missing",
            summary=(
                "Publication requires a typed `PushAuthorizationRecord` for the "
                "current HEAD. Record the governed commit through the review "
                "pipeline before pushing."
            ),
        )
    authorized_via_snapshot_receipt, blocked_decision = _validate_authorization_record(
        authorization=authorization,
        pipeline=pipeline,
        current_head=current_head,
        current_worktree_identity=current_worktree_identity,
        snapshot_receipt_ancestors=snapshot_receipt_ancestors,
    )
    if blocked_decision is not None:
        return blocked_decision
    if authorized_via_snapshot_receipt:
        reason = "push_authorization_snapshot_receipt_current"
        summary = (
            "Publication is authorized because the current HEAD is a "
            "snapshot-only ReviewSnapshot receipt whose parent matches the "
            "persisted push authorization record."
        )
    else:
        reason = "push_authorization_current"
        summary = (
            "Publication is authorized for the current HEAD by the persisted "
            "push authorization record."
        )
    return PublicationAuthorizationDecision(
        authorization_required=authorization_required,
        authorized=True,
        reason=reason,
        summary=summary,
        push_authorization=authorization,
        authorized_via_managed_receipt_chain=authorized_via_snapshot_receipt,
    )


def _validate_authorization_record(
    *,
    authorization: PushAuthorizationRecord,
    pipeline: RemoteCommitPipelineContract,
    current_head: str,
    current_worktree_identity: str,
    snapshot_receipt_ancestors: tuple[str, ...],
) -> tuple[bool, PublicationAuthorizationDecision | None]:
    authorized_via_snapshot_receipt = False
    if (
        authorization.authorized_head_sha
        and current_head
        and authorization.authorized_head_sha != current_head
    ):
        authorized_via_snapshot_receipt = any(
            _same_commit(candidate, authorization.authorized_head_sha)
            for candidate in snapshot_receipt_ancestors
        )
        if not authorized_via_snapshot_receipt:
            return False, _blocked_authorization_decision(
                reason="head_changed_after_authorization",
                summary=(
                    "The current HEAD no longer matches the authorized "
                    "publication record. Review and re-authorize the new "
                    "commit before pushing."
                ),
                authorization=authorization,
            )
    if is_expired(authorization.expires_at_utc):
        return False, _blocked_authorization_decision(
            reason="push_authorization_expired",
            summary=(
                "The current publication authorization has expired. Request a "
                "fresh approval or a typed override before pushing."
            ),
            authorization=authorization,
        )
    if authorization.guard_status != ActionOutcome.PASS:
        return False, _blocked_authorization_decision(
            reason="push_authorization_guard_not_passed",
            summary=(
                "The publication authorization does not carry a passing guard "
                "result for this commit."
            ),
            authorization=authorization,
        )
    if (
        pipeline.pipeline_id
        and pipeline.commit_sha
        and authorization.authorized_head_sha
        and pipeline.commit_sha != authorization.authorized_head_sha
    ):
        return False, _blocked_authorization_decision(
            reason="push_authorization_pipeline_drift",
            summary=(
                "The current pipeline commit no longer matches the persisted "
                "publication authorization."
            ),
            authorization=authorization,
        )
    if (
        pipeline.approved_target_identity
        and authorization.approved_target_identity
        and pipeline.approved_target_identity != authorization.approved_target_identity
    ):
        return False, _blocked_authorization_decision(
            reason="push_authorization_target_drift",
            summary=(
                "The approved publish identity drifted after authorization. "
                "Recover the pipeline and request a fresh approval."
            ),
            authorization=authorization,
        )
    if (
        pipeline.worktree_identity
        and authorization.worktree_identity
        and pipeline.worktree_identity != authorization.worktree_identity
    ):
        return False, _blocked_authorization_decision(
            reason="push_authorization_worktree_record_drift",
            summary=(
                "The approved worktree identity drifted after authorization. "
                "Recover the pipeline and request a fresh approval."
            ),
            authorization=authorization,
        )
    if (
        pipeline.worktree_identity
        and current_worktree_identity
        and pipeline.worktree_identity != current_worktree_identity
    ):
        return False, _blocked_authorization_decision(
            reason="push_authorization_worktree_drift",
            summary=(
                "The current worktree does not match the worktree that staged the "
                "approved publication pipeline. Resume the owning worker lane or "
                "recover and restage the pipeline here before pushing."
            ),
            authorization=authorization,
        )
    if (
        authorization.worktree_identity
        and current_worktree_identity
        and authorization.worktree_identity != current_worktree_identity
    ):
        return False, _blocked_authorization_decision(
            reason="push_authorization_worktree_mismatch",
            summary=(
                "The persisted publication authorization belongs to a different "
                "worktree. Request a fresh approval from the worker lane that "
                "owns this checkout before pushing."
            ),
            authorization=authorization,
        )
    return authorized_via_snapshot_receipt, None


def _blocked_authorization_decision(
    *,
    reason: str,
    summary: str,
    authorization: PushAuthorizationRecord,
) -> PublicationAuthorizationDecision:
    return PublicationAuthorizationDecision(
        authorization_required=True,
        authorized=False,
        reason=reason,
        summary=summary,
        push_authorization=authorization,
    )


def _authorization_required(
    *,
    review_state,
    pipeline: RemoteCommitPipelineContract,
    current_head: str,
    snapshot_receipt_ancestors: tuple[str, ...],
) -> bool:
    if _live_multi_agent_review(review_state):
        return True
    if pipeline.pipeline_id or pipeline.push_authorization is not None:
        return _pipeline_targets_current_publication(
            pipeline=pipeline,
            current_head=current_head,
            snapshot_receipt_ancestors=snapshot_receipt_ancestors,
        )
    return False


def _live_multi_agent_review(review_state) -> bool:
    if review_state is None:
        return False
    topology = resolve_role_topology(_review_state_bridge_liveness(review_state))
    return topology.live_reviewer and topology.live_implementer


def _review_state_bridge_liveness(review_state) -> Mapping[str, object]:
    bridge = getattr(review_state, "bridge", None)
    if bridge is None:
        return {}
    if isinstance(bridge, Mapping):
        return bridge
    if is_dataclass(bridge):
        return asdict(bridge)
    values = getattr(bridge, "__dict__", None)
    if isinstance(values, Mapping):
        return values
    return {}


def _pipeline_targets_current_publication(
    *,
    pipeline: RemoteCommitPipelineContract,
    current_head: str,
    snapshot_receipt_ancestors: tuple[str, ...],
) -> bool:
    authorization = pipeline.push_authorization
    authorized_head = (
        "" if authorization is None else str(authorization.authorized_head_sha or "")
    )
    return any(
        _same_commit(candidate, current)
        for candidate in (pipeline.commit_sha, authorized_head)
        for current in (current_head, *snapshot_receipt_ancestors)
    )


def _load_pipeline(repo_root: Path) -> RemoteCommitPipelineContract:
    return load_canonical_remote_commit_pipeline_contract(repo_root=repo_root)


def _snapshot_only_receipt_parent_sha(
    *,
    repo_root: Path,
    current_head: str,
    governance: object,
) -> str:
    """Return HEAD's parent when HEAD is a governed snapshot receipt commit."""
    return receipt_commit_parent_sha(
        repo_root=repo_root,
        current_head=current_head,
        governance=governance,
    )


def _same_commit(left: str, right: str) -> bool:
    left = str(left or "").strip()
    right = str(right or "").strip()
    return bool(left and right and (left.startswith(right) or right.startswith(left)))


__all__ = [
    "PublicationAuthorizationDecision",
    "publication_authorization_decision",
]
