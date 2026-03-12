"""Action-only support helpers for bridge-backed `devctl review-channel` flows."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ..approval_mode import normalize_approval_mode
from ..common import display_path
from ..review_channel.core import (
    DEFAULT_TERMINAL_PROFILE,
    REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
    detect_active_session_conflicts,
    summarize_active_session_conflicts,
)
from ..review_channel.event_store import ReviewChannelArtifactPaths, event_state_exists
from ..review_channel.events import post_packet
from ..review_channel.handoff import handoff_bundle_to_dict
from ..review_channel.launch import (
    build_launch_sessions,
    list_terminal_profiles,
    resolve_cli_path,
    resolve_terminal_profile_name,
)
from ..review_channel.promotion import promote_bridge_instruction
from .review_channel_bridge_support import (
    bridge_launch_state,
    build_bridge_guard_report,
)


@dataclass(frozen=True)
class BridgePromotionContext:
    repo_root: Path
    review_channel_path: Path
    bridge_path: Path
    promotion_plan_path: Path
    codex_lanes: list
    claude_lanes: list


@dataclass(frozen=True)
class BridgeSessionContext:
    repo_root: Path
    review_channel_path: Path
    bridge_path: Path
    bridge_liveness: dict[str, object]
    codex_lanes: list
    claude_lanes: list
    cursor_lanes: list | None
    handoff_bundle: object | None
    promotion_plan_path: Path
    script_dir: Path | None
    status_dir: Path


@dataclass(frozen=True)
class BridgeLifecycleEventContext:
    repo_root: Path
    review_channel_path: Path
    artifact_paths: ReviewChannelArtifactPaths | None
    sessions: list[dict[str, object]]


def validate_live_launch_conflicts(
    *,
    args,
    status_dir: Path,
    detect_active_session_conflicts_fn: Callable[..., object] | None = None,
    summarize_active_session_conflicts_fn: Callable[..., str] | None = None,
) -> None:
    """Reject live Terminal launches when previous session traces still look active."""
    if detect_active_session_conflicts_fn is None:
        detect_active_session_conflicts_fn = detect_active_session_conflicts
    if summarize_active_session_conflicts_fn is None:
        summarize_active_session_conflicts_fn = summarize_active_session_conflicts
    if args.action == "launch" and args.terminal == "terminal-app" and not args.dry_run:
        active_session_conflicts = detect_active_session_conflicts_fn(
            session_output_root=status_dir,
        )
        if active_session_conflicts:
            raise ValueError(
                "Live review-channel launch refused because existing session "
                "artifacts still look active. Close the current conductor "
                "windows or wait for the session traces to go stale before "
                "launching again: " + summarize_active_session_conflicts_fn(active_session_conflicts)
            )


def resolve_terminal_launch_state(
    args,
    *,
    codex_lanes: list,
    claude_lanes: list,
    list_terminal_profiles_fn: Callable[[], list[str]] | None = None,
) -> tuple[str | None, list[str]]:
    """Resolve the Terminal.app profile and collect launch-readiness warnings."""
    if list_terminal_profiles_fn is None:
        list_terminal_profiles_fn = list_terminal_profiles
    warnings: list[str] = []
    available_profiles = list_terminal_profiles_fn() if args.terminal == "terminal-app" else []
    terminal_profile_applied = resolve_terminal_profile_name(
        args.terminal_profile,
        available_profiles=available_profiles,
    )
    if args.codex_workers > len(codex_lanes):
        warnings.append(
            "Requested Codex worker budget exceeds the current lane table; "
            f"using {len(codex_lanes)} advertised Codex lanes."
        )
    if args.claude_workers > len(claude_lanes):
        warnings.append(
            "Requested Claude worker budget exceeds the current lane table; "
            f"using {len(claude_lanes)} advertised Claude lanes."
        )
    if args.terminal == "terminal-app" and args.terminal_profile == "auto-dark" and terminal_profile_applied is None:
        warnings.append(
            "No known dark Terminal.app profile was found; live launch will "
            "fall back to the current Terminal default."
        )
    if (
        args.terminal == "terminal-app"
        and args.terminal_profile not in {"auto-dark", "default", "system", "none"}
        and available_profiles
        and terminal_profile_applied not in available_profiles
    ):
        warnings.append(
            f"Requested Terminal profile `{args.terminal_profile}` was not "
            "found; live launch will fall back to the current Terminal default."
        )
        terminal_profile_applied = None
    return terminal_profile_applied, warnings


def resolve_promotion_and_terminal_state(
    *,
    args,
    context: BridgePromotionContext,
    list_terminal_profiles_fn: Callable[[], list[str]] | None = None,
    promote_bridge_instruction_fn: Callable[..., object] | None = None,
    bridge_launch_state_fn: Callable[..., tuple] | None = None,
) -> tuple[object, str | None, list[str]]:
    """Resolve terminal warnings or execute the promote-side bridge refresh."""
    if list_terminal_profiles_fn is None:
        list_terminal_profiles_fn = list_terminal_profiles
    if promote_bridge_instruction_fn is None:
        promote_bridge_instruction_fn = promote_bridge_instruction
    if bridge_launch_state_fn is None:
        bridge_launch_state_fn = bridge_launch_state

    promotion = None
    if args.action != "promote":
        terminal_profile_applied, warnings = resolve_terminal_launch_state(
            args,
            codex_lanes=context.codex_lanes,
            claude_lanes=context.claude_lanes,
            list_terminal_profiles_fn=list_terminal_profiles_fn,
        )
        return promotion, terminal_profile_applied, warnings

    promotion = promote_bridge_instruction_fn(
        repo_root=context.repo_root,
        bridge_path=context.bridge_path,
        promotion_plan_path=context.promotion_plan_path,
    )
    bridge_launch_state_fn(
        args=args,
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        bridge_path=context.bridge_path,
        bridge_actions={"launch", "rollover"},
        build_bridge_guard_report_fn=build_bridge_guard_report,
    )
    return promotion, None, []


def build_bridge_sessions(
    *,
    args,
    context: BridgeSessionContext,
    resolve_cli_path_fn: Callable[..., object] | None = None,
    build_launch_sessions_fn: Callable[..., list[dict[str, object]]] | None = None,
) -> list[dict[str, object]]:
    """Build session descriptors for launch/rollover actions."""
    if args.action not in {"launch", "rollover"}:
        return []
    if resolve_cli_path_fn is None:
        resolve_cli_path_fn = resolve_cli_path
    if build_launch_sessions_fn is None:
        build_launch_sessions_fn = build_launch_sessions

    effective_cursor_lanes = context.cursor_lanes or []
    approval_mode = normalize_approval_mode(
        getattr(args, "approval_mode", None),
        dangerous=bool(args.dangerous),
    )
    effective_resolve_cli_path = resolve_cli_path_fn
    if resolve_cli_path_fn is resolve_cli_path:
        effective_resolve_cli_path = _resolve_cli_path_or_provider_name
    return build_launch_sessions_fn(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        bridge_path=context.bridge_path,
        codex_lanes=context.codex_lanes,
        claude_lanes=context.claude_lanes,
        codex_workers=min(args.codex_workers, len(context.codex_lanes)),
        claude_workers=min(args.claude_workers, len(context.claude_lanes)),
        cursor_lanes=effective_cursor_lanes,
        cursor_workers=min(
            getattr(args, "cursor_workers", len(effective_cursor_lanes)),
            len(effective_cursor_lanes),
        ),
        approval_mode=approval_mode,
        dangerous=bool(args.dangerous),
        rollover_threshold_pct=args.rollover_threshold_pct,
        await_ack_seconds=args.await_ack_seconds,
        default_terminal_profile=DEFAULT_TERMINAL_PROFILE,
        retirement_note=REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
        promotion_plan_rel=display_path(
            context.promotion_plan_path,
            repo_root=context.repo_root,
        ),
        bridge_liveness=context.bridge_liveness,
        handoff_bundle=handoff_bundle_to_dict(context.handoff_bundle),
        script_dir=context.script_dir if isinstance(context.script_dir, Path) else None,
        session_output_root=context.status_dir,
        resolve_cli_path_fn=effective_resolve_cli_path,
    )


def _resolve_cli_path_or_provider_name(provider: str) -> str:
    """Prefer an absolute CLI path, but keep dry-run/script generation portable.

    Review-channel tests and dry-run/script-only flows should not depend on the
    current workstation or CI runner already having every provider CLI installed
    before the script is even written. When the default resolver cannot find a
    provider binary on PATH, fall back to the provider command name so the
    generated launcher script still reflects the intended invocation.
    """
    try:
        return resolve_cli_path(provider)
    except ValueError:
        return provider


def post_session_lifecycle_event(
    *,
    action: str,
    context: BridgeLifecycleEventContext,
    post_packet_fn: Callable[..., object] | None = None,
    event_state_exists_fn: Callable[[ReviewChannelArtifactPaths], bool] | None = None,
) -> None:
    """Post a bridge launch/rollover notice into the review-channel event store."""
    if post_packet_fn is None:
        post_packet_fn = post_packet
    if event_state_exists_fn is None:
        event_state_exists_fn = event_state_exists
    if context.artifact_paths is None or not event_state_exists_fn(context.artifact_paths):
        return

    provider_names = [str(session.get("provider", "")).capitalize() for session in context.sessions]
    label = "rollover" if action == "rollover" else "launch"
    summary = f"Session {label}: {', '.join(provider_names)} conductors started"
    lane_counts = [
        f"{session.get('provider', '?')}: {session.get('lane_count', 0)} lanes" for session in context.sessions
    ]
    body = (
        f"The operator {label}ed {len(context.sessions)} conductor session(s). "
        f"Lane allocation: {'; '.join(lane_counts)}."
    )
    with contextlib.suppress(OSError, ValueError):
        post_packet_fn(
            repo_root=context.repo_root,
            review_channel_path=context.review_channel_path,
            artifact_paths=context.artifact_paths,
            from_agent="system",
            to_agent="operator",
            kind="system_notice",
            summary=summary,
            body=body,
            evidence_refs=[],
            context_pack_refs=[],
            confidence=1.0,
            requested_action="review_only",
            policy_hint="review_only",
            approval_required=False,
            expires_in_minutes=60,
        )
