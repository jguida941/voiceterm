"""Typed action builders and constants for the remote commit/push pipeline."""

from __future__ import annotations

import secrets
from collections.abc import Sequence

from ...runtime import TypedAction
from ...runtime.remote_commit_pipeline_models import (
    CommitIntentState,
    RemoteCommitPipelineContract,
)
from .governed_executor_field_access import string_value

STAGE_ACTION_ID = "vcs.stage"
COMMIT_ACTION_ID = "vcs.commit"
RECOVER_ACTION_ID = "vcs.pipeline.recover"
APPROVAL_PACKET_KIND = "commit_approval"

_ACTIVE_PIPELINE_STATES = frozenset(
    {
        "drafted",
        "staged",
        "guards_running",
        "guards_passed",
        "operator_approval_pending",
        "approved",
        "commit_pending",
        "commit_recorded",
        "push_pending",
    }
)
_RECOVERABLE_PIPELINE_STATES = frozenset(
    {
        "",
        "guards_failed",
        "rejected",
        "push_blocked",
        "push_completed",
    }
)
_PUSHABLE_PIPELINE_STATES = frozenset(
    {
        "commit_recorded",
        "push_pending",
        "push_blocked",
    }
)


def build_stage_action(
    *,
    repo_pack_id: str,
    paths: Sequence[str] = (),
    commit_message_draft: str,
    push_requested: bool,
    guard_profile: str,
    work_intake_ref: str,
    remote: str = "origin",
    requested_by: str = "remote_commit_pipeline",
) -> TypedAction:
    """Build the canonical typed action for governed staging."""
    parameters: dict[str, object] = {}
    parameters["paths"] = [str(path) for path in paths if str(path).strip()]
    parameters["commit_message_draft"] = commit_message_draft
    parameters["push_requested"] = bool(push_requested)
    parameters["guard_profile"] = guard_profile
    parameters["work_intake_ref"] = work_intake_ref
    parameters["remote"] = remote
    return TypedAction(
        schema_version=1,
        contract_id="TypedAction",
        action_id=STAGE_ACTION_ID,
        repo_pack_id=repo_pack_id,
        parameters=parameters,
        requested_by=requested_by,
        dry_run=False,
    )


def build_commit_action(
    *,
    repo_pack_id: str,
    pipeline_id: str,
    requested_by: str = "remote_commit_pipeline",
) -> TypedAction:
    """Build the canonical typed action for governed commit execution."""
    return TypedAction(
        schema_version=1,
        contract_id="TypedAction",
        action_id=COMMIT_ACTION_ID,
        repo_pack_id=repo_pack_id,
        parameters={"pipeline_id": pipeline_id},
        requested_by=requested_by,
        dry_run=False,
    )


def build_recover_action(
    *,
    repo_pack_id: str,
    strategy: str = "clear",
    requested_by: str = "remote_commit_pipeline",
) -> TypedAction:
    """Build the canonical typed action for governed pipeline recovery."""
    return TypedAction(
        schema_version=1,
        contract_id="TypedAction",
        action_id=RECOVER_ACTION_ID,
        repo_pack_id=repo_pack_id,
        parameters={"strategy": strategy},
        requested_by=requested_by,
        dry_run=False,
    )


def build_staged_pipeline(
    *,
    action: TypedAction,
    staged: list[str],
    tree_hash: str,
    diff_summary: str,
    branch: str,
) -> RemoteCommitPipelineContract:
    """Construct a fresh pipeline contract from a staged snapshot."""
    pipeline_id = f"pipeline-{secrets.token_hex(6)}"
    generation_id = f"gen-{secrets.token_hex(6)}"
    remote = string_value(action.parameters.get("remote")) or "origin"
    intent = CommitIntentState(
        staged_tree_hash=tree_hash,
        staged_path_count=len(staged),
        staged_paths=tuple(staged),
        diff_summary=diff_summary,
        commit_message_draft=string_value(
            action.parameters.get("commit_message_draft")
        ),
        push_requested=bool(action.parameters.get("push_requested")),
        guard_profile=string_value(action.parameters.get("guard_profile")),
        work_intake_ref=string_value(action.parameters.get("work_intake_ref")),
    )
    return RemoteCommitPipelineContract(
        pipeline_id=pipeline_id,
        state="staged",
        requested_by=action.requested_by,
        branch=branch,
        remote=remote,
        intent=intent,
        blocked_reason="",
        recovery_action_allowed=RECOVER_ACTION_ID,
        generation_id=generation_id,
    )
