"""System-owned tandem-consistency checks."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.handoff import (
    extract_bridge_snapshot,
    summarize_bridge_liveness,
)
from dev.scripts.devctl.review_channel.bridge_heading_aliases import bridge_section_text
from dev.scripts.devctl.review_channel.launch_truth import (
    LaunchTruthState,
    classify_launch_truth,
)
from dev.scripts.devctl.review_channel.peer_liveness import (
    CODEX_POLL_STALE_AFTER_SECONDS,
    reviewer_mode_is_active,
)
from dev.scripts.devctl.runtime.review_state_semantics import (
    is_missing_instruction,
    is_pending_placeholder,
)

from .support import skip_live_freshness

_TANDEM_GUARD_STALE_THRESHOLD = CODEX_POLL_STALE_AFTER_SECONDS + 300


def check_launch_truth(
    bridge_text: str,
    *,
    typed_state: dict[str, object] | None = None,
) -> dict[str, object]:
    """Verify bridge liveness signals are internally consistent.

    When typed review_state.json is available, reads overall_state,
    reviewer_mode, codex_poll_state, and presence flags from the typed
    bridge block instead of re-parsing bridge prose via
    extract_bridge_snapshot/summarize_bridge_liveness.
    """
    bridge_block = (typed_state or {}).get("bridge") or {}
    typed_overall = str(bridge_block.get("overall_state") or "").strip()
    typed_launch_truth = str(bridge_block.get("launch_truth") or "").strip()
    snapshot = extract_bridge_snapshot(bridge_text)
    bridge_claude_status = bridge_section_text(snapshot.sections, "Implementer Status")
    bridge_claude_ack = bridge_section_text(snapshot.sections, "Implementer Ack")

    if typed_overall:
        overall_state = typed_overall
        reviewer_mode = str(bridge_block.get("reviewer_mode") or "")
        codex_poll_state = str(bridge_block.get("codex_poll_state") or "")
        current_instruction = str(
            ((typed_state or {}).get("current_session") or {}).get("current_instruction")
            or bridge_block.get("current_instruction")
            or ""
        ).strip()
        claude_status_present = _section_visible(
            str(bridge_block.get("claude_status") or "").strip(),
            bridge_claude_status,
        )
        claude_ack_present = _section_visible(
            str(bridge_block.get("claude_ack") or "").strip(),
            bridge_claude_ack,
        )
        age = bridge_block.get("last_codex_poll_age_seconds")
        launch_truth = typed_launch_truth or classify_launch_truth(
            {
                "reviewer_mode": reviewer_mode,
                "publisher_running": bridge_block.get("publisher_running"),
                "reviewer_supervisor_running": bridge_block.get(
                    "reviewer_supervisor_running"
                ),
                "codex_conductor_active": bridge_block.get("codex_conductor_active"),
                "claude_conductor_active": bridge_block.get("claude_conductor_active"),
                "poll_status_automation_only": bridge_block.get(
                    "poll_status_automation_only"
                ),
            }
        ).value
    else:
        liveness = summarize_bridge_liveness(snapshot)
        overall_state = liveness.overall_state
        reviewer_mode = liveness.reviewer_mode
        codex_poll_state = liveness.codex_poll_state
        current_instruction = str(
            bridge_section_text(snapshot.sections, "Current Instruction For Implementer")
            or ""
        ).strip()
        claude_status_present = liveness.claude_status_present
        claude_ack_present = liveness.claude_ack_present
        age = liveness.last_codex_poll_age_seconds
        launch_truth = ""

    if not reviewer_mode_is_active(reviewer_mode):
        return {
            "check": "launch_truth",
            "role": "system",
            "ok": True,
            "overall_state": overall_state,
            "launch_truth": launch_truth,
            "reviewer_mode": reviewer_mode,
            "codex_poll_state": codex_poll_state,
            "claude_status_present": claude_status_present,
            "claude_ack_present": claude_ack_present,
            "issues": [],
            "detail": (
                f"Launch truth is inactive because reviewer mode is `{reviewer_mode}`."
            ),
        }

    issues: list[str] = []
    implementer_visibility_required = not is_missing_instruction(current_instruction)
    genuinely_stale = (
        age is not None and age > _TANDEM_GUARD_STALE_THRESHOLD
    ) and not skip_live_freshness()
    if genuinely_stale:
        issues.append(f"Overall bridge state is {overall_state}.")
    if codex_poll_state == "missing":
        issues.append("Reviewer poll state is missing.")
    if implementer_visibility_required and not claude_status_present:
        issues.append("Implementer status is not visible in bridge.")
    if implementer_visibility_required and not claude_ack_present:
        issues.append("Implementer ACK is not visible in bridge.")
    if launch_truth == LaunchTruthState.DETACHED_RUNTIME_ONLY.value:
        issues.append("No live repo-owned Codex or Claude conductor sessions are present.")
    elif launch_truth == LaunchTruthState.HYBRID_CLAUDE_ONLY.value:
        issues.append("Only the Claude conductor is live; relaunch the repo-owned conductor pair.")
    elif launch_truth == LaunchTruthState.AUTOMATION_ONLY.value:
        issues.append("Reviewer poll still comes from automation-only heartbeat refresh.")

    return {
        "check": "launch_truth",
        "role": "system",
        "ok": len(issues) == 0,
        "overall_state": overall_state,
        "launch_truth": launch_truth,
        "codex_poll_state": codex_poll_state,
        "claude_status_present": claude_status_present,
        "claude_ack_present": claude_ack_present,
        "issues": issues,
        "detail": (
            "Launch truth is consistent."
            if not issues
            else f"Launch truth issues: {'; '.join(issues)}"
        ),
    }


def _section_visible(typed_value: str, bridge_value: str) -> bool:
    """Return True when typed or live bridge text proves section visibility."""
    if typed_value.strip():
        return True
    if is_pending_placeholder(bridge_value):
        return True
    return bool(bridge_value.strip())
