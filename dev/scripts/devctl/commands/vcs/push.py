"""Policy-driven guarded push flow for the current branch."""

from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from ...collect import collect_git_status
from ...common import emit_output, pipe_output, run_cmd, write_output
from ...config import REPO_ROOT
from ...governance.push_policy import build_post_push_commands, load_push_policy
from ...governance.push_routing import (
    PushRefRoutingState,
    build_preflight_shell_command,
    resolve_preflight_since_ref,
)
from ...governance.push_state import current_head_commit_sha, current_upstream_ref
from ...runtime import TypedAction
from ...runtime.push_authorization import publication_authorization_decision
from ...runtime.vcs import (
    branch_divergence,
    remote_branch_exists,
    remote_exists,
    run_git_capture,
)
from .push_artifact import (
    append_push_receipt,
    load_latest_push_report,
    latest_push_report_relpath,
    persist_latest_push_report,
    serialize_push_report,
)
from .push_flow import PushFlowDependencies, execute_push_flow_with_dependencies
from .push_report import render_push_report
from .push_snapshot import (
    PushReportContext,
    build_push_report_payload,
    persist_published_remote_snapshot,
)
from .governed_executor_actions import build_push_action

REQUESTED_BY = "devctl.push"


@dataclass(slots=True)
class PushRunState:
    """Mutable execution state for one guarded push attempt."""

    branch: str = ""
    remote: str = ""
    dirty_paths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    fetch_step: dict[str, Any] | None = None
    preflight_step: dict[str, Any] | None = None
    push_step: dict[str, Any] | None = None
    post_push_steps: list[dict[str, Any]] = field(default_factory=list)
    post_push_since_ref: str = ""
    branch_has_remote: bool = False
    ahead: int | None = None
    approved_target_identity: str = ""
    push_authorization_id: str = ""
    push_authorization_mode: str = ""


def _load_run_state(
    policy,
    args,
    *,
    repo_root: Path = REPO_ROOT,
) -> PushRunState:
    state = PushRunState()
    state.remote = str(args.remote or policy.default_remote).strip() or policy.default_remote
    state.warnings.extend(policy.warnings)
    _append_bypass_policy_errors(state, policy, args)
    git = _collect_git_status_for_repo(repo_root)
    if "error" in git:
        state.errors.append(str(git["error"]))
        return state

    state.branch = str(git.get("branch", "")).strip()
    state.dirty_paths = _summarize_dirty_paths(
        git.get("changes", []),
        exclude_paths=_push_exclusion_paths(policy),
    )
    if state.branch == "HEAD":
        state.errors.append("Detached HEAD is not supported. Check out a branch first.")
    if state.dirty_paths:
        state.errors.append("Working tree has uncommitted changes. Commit or stash before push.")
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


def _append_publication_authorization_errors(
    state: PushRunState,
    *,
    repo_root: Path = REPO_ROOT,
    publication_authorization_fn=None,
) -> None:
    """Fail closed when publication proof for the current HEAD is missing."""
    if state.errors:
        return
    if state.branch_has_remote and state.ahead == 0:
        return
    authorization_fn = (
        publication_authorization_decision
        if publication_authorization_fn is None
        else publication_authorization_fn
    )
    decision = authorization_fn(repo_root=repo_root)
    if decision.authorized:
        authorization = decision.push_authorization
        if authorization is not None:
            state.approved_target_identity = authorization.approved_target_identity
            state.push_authorization_id = authorization.authorization_id
            state.push_authorization_mode = authorization.approval_mode
        return
    summary = str(decision.summary or decision.reason or "").strip()
    detail = f" {summary}" if summary else ""
    state.errors.append(
        "Publication authorization blocks `devctl push`: "
        f"reason=`{decision.reason}`.{detail}"
    )


def _protected_branch_errors(branch: str, policy) -> list[str]:
    if branch == policy.release_branch:
        return [
            f"Branch `{branch}` is release-only. Use `devctl ship` for release/tag pushes."
        ]
    return [f"Direct pushes to protected branch `{branch}` are blocked by repo policy."]


def _run_fetch_and_preflight(
    state: PushRunState,
    policy,
    args,
    *,
    repo_root: Path = REPO_ROOT,
    run_cmd_fn=None,
) -> None:
    if state.errors:
        return
    command_runner = run_cmd if run_cmd_fn is None else run_cmd_fn
    state.fetch_step = command_runner(
        "git-fetch",
        ["git", "fetch", state.remote],
        cwd=repo_root,
    )
    if state.fetch_step["returncode"] != 0:
        state.errors.append(f"git fetch failed for remote `{state.remote}`.")
        return

    state.branch_has_remote = remote_branch_exists(
        state.remote,
        state.branch,
        repo_root=repo_root,
    )
    route_state = PushRefRoutingState(
        current_branch=state.branch,
        upstream_ref=current_upstream_ref(repo_root=repo_root),
        branch_has_remote=state.branch_has_remote,
    )
    state.post_push_since_ref = resolve_preflight_since_ref(
        remote=state.remote,
        development_branch=policy.development_branch,
        release_branch=policy.release_branch,
        since_ref_template=policy.preflight.since_ref_template,
        route_state=route_state,
    )
    if state.branch_has_remote and not _record_divergence(
        state,
        state.remote,
        state.branch,
        repo_root=repo_root,
    ):
        return
    if state.branch_has_remote and state.ahead == 0:
        return
    if args.skip_preflight:
        return

    preflight_command = build_preflight_shell_command(
        policy,
        remote=state.remote,
        route_state=route_state,
        quality_policy_path=getattr(args, "quality_policy", None),
    )
    state.preflight_step = command_runner(
        "push-preflight",
        ["bash", "-lc", preflight_command],
        cwd=repo_root,
    )
    if state.preflight_step["returncode"] != 0:
        state.errors.append("Configured push preflight failed.")


def _record_divergence(
    state: PushRunState,
    remote: str,
    branch: str,
    *,
    repo_root: Path = REPO_ROOT,
) -> bool:
    divergence = branch_divergence(remote, branch, repo_root=repo_root)
    if divergence["error"]:
        state.errors.append(
            f"Unable to compute divergence for `{branch}`: {divergence['error']}"
        )
        return False
    state.ahead = int(divergence["ahead"] or 0)
    behind = int(divergence["behind"] or 0)
    if behind > 0:
        state.errors.append(f"Branch `{branch}` is behind {remote}/{branch}; sync it before push.")
        return False
    return True


def _summarize_dirty_paths(
    changes: list[dict[str, object]],
    *,
    exclude_paths: tuple[str, ...] = (),
) -> list[str]:
    exclude_set = set(exclude_paths)
    paths: list[str] = []
    for change in changes:
        path = str(change.get("path", "")).strip()
        if not path or path in exclude_set:
            continue
        paths.append(path)
    return paths


def _push_exclusion_paths(policy) -> tuple[str, ...]:
    return (
        *policy.checkpoint.compatibility_projection_paths,
        *policy.checkpoint.advisory_context_paths,
    )


def _matches_allowed_prefixes(branch: str, prefixes: tuple[str, ...]) -> bool:
    if not prefixes:
        return True
    return any(branch.startswith(prefix) for prefix in prefixes)


def _emit_push_progress_notice(message: str) -> None:
    """Emit an interactive progress notice without corrupting stdout reports."""
    print(f"[devctl push] {message}", file=sys.stderr, flush=True)


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
) -> tuple[int, dict[str, Any]]:
    """Run the governed push flow and return ``(exit_code, report)``."""
    resolved_policy = policy or load_push_policy(
        repo_root=repo_root,
        policy_path=getattr(args, "quality_policy", None),
    )
    state = _load_run_state(
        resolved_policy,
        args,
        repo_root=repo_root,
    )
    head_commit = current_head_commit_sha(repo_root=repo_root)
    _run_fetch_and_preflight(
        state,
        resolved_policy,
        args,
        repo_root=repo_root,
        run_cmd_fn=run_cmd_fn,
    )
    _append_publication_authorization_errors(
        state,
        repo_root=repo_root,
        publication_authorization_fn=publication_authorization_fn,
    )
    approved_target_identity = (
        str(getattr(args, "approved_target_identity", "") or "").strip()
        or state.approved_target_identity
    )
    typed_action = asdict(
        build_push_action(
            repo_pack_id=resolved_policy.repo_pack_id,
            branch=state.branch,
            remote=state.remote,
            execute=bool(args.execute),
            skip_preflight=bool(args.skip_preflight),
            skip_post_push=bool(args.skip_post_push),
            approved_target_identity=approved_target_identity,
        )
    )
    artifact_path = latest_push_report_relpath(repo_root=repo_root)
    report_context = PushReportContext(
        repo_root=repo_root,
        policy=resolved_policy,
        state=state,
        args=args,
        head_commit=head_commit,
        typed_action=typed_action,
        artifact_path=artifact_path,
        approved_target_identity=approved_target_identity,
        push_authorization_id=state.push_authorization_id,
        push_authorization_mode=state.push_authorization_mode,
    )
    command_runner = run_cmd if run_cmd_fn is None else run_cmd_fn
    post_push_commands = (
        build_post_push_commands
        if build_post_push_commands_fn is None
        else build_post_push_commands_fn
    )
    def repo_bound_runner(
        name: str,
        cmd: list[str],
        cwd=None,
        env: dict[str, str] | None = None,
    ) -> dict[str, object]:
        del cwd
        return command_runner(name, cmd, cwd=repo_root, env=env)
    outcome = execute_push_flow_with_dependencies(
        state,
        resolved_policy,
        args,
        PushFlowDependencies(
            run_cmd_fn=repo_bound_runner,
            build_post_push_commands_fn=post_push_commands,
            published_remote_snapshot_fn=lambda reason, operator_guidance, partial_progress: (
                persist_published_remote_snapshot(
                    report_context,
                    reason=reason,
                    operator_guidance=operator_guidance,
                    partial_progress=partial_progress,
                )
            ),
            progress_notice_fn=_emit_push_progress_notice,
        ),
    )
    report = build_push_report_payload(report_context, outcome=outcome)
    if not emit_output_report:
        persist_latest_push_report(report, repo_root=repo_root)
        append_push_receipt(report, repo_root=repo_root)
        return (0 if outcome.ok else 1), report

    append_push_receipt(report, repo_root=repo_root)
    report_json = serialize_push_report(report)
    output = report_json if args.format == "json" else render_push_report(report)
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        additional_outputs=((report_json, artifact_path),),
        writer=write_output if writer is None else writer,
        piper=pipe_output if piper is None else piper,
    )
    if pipe_rc != 0:
        return pipe_rc, report
    return (0 if outcome.ok else 1), report


def run(args) -> int:
    """Validate and optionally execute a guarded push for the current branch."""
    from .governed_executor import GovernedVcsExecutor
    from .governed_executor_actions import _PUSHABLE_PIPELINE_STATES

    resolved_policy = load_push_policy(
        repo_root=REPO_ROOT,
        policy_path=getattr(args, "quality_policy", None),
    )
    state = _load_run_state(
        resolved_policy,
        args,
        repo_root=REPO_ROOT,
    )
    executor = GovernedVcsExecutor(
        repo_root=REPO_ROOT,
        push_policy=resolved_policy,
    )
    pipeline = executor.load_pipeline()
    active_pipeline_matches_branch = bool(pipeline.pipeline_id) and bool(state.branch) and (
        pipeline.branch == state.branch
    )
    if (
        active_pipeline_matches_branch
        and pipeline.state in _PUSHABLE_PIPELINE_STATES
        and bool(pipeline.commit_sha)
    ):
        result = executor.execute(
            build_push_action(
                repo_pack_id=resolved_policy.repo_pack_id,
                branch=str(pipeline.branch or getattr(args, "branch", "") or ""),
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
                requested_by=REQUESTED_BY,
            )
        )
        report = load_latest_push_report(repo_root=REPO_ROOT)
        if report is not None:
            report_json = serialize_push_report(report)
            output = report_json if args.format == "json" else render_push_report(report)
            pipe_rc = emit_output(
                output,
                output_path=args.output,
                pipe_command=args.pipe_command,
                pipe_args=args.pipe_args,
                additional_outputs=((report_json, latest_push_report_relpath(repo_root=REPO_ROOT)),),
                writer=write_output,
                piper=pipe_output,
            )
            if pipe_rc != 0:
                return pipe_rc
        return 0 if result.ok else 1
    exit_code, _ = run_push_action(args, policy=resolved_policy)
    return exit_code


def _execute_push_flow(state: PushRunState, policy, args):
    """Compatibility seam for older callers that patch the push executor directly."""
    return execute_push_flow_with_dependencies(
        state,
        policy,
        args,
        PushFlowDependencies(
            run_cmd_fn=run_cmd,
            build_post_push_commands_fn=build_post_push_commands,
        ),
    )


def _collect_git_status_for_repo(repo_root: Path) -> dict[str, object]:
    """Return branch and dirty state info for one repo root."""
    if repo_root == REPO_ROOT:
        return collect_git_status()

    branch_code, branch, branch_error = run_git_capture(
        ["rev-parse", "--abbrev-ref", "HEAD"],
        repo_root=repo_root,
    )
    if branch_code != 0:
        message = branch_error or f"git rev-parse exited with code {branch_code}"
        return {"error": message}

    status_code, status_output, status_error = run_git_capture(
        ["status", "--porcelain", "--untracked-files=all"],
        repo_root=repo_root,
    )
    if status_code != 0:
        message = status_error or f"git status exited with code {status_code}"
        return {"error": message}

    changes: list[dict[str, str]] = []
    for line in status_output.splitlines():
        if not line:
            continue
        parts = line.split(maxsplit=1)
        status = parts[0].strip()
        path = parts[1] if len(parts) == 2 else ""
        if "->" in path:
            path = path.split("->")[-1].strip()
        changes.append({"status": status, "path": path})
    return {"branch": branch, "changes": changes}


def build_push_args(
    *,
    remote: str | None = None,
    quality_policy: str | None = None,
    execute: bool = False,
    skip_preflight: bool = False,
    skip_post_push: bool = False,
    approved_target_identity: str | None = None,
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
        format=format,
        output=output,
        pipe_command=pipe_command,
        pipe_args=pipe_args,
    )
