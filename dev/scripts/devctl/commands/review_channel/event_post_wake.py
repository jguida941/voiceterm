"""Wake helpers for event-backed review-channel packet posts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ...review_channel.follow_controller import (
    maybe_wake_waiting_agent_conductor,
    maybe_wake_waiting_reviewer_conductor,
)
from ...review_channel.events import load_or_refresh_event_bundle, refresh_event_bundle
from ...review_channel.event_store import append_event, load_events
from ...review_channel.state import refresh_status_snapshot
from ...runtime.governance_scan import scan_repo_governance_safely
from ...runtime.operator_context import derive_operator_interaction_mode
from ..review_channel_command.models import RuntimePaths
from .wake_receipt_persistence import record_packet_wake_receipt as _record_packet_wake_receipt


@dataclass(frozen=True)
class EventPostWakeDeps:
    """Injectable seams for event-backed post wake handling."""

    refresh_status_snapshot_fn: Callable[..., object] = refresh_status_snapshot
    scan_repo_governance_fn: Callable[[Path], object | None] = (
        scan_repo_governance_safely
    )
    derive_operator_interaction_mode_fn: Callable[..., str] = (
        derive_operator_interaction_mode
    )
    maybe_wake_waiting_reviewer_conductor_fn: Callable[..., dict[str, object] | None] = (
        maybe_wake_waiting_reviewer_conductor
    )
    maybe_wake_waiting_agent_conductor_fn: Callable[..., dict[str, object] | None] = (
        maybe_wake_waiting_agent_conductor
    )
    load_or_refresh_event_bundle_fn: Callable[..., object] = load_or_refresh_event_bundle
    append_event_fn: Callable[..., dict[str, object]] = append_event
    load_events_fn: Callable[[Path], list[dict[str, object]]] = load_events
    refresh_event_bundle_fn: Callable[..., object] = refresh_event_bundle


_DEFAULT_EVENT_POST_WAKE_DEPS = EventPostWakeDeps()
NON_CONDUCTOR_WAKE_TARGETS = {"", "operator", "system"}


def maybe_wake_posted_reviewer_packet(
    *,
    args,
    repo_root: Path,
    paths: Mapping[str, object],
    packet: Mapping[str, object],
    posted_review_state_payload: Mapping[str, object] | None = None,
    deps: EventPostWakeDeps | None = None,
) -> dict[str, object] | None:
    """Trigger the existing reviewer wake path immediately after packet post.

    Event-backed packet posting already updates the typed queue, but without an
    explicit wake edge the reviewer only notices on the next ensure-follow tick.
    Reuse the same wake primitive the follow loop uses so packet arrival can
    restore the waiting reviewer turn immediately.
    """

    target_agent = str(packet.get("to_agent") or "").strip()
    skip_reason = _wake_skip_reason(packet)
    if skip_reason:
        return _wake_skipped(packet=packet, reason=skip_reason)
    resolved_deps = deps or _DEFAULT_EVENT_POST_WAKE_DEPS

    bridge_path = _as_path(paths.get("bridge_path"))
    review_channel_path = _as_path(paths.get("review_channel_path"))
    status_dir = _as_path(paths.get("status_dir"))
    missing = _missing_runtime_path_keys(
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        status_dir=status_dir,
    )
    if missing:
        return _wake_error(
            packet=packet,
            reason="missing_runtime_paths",
            detail=f"Missing runtime paths for reviewer wake: {', '.join(missing)}",
        )

    try:
        status_snapshot = resolved_deps.refresh_status_snapshot_fn(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=status_dir,
            promotion_plan_path=_as_path(paths.get("promotion_plan_path")),
            execution_mode=str(
                getattr(args, "execution_mode", "markdown-bridge")
                or "markdown-bridge"
            ),
        )
    except (OSError, ValueError) as exc:
        return _wake_error(packet=packet, reason="status_refresh_failed", detail=str(exc))

    review_state_payload = _merge_review_state_payloads(
        _provided_review_state_payload(posted_review_state_payload),
        _event_review_state_payload(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=paths.get("artifact_paths"),
            deps=resolved_deps,
        ),
        _review_state_payload(status_snapshot),
    )
    operator_interaction_mode = resolved_deps.derive_operator_interaction_mode_fn(
        governance=resolved_deps.scan_repo_governance_fn(repo_root),
        review_state_payload=review_state_payload,
        receipt=None,
        reviewer_mode=str(status_snapshot.bridge_liveness.get("reviewer_mode") or ""),
    )
    report = {
        "bridge_liveness": dict(status_snapshot.bridge_liveness),
        "packet_inbox": dict(review_state_payload.get("packet_inbox") or {}),
        "packets": list(review_state_payload.get("packets") or []),
        "coordination": review_state_payload.get("coordination"),
        "coordination_state": review_state_payload.get("coordination_state"),
        "agent_sync": review_state_payload.get("agent_sync"),
        "agent_work_board": review_state_payload.get("agent_work_board"),
        "agent_loop_decisions": review_state_payload.get("agent_loop_decisions"),
        "reviewer_runtime": review_state_payload.get("reviewer_runtime"),
        "authority_snapshot": review_state_payload.get("authority_snapshot"),
    }
    wake_paths = _wake_paths_mapping(
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        status_dir=status_dir,
        promotion_plan_path=_as_path(paths.get("promotion_plan_path")),
        artifact_paths=paths.get("artifact_paths"),
    )
    if target_agent == "codex":
        wake = resolved_deps.maybe_wake_waiting_reviewer_conductor_fn(
            args=args,
            repo_root=repo_root,
            paths=wake_paths,
            report=report,
            operator_interaction_mode=operator_interaction_mode,
        )
    else:
        wake = resolved_deps.maybe_wake_waiting_agent_conductor_fn(
            args=args,
            repo_root=repo_root,
            paths=wake_paths,
            report=report,
            operator_interaction_mode=operator_interaction_mode,
            target_agent=target_agent,
            packet=dict(packet),
        )
    if isinstance(wake, dict):
        _record_packet_wake_receipt(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=paths.get("artifact_paths"),
            packet=packet,
            wake=wake,
            deps=resolved_deps,
        )
    return wake


def _review_state_payload(status_snapshot: object) -> dict[str, object]:
    review_state = getattr(status_snapshot, "review_state", None)
    if review_state is None:
        return {}
    to_dict = getattr(review_state, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        return payload if isinstance(payload, dict) else {}
    return {}


def _event_review_state_payload(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: object,
    deps: EventPostWakeDeps,
) -> dict[str, object]:
    if artifact_paths is None:
        return {}
    try:
        bundle = deps.load_or_refresh_event_bundle_fn(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
    except (OSError, ValueError):
        return {}
    review_state = getattr(bundle, "review_state", None)
    return review_state if isinstance(review_state, dict) else {}


def _provided_review_state_payload(
    value: Mapping[str, object] | None,
) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _merge_review_state_payloads(
    *payloads: dict[str, object],
) -> dict[str, object]:
    merged: dict[str, object] = {}
    for field_name in (
        "packet_inbox",
        "packets",
        "coordination",
        "coordination_state",
        "agent_sync",
        "agent_work_board",
        "agent_loop_decisions",
        "reviewer_runtime",
        "authority_snapshot",
    ):
        for payload in payloads:
            value = payload.get(field_name)
            if value in (None, {}, [], ()):
                continue
            merged[field_name] = value
            break
    return merged


def _wake_error(
    *,
    packet: Mapping[str, object],
    reason: str,
    detail: str,
    target_agent: str = "",
) -> dict[str, object]:
    report = {
        "attempted": True,
        "woke": False,
        "reason": reason,
        "packet_id": str(packet.get("packet_id") or "").strip(),
        "requested_action": str(packet.get("requested_action") or "").strip(),
    }
    if target_agent:
        report["target_agent"] = target_agent
    if detail:
        report["warnings"] = [detail]
    return report


def _wake_skipped(
    *,
    packet: Mapping[str, object],
    reason: str,
) -> dict[str, object]:
    return {
        "attempted": False,
        "woke": False,
        "reason": reason,
        "packet_id": str(packet.get("packet_id") or "").strip(),
        "requested_action": str(packet.get("requested_action") or "").strip(),
    }


def _wake_skip_reason(packet: Mapping[str, object]) -> str:
    target_agent = str(packet.get("to_agent") or "").strip().lower()
    if target_agent in NON_CONDUCTOR_WAKE_TARGETS:
        return "non_conductor_target"
    status = str(packet.get("status") or "").strip().lower()
    if status and status != "pending":
        return "non_pending_packet"
    return ""


def _as_path(value: object) -> Path | None:
    return value if isinstance(value, Path) else None


def _missing_runtime_path_keys(
    *,
    bridge_path: Path | None,
    review_channel_path: Path | None,
    status_dir: Path | None,
) -> tuple[str, ...]:
    missing: list[str] = []
    if bridge_path is None:
        missing.append("bridge_path")
    if review_channel_path is None:
        missing.append("review_channel_path")
    if status_dir is None:
        missing.append("status_dir")
    return tuple(missing)


def _wake_paths_mapping(
    *,
    bridge_path: Path,
    review_channel_path: Path,
    status_dir: Path,
    promotion_plan_path: Path | None,
    artifact_paths: object,
) -> dict[str, object]:
    return {
        "bridge_path": bridge_path,
        "review_channel_path": review_channel_path,
        "status_dir": status_dir,
        "promotion_plan_path": promotion_plan_path,
        "artifact_paths": artifact_paths,
    }
