"""Implementer-owned tandem-consistency checks."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.peer_liveness import (
    normalize_reviewer_mode,
    reviewer_mode_is_active,
)
from dev.scripts.devctl.runtime.role_profile import TandemRole

from .support import (
    REVIEWER_WAIT_STATE_MARKERS,
    STALL_MARKERS,
    ack_references_instruction,
    contains_any_marker,
    extract_metadata_value,
    extract_section,
    leading_section_excerpt,
    make_result,
)


def check_implementer_ack_freshness(bridge_text: str) -> dict[str, object]:
    """Verify the implementer has acknowledged the current instruction tranche."""
    _CK, _R = "implementer_ack_freshness", TandemRole.IMPLEMENTER
    reviewer_mode = normalize_reviewer_mode(
        extract_metadata_value(bridge_text, "Reviewer mode:")
    )
    if not reviewer_mode_is_active(reviewer_mode):
        return make_result(
            _CK,
            _R,
            True,
            f"Reviewer mode is `{reviewer_mode}`; implementer ACK is not required.",
            reviewer_mode=reviewer_mode,
            tranche_aligned=None,
        )

    instruction = extract_section(bridge_text, "Current Instruction For Claude")
    ack = extract_section(bridge_text, "Claude Ack")
    status = extract_section(bridge_text, "Claude Status")
    if not instruction.strip():
        return make_result(
            _CK,
            _R,
            True,
            "No current instruction — implementer ACK not required.",
        )
    if not ack.strip():
        return make_result(
            _CK,
            _R,
            False,
            "Implementer has not acknowledged the current instruction.",
        )
    if not status.strip():
        return make_result(
            _CK,
            _R,
            False,
            "Implementer status is empty — no active coding session visible.",
        )

    aligned = ack_references_instruction(instruction, ack, status)
    return make_result(
        _CK,
        _R,
        aligned,
        "Implementer ACK and status are present and tranche-aligned."
        if aligned
        else (
            "Implementer ACK/status may be from a prior tranche — does not "
            "reference current instruction keywords."
        ),
        tranche_aligned=aligned,
    )


def check_implementer_completion_stall(bridge_text: str) -> dict[str, object]:
    """Fail when the implementer parks on review/polling while work is still live."""
    _CK, _R = "implementer_completion_stall", TandemRole.IMPLEMENTER
    reviewer_mode = normalize_reviewer_mode(
        extract_metadata_value(bridge_text, "Reviewer mode:")
    )
    instruction = extract_section(bridge_text, "Current Instruction For Claude")
    poll_status = extract_section(bridge_text, "Poll Status")
    ack = leading_section_excerpt(extract_section(bridge_text, "Claude Ack"))
    status = leading_section_excerpt(extract_section(bridge_text, "Claude Status"))
    combined = f"{status}\n{ack}".strip()

    if not contains_any_marker(combined, STALL_MARKERS):
        return make_result(
            _CK,
            _R,
            True,
            "Implementer status/ACK do not show a completion-stall pattern.",
            stalled=False,
        )

    if contains_any_marker(
        instruction,
        REVIEWER_WAIT_STATE_MARKERS,
    ) or contains_any_marker(poll_status, REVIEWER_WAIT_STATE_MARKERS):
        return make_result(
            _CK,
            _R,
            True,
            "Implementer is polling under an explicit reviewer-owned wait state.",
            stalled=False,
            wait_state=True,
        )

    if not reviewer_mode_is_active(reviewer_mode):
        return make_result(
            _CK,
            _R,
            False,
            "Implementer claims to be waiting/polling for reviewer action while reviewer mode is inactive.",
            stalled=True,
            reviewer_mode=reviewer_mode,
        )

    return make_result(
        _CK,
        _R,
        False,
        "Implementer appears parked on reviewer promotion/polling while the current instruction is still active.",
        stalled=True,
        reviewer_mode=reviewer_mode,
    )
