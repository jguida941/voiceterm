"""Helper actions for the event-backed review-channel command path."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...review_channel.context_refs import resolve_context_pack_refs
from ...review_channel.events import post_packet, transition_packet
from ...review_channel.packet_contract import (
    PacketPostRequest,
    PacketRuntimeApprovalFields,
    PacketTargetFields,
    PacketTransitionRequest,
)
from .event_watch_support import EventWatchContext, load_target_packets


@dataclass(frozen=True)
class EventActionContext:
    args: object
    repo_root: Path
    review_channel_path: Path
    artifact_paths: object
    build_event_report_fn: object


def load_post_body(args) -> str:
    """Read the packet body from --body or --body-file."""
    body = getattr(args, "body", None)
    body_file = getattr(args, "body_file", None)
    if body:
        return str(body)
    assert body_file is not None
    return Path(body_file).read_text(encoding="utf-8")


def run_post_action(
    *,
    context: EventActionContext,
) -> tuple[dict, int]:
    """Append one event-backed review packet."""
    bundle, event = post_packet(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        artifact_paths=context.artifact_paths,
        request=PacketPostRequest(
            from_agent=context.args.from_agent,
            to_agent=context.args.to_agent,
            kind=context.args.kind,
            summary=context.args.summary,
            body=load_post_body(context.args),
            evidence_refs=tuple(context.args.evidence_ref or []),
            context_pack_refs=tuple(
                resolve_context_pack_refs(context.args, context.repo_root)
            ),
            confidence=float(context.args.confidence),
            requested_action=context.args.requested_action,
            policy_hint=context.args.policy_hint,
            approval_required=bool(context.args.approval_required),
            packet_id=getattr(context.args, "packet_id", None),
            trace_id=getattr(context.args, "trace_id", None),
            session_id=context.args.session_id,
            plan_id=context.args.plan_id,
            controller_run_id=getattr(context.args, "controller_run_id", None),
            expires_in_minutes=context.args.expires_in_minutes,
            target=PacketTargetFields.from_values(
                target_kind=getattr(context.args, "target_kind", None),
                target_ref=getattr(context.args, "target_ref", None),
                target_revision=getattr(context.args, "target_revision", None),
                anchor_refs=getattr(context.args, "anchor_ref", []),
                intake_ref=getattr(context.args, "intake_ref", None),
                mutation_op=getattr(context.args, "mutation_op", None),
            ),
            runtime_approval=PacketRuntimeApprovalFields.from_values(
                pipeline_generation=getattr(context.args, "pipeline_generation", None),
                staged_snapshot_hash=getattr(context.args, "staged_snapshot_hash", None),
                guard_results_summary=getattr(context.args, "guard_results_summary", None),
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
    return context.build_event_report_fn(
        args=context.args,
        bundle=bundle,
        packet=packet,
        event=event,
    )


def run_packet_transition_action(
    *,
    context: EventActionContext,
) -> tuple[dict, int]:
    """Apply one ack/dismiss/apply transition to an existing packet."""
    bundle, event = transition_packet(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        artifact_paths=context.artifact_paths,
        request=PacketTransitionRequest(
            action=context.args.action,
            packet_id=context.args.packet_id,
            actor=context.args.actor,
            session_id=context.args.session_id,
            plan_id=context.args.plan_id,
            controller_run_id=getattr(context.args, "controller_run_id", None),
        ),
    )
    packet = next(
        (
            packet_row
            for packet_row in bundle.review_state.get("packets", [])
            if isinstance(packet_row, dict)
            and packet_row.get("packet_id") == context.args.packet_id
        ),
        None,
    )
    return context.build_event_report_fn(
        args=context.args,
        bundle=bundle,
        packet=packet,
        event=event,
    )


def run_inbox_like_action(
    *,
    context: EventActionContext,
    bundle,
    target_override: str | None = None,
    status_override: str | None = None,
    observe_action_requests: bool = True,
) -> tuple[dict, int]:
    """Run one inbox-like event query with optional target/status overrides."""
    if target_override is not None:
        context.args.target = target_override
    if status_override is not None and not getattr(context.args, "status", None):
        context.args.status = status_override
    bundle, packets = load_target_packets(
        context=EventWatchContext(
            args=context.args,
            bundle=bundle,
            repo_root=context.repo_root,
            review_channel_path=context.review_channel_path,
            artifact_paths=context.artifact_paths,
        ),
        observe_action_requests=observe_action_requests,
    )
    return context.build_event_report_fn(
        args=context.args,
        bundle=bundle,
        packets=packets,
    )
