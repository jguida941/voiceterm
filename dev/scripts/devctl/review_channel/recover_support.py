"""Shared support for repo-owned stale-implementer recovery."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from ..approval_mode import normalize_approval_mode
from ..runtime.role_profile import TandemRole
from ..time_utils import utc_timestamp
from .ack_contract import ACK_REVISION_REQUIREMENT_PREFIX
from .conductor_authority import normalize_provider_names
from .core import active_conductor_providers
from .handoff import extract_bridge_snapshot, summarize_bridge_liveness
from .peer_liveness import AttentionStatus, reviewer_mode_is_active
from .projection_bundle import projection_paths_to_dict
from .state import refresh_status_snapshot

_RECOVERABLE_ATTENTION_STATUSES = frozenset(
    {
        AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED,
    }
)
_RECOVERABLE_ERROR_PREFIXES = (
    ACK_REVISION_REQUIREMENT_PREFIX,
    "Live implementer ACK (`Claude Ack` compatibility heading) revision does not match the current reviewer instruction revision.",
    "Implementer status/ack compatibility sections (`Claude Status` / ",
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
    launch_warnings: list[str]


@dataclass(frozen=True)
class RecoverLaunchInput:
    """Inputs required to launch one recover-session attempt."""

    args: object
    repo_root: Path
    bridge_path: Path
    current_instruction_revision: str
    sessions: list[dict[str, object]]
    terminal_profile_applied: str | None
    interaction_mode: str
    artifact_paths: object | None = None


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
    if reviewer_provider in normalize_provider_names(active_providers):
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
        return (
            "review-channel recover refused because the implementer ACK "
            "(`Claude Ack` compatibility heading) is already current."
        )
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


def invalid_recover_state_report(
    *,
    args,
    status_snapshot,
    validation_error: str,
    provider: str,
) -> tuple[dict[str, object], int]:
    """Render one invalid recover-state report."""
    report = base_recover_report(args)
    report["bridge_active"] = True
    report["bridge_liveness"] = status_snapshot.bridge_liveness
    report["attention"] = status_snapshot.attention
    report["warnings"] = status_snapshot.warnings
    report["errors"] = [validation_error]
    report["recover_provider"] = provider
    report["sessions"] = []
    return report, 1


def recover_report(
    report_input: RecoverReportInput,
) -> dict[str, object]:
    """Render the final recover-action status report."""
    args = report_input.args
    refreshed_snapshot = report_input.refreshed_snapshot
    exit_code = report_input.exit_code
    provider = report_input.provider
    current_instruction_revision = report_input.current_instruction_revision
    sessions = report_input.sessions
    terminal_profile_applied = report_input.terminal_profile_applied
    launched = report_input.launched
    recover_ack_observed = report_input.recover_ack_observed
    launch_warnings = report_input.launch_warnings
    report = base_recover_report(args)
    report["ok"] = exit_code == 0
    report["exit_ok"] = exit_code == 0
    report["exit_code"] = exit_code
    report["bridge_active"] = True
    report["bridge_liveness"] = refreshed_snapshot.bridge_liveness
    report["attention"] = refreshed_snapshot.attention
    report["warnings"] = list(refreshed_snapshot.warnings) + list(launch_warnings)
    report["errors"] = recover_projection_errors(refreshed_snapshot.errors)
    report["projection_paths"] = projection_paths_to_dict(
        refreshed_snapshot.projection_paths
    )
    report["reviewer_worker"] = refreshed_snapshot.reviewer_worker
    report["service_identity"] = refreshed_snapshot.service_identity
    report["attach_auth_policy"] = refreshed_snapshot.attach_auth_policy
    report["recover_provider"] = provider
    report["recover_target_revision"] = current_instruction_revision
    report["sessions"] = sessions
    report["terminal_profile_applied"] = terminal_profile_applied
    report["launched"] = launched
    report["recover_ack_observed"] = recover_ack_observed
    if exit_code != 0 and recover_ack_observed is not None:
        report["errors"].append(
            f"Fresh {provider.title()} conductor did not write a current ACK before the recovery timeout expired."
        )
    return report


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
