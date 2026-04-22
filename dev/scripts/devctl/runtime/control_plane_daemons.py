"""Daemon and conductor liveness helpers for control-plane resolution."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .role_profile import (
    TandemRole,
    default_provider_for_role,
    normalize_tandem_role,
)
from .reviewer_runtime_models import (
    has_active_remote_control_attachment,
    remote_control_attachment_from_mapping,
)


def resolve_daemon_state(sources: dict[str, Any]) -> dict[str, Any]:
    """Derive publisher/supervisor/conductor liveness from typed authority."""
    authority = _typed_authority_payload(sources)
    doctor = _typed_doctor(authority)
    bridge = _typed_bridge(authority)

    pub_running = _resolve_daemon_running(
        sources.get("publisher_hb"),
        _bool_or_none(doctor.get("publisher_running")),
        _bool_or_none(bridge.get("publisher_running")),
    )
    sup_running = _resolve_daemon_running(
        sources.get("supervisor_hb"),
        _bool_or_none(doctor.get("reviewer_supervisor_running")),
        _bool_or_none(bridge.get("reviewer_supervisor_running")),
    )
    codex_alive = _coalesce_bool(
        _single_agent_remote_attachment_activity(
            authority=authority,
            target_provider="codex",
        ),
        _single_agent_local_reviewer_activity(
            authority=authority,
            sources=sources,
            target_provider="codex",
        ),
        _bool_or_none(bridge.get("codex_conductor_active")),
        _is_conductor_alive(sources.get("codex_conductor")),
    )
    claude_alive = _coalesce_bool(
        _single_agent_remote_attachment_activity(
            authority=authority,
            target_provider="claude",
        ),
        _single_agent_local_reviewer_activity(
            authority=authority,
            sources=sources,
            target_provider="claude",
        ),
        _bool_or_none(bridge.get("claude_conductor_active")),
        _is_conductor_alive(sources.get("claude_conductor")),
    )
    return {
        "publisher_running": pub_running,
        "supervisor_running": sup_running,
        "codex_conductor_alive": codex_alive,
        "claude_conductor_alive": claude_alive,
    }


def load_conductor_sources(paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    from ..review_channel.session_probe import load_conductor_sessions

    session_output_root = paths["codex_conductor"].parent.parent
    records = load_conductor_sessions(session_output_root=session_output_root)
    sources: dict[str, dict[str, Any]] = {}
    for record in records:
        if record.session_pid is None and not record.live:
            continue
        sources[record.provider] = {
            "provider": record.provider,
            "session_pid": record.session_pid,
            "live": record.live,
            "script_path": record.script_path,
        }
    return sources


def _typed_authority_payload(sources: dict[str, Any]) -> dict[str, Any]:
    """Return the best typed review-state payload available in ``sources``."""
    review_state = sources.get("review_state")
    if isinstance(review_state, dict):
        return review_state
    full_json = sources.get("full_json")
    if not isinstance(full_json, dict):
        return {}
    nested_review_state = full_json.get("review_state")
    if isinstance(nested_review_state, dict):
        return nested_review_state
    return full_json


def _typed_doctor(authority: dict[str, Any]) -> dict[str, Any]:
    """Extract the typed doctor surface from a review-state-like payload."""
    reviewer_runtime = authority.get("reviewer_runtime")
    if isinstance(reviewer_runtime, dict):
        doctor = reviewer_runtime.get("doctor")
        if isinstance(doctor, dict):
            return doctor
    doctor = authority.get("doctor")
    if isinstance(doctor, dict):
        return doctor
    compat = authority.get("_compat")
    if isinstance(compat, dict):
        compat_doctor = compat.get("doctor")
        if isinstance(compat_doctor, dict):
            return compat_doctor
    return {}


def _typed_bridge(authority: dict[str, Any]) -> dict[str, Any]:
    """Extract the typed bridge surface from a review-state-like payload."""
    bridge = authority.get("bridge")
    return bridge if isinstance(bridge, dict) else {}


def _single_agent_local_reviewer_activity(
    *,
    authority: dict[str, Any],
    sources: dict[str, Any],
    target_provider: str,
) -> bool | None:
    """Treat fresh local reviewer packet activity as live single-agent truth."""
    bridge = _typed_bridge(authority)
    reviewer_mode = str(bridge.get("reviewer_mode") or "").strip()
    if reviewer_mode != "single_agent":
        return None
    reviewer_provider = _reviewer_provider(authority)
    if reviewer_provider != target_provider:
        return None
    session_output_root = sources.get("session_output_root")
    if not isinstance(session_output_root, Path):
        return None
    from ..review_channel import collaboration_session

    collaboration_session._sync_local_reviewer_test_hooks()
    if collaboration_session._local_reviewer_activity_is_fresh(
        reviewer_provider=target_provider,
        session_output_root=session_output_root,
    ):
        return True
    return None


def _single_agent_remote_attachment_activity(
    *,
    authority: dict[str, Any],
    target_provider: str,
) -> bool | None:
    """Treat an attached remote-control provider as live single-agent truth."""
    bridge = _typed_bridge(authority)
    reviewer_mode = str(bridge.get("reviewer_mode") or "").strip()
    if reviewer_mode != "single_agent":
        return None
    reviewer_runtime = authority.get("reviewer_runtime")
    if not isinstance(reviewer_runtime, dict):
        return None
    attachment = remote_control_attachment_from_mapping(
        reviewer_runtime.get("remote_control_attachment")
    )
    if not has_active_remote_control_attachment(attachment):
        return None
    if normalize_tandem_role(getattr(attachment, "role", "")) == TandemRole.OPERATOR:
        return None
    provider = str(attachment.provider or "").strip().lower()
    if provider != target_provider:
        return None
    return True


def _reviewer_provider(authority: dict[str, Any]) -> str:
    """Return the current reviewer provider when the typed state names one."""
    collaboration = authority.get("collaboration")
    if isinstance(collaboration, dict):
        provider = str(collaboration.get("review_agent") or "").strip().lower()
        if provider:
            return provider
    reviewer_runtime = authority.get("reviewer_runtime")
    if isinstance(reviewer_runtime, dict):
        session_owner = reviewer_runtime.get("session_owner")
        if isinstance(session_owner, dict):
            provider = str(session_owner.get("provider") or "").strip().lower()
            if provider:
                return provider
    bridge = _typed_bridge(authority)
    capability = bridge.get("reviewer_capability")
    if isinstance(capability, dict):
        provider = str(capability.get("provider") or "").strip().lower()
        if provider:
            return provider
    return default_provider_for_role(TandemRole.REVIEWER)


def _bool_or_none(value: Any) -> bool | None:
    """Return a bool when the source is typed, else ``None``."""
    return value if isinstance(value, bool) else None


def _coalesce_bool(*values: bool | None) -> bool:
    """Return the first non-``None`` bool, defaulting false."""
    for value in values:
        if value is not None:
            return value
    return False


def _resolve_daemon_running(
    heartbeat: dict[str, Any] | None,
    *fallbacks: bool | None,
) -> bool:
    """Prefer OS-backed heartbeat truth over projected booleans.

    Review-state / bridge booleans are compatibility projections that can lag
    behind the real daemon lifecycle. When a heartbeat artifact exists, treat
    it as authoritative and fail closed on any stale or dead PID. Only fall
    back to projected booleans when no heartbeat artifact is available.
    """
    if heartbeat is not None:
        return _is_daemon_running(heartbeat)
    return _coalesce_bool(*fallbacks)


def _is_daemon_running(data: dict[str, Any] | None) -> bool:
    if data is None:
        return False
    if bool(data.get("stopped_at_utc", "")):
        return False
    pid = data.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        return False
    return pid_is_alive(pid)


def _is_conductor_alive(data: dict[str, Any] | None) -> bool:
    if data is None:
        return False
    live = data.get("live")
    if isinstance(live, bool):
        return live
    pid = data.get("session_pid")
    if not isinstance(pid, int) or pid <= 0:
        return False
    return pid_is_alive(pid)


def pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OSError):
        return False
