"""Shared support for repo-owned stale-implementer recovery."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from ..approval_mode import normalize_approval_mode
from ..runtime.role_profile import TandemRole
from ..time_utils import utc_timestamp
from .ack_contract import ACK_REVISION_REQUIREMENT_PREFIX
from .core import active_conductor_providers
from .handoff import extract_bridge_snapshot, summarize_bridge_liveness
from .peer_liveness import AttentionStatus, reviewer_mode_is_active
from .state import refresh_status_snapshot

_RECOVERABLE_ATTENTION_STATUSES = frozenset(
    {
        AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED,
    }
)
_RECOVERABLE_ERROR_PREFIXES = (
    ACK_REVISION_REQUIREMENT_PREFIX,
    "Live `Claude Ack` revision does not match the current reviewer instruction revision.",
    "Claude Status/Ack show implementer completion-stall language while ",
)


@dataclass(frozen=True)
class RecoverSessionBuildInput:
    """Inputs required to build one narrow stale-implementer relaunch."""

    args: object
    repo_root: Path
    runtime_paths: object
    status_snapshot: object
    reviewer_provider: str
    recover_provider: str
    provider_lane_map: dict[str, list]


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


def validate_recover_runtime_paths(runtime_paths: object) -> str | None:
    """Return an error when recover is missing required repo-owned paths."""
    bridge_path = getattr(runtime_paths, "bridge_path", None)
    review_channel_path = getattr(runtime_paths, "review_channel_path", None)
    status_dir = getattr(runtime_paths, "status_dir", None)
    if not isinstance(bridge_path, Path) or not isinstance(review_channel_path, Path):
        return "review-channel recover requires resolved bridge and review-channel paths."
    if not isinstance(status_dir, Path):
        return "review-channel recover requires a resolved status-dir path."
    return None


def resolve_recover_provider(args) -> str | None:
    """Normalize the requested recover provider."""
    provider = str(getattr(args, "recover_provider", "claude") or "claude").strip().lower()
    if provider not in {"claude", "codex", "cursor"}:
        return None
    return provider


def validate_live_reviewer_session_for_recover(
    *,
    status_dir: Path,
    reviewer_provider: str,
    recover_provider: str,
) -> str | None:
    """Fail closed unless the current reviewer conductor is already live."""
    active_providers = active_conductor_providers(session_output_root=status_dir)
    if reviewer_provider in active_providers:
        return None
    return (
        f"review-channel recover requires a live repo-owned {reviewer_provider.title()} conductor session. "
        f"The current state would create a hybrid loop ({recover_provider.title()} in Terminal, "
        f"{reviewer_provider.title()} in chat). "
        "Relaunch the pair with `review-channel --action launch` or "
        "`review-channel --action rollover` instead of relying on implementer-only recover."
    )


def refresh_recover_snapshot(
    *,
    args,
    repo_root: Path,
    runtime_paths: object,
):
    """Refresh the review-channel status snapshot for recover flows."""
    bridge_path = getattr(runtime_paths, "bridge_path", None)
    review_channel_path = getattr(runtime_paths, "review_channel_path", None)
    status_dir = getattr(runtime_paths, "status_dir", None)
    assert isinstance(bridge_path, Path)
    assert isinstance(review_channel_path, Path)
    assert isinstance(status_dir, Path)
    return refresh_status_snapshot(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=status_dir,
        promotion_plan_path=getattr(runtime_paths, "promotion_plan_path", None),
        execution_mode=getattr(args, "execution_mode", "markdown-bridge"),
        warnings=[],
        errors=[],
        reviewer_overdue_threshold_seconds=getattr(
            args, "reviewer_overdue_seconds", None
        ),
    )


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
    if attention_status == AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value:
        return (
            "review-channel recover refused because the live dual-agent loop itself is not "
            "trusted. Relaunch the repo-owned Codex and Claude conductors instead of "
            "replacing Claude only."
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


def planned_provider_for_role(
    lanes: list,
    *,
    role: TandemRole,
    default: str,
) -> str:
    """Return the provider assigned to the requested planned role."""
    for lane in lanes:
        if str(getattr(lane, "role", "") or "").strip() == role.value:
            provider = str(getattr(lane, "provider", "") or "").strip().lower()
            return provider or default
    return default


def has_role_lanes(lanes: list, *, role: TandemRole) -> bool:
    """Return True when the lane set contains at least one planned role."""
    return any(str(getattr(lane, "role", "") or "").strip() == role.value for lane in lanes)


def recover_worker_budget(*, args, provider: str, lane_count: int) -> int:
    """Clamp requested worker budget to the available planned lanes."""
    if provider == "codex":
        requested = getattr(args, "codex_workers", 0)
    elif provider == "claude":
        requested = getattr(args, "claude_workers", 0)
    else:
        requested = getattr(args, "cursor_workers", 0)
    return min(int(requested or 0), lane_count)


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
