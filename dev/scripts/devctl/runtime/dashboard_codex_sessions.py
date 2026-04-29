"""Codex session rows for DashboardSnapshot."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


def active_codex_sessions_section(
    *,
    repo_root: Path,
    session_posture: object = None,
) -> dict[str, Any]:
    """Return active Codex sessions, preferring typed posture liveness."""
    codex_sessions = _legacy_codex_sessions(repo_root)
    codex_sessions = _merge_codex_posture_sessions(
        codex_sessions,
        session_posture=session_posture,
    )
    return {
        "count": len(codex_sessions),
        "live_count": sum(1 for session in codex_sessions if session.get("live")),
        "sessions": codex_sessions,
    }


def _legacy_codex_sessions(repo_root: Path) -> list[dict[str, Any]]:
    try:
        from ..review_channel.event_store import resolve_artifact_paths
        from ..review_channel.session_probe import load_conductor_sessions

        artifact_paths = resolve_artifact_paths(repo_root=repo_root)
        sessions = load_conductor_sessions(
            session_output_root=Path(artifact_paths.projections_root)
        )
    except (OSError, ValueError):
        sessions = ()
    return [
        dict(
            provider=session.provider,
            role=session.role,
            session_name=session.session_name,
            live=session.live,
            age_seconds=session.age_seconds,
            live_reason=session.live_reason,
            metadata_path=session.metadata_path,
            workspace_root=session.workspace_root,
            prepared_head_sha=session.prepared_head_sha,
            prepared_instruction_revision=session.prepared_instruction_revision,
        )
        for session in sessions
        if session.provider == "codex"
    ]


def _merge_codex_posture_sessions(
    codex_sessions: list[dict[str, Any]],
    *,
    session_posture: object,
) -> list[dict[str, Any]]:
    posture = _mapping(session_posture)
    actors = posture.get("actors")
    if not isinstance(actors, list):
        return codex_sessions
    rows = list(codex_sessions)
    seen = {str(row.get("session_name") or row.get("source") or "") for row in rows}
    for actor in actors:
        if not isinstance(actor, Mapping):
            continue
        if str(actor.get("provider") or actor.get("actor_id") or "") != "codex":
            continue
        key = f"session_posture:{actor.get('actor_id') or 'codex'}"
        if key in seen:
            continue
        rows.append(_posture_session_row(actor, key=key))
    return rows


def _posture_session_row(actor: Mapping[str, object], *, key: str) -> dict[str, Any]:
    return {
        "provider": "codex",
        "role": str(actor.get("role") or ""),
        "session_name": key,
        "live": bool(actor.get("live")),
        "age_seconds": int(actor.get("activity_age_seconds") or 0),
        "live_reason": "SessionPosture actor liveness",
        "metadata_path": "",
        "workspace_root": "",
        "prepared_head_sha": "",
        "prepared_instruction_revision": "",
        "source": "session_posture",
        "current_activity": str(actor.get("current_activity") or "waiting"),
        "current_target": str(actor.get("current_target") or ""),
    }


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
