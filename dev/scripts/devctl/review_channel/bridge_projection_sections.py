"""Section helpers for bridge compatibility projections."""

from __future__ import annotations

from collections.abc import Mapping

from .action_request import render_action_requests_from_packets
from .bridge_projection_contract import BRIDGE_SECTION_ORDER


def projection_sections(
    raw_sections: Mapping[str, str],
    *,
    current_session: Mapping[str, object],
    reviewer_runtime: Mapping[str, object],
    packets: list[dict[str, object]] | None = None,
) -> dict[str, str]:
    sections = _tracked_sections(raw_sections)
    review_acceptance = _mapping(reviewer_runtime.get("review_acceptance"))
    typed_overrides = (
        (
            "Current Verdict",
            _typed_section_override(review_acceptance.get("current_verdict")),
        ),
        (
            "Open Findings",
            _typed_section_override(
                review_acceptance.get("open_findings")
                or current_session.get("open_findings")
            ),
        ),
        (
            "Claude Status",
            _typed_section_override(current_session.get("implementer_status")),
        ),
        (
            "Claude Ack",
            _typed_section_override(current_session.get("implementer_ack")),
        ),
        (
            "Current Instruction For Claude",
            _typed_section_override(current_session.get("current_instruction")),
        ),
        (
            "Last Reviewed Scope",
            _typed_section_override(current_session.get("last_reviewed_scope")),
        ),
    )
    for heading, value in typed_overrides:
        if value:
            sections[heading] = value
            continue
        if heading == "Claude Status" and "implementer_status" in current_session:
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
    current_session = _mapping(review_state.get("current_session"))
    reviewer_runtime = _mapping(review_state.get("reviewer_runtime"))
    review_acceptance = _mapping(reviewer_runtime.get("review_acceptance"))
    bridge_state = _mapping(review_state.get("bridge"))

    _set_missing(
        result,
        "Poll Status",
        _poll_status_fallback(review_state),
    )
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
    _set_missing(
        result,
        "Current Instruction For Claude",
        _section_text(
            current_session.get("current_instruction"),
            bridge_state.get("current_instruction"),
            default="- Await reviewer instruction refresh.",
        ),
    )
    _set_missing(
        result,
        "Last Reviewed Scope",
        _section_text(
            current_session.get("last_reviewed_scope"),
            bridge_state.get("last_reviewed_scope"),
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


def _poll_status_fallback(review_state: Mapping[str, object]) -> str:
    timestamp = str(review_state.get("timestamp") or "").strip()
    suffix = f" at {timestamp}" if timestamp else ""
    return "- Reviewer state rebuilt from typed review-state projection" + suffix + "."


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
