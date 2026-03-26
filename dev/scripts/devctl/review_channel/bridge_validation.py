"""Bridge-contract validation helpers extracted from handoff.py."""

from __future__ import annotations

import re

from .handoff_constants import (
    GENERIC_NEXT_ACTION_MARKERS,
    IDLE_FINDING_MARKERS,
    MARKDOWN_ITEM_RE,
    IDLE_NEXT_ACTION_MARKERS,
    RESOLVED_VERDICT_MARKERS,
    find_suspicious_bridge_text_lines,
    _is_substantive_text,
    _RESOLVED_ECHO_RE,
)
from .peer_liveness import (
    CodexPollState,
    IMPLEMENTER_STALL_MARKERS,
    REVIEWER_WAIT_STATE_MARKERS,
    ReviewerMode,
    normalize_reviewer_mode,
    reviewer_mode_is_active,
)

_POLL_STATUS_REVIEWER_MODE_PATTERNS = (
    re.compile(
        r"(?i)\breviewer mode(?:\s+is(?:\s+\w+)?(?:\s+to)?|\s*:)\s*`(?P<mode>[^`]+)`"
    ),
    re.compile(r"\(mode:\s*(?P<mode>[a-z_]+)\b"),
)
_REVIEWER_OWNED_VALIDATION_SECTIONS = (
    "Current Verdict",
    "Open Findings",
    "Current Instruction For Claude",
    "Last Reviewed Scope",
)
_ACCEPTED_VERDICT_PREFIX_RE = re.compile(
    r"^(?:reviewer[- ]accepted|accepted|all\s+green|resolved)\b",
    re.IGNORECASE,
)
_CLEAR_FINDINGS_PREFIX_RE = re.compile(
    r"^(?:\(none\)|none|no\s+blockers|all\s+clear|all\s+green|resolved)\b",
    re.IGNORECASE,
)


def _normalized_bridge_lines(text: str) -> tuple[str, ...]:
    """Return non-empty bridge lines normalized for section-state checks."""
    lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        match = MARKDOWN_ITEM_RE.match(stripped)
        candidate = match.group("value").strip() if match is not None else stripped
        if candidate:
            lines.append(candidate.lower())
    return tuple(lines)


def bridge_review_accepted(snapshot) -> bool:
    """Return True only when reviewer-owned bridge sections show acceptance."""
    verdict_lines = _normalized_bridge_lines(
        snapshot.sections.get("Current Verdict", "")
    )
    if not verdict_lines:
        return False
    if _ACCEPTED_VERDICT_PREFIX_RE.match(verdict_lines[0]) is None:
        return False

    finding_lines = _normalized_bridge_lines(
        snapshot.sections.get("Open Findings", "")
    )
    return not finding_lines or all(
        _CLEAR_FINDINGS_PREFIX_RE.match(line) is not None
        for line in finding_lines
    )


def extract_poll_status_reviewer_modes(poll_status: str) -> tuple[str, ...]:
    """Return normalized reviewer modes explicitly asserted inside Poll Status."""
    seen: list[str] = []
    valid_modes = {mode.value for mode in ReviewerMode}
    for pattern in _POLL_STATUS_REVIEWER_MODE_PATTERNS:
        for match in pattern.finditer(poll_status):
            normalized = normalize_reviewer_mode(match.group("mode"))
            if normalized in valid_modes and normalized not in seen:
                seen.append(normalized)
    return tuple(seen)


def validate_live_bridge_contract(snapshot) -> list[str]:
    """Return contract errors for the minimum live bridge state."""
    from .handoff import summarize_bridge_liveness as _summarize

    errors: list[str] = []
    reviewer_mode = normalize_reviewer_mode(snapshot.metadata.get("reviewer_mode"))
    liveness = _summarize(snapshot)
    poll_status = snapshot.sections.get("Poll Status", "").strip()
    last_reviewed_scope = snapshot.sections.get("Last Reviewed Scope", "").strip()
    if not last_reviewed_scope:
        errors.append(
            "Missing live `Last Reviewed Scope`; bridge-active coordination must "
            "keep the reviewed path set current."
        )

    current_instruction = snapshot.sections.get("Current Instruction For Claude", "").strip()
    if not current_instruction:
        errors.append(
            "Missing live next action in `Current Instruction For Claude`; the "
            "bridge must always expose the current coding queue."
        )
    elif any(marker in current_instruction.lower() for marker in IDLE_NEXT_ACTION_MARKERS):
        errors.append(
            "`Current Instruction For Claude` must point at the live next task, "
            "not an idle placeholder."
        )
    elif any(
        marker in current_instruction.lower()
        for marker in GENERIC_NEXT_ACTION_MARKERS
    ):
        errors.append(
            "`Current Instruction For Claude` is generic; reviewer must promote "
            "a concrete scoped checklist item with file-targeted steps."
        )
    else:
        implementer_stall_error = _implementer_completion_stall_error(
            snapshot=snapshot,
            reviewer_mode=reviewer_mode,
        )
        if implementer_stall_error is not None:
            errors.append(implementer_stall_error)

    if (
        reviewer_mode_is_active(reviewer_mode)
        and not _is_substantive_text(poll_status)
        and not liveness.claude_ack_current
    ):
        errors.append(
            "Active `active_dual_agent` bridge requires a substantive `Poll Status` "
            "reviewer note when `Claude Ack` is stale or missing; blank or "
            "placeholder `Poll Status` is a hard live-contract error."
        )

    explicit_revision = (snapshot.metadata.get("current_instruction_revision") or "").strip()
    if reviewer_mode_is_active(reviewer_mode) and liveness.claude_ack_present:
        if not explicit_revision:
            errors.append(
                "Active bridge mode requires `Current instruction revision` metadata "
                "so Claude ACK freshness can be checked."
            )
        elif not liveness.claude_ack_revision:
            errors.append(
                "Live `Claude Ack` must include `instruction-rev: <current revision>` "
                "in active bridge mode."
            )
        elif not liveness.claude_ack_current:
            errors.append(
                "Live `Claude Ack` revision does not match the current reviewer "
                "instruction revision."
            )

    current_verdict = snapshot.sections.get("Current Verdict", "").strip().lower()
    if (
        bridge_review_accepted(snapshot)
        and bool(_RESOLVED_ECHO_RE.search(current_instruction))
    ):
        errors.append(
            "Resolved bridge verdicts must promote the next scoped task in "
            "`Current Instruction For Claude` instead of echoing a completed state."
        )

    conflicting_poll_status_modes = [
        mode
        for mode in extract_poll_status_reviewer_modes(
            snapshot.sections.get("Poll Status", "")
        )
        if mode != reviewer_mode
    ]
    if conflicting_poll_status_modes:
        errors.append(
            "Poll Status contradicts `Reviewer mode` metadata; conflicting modes: "
            + ", ".join(f"`{mode}`" for mode in conflicting_poll_status_modes)
            + f" (metadata: `{reviewer_mode}`)."
        )
    for section in _REVIEWER_OWNED_VALIDATION_SECTIONS:
        suspicious_lines = find_suspicious_bridge_text_lines(
            snapshot.sections.get(section, "")
        )
        if suspicious_lines:
            quoted = ", ".join(f"`{line}`" for line in suspicious_lines)
            errors.append(
                f"`{section}` contains suspicious terminal/status text; rewrite "
                f"the reviewer-owned bridge section before continuing: {quoted}."
            )

    return errors


def _implementer_completion_stall_error(
    *,
    snapshot,
    reviewer_mode: ReviewerMode,
) -> str | None:
    if not reviewer_mode_is_active(reviewer_mode):
        return None
    instruction = snapshot.sections.get("Current Instruction For Claude", "")
    poll_status = snapshot.sections.get("Poll Status", "")
    if _contains_any_marker(instruction, REVIEWER_WAIT_STATE_MARKERS) or _contains_any_marker(
        poll_status,
        REVIEWER_WAIT_STATE_MARKERS,
    ):
        return None
    claude_status = _leading_section_excerpt(snapshot.sections.get("Claude Status", ""))
    claude_ack = _leading_section_excerpt(snapshot.sections.get("Claude Ack", ""))
    combined = f"{claude_status}\n{claude_ack}".strip()
    if not _contains_any_marker(combined, IMPLEMENTER_STALL_MARKERS):
        return None
    return (
        "Claude Status/Ack show implementer completion-stall language while "
        "`Current Instruction For Claude` still assigns active work. Resume "
        "the active slice or record one concrete blocker/question instead of "
        "parking on reviewer polling."
    )


def _contains_any_marker(text: str, markers: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in markers)


def _leading_section_excerpt(text: str, *, max_lines: int = 12) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        lines.append(stripped)
        if len(lines) >= max_lines:
            break
    return "\n".join(lines)


def validate_launch_bridge_state(
    snapshot,
    *,
    liveness=None,
) -> list[str]:
    """Return launch-blocking bridge errors for fresh-conductor bootstrap."""
    from .handoff import summarize_bridge_liveness as _summarize

    errors = validate_live_bridge_contract(snapshot)
    effective_liveness = liveness or _summarize(snapshot)
    if not reviewer_mode_is_active(effective_liveness.reviewer_mode):
        return errors
    if effective_liveness.codex_poll_state == CodexPollState.MISSING:
        errors.append(
            "Missing `Last Codex poll`; fresh launch requires a live reviewer poll "
            "timestamp in the bridge header."
        )
    elif effective_liveness.codex_poll_state == CodexPollState.STALE:
        errors.append(
            "`Last Codex poll` is stale; fresh launch requires bridge activity "
            "within the five-minute heartbeat contract."
        )
    if not effective_liveness.claude_status_present:
        errors.append(
            "Missing live `Claude Status`; fresh launch requires the implementer "
            "status section before bootstrap."
        )
    if not effective_liveness.claude_ack_present:
        errors.append(
            "Missing live `Claude Ack`; fresh launch requires a current Claude "
            "ACK before bootstrap."
        )
    return errors
