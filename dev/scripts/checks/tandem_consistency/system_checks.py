"""System-owned tandem-consistency checks."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.handoff import (
    extract_bridge_snapshot,
    summarize_bridge_liveness,
)
from dev.scripts.devctl.review_channel.peer_liveness import (
    CODEX_POLL_STALE_AFTER_SECONDS,
    reviewer_mode_is_active,
)

from .support import skip_live_freshness

_TANDEM_GUARD_STALE_THRESHOLD = CODEX_POLL_STALE_AFTER_SECONDS + 300


def check_launch_truth(bridge_text: str) -> dict[str, object]:
    """Verify bridge liveness signals are internally consistent."""
    snapshot = extract_bridge_snapshot(bridge_text)
    liveness = summarize_bridge_liveness(snapshot)
    overall_state = liveness.overall_state
    reviewer_mode = liveness.reviewer_mode
    codex_poll_state = liveness.codex_poll_state
    claude_status_present = liveness.claude_status_present
    claude_ack_present = liveness.claude_ack_present

    if not reviewer_mode_is_active(reviewer_mode):
        return {
            "check": "launch_truth",
            "role": "system",
            "ok": True,
            "overall_state": overall_state,
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
    age = liveness.last_codex_poll_age_seconds
    genuinely_stale = (
        age is not None and age > _TANDEM_GUARD_STALE_THRESHOLD
    ) and not skip_live_freshness()
    if genuinely_stale:
        issues.append(f"Overall bridge state is {overall_state}.")
    if codex_poll_state == "missing":
        issues.append("Reviewer poll state is missing.")
    if not claude_status_present:
        issues.append("Implementer status is not visible in bridge.")
    if not claude_ack_present:
        issues.append("Implementer ACK is not visible in bridge.")

    return {
        "check": "launch_truth",
        "role": "system",
        "ok": len(issues) == 0,
        "overall_state": overall_state,
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
