"""CLI and Terminal-app launch helpers for the transitional review channel."""

from __future__ import annotations

import os
import shlex
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, NamedTuple

from ..approval_mode import DEFAULT_APPROVAL_MODE, normalize_approval_mode
from ..time_utils import utc_timestamp
from .launch_records import (
    LaunchSessionRequest,
    PreparedSessionRecord,
    legacy_provider_lane_map,
    resolve_session_workspace_root,
    session_output_paths,
)
from .launch_authority import build_prepared_launch_authority, current_head_sha
from .launch_bypass import resolve_launch_bypass_lifecycle
from .launch_commands import (
    build_promote_command as _build_promote_command,
    build_rollover_command as _build_rollover_command,
)
from .launch_topology import ConductorLaunchSpec, build_conductor_launch_specs
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


def build_rollover_command(
    *,
    rollover_threshold_pct: int,
    await_ack_seconds: int,
    approval_mode: str = DEFAULT_APPROVAL_MODE,
    dangerous: bool = False,
    bypass_receipt_id: str = "",
) -> str:
    """Return the canonical self-relaunch command for planned rollovers."""
    return _build_rollover_command(
        rollover_threshold_pct=rollover_threshold_pct,
        await_ack_seconds=await_ack_seconds,
        approval_mode=approval_mode,
        dangerous=dangerous,
        bypass_receipt_id=bypass_receipt_id,
        interpreter=_DEVCTL_INTERPRETER,
    )


def build_promote_command(
    *,
    promotion_plan_rel: str,
) -> str:
    """Return the canonical typed next-task promotion command."""
    return _build_promote_command(
        promotion_plan_rel=promotion_plan_rel,
        interpreter=_DEVCTL_INTERPRETER,
    )

# Demoted to NamedTuple: private internal call bundle for _build_launch_session.
# Not a typed contract surface; do not register with the platform contract sweep.
class _LaunchSessionBuildContext(NamedTuple):
    request: LaunchSessionRequest
    effective_script_dir: Path
    session_dir: Path | None
    review_state_path: Path | None
    prepared_instruction_revision: str
    prepared_session_token: str
    prepared_at: str
    resolved_approval_mode: str
    rollover_command: str
    promote_command: str
    bypass_lifecycle: object | None
    build_conductor_prompt_fn: Callable[..., str]
    resolve_cli_path_fn: Callable[[str], str]


def resolve_cli_path(provider: str) -> str:
    """Resolve the requested provider CLI from PATH."""
    cli_path = shutil.which(provider)
    if cli_path:
        return cli_path
    raise ValueError(f"Required CLI not found on PATH: {provider}")


def _build_launch_session(
    *,
    spec: object,
    context: _LaunchSessionBuildContext,
) -> dict[str, object]:
    request = context.request
    provider = spec.provider
    provider_name = spec.provider_name
    other_name = spec.counterpart_name
    lanes = list(spec.lanes)
    requested_worker_budget = spec.requested_worker_budget
    session_name = f"{provider}-conductor"
    workspace_root = resolve_session_workspace_root(
        repo_root=request.repo_root,
        lanes=lanes,
        default_worktree_path=request.worktree_path,
    )
    head_root = workspace_root if workspace_root is not None else request.repo_root
    prepared_head_sha = current_head_sha(head_root)
    log_path, metadata_path = session_output_paths(
        session_dir=context.session_dir,
        session_name=session_name,
    )
    prompt = context.build_conductor_prompt_fn(
        provider=provider,
        provider_name=provider_name,
        other_name=other_name,
        role=spec.role,
        other_provider=spec.counterpart_provider,
        repo_root=request.repo_root,
        review_channel_path=request.review_channel_path,
        bridge_path=request.bridge_path,
        lanes=lanes,
        workspace_root=workspace_root,
        codex_workers=request.codex_workers,
        claude_workers=request.claude_workers,
        requested_worker_budget=requested_worker_budget,
        approval_mode=context.resolved_approval_mode,
        dangerous=request.dangerous,
        rollover_threshold_pct=request.rollover_threshold_pct,
        await_ack_seconds=request.await_ack_seconds,
        retirement_note=request.retirement_note,
        rollover_command=context.rollover_command,
        promote_command=context.promote_command,
        bridge_liveness=request.bridge_liveness,
        handoff_bundle=request.handoff_bundle,
    )
    script_name = f"{provider}-conductor.sh"
    script_path = context.effective_script_dir / script_name
    launch_command = f"/bin/zsh {shlex.quote(str(script_path))}"
    session_record = PreparedSessionRecord(
        session_name=session_name,
        provider=provider,
        provider_name=provider_name,
        role=spec.role,
        approval_mode=context.resolved_approval_mode,
        planned_lanes=lanes,
        requested_worker_budget=requested_worker_budget,
        repo_root=request.repo_root,
        script_path=script_path,
        launch_command=launch_command,
        prepared_at=context.prepared_at,
        log_path=log_path,
        metadata_path=metadata_path,
        interaction_mode=request.interaction_mode,
        rollover_provider=request.rollover_provider,
        prepared_head_sha=prepared_head_sha,
        prepared_instruction_revision=context.prepared_instruction_revision,
        prepared_session_token=context.prepared_session_token,
        review_state_path=context.review_state_path,
        workspace_root=workspace_root,
    )
    session_record.write_metadata()
    script_path = build_session_script(
        provider=provider,
        repo_root=request.repo_root,
        workspace_root=workspace_root,
        prompt=prompt,
        role=spec.role,
        approval_mode=context.resolved_approval_mode,
        dangerous=request.dangerous,
        headless=request.headless,
        script_path=script_path,
        log_path=log_path,
        resolve_cli_path_fn=context.resolve_cli_path_fn,
        interaction_mode=request.interaction_mode,
        prepared_head_sha=prepared_head_sha,
        prepared_instruction_revision=context.prepared_instruction_revision,
        prepared_session_token=context.prepared_session_token,
        review_state_path=context.review_state_path,
        bypass_lifecycle=context.bypass_lifecycle,
    )
    session_record.script_path = script_path
    return session_record.report_payload()


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
        bypass_receipt_id=request.bypass_receipt_id,
        rollover_threshold_pct=request.rollover_threshold_pct,
        await_ack_seconds=request.await_ack_seconds,
    )
    resolved_approval_mode = normalize_approval_mode(
        request.approval_mode,
        dangerous=request.dangerous,
    )
    bypass_lifecycle = resolve_launch_bypass_lifecycle(
        request=request,
        resolved_approval_mode=resolved_approval_mode,
    )
    promote_command = build_promote_command(
        promotion_plan_rel=request.promotion_plan_rel,
    )
    session_dir = (
        (request.session_output_root / "sessions")
        if request.session_output_root is not None
        else None
    )
    review_state_path = (
        request.review_state_path
        if request.review_state_path is not None
        else (
            request.session_output_root / "review_state.json"
            if request.session_output_root is not None
            else None
        )
    )
    prepared_at = utc_timestamp()
    shared_authority = build_prepared_launch_authority(
        repo_root=request.repo_root,
        workspace_root=request.worktree_path,
        bridge_path=request.bridge_path,
        bridge_liveness=request.bridge_liveness,
        review_state_path=review_state_path,
    )
    context = _LaunchSessionBuildContext(
        request=request,
        effective_script_dir=effective_script_dir,
        session_dir=session_dir,
        review_state_path=review_state_path,
        prepared_instruction_revision=shared_authority.instruction_revision,
        prepared_session_token=shared_authority.session_token,
        prepared_at=prepared_at,
        resolved_approval_mode=resolved_approval_mode,
        rollover_command=rollover_command,
        promote_command=promote_command,
        bypass_lifecycle=bypass_lifecycle,
        build_conductor_prompt_fn=build_conductor_prompt_fn,
        resolve_cli_path_fn=resolve_cli_path_fn,
    )
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
        # Typed contract boundary: build_conductor_launch_specs must hand back
        # ConductorLaunchSpec instances so the lane assembly cannot silently
        # accept raw tuples.
        if not isinstance(spec, ConductorLaunchSpec):
            raise TypeError(
                "build_conductor_launch_specs must return ConductorLaunchSpec rows"
            )
        sessions.append(
            _build_launch_session(
                spec=spec,
                context=context,
            )
        )
    return sessions
