"""Success-report assembly for bridge-backed review-channel actions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ...approval_mode import normalize_approval_mode
from ...review_channel.core import REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE
from ...review_channel.handoff import handoff_bundle_to_dict
from ...review_channel.heartbeat import bridge_heartbeat_refresh_to_dict
from ...review_channel.peer_liveness import OverallLivenessState
from ...review_channel.promotion import promotion_candidate_to_dict
from ...review_channel.reviewer_state import reviewer_state_write_to_dict
from ...review_channel.runtime_counts import build_runtime_counts
from ...review_channel.state import projection_paths_to_dict
from ...time_utils import utc_timestamp


@dataclass(frozen=True, slots=True)
class BridgeSuccessReportRequest:
    args: object
    bridge_liveness: dict[str, object]
    attention: dict[str, object]
    reviewer_worker: dict[str, object] | None
    codex_lanes: list
    claude_lanes: list
    terminal_profile_applied: str | None
    warnings: list[str]
    sessions: list[dict[str, object]]
    handoff_bundle: object
    projection_paths: object
    launched: bool
    handoff_ack_required: bool
    handoff_ack_observed: dict[str, bool] | None
    collaboration: Mapping[str, object] | None = None
    promotion: object | None = None
    bridge_heartbeat_refresh: object | None = None
    reviewer_state_write: object | None = None
    execution_mode_override: str | None = None


def build_bridge_success_report(
    request: BridgeSuccessReportRequest,
) -> tuple[dict, int]:
    """Assemble the bridge-action success report dict."""
    planned_rollover = (
        request.args.action == "rollover"
        and bool(getattr(request.args, "dry_run", False))
        and request.handoff_bundle is not None
    )
    report_ok = (
        str(request.bridge_liveness.get("overall_state") or "unknown")
        in {OverallLivenessState.FRESH, OverallLivenessState.INACTIVE}
        or request.bridge_heartbeat_refresh is not None
        or request.launched
        or planned_rollover
    )
    report = _base_success_report(request, report_ok=report_ok)
    _attach_report_warnings(report, request=request)
    if request.handoff_ack_required and request.handoff_ack_observed is not None:
        missing = [
            provider
            for provider, observed in request.handoff_ack_observed.items()
            if not observed
        ]
        if missing:
            report["ok"] = False
            report["exit_ok"] = False
            report["exit_code"] = 1
            report["errors"].append(
                "Timed out waiting for fresh-conductor rollover ACK lines "
                f"from: {', '.join(missing)}"
            )
            return report, 1
    return report, 0


def _base_success_report(
    request: BridgeSuccessReportRequest,
    *,
    report_ok: bool,
) -> dict:
    args = request.args
    report = dict((
        ("command", "review-channel"),
        ("timestamp", utc_timestamp()),
        ("action", args.action),
        ("ok", report_ok),
        ("exit_ok", True),
        ("exit_code", 0),
        ("execution_mode", _execution_mode(args, request.execution_mode_override)),
        ("terminal", args.terminal),
        ("terminal_profile_requested", args.terminal_profile),
        ("terminal_profile_applied", request.terminal_profile_applied),
        (
            "approval_mode",
            normalize_approval_mode(
                getattr(args, "approval_mode", None),
                dangerous=bool(args.dangerous),
            ),
        ),
        ("dangerous", bool(args.dangerous)),
        ("rollover_threshold_pct", args.rollover_threshold_pct),
        ("rollover_trigger", args.rollover_trigger if args.action == "rollover" else None),
        ("await_ack_seconds", args.await_ack_seconds),
        ("bridge_active", True),
        ("launched", request.launched),
        (
            "typed_state_written",
            _typed_state_written(
                action=args.action,
                dry_run=bool(getattr(args, "dry_run", False)),
                sessions=request.sessions,
            ),
        ),
        (
            "process_alive",
            _launch_process_alive(
                launched=request.launched,
                sessions=request.sessions,
            ),
        ),
        ("bridge_attached", _bridge_attached(request.bridge_liveness)),
        ("launch_visibility", getattr(args, "launch_visibility", None)),
        ("handoff_ack_required", request.handoff_ack_required),
        ("handoff_ack_observed", request.handoff_ack_observed),
        ("codex_requested_worker_budget", args.codex_workers),
        ("claude_requested_worker_budget", args.claude_workers),
        ("retirement_note", REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE),
        (
            "runtime_counts",
            build_runtime_counts(
                collaboration=request.collaboration,
                bridge_liveness=request.bridge_liveness,
                requested_worker_budgets={
                    "codex": args.codex_workers,
                    "claude": args.claude_workers,
                },
            ),
        ),
        ("warnings", request.warnings),
        ("errors", []),
        ("sessions", request.sessions),
        ("handoff_bundle", handoff_bundle_to_dict(request.handoff_bundle)),
        ("bridge_liveness", request.bridge_liveness),
        ("attention", request.attention),
        ("reviewer_worker", request.reviewer_worker),
        ("projection_paths", projection_paths_to_dict(request.projection_paths)),
        ("promotion", promotion_candidate_to_dict(request.promotion)),
        (
            "bridge_heartbeat_refresh",
            bridge_heartbeat_refresh_to_dict(request.bridge_heartbeat_refresh),
        ),
        (
            "reviewer_state_write",
            reviewer_state_write_to_dict(request.reviewer_state_write),
        ),
    ))
    if isinstance(request.reviewer_worker, dict):
        report["review_needed"] = bool(request.reviewer_worker.get("review_needed"))
    return report


def _attach_report_warnings(
    report: dict,
    *,
    request: BridgeSuccessReportRequest,
) -> None:
    if request.bridge_heartbeat_refresh is not None:
        report["warnings"].append(
            "Auto-refreshed the markdown-bridge reviewer heartbeat before "
            f"{request.args.action} so the live launch contract could proceed."
        )
    if (
        request.reviewer_state_write is not None
        and getattr(request.reviewer_state_write, "reason", "")
        == "auto-demote-stale-bridge"
    ):
        report["warnings"].append(
            "Auto-demoted the stale markdown bridge to `paused` because no live "
            "reviewer runtime owner was detected."
        )


def _execution_mode(args, execution_mode_override: str | None) -> str:
    return execution_mode_override or (
        "markdown-bridge"
        if args.execution_mode in ("auto", "markdown-bridge")
        else args.execution_mode
    )


def _typed_state_written(
    *,
    action: str,
    dry_run: bool,
    sessions: list[dict[str, object]],
) -> bool:
    return action in {"launch", "rollover"} and not dry_run and bool(sessions)


def _launch_process_alive(
    *,
    launched: bool,
    sessions: list[dict[str, object]],
) -> bool:
    if not launched:
        return False
    headless_statuses = [
        str(session.get("headless_launch_status") or "").strip()
        for session in sessions
        if str(session.get("headless_launch_status") or "").strip()
    ]
    if headless_statuses:
        return any(status == "alive" for status in headless_statuses)
    if any(session.get("terminal_window_id") for session in sessions):
        return True
    return launched


def _bridge_attached(bridge_liveness: dict[str, object]) -> bool:
    if any(
        bool(bridge_liveness.get(key))
        for key in (
            "codex_conductor_active",
            "claude_conductor_active",
            "cursor_conductor_active",
        )
    ):
        return True
    try:
        return int(bridge_liveness.get("active_conductor_count") or 0) > 0
    except (TypeError, ValueError):
        return False


__all__ = ["BridgeSuccessReportRequest", "build_bridge_success_report"]
