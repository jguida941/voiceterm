"""Implementer-owned tandem-consistency checks."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.peer_liveness import (
    normalize_reviewer_mode,
    reviewer_mode_is_active,
)
from dev.scripts.devctl.runtime.review_state_semantics import (
    is_pending_implementer_state,
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


def check_implementer_ack_freshness(
    bridge_text: str,
    *,
    typed_state: dict[str, object] | None = None,
) -> dict[str, object]:
    """Verify the implementer has acknowledged the current instruction tranche.

    When typed review_state.json is available, reads reviewer_mode from
    bridge block and implementer ACK state from current_session. Falls back
    to bridge prose parsing when typed fields are missing.
    """
    _CK, _R = "implementer_ack_freshness", TandemRole.IMPLEMENTER

    bridge_block = (typed_state or {}).get("bridge") or {}
    cs = (typed_state or {}).get("current_session") or {}
    typed_mode = str(bridge_block.get("reviewer_mode") or "").strip()
    typed_ack_current = bridge_block.get("claude_ack_current")

    # Prefer typed reviewer_mode
    if typed_mode:
        reviewer_mode = normalize_reviewer_mode(typed_mode)
    else:
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

    # Prefer typed current_session fields
    instruction = str(cs.get("current_instruction") or "").strip() or extract_section(bridge_text, "Current Instruction For Claude")
    ack = str(cs.get("implementer_ack") or "").strip() or extract_section(bridge_text, "Claude Ack")
    status = str(cs.get("implementer_status") or "").strip() or extract_section(bridge_text, "Claude Status")
    typed_ack_state = str(cs.get("implementer_ack_state") or "").strip().lower()

    if not instruction.strip():
        return make_result(
            _CK,
            _R,
            True,
            "No current instruction — implementer ACK not required.",
        )
    if is_pending_implementer_state(
        implementer_status=status,
        implementer_ack=ack,
        implementer_ack_state=typed_ack_state,
    ):
        return make_result(
            _CK,
            _R,
            True,
            "Implementer state is freshly reset to pending for the current instruction revision.",
            tranche_aligned=True,
            ack_state="pending",
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

    # Use typed ack_current flag when available; else fall back to keyword matching
    if typed_ack_current is not None:
        aligned = bool(typed_ack_current)
    else:
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


def check_implementer_completion_stall(
    bridge_text: str,
    *,
    typed_state: dict[str, object] | None = None,
) -> dict[str, object]:
    """Fail when the implementer parks on review/polling while work is still live.

    When typed review_state.json is available, reads the pre-computed
    ``bridge.implementer_completion_stall`` boolean and reviewer_mode
    instead of re-parsing bridge prose with marker heuristics.
    """
    _CK, _R = "implementer_completion_stall", TandemRole.IMPLEMENTER

    bridge_block = (typed_state or {}).get("bridge") or {}
    typed_stall = bridge_block.get("implementer_completion_stall")
    typed_mode = str(bridge_block.get("reviewer_mode") or "").strip()

    # Fast path: typed state has the pre-computed stall flag
    if typed_stall is not None and typed_mode:
        reviewer_mode = normalize_reviewer_mode(typed_mode)
        if not bool(typed_stall):
            return make_result(
                _CK,
                _R,
                True,
                "Implementer status/ACK do not show a completion-stall pattern (typed).",
                stalled=False,
            )
        # Stall detected via typed state
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

    # Fallback: parse bridge prose with marker heuristics
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
