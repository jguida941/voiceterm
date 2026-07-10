"""Recovery and attention parity checks for review-surface consistency."""

from __future__ import annotations

from .models import ConvergencePassViolation
from .queue_parity import queue_current_instruction_parity_violations
from .support import _nested

_ATTENTION_PROJECTION_FIELDS = (
    "status",
    "owner",
    "summary",
    "recommended_action",
    "recommended_command",
)


def recovery_surface_parity_errors(
    *,
    review_state: dict[str, object],
    compact: dict[str, object],
    bridge_poll: dict[str, object],
    turn_authority: dict[str, object],
) -> list[str]:
    return [
        violation.detail
        for violation in recovery_surface_parity_violations(
            review_state=review_state,
            compact=compact,
            bridge_poll=bridge_poll,
            turn_authority=turn_authority,
        )
    ]


def recovery_surface_parity_violations(
    *,
    review_state: dict[str, object],
    compact: dict[str, object],
    bridge_poll: dict[str, object],
    turn_authority: dict[str, object],
) -> list[ConvergencePassViolation]:
    diagnosis_status = _nested(
        review_state, "recovery_assessment", "diagnosis", "status"
    ) or _nested(review_state, "attention", "status")
    decision_action_id = _nested(
        review_state, "recovery_assessment", "decision", "action_id"
    )
    decision_command = _nested(
        review_state, "recovery_assessment", "decision", "command"
    ) or _nested(review_state, "attention", "recommended_command")
    if not diagnosis_status and not decision_action_id and not decision_command:
        return []

    errors: list[ConvergencePassViolation] = []
    surfaces = {
        "review_state_attention": {
            "diagnosis_status": _nested(review_state, "attention", "status"),
            "decision_command": _nested(
                review_state, "attention", "recommended_command"
            ),
        },
        "review_state_doctor": {
            "status": _nested(review_state, "_compat", "doctor", "status"),
            "diagnosis_status": _nested(
                review_state, "_compat", "doctor", "diagnosis_status"
            ),
            "decision_action_id": _nested(
                review_state, "_compat", "doctor", "decision_action_id"
            ),
            "decision_command": _nested(
                review_state, "_compat", "doctor", "decision_command"
            ),
        },
        "compact_doctor": {
            "status": _nested(compact, "doctor", "status"),
            "diagnosis_status": _nested(compact, "doctor", "diagnosis_status"),
            "decision_action_id": _nested(compact, "doctor", "decision_action_id"),
            "decision_command": _nested(compact, "doctor", "decision_command"),
        },
        "bridge_poll": bridge_poll,
        "turn_authority": turn_authority,
    }
    for surface_name, payload in surfaces.items():
        if not isinstance(payload, dict):
            continue
        _append_diagnosis_violations(
            errors,
            diagnosis_status=diagnosis_status,
            surface_name=surface_name,
            payload=payload,
        )
        _append_decision_violations(
            errors,
            decision_action_id=decision_action_id,
            decision_command=decision_command,
            surface_name=surface_name,
            payload=payload,
        )
    errors.extend(attention_projection_parity_violations(review_state))
    errors.extend(queue_current_instruction_parity_violations(review_state))
    return errors


def _append_diagnosis_violations(
    errors: list[ConvergencePassViolation],
    *,
    diagnosis_status: str,
    surface_name: str,
    payload: dict[str, object],
) -> None:
    if diagnosis_status:
        surface_status = str(payload.get("diagnosis_status") or "").strip()
        if not surface_status and surface_name == "review_state_attention":
            surface_status = str(payload.get("status") or "").strip()
        if surface_status and surface_status != diagnosis_status:
            errors.append(
                ConvergencePassViolation(
                    category="diagnosis_parity",
                    surface=surface_name,
                    field="diagnosis_status",
                    expected=diagnosis_status,
                    actual=surface_status,
                    detail=(
                        f"diagnosis parity mismatch on {surface_name}: "
                        f"expected={diagnosis_status!r}, actual={surface_status!r}"
                    ),
                )
            )
    status = str(payload.get("status") or "").strip()
    if diagnosis_status not in {"", "healthy"} and status == "healthy":
        errors.append(
            ConvergencePassViolation(
                category="healthy_surface_mismatch",
                surface=surface_name,
                field="status",
                expected=diagnosis_status,
                actual=status,
                detail=(
                    f"{surface_name} reports healthy while diagnosis is "
                    f"{diagnosis_status!r}"
                ),
            )
        )


def _append_decision_violations(
    errors: list[ConvergencePassViolation],
    *,
    decision_action_id: str,
    decision_command: str,
    surface_name: str,
    payload: dict[str, object],
) -> None:
    if decision_action_id:
        surface_action_id = str(payload.get("decision_action_id") or "").strip()
        if surface_action_id and surface_action_id != decision_action_id:
            errors.append(
                ConvergencePassViolation(
                    category="decision_parity",
                    surface=surface_name,
                    field="decision_action_id",
                    expected=decision_action_id,
                    actual=surface_action_id,
                    detail=(
                        f"decision parity mismatch on "
                        f"{surface_name}.decision_action_id: "
                        f"expected={decision_action_id!r}, "
                        f"actual={surface_action_id!r}"
                    ),
                )
            )
    if decision_command:
        surface_command = str(payload.get("decision_command") or "").strip()
        if not surface_command and surface_name == "review_state_attention":
            surface_command = str(
                payload.get("decision_command")
                or payload.get("recommended_command")
                or ""
            ).strip()
        if surface_command and surface_command != decision_command:
            errors.append(
                ConvergencePassViolation(
                    category="decision_parity",
                    surface=surface_name,
                    field="decision_command",
                    expected=decision_command,
                    actual=surface_command,
                    detail=(
                        f"decision parity mismatch on "
                        f"{surface_name}.decision_command: "
                        f"expected={decision_command!r}, "
                        f"actual={surface_command!r}"
                    ),
                )
            )


def attention_projection_parity_errors(review_state: dict[str, object]) -> list[str]:
    return [
        violation.detail
        for violation in attention_projection_parity_violations(review_state)
    ]


def attention_projection_parity_violations(
    review_state: dict[str, object],
) -> list[ConvergencePassViolation]:
    assessment = review_state.get("recovery_assessment")
    attention = review_state.get("attention")
    if not isinstance(assessment, dict):
        return []
    projected_attention = _assessment_attention_projection(assessment)
    if not projected_attention:
        return []
    if not isinstance(attention, dict):
        return [
            ConvergencePassViolation(
                category="attention_projection",
                surface="review_state.attention",
                detail="review_state.attention missing while recovery_assessment is present",
            )
        ]
    errors: list[ConvergencePassViolation] = []
    for field in _ATTENTION_PROJECTION_FIELDS:
        expected = projected_attention.get(field, "")
        actual = _nested(review_state, "attention", field)
        if actual != expected:
            errors.append(
                ConvergencePassViolation(
                    category="attention_projection",
                    surface="review_state.attention",
                    field=field,
                    expected=expected,
                    actual=actual,
                    detail=(
                        "attention projection mismatch on "
                        f"review_state.attention.{field}: "
                        f"expected={expected!r}, actual={actual!r}"
                    ),
                )
            )
    return errors


def _assessment_attention_projection(
    assessment: dict[str, object],
) -> dict[str, str]:
    diagnosis = assessment.get("diagnosis")
    decision = assessment.get("decision")
    if not isinstance(diagnosis, dict) and not isinstance(decision, dict):
        return {}
    diagnosis = diagnosis if isinstance(diagnosis, dict) else {}
    decision = decision if isinstance(decision, dict) else {}
    return {
        "status": str(diagnosis.get("status") or "unknown"),
        "owner": str(decision.get("execution_owner") or "system"),
        "summary": str(diagnosis.get("root_cause") or ""),
        "recommended_action": str(decision.get("rationale") or ""),
        "recommended_command": str(decision.get("command") or ""),
    }
