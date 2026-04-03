#!/usr/bin/env python3
"""launchd wrapper for the repo-owned review-channel publisher."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ACTIVE_REVIEWER_MODE = "active_dual_agent"
PUBLISHER_HEARTBEAT_REL = Path(
    "dev/reports/review_channel/latest/publisher_heartbeat.json"
)
RESTART_EXIT_CODES = {
    "timed_out": 70,
    "inactivity_timeout": 70,
    "output_error": 75,
    "detached_exit": 75,
    "failed_start": 75,
}
NO_RESTART_STOP_REASONS = {"", "completed", "manual_stop"}


def repo_root_for_service(script_path: Path | None = None) -> Path:
    """Resolve the repo root from the checked-in launchd wrapper path."""
    target = script_path if script_path is not None else Path(__file__)
    return target.resolve().parents[3]


def load_json(path: Path) -> dict[str, object]:
    """Read one JSON file or return an empty mapping when absent/corrupt."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def publisher_state(repo_root: Path) -> dict[str, object]:
    """Load the latest persisted publisher lifecycle state."""
    return load_json(repo_root / PUBLISHER_HEARTBEAT_REL)


def publisher_running(state: dict[str, object]) -> bool:
    """Return true when the persisted publisher heartbeat still reports live."""
    return bool(state.get("running"))


def reviewer_mode_is_inactive(status_payload: dict[str, object]) -> bool:
    """Skip launchd restarts outside active dual-agent review mode."""
    bridge_liveness = status_payload.get("bridge_liveness")
    if not isinstance(bridge_liveness, dict):
        return False
    effective_mode = str(
        bridge_liveness.get("effective_reviewer_mode")
        or bridge_liveness.get("reviewer_mode")
        or ""
    )
    return effective_mode != ACTIVE_REVIEWER_MODE


def status_command(repo_root: Path) -> list[str]:
    """Return the repo-owned status command used for inactive-mode gating."""
    return [
        sys.executable,
        str((repo_root / "dev/scripts/devctl.py").resolve()),
        "review-channel",
        "--action",
        "status",
        "--terminal",
        "none",
        "--format",
        "json",
    ]


def follow_command(repo_root: Path) -> list[str]:
    """Return the detached publisher command launchd should supervise."""
    return [
        sys.executable,
        str((repo_root / "dev/scripts/devctl.py").resolve()),
        "review-channel",
        "--action",
        "ensure",
        "--follow",
        "--terminal",
        "none",
        "--format",
        "json",
        "--follow-inactivity-timeout-seconds",
        "0",
    ]


def run_json_command(command: list[str], *, repo_root: Path) -> dict[str, object]:
    """Run one repo-owned JSON command and parse stdout when possible."""
    completed = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return {}
    return load_json_from_text(completed.stdout)


def load_json_from_text(content: str) -> dict[str, object]:
    """Parse JSON text or return an empty mapping."""
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def launchd_exit_code(stop_reason: str, *, returncode: int) -> int:
    """Map the publisher stop reason into launchd restart semantics."""
    reason = stop_reason.strip()
    if reason in NO_RESTART_STOP_REASONS:
        return 0
    mapped = RESTART_EXIT_CODES.get(reason)
    if mapped is not None:
        return mapped
    if returncode != 0:
        return RESTART_EXIT_CODES["output_error"]
    return 0


def main(*, script_path: Path | None = None) -> int:
    """Run the publisher follow loop under launchd-friendly exit semantics."""
    repo_root = repo_root_for_service(script_path)
    current_state = publisher_state(repo_root)
    if publisher_running(current_state):
        return 0

    status_payload = run_json_command(status_command(repo_root), repo_root=repo_root)
    if reviewer_mode_is_inactive(status_payload):
        return 0

    completed = subprocess.run(
        follow_command(repo_root),
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    final_state = publisher_state(repo_root)
    stop_reason = str(final_state.get("stop_reason") or "")
    return launchd_exit_code(stop_reason, returncode=completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
