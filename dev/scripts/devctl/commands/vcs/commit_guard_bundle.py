"""Guard-bundle helpers for the governed commit command."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ...runtime import ActionResult
from ...runtime.action_contracts import (
    ACTION_RESULT_CONTRACT_ID,
    ACTION_RESULT_SCHEMA_VERSION,
    ActionOutcome,
)

GUARD_PROFILE = "quick"
DEVCTL_SCRIPT = "dev/scripts/devctl.py"


def run_guard_bundle(
    *,
    repo_root: Path = REPO_ROOT,
    runner: Any = None,
    pipeline: object | None = None,
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
    if pipeline_has_checkpoint_snapshot(pipeline):
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


def guard_result(exit_code: int) -> ActionResult:
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


def pipeline_has_checkpoint_snapshot(pipeline: object | None) -> bool:
    """Return true when commit is running against a staged governed snapshot."""
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
