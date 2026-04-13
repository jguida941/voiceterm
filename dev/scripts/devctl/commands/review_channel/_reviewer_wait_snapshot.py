"""Snapshot-building helpers for the reviewer-side wait loop."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
from pathlib import Path

from ...runtime.review_state_models import packet_inbox_from_mapping
from ..review_channel_command import RuntimePaths
from ._wait_shared import WaitDeps


@dataclass(frozen=True, slots=True)
class ReviewerWaitSnapshot:
    """One status snapshot observed by the reviewer wait loop."""

    report: dict[str, object]
    exit_code: int
    worktree_hash: str
    reviewed_hash: str
    implementer_ack_revision: str
    implementer_ack_state: str
    implementer_status_excerpt: str
    attention_status: str
    attention_summary: str
    attention_recommended_action: str
    reviewer_mode: str
    latest_pending_packet_id: str = ""
    latest_finding_packet_id: str = ""
    packet_inbox_available: bool = False
    packet_attention_revision: str = ""
    implementer_state_hash: str = ""
    reviewer_accepted_implementer_state_hash: str = ""


def capture_reviewer_snapshot(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths,
    deps: WaitDeps,
) -> ReviewerWaitSnapshot:
    """Capture the typed state the reviewer loop uses to detect new work."""
    report, exit_code = deps.run_status_action_fn(
        args=args,
        repo_root=repo_root,
        paths=paths,
    )
    reviewer_worker = _mapping(report.get("reviewer_worker"))
    bridge_liveness = _mapping(report.get("bridge_liveness"))
    current_session = _load_current_session(report)
    attention = _mapping(report.get("attention"))
    reviewer_runtime = _mapping(report.get("reviewer_runtime"))
    review_acceptance = _mapping(reviewer_runtime.get("review_acceptance"))
    packet_inbox = _load_packet_inbox(report)
    agent_attention = (
        packet_inbox.for_agent("codex")
        if packet_inbox is not None
        else None
    )

    return ReviewerWaitSnapshot(
        report=dict(report),
        exit_code=exit_code,
        worktree_hash=str(reviewer_worker.get("current_hash") or ""),
        reviewed_hash=str(reviewer_worker.get("reviewed_hash") or ""),
        implementer_ack_revision=str(
            current_session.get("implementer_ack_revision")
            or bridge_liveness.get("claude_ack_revision")
            or ""
        ),
        implementer_ack_state=str(
            current_session.get("implementer_ack_state")
            or _bridge_ack_state(bridge_liveness)
        ),
        implementer_status_excerpt=str(
            current_session.get("implementer_status") or ""
        )[:200],
        attention_status=str(attention.get("status") or ""),
        attention_summary=str(attention.get("summary") or ""),
        attention_recommended_action=str(
            attention.get("recommended_action") or ""
        ),
        reviewer_mode=str(
            bridge_liveness.get("effective_reviewer_mode")
            or bridge_liveness.get("reviewer_mode")
            or reviewer_worker.get("reviewer_mode")
            or ""
        ),
        latest_pending_packet_id=_current_actionable_packet_id(agent_attention),
        latest_finding_packet_id=str(
            getattr(agent_attention, "latest_finding_packet_id", "") or ""
        ),
        packet_inbox_available=agent_attention is not None,
        packet_attention_revision=str(
            getattr(packet_inbox, "attention_revision", "") or ""
        ),
        implementer_state_hash=str(
            current_session.get("implementer_state_hash") or ""
        ),
        reviewer_accepted_implementer_state_hash=str(
            review_acceptance.get("reviewer_accepted_implementer_state_hash") or ""
        ),
    )


def _load_current_session(report: Mapping[str, object]) -> Mapping[str, object]:
    """Load typed current-session state from the generated status projections."""
    inline_session = _mapping(report.get("current_session"))
    if inline_session:
        return inline_session
    projection_paths = _mapping(report.get("projection_paths"))
    for key in ("review_state_path", "compact_path"):
        raw_path = projection_paths.get(key)
        if not raw_path:
            continue
        try:
            payload = json.loads(Path(str(raw_path)).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        current_session = payload.get("current_session")
        if isinstance(current_session, Mapping):
            return current_session
    return {}


def _load_packet_inbox(report: Mapping[str, object]):
    """Load typed packet-inbox state from the status report or projections."""
    inline_inbox = packet_inbox_from_mapping(report.get("packet_inbox"))
    if inline_inbox is not None:
        return inline_inbox
    projection_paths = _mapping(report.get("projection_paths"))
    for key in ("review_state_path", "compact_path"):
        raw_path = projection_paths.get(key)
        if not raw_path:
            continue
        try:
            payload = json.loads(Path(str(raw_path)).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        inbox = packet_inbox_from_mapping(payload.get("packet_inbox"))
        if inbox is not None:
            return inbox
    return None


def _current_actionable_packet_id(agent_attention) -> str:
    """Return the typed actionable packet id for the reviewer lane."""
    if agent_attention is None:
        return ""
    current_instruction = str(
        getattr(agent_attention, "current_instruction_packet_id", "") or ""
    ).strip()
    if current_instruction:
        return current_instruction
    pending_ids = getattr(agent_attention, "pending_actionable_packet_ids", ()) or ()
    for packet_id in pending_ids:
        text = str(packet_id or "").strip()
        if text:
            return text
    return ""


def _bridge_ack_state(bridge_liveness: Mapping[str, object]) -> str:
    """Derive a coarse ACK state from bridge-liveness when projections are unavailable."""
    if bool(bridge_liveness.get("claude_ack_current")):
        return "current"
    if bridge_liveness.get("claude_ack_present"):
        return "stale"
    return "missing"


def _mapping(value: object) -> Mapping[str, object]:
    """Return a mapping view or an empty mapping."""
    return value if isinstance(value, Mapping) else {}
