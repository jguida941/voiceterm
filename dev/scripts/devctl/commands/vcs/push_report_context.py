"""Push report context construction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ...common import emit_output, pipe_output, write_output
from .governed_executor_actions import build_push_action
from .push_artifact import (
    append_push_receipt,
    latest_push_report_relpath,
    persist_latest_push_report,
    serialize_push_report,
)
from .push_report import render_push_report
from .push_snapshot import PushReportContext


@dataclass(frozen=True, slots=True)
class PushReportFinishInputs:
    args: object
    repo_root: Path
    report: dict[str, Any]
    artifact_path: str
    outcome_ok: bool
    emit_output_report: bool
    writer: object = None
    piper: object = None


def build_push_report_context(
    *,
    repo_root: Path,
    policy,
    state,
    args,
    head_commit: str,
    approved_target_identity: str = "",
) -> PushReportContext:
    """Build the reusable push-report context for one execution phase."""
    typed_action = asdict(
        build_push_action(
            repo_pack_id=policy.repo_pack_id,
            branch=state.branch,
            remote=state.remote,
            execute=bool(args.execute),
            skip_preflight=bool(args.skip_preflight),
            skip_post_push=bool(args.skip_post_push),
            approved_target_identity=approved_target_identity,
            approved_worktree_identity=state.approved_worktree_identity,
            head_commit=head_commit,
            current_worktree_identity=state.current_worktree_identity,
            approved_target_identity_source=(
                "live_publication_authorization"
                if approved_target_identity
                else "authorization_not_required"
            ),
        )
    )
    return PushReportContext(
        repo_root=repo_root,
        policy=policy,
        state=state,
        args=args,
        head_commit=head_commit,
        typed_action=typed_action,
        artifact_path=latest_push_report_relpath(repo_root=repo_root),
        current_worktree_identity=state.current_worktree_identity,
        approved_target_identity=approved_target_identity,
        approved_worktree_identity=state.approved_worktree_identity,
        push_authorization_id=state.push_authorization_id,
        push_authorization_mode=state.push_authorization_mode,
    )


def finish_push_report(inputs: PushReportFinishInputs) -> tuple[int, dict[str, Any]]:
    report = inputs.report
    if not inputs.emit_output_report:
        persist_latest_push_report(report, repo_root=inputs.repo_root)
        append_push_receipt(report, repo_root=inputs.repo_root)
        return (0 if inputs.outcome_ok else 1), report

    append_push_receipt(report, repo_root=inputs.repo_root)
    report_json = serialize_push_report(report)
    args = inputs.args
    output = report_json if args.format == "json" else render_push_report(report)
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        additional_outputs=((report_json, inputs.artifact_path),),
        writer=write_output if inputs.writer is None else inputs.writer,
        piper=pipe_output if inputs.piper is None else inputs.piper,
    )
    if pipe_rc != 0:
        return pipe_rc, report
    return (0 if inputs.outcome_ok else 1), report
