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
from ...review_channel.projection_bundle import projection_paths_to_dict
from ...review_channel.recover_support import (
    RecoverReportInput,
    RecoverSessionBuildInput,
    base_recover_report,
    has_role_lanes,
    planned_provider_for_role,
    recover_error,
    recover_projection_errors,
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
        return _invalid_recover_state_report(
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
        return _invalid_recover_state_report(
            args=args,
            status_snapshot=status_snapshot,
            validation_error=validation_error,
            provider=provider,
        )

    terminal_profile_applied, current_instruction_revision, sessions = _build_recover_sessions(
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
    launched, recover_ack_observed, exit_code = _maybe_launch_recover_sessions(
        args=args,
        bridge_path=bridge_path,
        current_instruction_revision=current_instruction_revision,
        sessions=sessions,
        terminal_profile_applied=terminal_profile_applied,
    )
    refreshed_snapshot = refresh_recover_snapshot(
        args=args,
        repo_root=repo_root,
        runtime_paths=runtime_paths,
    )
    report = _recover_report(
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
    )
    )
    return report, exit_code


def _invalid_recover_state_report(
    *,
    args,
    status_snapshot,
    validation_error: str,
    provider: str,
) -> tuple[dict[str, object], int]:
    report = base_recover_report(args)
    report["bridge_active"] = True
    report["bridge_liveness"] = status_snapshot.bridge_liveness
    report["attention"] = status_snapshot.attention
    report["warnings"] = status_snapshot.warnings
    report["errors"] = [validation_error]
    report["recover_provider"] = provider
    report["sessions"] = []
    return report, 1


def _build_recover_sessions(
    build_input: RecoverSessionBuildInput,
) -> tuple[str | None, str, list[dict[str, object]]]:
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
        ),
    )
    return terminal_profile_applied, current_instruction_revision, sessions


def _maybe_launch_recover_sessions(
    *,
    args,
    bridge_path: Path,
    current_instruction_revision: str,
    sessions: list[dict[str, object]],
    terminal_profile_applied: str | None,
) -> tuple[bool, dict[str, object] | None, int]:
    launched = False
    recover_ack_observed: dict[str, object] | None = None
    exit_code = 0
    if (
        getattr(args, "terminal", "none") == "terminal-app"
        and not bool(getattr(args, "dry_run", False))
    ):
        launch_terminal_sessions(
            sessions,
            terminal_profile=terminal_profile_applied,
            default_terminal_profile=DEFAULT_TERMINAL_PROFILE,
            auto_dark_terminal_profiles=AUTO_DARK_TERMINAL_PROFILES,
        )
        launched = True
        if int(getattr(args, "await_ack_seconds", 0) or 0) > 0:
            recover_ack_observed = wait_for_claude_ack_refresh(
                bridge_path=bridge_path,
                expected_instruction_revision=current_instruction_revision,
                timeout_seconds=int(getattr(args, "await_ack_seconds", 180)),
            )
            if not bool(recover_ack_observed.get("observed")):
                exit_code = 1
    return launched, recover_ack_observed, exit_code


def _recover_report(
    report_input: RecoverReportInput,
) -> dict[str, object]:
    args = report_input.args
    refreshed_snapshot = report_input.refreshed_snapshot
    exit_code = report_input.exit_code
    provider = report_input.provider
    current_instruction_revision = report_input.current_instruction_revision
    sessions = report_input.sessions
    terminal_profile_applied = report_input.terminal_profile_applied
    launched = report_input.launched
    recover_ack_observed = report_input.recover_ack_observed
    report = base_recover_report(args)
    report["ok"] = exit_code == 0
    report["exit_ok"] = exit_code == 0
    report["exit_code"] = exit_code
    report["bridge_active"] = True
    report["bridge_liveness"] = refreshed_snapshot.bridge_liveness
    report["attention"] = refreshed_snapshot.attention
    report["warnings"] = list(refreshed_snapshot.warnings)
    report["errors"] = recover_projection_errors(refreshed_snapshot.errors)
    report["projection_paths"] = projection_paths_to_dict(
        refreshed_snapshot.projection_paths
    )
    report["reviewer_worker"] = refreshed_snapshot.reviewer_worker
    report["service_identity"] = refreshed_snapshot.service_identity
    report["attach_auth_policy"] = refreshed_snapshot.attach_auth_policy
    report["recover_provider"] = provider
    report["recover_target_revision"] = current_instruction_revision
    report["sessions"] = sessions
    report["terminal_profile_applied"] = terminal_profile_applied
    report["launched"] = launched
    report["recover_ack_observed"] = recover_ack_observed
    if exit_code != 0 and recover_ack_observed is not None:
        report["errors"].append(
            f"Fresh {provider.title()} conductor did not write a current ACK before the recovery timeout expired."
        )
    return report
