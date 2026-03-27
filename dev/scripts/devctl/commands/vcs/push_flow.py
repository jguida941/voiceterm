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


def execute_push_flow(state: "PushRunState", policy, args) -> PushFlowOutcome:
    return execute_push_flow_with_dependencies(
        state,
        policy,
        args,
        run_cmd_fn=run_cmd,
        build_post_push_commands_fn=build_post_push_commands,
    )


def execute_push_flow_with_dependencies(
    state: "PushRunState",
    policy,
    args,
    *,
    run_cmd_fn: Callable[..., dict[str, object]],
    build_post_push_commands_fn: Callable[..., list[str]],
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

    push_cmd = ["git", "push", state.remote, state.branch]
    if not state.branch_has_remote:
        push_cmd = ["git", "push", "--set-upstream", state.remote, state.branch]
    state.push_step = run_cmd_fn("git-push", push_cmd, cwd=REPO_ROOT)
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
        run_cmd_fn=run_cmd_fn,
        build_post_push_commands_fn=build_post_push_commands_fn,
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
) -> bool:
    for index, command in enumerate(
        build_post_push_commands_fn(policy, quality_policy_path=quality_policy_path),
        start=1,
    ):
        step = run_cmd_fn(
            f"push-post-{index:02d}",
            ["bash", "-lc", command],
            cwd=REPO_ROOT,
        )
        state.post_push_steps.append(step)
        if step["returncode"] != 0:
            return False
    return True
