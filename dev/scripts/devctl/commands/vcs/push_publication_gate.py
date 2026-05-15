"""Publication authorization binding for governed push."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...governance.push_state import current_head_commit_sha
from ...runtime.push_authorization import publication_authorization_decision
from .push_findings import append_approved_identity_errors
from .push_preflight_commit import run_post_validation_auto_commit_repair_phase
from .push_preflight_projection import repair_preflight_generated_changes_for_push


@dataclass(frozen=True, slots=True)
class PushPublicationGateInputs:
    """Inputs that vary between plain and executor-routed push flows."""

    repo_root: Path
    run_cmd_fn: Any
    commit_pipeline: Any
    publication_authorization_fn: Any
    pass_commit_pipeline_to_authorization: bool
    head_commit: str
    current_head_fn: Any = current_head_commit_sha


def finish_preflight_before_publication(
    state: Any,
    policy: Any,
    inputs: PushPublicationGateInputs,
) -> str:
    """Run managed post-validation repair and bind publication authorization."""
    head_commit = inputs.current_head_fn(repo_root=inputs.repo_root) or inputs.head_commit
    if inputs.run_cmd_fn is None:
        run_post_validation_auto_commit_repair_phase(
            state,
            policy,
            repo_root=inputs.repo_root,
            repair_fn=repair_preflight_generated_changes_for_push,
            validation_passed=not state.errors,
        )
    head_commit = inputs.current_head_fn(repo_root=inputs.repo_root) or head_commit
    _append_publication_authorization_errors(state, inputs=inputs)
    return head_commit


def _append_publication_authorization_errors(
    state: Any,
    *,
    inputs: PushPublicationGateInputs,
) -> None:
    """Fail closed when publication proof for the current HEAD is missing."""
    if state.errors:
        return
    if state.branch_has_remote and state.ahead == 0:
        return
    authorization_fn = (
        publication_authorization_decision
        if inputs.publication_authorization_fn is None
        else inputs.publication_authorization_fn
    )
    if inputs.pass_commit_pipeline_to_authorization:
        decision = authorization_fn(
            repo_root=inputs.repo_root,
            pipeline=inputs.commit_pipeline,
        )
    else:
        decision = authorization_fn(repo_root=inputs.repo_root)
    if decision.authorized:
        _bind_authorization_to_state(
            state,
            decision=decision,
            repo_root=inputs.repo_root,
        )
        return
    summary = str(decision.summary or decision.reason or "").strip()
    detail = f" {summary}" if summary else ""
    state.errors.append(
        "Publication authorization blocks `devctl push`: "
        f"reason=`{decision.reason}`.{detail}"
    )


def _bind_authorization_to_state(
    state: Any,
    *,
    decision: Any,
    repo_root: Path,
) -> None:
    authorization = decision.push_authorization
    if authorization is None:
        return
    state.approved_target_identity = authorization.approved_target_identity
    state.approved_worktree_identity = str(
        getattr(authorization, "worktree_identity", "") or ""
    ).strip()
    state.push_authorization_id = authorization.authorization_id
    state.push_authorization_mode = authorization.approval_mode
    state.push_authorization_head_commit = str(
        getattr(authorization, "authorized_head_sha", "") or ""
    ).strip()
    append_approved_identity_errors(
        state,
        authorization=authorization,
        repo_root=repo_root,
        authorized_via_managed_receipt_chain=bool(
            getattr(
                decision,
                "authorized_via_managed_receipt_chain",
                False,
            )
        ),
    )
