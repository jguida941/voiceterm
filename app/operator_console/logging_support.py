"""Diagnostics helpers for the optional PyQt6 Operator Console.

This module intentionally avoids any PyQt dependency so logging behavior can be
unit tested without a GUI runtime.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dev.scripts.devctl.repo_packs import VOICETERM_PATH_CONFIG

from .state.core.models import utc_timestamp

DEFAULT_DEV_LOG_ROOT_REL = VOICETERM_PATH_CONFIG.dev_log_root_rel


@dataclass(frozen=True)
class OperatorConsoleLogPaths:
    """Filesystem locations for one persisted diagnostics session."""

    root_dir: Path
    session_dir: Path
    session_log_path: Path
    session_events_path: Path
    session_command_output_path: Path
    latest_log_path: Path
    latest_events_path: Path
    latest_command_output_path: Path


class OperatorConsoleDiagnostics:
    """High-level event logger for the optional desktop Operator Console."""

    def __init__(
        self,
        *,
        enabled: bool,
        paths: OperatorConsoleLogPaths | None,
    ) -> None:
        self.enabled = enabled
        self.paths = paths

    @classmethod
    def create(
        cls,
        repo_root: Path,
        *,
        enabled: bool,
        root_rel: str = DEFAULT_DEV_LOG_ROOT_REL,
    ) -> "OperatorConsoleDiagnostics":
        """Create a diagnostics logger for the current Operator Console run."""
        if not enabled:
            return cls(enabled=False, paths=None)

        paths = build_log_paths(repo_root, root_rel=root_rel)
        paths.session_log_path.touch()
        paths.session_events_path.touch()
        paths.session_command_output_path.touch()
        paths.latest_log_path.write_text("", encoding="utf-8")
        paths.latest_events_path.write_text("", encoding="utf-8")
        paths.latest_command_output_path.write_text("", encoding="utf-8")
        return cls(enabled=True, paths=paths)

    @property
    def destination_summary(self) -> str:
        """Return the operator-facing summary of where diagnostics live."""
        if self.paths is None:
            return "memory-only diagnostics (relaunch with --dev-log to persist)"
        return str(self.paths.latest_log_path.resolve())

    def log(
        self,
        *,
        level: str,
        event: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> str:
        """Record one structured diagnostics event and return the text line."""
        record = {
            "timestamp_utc": utc_timestamp(),
            "level": level.upper(),
            "event": event,
            "message": message,
            "details": normalize_details(details or {}),
        }
        text_line = render_log_line(record)
        if self.paths is not None:
            self._append_text(
                self.paths.session_log_path,
                text_line + "\n",
            )
            self._append_text(
                self.paths.latest_log_path,
                text_line + "\n",
            )
            json_line = json.dumps(record, sort_keys=True) + "\n"
            self._append_text(self.paths.session_events_path, json_line)
            self._append_text(self.paths.latest_events_path, json_line)
        return text_line

    def append_command_output(self, *, stream_name: str, text: str) -> None:
        """Persist raw command output when dev logging is enabled."""
        if not text or self.paths is None:
            return
        timestamp = utc_timestamp()
        prefix = f"[{timestamp}] [{stream_name.upper()}]\n"
        rendered = prefix + text
        if not rendered.endswith("\n"):
            rendered += "\n"
        self._append_text(self.paths.session_command_output_path, rendered)
        self._append_text(self.paths.latest_command_output_path, rendered)

    def _append_text(self, path: Path, content: str) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(content)


def build_log_paths(
    repo_root: Path,
    *,
    root_rel: str = DEFAULT_DEV_LOG_ROOT_REL,
    timestamp_utc: str | None = None,
) -> OperatorConsoleLogPaths:
    """Return the canonical diagnostics paths for one persisted session."""
    stamp = sanitize_timestamp(timestamp_utc or utc_timestamp())
    root_dir = repo_root / root_rel
    session_dir = root_dir / "sessions" / stamp
    session_dir.mkdir(parents=True, exist_ok=True)
    root_dir.mkdir(parents=True, exist_ok=True)
    return OperatorConsoleLogPaths(
        root_dir=root_dir,
        session_dir=session_dir,
        session_log_path=session_dir / "operator_console.log",
        session_events_path=session_dir / "events.ndjson",
        session_command_output_path=session_dir / "command_output.log",
        latest_log_path=root_dir / "latest.operator_console.log",
        latest_events_path=root_dir / "latest.events.ndjson",
        latest_command_output_path=root_dir / "latest.command_output.log",
    )


def render_log_line(record: dict[str, Any]) -> str:
    """Render one human-readable diagnostics line."""
    details = record.get("details") or {}
    details_text = ""
    if details:
        rendered_parts = [
            f"{key}={json.dumps(value, sort_keys=True)}"
            for key, value in sorted(details.items())
        ]
        details_text = " | " + "; ".join(rendered_parts)
    return (
        f"{record['timestamp_utc']} "
        f"[{record['level']}] "
        f"{record['event']}: {record['message']}{details_text}"
    )


def normalize_details(details: dict[str, Any]) -> dict[str, Any]:
    """Normalize event details into JSON-serializable values."""
    normalized: dict[str, Any] = {}
    for key, value in details.items():
        normalized[key] = normalize_value(value)
    return normalized


def normalize_value(value: Any) -> Any:
    """Best-effort JSON normalization for diagnostics payloads."""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): normalize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [normalize_value(item) for item in value]
    return str(value)


def sanitize_timestamp(timestamp_utc: str) -> str:
    """Return a filesystem-safe UTC timestamp token."""
    return re.sub(r"[^0-9A-Z]", "", timestamp_utc.upper())
