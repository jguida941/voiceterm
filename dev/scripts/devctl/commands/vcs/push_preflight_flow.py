"""Fetch and validation-preflight flow for governed push."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...common import run_cmd
from ...config import REPO_ROOT
from ...governance.push_routing import (
    PushPreflightReportRouting,
    PushRefRoutingState,
    PushValidationRouting,
    build_preflight_shell_command,
    resolve_preflight_since_ref,
)
from ...governance.push_state import current_head_commit_sha, current_upstream_ref
from ...review_channel.event_store import push_window_write_suspension
from ...runtime.vcs import branch_divergence, remote_branch_exists
from .orphan_snapshot_advisory import append_orphan_snapshot_advisory
from .push_bridge_sync import (
    sync_bridge_projection_before_preflight as _sync_bridge_projection_before_preflight,
)
from .push_pipeline_scope import refresh_authorized_preflight_head_after_managed_receipts
from .push_preflight_projection import refresh_managed_projections_before_preflight
from .push_preflight_report import (
    PUSH_PREFLIGHT_CHECK_ROUTER_REPORT,
    annotate_preflight_step,
)
from .push_preflight_timeout import build_preflight_command_kwargs


@dataclass(frozen=True, slots=True)
class PushPreflightFlowInputs:
    policy: Any
    args: Any
    repo_root: Path = REPO_ROOT
    requested_by: str = "devctl.push"
    run_cmd_fn: Any = None
    commit_pipeline: Any = None


def run_fetch_and_preflight(
    state: Any,
    inputs: PushPreflightFlowInputs,
) -> None:
    if state.errors:
        return
    command_runner = run_cmd if inputs.run_cmd_fn is None else inputs.run_cmd_fn
    state.fetch_step = command_runner(
        "git-fetch",
        ["git", "fetch", state.remote],
        cwd=inputs.repo_root,
    )
    if state.fetch_step["returncode"] != 0:
        state.errors.append(f"git fetch failed for remote `{state.remote}`.")
        return

    state.branch_has_remote = remote_branch_exists(
        state.remote,
        state.branch,
        repo_root=inputs.repo_root,
    )
    route_state = PushRefRoutingState(
        current_branch=state.branch,
        upstream_ref=current_upstream_ref(repo_root=inputs.repo_root),
        branch_has_remote=state.branch_has_remote,
    )
    state.post_push_since_ref = resolve_preflight_since_ref(
        remote=state.remote,
        development_branch=inputs.policy.development_branch,
        release_branch=inputs.policy.release_branch,
        since_ref_template=inputs.policy.preflight.since_ref_template,
        route_state=route_state,
    )
    if state.branch_has_remote and not _record_divergence(
        state,
        state.remote,
        state.branch,
        repo_root=inputs.repo_root,
    ):
        return
    if state.branch_has_remote and state.ahead == 0:
        return
    append_orphan_snapshot_advisory(
        state.warnings,
        repo_root=inputs.repo_root,
        scan_trigger="push_preflight",
    )
    if inputs.args.skip_preflight:
        state.preflight_step = dict(
            name="push-preflight",
            cmd=[],
            cwd=str(inputs.repo_root),
            returncode=0,
            duration_s=0.0,
            skipped=True,
            reason="preflight skipped by policy",
        )
        return

    with push_window_write_suspension(
        repo_root=inputs.repo_root,
        window_kind="push_preflight",
        requested_by=inputs.requested_by,
        reason="governed push preflight owns projection writes",
        head_sha=current_head_commit_sha(repo_root=inputs.repo_root),
        branch=state.branch,
    ):
        _sync_bridge_projection_before_preflight(state, repo_root=inputs.repo_root)
        refresh_managed_projections_before_preflight(
            state,
            inputs.policy,
            repo_root=inputs.repo_root,
            command_runner=command_runner,
            quality_policy_path=getattr(inputs.args, "quality_policy", None),
        )
        if state.errors:
            return
        refresh_authorized_preflight_head_after_managed_receipts(
            state,
            commit_pipeline=inputs.commit_pipeline,
            repo_root=inputs.repo_root,
        )
        preflight_command = build_preflight_shell_command(
            inputs.policy,
            remote=state.remote,
            route_state=route_state,
            quality_policy_path=getattr(inputs.args, "quality_policy", None),
            validation_routing=PushValidationRouting(
                head_ref=state.push_authorization_head_commit or "HEAD",
                range_scope_only=bool(state.push_authorization_head_commit),
                validation_scope="pipeline_authorized_phase",
            ),
            report_routing=PushPreflightReportRouting(
                output_path=PUSH_PREFLIGHT_CHECK_ROUTER_REPORT,
            ),
        )
        state.preflight_step = command_runner(
            "push-preflight",
            ["bash", "-lc", preflight_command],
            **build_preflight_command_kwargs(
                command_runner,
                repo_root=inputs.repo_root,
            ),
        )
        annotate_preflight_step(
            state.preflight_step,
            report_path=inputs.repo_root / PUSH_PREFLIGHT_CHECK_ROUTER_REPORT,
        )
        if state.preflight_step["returncode"] != 0:
            state.errors.append("Configured push preflight failed.")


def _record_divergence(
    state: Any,
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
        state.errors.append(
            f"Branch `{branch}` is behind {remote}/{branch}; sync it before push."
        )
        return False
    return True


__all__ = ["PushPreflightFlowInputs", "run_fetch_and_preflight"]
