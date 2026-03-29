"""Shared models for typed startup push-decision projection."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .finding_contracts import RejectedRuleTraceRecord, RuleMatchEvidenceRecord


@dataclass(frozen=True, slots=True)
class PushDecisionState:
    """Typed answer for the next governed push step."""

    worktree_clean: bool = False
    review_gate_allows_push: bool = False
    has_remote_work_to_push: bool = False
    push_eligible_now: bool = False
    action: str = "await_checkpoint"
    reason: str = ""
    next_step_summary: str = ""
    next_step_command: str = ""
    rule_summary: str = ""
    match_evidence: tuple[RuleMatchEvidenceRecord, ...] = ()
    rejected_rule_traces: tuple[RejectedRuleTraceRecord, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["match_evidence"] = [
            evidence.to_dict() for evidence in self.match_evidence
        ]
        payload["rejected_rule_traces"] = [
            trace.to_dict() for trace in self.rejected_rule_traces
        ]
        return payload


@dataclass(frozen=True, slots=True)
class PushDecisionInputs:
    """Derived inputs reused across push-decision branches."""

    worktree_clean: bool
    review_gate_allows_push: bool
    has_remote_work_to_push: bool


@dataclass(frozen=True, slots=True)
class PushDecisionSpec:
    """Branch-specific payload that gets projected into a push decision."""

    action: str
    reason: str
    next_step_summary: str
    rule_summary: str
    match_evidence: tuple[RuleMatchEvidenceRecord, ...]
    rejected_rule_traces: tuple[RejectedRuleTraceRecord, ...]
    next_step_command: str = ""
    push_eligible_now: bool = False


def project_push_decision(
    inputs: PushDecisionInputs,
    spec: PushDecisionSpec,
) -> PushDecisionState:
    """Project one decision spec onto the shared typed push-decision payload."""
    return PushDecisionState(
        worktree_clean=inputs.worktree_clean,
        review_gate_allows_push=inputs.review_gate_allows_push,
        has_remote_work_to_push=inputs.has_remote_work_to_push,
        push_eligible_now=spec.push_eligible_now,
        action=spec.action,
        reason=spec.reason,
        next_step_summary=spec.next_step_summary,
        next_step_command=spec.next_step_command,
        rule_summary=spec.rule_summary,
        match_evidence=spec.match_evidence,
        rejected_rule_traces=spec.rejected_rule_traces,
    )
