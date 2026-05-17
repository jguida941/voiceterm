"""Guard-bundle helpers for the governed commit command."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ...runtime import ActionResult
from ...runtime.action_contracts import (
    ACTION_RESULT_CONTRACT_ID,
    ACTION_RESULT_SCHEMA_VERSION,
    ActionOutcome,
)
from .commit_guard_snapshot import (
    guard_check_args_for_pipeline,
    pipeline_has_checkpoint_snapshot as guard_snapshot_has_checkpoint_snapshot,
)

GUARD_PROFILE = "quick"
DEVCTL_SCRIPT = "dev/scripts/devctl.py"
_HOST_CLEANUP_AGE_WARNING = "Recent detached repo-related processes were not killed yet"
_HOST_CLEANUP_STEP_NAME = "host-process-cleanup-post"
_HOST_CLEANUP_RETRY_ACTION = "host_process_cleanup_post_age_retry"


@dataclass(slots=True)
class HostCleanupRetryReport:
    triggered: bool
    action: str
    command: str
    remediation_exit_code: int
    remediation_status: str
    second_attempt_exit_code: int | None = None
    second_attempt_status: str = "pending"

    def to_dict(self) -> dict[str, object]:
        return dict(
            [
                ("triggered", self.triggered),
                ("action", self.action),
                ("command", self.command),
                ("remediation_exit_code", self.remediation_exit_code),
                ("remediation_status", self.remediation_status),
                ("second_attempt_exit_code", self.second_attempt_exit_code),
                ("second_attempt_status", self.second_attempt_status),
            ]
        )


def run_guard_bundle(
    *,
    repo_root: Path = REPO_ROOT,
    runner: Any = None,
    pipeline: object | None = None,
) -> int:
    """Run the quick guard profile and return the exit code."""
    exit_code, _result = run_guard_bundle_with_result(
        repo_root=repo_root,
        runner=runner,
        pipeline=pipeline,
    )
    return exit_code


def run_guard_bundle_with_result(
    *,
    repo_root: Path = REPO_ROOT,
    runner: Any = None,
    pipeline: object | None = None,
) -> tuple[int, ActionResult]:
    """Run the quick guard profile and return the exit code plus ActionResult."""
    run_fn = runner or subprocess.run
    result = _run_guard_check(
        repo_root=repo_root,
        run_fn=run_fn,
        pipeline=pipeline,
    )
    if result.returncode == 0:
        return 0, guard_result(0)
    if not _host_cleanup_age_out_detected(result):
        return result.returncode, guard_result(result.returncode)

    retry_report = _run_host_cleanup_age_retry(repo_root=repo_root, run_fn=run_fn)
    if retry_report.remediation_exit_code == 0:
        retry_result = _run_guard_check(
            repo_root=repo_root,
            run_fn=run_fn,
            pipeline=pipeline,
        )
        retry_report.second_attempt_exit_code = retry_result.returncode
        retry_report.second_attempt_status = (
            "pass" if retry_result.returncode == 0 else "fail"
        )
        action_result = guard_result(
            retry_result.returncode,
            reason_chain=(
                "guard_bundle_failed",
                _HOST_CLEANUP_STEP_NAME,
                "recent_detached_process_age_out",
                "auto_retry_succeeded"
                if retry_result.returncode == 0
                else "auto_retry_failed",
            ),
            remediation=_HOST_CLEANUP_RETRY_ACTION,
            auto_executable=True,
            errors=(_host_cleanup_error(retry_report),),
            warnings=(_retry_warning(retry_report),),
        )
        return retry_result.returncode, action_result

    retry_report.second_attempt_status = "not_run"
    action_result = guard_result(
        result.returncode,
        reason_chain=(
            "guard_bundle_failed",
            _HOST_CLEANUP_STEP_NAME,
            "recent_detached_process_age_out",
            "auto_retry_failed",
        ),
        remediation=_HOST_CLEANUP_RETRY_ACTION,
        auto_executable=True,
        errors=(_host_cleanup_error(retry_report),),
        warnings=(_retry_warning(retry_report),),
    )
    return result.returncode, action_result


def _run_guard_check(
    *,
    repo_root: Path,
    run_fn: Any,
    pipeline: object | None,
) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        str(repo_root / DEVCTL_SCRIPT),
        "check",
        "--profile",
        GUARD_PROFILE,
        "--format",
        "json",
        *guard_check_args_for_pipeline(pipeline),
    ]
    child_env = os.environ.copy()
    if guard_snapshot_has_checkpoint_snapshot(pipeline):
        child_env["DEVCTL_COMMIT_GATE_BYPASS_STARTUP_AUTHORITY"] = "1"
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
    return result


def _run_host_cleanup_age_retry(
    *,
    repo_root: Path,
    run_fn: Any,
) -> HostCleanupRetryReport:
    cmd = [
        sys.executable,
        str(repo_root / DEVCTL_SCRIPT),
        "process-watch",
        "--cleanup",
        "--strict",
        "--stop-on-clean",
        "--iterations",
        "2",
        "--interval-seconds",
        "15",
        "--format",
        "json",
    ]
    result = run_fn(
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    return HostCleanupRetryReport(
        triggered=True,
        action=_HOST_CLEANUP_RETRY_ACTION,
        command=" ".join(str(part) for part in cmd),
        remediation_exit_code=int(result.returncode),
        remediation_status="pass" if result.returncode == 0 else "fail",
    )


def _host_cleanup_age_out_detected(result: subprocess.CompletedProcess) -> bool:
    text = f"{getattr(result, 'stdout', '')}\n{getattr(result, 'stderr', '')}"
    if _HOST_CLEANUP_AGE_WARNING in text and _HOST_CLEANUP_STEP_NAME in text:
        return True
    return _check_result_has_host_cleanup_age_out(text)


def _check_result_has_host_cleanup_age_out(text: str) -> bool:
    for payload in _iter_json_objects(text):
        steps = payload.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            if step.get("name") != _HOST_CLEANUP_STEP_NAME:
                continue
            haystack = json.dumps(step, sort_keys=True)
            if _HOST_CLEANUP_AGE_WARNING in haystack:
                return True
    return False


def _iter_json_objects(text: str) -> list[dict[str, object]]:
    decoder = json.JSONDecoder()
    objects: list[dict[str, object]] = []
    cursor = 0
    while True:
        start = text.find("{", cursor)
        if start < 0:
            return objects
        try:
            payload, end = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            cursor = start + 1
            continue
        if isinstance(payload, dict):
            objects.append(payload)
        cursor = start + end


def _host_cleanup_error(report: HostCleanupRetryReport) -> dict[str, object]:
    return {
        "reason": "host_process_cleanup_post_age_out",
        "reason_chain": [
            "guard_bundle_failed",
            _HOST_CLEANUP_STEP_NAME,
            "recent_detached_process_age_out",
        ],
        "remediation": _HOST_CLEANUP_RETRY_ACTION,
        "auto_executable": True,
        "details": report.to_dict(),
    }


def _retry_warning(report: HostCleanupRetryReport) -> str:
    return (
        "host_process_cleanup_post_age_retry: "
        f"triggered={report.triggered} "
        f"remediation_status={report.remediation_status} "
        f"second_attempt_status={report.second_attempt_status}"
    )


def guard_result(
    exit_code: int,
    *,
    reason_chain: tuple[str, ...] = (),
    remediation: str = "",
    auto_executable: bool = False,
    errors: tuple[dict[str, object], ...] = (),
    warnings: tuple[str, ...] = (),
) -> ActionResult:
    """Convert the guard exit code into the shared pipeline contract."""
    passed = exit_code == 0
    return ActionResult(
        schema_version=ACTION_RESULT_SCHEMA_VERSION,
        contract_id=ACTION_RESULT_CONTRACT_ID,
        action_id="quality.guard_bundle",
        ok=passed,
        status=ActionOutcome.PASS if passed else ActionOutcome.FAIL,
        reason="" if passed else "guard_bundle_failed",
        warnings=warnings,
        errors=errors,
        reason_chain=reason_chain,
        remediation=remediation,
        auto_executable=auto_executable,
    )


def pipeline_has_checkpoint_snapshot(pipeline: object | None) -> bool:
    """Return true when commit is running against a staged governed snapshot."""
    if guard_snapshot_has_checkpoint_snapshot(pipeline):
        return True
    if _pipeline_has_validation_plan(pipeline):
        return True
    if pipeline is None:
        return False
    intent = getattr(pipeline, "intent", None)
    if intent is None:
        return False
    staged_tree_hash = str(getattr(intent, "staged_tree_hash", "") or "").strip()
    try:
        staged_path_count = int(getattr(intent, "staged_path_count", 0) or 0)
    except (TypeError, ValueError):
        return False
    return bool(staged_tree_hash and staged_path_count > 0)


def _pipeline_has_validation_plan(pipeline: object | None) -> bool:
    """Return true only when the staged pipeline carries typed validation state."""
    if pipeline is None:
        return False
    intent = getattr(pipeline, "intent", None)
    if intent is None:
        return False
    plan = getattr(intent, "validation_plan", None)
    if plan is None:
        return False
    return bool(
        getattr(plan, "plan_id", "")
        and getattr(plan, "bundle_id", "")
        and getattr(plan, "staged_tree_hash", "")
    )
