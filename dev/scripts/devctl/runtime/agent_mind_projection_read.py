"""Read-side helpers for typed agent-mind projections."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..repo_packs import active_path_config


def agent_mind_projection_path(repo_root: Path, *, provider: str = "codex") -> Path:
    """Resolve the latest agent-mind projection path through repo-pack policy."""
    config = active_path_config()
    reports_root = Path(config.reports_root_rel)
    rel = reports_root / "agent_minds" / f"{provider.strip().lower()}_latest.json"
    if rel.is_absolute():
        return rel
    return repo_root / rel


def read_agent_mind_projection(
    repo_root: Path,
    *,
    provider: str = "codex",
) -> dict[str, Any]:
    """Return the latest agent-mind projection, or an empty dict when absent."""
    path = agent_mind_projection_path(repo_root, provider=provider)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def agent_mind_latest_age_seconds(agent_mind: Mapping[str, object]) -> float | None:
    """Return the age of the freshest agent-mind timestamp."""
    latest_at = _latest_agent_mind_timestamp(agent_mind)
    if latest_at is None:
        return None
    return max((datetime.now(timezone.utc) - latest_at).total_seconds(), 0.0)


def _latest_agent_mind_timestamp(agent_mind: Mapping[str, object]) -> datetime | None:
    timestamps = [
        _parse_utc_timestamp(agent_mind.get("generated_at_utc")),
        _parse_utc_timestamp(agent_mind.get("last_cursor")),
    ]
    events = agent_mind.get("latest_events")
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes)):
        events = agent_mind.get("events")
    if isinstance(events, Sequence) and not isinstance(events, (str, bytes)):
        for event in events:
            if isinstance(event, Mapping):
                timestamps.append(_parse_utc_timestamp(event.get("timestamp")))
    parsed = [timestamp for timestamp in timestamps if timestamp is not None]
    if not parsed:
        return None
    return max(parsed)


def _parse_utc_timestamp(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


__all__ = [
    "agent_mind_latest_age_seconds",
    "agent_mind_projection_path",
    "read_agent_mind_projection",
]
