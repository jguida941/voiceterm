"""Shared support for repo-owned stale-implementer recovery."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from ..approval_mode import normalize_approval_mode
from ..time_utils import utc_timestamp
from .handoff import extract_bridge_snapshot, summarize_bridge_liveness
from .peer_liveness import AttentionStatus, reviewer_mode_is_active

_RECOVERABLE_ATTENTION_STATUSES = frozenset(
    {
        AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED,
    }
)
_RECOVERABLE_ERROR_PREFIXES = (
    "Live `Claude Ack` must include `instruction-rev:",
    "Live `Claude Ack` revision does not match the current reviewer instruction revision.",
)


@dataclass(frozen=True)
class RecoverSessionBuildInput:
    """Inputs required to build one narrow stale-implementer relaunch."""

    args: object
    repo_root: Path
    runtime_paths: object
    status_snapshot: object
    codex_lanes: list
    claude_lanes: list


@dataclass(frozen=True)
class RecoverReportInput:
    """Inputs required to render one recover-action status report."""

    args: object
    refreshed_snapshot: object
    exit_code: int
    provider: str
    current_instruction_revision: str
    sessions: list[dict[str, object]]
    terminal_profile_applied: str | None
    launched: bool
    recover_ack_observed: dict[str, object] | None


def wait_for_claude_ack_refresh(
    *,
    bridge_path: Path,
    expected_instruction_revision: str,
    timeout_seconds: int,
    poll_interval_seconds: float = 2.0,
) -> dict[str, object]:
    """Wait until the live bridge shows a current Claude ACK for one revision."""
    deadline = time.monotonic() + max(timeout_seconds, 0)
    while True:
        snapshot = extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
        liveness = summarize_bridge_liveness(snapshot)
        observed = bool(
            expected_instruction_revision
            and liveness.claude_status_present
            and liveness.claude_ack_current
            and liveness.claude_ack_revision == expected_instruction_revision
        )
        if observed or time.monotonic() >= deadline:
            return {
                "observed": observed,
                "claude_status_present": liveness.claude_status_present,
                "claude_ack_present": liveness.claude_ack_present,
                "claude_ack_current": liveness.claude_ack_current,
                "claude_ack_revision": liveness.claude_ack_revision,
            }
        time.sleep(max(poll_interval_seconds, 0.1))


def validate_recoverable_state(
    *,
    bridge_liveness: dict[str, object],
    attention: dict[str, object],
) -> str | None:
    """Return a validation error when recover should not relaunch Claude."""
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    if not reviewer_mode_is_active(reviewer_mode):
        return "review-channel recover only runs while reviewer_mode is active_dual_agent."
    if bool(bridge_liveness.get("claude_ack_current")):
        return "review-channel recover refused because Claude Ack is already current."
    attention_status = str(attention.get("status") or "")
    if attention_status == AttentionStatus.BRIDGE_CONTRACT_ERROR.value:
        return (
            "review-channel recover refused because reviewer-owned bridge state is inconsistent. "
            "Repair reviewer sections before replacing Claude."
        )
    if attention_status in _RECOVERABLE_ATTENTION_STATUSES:
        return None
    return (
        "review-channel recover requires `implementer_relaunch_required`; "
        "let the reviewer path prove the stale implementer state before replacement."
    )


def recover_projection_errors(errors: list[str]) -> list[str]:
    """Drop stale-ACK errors that recover is intentionally replacing."""
    return [
        error
        for error in errors
        if not error.startswith(_RECOVERABLE_ERROR_PREFIXES)
    ]


def base_recover_report(args) -> dict[str, object]:
    """Build the common recover command report skeleton."""
    dangerous = bool(getattr(args, "dangerous", False))
    report: dict[str, object] = {}
    report["command"] = "review-channel"
    report["timestamp"] = utc_timestamp()
    report["action"] = getattr(args, "action", "recover")
    report["ok"] = False
    report["exit_ok"] = False
    report["exit_code"] = 1
    report["execution_mode"] = getattr(args, "execution_mode", "auto")
    report["terminal"] = getattr(args, "terminal", "terminal-app")
    report["terminal_profile_requested"] = getattr(args, "terminal_profile", None)
    report["approval_mode"] = normalize_approval_mode(
        getattr(args, "approval_mode", None),
        dangerous=dangerous,
    )
    report["dangerous"] = dangerous
    report["warnings"] = []
    report["errors"] = []
    return report


def recover_error(args, message: str) -> tuple[dict[str, object], int]:
    """Return a uniform recover command error payload."""
    report = base_recover_report(args)
    report["errors"] = [message]
    return report, 1
