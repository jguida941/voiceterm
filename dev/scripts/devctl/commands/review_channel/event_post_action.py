"""Post action for the event-backed review-channel command path."""

from __future__ import annotations

from pathlib import Path

from ...review_channel.context_refs import resolve_context_pack_refs
from ...review_channel.events import post_packet
from ...review_channel.packet_contract import (
    PacketGuardBundleEvidenceFields,
    PacketPostRequest,
    PacketRuntimeApprovalFields,
    PacketTargetFields,
)
from .event_action_support import EventActionContext
from .event_packet_lookup import packet_by_id


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
) -> tuple[dict, int, dict[str, object]]:
    """Append one event-backed review packet."""
    bundle, event = post_packet(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        artifact_paths=context.artifact_paths,
        request=_post_request(context),
    )
    packet = packet_by_id(bundle.review_state, event.get("packet_id"))
    report, exit_code = context.build_event_report_fn(
        args=context.args,
        bundle=bundle,
        packet=packet,
        event=event,
    )
    return report, exit_code, bundle.review_state


def _post_request(context: EventActionContext) -> PacketPostRequest:
    args = context.args
    return PacketPostRequest(
        from_agent=args.from_agent,
        to_agent=args.to_agent,
        kind=args.kind,
        summary=args.summary,
        body=load_post_body(args),
        evidence_refs=tuple(args.evidence_ref or []),
        context_pack_refs=tuple(resolve_context_pack_refs(args, context.repo_root)),
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
        target=_target_fields(args),
        runtime_approval=_runtime_approval_fields(args),
        guard_bundle_evidence=_guard_bundle_evidence_fields(args),
    )


def _target_fields(args) -> PacketTargetFields:
    return PacketTargetFields.from_values(
        target_kind=getattr(args, "target_kind", None),
        target_ref=getattr(args, "target_ref", None),
        target_revision=getattr(args, "target_revision", None),
        anchor_refs=getattr(args, "anchor_ref", []),
        intake_ref=getattr(args, "intake_ref", None),
        mutation_op=getattr(args, "mutation_op", None),
        target_role=getattr(args, "target_role", None),
        target_session_id=getattr(args, "target_session_id", None),
        requested_session_visibility=getattr(
            args,
            "requested_session_visibility",
            None,
        ),
    )


def _runtime_approval_fields(args) -> PacketRuntimeApprovalFields:
    return PacketRuntimeApprovalFields.from_values(
        pipeline_generation=getattr(args, "pipeline_generation", None),
        staged_snapshot_hash=getattr(args, "staged_snapshot_hash", None),
        guard_results_summary=getattr(args, "guard_results_summary", None),
    )


def _guard_bundle_evidence_fields(args) -> PacketGuardBundleEvidenceFields:
    return PacketGuardBundleEvidenceFields.from_values(
        full_guard_bundle_evidence=getattr(
            args,
            "full_guard_bundle_evidence",
            None,
        ),
    )
