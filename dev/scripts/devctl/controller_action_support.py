"""Helper logic for `devctl controller-action`."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .autonomy_loop_helpers import load_policy, resolve_path

try:
    from dev.scripts.checks.coderabbit_gate_support import (
        is_ci_environment as _is_ci_environment,
        looks_like_connectivity_error as _looks_like_connectivity_error,
    )
except ModuleNotFoundError:
    from checks.coderabbit_gate_support import (
        is_ci_environment as _is_ci_environment,
        looks_like_connectivity_error as _looks_like_connectivity_error,
    )


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_non_blocking_local_connectivity_error(message: str) -> bool:
    return bool(message) and _looks_like_connectivity_error(message) and not _is_ci_environment()


def workflow_allowed(policy: dict[str, Any], workflow_path: str) -> bool:
    allowed = policy.get("allowed_workflow_dispatches")
    if not isinstance(allowed, list) or not allowed:
        return False
    normalized = {str(row).strip() for row in allowed if str(row).strip()}
    return str(workflow_path).strip() in normalized


def branch_allowed(policy: dict[str, Any], branch: str) -> bool:
    triage_cfg = policy.get("triage_loop")
    if not isinstance(triage_cfg, dict):
        return branch == "develop"
    allowed = triage_cfg.get("allowed_branches")
    if not isinstance(allowed, list) or not allowed:
        return branch == "develop"
    normalized = {str(row).strip() for row in allowed if str(row).strip()}
    if not normalized:
        return branch == "develop"
    return branch in normalized


def autonomy_mode(policy: dict[str, Any]) -> str:
    default_mode = str(policy.get("autonomy_mode_default") or "read-only").strip() or "read-only"
    mode = str(os.getenv("AUTONOMY_MODE") or default_mode).strip() or default_mode
    return mode


def load_phone_payload(phone_json: str) -> tuple[dict[str, Any], str | None]:
    path = resolve_path(phone_json)
    if not path.exists():
        return {}, f"phone status artifact not found: {path}"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return {}, str(exc)
    except json.JSONDecodeError as exc:
        return {}, f"invalid json ({exc})"
    if not isinstance(payload, dict):
        return {}, "expected top-level object in phone status artifact"
    return payload, None


def write_controller_mode(
    *,
    mode_file: str,
    action: str,
    requested_mode: str,
    repo: str,
    branch: str,
    remote_enabled: bool,
    remote_ok: bool,
    dry_run: bool,
    warnings: list[str],
    errors: list[str],
) -> str:
    path = resolve_path(mode_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "timestamp": iso_z(utc_now()),
        "action": action,
        "requested_mode": requested_mode,
        "repo": repo,
        "branch": branch,
        "remote_enabled": remote_enabled,
        "remote_ok": remote_ok,
        "dry_run": dry_run,
        "warnings": [str(row) for row in warnings],
        "errors": [str(row) for row in errors],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)


def dispatch_workflow_command(
    *,
    workflow: str,
    repo: str,
    branch: str,
    max_attempts: int,
) -> list[str]:
    return [
        "gh",
        "workflow",
        "run",
        workflow,
        "--repo",
        repo,
        "--ref",
        branch,
        "-f",
        f"branch={branch}",
        "-f",
        "execution_mode=report-only",
        "-f",
        f"max_attempts={max_attempts}",
        "-f",
        "notify_mode=summary-only",
        "-f",
        "comment_target=auto",
    ]


def remote_mode_command(*, repo: str, requested_mode: str) -> list[str]:
    return [
        "gh",
        "variable",
        "set",
        "AUTONOMY_MODE",
        "--repo",
        repo,
        "--body",
        requested_mode,
    ]


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# devctl controller-action", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- action: {report.get('action')}")
    lines.append(f"- reason: {report.get('reason')}")
    lines.append(f"- repo: {report.get('repo')}")
    lines.append(f"- branch: {report.get('branch')}")
    lines.append(f"- workflow: {report.get('workflow') or 'n/a'}")
    lines.append(f"- autonomy_mode_runtime: {report.get('autonomy_mode_runtime')}")
    lines.append(f"- dry_run: {report.get('dry_run')}")
    result = report.get("result")
    if isinstance(result, dict) and result:
        lines.append("")
        lines.append("## Result")
        lines.append("")
        for key in sorted(result.keys()):
            lines.append(f"- {key}: {result.get(key)}")
    warnings = report.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.append("")
        lines.append("## Warnings")
        lines.append("")
        for row in warnings:
            lines.append(f"- {row}")
    errors = report.get("errors")
    if isinstance(errors, list) and errors:
        lines.append("")
        lines.append("## Errors")
        lines.append("")
        for row in errors:
            lines.append(f"- {row}")
    return "\n".join(lines)


def load_controller_policy() -> dict[str, Any]:
    payload = load_policy()
    return payload if isinstance(payload, dict) else {}
