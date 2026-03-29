"""Policy-driven guarded push flow for the current branch."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from ...collect import collect_git_status
from ...common import emit_output, pipe_output, run_cmd, write_output
from ...config import REPO_ROOT
from ...governance.push_policy import build_post_push_commands, load_push_policy
from ...governance.push_routing import PushRefRoutingState, build_preflight_shell_command
from ...governance.push_state import current_upstream_ref
from ...runtime import ActionResult, TypedAction
from ...runtime.startup_context import build_startup_context
from ...runtime.vcs import branch_divergence, remote_branch_exists, remote_exists
from .push_flow import PushFlowOutcome, execute_push_flow_with_dependencies
from .push_artifact import latest_push_report_relpath, serialize_push_report
from .push_report import (
    PushReportInputs,
    build_push_report,
    render_push_report,
)

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
    branch_has_remote: bool = False
    ahead: int | None = None


def _build_typed_action(
    *,
    repo_pack_id: str,
    branch: str,
    remote: str,
    args,
) -> TypedAction:
    parameters: dict[str, object] = {}
    parameters["branch"] = branch
    parameters["remote"] = remote
    parameters["execute"] = bool(args.execute)
    parameters["skip_preflight"] = bool(args.skip_preflight)
    parameters["skip_post_push"] = bool(args.skip_post_push)
    return TypedAction(
        schema_version=1,
        contract_id="TypedAction",
        action_id="vcs.push",
        repo_pack_id=repo_pack_id,
        parameters=parameters,
        requested_by=REQUESTED_BY,
        dry_run=not bool(args.execute),
    )


def _load_run_state(policy, args) -> PushRunState:
    state = PushRunState()
    state.remote = str(args.remote or policy.default_remote).strip() or policy.default_remote
    state.warnings.extend(policy.warnings)
    _append_bypass_policy_errors(state, policy, args)
    git = collect_git_status()
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
    if not remote_exists(state.remote):
        state.errors.append(f"Remote `{state.remote}` is not configured.")
    _append_startup_push_gate_errors(state)
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


def _append_startup_push_gate_errors(state: PushRunState) -> None:
    """Fail closed when startup/review state says governed push is not ready."""
    if state.errors:
        return
    ctx = build_startup_context(repo_root=REPO_ROOT)
    decision = ctx.push_decision
    if decision.action in {"run_devctl_push", "no_push_needed"}:
        return
    summary = str(decision.next_step_summary or decision.reason or "").strip()
    detail = f" {summary}" if summary else ""
    state.errors.append(
        "Startup push gate blocks `devctl push`: "
        f"push_decision=`{decision.action}` ({decision.reason}).{detail}"
    )


def _protected_branch_errors(branch: str, policy) -> list[str]:
    if branch == policy.release_branch:
        return [
            f"Branch `{branch}` is release-only. Use `devctl ship` for release/tag pushes."
        ]
    return [f"Direct pushes to protected branch `{branch}` are blocked by repo policy."]


def _run_fetch_and_preflight(state: PushRunState, policy, args) -> None:
    if state.errors:
        return
    state.fetch_step = run_cmd("git-fetch", ["git", "fetch", state.remote], cwd=REPO_ROOT)
    if state.fetch_step["returncode"] != 0:
        state.errors.append(f"git fetch failed for remote `{state.remote}`.")
        return

    state.branch_has_remote = remote_branch_exists(state.remote, state.branch)
    if state.branch_has_remote and not _record_divergence(state, state.remote, state.branch):
        return
    if args.skip_preflight:
        return

    preflight_command = build_preflight_shell_command(
        policy,
        remote=state.remote,
        route_state=PushRefRoutingState(
            current_branch=state.branch,
            upstream_ref=current_upstream_ref(),
            branch_has_remote=state.branch_has_remote,
        ),
        quality_policy_path=getattr(args, "quality_policy", None),
    )
    state.preflight_step = run_cmd(
        "push-preflight",
        ["bash", "-lc", preflight_command],
        cwd=REPO_ROOT,
    )
    if state.preflight_step["returncode"] != 0:
        state.errors.append("Configured push preflight failed.")


def _record_divergence(state: PushRunState, remote: str, branch: str) -> bool:
    divergence = branch_divergence(remote, branch)
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


def _execute_push_flow(state: PushRunState, policy, args) -> PushFlowOutcome:
    return execute_push_flow_with_dependencies(
        state,
        policy,
        args,
        run_cmd_fn=run_cmd,
        build_post_push_commands_fn=build_post_push_commands,
    )


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


def run(args) -> int:
    """Validate and optionally execute a guarded push for the current branch."""
    policy = load_push_policy(policy_path=getattr(args, "quality_policy", None))
    state = _load_run_state(policy, args)
    _run_fetch_and_preflight(state, policy, args)
    outcome = _execute_push_flow(state, policy, args)
    typed_action = asdict(
        _build_typed_action(
            repo_pack_id=policy.repo_pack_id,
            branch=state.branch,
            remote=state.remote,
            args=args,
        )
    )
    artifact_path = latest_push_report_relpath()
    action_result = ActionResult(
        schema_version=1,
        contract_id="ActionResult",
        action_id="vcs.push",
        ok=outcome.ok,
        status=outcome.status,
        reason=outcome.reason,
        retryable=not outcome.ok,
        partial_progress=outcome.partial_progress,
        operator_guidance=outcome.operator_guidance,
        warnings=tuple(state.warnings),
        artifact_paths=(artifact_path,),
    ).to_dict()
    report_inputs = PushReportInputs(
        policy=policy,
        branch=state.branch,
        remote=state.remote,
        execute=bool(args.execute),
        skip_preflight=bool(args.skip_preflight),
        skip_post_push=bool(args.skip_post_push),
        dirty_paths=state.dirty_paths,
        fetch_step=state.fetch_step,
        preflight_step=state.preflight_step,
        push_step=state.push_step,
        post_push_steps=state.post_push_steps,
        push_stages=outcome.stages,
        typed_action=typed_action,
        action_result=action_result,
        warnings=state.warnings,
        errors=state.errors,
        artifact_path=artifact_path,
    )
    report = build_push_report(report_inputs)
    report_json = serialize_push_report(report)
    output = report_json if args.format == "json" else render_push_report(report)
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        additional_outputs=((report_json, artifact_path),),
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_rc != 0:
        return pipe_rc
    return 0 if outcome.ok else 1
