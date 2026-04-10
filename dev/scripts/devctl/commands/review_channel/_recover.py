"""Repo-owned stale-implementer recovery for review-channel conductor sessions."""

from __future__ import annotations

from pathlib import Path

from ...review_channel.core import (
    AUTO_DARK_TERMINAL_PROFILES,
    DEFAULT_TERMINAL_PROFILE,
    ensure_launcher_prereqs,
    filter_provider_lanes,
)
from ...review_channel.launch import (
    build_launch_sessions,
    launch_terminal_sessions,
    list_terminal_profiles,
    resolve_terminal_profile_name,
)
from ...review_channel.launch_records import LaunchSessionRequest
from ...review_channel.recover_support import (
    RecoverLaunchInput,
    RecoverReportInput,
    RecoverSessionBuildInput,
    has_role_lanes,
    invalid_recover_state_report,
    planned_provider_for_role,
    recover_report,
    recover_error,
    recover_worker_budget,
    refresh_recover_snapshot,
    resolve_recover_provider,
    validate_live_reviewer_session_for_recover,
    validate_recover_runtime_paths,
    validate_recoverable_state,
    wait_for_claude_ack_refresh,
)
from ...runtime.role_profile import TandemRole, default_provider_for_role
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths
from .launcher_discipline import (
    enforce_launch_request_discipline,
)
from .bridge_launch_headless import (
    launch_sessions_headless as _launch_sessions_headless,
)
from .bridge_action_support import (
    resolve_launch_interaction_mode,
)


def run_recover_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths,
) -> tuple[dict[str, object], int]:
    """Launch one fresh implementer conductor and wait for a current ACK."""
    runtime_paths = _coerce_runtime_paths(paths)
    path_error = validate_recover_runtime_paths(runtime_paths)
    if path_error is not None:
        return recover_error(args, path_error)
    bridge_path = runtime_paths.bridge_path
    review_channel_path = runtime_paths.review_channel_path
    status_dir = runtime_paths.status_dir
    assert isinstance(bridge_path, Path)
    assert isinstance(review_channel_path, Path)
    assert isinstance(status_dir, Path)

    provider = resolve_recover_provider(args)
    if provider is None:
        return recover_error(
            args,
            f"Unsupported recover provider: {getattr(args, 'recover_provider', None)}",
        )

    status_snapshot = refresh_recover_snapshot(
        args=args,
        repo_root=repo_root,
        runtime_paths=runtime_paths,
    )
    _, lanes = ensure_launcher_prereqs(
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        execution_mode=getattr(args, "execution_mode", "markdown-bridge"),
    )
    reviewer_provider = planned_provider_for_role(
        lanes,
        role=TandemRole.REVIEWER,
        default=default_provider_for_role(TandemRole.REVIEWER),
    )
    recover_lanes = filter_provider_lanes(lanes, provider=provider)
    if not has_role_lanes(recover_lanes, role=TandemRole.IMPLEMENTER):
        return recover_error(
            args,
            "review-channel recover requires at least one implementer lane for the requested provider in review_channel.md.",
        )
    peer_session_error = validate_live_reviewer_session_for_recover(
        status_dir=status_dir,
        reviewer_provider=reviewer_provider,
        recover_provider=provider,
    )
    if peer_session_error is not None:
        return invalid_recover_state_report(
            args=args,
            status_snapshot=status_snapshot,
            validation_error=peer_session_error,
            provider=provider,
        )
    validation_error = validate_recoverable_state(
        bridge_liveness=status_snapshot.bridge_liveness,
        attention=status_snapshot.attention,
    )
    if validation_error is not None:
        return invalid_recover_state_report(
            args=args,
            status_snapshot=status_snapshot,
            validation_error=validation_error,
            provider=provider,
        )

    (
        terminal_profile_applied,
        current_instruction_revision,
        sessions,
        interaction_mode,
    ) = _build_recover_sessions(
        RecoverSessionBuildInput(
            args=args,
            repo_root=repo_root,
            runtime_paths=runtime_paths,
            status_snapshot=status_snapshot,
            reviewer_provider=reviewer_provider,
            recover_provider=provider,
            provider_lane_map={
                reviewer_provider: filter_provider_lanes(
                    lanes,
                    provider=reviewer_provider,
                ),
                provider: recover_lanes,
            },
        )
    )
    launched, recover_ack_observed, exit_code, launch_warnings = _maybe_launch_recover_sessions(
        RecoverLaunchInput(
            args=args,
            repo_root=repo_root,
            bridge_path=bridge_path,
            current_instruction_revision=current_instruction_revision,
            sessions=sessions,
            terminal_profile_applied=terminal_profile_applied,
            interaction_mode=interaction_mode,
        )
    )
    refreshed_snapshot = refresh_recover_snapshot(
        args=args,
        repo_root=repo_root,
        runtime_paths=runtime_paths,
    )
    report = recover_report(
        RecoverReportInput(
            args=args,
            refreshed_snapshot=refreshed_snapshot,
            exit_code=exit_code,
            provider=provider,
            current_instruction_revision=current_instruction_revision,
            sessions=sessions,
            terminal_profile_applied=terminal_profile_applied,
            launched=launched,
            recover_ack_observed=recover_ack_observed,
            launch_warnings=launch_warnings,
    )
    )
    return report, exit_code


def _build_recover_sessions(
    build_input: RecoverSessionBuildInput,
) -> tuple[str | None, str, list[dict[str, object]], str]:
    args = build_input.args
    repo_root = build_input.repo_root
    runtime_paths = build_input.runtime_paths
    status_snapshot = build_input.status_snapshot
    reviewer_provider = build_input.reviewer_provider
    recover_provider = build_input.recover_provider
    provider_lane_map = build_input.provider_lane_map
    bridge_path = runtime_paths.bridge_path
    review_channel_path = runtime_paths.review_channel_path
    status_dir = runtime_paths.status_dir
    assert isinstance(bridge_path, Path)
    assert isinstance(review_channel_path, Path)
    assert isinstance(status_dir, Path)
    available_profiles = (
        list_terminal_profiles()
        if getattr(args, "terminal", "none") == "terminal-app"
        else []
    )
    terminal_profile_applied = resolve_terminal_profile_name(
        getattr(args, "terminal_profile", None),
        available_profiles=available_profiles,
    )
    current_instruction_revision = str(
        status_snapshot.bridge_liveness.get("current_instruction_revision") or ""
    )
    interaction_mode = resolve_launch_interaction_mode(
        repo_root=repo_root,
        args_fallback=str(getattr(args, "operator_interaction_mode", "") or ""),
    )
    sessions = build_launch_sessions(
        request=LaunchSessionRequest(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            bridge_path=bridge_path,
            codex_lanes=[],
            claude_lanes=[],
            codex_workers=min(
                int(getattr(args, "codex_workers", 0) or 0),
                len(provider_lane_map.get("codex", ())),
            ),
            claude_workers=min(
                int(getattr(args, "claude_workers", 0) or 0),
                len(provider_lane_map.get("claude", ())),
            ),
            provider_lane_map=provider_lane_map,
            requested_worker_budgets={
                recover_provider: recover_worker_budget(
                    args=args,
                    provider=recover_provider,
                    lane_count=len(provider_lane_map.get(recover_provider, ())),
                ),
                reviewer_provider: recover_worker_budget(
                    args=args,
                    provider=reviewer_provider,
                    lane_count=len(provider_lane_map.get(reviewer_provider, ())),
                ),
            },
            rollover_threshold_pct=int(getattr(args, "rollover_threshold_pct", 50)),
            await_ack_seconds=int(getattr(args, "await_ack_seconds", 180)),
            retirement_note=(
                f"Recovery launcher: replace the stale {recover_provider.title()} conductor from repo state "
                "and wait for a current ACK before trusting the loop again."
            ),
            promotion_plan_rel="dev/active/review_channel.md",
            approval_mode=getattr(args, "approval_mode", None),
            dangerous=bool(getattr(args, "dangerous", False)),
            bridge_liveness=status_snapshot.bridge_liveness,
            handoff_bundle=None,
            script_dir=runtime_paths.script_dir,
            session_output_root=status_dir,
            providers_to_launch=(recover_provider,),
            interaction_mode=interaction_mode,
        ),
    )
    return (
        terminal_profile_applied,
        current_instruction_revision,
        sessions,
        interaction_mode,
    )


def _maybe_launch_recover_sessions(
    launch_input: RecoverLaunchInput,
) -> tuple[bool, dict[str, object] | None, int, list[str]]:
    launched = False
    recover_ack_observed: dict[str, object] | None = None
    exit_code = 0
    launch_warnings: list[str] = []
    args = launch_input.args
    terminal = str(getattr(args, "terminal", "none"))
    if not bool(getattr(args, "dry_run", False)) and terminal in {
        "terminal-app",
        "none",
    }:
        enforce_launch_request_discipline(
            repo_root=launch_input.repo_root,
            interaction_mode=launch_input.interaction_mode,
            terminal_arg=terminal,
        )
        if terminal == "terminal-app":
            launch_terminal_sessions(
                launch_input.sessions,
                terminal_profile=launch_input.terminal_profile_applied,
                default_terminal_profile=DEFAULT_TERMINAL_PROFILE,
                auto_dark_terminal_profiles=AUTO_DARK_TERMINAL_PROFILES,
            )
            launched = True
        else:
            launched = _launch_sessions_headless(
                launch_input.sessions, launch_warnings
            )
        if launched and int(getattr(args, "await_ack_seconds", 0) or 0) > 0:
            recover_ack_observed = wait_for_claude_ack_refresh(
                bridge_path=launch_input.bridge_path,
                expected_instruction_revision=launch_input.current_instruction_revision,
                timeout_seconds=int(getattr(args, "await_ack_seconds", 180)),
            )
            if not bool(recover_ack_observed.get("observed")):
                exit_code = 1
    return launched, recover_ack_observed, exit_code, launch_warnings
