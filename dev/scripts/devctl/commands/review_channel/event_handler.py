"""Event-backed action rendering and execution for `devctl review-channel`.

Handles post, watch, inbox, operator-inbox, ack, dismiss, apply, and history actions that
operate against the structured event store. Extracted from
commands/review_channel.py to keep the command orchestrator under the
file-size soft limit.
"""

from __future__ import annotations

import os
from pathlib import Path
import json
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
        control_decision_gate = None
        actor = str(getattr(args, "actor", "") or "").strip()
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
                    packet=packets[0],
                    packets=packets,
                    gate=gate,
                )
            control_decision_gate = gate
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
        report, exit_code = _build_event_report(
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
        executor_actor=executor_actor,
        executor_role=executor_role,
        executor_session_id=executor_session_id,
        subject_actor=subject_actor,
        subject_role=subject_role,
        subject_session_id=subject_session_id,
        source_decision_id=source_decision_id,
        source_snapshot_id=source_snapshot_id,
        source_latest_event_id=source_latest_event_id,
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
    if _operator_post_authority(args):
        return {
            "ok": True,
            "contract_id": "ControlDecisionObeyedGuard",
            "operator_source_authority": True,
            "authority_ordering": "operator_source_before_control_decision_obedience",
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


def _operator_post_authority(args) -> bool:
    """Operator-authored packet posts outrank stale controller wait state."""
    return (
        coerce_string(getattr(args, "action", "")).strip() == "post"
        and coerce_string(getattr(args, "from_agent", "")).strip() == "operator"
    )


def _control_decision_args(args) -> SimpleNamespace:
    values = dict(vars(args)) if hasattr(args, "__dict__") else {}
    values["actor"] = _action_actor(args)
    values["role"] = _action_role(args)
    values["session_id"] = _action_session_id(args)
    return SimpleNamespace(**values)


def _action_actor(args) -> str:
    return coerce_string(
        getattr(args, "actor", "")
        or getattr(args, "from_agent", "")
        or getattr(args, "to_agent", "")
    ).strip()


def _action_role(args) -> str:
    actor_role = coerce_string(getattr(args, "actor_role", "")).strip()
    if actor_role:
        return actor_role
    if coerce_string(getattr(args, "action", "")).strip() == "post":
        return coerce_string(getattr(args, "role", "")).strip()
    return coerce_string(
        getattr(args, "role", "") or getattr(args, "target_role", "")
    ).strip()


def _action_session_id(args) -> str:
    if coerce_string(getattr(args, "action", "")).strip() == "post":
        return coerce_string(getattr(args, "session_id", "")).strip()
    return coerce_string(
        getattr(args, "target_session_id", "") or getattr(args, "session_id", "")
    ).strip()


def _executor_actor(args, *, fallback_actor: str) -> str:
    explicit = coerce_string(getattr(args, "executor_actor", "")).strip()
    if explicit:
        return explicit
    env_actor = coerce_string(os.environ.get("DEVCTL_EXECUTOR_ACTOR")).strip()
    if env_actor:
        return env_actor
    if coerce_string(os.environ.get("CODEX_THREAD_ID")).strip():
        return "codex"
    return fallback_actor


def _executor_role(
    args,
    *,
    fallback_role: str,
    executor_actor: str,
    subject_actor: str,
) -> str:
    explicit = coerce_string(getattr(args, "executor_role", "")).strip()
    if explicit:
        return explicit
    env_role = coerce_string(os.environ.get("DEVCTL_EXECUTOR_ROLE")).strip()
    if env_role:
        return env_role
    return fallback_role if executor_actor == subject_actor else ""


def _executor_session_id(
    args,
    *,
    fallback_session_id: str,
    executor_actor: str,
    subject_actor: str,
) -> str:
    explicit = coerce_string(getattr(args, "executor_session_id", "")).strip()
    if explicit:
        return explicit
    env_session = coerce_string(os.environ.get("DEVCTL_EXECUTOR_SESSION_ID")).strip()
    if env_session:
        return env_session
    if executor_actor != subject_actor:
        return coerce_string(os.environ.get("CODEX_THREAD_ID")).strip()
    return fallback_session_id


def _proxy_authority_ref(
    args,
    *,
    executor_actor: str,
    executor_role: str,
    executor_session_id: str,
    subject_actor: str,
    subject_role: str,
    subject_session_id: str,
    source_decision_id: str,
    source_snapshot_id: str,
    source_latest_event_id: str,
) -> str:
    explicit = coerce_string(getattr(args, "proxy_authority_ref", "")).strip()
    if explicit:
        return explicit
    if not _is_proxy_execution(
        executor_actor=executor_actor,
        executor_role=executor_role,
        executor_session_id=executor_session_id,
        subject_actor=subject_actor,
        subject_role=subject_role,
        subject_session_id=subject_session_id,
    ):
        return ""
    return source_decision_id or source_snapshot_id or source_latest_event_id


def _is_proxy_execution(
    *,
    executor_actor: str,
    executor_role: str,
    executor_session_id: str,
    subject_actor: str,
    subject_role: str,
    subject_session_id: str,
) -> bool:
    if not executor_actor or not subject_actor:
        return False
    if executor_actor != subject_actor:
        return True
    if executor_role and subject_role and executor_role != subject_role:
        return True
    if executor_session_id and subject_session_id and executor_session_id != subject_session_id:
        return True
    return False


def _review_channel_attempted_argv(args, *, packet_id: str = "") -> tuple[str, ...]:
    argv = ["review-channel", "--action", coerce_string(getattr(args, "action", ""))]
    packet_kind = coerce_string(getattr(args, "kind", "")).strip()
    if packet_kind:
        argv.extend(("--kind", packet_kind))
    if packet_id:
        argv.extend(("--packet-id", packet_id))
    for option, attr in (
        ("--requested-action", "requested_action"),
        ("--target-kind", "target_kind"),
        ("--target-ref", "target_ref"),
        ("--target-revision", "target_revision"),
        ("--full-guard-bundle-evidence", "full_guard_bundle_evidence"),
    ):
        value = coerce_string(getattr(args, attr, "")).strip()
        if value:
            argv.extend((option, value))
    actor = _action_actor(args)
    if actor:
        argv.extend(("--actor", actor))
    actor_role = coerce_string(getattr(args, "actor_role", "")).strip()
    if actor_role:
        argv.extend(("--actor-role", actor_role))
    session_id = coerce_string(getattr(args, "session_id", "")).strip()
    if session_id:
        argv.extend(("--session-id", session_id))
    return tuple(item for item in argv if item)


def _review_channel_attempted_command(args, *, packet_id: str = "") -> str:
    return " ".join(("python3", "dev/scripts/devctl.py", *_review_channel_attempted_argv(args, packet_id=packet_id)))


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
