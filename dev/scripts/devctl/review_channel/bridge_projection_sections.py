"""Section helpers for bridge compatibility projections."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_state_semantics import is_missing_instruction
from .action_request import render_action_requests_from_packets
from .bridge_validation_poll_status import (
    extract_poll_status_reviewer_modes,
    poll_status_is_automation_only_refresh,
)
from .bridge_projection_contract import BRIDGE_SECTION_ORDER


def projection_sections(
    raw_sections: Mapping[str, str],
    *,
    current_session: Mapping[str, object],
    reviewer_runtime: Mapping[str, object],
    packets: list[dict[str, object]] | None = None,
) -> dict[str, str]:
    sections = _tracked_sections(raw_sections)
    if poll_status_is_automation_only_refresh(sections.get("Poll Status", "")):
        # Automation heartbeats are runtime bookkeeping, not reviewer-owned
        # authority. Drop them so render-bridge falls back to typed projection
        # text instead of preserving a stale launch-truth blocker.
        sections["Poll Status"] = ""
    review_acceptance = _mapping(reviewer_runtime.get("review_acceptance"))
    typed_overrides = (
        (
            "Current Verdict",
            _typed_section_override(review_acceptance.get("current_verdict")),
            "current_verdict" in review_acceptance,
        ),
        (
            "Open Findings",
            _typed_section_override(
                review_acceptance.get("open_findings")
                or current_session.get("open_findings")
            ),
            (
                "open_findings" in review_acceptance
                or "open_findings" in current_session
            ),
        ),
        (
            "Claude Status",
            _typed_section_override(current_session.get("implementer_status")),
            "implementer_status" in current_session,
        ),
        (
            "Claude Ack",
            _typed_section_override(current_session.get("implementer_ack")),
            "implementer_ack" in current_session,
        ),
        (
            "Current Instruction For Claude",
            _typed_section_override(current_session.get("current_instruction")),
            "current_instruction" in current_session,
        ),
        (
            "Last Reviewed Scope",
            _typed_section_override(current_session.get("last_reviewed_scope")),
            "last_reviewed_scope" in current_session,
        ),
    )
    for heading, value, typed_present in typed_overrides:
        if value:
            sections[heading] = value
            continue
        if typed_present:
            sections[heading] = ""
    if packets is not None:
        sections["Action Requests"] = render_action_requests_from_packets(
            packets
        )
    return sections


def with_fallback_sections(
    review_state: Mapping[str, object],
    sections: Mapping[str, str],
) -> dict[str, str]:
    result = {heading: str(sections.get(heading, "")) for heading in BRIDGE_SECTION_ORDER}
    compat_projection = _mapping(_mapping(review_state.get("_compat")).get("bridge_projection"))
    raw_projection_sections = string_mapping(compat_projection.get("sections"))
    current_session = _mapping(review_state.get("current_session"))
    reviewer_runtime = _mapping(review_state.get("reviewer_runtime"))
    review_acceptance = _mapping(reviewer_runtime.get("review_acceptance"))
    raw_poll_status = raw_projection_sections.get("Poll Status", "")
    poll_status_fallback = _poll_status_fallback(review_state)
    if poll_status_is_automation_only_refresh(raw_poll_status):
        result["Poll Status"] = poll_status_fallback
    elif _poll_status_conflicts_with_typed_mode(review_state, raw_poll_status):
        result["Poll Status"] = poll_status_fallback
    elif (
        not raw_poll_status.strip()
        and result.get("Poll Status", "").strip() == "- Reviewer state unavailable."
    ):
        result["Poll Status"] = poll_status_fallback
    else:
        _set_missing(result, "Poll Status", poll_status_fallback)
    _set_missing(
        result,
        "Current Verdict",
        _section_text(
            review_acceptance.get("current_verdict"),
            current_session.get("current_verdict"),
            default="- reviewer state unavailable",
        ),
    )
    _set_missing(
        result,
        "Open Findings",
        _section_text(
            review_acceptance.get("open_findings"),
            current_session.get("open_findings"),
            default="- none",
        ),
    )
    _set_missing(
        result,
        "Claude Status",
        _section_text(
            current_session.get("implementer_status"),
            default="- Status unavailable.",
        ),
    )
    _set_missing(result, "Claude Questions", "- None recorded.")
    _set_missing(
        result,
        "Claude Ack",
        _section_text(current_session.get("implementer_ack"), default="- missing"),
    )
    instruction_fallback = _current_instruction_fallback(review_state)
    if "current_instruction" in current_session:
        current_instruction = current_session.get("current_instruction")
        if is_missing_instruction(str(current_instruction or "")):
            current_instruction = ""
        _set_missing(
            result,
            "Current Instruction For Claude",
            _section_text(
                current_instruction,
                default=instruction_fallback,
            ),
        )
    else:
        _set_missing(
            result,
            "Current Instruction For Claude",
            instruction_fallback,
        )
    _replace_wait_placeholder_with_typed_fallback(
        result,
        instruction_fallback=instruction_fallback,
    )
    _set_missing(
        result,
        "Last Reviewed Scope",
        _section_text(
            current_session.get("last_reviewed_scope"),
            default="- (missing)",
        ),
    )
    return result


def mapping(value: object) -> Mapping[str, object]:
    return _mapping(value)


def string_mapping(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): str(item or "") for key, item in value.items()}


def tuple_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item).strip())
    return ()


def int_value(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _set_missing(sections: dict[str, str], heading: str, value: str) -> None:
    if not sections.get(heading, "").strip():
        sections[heading] = value


def _poll_status_conflicts_with_typed_mode(
    review_state: Mapping[str, object],
    poll_status: str,
) -> bool:
    typed_bridge = _mapping(review_state.get("bridge"))
    effective_mode = str(
        typed_bridge.get("effective_reviewer_mode")
        or typed_bridge.get("reviewer_mode")
        or ""
    ).strip()
    if not effective_mode:
        return False
    poll_status_modes = extract_poll_status_reviewer_modes(poll_status)
    if not poll_status_modes:
        return False
    return any(mode != effective_mode for mode in poll_status_modes)


def _poll_status_fallback(review_state: Mapping[str, object]) -> str:
    timestamp = str(review_state.get("timestamp") or "").strip()
    suffix = f" at {timestamp}" if timestamp else ""
    return "- Reviewer state rebuilt from typed review-state projection" + suffix + "."


def _current_instruction_fallback(review_state: Mapping[str, object]) -> str:
    attention = _mapping(review_state.get("attention"))
    if str(attention.get("status") or "").strip() != "checkpoint_required":
        return "- Await reviewer instruction refresh."
    command = str(
        review_state.get("recommended_command")
        or attention.get("recommended_command")
        or ""
    ).strip()
    rows = ["Cut a checkpoint before continuing to edit."]
    if command:
        rows.append(f"Run `{command}`.")
    return _section_text(rows, default="- Await reviewer instruction refresh.")


def _replace_wait_placeholder_with_typed_fallback(
    sections: dict[str, str],
    *,
    instruction_fallback: str,
) -> None:
    current_instruction = str(
        sections.get("Current Instruction For Claude") or ""
    ).strip()
    if current_instruction != "- Await reviewer instruction refresh.":
        return
    if instruction_fallback == "- Await reviewer instruction refresh.":
        return
    sections["Current Instruction For Claude"] = instruction_fallback


def _section_text(*values: object, default: str) -> str:
    for value in values:
        if isinstance(value, (list, tuple)):
            rows = [str(item).strip() for item in value if str(item).strip()]
            if rows:
                return "\n".join(
                    row if row.startswith("- ") else f"- {row}" for row in rows
                )
            continue
        text = str(value or "").strip()
        if text:
            return text
    return default


def _tracked_sections(raw_sections: Mapping[str, str]) -> dict[str, str]:
    return {
        heading: str(raw_sections.get(heading, ""))
        for heading in BRIDGE_SECTION_ORDER
    }


def _typed_section_override(value: object) -> str:
    text = str(value or "").strip()
    if text == "(missing)":
        return ""
    if not text:
        return ""
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if not any(line.lstrip().startswith("- ") for line in lines):
        return text
    normalized: list[str] = []
    seen_bullet = False
    for line in lines:
        stripped = line.strip()
        if line.lstrip().startswith("- "):
            normalized.append(line)
            seen_bullet = True
            continue
        if not seen_bullet:
            normalized.append(f"- {stripped}")
            continue
        normalized.append(line)
    return "\n".join(normalized)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
