"""Session-building adapter for bridge-backed review-channel actions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...review_channel.launch import (
    build_launch_sessions as default_build_launch_sessions,
    resolve_cli_path as default_resolve_cli_path,
)
from .bridge_action_support import (
    BridgeSessionContext,
    build_bridge_sessions,
    resolve_launch_interaction_mode,
)


@dataclass(frozen=True)
class BridgeSessionBuildContext:
    repo_root: Path
    review_channel_path: Path
    bridge_path: Path
    status_dir: Path
    script_dir: object
    promotion_plan_path: Path | None
    bridge_state: object
    handoff_bundle: object | None


def build_sessions_for_bridge_action(
    *,
    args,
    context: BridgeSessionBuildContext,
    resolve_cli_path_fn=None,
    build_launch_sessions_fn=None,
) -> tuple[list[dict[str, object]], str]:
    """Build launch sessions and return the governed interaction mode."""
    if resolve_cli_path_fn is None:
        resolve_cli_path_fn = default_resolve_cli_path
    if build_launch_sessions_fn is None:
        build_launch_sessions_fn = default_build_launch_sessions
    interaction_mode = resolve_launch_interaction_mode(
        repo_root=context.repo_root,
        args_fallback=str(getattr(args, "operator_interaction_mode", "") or ""),
    )
    sessions = build_bridge_sessions(
        args=args,
        context=BridgeSessionContext(
            repo_root=context.repo_root,
            review_channel_path=context.review_channel_path,
            bridge_path=context.bridge_path,
            bridge_liveness=context.bridge_state.bridge_liveness,
            codex_lanes=context.bridge_state.codex_lanes,
            claude_lanes=context.bridge_state.claude_lanes,
            cursor_lanes=context.bridge_state.cursor_lanes,
            handoff_bundle=context.handoff_bundle,
            promotion_plan_path=context.promotion_plan_path,
            script_dir=(
                context.script_dir if isinstance(context.script_dir, Path) else None
            ),
            status_dir=context.status_dir,
            interaction_mode=interaction_mode,
        ),
        resolve_cli_path_fn=resolve_cli_path_fn,
        build_launch_sessions_fn=build_launch_sessions_fn,
    )
    return sessions, interaction_mode
