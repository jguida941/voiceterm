"""Publication-authorization helpers for governed push execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..governance.draft import scan_repo_governance
from ..governance.push_state import current_head_commit_sha
from ..governance.push_state_support import is_expired
from ..repo_packs import active_path_config
from ..review_channel.remote_commit_pipeline_artifact import (
    load_remote_commit_pipeline_contract,
)
from .action_contracts import ActionOutcome
from .conductor_capability import normalize_reviewer_mode
from .remote_commit_pipeline_models import (
    PushAuthorizationRecord,
    RemoteCommitPipelineContract,
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
    authorization_required = _authorization_required(
        review_state=review_state,
        pipeline=pipeline,
    )
    if not authorization_required and authorization is None:
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
    current_head = current_head_commit_sha(repo_root=repo_root)
    if (
        authorization.authorized_head_sha
        and current_head
        and authorization.authorized_head_sha != current_head
    ):
        return PublicationAuthorizationDecision(
            authorization_required=True,
            authorized=False,
            reason="head_changed_after_authorization",
            summary=(
                "The current HEAD no longer matches the authorized publication "
                "record. Review and re-authorize the new commit before pushing."
            ),
            push_authorization=authorization,
        )
    if is_expired(authorization.expires_at_utc):
        return PublicationAuthorizationDecision(
            authorization_required=True,
            authorized=False,
            reason="push_authorization_expired",
            summary=(
                "The current publication authorization has expired. Request a "
                "fresh approval or a typed override before pushing."
            ),
            push_authorization=authorization,
        )
    if authorization.guard_status != ActionOutcome.PASS:
        return PublicationAuthorizationDecision(
            authorization_required=True,
            authorized=False,
            reason="push_authorization_guard_not_passed",
            summary=(
                "The publication authorization does not carry a passing guard "
                "result for this commit."
            ),
            push_authorization=authorization,
        )
    if (
        pipeline.pipeline_id
        and pipeline.commit_sha
        and authorization.authorized_head_sha
        and pipeline.commit_sha != authorization.authorized_head_sha
    ):
        return PublicationAuthorizationDecision(
            authorization_required=True,
            authorized=False,
            reason="push_authorization_pipeline_drift",
            summary=(
                "The current pipeline commit no longer matches the persisted "
                "publication authorization."
            ),
            push_authorization=authorization,
        )
    if (
        pipeline.approved_target_identity
        and authorization.approved_target_identity
        and pipeline.approved_target_identity != authorization.approved_target_identity
    ):
        return PublicationAuthorizationDecision(
            authorization_required=True,
            authorized=False,
            reason="push_authorization_target_drift",
            summary=(
                "The approved publish identity drifted after authorization. "
                "Recover the pipeline and request a fresh approval."
            ),
            push_authorization=authorization,
        )
    return PublicationAuthorizationDecision(
        authorization_required=authorization_required,
        authorized=True,
        reason="push_authorization_current",
        summary=(
            "Publication is authorized for the current HEAD by the persisted "
            "push authorization record."
        ),
        push_authorization=authorization,
    )


def _authorization_required(
    *,
    review_state,
    pipeline: RemoteCommitPipelineContract,
) -> bool:
    if pipeline.pipeline_id or pipeline.push_authorization is not None:
        return True
    if review_state is None:
        return False
    effective_mode = normalize_reviewer_mode(
        getattr(review_state.reviewer_runtime, "effective_reviewer_mode", "")
    )
    reviewer_mode = normalize_reviewer_mode(
        getattr(review_state.reviewer_runtime, "reviewer_mode", "")
    )
    return "active_dual_agent" in {effective_mode, reviewer_mode}


def _load_pipeline(repo_root: Path) -> RemoteCommitPipelineContract:
    return load_remote_commit_pipeline_contract(
        output_root=repo_root / active_path_config().review_status_dir_rel
    )
__all__ = [
    "PublicationAuthorizationDecision",
    "publication_authorization_decision",
]
