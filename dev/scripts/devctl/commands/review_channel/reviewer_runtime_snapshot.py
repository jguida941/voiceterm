"""Shared report-attachment helpers for reviewer-runtime projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, is_dataclass

from ...review_channel.reviewer_runtime_contract import (
    build_reviewer_doctor_surface,
    reviewer_runtime_contract_to_dict,
)
from ...review_channel.runtime_counts import build_runtime_counts
from ...review_channel.status_projection_bridge_state import (
    build_typed_bridge_liveness,
)
from ...runtime.authority_snapshot import project_authority_snapshot
from ...runtime.control_topology import derive_startup_control_truth
from ...runtime.review_state_models import ReviewState
from ...runtime.reviewer_mode_projection import (
    write_effective_reviewer_mode,
    write_reviewer_mode,
)

_AUTHORITY_BOOTSTRAP_COMMAND = (
    "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md"
)


def _collaboration_payload(collaboration_state: object) -> dict[str, object] | None:
    if collaboration_state is None:
        return None
    if is_dataclass(collaboration_state) and not isinstance(collaboration_state, type):
        return asdict(collaboration_state)
    if isinstance(collaboration_state, Mapping):
        return dict(collaboration_state)
    to_dict = getattr(collaboration_state, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, dict):
            return payload
    payload = getattr(collaboration_state, "__dict__", None)
    return dict(payload) if isinstance(payload, dict) else None


def _text(value: object) -> str:
    return str(value or "").strip()


def _attach_phase_zero_parity_fields(
    report: dict[str, object],
    *,
    review_state: ReviewState,
    current_session: object,
    bridge_liveness: Mapping[str, object],
) -> None:
    """Promote the proof-tick parity fields to the status top level."""
    authority_snapshot = report.get("authority_snapshot")
    if not isinstance(authority_snapshot, Mapping):
        authority_snapshot = getattr(review_state, "authority_snapshot", None)
    coordination = getattr(review_state, "coordination", None)
    reviewer_runtime = getattr(review_state, "reviewer_runtime", None)

    reviewer_mode = ""
    effective_reviewer_mode = ""
    current_instruction_revision = ""
    implementer_ack_state = ""
    resync_required: bool | None = None
    next_command = ""

    if authority_snapshot is not None:
        if isinstance(authority_snapshot, Mapping):
            reviewer_mode = _text(authority_snapshot.get("reviewer_mode"))
            current_instruction_revision = _text(
                authority_snapshot.get("current_instruction_revision")
            )
            implementer_ack_state = _text(
                authority_snapshot.get("implementer_ack_state")
            )
            resync_required = bool(authority_snapshot.get("resync_required", False))
            next_command = _text(authority_snapshot.get("next_command"))
        else:
            reviewer_mode = _text(getattr(authority_snapshot, "reviewer_mode", ""))
            current_instruction_revision = _text(
                getattr(authority_snapshot, "current_instruction_revision", "")
            )
            implementer_ack_state = _text(
                getattr(authority_snapshot, "implementer_ack_state", "")
            )
            resync_required = bool(
                getattr(authority_snapshot, "resync_required", False)
            )
            next_command = _text(getattr(authority_snapshot, "next_command", ""))

    if reviewer_runtime is not None:
        effective_reviewer_mode = _text(
            getattr(reviewer_runtime, "effective_reviewer_mode", "")
        )
        report["reviewer_freshness"] = _text(
            getattr(reviewer_runtime, "reviewer_freshness", "")
        )
        last_poll = getattr(reviewer_runtime, "last_poll", None)
        report["last_codex_poll"] = _text(
            getattr(last_poll, "last_codex_poll_utc", "")
        ) or _text(bridge_liveness.get("last_codex_poll_utc"))
        report["last_codex_poll_utc"] = report["last_codex_poll"]

    if coordination is not None:
        report["safe_to_fanout"] = bool(getattr(coordination, "safe_to_fanout", False))
        report["ownership_status"] = _text(
            getattr(coordination, "ownership_status", "")
        )
        resync_required = bool(getattr(coordination, "resync_required", False))

    if current_session is not None:
        current_instruction_revision = current_instruction_revision or _text(
            getattr(current_session, "current_instruction_revision", "")
        )
        implementer_ack_state = implementer_ack_state or _text(
            getattr(current_session, "implementer_ack_state", "")
        )

    write_reviewer_mode(report, reviewer_mode or effective_reviewer_mode)
    write_effective_reviewer_mode(
        report,
        effective_reviewer_mode
        or reviewer_mode
        or _text(bridge_liveness.get("effective_reviewer_mode")),
    )
    report["current_instruction_revision"] = current_instruction_revision
    report["implementer_ack_state"] = implementer_ack_state
    if resync_required is not None:
        report["resync_required"] = resync_required
    report["next_command"] = next_command

    snapshot_id = _text(getattr(review_state, "snapshot_id", ""))
    zref = _text(getattr(review_state, "zref", ""))
    if snapshot_id:
        report["snapshot_id"] = snapshot_id
    if zref:
        report["zref"] = zref


def attach_reviewer_runtime_snapshot(
    report: dict[str, object],
    *,
    review_state: ReviewState | None,
    attention: Mapping[str, object] | None,
) -> None:
    """Attach reviewer-runtime and doctor projections from one typed review state."""
    if review_state is None:
        return
    recovery_assessment = getattr(review_state, "recovery_assessment", None)
    review_attention = getattr(review_state, "attention", None)
    derived_attention = (
        asdict(review_attention) if review_attention is not None else None
    )
    effective_attention = derived_attention or (
        dict(attention) if isinstance(attention, Mapping) else None
    )
    report["reviewer_runtime"] = reviewer_runtime_contract_to_dict(
        review_state.reviewer_runtime
    )
    report["commit_pipeline"] = asdict(review_state.commit_pipeline)
    if effective_attention is not None:
        report["attention"] = effective_attention
    report["recovery_assessment"] = (
        asdict(recovery_assessment) if recovery_assessment is not None else None
    )
    bridge_liveness_report = (
        report.get("bridge_liveness")
        if isinstance(report.get("bridge_liveness"), Mapping)
        else None
    )
    collaboration_state = getattr(review_state, "collaboration", None)
    collaboration = _collaboration_payload(collaboration_state)
    if collaboration is not None:
        report["collaboration"] = collaboration
    current_session = getattr(review_state, "current_session", None)
    if current_session is not None:
        report["current_session"] = asdict(current_session)
    queue = getattr(review_state, "queue", None)
    if queue is not None:
        if is_dataclass(queue) and not isinstance(queue, type):
            report["queue"] = asdict(queue)
        elif isinstance(queue, Mapping):
            report["queue"] = dict(queue)
    coordination = getattr(review_state, "coordination", None)
    if coordination is not None:
        report["coordination"] = coordination.to_dict()
    observed_control_topology, implementation_permission = derive_startup_control_truth(
        review_state
    )
    report["observed_control_topology"] = observed_control_topology
    report["implementation_permission"] = implementation_permission
    bridge_liveness = dict(bridge_liveness_report or {})
    if current_session is not None:
        bridge_liveness.update(
            build_typed_bridge_liveness(
                bridge_liveness=bridge_liveness,
                current_session=current_session,
                collaboration=collaboration_state,
            )
        )
    if bridge_liveness:
        report["bridge_liveness"] = bridge_liveness
    publisher = report.get("publisher")
    reviewer_supervisor = report.get("reviewer_supervisor")
    report["doctor"] = build_reviewer_doctor_surface(
        contract=review_state.reviewer_runtime,
        collaboration=collaboration,
        bridge_liveness=bridge_liveness,
        recovery_assessment=recovery_assessment,
        attention=effective_attention,
        commit_pipeline=review_state.commit_pipeline,
        push_enforcement=(
            bridge_liveness.get("push_enforcement") if bridge_liveness else None
        ),
        runtime_state={
            "publisher": publisher,
            "reviewer_supervisor": reviewer_supervisor,
        },
    )
    report["runtime_counts"] = build_runtime_counts(
        collaboration=collaboration,
        bridge_liveness=bridge_liveness,
        publisher_running=bool(
            publisher.get("running") if isinstance(publisher, Mapping) else False
        ),
        reviewer_supervisor_running=bool(
            reviewer_supervisor.get("running")
            if isinstance(reviewer_supervisor, Mapping)
            else False
        ),
    )
    packet_inbox = getattr(review_state, "packet_inbox", None)
    if packet_inbox is not None:
        report["packet_inbox"] = asdict(packet_inbox)
    authority_snapshot = getattr(review_state, "authority_snapshot", None)
    fallback_next_command = (
        str(authority_snapshot.next_command or "").strip()
        if authority_snapshot is not None
        else ""
    )
    projected = project_authority_snapshot(report, caller_role="observer")
    if fallback_next_command and projected.next_command in {
        "",
        _AUTHORITY_BOOTSTRAP_COMMAND,
    }:
        project_authority_snapshot(
            report, caller_role="observer", next_command=fallback_next_command
        )
    _attach_phase_zero_parity_fields(
        report,
        review_state=review_state,
        current_session=current_session,
        bridge_liveness=bridge_liveness,
    )
