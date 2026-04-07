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
from .vcs import run_git_capture


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
    current_head = current_head_commit_sha(repo_root=repo_root)
    snapshot_receipt_parent = _snapshot_only_receipt_parent_sha(
        repo_root=repo_root,
        current_head=current_head,
        governance=governance,
    )
    authorization_required = _authorization_required(
        review_state=review_state,
        pipeline=pipeline,
        current_head=current_head,
        snapshot_receipt_parent=snapshot_receipt_parent,
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
    authorized_via_snapshot_receipt = False
    if (
        authorization.authorized_head_sha
        and current_head
        and authorization.authorized_head_sha != current_head
    ):
        authorized_via_snapshot_receipt = _same_commit(
            snapshot_receipt_parent,
            authorization.authorized_head_sha,
        )
        if not authorized_via_snapshot_receipt:
            return PublicationAuthorizationDecision(
                authorization_required=True,
                authorized=False,
                reason="head_changed_after_authorization",
                summary=(
                    "The current HEAD no longer matches the authorized "
                    "publication record. Review and re-authorize the new "
                    "commit before pushing."
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
    )


def _authorization_required(
    *,
    review_state,
    pipeline: RemoteCommitPipelineContract,
    current_head: str,
    snapshot_receipt_parent: str,
) -> bool:
    if _active_dual_agent_review(review_state):
        return True
    if pipeline.pipeline_id or pipeline.push_authorization is not None:
        return _pipeline_targets_current_publication(
            pipeline=pipeline,
            current_head=current_head,
            snapshot_receipt_parent=snapshot_receipt_parent,
        )
    return False


def _active_dual_agent_review(review_state) -> bool:
    if review_state is None:
        return False
    effective_mode = normalize_reviewer_mode(
        getattr(review_state.reviewer_runtime, "effective_reviewer_mode", "")
    )
    reviewer_mode = normalize_reviewer_mode(
        getattr(review_state.reviewer_runtime, "reviewer_mode", "")
    )
    return "active_dual_agent" in {effective_mode, reviewer_mode}


def _pipeline_targets_current_publication(
    *,
    pipeline: RemoteCommitPipelineContract,
    current_head: str,
    snapshot_receipt_parent: str,
) -> bool:
    authorization = pipeline.push_authorization
    authorized_head = (
        "" if authorization is None else str(authorization.authorized_head_sha or "")
    )
    return any(
        _same_commit(candidate, current)
        for candidate in (pipeline.commit_sha, authorized_head)
        for current in (current_head, snapshot_receipt_parent)
    )


def _load_pipeline(repo_root: Path) -> RemoteCommitPipelineContract:
    return load_remote_commit_pipeline_contract(
        output_root=repo_root / active_path_config().review_status_dir_rel
    )


def _snapshot_only_receipt_parent_sha(
    *,
    repo_root: Path,
    current_head: str,
    governance: object,
) -> str:
    """Return HEAD's parent when HEAD changes only the ReviewSnapshot file."""
    if not current_head:
        return ""
    snapshot_rel = _review_snapshot_relpath(governance)
    code, output, _ = run_git_capture(
        ["diff-tree", "--no-commit-id", "--name-only", "-r", current_head],
        repo_root=repo_root,
    )
    if code != 0:
        return ""
    changed_paths = tuple(line.strip() for line in output.splitlines() if line.strip())
    if changed_paths != (snapshot_rel,):
        return ""

    parent_code, parent_sha, _ = run_git_capture(
        ["rev-parse", f"{current_head}^"],
        repo_root=repo_root,
    )
    if parent_code != 0:
        return ""
    return parent_sha.strip()


def _review_snapshot_relpath(governance: object) -> str:
    if governance is not None:
        artifact_roots = getattr(governance, "artifact_roots", None)
        if artifact_roots is not None:
            value = str(
                getattr(artifact_roots, "review_snapshot_path", "") or ""
            ).strip()
            if value:
                return value
    return "dev/audits/REVIEW_SNAPSHOT.md"


def _same_commit(left: str, right: str) -> bool:
    left = str(left or "").strip()
    right = str(right or "").strip()
    return bool(left and right and (left.startswith(right) or right.startswith(left)))


__all__ = [
    "PublicationAuthorizationDecision",
    "publication_authorization_decision",
]
