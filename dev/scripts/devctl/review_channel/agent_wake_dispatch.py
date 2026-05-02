"""Per-provider wake dispatcher for typed packet wake targets.

Extracted from `follow_controller` so the multi-mode wake dispatch
(codex reviewer-wake / non-codex headless-delegate / fallback relaunch)
can grow independently without inflating the follow_controller host
file beyond shape limits. Re-exported from `follow_controller` for
backward-compatible imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .headless_delegate import (
    can_delegate_dashboard_packet_headless,
    session_pids,
)
from .reviewer_follow_guard import (
    ReviewerWakeDeps,
    ReviewerWakeLaunchContext,
    cleanup_candidate_provider_sessions,
    cleanup_codex_sessions,
    has_blocking_cleanup_warning,
    launch_waiting_reviewer_conductor,
)
from .reviewer_follow_guard import as_path
from .wake_receipt_models import WakeReceiptExtras, wake_report


@dataclass(frozen=True)
class WakeRoutingContext:
    """Bundle of routing inputs every wake-dispatch helper needs.

    Keeps each downstream function under the parameter-count guard
    threshold (>6 fails for python). Matches the shape of the
    governed-executor's request envelope so the dispatch can later be
    composed with `safe_auto_apply` without re-marshalling.
    """

    args: object
    repo_root: Path
    paths: dict[str, object]
    report: dict[str, object]
    operator_interaction_mode: str


def maybe_wake_waiting_agent_conductor(
    *,
    routing: WakeRoutingContext,
    target_agent: str,
    packet: dict[str, object],
    maybe_wake_reviewer_fn,
    deps: ReviewerWakeDeps | None = None,
) -> dict[str, object] | None:
    """Relaunch (or headless-delegate) a provider conductor for a typed packet."""

    provider = str(target_agent or "").strip().lower()
    if not provider:
        return None
    if provider == "codex":
        return maybe_wake_reviewer_fn(
            args=routing.args,
            repo_root=routing.repo_root,
            paths=routing.paths,
            report=routing.report,
            operator_interaction_mode=routing.operator_interaction_mode,
            deps=deps,
        )

    wake_paths = _resolve_wake_paths(routing.paths)
    if wake_paths is None:
        return wake_report(
            packet=packet,
            attempted=True,
            woke=False,
            reason="runtime_paths_missing",
            target_agent=provider,
        )

    target_session_id = str(packet.get("target_session_id") or "").strip()
    if target_session_id:
        return _wake_target_session_packet(
            routing=routing,
            provider=provider,
            packet=packet,
            wake_paths=wake_paths,
            target_session_id=target_session_id,
            deps=deps,
        )

    return _wake_via_relaunch(
        routing=routing,
        provider=provider,
        packet=packet,
        wake_paths=wake_paths,
        deps=deps,
    )


def _wake_target_session_packet(
    *,
    routing: WakeRoutingContext,
    provider: str,
    packet: dict[str, object],
    wake_paths,
    target_session_id: str,
    deps: ReviewerWakeDeps | None,
) -> dict[str, object]:
    if can_delegate_dashboard_packet_headless(
        packet,
        operator_interaction_mode=routing.operator_interaction_mode,
        headless_requested=str(getattr(routing.args, "terminal", "") or "").strip()
        == "none",
    ):
        effective_deps = deps or ReviewerWakeDeps()
        target_role = str(packet.get("target_role") or "").strip()
        return launch_waiting_reviewer_conductor(
            context=ReviewerWakeLaunchContext(
                args=routing.args,
                repo_root=routing.repo_root,
                paths=routing.paths,
                report=routing.report,
                packet=packet,
                wake_paths=wake_paths,
                cleanup_warnings=(),
                operator_interaction_mode=routing.operator_interaction_mode,
                provider=provider,
                wake_method_override="headless_delegate",
                target_role=target_role,
                target_session_id=target_session_id,
                dashboard_session_id=target_session_id,
            ),
            deps=effective_deps,
        )
    return wake_report(
        packet=packet,
        attempted=True,
        woke=False,
        reason="target_session_unreachable_without_registry",
        target_agent=provider,
        extras=WakeReceiptExtras(
            target_role=str(packet.get("target_role") or "").strip(),
            target_session_id=target_session_id,
            wake_method="unreachable_until_operator_prompt",
        ),
    )


def _wake_via_relaunch(
    *,
    routing: WakeRoutingContext,
    provider: str,
    packet: dict[str, object],
    wake_paths,
    deps: ReviewerWakeDeps | None,
) -> dict[str, object]:
    effective_deps = deps or ReviewerWakeDeps()
    cleanup_sessions = cleanup_candidate_provider_sessions(
        session_output_root=wake_paths.status_dir,
        provider=provider,
        deps=effective_deps,
    )
    cleanup_warnings: list[str] = []
    if cleanup_sessions:
        cleanup_warnings = cleanup_codex_sessions(
            live_codex_sessions=cleanup_sessions,
            deps=effective_deps,
        )
    if has_blocking_cleanup_warning(cleanup_warnings):
        return wake_report(
            packet=packet,
            attempted=True,
            woke=False,
            reason="cleanup_failed",
            target_agent=provider,
            extras=WakeReceiptExtras(warnings=tuple(cleanup_warnings)),
        )

    return launch_waiting_reviewer_conductor(
        context=ReviewerWakeLaunchContext(
            args=routing.args,
            repo_root=routing.repo_root,
            paths=routing.paths,
            report=routing.report,
            packet=packet,
            wake_paths=wake_paths,
            cleanup_warnings=tuple(cleanup_warnings),
            operator_interaction_mode=routing.operator_interaction_mode,
            provider=provider,
            replaced_session_count=len(cleanup_sessions),
            replaced_pids=session_pids(cleanup_sessions),
        ),
        deps=effective_deps,
    )


def _resolve_wake_paths(paths: dict[str, object]):
    """Local wake-path resolver mirroring the host module's contract."""
    from .reviewer_follow_guard import ReviewerWakePaths

    status_dir = as_path(paths.get("status_dir"))
    review_channel_path = as_path(paths.get("review_channel_path"))
    bridge_path = as_path(paths.get("bridge_path"))
    if status_dir is None or review_channel_path is None or bridge_path is None:
        return None
    return ReviewerWakePaths(
        status_dir=status_dir,
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
    )
