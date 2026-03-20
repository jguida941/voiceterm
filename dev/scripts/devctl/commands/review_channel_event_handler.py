"""Event-backed action rendering and execution for `devctl review-channel`.

Handles post, watch, inbox, ack, dismiss, apply, and history actions that
operate against the structured event store. Extracted from
commands/review_channel.py to keep the command orchestrator under the
file-size soft limit.
"""

from __future__ import annotations

import time
from pathlib import Path

from ..common import emit_output as compat_emit_output
from ..review_channel.context_refs import (
    resolve_context_pack_refs,
)
from ..review_channel.events import (
    artifact_paths_to_dict,
    filter_history_events,
    filter_inbox_packets,
    load_or_refresh_event_bundle,
    post_packet,
    refresh_event_bundle,
    transition_packet,
)
from ..review_channel.packet_contract import (
    PacketPostRequest,
    PacketTargetFields,
    PacketTransitionRequest,
)
from ..review_channel.event_render import render_event_md
from ..review_channel.follow_stream import (
    build_follow_completion_report,
    build_follow_output_error_report,
    emit_follow_ndjson_frame,
    reset_follow_output,
    validate_follow_json_format,
)
from ..review_channel.state import projection_paths_to_dict
from ..time_utils import utc_timestamp


emit_output = compat_emit_output


def _build_event_report(
    *,
    args,
    bundle,
    packet: dict[str, object] | None = None,
    event: dict[str, object] | None = None,
    packets: list[dict[str, object]] | None = None,
    history: list[dict[str, object]] | None = None,
    warnings: list[str] | None = None,
) -> tuple[dict, int]:
    """Assemble the event-backed action report dict."""
    report_warnings = list(bundle.review_state.get("warnings", []))
    report_warnings.extend(warnings or [])
    report_errors = list(bundle.review_state.get("errors", []))
    report = {
        "command": "review-channel",
        "timestamp": utc_timestamp(),
        "action": args.action,
        "report_mode": "event-backed",
        "ok": not report_errors,
        "exit_ok": not report_errors,
        "exit_code": 0 if not report_errors else 1,
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
        "queue": bundle.review_state.get("queue", {}),
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
        "event": event,
        "target": getattr(args, "target", None),
        "status_filter": getattr(args, "status", None),
        "limit": getattr(args, "limit", None),
    }
    return report, report["exit_code"]


def _load_post_body(args) -> str:
    """Read the packet body from --body or --body-file."""
    body = getattr(args, "body", None)
    body_file = getattr(args, "body_file", None)
    if body:
        return str(body)
    assert body_file is not None
    return Path(body_file).read_text(encoding="utf-8")


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
    if args.action == "post":
        bundle, event = post_packet(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
            request=PacketPostRequest(
                from_agent=args.from_agent,
                to_agent=args.to_agent,
                kind=args.kind,
                summary=args.summary,
                body=_load_post_body(args),
                evidence_refs=tuple(args.evidence_ref or []),
                context_pack_refs=tuple(resolve_context_pack_refs(args, repo_root)),
                confidence=float(args.confidence),
                requested_action=args.requested_action,
                policy_hint=args.policy_hint,
                approval_required=bool(args.approval_required),
                packet_id=getattr(args, "packet_id", None),
                trace_id=getattr(args, "trace_id", None),
                session_id=args.session_id,
                plan_id=args.plan_id,
                controller_run_id=getattr(args, "controller_run_id", None),
                expires_in_minutes=args.expires_in_minutes,
                target=PacketTargetFields.from_values(
                    target_kind=getattr(args, "target_kind", None),
                    target_ref=getattr(args, "target_ref", None),
                    target_revision=getattr(args, "target_revision", None),
                    anchor_refs=getattr(args, "anchor_ref", []),
                    intake_ref=getattr(args, "intake_ref", None),
                    mutation_op=getattr(args, "mutation_op", None),
                ),
            ),
        )
        packet = next(
            (
                packet_row
                for packet_row in bundle.review_state.get("packets", [])
                if isinstance(packet_row, dict)
                and packet_row.get("packet_id") == event.get("packet_id")
            ),
            None,
        )
        return _build_event_report(args=args, bundle=bundle, packet=packet, event=event)
    if args.action in {"ack", "dismiss", "apply"}:
        bundle, event = transition_packet(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
            request=PacketTransitionRequest(
                action=args.action,
                packet_id=args.packet_id,
                actor=args.actor,
                session_id=args.session_id,
                plan_id=args.plan_id,
                controller_run_id=getattr(args, "controller_run_id", None),
            ),
        )
        packet = next(
            (
                packet_row
                for packet_row in bundle.review_state.get("packets", [])
                if isinstance(packet_row, dict)
                and packet_row.get("packet_id") == args.packet_id
            ),
            None,
        )
        return _build_event_report(args=args, bundle=bundle, packet=packet, event=event)
    bundle = load_or_refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    if args.action == "status":
        bundle = refresh_event_bundle(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
        return _build_event_report(args=args, bundle=bundle)
    if args.action == "inbox":
        packets = filter_inbox_packets(
            bundle.review_state,
            target=getattr(args, "target", None),
            status=getattr(args, "status", None),
            limit=args.limit,
        )
        return _build_event_report(args=args, bundle=bundle, packets=packets)
    if args.action == "watch":
        packets = filter_inbox_packets(
            bundle.review_state,
            target=getattr(args, "target", None),
            status=getattr(args, "status", None) or "pending",
            limit=args.limit,
        )
        if getattr(args, "follow", False):
            return _run_watch_follow(
                args=args,
                repo_root=repo_root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                initial_bundle=bundle,
                initial_packets=packets,
            )
        return _build_event_report(
            args=args,
            bundle=bundle,
            packets=packets,
        )
    if args.action == "history":
        history = filter_history_events(
            bundle.events,
            trace_id=getattr(args, "trace_id", None),
            limit=args.limit,
        )
        return _build_event_report(args=args, bundle=bundle, history=history)
    raise ValueError(f"Unsupported event-backed review-channel action: {args.action}")


def _render_event_md(report: dict) -> str:
    """Compatibility wrapper for the moved event-backed markdown renderer."""
    return render_event_md(report)


def _run_watch_follow(
    *,
    args,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths,
    initial_bundle,
    initial_packets: list,
) -> tuple[dict, int]:
    """Poll the event store and return snapshots as NDJSON when packets change.

    ``--limit`` controls packet row count per snapshot (unchanged CLI contract).
    The stream runs until interrupted or until ``--max-follow-snapshots``
    snapshots have been emitted (default: unbounded).
    """
    validate_follow_json_format(action="watch", output_format=getattr(args, "format", "json"))
    interval = max(5, (getattr(args, "stale_minutes", 30) * 60) // 6)
    max_snapshots = getattr(args, "max_follow_snapshots", 0) or 0
    target = getattr(args, "target", None)
    status_filter = getattr(args, "status", None) or "pending"

    def _emit(report: dict, seq: int) -> int:
        frame = dict(report)
        frame["follow"] = True
        frame["snapshot_seq"] = seq
        return emit_follow_ndjson_frame(frame, args=args)

    # Emit initial snapshot through the normal output path
    reset_follow_output(getattr(args, "output", None))
    report, _ = _build_event_report(
        args=args, bundle=initial_bundle, packets=initial_packets,
    )
    pipe_rc = _emit(report, 0)
    if pipe_rc != 0:
        return build_follow_output_error_report(
            action="watch",
            snapshots_emitted=0,
            pipe_rc=pipe_rc,
        ), pipe_rc

    prev_ids = {p.get("packet_id") for p in initial_packets if isinstance(p, dict)}
    emitted_count = 1
    seq = 1

    try:
        while max_snapshots == 0 or emitted_count < max_snapshots:
            time.sleep(interval)
            try:
                bundle = refresh_event_bundle(
                    repo_root=repo_root,
                    review_channel_path=review_channel_path,
                    artifact_paths=artifact_paths,
                )
            except (OSError, ValueError):
                continue
            packets = filter_inbox_packets(
                bundle.review_state, target=target,
                status=status_filter, limit=args.limit,
            )
            cur_ids = {p.get("packet_id") for p in packets if isinstance(p, dict)}
            if cur_ids != prev_ids:
                report, _ = _build_event_report(
                    args=args,
                    bundle=bundle,
                    packets=packets,
                )
                pipe_rc = _emit(report, seq)
                if pipe_rc != 0:
                    return build_follow_output_error_report(
                        action="watch",
                        snapshots_emitted=emitted_count,
                        pipe_rc=pipe_rc,
                    ), pipe_rc
                prev_ids = cur_ids
                emitted_count += 1
                seq += 1
    except KeyboardInterrupt:
        pass

    return build_follow_completion_report(
        action="watch",
        snapshots_emitted=emitted_count,
        ok=True,
    ), 0
