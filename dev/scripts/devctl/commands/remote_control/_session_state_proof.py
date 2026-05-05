"""Claude session-state proof for live remote-control bridge presence."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from ...time_utils import parse_utc_timestamp

CLAUDE_SESSION_STATE_ROOT = Path.home() / ".claude" / "sessions"
SESSION_STATE_PROOF_CHANNEL = "claude_session_state"
SESSION_STATE_PHYSICAL_METHOD = "claude_session_state_bridge"
SESSION_STATE_URL_PREFIX = "https://claude.ai/code/"
_TERMINAL_STATUSES = frozenset(
    {"closed", "complete", "exited", "stopped", "terminated"}
)


@dataclass(frozen=True, slots=True)
class ClaudeSessionStateBridgeProof:
    """Live bridge identity read from Claude's local session-state file."""

    path: Path
    pid: int
    session_id: str
    bridge_session_id: str
    status: str
    updated_at_utc: str

    @property
    def session_url(self) -> str:
        return f"{SESSION_STATE_URL_PREFIX}{self.bridge_session_id}"


class _BridgePayload(NamedTuple):
    session_id: str
    bridge_session_id: str
    status: str
    updated_at_utc: datetime
    pid: int


def resolve_live_session_state_bridge_proof(
    *,
    session_id: str,
    now_utc: str,
    expected_cwd: str = "",
    max_age_seconds: int,
    session_state_root: Path | None = None,
    pid_checker: Callable[[int], bool] | None = None,
) -> ClaudeSessionStateBridgeProof | None:
    """Return live Claude remote-control bridge proof for one session id.

    Claude emits ``bridge_status`` as an activation edge. While remote
    control remains active, the current bridge identity is mirrored in
    ``~/.claude/sessions/<pid>.json`` as ``bridgeSessionId``. This reader
    treats that local provider-owned session state as the heartbeat-quality
    proof, bounded by session id, optional cwd, updatedAt freshness, and a
    live host pid check.
    """
    clean_session_id = _text(session_id)
    if not clean_session_id:
        return None
    now = parse_utc_timestamp(now_utc)
    if now is None:
        return None
    root = session_state_root or CLAUDE_SESSION_STATE_ROOT
    if not root.exists():
        return None
    checker = pid_checker or _pid_alive
    candidates: list[ClaudeSessionStateBridgeProof] = []
    for path in root.glob("*.json"):
        proof = _proof_from_path(
            path,
            session_id=clean_session_id,
            now=now,
            expected_cwd=expected_cwd,
            max_age_seconds=max_age_seconds,
            pid_checker=checker,
        )
        if proof is not None:
            candidates.append(proof)
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda proof: parse_utc_timestamp(proof.updated_at_utc)
        or datetime.min.replace(tzinfo=timezone.utc),
    )


def resolve_latest_live_session_state_bridge_proof(
    *,
    now_utc: str,
    expected_cwd: str,
    max_age_seconds: int,
    session_state_root: Path | None = None,
    pid_checker: Callable[[int], bool] | None = None,
) -> ClaudeSessionStateBridgeProof | None:
    """Return the freshest live bridge proof for a project cwd."""
    now = parse_utc_timestamp(now_utc)
    if now is None:
        return None
    root = session_state_root or CLAUDE_SESSION_STATE_ROOT
    if not root.exists():
        return None
    checker = pid_checker or _pid_alive
    candidates: list[ClaudeSessionStateBridgeProof] = []
    for path in root.glob("*.json"):
        proof = _proof_from_path(
            path,
            session_id="",
            now=now,
            expected_cwd=expected_cwd,
            max_age_seconds=max_age_seconds,
            pid_checker=checker,
        )
        if proof is not None:
            candidates.append(proof)
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda proof: parse_utc_timestamp(proof.updated_at_utc)
        or datetime.min.replace(tzinfo=timezone.utc),
    )


def _proof_from_path(
    path: Path,
    *,
    session_id: str,
    now: datetime,
    expected_cwd: str,
    max_age_seconds: int,
    pid_checker: Callable[[int], bool],
) -> ClaudeSessionStateBridgeProof | None:
    payload = _session_state_payload(path)
    if payload is None:
        return None
    bridge_payload = _bridge_payload(
        payload,
        session_id=session_id,
        now=now,
        expected_cwd=expected_cwd,
        max_age_seconds=max_age_seconds,
        pid_checker=pid_checker,
    )
    if bridge_payload is None:
        return None
    return ClaudeSessionStateBridgeProof(
        path=path,
        pid=bridge_payload.pid,
        session_id=bridge_payload.session_id,
        bridge_session_id=bridge_payload.bridge_session_id,
        status=bridge_payload.status,
        updated_at_utc=bridge_payload.updated_at_utc.isoformat().replace("+00:00", "Z"),
    )


def _session_state_payload(path: Path) -> Mapping[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, Mapping) else None


def _bridge_payload(
    payload: Mapping[str, object],
    *,
    session_id: str,
    now: datetime,
    expected_cwd: str,
    max_age_seconds: int,
    pid_checker: Callable[[int], bool],
) -> _BridgePayload | None:
    payload_session_id = _matching_session_id(payload, session_id=session_id)
    if not payload_session_id:
        return None
    if not _cwd_matches(payload.get("cwd"), expected_cwd=expected_cwd):
        return None
    status = _text(payload.get("status")).lower()
    bridge_session_id = _text(payload.get("bridgeSessionId"))
    updated_at = _fresh_updated_at(
        payload.get("updatedAt"),
        now=now,
        max_age_seconds=max_age_seconds,
    )
    pid = _int_or_zero(payload.get("pid"))
    if (
        status in _TERMINAL_STATUSES
        or not bridge_session_id.startswith("session_")
        or updated_at is None
        or pid <= 0
        or not pid_checker(pid)
    ):
        return None
    return _BridgePayload(
        session_id=payload_session_id,
        bridge_session_id=bridge_session_id,
        status=status,
        updated_at_utc=updated_at,
        pid=pid,
    )


def _matching_session_id(
    payload: Mapping[str, object],
    *,
    session_id: str,
) -> str:
    payload_session_id = _text(payload.get("sessionId"))
    if session_id:
        return payload_session_id if payload_session_id == session_id else ""
    return payload_session_id


def _fresh_updated_at(
    value: object,
    *,
    now: datetime,
    max_age_seconds: int,
) -> datetime | None:
    updated_at = _updated_at_utc(value)
    if updated_at is None:
        return None
    age_seconds = max((now - updated_at).total_seconds(), 0.0)
    return updated_at if age_seconds <= max_age_seconds else None


def _cwd_matches(value: object, *, expected_cwd: str) -> bool:
    expected = _text(expected_cwd)
    if not expected:
        return True
    actual = _text(value)
    if not actual:
        return False
    try:
        return Path(actual).resolve(strict=False) == Path(expected).resolve(strict=False)
    except OSError:
        return actual == expected


def _updated_at_utc(value: object) -> datetime | None:
    raw = _text(value)
    if not raw:
        return None
    try:
        numeric = float(raw)
    except ValueError:
        return parse_utc_timestamp(raw)
    if numeric > 10_000_000_000:
        numeric = numeric / 1000.0
    return datetime.fromtimestamp(numeric, tz=timezone.utc)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _int_or_zero(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "CLAUDE_SESSION_STATE_ROOT",
    "SESSION_STATE_PHYSICAL_METHOD",
    "SESSION_STATE_PROOF_CHANNEL",
    "ClaudeSessionStateBridgeProof",
    "resolve_latest_live_session_state_bridge_proof",
    "resolve_live_session_state_bridge_proof",
]
