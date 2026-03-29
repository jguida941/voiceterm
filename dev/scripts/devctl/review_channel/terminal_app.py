"""macOS Terminal.app launch helpers for review-channel sessions."""

from __future__ import annotations

import shlex
import shutil
import subprocess
import sys


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
            "end tell",
        ]
    return [
        'tell application "Terminal"',
        "activate",
        'do script ""',
        "set current settings of selected tab of front window to "
        f"settings set {_apple_string(resolved_profile)}",
        "do script "
        f"{_apple_string(launch_command)} in selected tab of front window",
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
        subprocess.run(
            ["osascript", *[item for line in script for item in ("-e", line)]],
            check=True,
        )


def _apple_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
