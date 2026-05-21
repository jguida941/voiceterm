"""Event-backed action rendering and execution for `devctl review-channel`.

Handles post, watch, inbox, operator-inbox, ack, dismiss, apply, and history actions that
operate against the structured event store. Extracted from
commands/review_channel.py to keep the command orchestrator under the
file-size soft limit.
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import time
from types import SimpleNamespace

from ...runtime.control_decision_artifacts import load_control_decision_payload
from ...runtime.control_decision_obedience import (
    build_attempted_action_receipt,
    evaluate_control_decision_obedience,
)
from ...runtime.value_coercion import coerce_string
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
from ...review_channel.agent_packet_attention import packet_attention_for_agent
from ...review_channel.packet_semantic_ingestion import record_packet_semantic_ingestion
from ...review_channel.packet_absorption import record_packet_absorption
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
from ...runtime.packet_attention_drain_report import (
    build_packet_attention_drain_report,
)
from .event_action_support import (
    EventActionContext,
    run_inbox_like_action,
)
from .event_attempted_action_scope import (
    ProxyAuthorityRoute,
    ProxyAuthoritySource,
    action_actor as _action_actor,
    action_role as _action_role,
    action_session_id as _action_session_id,
    executor_actor as _executor_actor,
    executor_role as _executor_role,
    executor_session_id as _executor_session_id,
    proxy_authority_ref as _proxy_authority_ref,
    review_channel_attempted_argv as _review_channel_attempted_argv,
    review_channel_attempted_command as _review_channel_attempted_command,
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
    packet_attention_drain_report: dict[str, object] | None = None,
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
        "packet_attention_drain_report": packet_attention_drain_report,
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
        gate = _review_channel_lifecycle_gate(
            args=args,
            context=context,
            packet_id=str(getattr(args, "packet_id", "") or ""),
        )
        if not gate["ok"]:
            bundle = load_or_refresh_event_bundle(
                repo_root=repo_root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
            )
            return _blocked_obedience_event_report(
                context=context,
                args=args,
                bundle=bundle,
                gate=gate,
            )
        report, exit_code, _review_state_payload = run_post_action_with_side_effects(
            context=context,
            args=args,
            repo_root=repo_root,
            paths=paths,
        )
        report["control_decision_obedience"] = gate
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
        gate = _review_channel_lifecycle_gate(
            args=args,
            context=context,
            packet_id=str(getattr(args, "packet_id", "") or ""),
        )
        if not gate["ok"]:
            bundle = load_or_refresh_event_bundle(
                repo_root=repo_root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
            )
            return _blocked_obedience_event_report(
                context=context,
                args=args,
                bundle=bundle,
                gate=gate,
            )
        report, exit_code = run_packet_transition_action(context=context)
        report["control_decision_obedience"] = gate
        return report, exit_code
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
    if args.action == "ingest":
        return _run_semantic_ingest_action(
            args=args,
            context=context,
            bundle=bundle,
        )
    if args.action == "absorb":
        return _run_packet_absorb_action(
            args=args,
            context=context,
            bundle=bundle,
        )
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
        packet_attention_before = None
        packet_attention_drain_report = None
        control_decision_gate = None
        actor = str(getattr(args, "actor", "") or "").strip()
        actor_role = _action_role(args)
        actor_session_id = _action_session_id(args)
        if (
            args.action == "show"
            and actor
            and len(packets) == 1
            and not artifact_writes_suppressed()
        ):
            gate = _review_channel_lifecycle_gate(
                args=args,
                context=context,
                packet_id=str(packets[0].get("packet_id") or ""),
            )
            if not gate["ok"]:
                return _blocked_obedience_event_report(
                    context=context,
                    args=args,
                    bundle=bundle,
                    gate=gate,
                )
            control_decision_gate = gate
            packet_attention_before = packet_attention_for_agent(
                bundle.review_state,
                actor=actor,
                role=actor_role,
                session=actor_session_id,
            )
            bundle, body_observation_event = record_packet_body_observation(
                repo_root=context.repo_root,
                review_channel_path=context.review_channel_path,
                artifact_paths=context.artifact_paths,
                bundle=bundle,
                packet=packets[0],
                actor=actor,
                role=actor_role,
                session_id=actor_session_id,
            )
            packets = filter_history_packets(
                bundle.review_state,
                target=getattr(args, "target", None),
                packet_id=getattr(args, "packet_id", None),
                limit=1,
            )
            if packet_attention_before is not None and packets:
                packet_attention_after = packet_attention_for_agent(
                    bundle.review_state,
                    actor=actor,
                    role=actor_role,
                    session=actor_session_id,
                )
                receipts = packets[0].get("packet_observation_receipts") or ()
                packet_attention_drain_report = build_packet_attention_drain_report(
                    observer_actor_id=actor,
                    observer_role_id=actor_role,
                    observer_session_id=actor_session_id,
                    generated_at_utc=utc_timestamp(),
                    before_attention=packet_attention_before,
                    after_attention=packet_attention_after,
                    observation_receipts=receipts if isinstance(receipts, list) else (),
                ).to_dict()
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
        report, exit_code = _build_event_report(
            args=args,
            bundle=bundle,
            packet=packets[0] if len(packets) == 1 else None,
            packets=packets,
            history=history,
            packet_outcome_ledger=packet_outcome_ledger,
            packet_attention_drain_report=packet_attention_drain_report,
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
        if control_decision_gate is not None:
            report["control_decision_obedience"] = control_decision_gate
        return report, exit_code
    raise ValueError(f"Unsupported event-backed review-channel action: {args.action}")


def _run_semantic_ingest_action(
    *,
    args,
    context: EventActionContext,
    bundle,
) -> tuple[dict, int]:
    packet_id = str(getattr(args, "packet_id", "") or "").strip()
    actor = str(getattr(args, "actor", "") or "").strip()
    if not packet_id:
        return _blocked_event_report(
            context=context,
            args=args,
            bundle=bundle,
            reason="packet_semantic_ingestion_requires_packet_id",
            warning="review-channel ingest requires --packet-id",
        )
    if not actor:
        return _blocked_event_report(
            context=context,
            args=args,
            bundle=bundle,
            reason="packet_semantic_ingestion_requires_actor",
            warning="review-channel ingest requires --actor",
        )
    action_item_rows, parse_error = _semantic_action_item_rows_from_args(args)
    if parse_error:
        return _blocked_event_report(
            context=context,
            args=args,
            bundle=bundle,
            reason="packet_semantic_ingestion_invalid_action_item_rows",
            warning=parse_error,
        )
    if not action_item_rows:
        return _blocked_event_report(
            context=context,
            args=args,
            bundle=bundle,
            reason="packet_semantic_ingestion_requires_action_item_rows",
            warning="review-channel ingest requires explicit --semantic-action-item rows",
        )
    packets = filter_history_packets(
        bundle.review_state,
        packet_id=packet_id,
        limit=1,
    )
    if len(packets) != 1:
        return _blocked_event_report(
            context=context,
            args=args,
            bundle=bundle,
            reason="packet_semantic_ingestion_packet_not_found",
            warning=f"review-channel ingest could not resolve packet {packet_id}",
        )
    gate = _review_channel_lifecycle_gate(
        args=args,
        context=context,
        packet_id=packet_id,
    )
    if not gate["ok"]:
        return _blocked_obedience_event_report(
            context=context,
            args=args,
            bundle=bundle,
            packet=packets[0],
            packets=packets,
            gate=gate,
        )
    bundle, event = record_packet_semantic_ingestion(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        artifact_paths=context.artifact_paths,
        bundle=bundle,
        packet=packets[0],
        actor=actor,
        role=str(getattr(args, "target_role", "") or ""),
        session_id=str(getattr(args, "target_session_id", "") or ""),
        action_item_rows=action_item_rows,
    )
    if event is None:
        return _blocked_event_report(
            context=context,
            args=args,
            bundle=bundle,
            packet=packets[0],
            packets=packets,
            reason="matching_packet_body_observation_required",
            warning=(
                "review-channel ingest requires matching packet body observation "
                "by actor/role/session"
            ),
        )
    packets = filter_history_packets(
        bundle.review_state,
        packet_id=packet_id,
        limit=1,
    )
    report, exit_code = context.build_event_report_fn(
        args=args,
        bundle=bundle,
        packet=packets[0] if len(packets) == 1 else None,
        packets=packets,
        event=event,
    )
    report["control_decision_obedience"] = gate
    return report, exit_code


def _run_packet_absorb_action(
    *,
    args,
    context: EventActionContext,
    bundle,
) -> tuple[dict, int]:
    packet_id = str(getattr(args, "packet_id", "") or "").strip()
    actor = str(getattr(args, "actor", "") or "").strip()
    role = str(
        getattr(args, "target_role", "") or getattr(args, "role", "") or ""
    ).strip()
    session_id = str(
        getattr(args, "target_session_id", "")
        or getattr(args, "session_id", "")
        or ""
    ).strip()
    if not packet_id:
        return _blocked_event_report(
            context=context,
            args=args,
            bundle=bundle,
            reason="packet_absorption_requires_packet_id",
            warning="review-channel absorb requires --packet-id",
        )
    if not actor:
        return _blocked_event_report(
            context=context,
            args=args,
            bundle=bundle,
            reason="packet_absorption_requires_actor",
            warning="review-channel absorb requires --actor",
        )
    if not (role and session_id):
        return _blocked_event_report(
            context=context,
            args=args,
            bundle=bundle,
            reason="packet_absorption_requires_actor_role_session_scope",
            warning=(
                "review-channel absorb requires --target-role and "
                "--target-session-id so the receipt matches semantic ingestion"
            ),
        )
    packets = filter_history_packets(
        bundle.review_state,
        packet_id=packet_id,
        limit=1,
    )
    if len(packets) != 1:
        return _blocked_event_report(
            context=context,
            args=args,
            bundle=bundle,
            reason="packet_absorption_packet_not_found",
            warning=f"review-channel absorb could not resolve packet {packet_id}",
        )
    gate = _review_channel_lifecycle_gate(
        args=args,
        context=context,
        packet_id=packet_id,
    )
    if not gate["ok"]:
        return _blocked_obedience_event_report(
            context=context,
            args=args,
            bundle=bundle,
            packet=packets[0],
            packets=packets,
            gate=gate,
        )
    bundle, event = record_packet_absorption(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        artifact_paths=context.artifact_paths,
        bundle=bundle,
        packet=packets[0],
        actor=actor,
        role=role,
        session_id=session_id,
    )
    if event is None:
        return _blocked_event_report(
            context=context,
            args=args,
            bundle=bundle,
            packet=packets[0],
            packets=packets,
            reason="matching_packet_semantic_ingestion_required",
            warning=(
                "review-channel absorb requires matching semantic ingestion "
                "by actor/role/session"
            ),
        )
    packets = filter_history_packets(
        bundle.review_state,
        packet_id=packet_id,
        limit=1,
    )
    report, exit_code = context.build_event_report_fn(
        args=args,
        bundle=bundle,
        packet=packets[0] if len(packets) == 1 else None,
        packets=packets,
        event=event,
    )
    report["control_decision_obedience"] = gate
    return report, exit_code


def _review_channel_lifecycle_gate(
    *,
    args,
    context: EventActionContext,
    packet_id: str = "",
) -> dict[str, object]:
    """Run the controller-decision obedience gate before event-store writes."""
    decision_args = _control_decision_args(args)
    decision = load_control_decision_payload(
        decision_args,
        repo_root=context.repo_root,
    )
    subject_actor = _action_actor(args)
    subject_role = _action_role(args)
    subject_session_id = _action_session_id(args)
    executor_actor = _executor_actor(args, fallback_actor=subject_actor)
    executor_role = _executor_role(
        args,
        fallback_role=subject_role,
        executor_actor=executor_actor,
        subject_actor=subject_actor,
    )
    executor_session_id = _executor_session_id(
        args,
        fallback_session_id=subject_session_id,
        executor_actor=executor_actor,
        subject_actor=subject_actor,
    )
    source_decision_id = coerce_string(decision.get("receipt_id"))
    source_snapshot_id = coerce_string(decision.get("source_snapshot_id"))
    source_latest_event_id = coerce_string(decision.get("source_latest_event_id"))
    proxy_authority_ref = _proxy_authority_ref(
        args,
        route=ProxyAuthorityRoute(
            executor_actor=executor_actor,
            executor_role=executor_role,
            executor_session_id=executor_session_id,
            subject_actor=subject_actor,
            subject_role=subject_role,
            subject_session_id=subject_session_id,
        ),
        source=ProxyAuthoritySource(
            decision_id=source_decision_id,
            snapshot_id=source_snapshot_id,
            latest_event_id=source_latest_event_id,
        ),
    )
    attempted = build_attempted_action_receipt(
        action_kind=f"review-channel.{getattr(args, 'action', '')}",
        command=_review_channel_attempted_command(args, packet_id=packet_id),
        argv=_review_channel_attempted_argv(args, packet_id=packet_id),
        actor=subject_actor,
        role=subject_role,
        session_id=subject_session_id,
        executor_actor=executor_actor,
        executor_role=executor_role,
        executor_session_id=executor_session_id,
        subject_actor=subject_actor,
        subject_role=subject_role,
        subject_session_id=subject_session_id,
        proxy_authority_ref=proxy_authority_ref,
        mutates=True,
        writes_state=True,
        executes_command=True,
        source_decision_id=source_decision_id,
        source_snapshot_id=source_snapshot_id,
        source_latest_event_id=source_latest_event_id,
        started_at_utc=utc_timestamp(),
    ).to_dict()
    # v4.43.1 (rev_pkt_4716): populate ``observed_event_id`` from canonical
    # review-channel state so the stale-decision blocker can compare the
    # decision source against fresh observation rather than against the
    # action's source-decision provenance (which is the same as decision).
    observed_event_id = _latest_observed_event_id(context)
    if observed_event_id:
        attempted["observed_event_id"] = observed_event_id
    if _operator_post_authority(args):
        return {
            "ok": True,
            "contract_id": "ControlDecisionObeyedGuard",
            "operator_source_authority": True,
            "authority_ordering": "operator_source_before_control_decision_obedience",
            "attempted_action_receipt": attempted,
        }
    if _orchestrator_post_authority(args):
        return {
            "ok": True,
            "contract_id": "ControlDecisionObeyedGuard",
            "orchestrator_source_authority": True,
            "authority_ordering": "orchestrator_source_before_control_decision_obedience",
            "attempted_action_receipt": attempted,
        }
    if _cascade_lifecycle_read_authority(args):
        return {
            "ok": True,
            "contract_id": "ControlDecisionObeyedGuard",
            "cascade_lifecycle_read_authority": True,
            "authority_ordering": "cascade_lifecycle_read_before_control_decision_obedience",
            "attempted_action_receipt": attempted,
        }
    if _cascade_lifecycle_post_authority(args, repo_root=context.repo_root):
        return {
            "ok": True,
            "contract_id": "ControlDecisionObeyedGuard",
            "cascade_lifecycle_post_authority": True,
            "authority_ordering": "cascade_lifecycle_post_before_control_decision_obedience",
            "attempted_action_receipt": attempted,
        }
    if not decision and _allow_missing_control_decision_for_test(
        args=args,
        repo_root=context.repo_root,
    ):
        return {
            "ok": True,
            "contract_id": "ControlDecisionObeyedGuard",
            "diagnostic_bypass": "allow_missing_control_decision_for_test",
            "attempted_action_receipt": attempted,
        }
    report = evaluate_control_decision_obedience(
        decision=decision or None,
        attempted_actions=(attempted,),
    ).to_dict()
    report["attempted_action_receipt"] = attempted
    report["command"] = "review-channel.control_decision_obedience"
    return report


def _latest_observed_event_id(context) -> str:
    """v4.43.2 (rev_pkt_4717): read the canonical observed event id from
    typed review-channel reduced state.

    Delegates to ``source_latest_event_id_from_reduced_state`` which walks
    the typed extraction order (AgentRuntimeClock → typed_snapshot_freshness
    → agent_sync → reviewer_runtime → top-level). The reduced state is read
    from ``context.artifact_paths.state_path`` — the canonical projection
    JSON written by ``refresh_event_bundle``.

    v4.43.1 used a direct trace.ndjson tail reader (which codex correctly
    flagged as a parallel cursor selector bypassing typed reducer state).
    v4.43.2 routes through the shared canonical extractor instead — the
    obedience guard's stale-decision detector sees the same event id that
    AgentRuntimeClock / agent_sync / reviewer_runtime consumers see.

    Returns ``""`` on any failure (missing artifact_paths, missing file,
    parse error, no typed event cursor yet) — the stale detector treats
    a missing ``observed_event_id`` as "no fresh observation supplied"
    and falls back to comparing against the action's ``source_latest_event_id``.
    """
    artifact_paths = getattr(context, "artifact_paths", None)
    if artifact_paths is None:
        return ""
    state_path = getattr(artifact_paths, "state_path", "")
    if not state_path:
        return ""
    try:
        from pathlib import Path  # noqa: PLC0415
        path = Path(state_path)
        if not path.exists():
            return ""
        import json  # noqa: PLC0415
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return ""
        if not isinstance(payload, dict):
            return ""
        # v4.43.2: reuse the canonical extractor so the observation cursor
        # is the same one AgentRuntimeClock / agent_sync / reviewer_runtime
        # consumers see — no parallel cursor selector.
        from ...runtime.control_decision_artifacts import (  # noqa: PLC0415
            source_latest_event_id_from_reduced_state,
        )
        return source_latest_event_id_from_reduced_state(payload)
    except OSError:
        return ""


def _operator_post_authority(args) -> bool:
    """Operator-authored packet posts outrank stale controller wait state."""
    return (
        coerce_string(getattr(args, "action", "")).strip() == "post"
        and coerce_string(getattr(args, "from_agent", "")).strip() == "operator"
    )


_ORCHESTRATOR_AUTHORIZED_POST_KINDS: frozenset[str] = frozenset(
    {"task_started", "finding"}
)


_CASCADE_LIFECYCLE_AUTHORIZED_POSTS: frozenset[tuple[str, str]] = frozenset(
    {
        ("claude", "task_produced"),
        ("claude", "task_blocked"),
        ("claude", "task_progress"),
        ("codex", "review_accepted"),
        ("codex", "review_failed"),
        ("codex", "task_blocked"),
        ("codex", "task_progress"),
    }
)


_CASCADE_PEER_REVERSAL: frozenset[tuple[str, str]] = frozenset(
    {
        ("claude", "codex"),
        ("codex", "claude"),
    }
)


_CASCADE_PARENT_PACKET_RE = re.compile(r"^packet:rev_pkt_\d+$")


_CASCADE_AGENT_ROLES: dict[str, str] = {
    "claude": "implementer",
    "codex": "reviewer",
}


_CASCADE_PARENT_STALE_STATUSES: frozenset[str] = frozenset(
    {"expired", "dismissed", "applied", "rejected"}
)


_CASCADE_CLOSURE_PARENT_KINDS: dict[str, frozenset[str]] = {
    "task_produced": frozenset({"task_started", "review_failed", "task_progress"}),
    "task_progress": frozenset(
        {"task_started", "task_produced", "task_progress", "task_blocked", "review_failed"}
    ),
    "task_blocked": frozenset(
        {"task_started", "task_produced", "task_progress", "review_failed"}
    ),
    "review_accepted": frozenset({"task_produced"}),
    "review_failed": frozenset({"task_produced", "task_progress"}),
}


_CASCADE_LIFECYCLE_READ_ACTIONS: frozenset[str] = frozenset(
    {"show", "inbox", "operator-inbox", "status", "history", "sync-status"}
)


_CASCADE_LIVE_AGENT_PEERS: frozenset[str] = frozenset({"claude", "codex"})


_CASCADE_FALLBACK_SESSION_IDS: frozenset[str] = frozenset({"", "local-review"})


def _resolve_cascade_live_session_id(
    agent_provider: str,
    repo_root: Path,
) -> str:
    """Read the current live session_id for a live agent from typed agent_minds projection.

    Phase 0.6.D v4.14 (rev_pkt_4668): re-uses the existing AgentMindSlice projection
    at ``dev/reports/agent_minds/<agent>_latest.json`` rather than introducing a
    parallel session registry. Returns empty string when the projection is absent.
    """
    if agent_provider not in _CASCADE_LIVE_AGENT_PEERS:
        return ""
    path = repo_root / "dev/reports/agent_minds" / f"{agent_provider}_latest.json"
    if not path.is_file():
        return ""
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return ""
    if not isinstance(data, dict):
        return ""
    return str(data.get("session_id") or "").strip()


def _cascade_lifecycle_read_authority(args) -> bool:
    """Read-action bypass for show/inbox/status: reads cannot mutate state.

    ControlDecisionObeyedGuard is a write-side authority gate. Read actions cannot
    mutate the event log or projections, so blocking them on stale-decision state
    would starve reviewers of the visibility they need to write valid closures
    (rev_pkt_4659 noted ``--action show rev_pkt_4655`` being blocked after a
    sibling finding posted).
    """
    action = coerce_string(getattr(args, "action", "")).strip()
    return action in _CASCADE_LIFECYCLE_READ_ACTIONS


def _resolve_cascade_parent_packet(
    parent_packet_id: str,
    repo_root: Path,
) -> dict[str, object] | None:
    """Lookup a parent packet by id from the event-log replay.

    Returns the packet dict (post-event hydration) or None if not found.
    """
    try:
        from ...review_channel.pending_packet_storage import load_pending_packets

        packets = load_pending_packets(repo_root, fail_closed=False)
    except Exception:  # pragma: no cover - storage layer fail-open
        return None
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        if str(packet.get("packet_id") or "").strip() == parent_packet_id:
            return dict(packet)
    return None


def _cascade_lifecycle_post_authority(
    args,
    *,
    repo_root: Path | None = None,
    parent_resolver: object = None,
) -> bool:
    """Bilateral cascade-closure post authority for task_started -> task_produced -> review_accepted.

    Companion to _orchestrator_post_authority. Where the orchestrator authority lets codex
    initiate work (task_started/finding) without first running ``develop next``, this rule
    permits the matching closure-direction posts so claude can return task_produced and
    codex can post review_accepted/review_failed without being gated by the most recent
    AgentLoopDecision's wait/may_mutate/body_open state.

    Phase 0.6.A structural narrow (rev_pkt_4657):
      - Only ``review-channel --action post``
      - Only (from_agent, kind) pairs in ``_CASCADE_LIFECYCLE_AUTHORIZED_POSTS``
      - (from_agent, to_agent) must be claude<->codex reversal
      - --target-session-id and --target-role must be non-empty
      - At least one --evidence-ref must match ``packet:rev_pkt_<digits>``

    v4.22 explicit primary parent resolution (rev_pkt_4681):
      - If ``--parent-packet-id`` is set, it must match a packet:rev_pkt_<id>
        evidence_ref (or evidence_refs may be empty) and that id is the parent.
      - If ``--parent-packet-id`` is empty and exactly one packet:rev_pkt_<id>
        evidence_ref is present, that ref is the parent (backwards compat).
      - If ``--parent-packet-id`` is empty and MULTIPLE packet:rev_pkt_<id>
        evidence_refs are present, the predicate fails closed - evidence
        order MUST NOT silently choose lifecycle parentage.

    Phase 0.6.B semantic cross-reference against parent task_started (rev_pkt_4659):
      - Parent packet must resolve via ``parent_resolver`` / ``load_pending_packets``
      - parent.kind == "task_started" (unrelated-parent-kind rejected)
      - parent.status not in {expired, dismissed, applied, rejected} (stale rejected)
      - closure.from_agent == parent.to_agent AND closure.to_agent == parent.from_agent
        (wrong-peer rejected via authoritative cross-ref vs structural reversal)
      - closure.target_session_id == parent.session_id (wrong-session rejected)
      - closure.target_role == _CASCADE_AGENT_ROLES[parent.from_agent] (wrong-role rejected)
      - When both non-empty: closure.target_ref == parent.target_ref (target-ref mismatch
        rejected)

    Fail-closed: if no ``repo_root`` and no ``parent_resolver`` are provided, returns False.
    Production callers pass ``repo_root=context.repo_root``; unit tests inject
    ``parent_resolver`` for deterministic verification without event-log fixtures.
    """
    if coerce_string(getattr(args, "action", "")).strip() != "post":
        return False
    from_agent = coerce_string(getattr(args, "from_agent", "")).strip()
    to_agent = coerce_string(getattr(args, "to_agent", "")).strip()
    kind = coerce_string(getattr(args, "kind", "")).strip()
    if (from_agent, kind) not in _CASCADE_LIFECYCLE_AUTHORIZED_POSTS:
        return False
    if (from_agent, to_agent) not in _CASCADE_PEER_REVERSAL:
        return False
    target_session_id = coerce_string(getattr(args, "target_session_id", "")).strip()
    if not target_session_id:
        return False
    target_role = coerce_string(getattr(args, "target_role", "")).strip()
    if not target_role:
        return False
    evidence_refs = getattr(args, "evidence_ref", None) or ()
    matching_packet_ids: list[str] = []
    for ref in evidence_refs:
        ref_str = coerce_string(ref).strip()
        if _CASCADE_PARENT_PACKET_RE.match(ref_str):
            matching_packet_ids.append(ref_str.split(":", 1)[1])
    explicit_parent_id = coerce_string(
        getattr(args, "parent_packet_id", "")
    ).strip()
    if explicit_parent_id:
        if explicit_parent_id not in matching_packet_ids:
            return False
        parent_packet_id = explicit_parent_id
    elif len(matching_packet_ids) == 1:
        parent_packet_id = matching_packet_ids[0]
    elif len(matching_packet_ids) > 1:
        return False
    else:
        parent_packet_id = ""
    if not parent_packet_id:
        return False
    resolver = parent_resolver
    if resolver is None:
        if repo_root is None:
            return False
        resolver = lambda pid: _resolve_cascade_parent_packet(pid, repo_root)
    try:
        parent = resolver(parent_packet_id)
    except Exception:  # pragma: no cover - resolver fail-closed
        return False
    if parent is None or not isinstance(parent, dict):
        return False
    parent_kind = str(parent.get("kind") or "").strip()
    expected_parent_kinds = _CASCADE_CLOSURE_PARENT_KINDS.get(kind, frozenset())
    if parent_kind not in expected_parent_kinds:
        return False
    parent_status = str(parent.get("status") or "").strip()
    if parent_status in _CASCADE_PARENT_STALE_STATUSES:
        return False
    parent_from = str(parent.get("from_agent") or "").strip()
    parent_to = str(parent.get("to_agent") or "").strip()
    if from_agent != parent_to or to_agent != parent_from:
        return False
    parent_session_id = str(parent.get("session_id") or "").strip()
    if (
        parent_from in _CASCADE_LIVE_AGENT_PEERS
        or parent_to in _CASCADE_LIVE_AGENT_PEERS
    ) and parent_session_id in _CASCADE_FALLBACK_SESSION_IDS:
        return False
    if target_session_id != parent_session_id:
        return False
    if target_session_id in _CASCADE_FALLBACK_SESSION_IDS:
        return False
    if repo_root is not None and parent_from in _CASCADE_LIVE_AGENT_PEERS:
        live_session_id = _resolve_cascade_live_session_id(parent_from, repo_root)
        if not live_session_id:
            return False
        if live_session_id != parent_session_id:
            return False
    expected_target_role = _CASCADE_AGENT_ROLES.get(parent_from, "")
    if expected_target_role and target_role != expected_target_role:
        return False
    target_ref = coerce_string(getattr(args, "target_ref", "")).strip()
    parent_target_ref = str(parent.get("target_ref") or "").strip()
    if target_ref and parent_target_ref and target_ref != parent_target_ref:
        return False
    return True


def _orchestrator_post_authority(args) -> bool:
    """Codex orchestrator (TandemRole.REVIEWER) may post task_started/finding directly.

    Role-flip narrow exemption: codex as CognitiveRole.ORCHESTRATOR + TandemRole.REVIEWER
    issues task_started directives and finding evidence packets without first chaining
    through ``develop next`` for an AgentLoopDecision. Until CognitiveRoleFleetAssignment
    lands, accept codex-source by typed actor identity.

    Strict scope: only ``review-channel --action post`` + only ``--kind`` in
    {task_started, finding}. Does NOT bypass VCS/edit/raw-git/commit/push gates or
    any other lifecycle mutation. Operator-source authority remains unchanged.
    """
    if coerce_string(getattr(args, "action", "")).strip() != "post":
        return False
    if (
        coerce_string(getattr(args, "kind", "")).strip()
        not in _ORCHESTRATOR_AUTHORIZED_POST_KINDS
    ):
        return False
    return (
        coerce_string(getattr(args, "from_agent", "")).strip() == "codex"
    )


def _control_decision_args(args) -> SimpleNamespace:
    values = dict(vars(args)) if hasattr(args, "__dict__") else {}
    values["actor"] = _action_actor(args)
    values["role"] = _action_role(args)
    values["session_id"] = _action_session_id(args)
    return SimpleNamespace(**values)


def _allow_missing_control_decision_for_test(*, args, repo_root: Path) -> bool:
    return bool(getattr(args, "allow_missing_control_decision_for_test", False))


def _semantic_action_item_rows_from_args(args) -> tuple[list[dict[str, object]], str]:
    rows: list[dict[str, object]] = []
    for raw in getattr(args, "semantic_action_item", []) or []:
        try:
            parsed = json.loads(str(raw))
        except json.JSONDecodeError as exc:
            return [], f"invalid --semantic-action-item JSON: {exc}"
        if not isinstance(parsed, dict):
            return [], "--semantic-action-item must be a JSON object"
        rows.append(parsed)
    return rows, ""


def _blocked_event_report(
    *,
    context: EventActionContext,
    args,
    bundle,
    reason: str,
    warning: str,
    packet: dict[str, object] | None = None,
    packets: list[dict[str, object]] | None = None,
) -> tuple[dict, int]:
    report, _exit_code = context.build_event_report_fn(
        args=args,
        bundle=bundle,
        packet=packet,
        packets=packets,
        warnings=[warning],
    )
    report["ok"] = False
    report["exit_ok"] = False
    report["exit_code"] = 1
    report["status"] = "blocked"
    report.setdefault("errors", []).append(reason)
    return report, 1


def _blocked_obedience_event_report(
    *,
    context: EventActionContext,
    args,
    bundle,
    gate: dict[str, object],
    packet: dict[str, object] | None = None,
    packets: list[dict[str, object]] | None = None,
) -> tuple[dict, int]:
    report, exit_code = _blocked_event_report(
        context=context,
        args=args,
        bundle=bundle,
        packet=packet,
        packets=packets,
        reason="control_decision_obedience_failed",
        warning="review-channel lifecycle mutation blocked by ControlDecisionObeyedGuard",
    )
    del exit_code
    report["control_decision_obedience"] = gate
    return report, 1


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
