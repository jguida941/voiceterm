"""Execution-stage helpers for the governed branch push flow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ...common import run_cmd
from ...config import REPO_ROOT
from ...governance.push_policy import build_post_push_commands
from ...governance.push_state import current_head_commit_sha
from ...runtime.vcs import run_git_capture
from .push_findings import append_finding
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
    current_head_sha_fn: Callable[..., str] | None = None
    remote_head_sha_fn: Callable[..., str] | None = None
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


def bind_command_runner_to_repo(command_runner, repo_root):
    """Return a command runner that ignores caller cwd and uses repo_root."""

    def repo_bound_runner(
        name: str,
        cmd: list[str],
        cwd=None,
        env: dict[str, str] | None = None,
    ) -> dict[str, object]:
        del cwd
        return command_runner(name, cmd, cwd=repo_root, env=env)

    return repo_bound_runner


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
            stages=PushStageTruth(validation_ready=True, published_remote=True),
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

    # ReviewSnapshot refresh happens before routed preflight in push.py. Managed
    # projection receipts move HEAD first, then the snapshot receipt refresh
    # binds the external-review file to that contiguous receipt chain before
    # freshness guards and publication authorization consume it.

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
    proof_outcome = _verify_remote_publication(state, dependencies)
    if proof_outcome is not None:
        return proof_outcome
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
        state.post_push_steps.append(
            _skipped_step(
                "push-post-skipped",
                "post-push bundle skipped by policy",
            )
        )
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
    if total_commands == 0:
        state.post_push_steps.append(
            _skipped_step(
                "push-post-none", "post-push bundle has no configured commands"
            )
        )
        return True
    for index, command in enumerate(commands, start=1):
        if progress_notice_fn is not None:
            progress_notice_fn(f"Post-push step {index}/{total_commands}: {command}")
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


def _remote_head_sha(remote: str, branch: str, *, repo_root: Path) -> str:
    code, output, _error = run_git_capture(
        ["ls-remote", "--heads", remote, f"refs/heads/{branch}"],
        repo_root=repo_root,
    )
    if code != 0:
        return ""
    first_line = output.splitlines()[0].strip() if output.splitlines() else ""
    return first_line.split()[0] if first_line else ""


remote_head_sha = _remote_head_sha


def _state_repo_root(state: object) -> Path:
    raw = str(getattr(state, "repo_root", "") or "").strip()
    return Path(raw) if raw else REPO_ROOT


def _skipped_step(name: str, reason: str) -> dict[str, object]:
    return dict(
        name=name,
        cmd=[],
        cwd=str(REPO_ROOT),
        returncode=0,
        duration_s=0.0,
        skipped=True,
        reason=reason,
    )


def _verify_remote_publication(
    state: object,
    dependencies: PushFlowDependencies,
) -> PushFlowOutcome | None:
    if dependencies.remote_head_sha_fn is None:
        return None
    repo_root = _state_repo_root(state)
    remote_head_after = dependencies.remote_head_sha_fn(
        state.remote, state.branch, repo_root=repo_root
    )
    try:
        state.remote_head_after = remote_head_after
    except (AttributeError, TypeError):
        pass
    head_commit = (
        dependencies.current_head_sha_fn(repo_root=repo_root)
        if dependencies.current_head_sha_fn is not None
        else current_head_commit_sha(repo_root=repo_root)
    )
    if remote_head_after and remote_head_after == head_commit:
        return None
    append_finding(
        state,
        "SilentPushFailure",
        "git push returned success but the remote ref does not match current HEAD.",
        evidence=dict(
            branch=state.branch,
            remote=state.remote,
            head_commit=head_commit,
            remote_head_after=remote_head_after,
        ),
    )
    return PushFlowOutcome(
        ok=False,
        reason="remote_ref_not_updated",
        operator_guidance=(
            "The governed git push returned success, but the remote ref could not "
            "be proven at the current HEAD. Inspect the remote and retry through "
            "`devctl push --execute`."
        ),
        stages=PushStageTruth(),
    )
