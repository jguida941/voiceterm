"""Shared report-attachment helpers for reviewer-runtime projections."""

from __future__ import annotations

from dataclasses import asdict
from collections.abc import Mapping

from ...runtime.control_topology import derive_startup_control_truth
from ...runtime.review_state_models import ReviewState
from ...review_channel.runtime_counts import build_runtime_counts
from ...review_channel.reviewer_runtime_contract import (
    build_reviewer_doctor_surface,
    reviewer_runtime_contract_to_dict,
)
from ...review_channel.status_projection_bridge_state import (
    build_typed_bridge_liveness,
)
from ...runtime.authority_snapshot import project_authority_snapshot

_AUTHORITY_BOOTSTRAP_COMMAND = (
    "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md"
)


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
    derived_attention = asdict(review_attention) if review_attention is not None else None
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
        asdict(recovery_assessment)
        if recovery_assessment is not None
        else None
    )
    bridge_liveness_report = (
        report.get("bridge_liveness")
        if isinstance(report.get("bridge_liveness"), Mapping)
        else None
    )
    collaboration_state = getattr(review_state, "collaboration", None)
    collaboration = (
        asdict(collaboration_state)
        if collaboration_state is not None
        else None
    )
    current_session = getattr(review_state, "current_session", None)
    if current_session is not None:
        report["current_session"] = asdict(current_session)
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
            bridge_liveness.get("push_enforcement")
            if bridge_liveness
            else None
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
            publisher.get("running")
            if isinstance(publisher, Mapping)
            else False
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
    projected = project_authority_snapshot(report)
    if (
        fallback_next_command
        and projected.next_command in {"", _AUTHORITY_BOOTSTRAP_COMMAND}
    ):
        project_authority_snapshot(report, next_command=fallback_next_command)
