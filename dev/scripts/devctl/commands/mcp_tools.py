"""MCP tool schemas and read-only snapshot handlers.

Each handler produces a structured payload for its corresponding MCP tool invocation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from ..policy_gate import run_json_policy_gate
from ..reports_retention import PROTECTED_REPORT_PATHS
from ..status_report import build_project_report
from . import check, compat_matrix, failure_cleanup, ship_steps


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def to_int(value: Any, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        try:
            return int(text)
        except ValueError:
            return default
    return default


TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "status_snapshot": {
        "type": "object",
        "properties": {
            "include_ci": {"type": "boolean"},
            "ci_limit": {"type": "integer", "minimum": 1},
            "include_dev_logs": {"type": "boolean"},
            "dev_root": {"type": "string"},
            "dev_sessions_limit": {"type": "integer", "minimum": 1},
            "parallel": {"type": "boolean"},
        },
        "additionalProperties": False,
    },
    "report_snapshot": {
        "type": "object",
        "properties": {
            "include_ci": {"type": "boolean"},
            "ci_limit": {"type": "integer", "minimum": 1},
            "include_dev_logs": {"type": "boolean"},
            "dev_root": {"type": "string"},
            "dev_sessions_limit": {"type": "integer", "minimum": 1},
            "parallel": {"type": "boolean"},
        },
        "additionalProperties": False,
    },
    "compat_matrix_snapshot": {
        "type": "object",
        "properties": {
            "run_smoke": {"type": "boolean"},
        },
        "additionalProperties": False,
    },
    "release_contract_snapshot": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}


def tool_status_snapshot(arguments: dict[str, Any]) -> dict[str, Any]:
    include_ci = to_bool(arguments.get("include_ci"), default=True)
    ci_limit = max(1, to_int(arguments.get("ci_limit"), 20))
    include_dev_logs = to_bool(arguments.get("include_dev_logs"), default=False)
    dev_root = arguments.get("dev_root")
    dev_sessions_limit = max(1, to_int(arguments.get("dev_sessions_limit"), 5))
    parallel = to_bool(arguments.get("parallel"), default=True)
    payload = build_project_report(
        command="mcp.status_snapshot",
        include_ci=include_ci,
        ci_limit=ci_limit,
        include_dev_logs=include_dev_logs,
        dev_root=dev_root if isinstance(dev_root, str) else None,
        dev_sessions_limit=dev_sessions_limit,
        parallel=parallel,
    )
    return {
        "tool": "status_snapshot",
        "timestamp": utc_now(),
        "payload": payload,
    }


def tool_report_snapshot(arguments: dict[str, Any]) -> dict[str, Any]:
    include_ci = to_bool(arguments.get("include_ci"), default=False)
    ci_limit = max(1, to_int(arguments.get("ci_limit"), 20))
    include_dev_logs = to_bool(arguments.get("include_dev_logs"), default=False)
    dev_root = arguments.get("dev_root")
    dev_sessions_limit = max(1, to_int(arguments.get("dev_sessions_limit"), 5))
    parallel = to_bool(arguments.get("parallel"), default=True)
    payload = build_project_report(
        command="mcp.report_snapshot",
        include_ci=include_ci,
        ci_limit=ci_limit,
        include_dev_logs=include_dev_logs,
        dev_root=dev_root if isinstance(dev_root, str) else None,
        dev_sessions_limit=dev_sessions_limit,
        parallel=parallel,
    )
    return {
        "tool": "report_snapshot",
        "timestamp": utc_now(),
        "payload": payload,
    }


def tool_compat_matrix_snapshot(arguments: dict[str, Any]) -> dict[str, Any]:
    run_smoke = to_bool(arguments.get("run_smoke"), default=True)
    validation_report = run_json_policy_gate(
        compat_matrix.COMPAT_MATRIX_SCRIPT,
        "compatibility matrix validation gate",
    )
    smoke_report = None
    if run_smoke:
        smoke_report = run_json_policy_gate(
            compat_matrix.COMPAT_MATRIX_SMOKE_SCRIPT,
            "compatibility matrix smoke gate",
        )
    validation_ok = bool(validation_report.get("ok", False))
    smoke_ok = bool(smoke_report.get("ok", False)) if run_smoke else True
    return {
        "tool": "compat_matrix_snapshot",
        "timestamp": utc_now(),
        "payload": {
            "ok": validation_ok and smoke_ok,
            "run_smoke": run_smoke,
            "validation_ok": validation_ok,
            "smoke_ok": smoke_ok,
            "validation_report": validation_report,
            "smoke_report": smoke_report,
        },
    }


def tool_release_contract_snapshot(arguments: dict[str, Any]) -> dict[str, Any]:
    _ = arguments
    return {
        "tool": "release_contract_snapshot",
        "timestamp": utc_now(),
        "payload": {
            "check_profile_release_flags": check.resolve_profile_settings(
                type(
                    "ReleaseArgs",
                    (),
                    {
                        "profile": "release",
                        "skip_build": False,
                        "skip_tests": False,
                        "with_perf": False,
                        "with_mem_loop": False,
                        "with_mutants": False,
                        "with_mutation_score": False,
                        "with_wake_guard": False,
                        "with_ai_guard": False,
                    },
                )()
            )[0],
            "check_release_gate_commands": check.build_release_gate_commands(),
            "ship_verify_checks": [
                {"name": name, "cmd": cmd}
                for name, cmd in ship_steps.build_verify_checks(verify_docs=True)
            ],
            "cleanup_path_contract": {
                "failure_cleanup_root": str(failure_cleanup.FAILURE_ROOT_RELATIVE),
                "failure_cleanup_override_root": str(
                    failure_cleanup.OUTSIDE_OVERRIDE_ROOT_RELATIVE
                ),
                "reports_cleanup_protected_paths": [
                    str(item) for item in PROTECTED_REPORT_PATHS
                ],
            },
        },
    }


TOOL_HANDLERS = {
    "status_snapshot": tool_status_snapshot,
    "report_snapshot": tool_report_snapshot,
    "compat_matrix_snapshot": tool_compat_matrix_snapshot,
    "release_contract_snapshot": tool_release_contract_snapshot,
}
