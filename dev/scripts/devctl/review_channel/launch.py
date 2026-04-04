"""CLI and Terminal-app launch helpers for the transitional review channel."""

from __future__ import annotations

import os
import shlex
import shutil
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from ..approval_mode import DEFAULT_APPROVAL_MODE, normalize_approval_mode
from ..time_utils import utc_timestamp
from .launch_records import (
    LaunchSessionRequest,
    PreparedSessionRecord,
    legacy_provider_lane_map,
    session_output_paths,
)
from .launch_topology import build_conductor_launch_specs
from .launch_script import build_session_script
from .prompt import build_conductor_prompt
from .terminal_app import (
    build_terminal_launch_lines,
    launch_terminal_sessions as launch_terminal_sessions,
    list_terminal_profiles as list_terminal_profiles,
    resolve_terminal_profile_name as resolve_terminal_profile_name,
)

if TYPE_CHECKING:
    from .core import LaneAssignment

_build_terminal_launch_lines = build_terminal_launch_lines

_DEVCTL_INTERPRETER = os.path.basename(sys.executable)
"""Interpreter name matching the runtime that loaded this module."""


def resolve_cli_path(provider: str) -> str:
    """Resolve the requested provider CLI from PATH."""
    cli_path = shutil.which(provider)
    if cli_path:
        return cli_path
    raise ValueError(f"Required CLI not found on PATH: {provider}")


def build_rollover_command(
    *,
    rollover_threshold_pct: int,
    await_ack_seconds: int,
    approval_mode: str = DEFAULT_APPROVAL_MODE,
    dangerous: bool = False,
) -> str:
    """Return the canonical self-relaunch command for planned rollovers."""
    command = [
        _DEVCTL_INTERPRETER,
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
        _DEVCTL_INTERPRETER,
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
    request: LaunchSessionRequest,
    build_conductor_prompt_fn: Callable[..., str] = build_conductor_prompt,
    resolve_cli_path_fn: Callable[[str], str] = resolve_cli_path,
) -> list[dict[str, object]]:
    """Create conductor launch scripts and return session metadata."""
    effective_script_dir = (
        request.script_dir
        if request.script_dir is not None
        else Path(tempfile.mkdtemp(prefix="review-channel-launch-"))
    )
    sessions: list[dict[str, object]] = []
    rollover_command = build_rollover_command(
        approval_mode=request.approval_mode,
        dangerous=request.dangerous,
        rollover_threshold_pct=request.rollover_threshold_pct,
        await_ack_seconds=request.await_ack_seconds,
    )
    resolved_approval_mode = normalize_approval_mode(
        request.approval_mode,
        dangerous=request.dangerous,
    )
    promote_command = build_promote_command(
        promotion_plan_rel=request.promotion_plan_rel,
    )
    session_dir = (
        (request.session_output_root / "sessions")
        if request.session_output_root is not None
        else None
    )
    prepared_at = utc_timestamp()
    launch_specs = build_conductor_launch_specs(
        provider_lane_map=request.provider_lane_map
        or legacy_provider_lane_map(
            codex_lanes=request.codex_lanes,
            claude_lanes=request.claude_lanes,
            cursor_lanes=request.cursor_lanes,
        ),
        requested_worker_budgets=request.requested_worker_budgets
        or {
            "codex": request.codex_workers,
            "claude": request.claude_workers,
            "cursor": request.cursor_workers,
        },
        providers_to_launch=request.providers_to_launch,
    )
    for spec in launch_specs:
        provider = spec.provider
        provider_name = spec.provider_name
        other_name = spec.counterpart_name
        lanes = list(spec.lanes)
        requested_worker_budget = spec.requested_worker_budget
        session_name = f"{provider}-conductor"
        log_path, metadata_path = session_output_paths(
            session_dir=session_dir,
            session_name=session_name,
        )
        prompt = build_conductor_prompt_fn(
            provider=provider,
            provider_name=provider_name,
            other_name=other_name,
            repo_root=request.repo_root,
            review_channel_path=request.review_channel_path,
            bridge_path=request.bridge_path,
            lanes=lanes,
            codex_workers=request.codex_workers,
            claude_workers=request.claude_workers,
            approval_mode=resolved_approval_mode,
            dangerous=request.dangerous,
            rollover_threshold_pct=request.rollover_threshold_pct,
            await_ack_seconds=request.await_ack_seconds,
            retirement_note=request.retirement_note,
            rollover_command=rollover_command,
            promote_command=promote_command,
            bridge_liveness=request.bridge_liveness,
            handoff_bundle=request.handoff_bundle,
        )
        script_name = f"{provider}-conductor.sh"
        script_path = effective_script_dir / script_name
        launch_command = f"/bin/zsh {shlex.quote(str(script_path))}"
        session_record = PreparedSessionRecord(
            session_name=session_name,
            provider=provider,
            provider_name=provider_name,
            role=spec.role,
            approval_mode=resolved_approval_mode,
            planned_lanes=lanes,
            requested_worker_budget=requested_worker_budget,
            repo_root=request.repo_root,
            script_path=script_path,
            launch_command=launch_command,
            prepared_at=prepared_at,
            log_path=log_path,
            metadata_path=metadata_path,
        )
        session_record.write_metadata()
        script_path = build_session_script(
            provider=provider,
            repo_root=request.repo_root,
            prompt=prompt,
            approval_mode=resolved_approval_mode,
            dangerous=request.dangerous,
            headless=request.headless,
            script_path=script_path,
            log_path=log_path,
            resolve_cli_path_fn=resolve_cli_path_fn,
        )
        session_record.script_path = script_path
        sessions.append(
            session_record.report_payload()
        )
    return sessions
