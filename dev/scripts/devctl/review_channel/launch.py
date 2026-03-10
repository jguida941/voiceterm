"""CLI and Terminal-app launch helpers for the transitional review channel."""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from ..approval_mode import DEFAULT_APPROVAL_MODE, normalize_approval_mode
from .launch_script import build_session_script
from .prompt import build_conductor_prompt
from ..time_utils import utc_timestamp

if TYPE_CHECKING:
    from .core import LaneAssignment


def resolve_cli_path(provider: str) -> str:
    """Resolve the requested provider CLI from PATH."""
    cli_path = shutil.which(provider)
    if cli_path:
        return cli_path
    raise ValueError(f"Required CLI not found on PATH: {provider}")


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


def build_rollover_command(
    *,
    rollover_threshold_pct: int,
    await_ack_seconds: int,
    approval_mode: str = DEFAULT_APPROVAL_MODE,
    dangerous: bool = False,
) -> str:
    """Return the canonical self-relaunch command for planned rollovers."""
    command = [
        "python3",
        "dev/scripts/devctl.py",
        "review-channel",
        "--action",
        "rollover",
        "--rollover-threshold-pct",
        str(rollover_threshold_pct),
        "--await-ack-seconds",
        str(await_ack_seconds),
        "--terminal",
        "terminal-app",
    ]
    resolved_mode = normalize_approval_mode(approval_mode, dangerous=dangerous)
    command.extend(["--approval-mode", resolved_mode])
    return shlex.join(command)


def build_promote_command(
    *,
    promotion_plan_rel: str,
) -> str:
    """Return the canonical typed next-task promotion command."""
    command = [
        "python3",
        "dev/scripts/devctl.py",
        "review-channel",
        "--action",
        "promote",
        "--promotion-plan",
        promotion_plan_rel,
        "--terminal",
        "none",
        "--format",
        "md",
    ]
    return shlex.join(command)


def build_launch_sessions(
    *,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
    codex_lanes: list["LaneAssignment"],
    claude_lanes: list["LaneAssignment"],
    codex_workers: int,
    claude_workers: int,
    rollover_threshold_pct: int,
    await_ack_seconds: int,
    default_terminal_profile: str,
    retirement_note: str,
    promotion_plan_rel: str,
    approval_mode: str = DEFAULT_APPROVAL_MODE,
    dangerous: bool = False,
    bridge_liveness: dict[str, object] | None = None,
    handoff_bundle: dict[str, str] | None = None,
    script_dir: Path | None = None,
    session_output_root: Path | None = None,
    cursor_lanes: list["LaneAssignment"] | None = None,
    cursor_workers: int = 0,
    build_conductor_prompt_fn: Callable[..., str] = build_conductor_prompt,
    resolve_cli_path_fn: Callable[[str], str] = resolve_cli_path,
) -> list[dict[str, object]]:
    """Create conductor launch scripts and return session metadata."""
    effective_script_dir = (
        script_dir
        if script_dir is not None
        else Path(tempfile.mkdtemp(prefix="review-channel-launch-"))
    )
    sessions: list[dict[str, object]] = []
    rollover_command = build_rollover_command(
        approval_mode=approval_mode,
        dangerous=dangerous,
        rollover_threshold_pct=rollover_threshold_pct,
        await_ack_seconds=await_ack_seconds,
    )
    resolved_approval_mode = normalize_approval_mode(
        approval_mode,
        dangerous=dangerous,
    )
    promote_command = build_promote_command(
        promotion_plan_rel=promotion_plan_rel,
    )
    session_dir = (
        (session_output_root / "sessions")
        if session_output_root is not None
        else None
    )
    prepared_at = utc_timestamp()
    provider_roster: list[tuple[str, str, str, list, int]] = [
        ("codex", "Codex", "Claude", codex_lanes, codex_workers),
        ("claude", "Claude", "Codex", claude_lanes, claude_workers),
    ]
    if cursor_lanes:
        provider_roster.append(
            ("cursor", "Cursor", "Claude", cursor_lanes, cursor_workers),
        )
    for provider, provider_name, other_name, lanes, worker_budget in provider_roster:
        session_name = f"{provider}-conductor"
        log_path = None if session_dir is None else session_dir / f"{session_name}.log"
        metadata_path = (
            None if session_dir is None else session_dir / f"{session_name}.json"
        )
        prompt = build_conductor_prompt_fn(
            provider=provider,
            provider_name=provider_name,
            other_name=other_name,
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            bridge_path=bridge_path,
            lanes=lanes,
            codex_workers=codex_workers,
            claude_workers=claude_workers,
            approval_mode=resolved_approval_mode,
            dangerous=dangerous,
            rollover_threshold_pct=rollover_threshold_pct,
            await_ack_seconds=await_ack_seconds,
            retirement_note=retirement_note,
            rollover_command=rollover_command,
            promote_command=promote_command,
            bridge_liveness=bridge_liveness,
            handoff_bundle=handoff_bundle,
        )
        script_name = f"{provider}-conductor.sh"
        script_path = effective_script_dir / script_name
        launch_command = f"/bin/zsh {shlex.quote(str(script_path))}"
        if metadata_path is not None and log_path is not None:
            _write_session_metadata(
                metadata_path=metadata_path,
                payload={
                    "provider": provider,
                    "provider_name": provider_name,
                    "session_name": session_name,
                    "capture_mode": "terminal-script",
                    "prepared_at": prepared_at,
                    "repo_root": str(repo_root),
                    "script_path": str(script_path),
                    "log_path": str(log_path),
                    "launch_command": launch_command,
                    "supervision_mode": "restart-on-clean-exit",
                    "approval_mode": resolved_approval_mode,
                    "lane_count": len(lanes),
                    "worker_budget": worker_budget,
                    "lanes": [asdict(lane) for lane in lanes],
                },
            )
        script_path = build_session_script(
            provider=provider,
            repo_root=repo_root,
            prompt=prompt,
            approval_mode=resolved_approval_mode,
            dangerous=dangerous,
            script_path=script_path,
            log_path=log_path,
            resolve_cli_path_fn=resolve_cli_path_fn,
        )
        sessions.append(
            {
                "session_name": session_name,
                "provider": provider,
                "worker_budget": worker_budget,
                "approval_mode": resolved_approval_mode,
                "lane_count": len(lanes),
                "lanes": [asdict(lane) for lane in lanes],
                "script_path": str(script_path),
                "launch_command": launch_command,
                "log_path": str(log_path) if log_path is not None else None,
                "supervision_mode": "restart-on-clean-exit",
                "metadata_path": (
                    str(metadata_path) if metadata_path is not None else None
                ),
                "capture_mode": "terminal-script" if log_path is not None else None,
            }
        )
    return sessions


def _write_session_metadata(
    *,
    metadata_path: Path,
    payload: dict[str, object],
) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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
        script = [
            "tell application \"Terminal\"",
            "activate",
            f"do script {_apple_string(launch_command)}",
        ]
        if resolved_profile is not None and (
            not available_profiles or resolved_profile in available_profiles
        ):
            script.append(
                "set current settings of selected tab of front window to "
                f"settings set {_apple_string(resolved_profile)}"
            )
        script.append("end tell")
        subprocess.run(
            ["osascript", *[item for line in script for item in ("-e", line)]],
            check=True,
        )


def _apple_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
