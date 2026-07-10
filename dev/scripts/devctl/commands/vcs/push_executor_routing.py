"""Executor-routed governed push reuse for an existing commit pipeline."""

from __future__ import annotations

from ...common import emit_output, pipe_output, write_output
from ...config import REPO_ROOT
from ...governance.push_state import current_head_commit_sha
from .governed_executor_actions import build_push_action
from .push_artifact import (
    latest_push_report_relpath,
    load_latest_push_report,
    serialize_push_report,
)
from .push_pipeline_recovery import maybe_refresh_same_head_pipeline_authorization
from .push_report import render_push_report


def maybe_run_executor_routed_push(*, args, resolved_policy, state, executor, pipeline):
    """Reuse the active governed pipeline when it already owns the current branch."""
    active_pipeline_matches_branch = (
        bool(pipeline.pipeline_id)
        and bool(state.branch)
        and (pipeline.branch == state.branch)
    )
    if not (
        active_pipeline_matches_branch
        and pipeline.state in {"commit_recorded", "push_pending", "push_blocked"}
        and bool(pipeline.commit_sha)
    ):
        return None

    pipeline = maybe_refresh_same_head_pipeline_authorization(
        args=args,
        executor=executor,
        pipeline=pipeline,
    )
    repo_root = getattr(executor, "repo_root", REPO_ROOT) or REPO_ROOT
    head_commit = current_head_commit_sha(repo_root=repo_root)
    result = executor.execute(
        build_push_action(
            repo_pack_id=resolved_policy.repo_pack_id,
            branch=str(
                state.branch or pipeline.branch or getattr(args, "branch", "") or ""
            ),
            remote=str(
                getattr(args, "remote", "")
                or state.remote
                or resolved_policy.default_remote
            ),
            execute=bool(args.execute),
            skip_preflight=bool(args.skip_preflight),
            skip_post_push=bool(args.skip_post_push),
            approved_target_identity=str(
                getattr(args, "approved_target_identity", "")
                or getattr(pipeline, "approved_target_identity", "")
                or state.approved_target_identity
            ),
            approved_worktree_identity=str(
                getattr(pipeline, "worktree_identity", "")
                or state.approved_worktree_identity
            ),
            head_commit=head_commit,
            current_worktree_identity=str(
                getattr(state, "current_worktree_identity", "") or ""
            ),
            approved_target_identity_source="live_publication_authorization",
            requested_by="devctl.push",
        )
    )
    report = getattr(executor, "last_push_report", None)
    if not isinstance(report, dict):
        latest = load_latest_push_report(repo_root=repo_root)
        report = (
            latest
            if _latest_report_matches_current_push(
                latest,
                branch=state.branch,
                head_commit=head_commit,
            )
            else None
        )
    if report is not None:
        report_json = serialize_push_report(report)
        output = report_json if args.format == "json" else render_push_report(report)
        pipe_rc = emit_output(
            output,
            output_path=args.output,
            pipe_command=args.pipe_command,
            pipe_args=args.pipe_args,
            additional_outputs=(
                (report_json, latest_push_report_relpath(repo_root=repo_root)),
            ),
            writer=write_output,
            piper=pipe_output,
        )
        if pipe_rc != 0:
            return pipe_rc
    return 0 if result.ok else 1


def _latest_report_matches_current_push(
    report: object,
    *,
    branch: str,
    head_commit: str,
) -> bool:
    """Return true only for a latest-push artifact from this branch and HEAD."""
    if not isinstance(report, dict):
        return False
    if str(report.get("branch") or "").strip() != str(branch or "").strip():
        return False
    if str(report.get("head_commit") or "").strip() != str(head_commit or "").strip():
        return False
    return True
