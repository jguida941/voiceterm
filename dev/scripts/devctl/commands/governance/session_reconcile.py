"""Implementation for ``devctl session reconcile``.

The command exposes the attachment-layer repair path used during launch
recovery. Report-only mode returns the typed `SessionLivenessReconciler`
without mutation. `--kill-stale` detaches stale persisted remote-control
attachments and may terminate a still-live stale PID through the runtime
reconciler; after a real cleanup it refreshes the existing review-channel
status projection so subsequent startup packets see the repaired liveness
state. Re-running the command is idempotent because detached/current
attachments are not detached again.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...common import emit_output, pipe_output, resolve_repo_path, write_output
from ...repo_packs import active_path_config
from ...review_channel.state import refresh_status_snapshot
from ...runtime.session_liveness_reconciler import (
    SessionLivenessReconciler,
    reconcile_session_liveness,
)


def run_reconcile(args: Any, *, repo_root: Path) -> int:
    """Run attachment liveness reconciliation for the session subcommand."""
    output_root = _session_output_root(args, repo_root=repo_root)
    result = reconcile_session_liveness(
        session_output_root=output_root,
        kill_stale=bool(getattr(args, "kill_stale", False)),
        dry_run=bool(getattr(args, "dry_run", False)),
    )
    payload = result.to_dict()
    payload["command"] = "session"
    payload["action"] = "reconcile"
    payload["status_refreshed"] = False
    payload["status_refresh_reason"] = ""

    if _should_refresh_status(args, result):
        refreshed, reason = _refresh_status(args, repo_root=repo_root, output_root=output_root)
        payload["status_refreshed"] = refreshed
        payload["status_refresh_reason"] = reason

    output = (
        json.dumps(payload, indent=2, sort_keys=True)
        if args.format == "json"
        else _render_md(payload)
    )
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_rc != 0:
        return pipe_rc
    return 0 if result.ok else 1


def _session_output_root(args: Any, *, repo_root: Path) -> Path:
    override = str(getattr(args, "session_output_root", "") or "").strip()
    if override:
        return resolve_repo_path(override, repo_root=repo_root)
    return repo_root / active_path_config().review_status_dir_rel


def _should_refresh_status(args: Any, result: SessionLivenessReconciler) -> bool:
    if bool(getattr(args, "no_refresh_status", False)):
        return False
    if bool(getattr(args, "dry_run", False)):
        return False
    return bool(getattr(args, "kill_stale", False)) and result.cleared_attachment_count > 0


def _refresh_status(
    args: Any,
    *,
    repo_root: Path,
    output_root: Path,
) -> tuple[bool, str]:
    config = active_path_config()
    bridge_path = repo_root / config.bridge_rel
    review_channel_path = repo_root / config.review_channel_rel
    if not bridge_path.exists() or not review_channel_path.exists():
        return False, "bridge_or_review_channel_missing"
    try:
        refresh_status_snapshot(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=output_root,
            execution_mode=getattr(args, "execution_mode", "markdown-bridge"),
            warnings=[],
            errors=[],
        )
    except (OSError, ValueError) as exc:
        return False, f"refresh_failed:{exc}"
    return True, "refreshed_after_stale_attachment_cleanup"


def _render_md(report: dict[str, object]) -> str:
    lines = ["# devctl session reconcile", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- kill_stale: {report.get('kill_stale')}")
    lines.append(f"- dry_run: {report.get('dry_run')}")
    lines.append(f"- session_output_root: {report.get('session_output_root')}")
    lines.append(f"- stale_count: {report.get('stale_count')}")
    lines.append(f"- cleared_attachment_count: {report.get('cleared_attachment_count')}")
    lines.append(f"- killed_pid_count: {report.get('killed_pid_count')}")
    lines.append(f"- status_refreshed: {report.get('status_refreshed')}")
    reason = str(report.get("status_refresh_reason") or "")
    if reason:
        lines.append(f"- status_refresh_reason: {reason}")

    rows = report.get("rows")
    if isinstance(rows, list) and rows:
        lines.append("")
        lines.append("## Rows")
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- "
                f"{row.get('provider', '')} {row.get('record_kind', '')} "
                f"status={row.get('before_status', '')}->{row.get('after_status', '')} "
                f"pid={row.get('host_pid', '')} live={row.get('process_live', '')} "
                f"stale={row.get('stale', '')} action={row.get('action', '')} "
                f"reason={row.get('reason', '')}"
            )

    warnings = report.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.append("")
        lines.append("## Warnings")
        for warning in warnings:
            lines.append(f"- {warning}")

    errors = report.get("errors")
    if isinstance(errors, list) and errors:
        lines.append("")
        lines.append("## Errors")
        for error in errors:
            lines.append(f"- {error}")
    return "\n".join(lines)


__all__ = ["run_reconcile"]
