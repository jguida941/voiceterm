"""Packet transition action for the event-backed review-channel command path."""

from __future__ import annotations

from ...review_channel.events import transition_packet
from ...review_channel.packet_attestation import PacketGuardAttestation
from ...review_channel.packet_contract import PacketTransitionRequest
from .event_action_support import EventActionContext
from .event_packet_lookup import packet_by_id


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
            guard_attestation=_guard_attestation_from_args(context.args),
        ),
    )
    packet = packet_by_id(bundle.review_state, context.args.packet_id)
    return context.build_event_report_fn(
        args=context.args,
        bundle=bundle,
        packet=packet,
        event=event,
    )


def _guard_attestation_from_args(args) -> PacketGuardAttestation | None:
    if getattr(args, "action", "") != "apply":
        return None
    fields = _attestation_fields(args)
    if not _has_attestation_evidence(args, fields):
        return None
    return PacketGuardAttestation(
        packet_id=str(getattr(args, "packet_id", "") or "").strip(),
        attestation_kind=fields["attestation_kind"] or "manual_apply",
        run_record_ids=tuple(getattr(args, "run_record_id", []) or []),
        action_result_ids=tuple(getattr(args, "action_result_id", []) or []),
        commit_sha=fields["commit_sha"],
        plan_revision_before=fields["plan_revision_before"],
        plan_revision_after=fields["plan_revision_after"],
        evidence_artifact_paths=tuple(
            getattr(args, "evidence_artifact_path", []) or []
        ),
        attested_at_utc="",
        attested_by=str(getattr(args, "actor", "") or "").strip(),
        operator_signature=fields["operator_signature"],
        pipeline_generation=fields["pipeline_generation"],
        staged_snapshot_hash=fields["staged_snapshot_hash"],
        mutation_op=fields["mutation_op"],
    )


def _attestation_fields(args) -> dict[str, str]:
    return dict(
        attestation_kind=str(getattr(args, "attestation_kind", "") or "").strip(),
        commit_sha=str(getattr(args, "commit_sha", "") or "").strip(),
        plan_revision_before=str(
            getattr(args, "plan_revision_before", "") or ""
        ).strip(),
        plan_revision_after=str(
            getattr(args, "plan_revision_after", "") or ""
        ).strip(),
        operator_signature=str(
            getattr(args, "operator_signature", "") or ""
        ).strip(),
        pipeline_generation=str(
            getattr(args, "pipeline_generation", "") or ""
        ).strip(),
        staged_snapshot_hash=str(
            getattr(args, "staged_snapshot_hash", "") or ""
        ).strip(),
        mutation_op=str(getattr(args, "mutation_op", "") or "").strip(),
    )


def _has_attestation_evidence(args, fields: dict[str, str]) -> bool:
    return (
        any(fields.values())
        or bool(getattr(args, "run_record_id", []) or [])
        or bool(getattr(args, "action_result_id", []) or [])
        or bool(getattr(args, "evidence_artifact_path", []) or [])
    )
