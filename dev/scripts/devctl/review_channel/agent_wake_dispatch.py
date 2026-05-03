"""Per-provider wake dispatcher for typed packet wake targets.

Extracted from `follow_controller` so the multi-mode wake dispatch
(legacy reviewer-wake / dashboard poll / visible worker / fallback relaunch)
can grow independently without inflating the follow_controller host
file beyond shape limits. Re-exported from `follow_controller` for
backward-compatible imports.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .headless_delegate import (
    packet_targets_dashboard_poll,
    requested_worker_visibility,
)
from .follow_controller_wake_target import (
    resolve_reviewer_wake_paths,
)
from .packet_predicates import packet_has_actor_route
from .reviewer_follow_guard import (
    ReviewerWakeDeps,
    ReviewerWakeLaunchContext,
    launch_waiting_reviewer_conductor,
)
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
    in_remote_control = (
        str(routing.operator_interaction_mode or "").strip() == "remote_control"
    )
    # rev_pkt_2904 fix: in remote_control, unscoped codex packets must
    # record attention only and NOT take the legacy reviewer-wake path
    # which can spawn or replace a codex conductor. The remote_control
    # guard inside `_wake_via_relaunch` (rev_pkt_2879 Finding W) is too
    # late because this branch returns before reaching that function.
    # Codex's live review of Phase 1.5: "agent_wake_dispatch.py
    # immediately sends provider=codex packets without target_role or
    # target_session_id back to maybe_wake_reviewer_fn before the
    # remote_control attention-only guard. That defeats the rev_pkt_2892
    # fix and can still spawn or replace a Codex conductor from packet
    # post."
    if (
        provider == "codex"
        and not packet_has_actor_route(packet)
        and in_remote_control
    ):
        return wake_report(
            packet=packet,
            attempted=True,
            woke=False,
            reason="remote_control_post_action_records_attention_only",
            target_agent=provider,
            extras=WakeReceiptExtras(
                target_role=str(packet.get("target_role") or "").strip(),
                wake_method="typed_attention_event",
                visible_session_woke=False,
                warnings=(
                    "Packet-post wake suppressed in remote_control: "
                    "operator cannot authorize a spawned conductor through "
                    "chat. Use `review-channel --action launch` for "
                    "explicit relaunch.",
                ),
            ),
        )
    if provider == "codex" and not packet_has_actor_route(packet):
        return maybe_wake_reviewer_fn(
            args=routing.args,
            repo_root=routing.repo_root,
            paths=routing.paths,
            report=routing.report,
            operator_interaction_mode=routing.operator_interaction_mode,
            deps=deps,
        )

    wake_paths = resolve_reviewer_wake_paths(routing.paths)
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
    return wake_report(
        packet=packet,
        attempted=True,
        woke=False,
        reason="target_session_poll_required",
        target_agent=provider,
        extras=WakeReceiptExtras(
            target_role=str(packet.get("target_role") or "").strip(),
            target_session_id=target_session_id,
            dashboard_session_id=(
                target_session_id if packet_targets_dashboard_poll(packet) else ""
            ),
            wake_method="session_poll",
            requested_session_visibility=requested_worker_visibility(packet),
            visible_session_woke=False,
            warnings=(
                "External push wake is unavailable for an existing provider "
                "session; the bound role/session must observe this packet on "
                "its next typed poll.",
            ),
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
    target_role = str(packet.get("target_role") or "").strip()
    visibility = requested_worker_visibility(
        packet,
        terminal_arg=getattr(routing.args, "terminal", ""),
    )
    # In remote_control mode the operator cannot see or auth a fresh
    # spawned conductor, so packet-post wake must record attention only and
    # leave conductor relaunch to explicit `review-channel --action launch`
    # or the scheduled publisher follow daemon. Without this gate, every
    # packet post tries-and-fails to spawn a TTY-bound codex session.
    if (
        str(getattr(routing, "operator_interaction_mode", "") or "").strip()
        == "remote_control"
    ):
        return wake_report(
            packet=packet,
            attempted=True,
            woke=False,
            reason="remote_control_post_action_records_attention_only",
            target_agent=provider,
            extras=WakeReceiptExtras(
                target_role=target_role,
                wake_method="typed_attention_event",
                requested_session_visibility=visibility,
                visible_session_woke=False,
                warnings=(
                    "Packet-post wake suppressed in remote_control: operator "
                    "cannot authorize a spawned conductor through chat. Use "
                    "`review-channel --action launch` for explicit relaunch.",
                ),
            ),
        )
    if not target_role:
        return wake_report(
            packet=packet,
            attempted=True,
            woke=False,
            reason="target_session_binding_required",
            target_agent=provider,
            extras=WakeReceiptExtras(
                wake_method="typed_attention_event",
                visible_session_woke=False,
                warnings=(
                    "Provider wake suppressed: packet lacks actor role/session "
                    "routing, so launching a fresh session would not prove the "
                    "intended actor consumed it.",
                ),
            ),
        )
    if visibility == "headless":
        return wake_report(
            packet=packet,
            attempted=True,
            woke=False,
            reason="headless_requires_typed_approval",
            target_agent=provider,
            extras=WakeReceiptExtras(
                target_role=target_role,
                wake_method="headless_suppressed",
                requested_session_visibility=visibility,
                visible_session_woke=False,
                warnings=(
                    "Headless worker launch is suppressed until typed "
                    "approval/proof marks this route as headless-approved.",
                ),
            ),
        )
    missing = _missing_launch_capabilities(
        report=routing.report,
        provider=provider,
        role=target_role,
        packet=packet,
    )
    if missing:
        return wake_report(
            packet=packet,
            attempted=True,
            woke=False,
            reason="launch_authority_missing",
            target_agent=provider,
            extras=WakeReceiptExtras(
                target_role=target_role,
                wake_method="visible_launch_suppressed",
                requested_session_visibility=visibility,
                visible_session_woke=False,
                warnings=(
                    "Visible worker launch is suppressed because typed "
                    "actor authority lacks required capability grants: "
                    + ", ".join(missing),
                ),
            ),
        )
    effective_deps = deps or ReviewerWakeDeps()
    return launch_waiting_reviewer_conductor(
        context=ReviewerWakeLaunchContext(
            args=_args_with_terminal(routing.args, terminal="terminal-app"),
            repo_root=routing.repo_root,
            paths=routing.paths,
            report=routing.report,
            packet=packet,
            wake_paths=wake_paths,
            cleanup_warnings=(),
            operator_interaction_mode=routing.operator_interaction_mode,
            provider=provider,
            wake_method_override="visible_session_launch",
            target_role=target_role,
        ),
        deps=effective_deps,
    )


def _args_with_terminal(args: object, *, terminal: str) -> object:
    from types import SimpleNamespace

    values = dict(vars(args)) if hasattr(args, "__dict__") else {}
    values["terminal"] = terminal
    return SimpleNamespace(**values)


def _missing_launch_capabilities(
    *,
    report: Mapping[str, object],
    provider: str,
    role: str,
    packet: Mapping[str, object],
) -> tuple[str, ...]:
    required = _required_launch_capabilities(packet)
    if not required:
        return ()
    grants = _granted_capabilities_for_route(
        report=report,
        provider=provider,
        role=role,
    )
    return tuple(capability for capability in required if capability not in grants)


def _required_launch_capabilities(packet: Mapping[str, object]) -> tuple[str, ...]:
    action = str(packet.get("requested_action") or "").strip()
    if action == "stage_commit_pipeline":
        return ("repo.stage", "repo.commit")
    if action in {"commit", "push"}:
        return ("repo.commit",)
    if action == "kill_process":
        return ("runtime.terminate",)
    if action == "run_check":
        return ("runtime.observe",)
    if str(packet.get("kind") or "").strip() in {"action_request", "instruction"}:
        return ("runtime.observe",)
    return ("runtime.observe",)


def _granted_capabilities_for_route(
    *,
    report: Mapping[str, object],
    provider: str,
    role: str,
) -> set[str]:
    rows = _actor_authority_rows(report)
    provider_key = _normalize(provider)
    role_key = _normalize(role)
    capabilities: set[str] = set()
    for row in rows:
        row_provider = _normalize(row.get("provider"))
        row_actor = _normalize(row.get("actor_id"))
        row_role = _normalize(row.get("role"))
        if provider_key and provider_key not in {row_provider, row_actor}:
            continue
        if role_key and row_role and role_key != row_role:
            continue
        for grant in _rows(row.get("grants")):
            if bool(grant.get("granted")):
                capability = str(grant.get("capability") or "").strip()
                if capability:
                    capabilities.add(capability)
    return capabilities


def _actor_authority_rows(report: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    authority = report.get("authority_snapshot")
    if isinstance(authority, Mapping):
        rows = _rows(authority.get("actor_authorities"))
        if rows:
            return rows
    collaboration = report.get("collaboration")
    if isinstance(collaboration, Mapping):
        return _rows(collaboration.get("actor_authorities"))
    return ()


def _rows(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(row for row in value if isinstance(row, Mapping))


def _normalize(value: object) -> str:
    return str(value or "").strip().lower()

