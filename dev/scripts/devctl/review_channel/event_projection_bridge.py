"""Bridge-state derivation helpers for event-backed review-state projections."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256

from .current_session_projection import (
    current_session_mapping,
    event_agent_status,
    event_claude_ack,
    event_current_instruction,
    event_open_findings,
)
from .event_projection_bridge_state import build_event_bridge_state_projection
from .launch_truth import classify_launch_truth, effective_reviewer_mode
from .peer_liveness import (
    IMPLEMENTER_STALL_MARKERS,
    REVIEWER_WAIT_STATE_MARKERS,
    normalize_reviewer_mode,
)


def build_event_bridge_liveness_projection(
    review_state: Mapping[str, object],
    *,
    bridge_snapshot: object | None = None,
) -> dict[str, object]:
    """Build a fail-closed compatibility projection for event-backed liveness."""
    compat = _mapping(review_state.get("_compat"))
    runtime = _mapping(compat.get("runtime"))
    daemons = _mapping(runtime.get("daemons"))
    publisher = _mapping(daemons.get("publisher"))
    reviewer_supervisor = _mapping(daemons.get("reviewer_supervisor"))
    queue = _mapping(review_state.get("queue"))
    current_session = current_session_mapping(review_state)
    claude_status = event_agent_status(review_state, "claude")
    claude_ack = event_claude_ack(queue)
    open_findings = event_open_findings(review_state)
    reviewer_mode = _event_reviewer_mode(
        runtime,
        bridge_snapshot=bridge_snapshot,
        reviewer_runtime=_mapping(review_state.get("reviewer_runtime")),
    )
    bridge_liveness: dict[str, object] = {}
    bridge_liveness["overall_state"] = (
        "stale" if review_state.get("errors") else "fresh"
    )
    bridge_liveness["codex_poll_state"] = (
        "fresh" if review_state.get("timestamp") else "missing"
    )
    bridge_liveness["reviewer_freshness"] = (
        "fresh" if review_state.get("timestamp") else "missing"
    )
    bridge_liveness["reviewer_mode"] = reviewer_mode
    bridge_liveness["last_codex_poll_utc"] = str(review_state.get("timestamp") or "")
    bridge_liveness["last_codex_poll_age_seconds"] = 0
    bridge_liveness["claude_status_present"] = bool(claude_status)
    bridge_liveness["claude_ack_present"] = bool(claude_ack)
    bridge_liveness["open_findings_present"] = bool(
        open_findings and open_findings != "none"
    )
    bridge_liveness["reviewed_hash_current"] = None
    bridge_liveness["implementer_completion_stall"] = detect_event_implementer_stall(
        claude_status=claude_status,
        claude_ack=claude_ack,
        instruction=event_current_instruction(review_state),
        poll_status=str(queue.get("derived_next_instruction") or ""),
        reviewer_mode=reviewer_mode,
    )
    bridge_liveness["publisher_running"] = bool(publisher.get("running"))
    bridge_liveness["reviewer_supervisor_running"] = bool(
        reviewer_supervisor.get("running")
    )
    bridge_liveness["publisher_stop_reason"] = str(publisher.get("stop_reason") or "")
    instruction_text = event_current_instruction(review_state)
    # Per rev_pkt_2546/2552 (Plan 4.1 Scope 1): the typed reviewer_checkpoint
    # event carries the reviewer-owned revision directly. Prefer that revision
    # over an SHA-of-text synthesis so ``bridge_validation.py`` reads the same
    # revision Codex wrote at checkpoint time. The bridge_snapshot is now a
    # second-tier fallback for legacy projections; the SHA-of-text path is
    # the last fallback for sessions that have neither typed event nor live
    # bridge snapshot. Compatibility projection only -- ACK/worktree truth
    # still stays fail-closed below.
    instruction_rev = ""
    typed_checkpoint = review_state.get("latest_reviewer_checkpoint") or {}
    if isinstance(typed_checkpoint, Mapping):
        instruction_rev = str(
            typed_checkpoint.get("current_instruction_revision") or ""
        ).strip()
    if not instruction_rev and bridge_snapshot is not None:
        snapshot_rev = str(
            getattr(bridge_snapshot, "metadata", {}).get(
                "current_instruction_revision"
            )
            or ""
        ).strip()
        if snapshot_rev:
            instruction_rev = snapshot_rev
    if not instruction_rev and instruction_text.strip():
        instruction_rev = sha256(
            instruction_text.strip().encode("utf-8")
        ).hexdigest()[:12]
    bridge_liveness["current_instruction_revision"] = instruction_rev
    bridge_liveness["claude_ack_revision"] = ""
    bridge_liveness["claude_ack_current"] = False
    bridge_liveness["reviewer_poll_state"] = bridge_liveness["codex_poll_state"]
    bridge_liveness["last_reviewer_poll_utc"] = bridge_liveness["last_codex_poll_utc"]
    bridge_liveness["last_reviewer_poll_age_seconds"] = bridge_liveness[
        "last_codex_poll_age_seconds"
    ]
    bridge_liveness["implementer_status"] = str(
        current_session.get("implementer_status") or claude_status or ""
    )
    bridge_liveness["implementer_ack"] = str(
        current_session.get("implementer_ack") or claude_ack or ""
    )
    bridge_liveness["implementer_ack_revision"] = str(
        current_session.get("implementer_ack_revision") or ""
    )
    bridge_liveness["implementer_ack_current"] = (
        str(current_session.get("implementer_ack_state") or "").strip() == "current"
    )
    bridge_liveness["launch_truth"] = classify_launch_truth(bridge_liveness).value
    bridge_liveness["effective_reviewer_mode"] = effective_reviewer_mode(
        bridge_liveness
    )
    bridge_liveness["session_liveness_signals"] = ()
    # NOTE per Codex rev_pkt_2326/2337: bridge-poll consumers must NOT rely
    # on bridge_liveness for canonical active-packet authority. The typed
    # ReviewBridgeState schema does not round-trip new fields (per
    # rev_pkt_2271 #3). Consumers should read
    # ``review_state["coordination_state"]`` and
    # ``review_state["agent_work_board"]`` directly, OR call
    # ``review_channel.active_packet_authority.current_active_packet_for_agent``.
    # Bridge prose remains compatibility projection per CLAUDE.md Platform
    # Boundary doctrine; it is not authority for active-packet truth.
    return bridge_liveness


def _event_reviewer_mode(
    runtime: Mapping[str, object],
    *,
    bridge_snapshot: object | None = None,
    reviewer_runtime: Mapping[str, object] | None = None,
) -> str:
    runtime_mode = _runtime_reviewer_mode(reviewer_runtime)
    if runtime_mode:
        return runtime_mode
    bridge_mode = _bridge_snapshot_reviewer_mode(bridge_snapshot)
    if bridge_mode:
        return bridge_mode

    daemons = _mapping(runtime.get("daemons"))
    for daemon_name in ("publisher", "reviewer_supervisor"):
        daemon_state = _mapping(daemons.get(daemon_name))
        if not bool(daemon_state.get("running")):
            continue
        reviewer_mode = str(daemon_state.get("reviewer_mode") or "").strip()
        if reviewer_mode:
            return normalize_reviewer_mode(reviewer_mode).value
    return "tools_only"


def _runtime_reviewer_mode(reviewer_runtime: Mapping[str, object] | None) -> str:
    runtime = reviewer_runtime if isinstance(reviewer_runtime, Mapping) else {}
    if _runtime_reviewer_mode_is_placeholder(runtime):
        return ""
    posture = _mapping(runtime.get("session_posture"))
    mode = str(
        posture.get("reviewer_mode")
        or posture.get("effective_reviewer_mode")
        or runtime.get("reviewer_mode")
        or runtime.get("effective_reviewer_mode")
        or ""
    ).strip()
    return normalize_reviewer_mode(mode).value if mode else ""


def _runtime_reviewer_mode_is_placeholder(runtime: Mapping[str, object]) -> bool:
    mode = str(
        runtime.get("reviewer_mode") or runtime.get("effective_reviewer_mode") or ""
    ).strip()
    if mode and normalize_reviewer_mode(mode).value != "single_agent":
        return False
    posture = _mapping(runtime.get("session_posture"))
    actors = posture.get("actors")
    if isinstance(actors, (list, tuple)) and actors:
        return False
    remote_control_attachment = runtime.get("remote_control_attachment")
    if isinstance(remote_control_attachment, Mapping) and remote_control_attachment:
        return False
    for key in ("last_poll", "agent_runtime_clock", "packet_attention"):
        if _meaningful_runtime_mapping(_mapping(runtime.get(key))):
            return False
    return True


def _meaningful_runtime_mapping(value: Mapping[str, object]) -> bool:
    return any(
        str(item or "").strip()
        for key, item in value.items()
        if key not in {"schema_version", "contract_id"}
    )


def _bridge_snapshot_reviewer_mode(bridge_snapshot: object | None) -> str:
    metadata = getattr(bridge_snapshot, "metadata", None)
    if not isinstance(metadata, Mapping):
        return ""
    reviewer_mode = str(metadata.get("reviewer_mode") or "").strip()
    if not reviewer_mode:
        return ""
    return normalize_reviewer_mode(reviewer_mode).value


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def detect_event_implementer_stall(
    *,
    claude_status: str,
    claude_ack: str,
    instruction: str,
    poll_status: str,
    reviewer_mode: str,
) -> bool:
    """Detect implementer completion stall from event-backed state."""
    from .peer_liveness import reviewer_mode_is_active

    combined = f"{claude_status}\n{claude_ack}".lower()
    if not any(marker in combined for marker in IMPLEMENTER_STALL_MARKERS):
        return False
    instruction_lower = instruction.lower()
    if any(marker in instruction_lower for marker in REVIEWER_WAIT_STATE_MARKERS):
        return False
    if not reviewer_mode_is_active(reviewer_mode):
        return True
    return True
