"""Governed commit command backed by the typed remote/local pipeline."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ...governance.push_policy import load_push_policy
from ...review_channel.events import post_packet, resolve_artifact_paths, transition_packet
from ...review_channel.packet_contract import PacketTransitionRequest
from ...runtime import ActionResult
from ...runtime.action_contracts import ActionOutcome
from ...runtime.action_contracts import ACTION_RESULT_CONTRACT_ID, ACTION_RESULT_SCHEMA_VERSION
from ...runtime.control_plane_read_model import build_control_plane_read_model
from ...runtime.governance_scan import scan_repo_governance_safely
from ...runtime.operator_context import OperatorInteractionMode, resolve_operator_interaction_mode
from .governed_executor import GovernedVcsExecutor
from .governed_executor_actions import APPROVAL_PACKET_KIND, _build_report, _emit_report, build_commit_action, build_stage_action
from .governed_executor_packets import build_commit_approval_decision, build_commit_approval_request
from .governed_executor_sync import sync_pipeline_approval

GUARD_PROFILE = "quick"
DEVCTL_SCRIPT = "dev/scripts/devctl.py"
_REUSABLE_PIPELINE_STATES = frozenset(
    {
        "staged",
        "guards_running",
        "guards_passed",
        "operator_approval_pending",
        "approved",
        "commit_pending",
    }
)
_PIPELINE_BLOCKING_STATES = frozenset({"commit_recorded", "push_pending"})


@dataclass(frozen=True, slots=True)
class CommitPassthrough:
    """Supported passthrough flags for the governed commit path."""

    allow_empty: bool = False
    no_edit: bool = False
    unsupported: tuple[str, ...] = ()


def _run_guard_bundle(
    *,
    repo_root: Path = REPO_ROOT,
    runner: Any = None,
) -> int:
    """Run the quick guard profile and return the exit code."""
    cmd = [
        sys.executable,
        str(repo_root / DEVCTL_SCRIPT),
        "check",
        "--profile",
        GUARD_PROFILE,
        "--format",
        "json",
    ]
    child_env = os.environ.copy()
    child_env["DEVCTL_COMMIT_GATE_BYPASS_STARTUP_AUTHORITY"] = "1"
    run_fn = runner or subprocess.run
    result = run_fn(
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        env=child_env,
    )
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    return result.returncode


def _guard_result(exit_code: int) -> ActionResult:
    """Convert the guard exit code into the shared pipeline contract."""
    passed = exit_code == 0
    return ActionResult(
        schema_version=ACTION_RESULT_SCHEMA_VERSION,
        contract_id=ACTION_RESULT_CONTRACT_ID,
        action_id="quality.guard_bundle",
        ok=passed,
        status=ActionOutcome.PASS if passed else ActionOutcome.FAIL,
        reason="" if passed else "guard_bundle_failed",
    )


def _resolve_interaction_mode(repo_root: Path) -> str:
    """Return the current operator interaction mode for commit approval."""
    try:
        governance = scan_repo_governance_safely(repo_root)
        model = build_control_plane_read_model(
            repo_root,
            governance=governance,
        )
    except (OSError, ValueError):
        return "unresolved"
    return str(model.operator_interaction_mode or "").strip() or "unresolved"


def _should_auto_approve(interaction_mode: str) -> bool:
    """Only promptless on-box modes self-approve via typed packets.

    ``local_terminal`` (operator is physically at the repo machine and can
    confirm the commit inline) and ``single_agent`` (no human-in-the-loop
    by design) are the two modes that may synthesize an applied operator
    decision locally. ``remote_control`` intentionally does NOT self-
    approve: the operator is off-box and cannot confirm in person, so
    the governed commit must wait for a typed approval packet or
    action-request path to be applied by the remote operator. Collapsing
    that approval boundary was F1 in the Codex review and is the reason
    we no longer include ``remote_control`` in this set.
    """
    mode = resolve_operator_interaction_mode(str(interaction_mode or "").strip()).value
    return mode in {
        OperatorInteractionMode.LOCAL_TERMINAL.value,
        OperatorInteractionMode.SINGLE_AGENT.value,
    }


def _ensure_approval_request(
    executor: GovernedVcsExecutor,
    pipeline,
) -> str:
    """Post the typed approval request once per governed pipeline."""
    synced = sync_pipeline_approval(
        pipeline,
        executor._event_packets(),
        approval_packet_kind=APPROVAL_PACKET_KIND,
    )
    if synced.approval_packet_id or synced.approval_state == "approved":
        executor._persist_pipeline(synced)
        return synced.approval_packet_id
    artifact_paths = resolve_artifact_paths(repo_root=executor.repo_root)
    _, event = post_packet(
        repo_root=executor.repo_root,
        review_channel_path=executor.review_channel_path,
        artifact_paths=artifact_paths,
        request=build_commit_approval_request(pipeline),
    )
    return str(event.get("packet_id") or "").strip()


def _apply_local_approval(executor: GovernedVcsExecutor, pipeline) -> None:
    """Record request + applied operator decision for local terminal commits."""
    artifact_paths = resolve_artifact_paths(repo_root=executor.repo_root)
    request_packet_id = _ensure_approval_request(executor, pipeline)
    if request_packet_id:
        try:
            transition_packet(
                repo_root=executor.repo_root,
                review_channel_path=executor.review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketTransitionRequest(
                    action="apply",
                    packet_id=request_packet_id,
                    actor="operator",
                ),
            )
        except ValueError:
            pass
    _, decision_event = post_packet(
        repo_root=executor.repo_root,
        review_channel_path=executor.review_channel_path,
        artifact_paths=artifact_paths,
        request=build_commit_approval_decision(
            pipeline,
            summary=f"Local terminal approval for `{pipeline.pipeline_id}`",
            body=(
                "The local terminal operator approved the guarded staged "
                "snapshot for governed commit execution."
            ),
        ),
    )
    transition_packet(
        repo_root=executor.repo_root,
        review_channel_path=executor.review_channel_path,
        artifact_paths=artifact_paths,
        request=PacketTransitionRequest(
            action="apply",
            packet_id=str(decision_event.get("packet_id") or ""),
            actor="operator",
        ),
    )


def _parse_passthrough(args) -> CommitPassthrough:
    """Normalize supported passthrough flags and reject the rest."""
    allow_empty = False
    no_edit = False
    unsupported: list[str] = []
    for value in getattr(args, "passthrough", None) or ():
        flag = str(value or "").strip()
        if not flag:
            continue
        if flag == "--allow-empty":
            allow_empty = True
            continue
        if flag == "--no-edit":
            no_edit = True
            continue
        unsupported.append(flag)
    return CommitPassthrough(
        allow_empty=allow_empty,
        no_edit=no_edit,
        unsupported=tuple(unsupported),
    )


def _build_git_commit_cmd(args) -> list[str]:
    """Compatibility helper used by parser tests and docs."""
    cmd = ["git", "commit"]
    if getattr(args, "message", None):
        cmd.extend(["-m", args.message])
    if getattr(args, "amend", False):
        cmd.append("--amend")
    extra = getattr(args, "passthrough", None) or []
    cmd.extend(extra)
    return cmd


def run_commit(
    args,
    *,
    repo_root: Path = REPO_ROOT,
    guard_runner=None,
    policy=None,
    executor: GovernedVcsExecutor | None = None,
    interaction_mode: str | None = None,
) -> int:
    """Run governed commit through the typed remote/local pipeline."""
    passthrough = _parse_passthrough(args)
    if passthrough.unsupported:
        report = _build_report(
            status="blocked",
            reason="unsupported_passthrough",
            unsupported_passthrough=list(passthrough.unsupported),
            guidance=(
                "Stage the exact paths first, then rerun `devctl commit`. "
                "The governed commit path only supports `--allow-empty` and "
                "`--no-edit`."
            ),
        )
        _emit_report(args, report)
        return 1

    resolved_policy = policy or load_push_policy(repo_root=repo_root)
    vcs_executor = executor or GovernedVcsExecutor(
        repo_root=repo_root,
        push_policy=resolved_policy,
    )
    stage_warnings: list[str] = []

    pipeline = vcs_executor.load_pipeline()
    if pipeline.pipeline_id and pipeline.state in _PIPELINE_BLOCKING_STATES:
        report = _build_report(
            status="blocked",
            reason="active_pipeline_requires_publish_or_recovery",
            pipeline_id=pipeline.pipeline_id,
            pipeline_state=pipeline.state,
            guidance=(
                "Finish the current governed publish flow or recover the "
                "existing pipeline before creating another commit."
            ),
        )
        _emit_report(args, report)
        return 1

    if not pipeline.pipeline_id or pipeline.state not in _REUSABLE_PIPELINE_STATES:
        stage_result = vcs_executor.execute(
            build_stage_action(
                repo_pack_id=resolved_policy.repo_pack_id,
                commit_message_draft=str(getattr(args, "message", "") or ""),
                push_requested=False,
                guard_profile=GUARD_PROFILE,
                work_intake_ref="devctl.commit",
                reuse_staged_index=True,
                allow_empty=passthrough.allow_empty,
                requested_by="devctl.commit",
            )
        )
        pipeline = vcs_executor.load_pipeline()
        stage_warnings = list(stage_result.warnings)
        if not stage_result.ok:
            report = _build_report(
                status="blocked",
                reason=stage_result.reason,
                pipeline_id=pipeline.pipeline_id,
                pipeline_state=pipeline.state,
                operator_guidance=stage_result.operator_guidance,
                warnings=list(stage_result.warnings),
            )
            _emit_report(args, report)
            return 1

    if pipeline.guard_result is None or pipeline.guard_result.status != ActionOutcome.PASS:
        guard_rc = _run_guard_bundle(repo_root=repo_root, runner=guard_runner)
        pipeline = vcs_executor.record_guard_result(_guard_result(guard_rc))
        if guard_rc != 0:
            report = _build_report(
                status="blocked",
                reason="guard_bundle_failed",
                guard_exit_code=guard_rc,
                pipeline_id=pipeline.pipeline_id,
                pipeline_state=pipeline.state,
                warnings=stage_warnings,
            )
            _emit_report(args, report)
            return 1

    resolved_mode = interaction_mode or _resolve_interaction_mode(repo_root)
    if pipeline.approval_state != "approved":
        if _should_auto_approve(resolved_mode):
            _apply_local_approval(vcs_executor, pipeline)
        else:
            _ensure_approval_request(vcs_executor, pipeline)

    commit_result = vcs_executor.execute(
        build_commit_action(
            repo_pack_id=resolved_policy.repo_pack_id,
            pipeline_id=vcs_executor.load_pipeline().pipeline_id,
            commit_message_draft=str(getattr(args, "message", "") or ""),
            amend=bool(getattr(args, "amend", False)),
            allow_empty=passthrough.allow_empty,
            no_edit=passthrough.no_edit,
            requested_by="devctl.commit",
        )
    )
    pipeline = vcs_executor.load_pipeline()
    report = _build_report(
        status="committed" if commit_result.ok else "blocked",
        reason=commit_result.reason,
        pipeline_id=pipeline.pipeline_id,
        pipeline_state=pipeline.state,
        approval_state=pipeline.approval_state,
        commit_sha=pipeline.commit_sha,
        operator_guidance=commit_result.operator_guidance,
        interaction_mode=resolved_mode,
        warnings=[*stage_warnings, *commit_result.warnings],
    )
    _emit_report(args, report)
    return 0 if commit_result.ok else 1


def run(args) -> int:
    """Entry point for ``devctl commit``."""
    return run_commit(args)
