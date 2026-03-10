"""Helpers for `devctl mobile-app`."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from .config import REPO_ROOT

IOS_APP_DIR = REPO_ROOT / "app/ios/VoiceTermMobileApp"
IOS_PROJECT = IOS_APP_DIR / "VoiceTermMobileApp.xcodeproj"
SIMULATOR_DEMO_SCRIPT = IOS_APP_DIR / "run_guided_simulator_demo.sh"
IOS_SCHEME = "VoiceTermMobileApp"
IOS_APP_BUNDLE_ID = "com.voiceterm.VoiceTermMobileApp"
DEVICE_DERIVED_DATA_PATH = Path("/tmp/voiceterm-mobile-device-derived")
XCTRACE_DEVICE_PATTERN = re.compile(
    r"^(?P<name>.+?) \((?P<runtime>[^)]+)\) \((?P<identifier>[0-9A-Fa-f-]{10,})\)$"
)
SIMCTL_DEVICE_PATTERN = re.compile(
    r"^\s*(?P<name>.+?) \((?P<identifier>[0-9A-F-]{36})\) \((?P<state>[^)]+)\)\s*$"
)


def _capture(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout


def list_available_simulators() -> list[dict[str, str]]:
    simulators: list[dict[str, str]] = []
    for line in _capture(["xcrun", "simctl", "list", "devices", "available"]).splitlines():
        match = SIMCTL_DEVICE_PATTERN.match(line)
        if not match:
            continue
        simulators.append(match.groupdict())
    return simulators


def select_simulator(device_id: str | None) -> str | None:
    if device_id:
        return device_id
    booted = _capture(["xcrun", "simctl", "list", "devices", "booted"])
    booted_match = re.search(r"([0-9A-F-]{36})", booted)
    if booted_match:
        return booted_match.group(1)
    simulators = list_available_simulators()
    return simulators[0]["identifier"] if simulators else None


def list_physical_devices() -> list[dict[str, str]]:
    devices: list[dict[str, str]] = []
    output = _capture(["xcrun", "xctrace", "list", "devices"])
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("==") or "Simulator" in line:
            continue
        match = XCTRACE_DEVICE_PATTERN.match(line)
        if not match:
            continue
        device = match.groupdict()
        if device["name"].startswith("My Mac"):
            continue
        devices.append(device)
    return devices


def select_physical_device(
    device_id: str | None,
    devices: list[dict[str, str]] | None = None,
) -> str | None:
    available = devices if devices is not None else list_physical_devices()
    if device_id:
        return device_id
    return available[0]["identifier"] if available else None


def resolve_development_team(cli_value: str | None) -> str | None:
    if cli_value and cli_value.strip():
        return cli_value.strip()
    env_value = os.environ.get("VOICETERM_IOS_DEVELOPMENT_TEAM", "").strip()
    if env_value:
        return env_value
    return None


def project_relative_path(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))
