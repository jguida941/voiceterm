"""Helper functions for the `devctl review-channel` command."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ...approval_mode import normalize_approval_mode
from ...review_channel.launch_authority_ordering import launch_authority_report_fields
from ...review_channel.events import resolve_artifact_paths
from .constants import CLI_RUNTIME_PATH_ARGS
from .constants import EVENT_STATUS_FALLBACK_DETAIL
from .constants import ReviewChannelAction
from .models import ReviewChannelErrorReport
from .models import RuntimePaths
from .validation import _require_nonnegative
from .validation import _require_percentage
from .validation import _require_positive
from .validation import _require_present
from .validation import _validate_args
from .validation import _validate_common_limits
from .validation import _validate_required_args


def _coerce_action(action: object) -> ReviewChannelAction:
    """Normalize one CLI action string."""
    try:
        return ReviewChannelAction(str(action))
    except ValueError as exc:
        raise ValueError(f"Unsupported review-channel action: {action}") from exc


def _coerce_runtime_paths(paths: RuntimePaths | Mapping[str, object]) -> RuntimePaths:
    """Accept typed paths or legacy dict inputs."""
    if isinstance(paths, RuntimePaths):
        return paths
    return RuntimePaths.from_mapping(paths)


def _error_report(args, message: str, *, exit_code: int) -> tuple[dict[str, object], int]:
    """Build a structured failure report."""
    dangerous = bool(getattr(args, "dangerous", False))
    payload = ReviewChannelErrorReport(
        action=getattr(args, "action", None),
        exit_code=exit_code,
        execution_mode=getattr(args, "execution_mode", "auto"),
        terminal=getattr(args, "terminal", "terminal-app"),
        terminal_profile_requested=getattr(args, "terminal_profile", None),
        approval_mode=normalize_approval_mode(
            getattr(args, "approval_mode", None),
            dangerous=dangerous,
        ),
        dangerous=dangerous,
        rollover_threshold_pct=getattr(args, "rollover_threshold_pct", None),
        rollover_trigger=getattr(args, "rollover_trigger", None),
        await_ack_seconds=getattr(args, "await_ack_seconds", None),
        errors=[message],
        **launch_authority_report_fields(args),
    )
    return payload.to_report(), exit_code


def _render_report(report: dict[str, object]) -> str:
    """Render one report as markdown."""
    if report.get("report_mode") == "event-backed":
        from ..review_channel_event_handler import _render_event_md

        return _render_event_md(report)
    from ..review_channel.bridge_handler import _render_bridge_md

    return _render_bridge_md(report)


def _event_report_error_detail(report: dict[str, object]) -> str:
    """Summarize event report errors."""
    errors = report.get("errors")
    if not isinstance(errors, list):
        return EVENT_STATUS_FALLBACK_DETAIL

    messages = [text for error in errors if (text := str(error).strip())]
    return "; ".join(messages) or EVENT_STATUS_FALLBACK_DETAIL


def _resolve_runtime_paths(args, repo_root: Path) -> RuntimePaths:
    """Resolve review-channel runtime paths."""
    resolved_paths = {
        name: (repo_root / getattr(args, name)).resolve()
        for name in CLI_RUNTIME_PATH_ARGS
    }
    promotion_plan_rel = getattr(args, "promotion_plan", None)
    script_dir = None
    if getattr(args, "script_dir", None):
        script_dir = (repo_root / args.script_dir).resolve()

    artifact_paths = resolve_artifact_paths(
        repo_root=repo_root,
        artifact_root_rel=getattr(args, "artifact_root", None),
        state_json_rel=getattr(args, "state_json", None),
        projections_dir_rel=getattr(args, "emit_projections", None),
    )
    return RuntimePaths(
        **resolved_paths,
        promotion_plan_path=(
            (repo_root / str(promotion_plan_rel)).resolve()
            if promotion_plan_rel
            else None
        ),
        script_dir=script_dir,
        artifact_paths=artifact_paths,
    )
