"""Pre-launch preparation for bridge-backed review-channel actions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ...review_channel.bridge_runtime_state import BridgeStateContext
from ...review_channel.bridge_promotion import maybe_auto_promote_next_task
from ...review_channel.promotion import promote_bridge_instruction
from ...review_channel.bridge_runtime_state import enforce_bridge_launch_attention
from ...review_channel.launch import list_terminal_profiles
from .bridge_action_support import BridgePromotionContext, resolve_promotion_and_terminal_state
from .bridge_launch_control import prepare_rollover_bundle
from .bridge_support import (
    apply_scope_if_requested,
    bridge_launch_state,
    build_bridge_guard_report,
)


@dataclass(frozen=True)
class BridgeActionPreparation:
    promotion_plan_path: Path | None
    bridge_state: object
    promotion: object | None
    terminal_profile_applied: str | None
    warnings: list[str]
    handoff_bundle: object | None


@dataclass(frozen=True)
class BridgeActionPreparationRequest:
    args: object
    repo_root: Path
    review_channel_path: Path
    bridge_path: Path
    rollover_dir: Path
    status_dir: Path
    promotion_plan_path: Path | None
    bridge_actions: set[str]
    extra_warnings: list[str] | None


def prepare_bridge_action(
    *,
    request: BridgeActionPreparationRequest,
    build_bridge_guard_report_fn: Callable[..., dict[str, object]] | None = None,
    list_terminal_profiles_fn: Callable[[], list[str]] | None = None,
) -> BridgeActionPreparation:
    """Resolve bridge state, promotion, warnings, and rollover bundle."""
    scope_promotion = apply_scope_if_requested(
        args=request.args,
        repo_root=request.repo_root,
        bridge_path=request.bridge_path,
    )
    prelaunch_promotion, prelaunch_promotion_warnings = maybe_auto_promote_next_task(
        args=request.args,
        repo_root=request.repo_root,
        bridge_path=request.bridge_path,
        promotion_plan_path=request.promotion_plan_path,
        promote_bridge_instruction_fn=promote_bridge_instruction,
    )
    bridge_state = bridge_launch_state(
        args=request.args,
        context=BridgeStateContext(
            repo_root=request.repo_root,
            review_channel_path=request.review_channel_path,
            bridge_path=request.bridge_path,
            status_dir=request.status_dir,
        ),
        bridge_actions=request.bridge_actions,
        build_bridge_guard_report_fn=build_bridge_guard_report_fn
        or build_bridge_guard_report,
    )
    enforce_bridge_launch_attention(
        action=request.args.action,
        bridge_actions=request.bridge_actions,
        bridge_liveness=bridge_state.bridge_liveness,
    )
    promotion, terminal_profile_applied, warnings = resolve_promotion_and_terminal_state(
        args=request.args,
        context=BridgePromotionContext(
            repo_root=request.repo_root,
            review_channel_path=request.review_channel_path,
            bridge_path=request.bridge_path,
            promotion_plan_path=request.promotion_plan_path,
            codex_lanes=bridge_state.codex_lanes,
            claude_lanes=bridge_state.claude_lanes,
        ),
        list_terminal_profiles_fn=list_terminal_profiles_fn or list_terminal_profiles,
    )
    promotion = promotion or scope_promotion or prelaunch_promotion
    warnings = [
        *list(request.extra_warnings or []),
        *prelaunch_promotion_warnings,
        *warnings,
    ]
    if request.promotion_plan_path is None:
        warnings.append(
            "Scoped promotion plan unresolved; auto-promotion is disabled until bridge/tracker scope is set."
        )
    handoff_bundle, handoff_warnings = prepare_rollover_bundle(
        args=request.args,
        repo_root=request.repo_root,
        bridge_path=request.bridge_path,
        review_channel_path=request.review_channel_path,
        rollover_dir=request.rollover_dir,
        lanes=bridge_state.lanes,
    )
    warnings.extend(handoff_warnings)
    return BridgeActionPreparation(
        promotion_plan_path=request.promotion_plan_path,
        bridge_state=bridge_state,
        promotion=promotion,
        terminal_profile_applied=terminal_profile_applied,
        warnings=warnings,
        handoff_bundle=handoff_bundle,
    )


__all__ = [
    "BridgeActionPreparation",
    "BridgeActionPreparationRequest",
    "prepare_bridge_action",
]
