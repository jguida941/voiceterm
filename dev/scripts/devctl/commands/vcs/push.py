"""Policy-driven guarded push flow for the current branch."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from ...collect import collect_git_status
from ...common import pipe_output, run_cmd, write_output
from ...config import REPO_ROOT
from ...governance.push_policy import build_post_push_commands, load_push_policy
from ...governance.push_state import current_head_commit_sha
from ...review_channel.event_store import push_window_write_suspension
from ...review_channel.service_identity import worktree_identity_for_repo
from ...runtime import TypedAction
from ...runtime.push_authorization import publication_authorization_decision
from ...runtime.vcs import (
    remote_exists,
    run_git_capture,
)
from . import push_flow
from .governed_executor_actions import build_push_action
from .push_control_decision import push_control_decision_obedience_report
from .push_control_decision_report import emit_push_control_decision_report
from .push_executor_routing import maybe_run_executor_routed_push
from .push_findings import (
    APPROVED_TARGET_IDENTITY_VIOLATION,
    BRANCH_IDENTITY_VIOLATION,
    PushFindingPayload,
    append_finding,
)
from .push_flow import (
    PushFlowDependencies,
    bind_command_runner_to_repo,
    execute_push_flow as _execute_push_flow,
    execute_push_flow_with_dependencies,
)
from .push_git_status import collect_git_status_for_repo
from .push_pipeline_state_sync import sync_commit_pipeline_with_push_report
from .push_pipeline_scope import (
    authorized_head_sha,
    commit_pipeline_authorizes_publication_scope,
)
from .push_preflight_flow import PushPreflightFlowInputs, run_fetch_and_preflight
from .push_publication_gate import (
    PushPublicationGateInputs,
    finish_preflight_before_publication,
)
from .push_preflight_timeout import (
    PUSH_PREFLIGHT_TIMEOUT_SECONDS,
)
from .push_report import PushStageTruth
from .push_report_context import (
    PushReportFinishInputs,
    build_push_report_context,
    finish_push_report,
)
from .push_snapshot import (
    build_push_report_payload,
    persist_published_remote_snapshot,
    persist_push_progress_snapshot,
)
from .push_worktree_changes import blocking_dirty_paths, push_exclusion_paths

REQUESTED_BY = "devctl.push"


@dataclass(slots=True)
class PushRunState:
    """Mutable execution state for one guarded push attempt."""

    repo_root: str = ""
    branch: str = ""
    configured_branch: str = ""
    live_branch: str = ""
    remote: str = ""
    dirty_paths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    findings: list[PushFindingPayload] = field(default_factory=list)
    fetch_step: dict[str, Any] | None = None
    preflight_step: dict[str, Any] | None = None
    push_step: dict[str, Any] | None = None
    post_push_steps: list[dict[str, Any]] = field(default_factory=list)
    post_push_since_ref: str = ""
    branch_has_remote: bool = False
    ahead: int | None = None
    current_worktree_identity: str = ""
    approved_target_identity: str = ""
    approved_worktree_identity: str = ""
    push_authorization_id: str = ""
    push_authorization_mode: str = ""
    push_authorization_head_commit: str = ""
    remote_head_after: str = ""
    pre_validation_managed_projection_sync: dict[str, Any] = field(default_factory=dict)
    pre_validation_recovery_loop_repair: dict[str, Any] = field(default_factory=dict)
    pre_validation_recovery_loop_repair_required: bool = False
    pre_validation_recovery_loop_repair_startup: dict[str, Any] = field(
        default_factory=dict
    )
    post_validation_auto_commit_repair: dict[str, Any] = field(default_factory=dict)


def execute_push_flow_under_publication_suspension(
    *,
    state: Any,
    policy: Any,
    args: Any,
    repo_root: Path,
    report_context: Any,
    command_runner: Any,
    post_push_commands: Any,
    head_commit: str,
    requested_by: str,
    progress_notice_fn: Any,
    published_remote_snapshot_fn: Any,
) -> Any:
    """Run the push publication phase while publisher projection writes pause."""
    with push_window_write_suspension(
        repo_root=repo_root,
        window_kind="push_publication",
        requested_by=requested_by,
        reason="governed push publication owns projection writes",
        head_sha=head_commit,
        branch=state.branch,
    ):
        return execute_push_flow_with_dependencies(
            state,
            policy,
            args,
            PushFlowDependencies(
                run_cmd_fn=bind_command_runner_to_repo(command_runner, repo_root),
                build_post_push_commands_fn=post_push_commands,
                current_head_sha_fn=push_flow.current_head_commit_sha,
                remote_head_sha_fn=push_flow._remote_head_sha,
                published_remote_snapshot_fn=lambda reason, operator_guidance, partial_progress: (
                    published_remote_snapshot_fn(
                        report_context,
                        reason=reason,
                        operator_guidance=operator_guidance,
                        partial_progress=partial_progress,
                    )
                ),
                progress_notice_fn=progress_notice_fn,
            ),
        )


def _load_run_state(
    policy,
    args,
    *,
    repo_root: Path = REPO_ROOT,
    commit_pipeline: Any = None,
) -> PushRunState:
    state = PushRunState()
    state.repo_root = str(repo_root)
    state.remote = (
        str(args.remote or policy.default_remote).strip() or policy.default_remote
    )
    state.current_worktree_identity = worktree_identity_for_repo(repo_root)
    state.warnings.extend(policy.warnings)
    _append_bypass_policy_errors(state, policy, args)
    git = collect_git_status_for_repo(
        repo_root,
        default_collect_fn=collect_git_status,
    )
    if "error" in git:
        state.errors.append(str(git["error"]))
        return state

    state.configured_branch = str(git.get("branch", "")).strip()
    state.live_branch = _live_current_branch(repo_root)
    if state.configured_branch and state.live_branch:
        state.branch = state.live_branch
        if state.configured_branch != state.live_branch:
            append_finding(
                state,
                BRANCH_IDENTITY_VIOLATION,
                "Configured push branch does not match live git branch.",
                evidence=dict(
                    configured_branch=state.configured_branch,
                    live_branch=state.live_branch,
                ),
            )
    else:
        state.branch = state.live_branch or state.configured_branch
    state.dirty_paths = blocking_dirty_paths(
        git.get("changes", []),
        exclude_paths=push_exclusion_paths(policy, repo_root=repo_root),
    )
    pipeline_authorizes_publication = commit_pipeline_authorizes_publication_scope(
        commit_pipeline,
        state=state,
        repo_root=repo_root,
    )
    if pipeline_authorizes_publication:
        state.push_authorization_head_commit = authorized_head_sha(commit_pipeline)
    if state.branch == "HEAD":
        state.errors.append("Detached HEAD is not supported. Check out a branch first.")
    if state.dirty_paths and pipeline_authorizes_publication:
        state.warnings.append(
            "Ignoring unrelated worktree dirt because the active governed commit "
            "pipeline owns the current branch and authorized HEAD."
        )
    elif state.dirty_paths:
        state.errors.append(
            "Working tree has uncommitted changes. Commit or stash before push."
        )
    if state.branch in policy.protected_branches:
        state.errors.extend(_protected_branch_errors(state.branch, policy))
    if state.branch and not _matches_allowed_prefixes(
        state.branch,
        policy.allowed_branch_prefixes,
    ):
        state.errors.append(
            "Current branch does not match repo_governance.push.allowed_branch_prefixes: "
            + ", ".join(policy.allowed_branch_prefixes)
        )
    if not remote_exists(state.remote, repo_root=repo_root):
        state.errors.append(f"Remote `{state.remote}` is not configured.")
    return state


def _append_bypass_policy_errors(state: PushRunState, policy, args) -> None:
    if args.skip_preflight and not policy.bypass.allow_skip_preflight:
        state.errors.append(
            "Repo policy blocks `--skip-preflight` for `devctl push`. "
            "Remove the flag or enable "
            "`repo_governance.push.bypass.allow_skip_preflight`."
        )
    if args.skip_post_push and not policy.bypass.allow_skip_post_push:
        state.errors.append(
            "Repo policy blocks `--skip-post-push` for `devctl push`. "
            "Remove the flag or enable "
            "`repo_governance.push.bypass.allow_skip_post_push`."
        )


def _live_current_branch(repo_root: Path) -> str:
    code, branch, error = run_git_capture(
        ["rev-parse", "--abbrev-ref", "HEAD"],
        repo_root=repo_root,
    )
    if code != 0:
        return ""
    return (branch or error or "").strip()


def _protected_branch_errors(branch: str, policy) -> list[str]:
    if branch == policy.release_branch:
        return [
            f"Branch `{branch}` is release-only. Use `devctl ship` for release/tag pushes."
        ]
    return [f"Direct pushes to protected branch `{branch}` are blocked by repo policy."]


def _matches_allowed_prefixes(branch: str, prefixes: tuple[str, ...]) -> bool:
    if not prefixes:
        return True
    return any(branch.startswith(prefix) for prefix in prefixes)


def _emit_push_progress_notice(message: str) -> None:
    """Emit an interactive progress notice without corrupting stdout reports."""
    print(f"[devctl push] {message}", file=sys.stderr, flush=True)


def _run_fetch_and_preflight(state: Any, policy: Any, args: Any) -> None:
    """Compatibility adapter for sync's governed-push path."""
    run_fetch_and_preflight(
        state,
        PushPreflightFlowInputs(policy=policy, args=args),
    )


def run_push_action(
    args,
    *,
    repo_root: Path = REPO_ROOT,
    policy=None,
    emit_output_report: bool = True,
    run_cmd_fn=None,
    build_post_push_commands_fn=None,
    publication_authorization_fn=None,
    writer=None,
    piper=None,
    commit_pipeline: Any = None,
) -> tuple[int, dict[str, Any]]:
    resolved_policy = policy or load_push_policy(
        repo_root=repo_root,
        policy_path=getattr(args, "quality_policy", None),
    )
    state = _load_run_state(
        resolved_policy, args, repo_root=repo_root, commit_pipeline=commit_pipeline
    )
    head_commit = current_head_commit_sha(repo_root=repo_root)
    if bool(args.execute) and not state.errors:
        persist_push_progress_snapshot(
            build_push_report_context(
                repo_root=repo_root,
                policy=resolved_policy,
                state=state,
                args=args,
                head_commit=head_commit,
            ),
            reason="push_preflight_running",
            operator_guidance=(
                "No git push has started. Governed publication is in preflight "
                "validation for the current HEAD; remote publication can only start "
                "after validation_ready=true."
            ),
            stages=PushStageTruth(),
        )
    run_fetch_and_preflight(
        state,
        PushPreflightFlowInputs(
            policy=resolved_policy,
            args=args,
            repo_root=repo_root,
            requested_by=REQUESTED_BY,
            run_cmd_fn=run_cmd if run_cmd_fn is None else run_cmd_fn,
            commit_pipeline=commit_pipeline,
        ),
    )
    head_commit = finish_preflight_before_publication(
        state,
        resolved_policy,
        PushPublicationGateInputs(
            repo_root=repo_root,
            run_cmd_fn=run_cmd_fn,
            commit_pipeline=commit_pipeline,
            publication_authorization_fn=(
                publication_authorization_fn or publication_authorization_decision
            ),
            pass_commit_pipeline_to_authorization=publication_authorization_fn is None,
            head_commit=head_commit,
            current_head_fn=current_head_commit_sha,
        ),
    )
    requested_approved_target_identity = str(
        getattr(args, "approved_target_identity", "") or ""
    ).strip()
    if (
        requested_approved_target_identity
        and state.approved_target_identity
        and requested_approved_target_identity != state.approved_target_identity
    ):
        append_finding(
            state,
            APPROVED_TARGET_IDENTITY_VIOLATION,
            "Requested approved target identity does not match live authorization.",
            evidence=dict(
                requested_approved_target_identity=requested_approved_target_identity,
                live_approved_target_identity=state.approved_target_identity,
            ),
        )
    approved_target_identity = state.approved_target_identity
    report_context = build_push_report_context(
        repo_root=repo_root,
        policy=resolved_policy,
        state=state,
        args=args,
        head_commit=head_commit,
        approved_target_identity=approved_target_identity,
    )
    if (
        bool(args.execute)
        and not state.errors
        and not (state.branch_has_remote and state.ahead == 0)
    ):
        persist_push_progress_snapshot(
            report_context,
            reason="push_pending",
            operator_guidance=(
                "Governed push is running for the current HEAD. Wait for the managed "
                "latest push report or command completion before retrying."
            ),
            stages=PushStageTruth(validation_ready=True),
        )
    command_runner = run_cmd if run_cmd_fn is None else run_cmd_fn
    post_push_commands = (
        build_post_push_commands
        if build_post_push_commands_fn is None
        else build_post_push_commands_fn
    )

    outcome = execute_push_flow_under_publication_suspension(
        state=state,
        policy=resolved_policy,
        args=args,
        repo_root=repo_root,
        report_context=report_context,
        command_runner=command_runner,
        post_push_commands=post_push_commands,
        head_commit=head_commit,
        requested_by=REQUESTED_BY,
        progress_notice_fn=_emit_push_progress_notice,
        published_remote_snapshot_fn=persist_published_remote_snapshot,
    )
    report = build_push_report_payload(report_context, outcome=outcome)
    if bool(args.execute):
        sync_commit_pipeline_with_push_report(
            repo_root=repo_root,
            current_branch=state.branch,
            current_remote=state.remote,
            current_head_commit=current_head_commit_sha(repo_root=repo_root),
            approved_target_identity=approved_target_identity,
            report=report,
        )
    return finish_push_report(
        PushReportFinishInputs(
            args=args,
            repo_root=repo_root,
            report=report,
            artifact_path=report_context.artifact_path,
            outcome_ok=outcome.ok,
            emit_output_report=emit_output_report,
            writer=write_output if writer is None else writer,
            piper=pipe_output if piper is None else piper,
        )
    )


def run(args) -> int:
    """Validate and optionally execute a guarded push for the current branch."""
    from .governed_executor import GovernedVcsExecutor

    if bool(getattr(args, "execute", False)):
        obedience_report = push_control_decision_obedience_report(
            args,
            repo_root=REPO_ROOT,
        )
        if not obedience_report or not bool(obedience_report.get("ok")):
            report = {
                "ok": False,
                "command": "devctl.push",
                "reason": "control_decision_obedience_failed",
                "control_decision_obedience": obedience_report
                or {
                    "ok": False,
                    "reason": "no_valid_control_decision",
                },
            }
            emit_push_control_decision_report(args, report)
            return 1

    resolved_policy = load_push_policy(
        repo_root=REPO_ROOT,
        policy_path=getattr(args, "quality_policy", None),
    )
    executor = GovernedVcsExecutor(
        repo_root=REPO_ROOT,
        push_policy=resolved_policy,
    )
    pipeline = executor.load_pipeline()
    state = _load_run_state(
        resolved_policy,
        args,
        repo_root=REPO_ROOT,
        commit_pipeline=pipeline,
    )
    routed_exit = maybe_run_executor_routed_push(
        args=args,
        resolved_policy=resolved_policy,
        state=state,
        executor=executor,
        pipeline=pipeline,
    )
    if routed_exit is not None:
        return routed_exit
    exit_code, _ = run_push_action(args, policy=resolved_policy)
    return exit_code


def build_push_args(
    *,
    remote: str | None = None,
    quality_policy: str | None = None,
    execute: bool = False,
    skip_preflight: bool = False,
    skip_post_push: bool = False,
    approved_target_identity: str | None = None,
    actor: str = "",
    role: str = "",
    session_id: str = "",
    control_decision_input: str = "",
    format: str = "json",
    output: str | None = None,
    pipe_command: str | None = None,
    pipe_args: list[str] | None = None,
) -> SimpleNamespace:
    """Build a simple argparse-like object for programmatic push execution."""
    return SimpleNamespace(
        remote=remote,
        quality_policy=quality_policy,
        execute=execute,
        skip_preflight=skip_preflight,
        skip_post_push=skip_post_push,
        approved_target_identity=approved_target_identity,
        actor=actor,
        role=role,
        session_id=session_id,
        control_decision_input=control_decision_input,
        format=format,
        output=output,
        pipe_command=pipe_command,
        pipe_args=pipe_args,
    )
