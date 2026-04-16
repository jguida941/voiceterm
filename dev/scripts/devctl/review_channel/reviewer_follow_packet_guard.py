"""Packet-trigger helpers for detached reviewer follow loops."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .events import (
    load_or_refresh_event_bundle,
    post_packet,
    resolve_artifact_paths,
)
from .packet_contract import PacketPostRequest
from .turn_authority import ReviewerTurnAuthority
from .reviewer_follow_trigger_gate import (
    typed_report_trigger_available as _typed_report_trigger_available,
    typed_report_trigger_met as _typed_report_trigger_met,
    authority_trigger_met as _authority_trigger_met,
    legacy_trigger_met as _legacy_trigger_met,
)

_REVIEW_TRIGGER_KEY_PREFIX = "- review_trigger_key: `"
_REVIEW_TRIGGER_KIND = "action_request"
_REVIEW_TRIGGER_REQUESTED_ACTION = "restore_reviewer_turn"


@dataclass(slots=True)
class ReviewerFollowTriggerState:
    """In-memory dedupe state for bounded reviewer follow-up packet writes."""

    last_trigger_key: str = ""


@dataclass(frozen=True, slots=True)
class ReviewerFollowPacketRequest:
    """Immutable inputs for one reviewer follow-up packet decision."""

    args: object
    repo_root: Path
    paths: dict[str, object]
    report: dict[str, object]
    turn_authority: ReviewerTurnAuthority | None = None


@dataclass(frozen=True, slots=True)
class ReviewerFollowPacketDeps:
    """Injectable seams for reviewer follow-up packet writes."""

    load_bundle_fn: Callable[..., object] = load_or_refresh_event_bundle
    post_packet_fn: Callable[..., object] = post_packet


@dataclass(frozen=True, slots=True)
class ReviewerFollowPacketContext:
    """Resolved state for one pending reviewer follow-up trigger."""

    bridge_liveness: dict[str, object]
    attention: dict[str, object]
    reviewer_worker: dict[str, object]
    review_channel_path: Path | None
    attention_status: str
    trigger_key: str


def maybe_queue_reviewer_follow_packet(
    *,
    request: ReviewerFollowPacketRequest,
    trigger_state: ReviewerFollowTriggerState,
    deps: ReviewerFollowPacketDeps = ReviewerFollowPacketDeps(),
) -> dict[str, object] | None:
    """Queue one Claude-targeted follow-up packet when the reviewer loop is detached."""
    context = _resolve_packet_context(request)
    if context is None:
        trigger_state.last_trigger_key = ""
        return None
    if context.review_channel_path is None:
        return _trigger_response(
            attempted=True,
            queued=False,
            reason="review_channel_path_missing",
            trigger_key=context.trigger_key,
        )

    artifact_paths = resolve_artifact_paths(repo_root=request.repo_root)
    existing_packet_id = _existing_pending_trigger_packet_id(
        repo_root=request.repo_root,
        review_channel_path=context.review_channel_path,
        artifact_paths=artifact_paths,
        trigger_key=context.trigger_key,
        load_bundle_fn=deps.load_bundle_fn,
    )
    if existing_packet_id:
        trigger_state.last_trigger_key = context.trigger_key
        return _trigger_response(
            attempted=True,
            queued=False,
            reason="already_pending",
            trigger_key=context.trigger_key,
            packet_id=existing_packet_id,
        )

    bundle, event = deps.post_packet_fn(
        repo_root=request.repo_root,
        review_channel_path=context.review_channel_path,
        artifact_paths=artifact_paths,
        request=_build_review_trigger_request(request=request, context=context),
    )
    del bundle
    trigger_state.last_trigger_key = context.trigger_key
    return _trigger_response(
        attempted=True,
        queued=True,
        trigger_key=context.trigger_key,
        packet_id=str(event.get("packet_id") or ""),
        attention_status=context.attention_status,
    )


def _resolve_packet_context(
    request: ReviewerFollowPacketRequest,
) -> ReviewerFollowPacketContext | None:
    authority = request.turn_authority
    bridge_liveness = request.report.get("bridge_liveness")
    attention = request.report.get("attention")
    reviewer_worker = request.report.get("reviewer_worker")
    if not isinstance(bridge_liveness, dict) or not isinstance(attention, dict):
        return None
    if not isinstance(reviewer_worker, dict):
        return None

    if authority is not None:
        if not _authority_trigger_met(authority):
            return None
        attention_status = authority.attention_status
    elif _typed_report_trigger_available(request.report):
        if not _typed_report_trigger_met(request.report):
            return None
        authority_snap = request.report["authority_snapshot"]
        assert isinstance(authority_snap, dict)
        attention_status = str(authority_snap.get("attention_status") or "").strip()
    else:
        if not bool(request.report.get("review_needed")):
            return None
        if not _legacy_trigger_met(bridge_liveness, attention):
            return None
        attention_status = str(attention.get("status") or "").strip()

    review_channel_path = request.paths.get("review_channel_path")
    trigger_key = _build_trigger_key(
        attention_status=attention_status,
        reviewer_worker=reviewer_worker,
        bridge_liveness=bridge_liveness,
        turn_authority=authority,
    )
    if not trigger_key:
        return None
    return ReviewerFollowPacketContext(
        bridge_liveness=bridge_liveness,
        attention=attention,
        reviewer_worker=reviewer_worker,
        review_channel_path=(
            review_channel_path if isinstance(review_channel_path, Path) else None
        ),
        attention_status=attention_status,
        trigger_key=trigger_key,
    )




def _build_trigger_key(
    *,
    attention_status: str,
    reviewer_worker: dict[str, object],
    bridge_liveness: dict[str, object],
    turn_authority: ReviewerTurnAuthority | None = None,
) -> str:
    current_hash = str(reviewer_worker.get("current_hash") or "").strip()
    reviewed_hash = str(reviewer_worker.get("reviewed_hash") or "").strip()
    if turn_authority is not None:
        instruction_revision = turn_authority.current_instruction_revision
        launch_truth = turn_authority.launch_truth
    else:
        instruction_revision = str(
            bridge_liveness.get("current_instruction_revision") or ""
        ).strip()
        launch_truth = str(bridge_liveness.get("launch_truth") or "").strip()
    return "\0".join(
        (
            attention_status,
            launch_truth,
            current_hash,
            reviewed_hash,
            instruction_revision,
        )
    ).strip("\0")


def _build_review_trigger_request(
    *,
    request: ReviewerFollowPacketRequest,
    context: ReviewerFollowPacketContext,
) -> PacketPostRequest:
    return PacketPostRequest(
        from_agent="system",
        to_agent="claude",
        kind=_REVIEW_TRIGGER_KIND,
        summary="Restore reviewer turn: worktree changed since last accepted review.",
        body=_review_trigger_body(context),
        evidence_refs=(
            "bridge.md",
            str(context.review_channel_path.relative_to(request.repo_root)),
        ),
        confidence=1.0,
        requested_action=_REVIEW_TRIGGER_REQUESTED_ACTION,
        policy_hint="review_only",
        approval_required=False,
        session_id=str(getattr(request.args, "session_id", "") or "local-review"),
        plan_id=str(getattr(request.args, "plan_id", "") or "MP-355"),
        controller_run_id=_controller_run_id_from_report(request.report),
        expires_in_minutes=max(
            1, int(getattr(request.args, "expires_in_minutes", 30) or 30)
        ),
    )


def _controller_run_id_from_report(report: dict[str, object]) -> str | None:
    service_identity = report.get("service_identity")
    if not isinstance(service_identity, dict):
        return None
    controller_run_id = str(service_identity.get("service_id") or "").strip()
    return controller_run_id or None


def _trigger_response(
    *,
    attempted: bool,
    queued: bool,
    reason: str | None = None,
    trigger_key: str = "",
    packet_id: str = "",
    attention_status: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {}
    payload["attempted"] = attempted
    payload["queued"] = queued
    if reason:
        payload["reason"] = reason
    if trigger_key:
        payload["trigger_key"] = trigger_key
    if packet_id:
        payload["packet_id"] = packet_id
    payload["to_agent"] = "claude"
    if attention_status:
        payload["attention_status"] = attention_status
    return payload


def _existing_pending_trigger_packet_id(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths,
    trigger_key: str,
    load_bundle_fn,
) -> str:
    try:
        bundle = load_bundle_fn(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
    except ValueError:
        return ""
    packets = bundle.review_state.get("packets")
    if not isinstance(packets, list):
        return ""
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        if packet.get("status") != "pending":
            continue
        if packet.get("to_agent") != "claude":
            continue
        if packet.get("requested_action") != _REVIEW_TRIGGER_REQUESTED_ACTION:
            continue
        body = str(packet.get("body") or "")
        if f"{_REVIEW_TRIGGER_KEY_PREFIX}{trigger_key}`" not in body:
            continue
        return str(packet.get("packet_id") or "")
    return ""


def _review_trigger_body(context: ReviewerFollowPacketContext) -> str:
    lines = [
        "Automation-only reviewer follow detected pending review without a live reviewer turn.",
        "",
        f"{_REVIEW_TRIGGER_KEY_PREFIX}{context.trigger_key}`",
        f"- attention_status: `{context.attention.get('status') or 'unknown'}`",
        f"- launch_truth: `{context.bridge_liveness.get('launch_truth') or 'unknown'}`",
        f"- poll_status_reason: `{context.bridge_liveness.get('poll_status_reason') or 'unknown'}`",
        f"- current_hash: `{context.reviewer_worker.get('current_hash') or ''}`",
        f"- reviewed_hash: `{context.reviewer_worker.get('reviewed_hash') or ''}`",
        f"- current_instruction_revision: `{context.bridge_liveness.get('current_instruction_revision') or ''}`",
    ]
    recommended_command = str(
        context.attention.get("recommended_command") or ""
    ).strip()
    if recommended_command:
        lines.append(f"- recommended_command: `{recommended_command}`")
    lines.extend(
        [
            "",
            "Use the existing review-channel recovery path to restore a real Codex reviewer pass.",
            "Do not treat automation heartbeats as reviewer progress on this tree.",
        ]
    )
    return "\n".join(lines)
