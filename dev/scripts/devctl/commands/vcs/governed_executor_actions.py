"""Typed action builders and support helpers for the VCS pipeline."""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from typing import Any

from ...common import emit_output, write_output
from ...runtime import TypedAction
from ...runtime.remote_commit_pipeline_models import CommitIntentState, RemoteCommitPipelineContract
from ...time_utils import utc_timestamp
from .governed_executor_field_access import string_value
from .governed_executor_validation import build_validation_plan

STAGE_ACTION_ID = "vcs.stage"
COMMIT_ACTION_ID = "vcs.commit"
PUSH_ACTION_ID = "vcs.push"
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


@dataclass(frozen=True, slots=True)
class StageActionInputs:
    """Structured inputs for `vcs.stage`."""

    repo_pack_id: str
    paths: tuple[str, ...] = ()
    commit_message_draft: str = ""
    push_requested: bool = False
    guard_profile: str = ""
    risk_addons: tuple[str, ...] = ()
    proof_level: str = ""
    work_intake_ref: str = ""
    remote: str = "origin"
    reuse_staged_index: bool = False
    allow_empty: bool = False
    requested_by: str = "remote_commit_pipeline"


@dataclass(frozen=True, slots=True)
class CommitActionInputs:
    """Structured inputs for `vcs.commit`."""

    repo_pack_id: str
    pipeline_id: str
    commit_message_draft: str = ""
    amend: bool = False
    allow_empty: bool = False
    no_edit: bool = False
    requested_by: str = "remote_commit_pipeline"


@dataclass(frozen=True, slots=True)
class PushActionInputs:
    """Structured inputs for `vcs.push`."""

    repo_pack_id: str
    branch: str
    remote: str
    execute: bool
    skip_preflight: bool = False
    skip_post_push: bool = False
    approved_target_identity: str = ""
    requested_by: str = "devctl.push"


def build_stage_action(
    *,
    inputs: StageActionInputs | None = None,
    **kwargs: object,
) -> TypedAction:
    """Build the canonical typed action for governed staging."""
    if inputs is None:
        unexpected = sorted(kwargs.keys() - {
            "repo_pack_id",
            "paths",
            "commit_message_draft",
            "push_requested",
            "guard_profile",
            "risk_addons",
            "proof_level",
            "work_intake_ref",
            "remote",
            "reuse_staged_index",
            "allow_empty",
            "requested_by",
        })
        if unexpected:
            raise TypeError(f"Unexpected stage action inputs: {', '.join(unexpected)}")
        resolved = StageActionInputs(
            repo_pack_id=str(kwargs["repo_pack_id"]),
            paths=tuple(str(path) for path in kwargs.get("paths", ()) or ()),
            commit_message_draft=str(kwargs.get("commit_message_draft", "")),
            push_requested=bool(kwargs.get("push_requested", False)),
            guard_profile=str(kwargs.get("guard_profile", "")),
            risk_addons=tuple(
                str(item) for item in kwargs.get("risk_addons", ()) or ()
            ),
            proof_level=str(kwargs.get("proof_level", "")),
            work_intake_ref=str(kwargs.get("work_intake_ref", "")),
            remote=str(kwargs.get("remote", "origin")),
            reuse_staged_index=bool(kwargs.get("reuse_staged_index", False)),
            allow_empty=bool(kwargs.get("allow_empty", False)),
            requested_by=str(kwargs.get("requested_by", "remote_commit_pipeline")),
        )
    else:
        resolved = inputs
    parameters: dict[str, object] = {}
    parameters["paths"] = [str(path) for path in resolved.paths if str(path).strip()]
    parameters["commit_message_draft"] = resolved.commit_message_draft
    parameters["push_requested"] = bool(resolved.push_requested)
    parameters["guard_profile"] = resolved.guard_profile
    parameters["risk_addons"] = list(resolved.risk_addons)
    parameters["proof_level"] = resolved.proof_level
    parameters["work_intake_ref"] = resolved.work_intake_ref
    parameters["remote"] = resolved.remote
    parameters["reuse_staged_index"] = bool(resolved.reuse_staged_index)
    parameters["allow_empty"] = bool(resolved.allow_empty)
    return TypedAction(
        schema_version=1,
        contract_id="TypedAction",
        action_id=STAGE_ACTION_ID,
        repo_pack_id=resolved.repo_pack_id,
        parameters=parameters,
        requested_by=resolved.requested_by,
        dry_run=False,
    )


def build_commit_action(
    *,
    inputs: CommitActionInputs | None = None,
    **kwargs: object,
) -> TypedAction:
    """Build the canonical typed action for governed commit execution."""
    if inputs is None:
        unexpected = sorted(kwargs.keys() - {
            "repo_pack_id",
            "pipeline_id",
            "commit_message_draft",
            "amend",
            "allow_empty",
            "no_edit",
            "requested_by",
        })
        if unexpected:
            raise TypeError(f"Unexpected commit action inputs: {', '.join(unexpected)}")
        resolved = CommitActionInputs(
            repo_pack_id=str(kwargs["repo_pack_id"]),
            pipeline_id=str(kwargs["pipeline_id"]),
            commit_message_draft=str(kwargs.get("commit_message_draft", "")),
            amend=bool(kwargs.get("amend", False)),
            allow_empty=bool(kwargs.get("allow_empty", False)),
            no_edit=bool(kwargs.get("no_edit", False)),
            requested_by=str(kwargs.get("requested_by", "remote_commit_pipeline")),
        )
    else:
        resolved = inputs
    parameters: dict[str, object] = {"pipeline_id": resolved.pipeline_id}
    parameters["commit_message_draft"] = resolved.commit_message_draft
    parameters["amend"] = bool(resolved.amend)
    parameters["allow_empty"] = bool(resolved.allow_empty)
    parameters["no_edit"] = bool(resolved.no_edit)
    return TypedAction(
        schema_version=1,
        contract_id="TypedAction",
        action_id=COMMIT_ACTION_ID,
        repo_pack_id=resolved.repo_pack_id,
        parameters=parameters,
        requested_by=resolved.requested_by,
        dry_run=False,
    )


def build_push_action(
    *,
    inputs: PushActionInputs | None = None,
    **kwargs: object,
) -> TypedAction:
    """Build the canonical typed action for one governed push request."""
    if inputs is None:
        unexpected = sorted(kwargs.keys() - {
            "repo_pack_id",
            "branch",
            "remote",
            "execute",
            "skip_preflight",
            "skip_post_push",
            "approved_target_identity",
            "requested_by",
        })
        if unexpected:
            raise TypeError(f"Unexpected push action inputs: {', '.join(unexpected)}")
        resolved = PushActionInputs(
            repo_pack_id=str(kwargs["repo_pack_id"]),
            branch=str(kwargs["branch"]),
            remote=str(kwargs["remote"]),
            execute=bool(kwargs["execute"]),
            skip_preflight=bool(kwargs.get("skip_preflight", False)),
            skip_post_push=bool(kwargs.get("skip_post_push", False)),
            approved_target_identity=str(kwargs.get("approved_target_identity", "")),
            requested_by=str(kwargs.get("requested_by", "devctl.push")),
        )
    else:
        resolved = inputs
    parameters: dict[str, object] = {}
    parameters["branch"] = resolved.branch
    parameters["remote"] = resolved.remote
    parameters["execute"] = resolved.execute
    parameters["skip_preflight"] = resolved.skip_preflight
    parameters["skip_post_push"] = resolved.skip_post_push
    if resolved.approved_target_identity:
        parameters["approved_target_identity"] = resolved.approved_target_identity
    return TypedAction(
        schema_version=1,
        contract_id="TypedAction",
        action_id=PUSH_ACTION_ID,
        repo_pack_id=resolved.repo_pack_id,
        parameters=parameters,
        requested_by=resolved.requested_by,
        dry_run=not bool(resolved.execute),
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

def _build_report(*, status: str, reason: str = "", **extra: object) -> dict[str, object]:
    """Build a commit report dict."""
    report: dict[str, object] = {
        "command": "commit",
        "timestamp": utc_timestamp(),
        "status": status,
    }
    if reason:
        report["reason"] = reason
    report.update(extra)
    return report


def _emit_report(args, report: dict[str, Any]) -> None:
    """Emit the commit report in the requested format."""
    fmt = getattr(args, "format", "md")
    if fmt == "json":
        output = json.dumps(report, indent=2)
    else:
        lines = [f"# devctl commit — {report['status']}"]
        for key, value in report.items():
            if key in {"command", "status"}:
                continue
            lines.append(f"- **{key}**: {value}")
        output = "\n".join(lines)
    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
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
    push_requested = bool(action.parameters.get("push_requested"))
    guard_profile = string_value(action.parameters.get("guard_profile"))
    validation_plan = build_validation_plan(
        action=action,
        staged=staged,
        tree_hash=tree_hash,
    )
    intent = CommitIntentState(
        staged_tree_hash=tree_hash,
        staged_path_count=len(staged),
        staged_paths=tuple(staged),
        diff_summary=diff_summary,
        commit_message_draft=string_value(
            action.parameters.get("commit_message_draft")
        ),
        push_requested=push_requested,
        guard_profile=guard_profile,
        validation_plan=validation_plan,
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
