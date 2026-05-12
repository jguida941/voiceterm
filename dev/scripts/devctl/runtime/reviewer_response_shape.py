"""Typed terminal-response shape for reviewer/controller loops."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from .value_coercion import coerce_string, coerce_string_items


REVIEWER_RESPONSE_SHAPE_CONTRACT_ID = "ReviewerResponseShape"
REVIEWER_RESPONSE_SHAPE_SCHEMA_VERSION = 1

_FORBIDDEN_STATUS_MARKERS = (
    "holding position",
    "monitor armed",
    "status update",
    "status ledger",
    "session ledger",
    "insight block",
    "waiting for",
)
_FORBIDDEN_COMPLETION_MARKERS = (
    "task_complete",
    "done",
    "ready",
    "complete",
    "completed",
    "final summary",
)


@dataclass(frozen=True, slots=True)
class ReviewerResponseShape:
    """Terminal response policy derived from typed controller state."""

    actor_id: str = ""
    role: str = ""
    final_response_allowed: bool = False
    continuation_state: str = "must_continue"
    response_mode: str = "continue_to_goal"
    status_prose_allowed: bool = False
    completion_prose_allowed: bool = False
    required_next_action: str = "run_next_command"
    next_required_command: str = ""
    continuation_goal: str = ""
    blocking_packet_id: str = ""
    operator_status_source: str = ""
    proposed_response_text_observed: bool = False
    proposed_response_text_source: str = ""
    allowed_response_kinds: tuple[str, ...] = ()
    forbidden_markers: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()
    status: str = "allowed"
    summary: str = ""
    schema_version: int = REVIEWER_RESPONSE_SHAPE_SCHEMA_VERSION
    contract_id: str = REVIEWER_RESPONSE_SHAPE_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["allowed_response_kinds"] = list(self.allowed_response_kinds)
        payload["forbidden_markers"] = list(self.forbidden_markers)
        payload["violations"] = list(self.violations)
        return payload


def reviewer_response_shape_for_gate(
    final_response_gate: Any,
    *,
    actor_id: object = "",
    role: object = "",
    session_activity_log_ref: object = "",
    proposed_response_text: object = "",
    proposed_response_text_source: object = "",
) -> ReviewerResponseShape:
    """Resolve the response shape allowed by a materialized final gate."""
    gate_allows = _bool(_field(final_response_gate, "allow_final_response"))
    continuation_state = (
        coerce_string(_field(final_response_gate, "continuation_state"))
        or ("may_stop" if gate_allows else "must_continue")
    )
    activity_ref = coerce_string(session_activity_log_ref)
    proposed_text = coerce_string(proposed_response_text)
    proposed_source = coerce_string(proposed_response_text_source)
    if proposed_text and not proposed_source:
        proposed_source = "direct_argument"
    if gate_allows:
        shape = ReviewerResponseShape(
            actor_id=coerce_string(actor_id),
            role=coerce_string(role),
            final_response_allowed=True,
            continuation_state=continuation_state,
            response_mode="completion_summary_from_receipts",
            status_prose_allowed=True,
            completion_prose_allowed=True,
            required_next_action=(
                coerce_string(_field(final_response_gate, "action"))
                or "allow_final_response"
            ),
            next_required_command=coerce_string(
                _field(final_response_gate, "next_required_command")
            ),
            continuation_goal=coerce_string(
                _field(final_response_gate, "continuation_goal")
            ),
            blocking_packet_id=coerce_string(
                _field(final_response_gate, "blocking_packet_id")
            ),
            operator_status_source=activity_ref or "typed_receipts",
            proposed_response_text_observed=bool(proposed_text),
            proposed_response_text_source=proposed_source,
            allowed_response_kinds=(
                "completion_summary",
                "typed_receipt_summary",
            ),
            forbidden_markers=(),
            summary=(
                "Typed controller is closed; completion prose may summarize "
                "typed receipts."
            ),
        )
        return _with_violations(shape, proposed_text)

    shape = ReviewerResponseShape(
        actor_id=coerce_string(actor_id),
        role=coerce_string(role),
        final_response_allowed=False,
        continuation_state=continuation_state,
        response_mode="continue_to_goal",
        status_prose_allowed=False,
        completion_prose_allowed=False,
        required_next_action=(
            coerce_string(_field(final_response_gate, "action"))
            or coerce_string(_field(final_response_gate, "user_action"))
            or "run_next_command"
        ),
        next_required_command=coerce_string(
            _field(final_response_gate, "next_required_command")
        ),
        continuation_goal=coerce_string(
            _field(final_response_gate, "continuation_goal")
        )
        or coerce_string(_field(final_response_gate, "blocking_packet_id")),
        blocking_packet_id=coerce_string(
            _field(final_response_gate, "blocking_packet_id")
        ),
        operator_status_source=activity_ref or "session_activity_log_required",
        proposed_response_text_observed=bool(proposed_text),
        proposed_response_text_source=proposed_source,
        allowed_response_kinds=(
            "typed_packet",
            "tool_command",
            "brief_progress_event",
        ),
        forbidden_markers=(
            *_FORBIDDEN_STATUS_MARKERS,
            *_FORBIDDEN_COMPLETION_MARKERS,
            "markdown_table",
        ),
        summary=(
            "Typed controller still requires work; operator-facing status "
            "belongs in SessionActivityLog/typed packets, not terminal prose."
        ),
    )
    return _with_violations(shape, proposed_response_text)


def reviewer_response_shape_from_mapping(
    payload: Mapping[str, object],
) -> ReviewerResponseShape:
    """Normalize a mapping into a ReviewerResponseShape."""
    return ReviewerResponseShape(
        actor_id=coerce_string(payload.get("actor_id")),
        role=coerce_string(payload.get("role")),
        final_response_allowed=_bool(payload.get("final_response_allowed")),
        continuation_state=(
            coerce_string(payload.get("continuation_state")) or "must_continue"
        ),
        response_mode=coerce_string(payload.get("response_mode")) or "continue_to_goal",
        status_prose_allowed=_bool(payload.get("status_prose_allowed")),
        completion_prose_allowed=_bool(payload.get("completion_prose_allowed")),
        required_next_action=(
            coerce_string(payload.get("required_next_action")) or "run_next_command"
        ),
        next_required_command=coerce_string(payload.get("next_required_command")),
        continuation_goal=coerce_string(payload.get("continuation_goal")),
        blocking_packet_id=coerce_string(payload.get("blocking_packet_id")),
        operator_status_source=coerce_string(payload.get("operator_status_source")),
        proposed_response_text_observed=_bool(
            payload.get("proposed_response_text_observed")
        ),
        proposed_response_text_source=coerce_string(
            payload.get("proposed_response_text_source")
        ),
        allowed_response_kinds=coerce_string_items(
            payload.get("allowed_response_kinds")
        ),
        forbidden_markers=coerce_string_items(payload.get("forbidden_markers")),
        violations=coerce_string_items(payload.get("violations")),
        status=coerce_string(payload.get("status")) or "allowed",
        summary=coerce_string(payload.get("summary")),
        schema_version=_int(payload.get("schema_version"))
        or REVIEWER_RESPONSE_SHAPE_SCHEMA_VERSION,
        contract_id=(
            coerce_string(payload.get("contract_id"))
            or REVIEWER_RESPONSE_SHAPE_CONTRACT_ID
        ),
    )


def _with_violations(
    shape: ReviewerResponseShape,
    proposed_response_text: object,
) -> ReviewerResponseShape:
    text = coerce_string(proposed_response_text)
    violations = _response_shape_violations(text, shape)
    if not violations:
        return shape
    return ReviewerResponseShape(
        **{
            **shape.to_dict(),
            "violations": violations,
            "status": "blocked",
            "summary": (
                "Proposed terminal response conflicts with typed continuation "
                "state."
            ),
        }
    )


def _response_shape_violations(
    text: str,
    shape: ReviewerResponseShape,
) -> tuple[str, ...]:
    if not text:
        return ()
    lowered = text.lower()
    violations: list[str] = []
    if not shape.status_prose_allowed:
        for marker in _FORBIDDEN_STATUS_MARKERS:
            if marker in lowered:
                violations.append(f"status_marker:{marker}")
        if _looks_like_markdown_table(text):
            violations.append("status_marker:markdown_table")
    if not shape.completion_prose_allowed:
        for marker in _FORBIDDEN_COMPLETION_MARKERS:
            if marker in lowered:
                violations.append(f"completion_marker:{marker}")
    return tuple(dict.fromkeys(violations))


def _looks_like_markdown_table(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines()]
    pipe_lines = [line for line in lines if line.startswith("|") and line.endswith("|")]
    return len(pipe_lines) >= 2 and any("---" in line for line in pipe_lines)


def _field(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None)


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return coerce_string(value).lower() in {"1", "true", "yes", "on"}


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "REVIEWER_RESPONSE_SHAPE_CONTRACT_ID",
    "REVIEWER_RESPONSE_SHAPE_SCHEMA_VERSION",
    "ReviewerResponseShape",
    "reviewer_response_shape_for_gate",
    "reviewer_response_shape_from_mapping",
]
