"""Queue/current-session parity checks for review-surface consistency."""

from __future__ import annotations

from .models import ConvergencePassViolation
from .support import _nested


def queue_current_instruction_parity_violations(
    review_state: dict[str, object],
) -> list[ConvergencePassViolation]:
    """Ensure the packet queue's active instruction reaches current_session."""
    expected = _nested(review_state, "queue", "derived_next_instruction").strip()
    if not expected:
        return []
    actual = _nested(review_state, "current_session", "current_instruction").strip()
    if _instruction_content_matches(actual, expected):
        return []
    source_packet = _nested(
        review_state,
        "queue",
        "derived_next_instruction_source",
        "packet_id",
    )
    return [
        ConvergencePassViolation(
            category="queue_current_instruction_parity",
            surface="review_state.current_session",
            field="current_instruction",
            expected=expected,
            actual=actual,
            detail=(
                "queue/current-session parity mismatch: "
                f"queue.derived_next_instruction={expected!r} from "
                f"{source_packet or 'unknown packet'} but "
                f"current_session.current_instruction={actual!r}"
            ),
        )
    ]


def _instruction_content_matches(actual: str, expected: str) -> bool:
    if actual == expected:
        return True
    return _without_markdown_bullets(actual) == _without_markdown_bullets(expected)


def _without_markdown_bullets(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        lines.append(stripped)
    return "\n".join(lines).strip()
