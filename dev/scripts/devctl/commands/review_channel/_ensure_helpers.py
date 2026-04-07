"""Heartbeat refresh and detail assembly for ensure-action orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ...review_channel.peer_liveness import REVIEW_CHANNEL_REVIEWER_FOLLOW_COMMAND
from ..review_channel_command import (
    EnsureActionReport,
    EnsureBridgeStatus,
    PublisherLifecycleAssessment,
    RuntimePaths,
    PUBLISHER_FOLLOW_COMMAND,
)

if TYPE_CHECKING:
    from .ensure import EnsureActionDeps


@dataclass(frozen=True, slots=True)
class HeartbeatRefreshResult:
    """Outcome of a bridge heartbeat refresh attempt."""

    refreshed: bool
    detail: str | None
    report: dict[str, object]
    bridge_state: EnsureBridgeStatus


def try_refresh_heartbeat(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths,
    bridge_state: EnsureBridgeStatus,
    report: dict[str, object],
    deps: EnsureActionDeps,
    read_ensure_status_fn,
) -> HeartbeatRefreshResult:
    """Refresh a stale bridge heartbeat and re-read status."""
    no_change = HeartbeatRefreshResult(
        refreshed=False, detail=None, report=report, bridge_state=bridge_state,
    )

    if bridge_state.codex_poll_state not in ("stale", "missing"):
        return no_change

    if paths.bridge_path is None or not paths.bridge_path.exists():
        return no_change

    try:
        result = deps.refresh_bridge_heartbeat_fn(
            repo_root=repo_root,
            bridge_path=paths.bridge_path,
            reason="ensure",
        )

        new_report, new_state = read_ensure_status_fn(
            args=args, repo_root=repo_root, paths=paths, deps=deps,
        )

        return HeartbeatRefreshResult(
            refreshed=True,
            detail=f"Heartbeat refreshed at {result.last_codex_poll_utc}",
            report=new_report,
            bridge_state=new_state,
        )
    except (ValueError, OSError) as exc:
        return HeartbeatRefreshResult(
            refreshed=False,
            detail=f"Heartbeat refresh failed: {exc}",
            report=report,
            bridge_state=bridge_state,
        )


def _supervisor_restart_detail(restart_attempt) -> str | None:
    """Return one detail line describing the supervisor restart outcome."""
    if restart_attempt.restarted:
        return "Reviewer supervisor was dead; auto-restarted."

    start_status = str(restart_attempt.start_status or "")
    if start_status.startswith("non_restartable_stop_reason:"):
        stop_reason = start_status.split(":", 1)[1]
        return (
            f"Reviewer supervisor has stop_reason={stop_reason}; "
            "not auto-restarting."
        )

    if not restart_attempt.attempted:
        return None

    if restart_attempt.start_status == "spawn_failed":
        return "Reviewer supervisor auto-restart failed before launch confirmation."

    if restart_attempt.start_status != "not_attempted":
        return "Reviewer supervisor auto-restart failed before heartbeat confirmation."

    return None


def _choose_recommended_command(
    *,
    bridge_state: EnsureBridgeStatus,
    supervisor_restarted: bool,
    pub: PublisherLifecycleAssessment,
) -> str | None:
    """Pick the single recommended next-step command."""
    if not bridge_state.reviewer_supervisor_ok and not supervisor_restarted:
        return REVIEW_CHANNEL_REVIEWER_FOLLOW_COMMAND

    if pub.publisher_required and not pub.publisher_running:
        return PUBLISHER_FOLLOW_COMMAND

    return pub.recommended_command


def build_ensure_detail(
    *,
    restart_attempt,
    ensure_ok: bool,
    attention_status: str,
    bridge_state: EnsureBridgeStatus,
    refresh_detail: str | None,
    pub: PublisherLifecycleAssessment,
) -> tuple[str, str | None]:
    """Assemble the ensure detail string and recommended command."""
    parts: list[str] = []

    supervisor_detail = _supervisor_restart_detail(restart_attempt)
    if supervisor_detail:
        parts.append(supervisor_detail)

    if ensure_ok:
        parts.append("Reviewer loop is healthy.")
    else:
        parts.append(
            f"Reviewer loop needs attention: {attention_status} "
            f"(poll={bridge_state.codex_poll_state})."
        )

    if refresh_detail:
        parts.append(refresh_detail)

    supervisor_restarted = restart_attempt.restarted
    if not bridge_state.reviewer_supervisor_ok and not supervisor_restarted:
        parts.append(
            "reviewer supervisor follow loop is required while review is pending."
        )

    parts.extend(pub.details)

    command = _choose_recommended_command(
        bridge_state=bridge_state,
        supervisor_restarted=supervisor_restarted,
        pub=pub,
    )

    return " ".join(parts), command


def build_ensure_report(
    *,
    ensure_ok: bool,
    bridge_state: EnsureBridgeStatus,
    attention_status: str,
    hb: HeartbeatRefreshResult,
    pub: PublisherLifecycleAssessment,
    detail: str,
    recommended_command: str | None,
) -> dict:
    """Construct the final EnsureActionReport dict."""
    return EnsureActionReport(
        command="review-channel",
        action="ensure",
        ok=ensure_ok,

        reviewer_mode=bridge_state.reviewer_mode,
        codex_poll_state=bridge_state.codex_poll_state,
        reviewer_freshness=bridge_state.reviewer_freshness,
        heartbeat_age_seconds=bridge_state.heartbeat_age_seconds,
        attention_status=attention_status,

        refreshed=hb.refreshed,
        review_needed=bridge_state.review_needed,
        detail=detail,
        recommended_command=recommended_command,

        publisher=pub.publisher_state,
        publisher_required=pub.publisher_required,
        publisher_status=pub.publisher_status,
        publisher_start_status=pub.publisher_start_status,
        publisher_pid=pub.publisher_pid,
        publisher_log_path=pub.publisher_log_path,

        reviewer_worker=bridge_state.reviewer_worker,
        reviewer_supervisor=bridge_state.reviewer_supervisor,
        service_identity=bridge_state.service_identity,
        attach_auth_policy=bridge_state.attach_auth_policy,
    ).to_report()
