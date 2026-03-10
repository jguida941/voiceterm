"""`devctl review-channel` command implementation.

Orchestrates bridge-backed and event-backed review-channel actions. The
heavy rendering and execution logic lives in the dedicated handler modules:

- review_channel_bridge_handler: launch, rollover, promote, status (bridge)
- review_channel_event_handler: post, watch, inbox, ack, dismiss, apply, history
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..approval_mode import normalize_approval_mode
from ..common import emit_output
from ..config import REPO_ROOT
from ..review_channel.core import REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE
from ..review_channel.context_refs import resolve_context_pack_refs  # noqa: F401 -- re-exported for test patch targets
from ..review_channel.events import event_state_exists, resolve_artifact_paths
from ..review_channel.event_store import (
    build_bridge_status_fallback_warning,
    summarize_review_state_errors,
)
from ..review_channel.promotion import DEFAULT_PROMOTION_PLAN_REL
from ..time_utils import utc_timestamp

from .review_channel_bridge_handler import (
    BRIDGE_ACTIONS,
    _render_bridge_md,
    _run_bridge_action,
)
from .review_channel_event_handler import (
    _render_event_md,
    _run_event_action,
)

EVENT_ACTIONS = {"post", "watch", "inbox", "ack", "dismiss", "apply", "history"}


def _error_report(args, message: str, *, exit_code: int) -> tuple[dict, int]:
    """Build a structured error report for any review-channel failure."""
    report = {
        "command": "review-channel",
        "timestamp": utc_timestamp(),
        "action": getattr(args, "action", None),
        "ok": False,
        "exit_ok": False,
        "exit_code": exit_code,
        "execution_mode": getattr(args, "execution_mode", "auto"),
        "terminal": getattr(args, "terminal", "terminal-app"),
        "terminal_profile_requested": getattr(args, "terminal_profile", None),
        "terminal_profile_applied": None,
        "approval_mode": normalize_approval_mode(
            getattr(args, "approval_mode", None),
            dangerous=bool(getattr(args, "dangerous", False)),
        ),
        "dangerous": bool(getattr(args, "dangerous", False)),
        "rollover_threshold_pct": getattr(args, "rollover_threshold_pct", None),
        "rollover_trigger": getattr(args, "rollover_trigger", None),
        "await_ack_seconds": getattr(args, "await_ack_seconds", None),
        "retirement_note": REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
        "errors": [message],
        "warnings": [],
        "sessions": [],
        "handoff_bundle": None,
        "handoff_ack_required": False,
        "handoff_ack_observed": None,
        "bridge_liveness": None,
        "projection_paths": None,
        "artifact_paths": None,
        "packet": None,
        "packets": [],
        "history": [],
        "promotion": None,
        "bridge_heartbeat_refresh": None,
    }
    return report, exit_code


def _render_report(report: dict) -> str:
    """Route to the appropriate markdown renderer based on report mode."""
    if report.get("report_mode") == "event-backed":
        return _render_event_md(report)
    return _render_bridge_md(report)


def _event_report_error_detail(report: dict[str, object]) -> str:
    """Extract a concise error string from an event-backed report."""
    errors = report.get("errors")
    if isinstance(errors, list):
        messages = [str(error).strip() for error in errors if str(error).strip()]
        if messages:
            return "; ".join(messages)
    return "event-backed review-channel state was not ok"


def _validate_args(args) -> None:
    """Validate CLI arguments for the requested review-channel action."""
    rollover_threshold_pct = getattr(args, "rollover_threshold_pct", 50)
    await_ack_seconds = getattr(args, "await_ack_seconds", 0)
    limit = getattr(args, "limit", 20)
    stale_minutes = getattr(args, "stale_minutes", 30)
    expires_in_minutes = getattr(args, "expires_in_minutes", 30)
    if rollover_threshold_pct <= 0 or rollover_threshold_pct > 100:
        raise ValueError("--rollover-threshold-pct must be between 1 and 100.")
    if await_ack_seconds < 0:
        raise ValueError("--await-ack-seconds must be zero or greater.")
    if args.action == "rollover" and await_ack_seconds <= 0:
        raise ValueError(
            "--await-ack-seconds must be greater than zero for rollover so "
            "fresh-session ACK stays fail-closed."
        )
    if args.action == "post":
        if not getattr(args, "from_agent", None):
            raise ValueError("--from-agent is required for review-channel post.")
        if not getattr(args, "to_agent", None):
            raise ValueError("--to-agent is required for review-channel post.")
        if not getattr(args, "kind", None):
            raise ValueError("--kind is required for review-channel post.")
        if not getattr(args, "summary", None):
            raise ValueError("--summary is required for review-channel post.")
        if bool(getattr(args, "body", None)) == bool(getattr(args, "body_file", None)):
            raise ValueError(
                "Review-channel post requires exactly one of --body or --body-file."
            )
    if args.action in {"ack", "dismiss", "apply"}:
        if not getattr(args, "packet_id", None):
            raise ValueError(f"--packet-id is required for review-channel {args.action}.")
        if not getattr(args, "actor", None):
            raise ValueError(f"--actor is required for review-channel {args.action}.")
    if args.action in {"inbox", "watch", "history"} and limit <= 0:
        raise ValueError("--limit must be greater than zero.")
    if stale_minutes <= 0:
        raise ValueError("--stale-minutes must be greater than zero.")
    if expires_in_minutes <= 0:
        raise ValueError("--expires-in-minutes must be greater than zero.")


def _resolve_runtime_paths(args, repo_root: Path) -> dict[str, object]:
    """Resolve all filesystem paths from CLI arguments and repo root."""
    script_dir = None
    if getattr(args, "script_dir", None):
        script_dir = (repo_root / args.script_dir).resolve()
    promotion_plan_rel = getattr(args, "promotion_plan", None) or DEFAULT_PROMOTION_PLAN_REL
    artifact_paths = resolve_artifact_paths(
        repo_root=repo_root,
        artifact_root_rel=getattr(args, "artifact_root", None),
        state_json_rel=getattr(args, "state_json", None),
        projections_dir_rel=getattr(args, "emit_projections", None),
    )
    return {
        "review_channel_path": (repo_root / args.review_channel_path).resolve(),
        "bridge_path": (repo_root / args.bridge_path).resolve(),
        "rollover_dir": (repo_root / args.rollover_dir).resolve(),
        "status_dir": (repo_root / args.status_dir).resolve(),
        "promotion_plan_path": (repo_root / promotion_plan_rel).resolve(),
        "script_dir": script_dir,
        "artifact_paths": artifact_paths,
    }


def _run_status_action(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
) -> tuple[dict, int]:
    """Run the status action with event-backed fallback to bridge-backed mode."""
    artifact_paths = paths["artifact_paths"]
    execution_mode = getattr(args, "execution_mode", "auto")
    fallback_warnings: list[str] = []
    if execution_mode != "markdown-bridge" and event_state_exists(artifact_paths):
        try:
            report, exit_code = _run_event_action(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
        except (OSError, ValueError) as exc:
            fallback_warnings.append(build_bridge_status_fallback_warning(str(exc)))
        else:
            state_errors = summarize_review_state_errors(
                {"ok": report.get("ok"), "errors": report.get("errors")}
            )
            if exit_code == 0 and state_errors is None:
                return report, exit_code
            fallback_warnings.append(
                build_bridge_status_fallback_warning(
                    state_errors or _event_report_error_detail(report)
                )
            )
    if not fallback_warnings:
        return _run_bridge_action(args=args, repo_root=repo_root, paths=paths)
    try:
        return _run_bridge_action(
            args=args,
            repo_root=repo_root,
            paths=paths,
            extra_warnings=fallback_warnings,
            report_execution_mode="markdown-bridge",
        )
    except ValueError as exc:
        raise ValueError(
            f"{fallback_warnings[-1]} Markdown-bridge fallback was unavailable: {exc}"
        ) from exc


def run(args) -> int:
    """Run one review-channel action."""
    repo_root = REPO_ROOT.resolve()
    try:
        _validate_args(args)
        paths = _resolve_runtime_paths(args, repo_root)
        if args.action == "status":
            report, exit_code = _run_status_action(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
        elif args.action in EVENT_ACTIONS:
            report, exit_code = _run_event_action(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
        elif args.action in BRIDGE_ACTIONS or args.action == "promote":
            report, exit_code = _run_bridge_action(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
        else:
            report, exit_code = _error_report(
                args,
                f"Unsupported review-channel action: {args.action}",
                exit_code=2,
            )
    except ValueError as exc:
        report, exit_code = _error_report(args, str(exc), exit_code=1)
    except subprocess.CalledProcessError as exc:
        report, exit_code = _error_report(
            args,
            f"launcher subprocess failed: {exc}",
            exit_code=1,
        )
    except OSError as exc:
        report, exit_code = _error_report(args, str(exc), exit_code=1)

    output = json.dumps(report, indent=2) if args.format == "json" else _render_report(report)
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
    )
    if pipe_rc != 0:
        return pipe_rc
    return exit_code
