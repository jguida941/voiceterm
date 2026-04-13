"""Metadata helpers for bridge-compatibility projections."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_LOCAL_TIME_FORMAT = "%Y-%m-%d %H:%M:%S %Z"


def local_tz() -> ZoneInfo:
    """Return the display timezone from the active repo-pack config."""
    from ..repo_packs import active_path_config

    return ZoneInfo(active_path_config().display_timezone)


def format_local_poll_time(last_codex_poll_utc: str) -> str:
    try:
        parsed = datetime.strptime(
            last_codex_poll_utc,
            "%Y-%m-%dT%H:%M:%SZ",
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return ""
    return parsed.astimezone(local_tz()).strftime(_LOCAL_TIME_FORMAT)


def projection_metadata(
    *,
    snapshot,
    bridge_liveness: Mapping[str, object],
    sections: Mapping[str, str],
    current_session: Mapping[str, object],
    bridge_state: Mapping[str, object],
) -> dict[str, str]:
    current_instruction = str(sections.get("Current Instruction For Claude", "")).strip()
    current_revision = str(
        current_session.get("current_instruction_revision")
        or bridge_state.get("current_instruction_revision")
        or bridge_liveness.get("current_instruction_revision")
        or snapshot.metadata.get("current_instruction_revision")
        or ""
    ).strip()
    if not current_revision and current_instruction:
        current_revision = hashlib.sha256(
            current_instruction.encode("utf-8")
        ).hexdigest()[:12]
    last_codex_poll_utc = str(snapshot.metadata.get("last_codex_poll_utc") or "").strip()
    last_codex_poll_local = str(
        snapshot.metadata.get("last_codex_poll_local") or ""
    ).strip()
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
