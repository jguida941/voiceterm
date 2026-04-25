"""Execution-stage helpers for the governed branch push flow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...common import run_cmd
from ...config import REPO_ROOT
from ...governance.push_policy import build_post_push_commands
from .push_report import PushStageTruth

if TYPE_CHECKING:
    from .push import PushRunState


@dataclass(frozen=True, slots=True)
class PushFlowOutcome:
    """Resolved outcome for one governed push attempt."""

    ok: bool
    reason: str
    operator_guidance: str
    stages: PushStageTruth
    partial_progress: bool = False

    @property
    def status(self) -> str:
        return self.stages.highest_stage()


@dataclass(frozen=True, slots=True)
class PushFlowDependencies:
    run_cmd_fn: Callable[..., dict[str, object]]
    build_post_push_commands_fn: Callable[..., list[str]]
    published_remote_snapshot_fn: Callable[[str, str, bool], None] | None = None
    progress_notice_fn: Callable[[str], None] | None = None


def execute_push_flow(state: "PushRunState", policy, args) -> PushFlowOutcome:
    return execute_push_flow_with_dependencies(
        state,
        policy,
        args,
        PushFlowDependencies(
            run_cmd_fn=run_cmd,
            build_post_push_commands_fn=build_post_push_commands,
        ),
    )


def execute_push_flow_with_dependencies(
    state: "PushRunState",
    policy,
    args,
    dependencies: PushFlowDependencies,
) -> PushFlowOutcome:
    if state.errors:
        return PushFlowOutcome(
            ok=False,
            reason="validation_failed",
            operator_guidance=(
                "Fix the reported policy or preflight failures, then rerun "
                "`devctl push`."
            ),
            stages=PushStageTruth(),
        )
    if state.branch_has_remote and state.ahead == 0:
        return PushFlowOutcome(
            ok=True,
            reason="branch_already_pushed",
            operator_guidance=(
                "No push is required; the current branch already matches the remote."
            ),
            stages=PushStageTruth(
                validation_ready=True,
                published_remote=True,
            ),
        )
    if not args.execute:
        return PushFlowOutcome(
            ok=True,
            reason="execute_flag_required",
            operator_guidance=(
                "Validation passed. Re-run with `--execute` to push this branch."
            ),
            stages=PushStageTruth(validation_ready=True),
        )

    # ReviewSnapshot refresh happens before routed preflight in push.py and is
    # committed through the managed projection receipt path when it changes the
    # tracked projection. By the time execution reaches git push, preflight has
    # already validated the current committed freshness state.

    push_cmd = _governed_git_push_cmd(state.remote, state.branch)
    if not state.branch_has_remote:
        push_cmd = _governed_git_push_cmd(
            state.remote,
            state.branch,
            set_upstream=True,
        )
    state.push_step = dependencies.run_cmd_fn(
        "git-push",
        push_cmd,
        cwd=REPO_ROOT,
    )
    if state.push_step["returncode"] != 0:
        return PushFlowOutcome(
            ok=False,
            reason="git_push_failed",
            operator_guidance=(
                "Inspect the push failure, repair the git state, and rerun "
                "`devctl push --execute`."
            ),
            stages=PushStageTruth(validation_ready=True),
        )
    if dependencies.published_remote_snapshot_fn is not None:
        dependencies.published_remote_snapshot_fn(
            "post_push_bundle_pending",
            (
                "Push completed and remote publication is recorded. The post-push "
                "bundle still needs to finish before the slice is fully green."
            ),
            True,
        )
    if dependencies.progress_notice_fn is not None:
        dependencies.progress_notice_fn(
            "Remote publication recorded for the current HEAD; running post-push bundle."
        )
    if args.skip_post_push:
        return PushFlowOutcome(
            ok=True,
            reason="post_push_skipped_by_policy",
            operator_guidance=(
                "Push completed. Repo policy allowed `--skip-post-push`, so the "
                "branch is published but not post-push green."
            ),
            stages=PushStageTruth(
                validation_ready=True,
                published_remote=True,
            ),
            partial_progress=True,
        )
    if run_post_push_bundle(
        state,
        policy,
        quality_policy_path=getattr(args, "quality_policy", None),
        run_cmd_fn=dependencies.run_cmd_fn,
        build_post_push_commands_fn=dependencies.build_post_push_commands_fn,
        progress_notice_fn=dependencies.progress_notice_fn,
    ):
        return PushFlowOutcome(
            ok=True,
            reason="push_completed",
            operator_guidance="Push and post-push audit completed successfully.",
            stages=PushStageTruth(
                validation_ready=True,
                published_remote=True,
                post_push_green=True,
            ),
        )
    return PushFlowOutcome(
        ok=False,
        reason="post_push_bundle_failed",
        operator_guidance=(
            "The branch was published to the remote, but the post-push bundle "
            "failed. Fix the failure before merge."
        ),
        stages=PushStageTruth(
            validation_ready=True,
            published_remote=True,
        ),
        partial_progress=True,
    )


def run_post_push_bundle(
    state: "PushRunState",
    policy,
    *,
    quality_policy_path: str | None,
    run_cmd_fn: Callable[..., dict[str, object]],
    build_post_push_commands_fn: Callable[..., list[str]],
    progress_notice_fn: Callable[[str], None] | None = None,
) -> bool:
    commands = build_post_push_commands_fn(
        policy,
        quality_policy_path=quality_policy_path,
        since_ref=state.post_push_since_ref,
    )
    total_commands = len(commands)
    for index, command in enumerate(commands, start=1):
        if progress_notice_fn is not None:
            progress_notice_fn(
                f"Post-push step {index}/{total_commands}: {command}"
            )
        step = run_cmd_fn(
            f"push-post-{index:02d}",
            ["bash", "-lc", command],
            cwd=REPO_ROOT,
        )
        state.post_push_steps.append(step)
        if step["returncode"] != 0:
            if progress_notice_fn is not None:
                progress_notice_fn(
                    f"Post-push step {index}/{total_commands} failed with rc={step['returncode']}."
                )
            return False
    return True


def _governed_git_push_cmd(
    remote: str,
    branch: str,
    *,
    set_upstream: bool = False,
) -> list[str]:
    cmd = ["git", "-c", "devctl.governed-push=true", "push"]
    if set_upstream:
        cmd.append("--set-upstream")
    cmd.extend([remote, branch])
    return cmd
