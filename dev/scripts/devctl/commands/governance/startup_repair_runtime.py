"""Repo-owned orchestration helpers for `startup-context --repair`."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys

from ...common_io import display_path
from ...runtime.startup_authority import build_startup_authority_report
from ...runtime.startup_context import build_startup_context
from ...runtime.startup_receipt import build_startup_receipt, write_startup_receipt
from ...runtime.startup_repair import (
    StartupRepairActionRecord,
    StartupRepairResult,
    build_startup_repair_result,
)

_TRACKED_STATE_ACTIONS = {"render_bridge", "reset_implementer_state"}
_ACTION_RUNTIME_COMMANDS = {
    "ensure_runtime": ("ensure", ["--start-publisher-if-missing"]),
    "render_bridge": ("render-bridge", []),
    "reset_implementer_state": (
        "reset-implementer-state",
        ["--reviewer-mode", "active_dual_agent", "--reason", "startup-context-repair"],
    ),
}


@dataclass(frozen=True, slots=True)
class ReviewRuntimePaths:
    """Bounded runtime paths for review-channel CLI orchestration."""

    review_channel_path: Path
    bridge_path: Path
    status_dir: Path
    promotion_plan_path: Path | None = None


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
    review_report, review_error, runtime_paths = _read_review_state(
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
        review_report=review_report,
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
    action = _ACTION_RUNTIME_COMMANDS.get(action_id)
    if action is None:
        return _failed_action_record(
            action_id,
            f"Unsupported startup-context repair action: {action_id}",
        )

    try:
        report, exit_code, error_text = _run_review_channel_json(
            repo_root=repo_root,
            runtime_paths=runtime_paths,
            action=action[0],
            extra_args=action[1],
        )
    except OSError as exc:
        return _failed_action_record(action_id, str(exc))
    if report is None:
        return _failed_action_record(
            action_id,
            error_text or "review-channel action did not emit JSON output.",
        )
    return _action_record(action_id=action_id, report=report, exit_code=exit_code)


def _read_review_state(
    *,
    repo_root: Path,
    ctx,
) -> tuple[dict[str, object] | None, str | None, ReviewRuntimePaths | None]:
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

    report, _exit_code, error_text = _run_review_channel_json(
        repo_root=repo_root,
        runtime_paths=runtime_paths,
        action="status",
    )
    if report is None:
        return (
            None,
            error_text or "review-channel status did not emit JSON output.",
            runtime_paths,
        )
    return report, None, runtime_paths


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
    return ReviewRuntimePaths(
        review_channel_path=(repo_root / review_channel_rel).resolve(),
        bridge_path=(repo_root / bridge_rel).resolve(),
        status_dir=(repo_root / review_root_rel).resolve(),
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


def _run_review_channel_json(
    *,
    repo_root: Path,
    runtime_paths: ReviewRuntimePaths,
    action: str,
    extra_args: list[str] | None = None,
) -> tuple[dict[str, object] | None, int, str]:
    argv = [
        sys.executable,
        "dev/scripts/devctl.py",
        "review-channel",
        "--action",
        action,
        "--review-channel-path",
        _repo_relative_arg(runtime_paths.review_channel_path, repo_root=repo_root),
        "--bridge-path",
        _repo_relative_arg(runtime_paths.bridge_path, repo_root=repo_root),
        "--status-dir",
        _repo_relative_arg(runtime_paths.status_dir, repo_root=repo_root),
        "--terminal",
        "none",
        "--format",
        "json",
        "--execution-mode",
        "markdown-bridge",
    ]
    if runtime_paths.promotion_plan_path is not None:
        argv.extend(
            [
                "--promotion-plan",
                _repo_relative_arg(runtime_paths.promotion_plan_path, repo_root=repo_root),
            ]
        )
    if extra_args:
        argv.extend(extra_args)

    completed = subprocess.run(
        argv,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if not stdout:
        return None, completed.returncode, stderr
    try:
        payload = json.loads(stdout)
    except ValueError:
        return None, completed.returncode, stderr or stdout
    if not isinstance(payload, dict):
        return None, completed.returncode, stderr or stdout
    return payload, completed.returncode, stderr


def _repo_relative_arg(path: Path, *, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


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
