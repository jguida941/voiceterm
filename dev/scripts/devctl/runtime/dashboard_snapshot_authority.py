"""Canonical DashboardSnapshot v3 contract and shared enrichers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Mapping

from ..config import REPO_ROOT
from .agent_mind_projection_read import (
    agent_mind_projection_path,
    read_agent_mind_projection,
)
from .dashboard_codex_sessions import active_codex_sessions_section


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    """Portable dashboard contract consumed by CLI, desktop, and mobile."""

    payload: Mapping[str, Any] = field(default_factory=dict)

    contract_id: ClassVar[str] = "DashboardSnapshot"
    schema_version: ClassVar[int] = 3

    def to_dict(self) -> dict[str, Any]:
        snapshot = dict(self.payload)
        snapshot["contract_id"] = self.contract_id
        snapshot["schema_version"] = self.schema_version
        return snapshot


def build_dashboard_snapshot(
    *,
    repo_root: Path = REPO_ROOT,
    view: str = "overview",
    role: str = "dashboard",
) -> dict[str, Any]:
    """Build the shared DashboardSnapshot through the CLI builder adapter."""
    from ..commands.dashboard import build_snapshot

    snapshot = build_snapshot(repo_root=repo_root, view=view, role=role)
    if (
        snapshot.get("contract_id") == DashboardSnapshot.contract_id
        and snapshot.get("schema_version") == DashboardSnapshot.schema_version
    ):
        return dict(snapshot)
    return normalize_dashboard_snapshot(
        snapshot,
        repo_root=repo_root,
    )


def normalize_dashboard_snapshot(
    snapshot: Mapping[str, Any],
    *,
    repo_root: Path = REPO_ROOT,
    review_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a v3 snapshot with the shared typed dashboard sections present."""
    payload = dict(snapshot)
    payload["contract_id"] = DashboardSnapshot.contract_id
    payload["schema_version"] = DashboardSnapshot.schema_version
    state = review_state if review_state is not None else _mapping(payload.get("review_state"))
    if not state:
        state = _mapping(payload.get("_review_state"))
    payload["agent_mind"] = _agent_mind_section(repo_root)
    payload["session_outcomes"] = _session_outcomes_section(repo_root, state)
    payload["ack_freshness"] = _ack_freshness_section(state)
    payload["session_posture"] = _session_posture_section(payload, state)
    payload["session_liveness"] = _session_liveness_section(state)
    payload["active_codex_sessions"] = active_codex_sessions_section(
        repo_root=repo_root,
        session_posture=payload.get("session_posture"),
    )
    payload["system_topology"] = _system_topology_section(repo_root)
    return payload


def _agent_mind_section(repo_root: Path) -> dict[str, Any]:
    path = agent_mind_projection_path(repo_root, provider="codex")
    payload = read_agent_mind_projection(repo_root, provider="codex")
    if not payload:
        return dict(available=False, path=_rel(path, repo_root), events=[])
    events = payload.get("events")
    if not isinstance(events, list):
        events = []
    return dict(
        available=True,
        path=_rel(path, repo_root),
        agent_provider=str(payload.get("agent_provider") or ""),
        generated_at_utc=str(payload.get("generated_at_utc") or ""),
        session_id=str(payload.get("session_id") or ""),
        event_count=int(payload.get("event_count") or len(events)),
        latest_events=[_agent_mind_event(row) for row in events[-5:]],
    )


def _agent_mind_event(row: object) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {}
    return dict(
        timestamp=str(row.get("timestamp") or ""),
        event_type=str(row.get("event_type") or ""),
        summary=str(row.get("summary") or ""),
        tool_name=str(row.get("tool_name") or ""),
        is_error=bool(row.get("is_error")),
        is_escalation=bool(row.get("is_escalation")),
    )


def _session_outcomes_section(
    repo_root: Path,
    review_state: Mapping[str, Any],
) -> dict[str, Any]:
    rows = _collaboration_session_outcomes(review_state)
    if not rows:
        try:
            from ..review_channel.agent_session_outcome_events import (
                load_agent_session_outcomes,
            )
            from ..review_channel.event_store import resolve_artifact_paths

            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            rows = [
                asdict(outcome)
                for outcome in load_agent_session_outcomes(
                    events_path=Path(artifact_paths.event_log_path)
                )
            ]
        except (OSError, ValueError):
            rows = []
    return {
        "count": len(rows),
        "latest": rows[-5:],
    }


def _collaboration_session_outcomes(review_state: Mapping[str, Any]) -> list[dict[str, Any]]:
    collaboration = _mapping(review_state.get("collaboration"))
    rows = collaboration.get("session_outcomes")
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _ack_freshness_section(review_state: Mapping[str, Any]) -> dict[str, Any]:
    current_session = _mapping(review_state.get("current_session"))
    if not current_session:
        return {"available": False, "is_current": False}
    from ..review_channel.ack_freshness_authority import (
        current_session_from_mapping,
        is_implementer_ack_current,
    )

    typed_session = current_session_from_mapping(current_session)
    return {
        "available": True,
        "is_current": is_implementer_ack_current(typed_session),
        "implementer_ack_state": typed_session.implementer_ack_state,
        "implementer_ack_revision": typed_session.implementer_ack_revision,
        "current_instruction_revision": typed_session.current_instruction_revision,
    }


def _session_posture_section(
    payload: Mapping[str, Any],
    review_state: Mapping[str, Any],
) -> dict[str, Any]:
    control_plane = _mapping(payload.get("control_plane"))
    posture = _mapping(control_plane.get("session_posture"))
    if not posture:
        posture = _mapping(_mapping(review_state.get("reviewer_runtime")).get("session_posture"))
    if not posture:
        return {"available": False}
    result = dict(posture)
    result["available"] = True
    return result


def _session_liveness_section(review_state: Mapping[str, Any]) -> dict[str, Any]:
    bridge_liveness = _mapping(review_state.get("bridge_liveness"))
    bridge = _mapping(review_state.get("bridge"))
    rows = (
        bridge_liveness.get("session_liveness_signals")
        or bridge_liveness.get("participant_liveness")
        or bridge.get("session_liveness_signals")
        or bridge.get("participant_liveness")
        or []
    )
    if not isinstance(rows, list):
        rows = []
    signals = [dict(row) for row in rows if isinstance(row, Mapping)]
    return {
        "available": bool(signals),
        "signals": signals,
    }


def _system_topology_section(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "dev/guides/SYSTEM_MAP.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        text = ""
    return {
        "path": _rel(path, repo_root),
        "generated_block_present": "<!-- BEGIN DEVCTL_SYSTEM_MAP_GENERATED -->" in text,
        "snapshot_builder_debt_mentioned": "Three parallel snapshot builders" in text
        or "System snapshot 3 builders" in text,
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


__all__ = [
    "DashboardSnapshot",
    "build_dashboard_snapshot",
    "normalize_dashboard_snapshot",
]
