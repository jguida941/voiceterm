"""Session-detection helpers extracted from review_channel.core."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .launch_authority import assess_prepared_launch_authority
from .session_liveness import SessionLivenessEvidence, build_session_liveness_evidence

ACTIVE_SESSION_FRESHNESS_SECONDS = 120


@dataclass(frozen=True)
class ActiveSessionConflict:
    """One repo-visible session artifact that still looks live."""

    provider: str
    session_name: str
    metadata_path: str
    log_path: str | None
    age_seconds: int | None
    reason: str

@dataclass(frozen=True)
class ConductorSessionRecord:
    """Normalized repo-owned conductor-session metadata."""

    provider: str
    role: str
    provider_name: str
    session_name: str
    capture_mode: str
    prepared_at: str
    repo_root: str
    script_path: str
    log_path: str
    launch_command: str
    supervision_mode: str
    approval_mode: str
    planned_lane_count: int
    requested_worker_budget: int | None
    terminal_window_id: int | None
    session_pid: int | None
    planned_lanes: tuple[dict[str, str], ...]
    metadata_path: str
    live: bool
    age_seconds: int | None
    prepared_head_sha: str = ""
    prepared_instruction_revision: str = ""
    prepared_session_token: str = ""
    review_state_path: str = ""
    workspace_root: str = ""
    live_reason: str = ""
    script_probe_state: str = ""
    terminal_window_state: str = ""
    launch_authority_state: str = ""
    launch_authority_reason: str = ""


def detect_active_session_conflicts(
    *,
    session_output_root: Path,
    freshness_seconds: int = ACTIVE_SESSION_FRESHNESS_SECONDS,
) -> tuple[ActiveSessionConflict, ...]:
    """Return live-looking session artifacts that should block a second launch."""
    conflicts: list[ActiveSessionConflict] = []
    for session in load_conductor_sessions(
        session_output_root=session_output_root,
        freshness_seconds=freshness_seconds,
    ):
        if not session.live:
            continue
        conflicts.append(
            ActiveSessionConflict(
                provider=session.provider,
                session_name=session.session_name,
                metadata_path=session.metadata_path,
                log_path=session.log_path or None,
                age_seconds=session.age_seconds,
                reason=session.live_reason,
            )
        )
    return tuple(conflicts)


def summarize_active_session_conflicts(
    conflicts: tuple[ActiveSessionConflict, ...],
) -> str:
    """Render one concise duplicate-launch blocker message."""
    if not conflicts:
        return "none"
    parts: list[str] = []
    for conflict in conflicts:
        detail = f"{conflict.provider}: {conflict.reason}"
        if conflict.log_path:
            detail += f" (log: {conflict.log_path})"
        parts.append(detail)
    return "; ".join(parts)


def active_conductor_providers(
    *,
    session_output_root: Path,
    freshness_seconds: int = ACTIVE_SESSION_FRESHNESS_SECONDS,
) -> tuple[str, ...]:
    """Return provider ids with live-looking repo-owned conductor sessions."""
    sessions = load_conductor_sessions(
        session_output_root=session_output_root,
        freshness_seconds=freshness_seconds,
    )
    return tuple(sorted({session.provider for session in sessions if session.live}))


def load_conductor_sessions(
    *,
    session_output_root: Path,
    freshness_seconds: int = ACTIVE_SESSION_FRESHNESS_SECONDS,
) -> tuple[ConductorSessionRecord, ...]:
    """Return normalized conductor-session metadata with live/runtime truth."""
    session_dir = session_output_root / "sessions"
    if not session_dir.exists():
        return ()

    records: list[ConductorSessionRecord] = []
    for metadata_path in sorted(session_dir.glob("*-conductor.json")):
        metadata = _load_session_metadata(metadata_path)
        if metadata is None:
            continue
        provider = _session_metadata_text(metadata, "provider") or metadata_path.stem.removesuffix(
            "-conductor"
        )
        provider = provider.strip().lower()
        if not provider:
            continue
        planned_lanes = tuple(_planned_lane_rows(metadata.get("planned_lanes")))
        repo_root_text = _session_metadata_text(metadata, "repo_root") or ""
        workspace_root_text = _session_metadata_text(metadata, "workspace_root") or ""
        script_path_text = _session_metadata_text(metadata, "script_path")
        log_path_text = _session_metadata_text(metadata, "log_path")
        review_state_path_text = _session_metadata_text(metadata, "review_state_path") or ""
        terminal_window_id = _session_metadata_optional_int(metadata, "terminal_window_id")
        session_pid = _probe_script_pid(script_path_text)
        process_running = _probe_script_running(
            script_path_text,
            session_pid=session_pid,
        )
        age_seconds = _log_age_seconds(log_path_text)
        launch_authority = assess_prepared_launch_authority(
            repo_root=Path(repo_root_text) if repo_root_text else None,
            workspace_root=Path(workspace_root_text) if workspace_root_text else None,
            review_state_path=Path(review_state_path_text)
            if review_state_path_text
            else None,
            prepared_head_sha=_session_metadata_text(metadata, "prepared_head_sha")
            or "",
            prepared_instruction_revision=_session_metadata_text(
                metadata, "prepared_instruction_revision"
            )
            or "",
            prepared_session_token=_session_metadata_text(
                metadata, "prepared_session_token"
            )
            or "",
        )
        liveness = build_session_liveness_evidence(
            process_running=process_running,
            terminal_window_id=terminal_window_id,
            age_seconds=age_seconds,
            freshness_seconds=freshness_seconds,
            launch_authority_state=launch_authority.state,
            launch_authority_reason=launch_authority.reason,
        )
        records.append(
            ConductorSessionRecord(
                provider=provider,
                role=_session_metadata_text(metadata, "role") or "",
                provider_name=_session_metadata_text(metadata, "provider_name")
                or provider.title(),
                session_name=_session_metadata_text(metadata, "session_name")
                or f"{provider}-conductor",
                capture_mode=_session_metadata_text(metadata, "capture_mode") or "",
                prepared_at=_session_metadata_text(metadata, "prepared_at") or "",
                repo_root=repo_root_text,
                script_path=script_path_text or "",
                log_path=log_path_text or "",
                launch_command=_session_metadata_text(metadata, "launch_command") or "",
                supervision_mode=_session_metadata_text(metadata, "supervision_mode")
                or "",
                approval_mode=_session_metadata_text(metadata, "approval_mode") or "",
                planned_lane_count=_session_metadata_int(metadata, "planned_lane_count"),
                requested_worker_budget=_session_metadata_optional_int(
                    metadata, "requested_worker_budget"
                ),
                terminal_window_id=terminal_window_id,
                session_pid=session_pid,
                planned_lanes=planned_lanes,
                metadata_path=str(metadata_path),
                live=liveness.live,
                age_seconds=age_seconds,
                prepared_head_sha=_session_metadata_text(
                    metadata, "prepared_head_sha"
                )
                or "",
                prepared_instruction_revision=_session_metadata_text(
                    metadata, "prepared_instruction_revision"
                )
                or "",
                prepared_session_token=_session_metadata_text(
                    metadata, "prepared_session_token"
                )
                or "",
                review_state_path=review_state_path_text,
                workspace_root=workspace_root_text,
                live_reason=liveness.reason,
                script_probe_state=liveness.script_probe_state,
                terminal_window_state=liveness.terminal_window_state,
                launch_authority_state=launch_authority.state,
                launch_authority_reason=launch_authority.reason,
            )
        )
    return tuple(records)


def _load_session_metadata(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _session_metadata_text(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _session_metadata_int(payload: dict[str, object], key: str) -> int:
    try:
        return int(payload.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def _session_metadata_optional_int(
    payload: dict[str, object],
    key: str,
) -> int | None:
    value = payload.get(key)
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _planned_lane_rows(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    rows: list[dict[str, str]] = []
    for row in value:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                key: _normalize_session_text(item)
                for key, item in row.items()
                if _normalize_session_text(item)
            }
        )
    return rows


def _normalize_session_text(value: object) -> str:
    text = str(value or "").strip()
    if text.startswith("`") and text.endswith("`") and len(text) >= 2:
        text = text[1:-1].strip()
    return text


def _probe_script_running(
    script_path_text: str | None,
    *,
    session_pid: int | None = None,
) -> bool | None:
    pid = session_pid if session_pid is not None else _probe_script_pid(script_path_text)
    if pid is not None:
        return True
    if not script_path_text or shutil.which("pgrep") is None:
        return None
    try:
        result = subprocess.run(
            ["pgrep", "-f", script_path_text],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode == 1:
        return False
    return None


def _probe_script_pid(script_path_text: str | None) -> int | None:
    if not script_path_text or shutil.which("pgrep") is None:
        return None
    try:
        result = subprocess.run(
            ["pgrep", "-fo", script_path_text],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip().splitlines()[0])
    except (IndexError, TypeError, ValueError):
        return None


def _log_age_seconds(log_path_text: str | None) -> int | None:
    if not log_path_text:
        return None
    log_path = Path(log_path_text)
    if not log_path.exists():
        return None
    modified = datetime.fromtimestamp(log_path.stat().st_mtime, tz=timezone.utc)
    age = datetime.now(tz=timezone.utc) - modified
    return max(0, int(age.total_seconds()))
