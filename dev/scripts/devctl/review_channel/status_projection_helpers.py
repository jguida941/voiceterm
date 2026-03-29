"""Helpers extracted from status_projection to stay under code-shape limits."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .daemon_reducer import DaemonSnapshot, empty_daemon_state
from .core import active_conductor_providers
from .peer_liveness import (
    CodexPollState,
    OverallLivenessState,
    ReviewerFreshness,
    reviewer_mode_is_active,
)
from .session_state_hints import provider_session_state_hint
from ..governance.push_policy import load_push_policy
from ..governance.push_state import PushEnforcementSnapshot, detect_push_enforcement_state


def build_bridge_runtime(
    bridge_liveness: dict[str, object],
    reduced_runtime: dict[str, object] | None,
) -> dict[str, object]:
    """Build the runtime section, preferring event-reduced state when available."""
    if reduced_runtime and reduced_runtime.get("last_daemon_event_utc"):
        return reduced_runtime

    publisher_running = bool(bridge_liveness.get("publisher_running"))
    pub = DaemonSnapshot()
    pub.reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    pub.stop_reason = str(bridge_liveness.get("publisher_stop_reason") or "")

    return {
        "daemons": {
            "publisher": (
                pub.to_dict()
                if not publisher_running
                else _running_bridge_publisher(bridge_liveness)
            ),
            "reviewer_supervisor": empty_daemon_state(),
        },
        "active_daemons": 1 if publisher_running else 0,
        "last_daemon_event_utc": "",
    }


def build_bridge_push_enforcement_state(repo_root: Path) -> dict[str, object]:
    """Load the repo-governance push/checkpoint state for bridge projections."""
    try:
        policy = load_push_policy(repo_root=repo_root)
        return detect_push_enforcement_state(policy, repo_root=repo_root)
    except (OSError, ValueError):
        return asdict(
            PushEnforcementSnapshot(
                current_branch="",
                current_head_commit="",
                default_remote="origin",
                development_branch="main",
                release_branch="main",
                pre_push_hook_path="",
                pre_push_hook_installed=False,
                raw_git_push_guarded=False,
                upstream_ref="",
                ahead_of_upstream_commits=None,
                dirty_path_count=0,
                untracked_path_count=0,
                max_dirty_paths_before_checkpoint=12,
                max_untracked_paths_before_checkpoint=6,
                checkpoint_required=False,
                safe_to_continue_editing=True,
                checkpoint_reason="clean_worktree",
                worktree_dirty=False,
                worktree_clean=True,
                recommended_action="use_devctl_push",
            )
        )


def _running_bridge_publisher(
    bridge_liveness: dict[str, object],
) -> dict[str, object]:
    """Build a publisher daemon dict from bridge liveness when running."""
    pub = DaemonSnapshot()
    pub.pid = 1
    pub.started_at_utc = "(bridge-derived)"
    pub.last_heartbeat_utc = "(bridge-derived)"
    pub.reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    return pub.to_dict()


def clean_section(raw: str) -> str:
    return raw.strip() or "(missing)"


def bridge_liveness_warnings(bridge_liveness: dict[str, object]) -> list[str]:
    warnings: list[str] = []
    codex_poll_state = str(bridge_liveness.get("codex_poll_state") or "unknown")
    reviewer_freshness = str(bridge_liveness.get("reviewer_freshness") or "")
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    if not reviewer_mode_is_active(reviewer_mode):
        warnings.append(
            "Bridge reviewer mode is inactive; live heartbeat freshness is not enforced until the reviewer resumes active_dual_agent mode."
        )
    elif overall_state == OverallLivenessState.RUNTIME_MISSING:
        warnings.append(
            "Reviewer runtime is missing while `active_dual_agent` is still declared. The daemon is treated as missing runtime, not as authority to pause the loop."
        )
    elif reviewer_freshness == ReviewerFreshness.MISSING or codex_poll_state == CodexPollState.MISSING:
        warnings.append(
            "Bridge liveness is missing: the bridge header does not expose a usable `Last Codex poll` timestamp yet."
        )
    elif reviewer_freshness == ReviewerFreshness.OVERDUE:
        warnings.append(
            "Bridge liveness is overdue: the latest Codex poll timestamp has exceeded the controller escalation threshold."
        )
    elif reviewer_freshness == ReviewerFreshness.STALE or codex_poll_state == CodexPollState.STALE:
        warnings.append(
            "Bridge liveness is stale: the latest Codex poll timestamp is older than the five-minute heartbeat contract."
        )
    elif reviewer_freshness == ReviewerFreshness.POLL_DUE or codex_poll_state == CodexPollState.POLL_DUE:
        warnings.append(
            "Bridge liveness is due for refresh: the latest Codex poll timestamp is older than the 2-3 minute reviewer cadence but still within the five-minute heartbeat window."
        )
    elif overall_state == OverallLivenessState.WAITING_ON_PEER:
        warnings.append(
            "Bridge liveness is waiting_on_peer: the current bridge state still needs a fresh reviewer poll or complete Claude status/ACK state before the next cycle."
        )
    if bridge_liveness.get("reviewed_hash_current") is False:
        warnings.append(
            "Bridge review content is stale: the worktree has changed since the last reviewed hash. Current Verdict, Open Findings, and Current Instruction may not reflect the current tree state."
        )
    claude_hint = provider_session_state_hint(bridge_liveness, provider="claude")
    if claude_hint:
        warnings.append(str(claude_hint.get("summary") or "Claude session hint detected."))
    return warnings


def attach_conductor_session_state(
    *,
    bridge_liveness: dict[str, object],
    output_root: Path,
) -> None:
    active_providers = active_conductor_providers(session_output_root=output_root)
    bridge_liveness["active_conductor_providers"] = list(active_providers)
    bridge_liveness["codex_conductor_active"] = "codex" in active_providers
    bridge_liveness["claude_conductor_active"] = "claude" in active_providers


def hybrid_loop_errors(bridge_liveness: dict[str, object]) -> list[str]:
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    if not reviewer_mode_is_active(reviewer_mode):
        return []
    codex_conductor_active = bool(bridge_liveness.get("codex_conductor_active"))
    claude_conductor_active = bool(bridge_liveness.get("claude_conductor_active"))
    publisher_running = bool(bridge_liveness.get("publisher_running"))
    reviewer_supervisor_running = bool(
        bridge_liveness.get("reviewer_supervisor_running")
    )
    if (
        not codex_conductor_active
        and not claude_conductor_active
        and (publisher_running or reviewer_supervisor_running)
    ):
        return [
            "Reviewer mode is `active_dual_agent` but no live repo-owned Codex or "
            "Claude conductor sessions are present. Do not trust detached "
            "publisher/supervisor heartbeats as proof the review loop is live; "
            "relaunch with `review-channel --action launch` or "
            "`review-channel --action rollover` before continuing."
        ]
    if not claude_conductor_active:
        return []
    if codex_conductor_active and bool(
        bridge_liveness.get("poll_status_automation_only")
    ):
        reason = str(bridge_liveness.get("poll_status_reason") or "unknown")
        return [
            "Repo-owned Codex conductor sessions are present, but the latest "
            "reviewer poll still comes from automation-only heartbeat refresh "
            f"(`{reason}`) rather than a reviewer-owned turn. Do not treat the "
            "live loop as started until `Poll Status` advances through a real "
            "Codex reviewer action."
        ]
    if codex_conductor_active:
        return []
    return [
        "Repo-owned Claude conductor is active but no live repo-owned Codex conductor session is present. Hybrid chat/terminal review loops are not trusted; relaunch with `review-channel --action launch` or `review-channel --action rollover` instead of relying on Claude-only recover."
    ]
