"""Policy-driven guarded push flow for the current branch."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from ...collect import collect_git_status
from ...common import emit_output, pipe_output, run_cmd, write_output
from ...config import REPO_ROOT
from ...governance.push_policy import (
    build_post_push_commands,
    load_push_policy,
)
from ...governance.push_routing import PushRefRoutingState, build_preflight_shell_command
from ...governance.push_state import current_upstream_ref
from ...runtime import ActionResult, TypedAction
from ...runtime.vcs import branch_divergence, remote_branch_exists, remote_exists
from .push_report import PushReportInputs, build_push_report, render_push_report

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
    return state


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


def _execute_push_flow(state: PushRunState, policy, args) -> tuple[bool, str, str, str]:
    if state.errors:
        return (
            False,
            "blocked",
            "validation_failed",
            "Fix the reported policy or preflight failures, then rerun `devctl push`.",
        )
    if state.branch_has_remote and state.ahead == 0:
        return (
            True,
            "already-synced",
            "branch_already_pushed",
            "No push is required; the current branch already matches the remote.",
        )
    if not args.execute:
        return (
            True,
            "ready",
            "execute_flag_required",
            "Validation passed. Re-run with `--execute` to push this branch.",
        )

    push_cmd = ["git", "push", state.remote, state.branch]
    if not state.branch_has_remote:
        push_cmd = ["git", "push", "--set-upstream", state.remote, state.branch]
    state.push_step = run_cmd("git-push", push_cmd, cwd=REPO_ROOT)
    if state.push_step["returncode"] != 0:
        return (
            False,
            "push-failed",
            "git_push_failed",
            "Inspect the push failure, repair the git state, and rerun `devctl push --execute`.",
        )
    if args.skip_post_push:
        return (
            True,
            "pushed",
            "push_completed",
            "Push completed. Post-push bundle was skipped for this run.",
        )
    if _run_post_push_bundle(state, policy, getattr(args, "quality_policy", None)):
        return (
            True,
            "pushed",
            "push_completed",
            "Push and post-push audit completed successfully.",
        )
    return (
        False,
        "post-push-failed",
        "post_push_bundle_failed",
        "The branch was pushed, but the post-push bundle failed. Fix the failure before merge.",
    )


def _run_post_push_bundle(
    state: PushRunState,
    policy,
    quality_policy_path: str | None,
) -> bool:
    for index, command in enumerate(
        build_post_push_commands(policy, quality_policy_path=quality_policy_path),
        start=1,
    ):
        step = run_cmd(
            f"push-post-{index:02d}",
            ["bash", "-lc", command],
            cwd=REPO_ROOT,
        )
        state.post_push_steps.append(step)
        if step["returncode"] != 0:
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


def _build_action_result(
    *,
    status: str,
    reason: str,
    ok: bool,
    warnings: list[str],
    partial_progress: bool,
    operator_guidance: str,
) -> ActionResult:
    return ActionResult(
        schema_version=1,
        contract_id="ActionResult",
        action_id="vcs.push",
        ok=ok,
        status=status,
        reason=reason,
        retryable=not ok,
        partial_progress=partial_progress,
        operator_guidance=operator_guidance,
        warnings=tuple(warnings),
    )


def run(args) -> int:
    """Validate and optionally execute a guarded push for the current branch."""
    policy = load_push_policy(policy_path=getattr(args, "quality_policy", None))
    state = _load_run_state(policy, args)
    _run_fetch_and_preflight(state, policy, args)
    ok, status, reason, operator_guidance = _execute_push_flow(state, policy, args)
    typed_action = asdict(
        _build_typed_action(
            repo_pack_id=policy.repo_pack_id,
            branch=state.branch,
            remote=state.remote,
            args=args,
        )
    )
    action_result = _build_action_result(
        status=status,
        reason=reason,
        ok=ok,
        warnings=state.warnings,
        partial_progress=status == "post-push-failed",
        operator_guidance=operator_guidance,
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
        typed_action=typed_action,
        action_result=action_result,
        warnings=state.warnings,
        errors=state.errors,
    )
    report = build_push_report(report_inputs)
    output = json.dumps(report, indent=2) if args.format == "json" else render_push_report(report)
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_rc != 0:
        return pipe_rc
    return 0 if ok else 1
