"""Metadata helpers for bridge-compatibility projections."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_LOCAL_TIME_FORMAT = "%Y-%m-%d %H:%M:%S %Z"
_PLACEHOLDER_INSTRUCTION_MARKERS = (
    "stop at a safe boundary",
    "relaunch before compaction",
    "await reviewer instruction refresh",
)


def local_tz() -> ZoneInfo:
    """Return the display timezone from the active repo-pack config."""
    from ..repo_packs import active_path_config

    return ZoneInfo(active_path_config().display_timezone)


def format_local_poll_time(last_codex_poll_utc: str) -> str:
    normalized_poll_utc = normalize_poll_time(last_codex_poll_utc)
    if not normalized_poll_utc:
        return ""
    try:
        parsed = datetime.strptime(
            normalized_poll_utc,
            "%Y-%m-%dT%H:%M:%SZ",
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return ""
    return parsed.astimezone(local_tz()).strftime(_LOCAL_TIME_FORMAT)


def normalize_poll_time(last_codex_poll_utc: str) -> str:
    normalized = str(last_codex_poll_utc or "").strip()
    if not normalized:
        return ""
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def projection_metadata(
    *,
    snapshot,
    bridge_liveness: Mapping[str, object],
    sections: Mapping[str, str],
    current_session: Mapping[str, object],
    bridge_state: Mapping[str, object],
) -> dict[str, str]:
    current_instruction = str(sections.get("Current Instruction For Claude", "")).strip()
    if _typed_instruction_explicitly_cleared(current_session):
        current_revision = ""
    else:
        current_revision = str(
            current_session.get("current_instruction_revision")
            or bridge_state.get("current_instruction_revision")
            or bridge_liveness.get("current_instruction_revision")
            or snapshot.metadata.get("current_instruction_revision")
            or ""
        ).strip()
    if current_instruction and not _is_placeholder_instruction(current_instruction):
        derived_revision = hashlib.sha256(
            current_instruction.encode("utf-8")
        ).hexdigest()[:12]
        if not current_revision or current_revision != derived_revision:
            current_revision = derived_revision
    last_codex_poll_utc = _first_text(
        snapshot.metadata.get("last_codex_poll_utc"),
        bridge_state.get("last_codex_poll_utc"),
        bridge_state.get("last_reviewer_poll_utc"),
        bridge_liveness.get("last_codex_poll_utc"),
        bridge_liveness.get("last_reviewer_poll_utc"),
    )
    last_codex_poll_local = _first_text(
        snapshot.metadata.get("last_codex_poll_local"),
        bridge_state.get("last_codex_poll_local"),
        bridge_state.get("last_reviewer_poll_local"),
        bridge_liveness.get("last_codex_poll_local"),
        bridge_liveness.get("last_reviewer_poll_local"),
    )
    normalized_poll_utc = normalize_poll_time(last_codex_poll_utc)
    if normalized_poll_utc:
        last_codex_poll_utc = normalized_poll_utc
    if not last_codex_poll_local and last_codex_poll_utc:
        last_codex_poll_local = format_local_poll_time(last_codex_poll_utc)
    return {
        "last_codex_poll_utc": last_codex_poll_utc,
        "last_codex_poll_local": last_codex_poll_local,
        "reviewer_mode": str(
            bridge_liveness.get("reviewer_mode")
            or snapshot.metadata.get("reviewer_mode")
            or "active_dual_agent"
        ).strip(),
        "current_instruction_revision": current_revision,
    }


def _typed_instruction_explicitly_cleared(current_session: Mapping[str, object]) -> bool:
    if "current_instruction" not in current_session:
        return False
    instruction = str(current_session.get("current_instruction") or "").strip()
    revision = str(current_session.get("current_instruction_revision") or "").strip()
    return not instruction and not revision


def _first_text(*candidates: object) -> str:
    for candidate in candidates:
        value = str(candidate or "").strip()
        if value:
            return value
    return ""


def _is_placeholder_instruction(current_instruction: str) -> bool:
    normalized = str(current_instruction or "").strip().lower()
    return any(marker in normalized for marker in _PLACEHOLDER_INSTRUCTION_MARKERS)
