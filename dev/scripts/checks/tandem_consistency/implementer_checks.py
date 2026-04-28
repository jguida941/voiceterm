"""Implementer-owned tandem-consistency checks."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.peer_liveness import (
    normalize_reviewer_mode,
    reviewer_mode_is_active,
)
from dev.scripts.devctl.review_channel.ack_freshness_authority import (
    current_session_from_mapping,
    is_implementer_ack_current,
)
from dev.scripts.devctl.runtime.review_state_semantics import (
    is_missing_instruction,
    is_pending_implementer_state,
    is_pending_placeholder,
)
from dev.scripts.devctl.runtime.role_profile import TandemRole

from .support import (
    REVIEWER_WAIT_STATE_MARKERS,
    STALL_MARKERS,
    contains_any_marker,
    extract_metadata_value,
    extract_section,
    leading_section_excerpt,
    make_result,
)


def _typed_or_bridge_section(
    typed_current_session: dict[str, object],
    *,
    field: str,
    bridge_text: str,
    section: str,
) -> str:
    bridge_value = extract_section(bridge_text, section)
    if section in {"Claude Status", "Claude Ack"} and is_pending_placeholder(
        bridge_value
    ):
        return bridge_value.strip()
    if field in typed_current_session:
        typed_value = str(typed_current_session.get(field) or "").strip()
        if typed_value:
            return typed_value
    return bridge_value


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
    instruction = _typed_or_bridge_section(
        cs,
        field="current_instruction",
        bridge_text=bridge_text,
        section="Current Instruction For Claude",
    )
    ack = _typed_or_bridge_section(
        cs,
        field="implementer_ack",
        bridge_text=bridge_text,
        section="Claude Ack",
    )
    status = _typed_or_bridge_section(
        cs,
        field="implementer_status",
        bridge_text=bridge_text,
        section="Claude Status",
    )
    typed_ack_state = str(cs.get("implementer_ack_state") or "").strip().lower()

    if is_missing_instruction(instruction):
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

    aligned = is_implementer_ack_current(current_session_from_mapping(cs))

    return make_result(
        _CK,
        _R,
        aligned,
        "Implementer ACK and status are present and tranche-aligned."
        if aligned
        else (
            "Implementer ACK/status may be from a prior tranche based on "
            "typed ACK freshness state."
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
