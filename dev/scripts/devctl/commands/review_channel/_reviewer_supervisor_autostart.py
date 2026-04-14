"""Auto-start policy for the detached reviewer-supervisor follow loop."""

from __future__ import annotations

import time as _time
from collections.abc import Mapping
from pathlib import Path

from ...review_channel.lifecycle_state import read_reviewer_supervisor_state
from ...review_channel.peer_liveness import reviewer_mode_is_active
from ...runtime.governance_scan import scan_repo_governance_safely
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths
from ._publisher import spawn_reviewer_supervisor, verify_reviewer_supervisor_start
from ._supervisor_restart_policy import (
    non_restartable_reviewer_supervisor_stop_reason,
)


def _resolve_supervisor_interaction_mode(
    *,
    repo_root: Path,
    args_fallback: str = "",
) -> str:
    """Read operator interaction mode from governance typed state.

    Active remote-control attachment overrides ``local_terminal`` governance
    default so supervisor restarts inherit the live attachment mode
    (rev_pkt_0459 follow-up to rev_pkt_0448).
    """
    from ...runtime.review_state_locator import load_current_review_state_payload
    from ...runtime.reviewer_runtime_models import (
        has_active_remote_control_attachment,
        remote_control_attachment_from_mapping,
    )
    governance = scan_repo_governance_safely(repo_root)
    gov_mode = ""
    if governance is not None:
        gov_mode = (governance.bridge_config.operator_interaction_mode or "").strip()
    if gov_mode and gov_mode != "local_terminal":
        return gov_mode
    try:
        payload = load_current_review_state_payload(repo_root, governance=governance)
    except Exception:  # broad-except: allow reason=supervisor-path must not crash on state read fallback=governance default
        payload = None
    runtime = payload.get("reviewer_runtime") if isinstance(payload, dict) else None
    if isinstance(runtime, dict) and has_active_remote_control_attachment(
        remote_control_attachment_from_mapping(runtime.get("remote_control_attachment"))
    ):
        return "remote_control"
    return gov_mode or args_fallback.strip() or ""


def ensure_reviewer_supervisor_running(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    allow_follow: bool = False,
    sleep_seconds: float = 0.5,
) -> dict[str, object] | None:
    """Keep the detached reviewer supervisor alive for active reviewer mode."""
    if getattr(args, "follow", False) and not allow_follow:
        return None
    if not reviewer_mode_is_active(getattr(args, "reviewer_mode", None)):
        return None

    runtime_paths = _coerce_runtime_paths(paths)
    if runtime_paths.status_dir is None:
        return {
            "attempted": False,
            "started": False,
            "reason": "status_dir_not_resolved",
        }

    supervisor_state = read_reviewer_supervisor_state(runtime_paths.status_dir)
    if bool(supervisor_state.get("running")):
        return {"attempted": False, "started": False, "reason": "already_running"}
    blocked_reason = non_restartable_reviewer_supervisor_stop_reason(
        supervisor_state,
    )
    if blocked_reason:
        return {
            "attempted": False,
            "started": False,
            "reason": "non_restartable_stop_reason",
            "stop_reason": blocked_reason,
        }

    args_fallback = str(getattr(args, "operator_interaction_mode", "") or "").strip()
    interaction_mode = _resolve_supervisor_interaction_mode(
        repo_root=repo_root,
        args_fallback=args_fallback,
    )
    started, pid, log_path = spawn_reviewer_supervisor(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        operator_interaction_mode=interaction_mode,
    )
    if not started:
        return {
            "attempted": True,
            "started": False,
            "pid": pid,
            "log_path": log_path,
            "start_status": "spawn_failed",
        }
    _time.sleep(sleep_seconds)
    mode = str(getattr(args, "reviewer_mode", "active_dual_agent"))
    start_status = verify_reviewer_supervisor_start(
        pid=pid,
        paths=runtime_paths,
        reviewer_mode=mode,
    )
    return {
        "attempted": True,
        "started": start_status == "started",
        "pid": pid,
        "log_path": log_path,
        "start_status": start_status,
    }
