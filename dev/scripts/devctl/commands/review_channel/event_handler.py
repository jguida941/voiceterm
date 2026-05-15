"""Event-backed action rendering and execution for `devctl review-channel`.

Handles post, watch, inbox, operator-inbox, ack, dismiss, apply, and history actions that
operate against the structured event store. Extracted from
commands/review_channel.py to keep the command orchestrator under the
file-size soft limit.
"""

from __future__ import annotations

from pathlib import Path
import time
from types import SimpleNamespace

from ...common import emit_output as compat_emit_output
from ...review_channel.events import (
    artifact_paths_to_dict,
    filter_history_packets,
    filter_history_events,
    load_or_refresh_event_bundle,
    refresh_event_bundle,
)
from ...review_channel.follow_stream import (
    build_follow_completion_report,
    build_follow_output_error_report,
    emit_follow_ndjson_frame,
    reset_follow_output,
    validate_follow_json_format,
)
from ...review_channel.pending_packets import reconcile_review_state_packet_queue
from ...review_channel.packet_body_observation import record_packet_body_observation
from ...review_channel.projection_bundle import artifact_writes_suppressed
from ...review_channel.readable_packet_projection import (
    build_operational_summary_view,
    history_operational_summary_requested,
)
from ...review_channel.state import projection_paths_to_dict
from ...review_channel.watch_lifecycle import (
    claim_watch_lifecycle,
    release_watch_lifecycle,
    watch_parent_is_alive,
    write_watch_heartbeat,
    write_watch_stop,
)
from ...review_channel.watch_paths import watch_key
from ...time_utils import utc_timestamp
from .event_action_support import (
    EventActionContext,
    run_inbox_like_action,
)
from .event_ack_freshness_action import run_check_ack_freshness_action
from .event_handler_side_effects import (
    run_implementer_ack_with_bridge_sync,
    run_post_action_with_side_effects,
)
from .event_history_outcomes import attach_history_outcomes_if_requested
from .event_expire_packets_action import run_expire_packets_action
from .event_packet_transition_action import run_packet_transition_action
from .event_queue_report import queue_for_event_report
from .sync_status_action import run_sync_status_action
from .event_watch_support import load_target_packets, watch_snapshot_signature
from .watch_follow import WatchFollowDeps, run_watch_follow


emit_output = compat_emit_output


def _build_event_report(
    *,
    args,
    bundle,
    packet: dict[str, object] | None = None,
    event: dict[str, object] | None = None,
    packets: list[dict[str, object]] | None = None,
    history: list[dict[str, object]] | None = None,
    packet_outcome_ledger: dict[str, object] | None = None,
    packet_expiry_materialization: dict[str, object] | None = None,
    operational_summary_view: dict[str, object] | None = None,
    operational_summary_only: bool = False,
    warnings: list[str] | None = None,
) -> tuple[dict, int]:
    """Assemble the event-backed action report dict."""
    report_warnings = list(bundle.review_state.get("warnings", []))
    report_warnings.extend(warnings or [])
    report_errors = list(bundle.review_state.get("errors", []))
    queue_reconciliation = None
    if (
        args.action in {"status", "history"}
        and getattr(args, "target", None) is None
    ):
        history_limit = (
            getattr(args, "limit", None)
            if args.action in {"history", "show"}
            else None
        )
        queue_reconciliation = reconcile_review_state_packet_queue(
            bundle.review_state,
            history_limit=history_limit,
        ).to_dict()
    queue = queue_for_event_report(args=args, bundle=bundle, packets=packets)
    report = {
        "command": "review-channel",
        "timestamp": utc_timestamp(),
        "action": args.action,
        "report_mode": "event-backed",
        "ok": not report_errors,
        "exit_ok": not report_errors,
        "exit_code": 0 if not report_errors else 1,
        "status": "ok" if not report_errors else "blocked",
        "execution_mode": "event-backed",
        "terminal": "none",
        "terminal_profile_requested": getattr(args, "terminal_profile", None),
        "terminal_profile_applied": None,
        "approval_mode": getattr(args, "approval_mode", "balanced"),
        "dangerous": False,
        "warnings": report_warnings,
        "errors": report_errors,
        "sessions": [],
        "handoff_bundle": None,
        "handoff_ack_required": False,
        "handoff_ack_observed": None,
        "bridge_liveness": None,
        "projection_paths": projection_paths_to_dict(bundle.projection_paths),
        "artifact_paths": artifact_paths_to_dict(bundle.artifact_paths),
        "queue": queue,
        "queue_reconciliation": queue_reconciliation,
        "packet": packet,
        "packets": packets or [],
        "pending_packets": [
            p for p in (packets or [])
            if isinstance(p, dict) and p.get("status") == "pending"
        ],
        "resolved_packets": [
            p for p in (packets or [])
            if isinstance(p, dict) and p.get("status") != "pending"
        ],
        "history": history or [],
        "packet_outcome_ledger": packet_outcome_ledger,
        "packet_expiry_materialization": packet_expiry_materialization,
        "operational_summary_view": operational_summary_view,
        "operational_summary_only": operational_summary_only,
        "event": event,
        "target": getattr(args, "target", None),
        "target_role": getattr(args, "target_role", None),
        "target_session_id": getattr(args, "target_session_id", None),
        "status_filter": getattr(args, "status", None),
        "limit": getattr(args, "limit", None),
    }
    return report, report["exit_code"]


def _run_event_action(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
) -> tuple[dict, int]:
    """Execute an event-backed review-channel action (post, inbox, watch, ack, etc.)."""
    review_channel_path = paths["review_channel_path"]
    artifact_paths = paths["artifact_paths"]
    assert isinstance(review_channel_path, Path)
    context = EventActionContext(
        args=args,
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
        build_event_report_fn=_build_event_report,
    )
    if args.action == "watch" and getattr(args, "follow", False):
        return _run_watch_follow(
            args=args,
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
    if args.action == "post":
        report, exit_code, _review_state_payload = run_post_action_with_side_effects(
            context=context,
            args=args,
            repo_root=repo_root,
            paths=paths,
        )
        if getattr(args, "follow", False) and exit_code == 0:
            return _run_watch_follow(
                args=_post_follow_watch_args(args),
                repo_root=repo_root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
            )
        return report, exit_code
    if args.action == "implementer-ack":
        return run_implementer_ack_with_bridge_sync(
            context=context,
            repo_root=repo_root,
            paths=paths,
        )
    if args.action in {"ack", "dismiss", "apply"}:
        return run_packet_transition_action(context=context)
    if args.action in {"status", "sync-status"}:
        bundle = refresh_event_bundle(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
        if args.action == "status":
            return _build_event_report(args=args, bundle=bundle)
        return run_sync_status_action(args=args, bundle=bundle)
    bundle = load_or_refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    return _run_loaded_bundle_action(args=args, context=context, bundle=bundle)


def _run_loaded_bundle_action(
    *,
    args,
    context: EventActionContext,
    bundle,
) -> tuple[dict, int]:
    if args.action == "status":
        return _build_event_report(args=args, bundle=bundle)
    if args.action == "inbox":
        return run_inbox_like_action(context=context, bundle=bundle)
    if args.action == "operator-inbox":
        return run_inbox_like_action(
            context=context,
            bundle=bundle,
            target_override="operator",
            status_override="pending",
            observe_action_requests=False,
        )
    if args.action == "sync-status":
        return run_sync_status_action(args=args, bundle=bundle)
    if args.action == "check-ack-freshness":
        return run_check_ack_freshness_action(context=context, bundle=bundle)
    if args.action == "expire-packets":
        return run_expire_packets_action(context=context)
    if args.action == "watch":
        return run_inbox_like_action(
            context=context,
            bundle=bundle,
            status_override="pending",
        )
    if args.action in {"history", "show"}:
        summary_requested = history_operational_summary_requested(args)
        packets = filter_history_packets(
            bundle.review_state,
            target=getattr(args, "target", None),
            packet_id=getattr(args, "packet_id", None),
            limit=args.limit if args.action == "history" else 1,
        )
        body_observation_event = None
        actor = str(getattr(args, "actor", "") or "").strip()
        if (
            args.action == "show"
            and actor
            and len(packets) == 1
            and not artifact_writes_suppressed()
        ):
            bundle, body_observation_event = record_packet_body_observation(
                repo_root=context.repo_root,
                review_channel_path=context.review_channel_path,
                artifact_paths=context.artifact_paths,
                bundle=bundle,
                packet=packets[0],
                actor=actor,
                role=str(getattr(args, "target_role", "") or ""),
                session_id=str(getattr(args, "target_session_id", "") or ""),
            )
            packets = filter_history_packets(
                bundle.review_state,
                target=getattr(args, "target", None),
                packet_id=getattr(args, "packet_id", None),
                limit=1,
            )
        packets, packet_outcome_ledger = attach_history_outcomes_if_requested(
            args=args,
            bundle=bundle,
            packets=packets,
            generated_at_utc=utc_timestamp(),
        )
        history = []
        if getattr(args, "trace_id", None) or getattr(args, "packet_id", None):
            history = filter_history_events(
                bundle.events,
                trace_id=getattr(args, "trace_id", None),
                packet_id=getattr(args, "packet_id", None),
                limit=args.limit,
            )
        return _build_event_report(
            args=args,
            bundle=bundle,
            packet=packets[0] if len(packets) == 1 else None,
            packets=packets,
            history=history,
            packet_outcome_ledger=packet_outcome_ledger,
            event=body_observation_event,
            operational_summary_view=(
                build_operational_summary_view(
                    bundle.review_state,
                    target=getattr(args, "target", None),
                    sample_limit=getattr(args, "limit", None),
                    generated_at_utc=utc_timestamp(),
                )
                if summary_requested
                else None
            ),
            operational_summary_only=summary_requested,
        )
    raise ValueError(f"Unsupported event-backed review-channel action: {args.action}")


def _render_event_md(report: dict) -> str:
    """Compatibility wrapper for the moved event-backed markdown renderer."""
    from ...review_channel.event_render import render_event_md

    return render_event_md(report)


def _run_watch_follow(
    *,
    args,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths,
) -> tuple[dict, int]:
    return run_watch_follow(
        args=args,
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
        deps=WatchFollowDeps(
            validate_follow_json_format_fn=validate_follow_json_format,
            reset_follow_output_fn=reset_follow_output,
            emit_follow_ndjson_frame_fn=emit_follow_ndjson_frame,
            build_follow_output_error_report_fn=build_follow_output_error_report,
            build_follow_completion_report_fn=build_follow_completion_report,
            claim_watch_lifecycle_fn=claim_watch_lifecycle,
            release_watch_lifecycle_fn=release_watch_lifecycle,
            write_watch_heartbeat_fn=write_watch_heartbeat,
            write_watch_stop_fn=write_watch_stop,
            watch_parent_is_alive_fn=watch_parent_is_alive,
            load_or_refresh_event_bundle_fn=load_or_refresh_event_bundle,
            refresh_event_bundle_fn=refresh_event_bundle,
            load_target_packets_fn=load_target_packets,
            watch_snapshot_signature_fn=watch_snapshot_signature,
            build_event_report_fn=_build_event_report,
            watch_key_fn=watch_key,
            utc_timestamp_fn=utc_timestamp,
            sleep_fn=time.sleep,
        ),
    )


def _post_follow_watch_args(args) -> SimpleNamespace:
    """Convert `post --follow` into a target watch over the posted packet lane."""
    values = dict(vars(args))
    values["action"] = "watch"
    values["target"] = str(getattr(args, "to_agent", "") or "")
    values["status"] = getattr(args, "status", None) or "pending"
    return SimpleNamespace(**values)
