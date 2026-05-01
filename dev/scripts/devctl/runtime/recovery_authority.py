"""Typed destructive-recovery authority for startup and runtime gates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

RecoveryAction = Literal[
    "none",
    "observe_only",
    "relaunch_allowed",
    "terminate_allowed",
]
RecoveryBasis = Literal[
    "none",
    "singleton_violation_proven",
    "stall_proven",
    "operator_approved",
    "process_dead",
]
RecoveryScope = Literal["this_session", "this_slice", "entire_lane"]

_RELAUNCH_ACTION_IDS = frozenset(
    {
        "ensure_runtime",
        "recover_implementer",
        "relaunch_review_loop",
        "resume_live_review_loop",
        "start_reviewer_follow_loop",
    }
)
_TERMINATE_ACTION_IDS = frozenset(
    {
        "kill_process",
        "kill_session",
        "terminate_lane",
        "terminate_process",
        "terminate_session",
    }
)
_HEALTHY_ACTION_IDS = frozenset({"", "continue_scoped_loop"})


@dataclass(frozen=True, slots=True)
class RecoveryAuthorityState:
    """Closed destructive-recovery decision emitted before runtime mutation."""

    schema_version: int = 1
    contract_id: str = "RecoveryAuthority"
    recovery_action: RecoveryAction = "none"
    recovery_basis: RecoveryBasis = "none"
    recovery_scope: RecoveryScope = "this_session"
    decision_action_id: str = ""
    diagnosis_status: str = ""
    command: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def derive_recovery_authority(review_state: object | None) -> RecoveryAuthorityState:
    """Derive destructive recovery authority from typed review-state evidence.

    Per Codex rev_pkt_2326/2361: when typed CoordinationStateProjection
    reports ``recovery_eligibility=remote_only``, local destructive
    commands like ``devctl commit`` must NOT be advised. The legacy
    decision.command field is suppressed in that case.
    """
    assessment = getattr(review_state, "recovery_assessment", None)
    if assessment is None:
        return RecoveryAuthorityState(reason="no_recovery_assessment")

    diagnosis = getattr(assessment, "diagnosis", None)
    decision = getattr(assessment, "decision", None)
    action_id = _text(getattr(decision, "action_id", ""))
    diagnosis_status = _text(getattr(diagnosis, "status", ""))
    raw_command = _text(getattr(decision, "command", ""))
    basis = _recovery_basis(diagnosis=diagnosis, decision=decision)
    scope = _recovery_scope(action_id)

    # Per rev_pkt_2326/2361: typed recovery_eligibility supersedes legacy
    # decision.command. When typed says remote_only or blocked, the
    # legacy command is suppressed to "" so consumers don't render
    # contradictory local-commit advice.
    typed_recovery_eligibility = ""
    if isinstance(review_state, object):
        coord = getattr(review_state, "coordination_state", None)
        if isinstance(coord, dict):
            typed_recovery_eligibility = str(
                coord.get("recovery_eligibility") or ""
            ).strip()
    command = (
        ""
        if typed_recovery_eligibility in {"remote_only", "blocked"}
        else raw_command
    )

    if action_id in _HEALTHY_ACTION_IDS:
        return RecoveryAuthorityState(
            recovery_scope=scope,
            decision_action_id=action_id,
            diagnosis_status=diagnosis_status,
            command=command,
            reason="no_destructive_recovery_needed",
        )

    if action_id in _TERMINATE_ACTION_IDS:
        if basis in {"operator_approved", "singleton_violation_proven"}:
            return RecoveryAuthorityState(
                recovery_action="terminate_allowed",
                recovery_basis=basis,
                recovery_scope=scope,
                decision_action_id=action_id,
                diagnosis_status=diagnosis_status,
                command=command,
                reason="terminate_preconditions_proven",
            )
        return _observe_only(
            basis=basis,
            scope=scope,
            action_id=action_id,
            diagnosis_status=diagnosis_status,
            command=command,
            reason="terminate_preconditions_missing",
        )

    if action_id in _RELAUNCH_ACTION_IDS:
        if basis in {
            "operator_approved",
            "process_dead",
            "singleton_violation_proven",
            "stall_proven",
        }:
            return RecoveryAuthorityState(
                recovery_action="relaunch_allowed",
                recovery_basis=basis,
                recovery_scope=scope,
                decision_action_id=action_id,
                diagnosis_status=diagnosis_status,
                command=command,
                reason="relaunch_preconditions_proven",
            )
        return _observe_only(
            basis=basis,
            scope=scope,
            action_id=action_id,
            diagnosis_status=diagnosis_status,
            command=command,
            reason="relaunch_preconditions_missing",
        )

    return _observe_only(
        basis=basis,
        scope=scope,
        action_id=action_id,
        diagnosis_status=diagnosis_status,
        command=command,
        reason="non_destructive_recovery_action",
    )


def _observe_only(
    *,
    basis: RecoveryBasis,
    scope: RecoveryScope,
    action_id: str,
    diagnosis_status: str,
    command: str,
    reason: str,
) -> RecoveryAuthorityState:
    return RecoveryAuthorityState(
        recovery_action="observe_only",
        recovery_basis=basis,
        recovery_scope=scope,
        decision_action_id=action_id,
        diagnosis_status=diagnosis_status,
        command=command,
        reason=reason,
    )


def _recovery_basis(
    *,
    diagnosis: object | None,
    decision: object | None,
) -> RecoveryBasis:
    evidence_text = " ".join(_evidence_terms(diagnosis=diagnosis, decision=decision))
    if _contains_any(evidence_text, ("operator_approved", "approval_applied")):
        return "operator_approved"
    if _contains_any(evidence_text, ("singleton_violation", "duplicate_session")):
        return "singleton_violation_proven"
    if _contains_any(
        evidence_text,
        ("process_dead", "conductor_inactive", "runtime_missing"),
    ):
        return "process_dead"
    if _contains_any(evidence_text, ("stall_proven", "stall_confirmed")):
        return "stall_proven"
    return "none"


def _evidence_terms(
    *,
    diagnosis: object | None,
    decision: object | None,
) -> tuple[str, ...]:
    values: list[str] = []
    for value in (
        getattr(diagnosis, "status", ""),
        getattr(diagnosis, "root_cause", ""),
        getattr(decision, "rationale", ""),
    ):
        text = _text(value)
        if text:
            values.append(text)
    values.extend(
        _text(item) for item in getattr(diagnosis, "supporting_causes", ()) or ()
    )
    for row in getattr(diagnosis, "evidence", ()) or ():
        for field_name in ("code", "surface", "field", "value", "detail"):
            value = _text(getattr(row, field_name, ""))
            if value:
                values.append(value)
    return tuple(values)


def _recovery_scope(action_id: str) -> RecoveryScope:
    if action_id in {
        "relaunch_review_loop",
        "resume_live_review_loop",
        "terminate_lane",
    }:
        return "entire_lane"
    if action_id in {"start_reviewer_follow_loop"}:
        return "this_slice"
    return "this_session"


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "RecoveryAction",
    "RecoveryAuthorityState",
    "RecoveryBasis",
    "RecoveryScope",
    "derive_recovery_authority",
]
