"""Bridge-contract validation helpers extracted from handoff.py."""

from __future__ import annotations

from ..runtime.review_state_semantics import is_pending_implementer_state
from .bridge_validation_acceptance import review_acceptance_projection
from .bridge_validation_poll_status import (
    extract_poll_status_reviewer_modes,
    extract_poll_status_write_context,
    poll_status_is_automation_only_refresh,
)
from .bridge_validation_stall import _implementer_completion_stall_error
from .handoff_constants import (
    GENERIC_NEXT_ACTION_MARKERS,
    IDLE_FINDING_MARKERS,
    IDLE_NEXT_ACTION_MARKERS,
    RESOLVED_VERDICT_MARKERS,
    find_suspicious_bridge_text_lines,
    _is_substantive_text,
    _RESOLVED_ECHO_RE,
)
from .peer_liveness import (
    CodexPollState,
    normalize_reviewer_mode,
    reviewer_mode_is_active,
)
_REVIEWER_OWNED_VALIDATION_SECTIONS = (
    "Current Verdict",
    "Open Findings",
    "Current Instruction For Claude",
    "Last Reviewed Scope",
)


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
    if review_acceptance_projection(snapshot)[2] and bool(
        _RESOLVED_ECHO_RE.search(current_instruction)
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
def validate_launch_bridge_state(
    snapshot,
    *,
    liveness=None,
) -> list[str]:
    """Return launch-blocking bridge errors for fresh-conductor bootstrap."""
    from .handoff import summarize_bridge_liveness as _summarize

    errors = validate_live_bridge_contract(snapshot)
    effective_liveness = liveness or _summarize(snapshot)
    pending_implementer_state = is_pending_implementer_state(
        implementer_status=snapshot.sections.get("Claude Status", ""),
        implementer_ack=snapshot.sections.get("Claude Ack", ""),
    )

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
    if not effective_liveness.claude_status_present and not pending_implementer_state:
        errors.append(
            "Missing live `Claude Status`; fresh launch requires the implementer "
            "status section before bootstrap."
        )
    if not effective_liveness.claude_ack_present and not pending_implementer_state:
        errors.append(
            "Missing live `Claude Ack`; fresh launch requires a current Claude "
            "ACK before bootstrap."
        )
    return errors
