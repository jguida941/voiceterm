"""macOS Terminal.app launch helpers for review-channel sessions."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

from .lifecycle_state import _pid_is_alive

if TYPE_CHECKING:
    from .session_probe import ConductorSessionRecord


def list_terminal_profiles() -> list[str]:
    """Return the available Terminal.app profile names on macOS."""
    if sys.platform != "darwin":
        return []
    if shutil.which("osascript") is None:
        return []
    try:
        result = subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "Terminal" to get name of every settings set',
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []
    if result.returncode != 0:
        return []
    raw = result.stdout.strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def resolve_terminal_profile_name(
    requested_profile: str | None,
    *,
    available_profiles: list[str] | None = None,
    default_terminal_profile: str = "auto-dark",
    auto_dark_terminal_profiles: tuple[str, ...] = ("Pro", "Homebrew", "Clear Dark"),
) -> str | None:
    """Resolve the requested Terminal.app profile into an actual profile name."""
    normalized = str(requested_profile or "").strip()
    if not normalized or normalized.lower() in {"default", "system", "none"}:
        return None
    available = available_profiles if available_profiles is not None else []
    if normalized.lower() == default_terminal_profile:
        if not available:
            return auto_dark_terminal_profiles[0]
        for candidate in auto_dark_terminal_profiles:
            if candidate in available:
                return candidate
        return None
    return normalized


def build_terminal_launch_lines(
    *,
    launch_command: str,
    resolved_profile: str | None,
    available_profiles: list[str],
) -> list[str]:
    """Build the AppleScript launch sequence for one Terminal.app session."""
    if resolved_profile is None or (
        available_profiles and resolved_profile not in available_profiles
    ):
        return [
            'tell application "Terminal"',
            "activate",
            f"do script {_apple_string(launch_command)}",
            "set launched_window_id to id of front window",
            "return launched_window_id as text",
            "end tell",
        ]
    return [
        'tell application "Terminal"',
        "activate",
        'do script ""',
        "set launched_window_id to id of front window",
        "set current settings of selected tab of front window to "
        f"settings set {_apple_string(resolved_profile)}",
        "delay 0.5",
        f"do script {_apple_string(launch_command)} in selected tab of front window",
        "return launched_window_id as text",
        "end tell",
    ]


def launch_terminal_sessions(
    sessions: list[dict[str, object]],
    *,
    terminal_profile: str | None,
    default_terminal_profile: str,
    auto_dark_terminal_profiles: tuple[str, ...],
) -> None:
    """Open one Terminal.app window per session script."""
    if sys.platform != "darwin":
        raise ValueError(
            "Terminal.app launch is only supported on macOS. Use --terminal none "
            "to emit scripts/prompts without opening windows."
        )
    if shutil.which("osascript") is None:
        raise ValueError("`osascript` is required for Terminal.app launch.")
    available_profiles = list_terminal_profiles()
    resolved_profile = resolve_terminal_profile_name(
        terminal_profile,
        available_profiles=available_profiles,
        default_terminal_profile=default_terminal_profile,
        auto_dark_terminal_profiles=auto_dark_terminal_profiles,
    )
    for session in sessions:
        launch_command = str(session["launch_command"])
        script = build_terminal_launch_lines(
            launch_command=launch_command,
            resolved_profile=resolved_profile,
            available_profiles=available_profiles,
        )
        result = subprocess.run(
            ["osascript", *[item for line in script for item in ("-e", line)]],
            capture_output=True,
            text=True,
            check=True,
        )
        _record_terminal_window_id(
            session=session,
            terminal_window_id=_parse_terminal_window_id(result.stdout),
        )


def cleanup_terminal_session(
    session: "ConductorSessionRecord",
    *,
    grace_seconds: float = 2.0,
) -> list[str]:
    """Best-effort cleanup for one retired Terminal.app-backed conductor session."""
    session_name = str(session.session_name or session.provider or "session")
    warnings: list[str] = []
    session_pid = int(session.session_pid or 0)
    pid_still_alive = False
    if session_pid > 0:
        pid_still_alive = _pid_is_alive(session_pid)
        if pid_still_alive:
            try:
                os.kill(session_pid, signal.SIGTERM)
            except PermissionError:
                warnings.append(
                    f"{session_name}: permission denied while stopping pid {session_pid}."
                )
                return warnings
            except ProcessLookupError:
                pid_still_alive = False
            except OSError as exc:
                warnings.append(
                    f"{session_name}: failed to stop pid {session_pid}: {exc}."
                )
                return warnings
            pid_still_alive = _wait_for_pid_exit(
                session_pid,
                grace_seconds=grace_seconds,
            )
            if pid_still_alive:
                warnings.append(
                    f"{session_name}: pid {session_pid} stayed alive; skipped Terminal window close."
                )
                return warnings
    terminal_window_id = session.terminal_window_id
    if terminal_window_id is None:
        if session_pid <= 0:
            return warnings
        warnings.append(
            f"{session_name}: terminal_window_id missing; skipped Terminal window close."
        )
        return warnings
    if sys.platform != "darwin" or shutil.which("osascript") is None:
        warnings.append(
            f"{session_name}: osascript unavailable; skipped Terminal window close."
        )
        return warnings
    try:
        subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "Terminal"',
                "-e",
                f"if exists window id {int(terminal_window_id)} then close window id {int(terminal_window_id)}",
                "-e",
                "end tell",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        warnings.append(
            f"{session_name}: failed to close Terminal window {terminal_window_id}: {detail}."
        )
    except OSError as exc:
        warnings.append(
            f"{session_name}: failed to close Terminal window {terminal_window_id}: {exc}."
        )
    return warnings


def _wait_for_pid_exit(pid: int, *, grace_seconds: float) -> bool:
    if pid <= 0:
        return False
    if grace_seconds <= 0:
        return _pid_is_alive(pid)
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if not _pid_is_alive(pid):
            return False
        time.sleep(0.1)
    return _pid_is_alive(pid)


def _record_terminal_window_id(
    *,
    session: dict[str, object],
    terminal_window_id: int | None,
) -> None:
    session["terminal_window_id"] = terminal_window_id
    if terminal_window_id is None:
        return
    metadata_path_text = str(session.get("metadata_path") or "").strip()
    if not metadata_path_text:
        return
    metadata_path = Path(metadata_path_text)
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return
    if not isinstance(payload, dict):
        return
    payload["terminal_window_id"] = terminal_window_id
    metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _parse_terminal_window_id(stdout: str) -> int | None:
    matches = re.findall(r"-?\d+", str(stdout or ""))
    if not matches:
        return None
    try:
        return int(matches[-1])
    except ValueError:
        return None


def _apple_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
