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

    if typed_overall:
        overall_state = typed_overall
        reviewer_mode = str(bridge_block.get("reviewer_mode") or "")
        codex_poll_state = str(bridge_block.get("codex_poll_state") or "")
        claude_status_present = bool(
            str(bridge_block.get("claude_status") or "").strip()
        )
        claude_ack_present = bool(
            str(bridge_block.get("claude_ack") or "").strip()
        )
        age = bridge_block.get("last_codex_poll_age_seconds")
    else:
        snapshot = extract_bridge_snapshot(bridge_text)
        liveness = summarize_bridge_liveness(snapshot)
        overall_state = liveness.overall_state
        reviewer_mode = liveness.reviewer_mode
        codex_poll_state = liveness.codex_poll_state
        claude_status_present = liveness.claude_status_present
        claude_ack_present = liveness.claude_ack_present
        age = liveness.last_codex_poll_age_seconds

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
