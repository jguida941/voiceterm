"""Metadata helpers for bridge-compatibility projections."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .bridge_projection_instruction import (
    is_placeholder_instruction as _is_placeholder_instruction,
    typed_instruction_explicitly_cleared as _typed_instruction_explicitly_cleared,
)
from .peer_liveness import resolve_reported_reviewer_mode
from ..runtime.review_state_semantics import is_missing_instruction

_LOCAL_TIME_FORMAT = "%Y-%m-%d %H:%M:%S %Z"
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
    typed_instruction_cleared = _typed_instruction_explicitly_cleared(
        current_session,
        projected_instruction=current_instruction,
    )
    if typed_instruction_cleared:
        current_revision = ""
    else:
        current_revision = str(
            current_session.get("current_instruction_revision")
            or bridge_state.get("current_instruction_revision")
            or bridge_liveness.get("current_instruction_revision")
            or snapshot.metadata.get("current_instruction_revision")
            or ""
        ).strip()
    if (
        not typed_instruction_cleared
        and current_instruction
        and not is_missing_instruction(current_instruction)
        and not _is_placeholder_instruction(current_instruction)
    ):
        derived_revision = hashlib.sha256(
            current_instruction.encode("utf-8")
        ).hexdigest()[:12]
        if not current_revision or current_revision != derived_revision:
            current_revision = derived_revision
    last_codex_poll_utc = _newest_poll_time(
        bridge_state.get("last_codex_poll_utc"),
        bridge_state.get("last_reviewer_poll_utc"),
        bridge_liveness.get("last_codex_poll_utc"),
        bridge_liveness.get("last_reviewer_poll_utc"),
        snapshot.metadata.get("last_codex_poll_utc"),
    )
    normalized_poll_utc = normalize_poll_time(last_codex_poll_utc)
    if normalized_poll_utc:
        last_codex_poll_utc = normalized_poll_utc
    last_codex_poll_local = (
        format_local_poll_time(last_codex_poll_utc)
        if last_codex_poll_utc
        else _first_text(
            bridge_state.get("last_codex_poll_local"),
            bridge_state.get("last_reviewer_poll_local"),
            bridge_liveness.get("last_codex_poll_local"),
            bridge_liveness.get("last_reviewer_poll_local"),
            snapshot.metadata.get("last_codex_poll_local"),
        )
    )
    effective_reviewer_mode = resolve_reported_reviewer_mode(
        {
            "reviewer_mode": _first_text(
                bridge_liveness.get("effective_reviewer_mode"),
                bridge_state.get("effective_reviewer_mode"),
            )
        }
    )
    declared_reviewer_mode = resolve_reported_reviewer_mode(
        {
            "reviewer_mode": _first_text(
                bridge_liveness.get("reviewer_mode"),
                bridge_state.get("reviewer_mode"),
                snapshot.metadata.get("reviewer_mode"),
            )
        }
    )
    reviewer_mode = effective_reviewer_mode or declared_reviewer_mode
    metadata: dict[str, str] = {}
    metadata["last_codex_poll_utc"] = last_codex_poll_utc
    metadata["last_codex_poll_local"] = last_codex_poll_local
    metadata["reviewer_mode"] = reviewer_mode
    metadata["declared_reviewer_mode"] = declared_reviewer_mode
    metadata["effective_reviewer_mode"] = effective_reviewer_mode
    metadata["current_instruction_revision"] = current_revision
    metadata["current_instruction_explicitly_cleared"] = (
        "true" if typed_instruction_cleared else ""
    )
    return metadata

def _first_text(*candidates: object) -> str:
    for candidate in candidates:
        value = str(candidate or "").strip()
        if value:
            return value
    return ""


def _newest_poll_time(*candidates: object) -> str:
    best_text = ""
    best_parsed: datetime | None = None
    for candidate in candidates:
        normalized = normalize_poll_time(str(candidate or ""))
        if not normalized:
            continue
        try:
            parsed = datetime.strptime(normalized, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            continue
        if best_parsed is None or parsed > best_parsed:
            best_parsed = parsed
            best_text = normalized
    return best_text or _first_text(*candidates)
