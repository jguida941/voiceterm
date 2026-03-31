"""Repo-owned orchestration helpers for `startup-context --repair`."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from ...common_io import display_path
from ...runtime.review_state_models import ReviewState
from ...runtime.startup_authority import build_startup_authority_report
from ...runtime.startup_context import build_startup_context
from ...runtime.startup_receipt import build_startup_receipt, write_startup_receipt
from ...runtime.startup_repair import (
    StartupRepairActionRecord,
    StartupRepairResult,
    build_startup_repair_result,
)
from ...runtime.startup_repair_models import StartupRepairActionId

_TRACKED_STATE_ACTIONS = {
    StartupRepairActionId.RENDER_BRIDGE.value,
    StartupRepairActionId.RESET_IMPLEMENTER_STATE.value,
}


@dataclass(frozen=True, slots=True)
class ReviewRuntimePaths:
    """Bounded runtime paths needed by startup repair."""

    review_channel_path: Path
    bridge_path: Path
    status_dir: Path
    rollover_dir: Path


@dataclass(frozen=True, slots=True)
class CollectedStartupRepairState:
    """Current typed startup repair snapshot."""

    result: StartupRepairResult
    runtime_paths: ReviewRuntimePaths | None


def collect_state(
    *,
    repo_root: Path,
    applied_actions: tuple[StartupRepairActionRecord, ...],
) -> CollectedStartupRepairState:
    ctx = build_startup_context(repo_root=repo_root)
    authority_report = build_startup_authority_report(repo_root=repo_root)
    review_state, review_error, runtime_paths = _read_review_state(
        repo_root=repo_root,
        ctx=ctx,
    )
    receipt_path = _write_current_startup_receipt(
        repo_root=repo_root,
        ctx=ctx,
        authority_report=authority_report,
    )
    result = build_startup_repair_result(
        ctx=ctx,
        authority_report=authority_report,
        startup_receipt_path=receipt_path,
        review_state=review_state,
        review_error=review_error,
        applied_actions=applied_actions,
    )
    return CollectedStartupRepairState(result=result, runtime_paths=runtime_paths)


def apply_safe_repair_action(
    *,
    action_id: str,
    repo_root: Path,
    runtime_paths: ReviewRuntimePaths | None,
) -> StartupRepairActionRecord:
    if runtime_paths is None:
        return _failed_action_record(
            action_id,
            "Review-channel runtime paths were unavailable for the requested repair action.",
        )
    try:
        report, exit_code = _run_review_channel_action(
            action_id=action_id,
            repo_root=repo_root,
            runtime_paths=runtime_paths,
        )
    except (OSError, ValueError) as exc:
        return _failed_action_record(
            action_id,
            str(exc),
        )
    return _action_record(action_id=action_id, report=report, exit_code=exit_code)


def _read_review_state(
    *,
    repo_root: Path,
    ctx,
) -> tuple[ReviewState | None, str | None, ReviewRuntimePaths | None]:
    runtime_paths = _resolve_review_runtime_paths(repo_root=repo_root, ctx=ctx)
    if runtime_paths is None:
        if not ctx.reviewer_gate.bridge_active:
            return None, None, None
        return (
            None,
            "Review-channel bridge is active but typed governance did not resolve "
            "bridge, review-channel, and review-status roots.",
            None,
        )

    try:
        from ...review_channel.state import refresh_status_snapshot

        snapshot = refresh_status_snapshot(
            repo_root=repo_root,
            bridge_path=runtime_paths.bridge_path,
            review_channel_path=runtime_paths.review_channel_path,
            output_root=runtime_paths.status_dir,
            promotion_plan_path=None,
            execution_mode="markdown-bridge",
            warnings=[],
            errors=[],
        )
    except (OSError, ValueError) as exc:
        return (
            None,
            str(exc) or "review-channel status refresh failed.",
            runtime_paths,
        )
    if snapshot.review_state is None:
        return (
            None,
            "review-channel status refresh did not yield a typed ReviewState payload.",
            runtime_paths,
        )
    return snapshot.review_state, None, runtime_paths


def _resolve_review_runtime_paths(
    *,
    repo_root: Path,
    ctx,
) -> ReviewRuntimePaths | None:
    if not ctx.reviewer_gate.bridge_active:
        return None
    governance = ctx.governance
    if governance is None:
        return None
    bridge_rel = str(governance.bridge_config.bridge_path or "").strip()
    review_channel_rel = str(governance.bridge_config.review_channel_path or "").strip()
    review_root_rel = str(governance.artifact_roots.review_root or "").strip()
    if not bridge_rel or not review_channel_rel or not review_root_rel:
        return None
    status_dir = (repo_root / review_root_rel).resolve()
    return ReviewRuntimePaths(
        review_channel_path=(repo_root / review_channel_rel).resolve(),
        bridge_path=(repo_root / bridge_rel).resolve(),
        status_dir=status_dir,
        rollover_dir=(status_dir.parent / "rollovers").resolve(),
    )


def _write_current_startup_receipt(
    *,
    repo_root: Path,
    ctx,
    authority_report: dict[str, object],
) -> str:
    receipt = build_startup_receipt(
        ctx,
        authority_report=authority_report,
        repo_root=repo_root,
    )
    path = write_startup_receipt(
        receipt,
        governance=ctx.governance,
        repo_root=repo_root,
    )
    return display_path(path)


def _run_review_channel_action(
    *,
    action_id: str,
    repo_root: Path,
    runtime_paths: ReviewRuntimePaths,
) -> tuple[dict[str, object], int]:
    from ..review_channel_command import RuntimePaths

    command_paths = RuntimePaths(
        review_channel_path=runtime_paths.review_channel_path,
        bridge_path=runtime_paths.bridge_path,
        rollover_dir=runtime_paths.rollover_dir,
        status_dir=runtime_paths.status_dir,
        promotion_plan_path=None,
        script_dir=None,
        artifact_paths=None,
    )

    def action_args(**overrides: object) -> SimpleNamespace:
        namespace = SimpleNamespace(
            action="",
            execution_mode="markdown-bridge",
            terminal="none",
            terminal_profile=None,
            approval_mode=None,
            dangerous=False,
            rollover_threshold_pct=50,
            await_ack_seconds=180,
            codex_workers=0,
            claude_workers=0,
            reviewer_overdue_seconds=None,
        )
        for key, value in overrides.items():
            setattr(namespace, key, value)
        return namespace

    if action_id == StartupRepairActionId.ENSURE_RUNTIME.value:
        from ..review_channel._follow_runtime import (
            run_ensure_action as _run_ensure_action,
        )

        args = action_args(
            action="ensure",
            follow=False,
            start_publisher_if_missing=True,
        )
        return _run_ensure_action(
            args=args,
            repo_root=repo_root,
            paths=command_paths,
        )
    if action_id == StartupRepairActionId.RENDER_BRIDGE.value:
        from ..review_channel._render_bridge import (
            run_render_bridge_action as _run_render_bridge_action,
        )

        args = action_args(
            action="render-bridge",
        )
        return _run_render_bridge_action(
            args=args,
            repo_root=repo_root,
            paths=command_paths,
        )
    if action_id == StartupRepairActionId.RESET_IMPLEMENTER_STATE.value:
        from ..review_channel._reset_implementer import (
            run_reset_implementer_state_action as _run_reset_implementer_state_action,
        )
        from ..review_channel.status import _run_status_action

        args = action_args(
            action="reset-implementer-state",
            reason="startup-context-repair",
            reviewer_mode="active_dual_agent",
        )
        return _run_reset_implementer_state_action(
            args=args,
            repo_root=repo_root,
            paths=command_paths,
            run_status_action_fn=_run_status_action,
        )
    raise ValueError(f"Unsupported startup-context repair action: {action_id}")


def _action_record(
    *,
    action_id: str,
    report: dict[str, object],
    exit_code: int,
) -> StartupRepairActionRecord:
    return StartupRepairActionRecord(
        action_id=action_id,
        ok=exit_code == 0,
        exit_code=exit_code,
        detail=_action_detail(action_id, report),
        changed_tracked_state=action_id in _TRACKED_STATE_ACTIONS,
        resulting_attention_status=_attention_status(report),
    )


def _failed_action_record(action_id: str, detail: str) -> StartupRepairActionRecord:
    return StartupRepairActionRecord(
        action_id=action_id,
        ok=False,
        exit_code=1,
        detail=detail,
        changed_tracked_state=action_id in _TRACKED_STATE_ACTIONS,
    )


def _attention_status(report: dict[str, object]) -> str:
    attention = report.get("attention")
    if isinstance(attention, dict):
        return str(attention.get("status") or "").strip()
    return str(report.get("attention_status") or "").strip()


def _action_detail(action_id: str, report: dict[str, object]) -> str:
    if action_id == "ensure_runtime":
        return str(report.get("detail") or "").strip()
    if action_id == "render_bridge":
        return "Re-rendered `bridge.md` from typed review-state compatibility data."
    reset = report.get("implementer_state_reset")
    if isinstance(reset, dict) and bool(reset.get("changed", False)):
        return "Reset implementer-owned bridge sections to canonical pending state."
    return "Implementer-owned bridge sections already matched the pending state."
