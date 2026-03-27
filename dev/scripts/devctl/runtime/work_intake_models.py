"""Typed models for startup work-intake packets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .finding_contracts import (
    RejectedRuleTraceRecord,
    RuleMatchEvidenceRecord,
)


@dataclass(frozen=True, slots=True)
class PlanTargetRef:
    """Canonical mutable plan target selected for startup continuity."""

    target_id: str
    plan_path: str
    plan_title: str
    plan_scope: str
    target_kind: str
    anchor_ref: str
    expected_revision: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SessionContinuityState:
    """Reconciled continuity state across plan resume and live review state."""

    source_plan_path: str = ""
    source_plan_title: str = ""
    source_scope: str = ""
    summary: str = ""
    current_goal: str = ""
    next_action: str = ""
    review_scope: str = ""
    review_instruction: str = ""
    review_open_findings: str = ""
    implementer_status: str = ""
    alignment_status: str = "missing"
    alignment_reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class IntakeRoutingState:
    """Live startup-routing decisions derived from ProjectGovernance."""

    startup_reads: tuple[str, ...] = ()
    workflow_profiles: tuple[str, ...] = ()
    selected_workflow_profile: str = ""
    default_remote: str = ""
    development_branch: str = ""
    preflight_command: str = ""
    post_push_bundle: str = ""
    rule_summary: str = ""
    match_evidence: tuple[RuleMatchEvidenceRecord, ...] = ()
    rejected_rule_traces: tuple[RejectedRuleTraceRecord, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["startup_reads"] = list(self.startup_reads)
        payload["workflow_profiles"] = list(self.workflow_profiles)
        payload["match_evidence"] = [
            evidence.to_dict() for evidence in self.match_evidence
        ]
        payload["rejected_rule_traces"] = [
            trace.to_dict() for trace in self.rejected_rule_traces
        ]
        return payload


@dataclass(frozen=True, slots=True)
class WorkIntakePacket:
    """First bounded startup/work-routing packet for AI sessions."""

    schema_version: int = 1
    contract_id: str = "WorkIntakePacket"
    goal: str = "startup-context"
    advisory_action: str = ""
    advisory_reason: str = ""
    active_target: PlanTargetRef | None = None
    continuity: SessionContinuityState = field(default_factory=SessionContinuityState)
    routing: IntakeRoutingState = field(default_factory=IntakeRoutingState)
    scope_hints: tuple[str, ...] = ()
    warm_refs: tuple[str, ...] = ()
    writeback_sinks: tuple[str, ...] = ()
    confidence: str = "low"
    fallback_reason: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scope_hints"] = list(self.scope_hints)
        payload["warm_refs"] = list(self.warm_refs)
        payload["writeback_sinks"] = list(self.writeback_sinks)
        if self.active_target is not None:
            payload["active_target"] = self.active_target.to_dict()
        payload["continuity"] = self.continuity.to_dict()
        payload["routing"] = self.routing.to_dict()
        return payload


__all__ = [
    "IntakeRoutingState",
    "PlanTargetRef",
    "SessionContinuityState",
    "WorkIntakePacket",
]
