"""Typed ReviewState extraction helpers for the dashboard (Slice D: MP-384).

Each function maps a typed ReviewState dict into the flat shape expected
by downstream dashboard builders, so the data pipeline works identically
regardless of whether the source is compact.json or review_state.json.
"""

from __future__ import annotations

from collections.abc import Sequence
import re
from typing import Any, TypedDict

from ..review_channel.pending_packets import live_pending_packets
from ..review_channel.runtime_counts import build_runtime_counts


class SessionFields(TypedDict):
    """Flat session shape matching compact.json's current_session layout."""

    current_instruction: str
    current_instruction_revision: str
    implementer_status: str
    implementer_ack_state: str
    open_findings: str
    last_reviewed_scope: str
    implementer_state_hash: str


class PendingPacketFields(TypedDict):
    """Typed shape for a single pending review packet."""

    packet_id: str
    kind: str
    from_agent: str
    to_agent: str
    summary: str
    status: str
    requested_action: str
    policy_hint: str
    target_ref: str
    target_revision: str
    target_role: str
    target_session_id: str
    approval_required: bool
    posted_at: str
    delivery_emitted_at_utc: str
    delivery_observed_at_utc: str
    delivery_observed_by: str
    execution_started_at_utc: str
    execution_started_by: str
    lifecycle_current_state: str
    semantic_zref: str


class BridgeFields(TypedDict):
    """Flat bridge shape matching _parse_bridge() output."""

    last_poll: str
    last_poll_utc: str
    reviewer_mode: str
    instruction: str
    verdict: str
    findings_raw: str
    reviewed_scope_raw: str
    instruction_full: str


def _extract_typed_session(review_state: dict[str, Any]) -> SessionFields:
    """Extract current_session fields from a typed ReviewState dict.

    Maps ReviewState.current_session (ReviewCurrentSessionState) into the
    same flat dict shape that compact.json's current_session provides, so
    downstream builders work unchanged.
    """
    cs = review_state.get("current_session", {})
    return SessionFields(
        current_instruction=cs.get("current_instruction", ""),
        current_instruction_revision=cs.get("current_instruction_revision", ""),
        implementer_status=cs.get("implementer_status", ""),
        implementer_ack_state=cs.get("implementer_ack_state", ""),
        open_findings=cs.get("open_findings", ""),
        last_reviewed_scope=cs.get("last_reviewed_scope", ""),
        implementer_state_hash=cs.get("implementer_state_hash", ""),
    )


def _extract_typed_doctor(review_state: dict[str, Any]) -> dict[str, Any]:
    """Extract doctor/runtime health fields from a typed ReviewState dict.

    ReviewState carries reviewer_runtime.doctor or a top-level doctor key
    depending on the projection version. This function normalizes both shapes.
    """
    rt = review_state.get("reviewer_runtime", {})
    doctor = rt.get("doctor", {}) if isinstance(rt, dict) else {}
    if not doctor:
        doctor = review_state.get("doctor", {})
    if not doctor:
        compat = review_state.get("_compat", {})
        doctor = compat.get("doctor", {}) if isinstance(compat, dict) else {}
    return doctor if isinstance(doctor, dict) else {}


def _extract_typed_attention(
    review_state: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Extract attention state from a typed ReviewState dict.

    Returns a flat dict with status, owner, summary, recommended_action, and
    recommended_command. Returns None when ReviewState is absent.
    """
    if review_state is None:
        return None
    attn = review_state.get("attention")
    if not isinstance(attn, dict):
        return None
    return {
        "status": attn.get("status", "n/a"),
        "owner": attn.get("owner", "n/a"),
        "summary": attn.get("summary", "n/a"),
        "recommended_action": attn.get("recommended_action", ""),
        "recommended_command": attn.get("recommended_command", ""),
    }


def _extract_typed_instruction_provenance(
    review_state: dict[str, Any] | None,
) -> dict[str, Any]:
    """Extract current-instruction provenance from the same ReviewState tick."""
    if review_state is None:
        return {}
    queue = review_state.get("queue")
    if not isinstance(queue, dict):
        return {}
    source = queue.get("derived_next_instruction_source")
    if not isinstance(source, dict):
        return {}
    provenance = source.get("provenance")
    return dict(provenance) if isinstance(provenance, dict) else {}


def _extract_typed_priority_decision(
    review_state: dict[str, Any] | None,
) -> dict[str, Any]:
    """Extract packet priority decision from the same ReviewState tick."""
    if review_state is None:
        return {}
    queue = review_state.get("queue")
    if not isinstance(queue, dict):
        return {}
    decision = queue.get("instruction_priority_decision")
    if isinstance(decision, dict) and decision:
        return dict(decision)
    source = queue.get("derived_next_instruction_source")
    if not isinstance(source, dict):
        return {}
    source_decision = source.get("priority_decision")
    return dict(source_decision) if isinstance(source_decision, dict) else {}


def _extract_typed_coordination(
    review_state: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Extract the shared coordination snapshot from a typed ReviewState dict."""
    if review_state is None:
        return None
    coordination = review_state.get("coordination")
    return coordination if isinstance(coordination, dict) else None


def _extract_typed_packets(
    review_state: dict[str, Any] | None,
) -> list[PendingPacketFields]:
    """Extract pending review packets from a typed ReviewState dict.

    Returns only live pending packets so the dashboard surfaces actionable
    items that need operator or agent attention and leaves stale history in
    the underlying packet log.
    """
    if review_state is None:
        return []
    packets = review_state.get("packets", [])
    if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
        return []
    pending: list[PendingPacketFields] = []
    for pkt in live_pending_packets(packets):
        pending.append(PendingPacketFields(
            packet_id=pkt.get("packet_id", ""),
            kind=pkt.get("kind", ""),
            from_agent=pkt.get("from_agent", ""),
            to_agent=pkt.get("to_agent", ""),
            summary=pkt.get("summary", ""),
            status="pending",
            requested_action=pkt.get("requested_action", ""),
            policy_hint=pkt.get("policy_hint", ""),
            target_ref=pkt.get("target_ref", ""),
            target_revision=pkt.get("target_revision", ""),
            target_role=pkt.get("target_role", ""),
            target_session_id=pkt.get("target_session_id", ""),
            approval_required=pkt.get("approval_required", False),
            posted_at=pkt.get("posted_at", ""),
            delivery_emitted_at_utc=pkt.get("delivery_emitted_at_utc", ""),
            delivery_observed_at_utc=pkt.get("delivery_observed_at_utc", ""),
            delivery_observed_by=pkt.get("delivery_observed_by", ""),
            execution_started_at_utc=pkt.get("execution_started_at_utc", ""),
            execution_started_by=pkt.get("execution_started_by", ""),
            lifecycle_current_state=pkt.get("lifecycle_current_state", ""),
            semantic_zref=pkt.get("semantic_zref", ""),
        ))
    return pending


def _extract_typed_control_packets(
    review_state: dict[str, Any] | None,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Extract action-request lifecycle rows from typed ReviewState.

    This is deliberately broader than ``pending_packets``: acknowledged,
    in-progress, failed, apply-pending, and applied action requests must stay
    visible to operator and agent surfaces even after they leave the live
    pending queue.
    """
    if review_state is None:
        return []
    packets = review_state.get("packets", [])
    if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
        return []
    rows = [
        _control_packet_row(pkt)
        for pkt in packets
        if isinstance(pkt, dict) and str(pkt.get("kind") or "").strip() == "action_request"
    ]
    rows = [row for row in rows if row]
    return sorted(rows, key=_control_packet_sort_key, reverse=True)[:limit]


def _control_packet_row(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "packet_id": packet.get("packet_id", ""),
        "kind": packet.get("kind", ""),
        "from_agent": packet.get("from_agent", ""),
        "to_agent": packet.get("to_agent", ""),
        "summary": packet.get("summary", ""),
        "status": packet.get("status", ""),
        "requested_action": packet.get("requested_action", ""),
        "policy_hint": packet.get("policy_hint", ""),
        "target_ref": packet.get("target_ref", ""),
        "target_revision": packet.get("target_revision", ""),
        "target_role": packet.get("target_role", ""),
        "target_session_id": packet.get("target_session_id", ""),
        "posted_at": packet.get("posted_at", ""),
        "acked_at_utc": packet.get("acked_at_utc", ""),
        "acked_by": packet.get("acked_by", ""),
        "applied_at_utc": packet.get("applied_at_utc", ""),
        "delivery_emitted_at_utc": packet.get("delivery_emitted_at_utc", ""),
        "delivery_observed_at_utc": packet.get("delivery_observed_at_utc", ""),
        "delivery_observed_by": packet.get("delivery_observed_by", ""),
        "execution_started_at_utc": packet.get("execution_started_at_utc", ""),
        "execution_started_by": packet.get("execution_started_by", ""),
        "execution_failed_at_utc": packet.get("execution_failed_at_utc", ""),
        "execution_failed_by": packet.get("execution_failed_by", ""),
        "execution_failed_reason": packet.get("execution_failed_reason", ""),
        "apply_pending_after_execution_at_utc": packet.get(
            "apply_pending_after_execution_at_utc",
            "",
        ),
        "apply_pending_after_execution_by": packet.get(
            "apply_pending_after_execution_by",
            "",
        ),
        "apply_pending_after_execution_reason": packet.get(
            "apply_pending_after_execution_reason",
            "",
        ),
        "lifecycle_current_state": packet.get("lifecycle_current_state", ""),
        "semantic_zref": packet.get("semantic_zref", ""),
        "source_identity": packet.get("source_identity", {}),
    }


def _control_packet_sort_key(packet: dict[str, Any]) -> str:
    return str(
        packet.get("apply_pending_after_execution_at_utc")
        or packet.get("execution_failed_at_utc")
        or packet.get("applied_at_utc")
        or packet.get("execution_started_at_utc")
        or packet.get("acked_at_utc")
        or packet.get("delivery_observed_at_utc")
        or packet.get("posted_at")
        or ""
    )


def _extract_typed_bridge_fields(
    review_state: dict[str, Any],
) -> BridgeFields:
    """Map ReviewState.bridge into the same shape as _parse_bridge() output.

    The typed ReviewBridgeState carries current_instruction, open_findings,
    reviewer_mode, last_codex_poll_utc, and last_reviewed_scope. Verdict is
    extracted from ``reviewer_runtime.review_acceptance.current_verdict``
    which is the typed equivalent of the bridge "Current Verdict" section.
    """
    bridge = review_state.get("bridge", {})
    if not isinstance(bridge, dict):
        bridge = {}
    reviewer_runtime = review_state.get("reviewer_runtime", {})
    if not isinstance(reviewer_runtime, dict):
        reviewer_runtime = {}
    instr = bridge.get("current_instruction", "")
    poll_utc = bridge.get("last_codex_poll_utc", "")
    findings = bridge.get("open_findings", "")
    scope = bridge.get("last_reviewed_scope", "")
    truncated = instr[:120] + ("..." if len(instr) > 120 else "") if instr else "n/a"
    reviewer_mode = (
        bridge.get("effective_reviewer_mode")
        or reviewer_runtime.get("effective_reviewer_mode")
        or bridge.get("reviewer_mode")
        or reviewer_runtime.get("reviewer_mode")
        or "n/a"
    )
    verdict = _resolve_typed_verdict(review_state)
    return BridgeFields(
        last_poll=poll_utc if poll_utc else "n/a",
        last_poll_utc=poll_utc,
        reviewer_mode=reviewer_mode,
        instruction=truncated,
        verdict=verdict,
        findings_raw=findings,
        reviewed_scope_raw=scope,
        instruction_full=instr if instr else "n/a",
    )


def _resolve_typed_verdict(review_state: dict[str, Any]) -> str:
    """Extract the current verdict from ReviewerRuntimeContract.review_acceptance.

    Falls back to "n/a" when the reviewer_runtime subtree is absent or
    the current_verdict field is empty.
    """
    rt = review_state.get("reviewer_runtime", {})
    if not isinstance(rt, dict):
        return "n/a"
    acceptance = rt.get("review_acceptance", {})
    if not isinstance(acceptance, dict):
        return "n/a"
    verdict = acceptance.get("current_verdict", "")
    return verdict.strip() if verdict and verdict.strip() else "n/a"


def _extract_typed_bridge_findings(
    review_state: dict[str, Any],
) -> list[dict[str, str]]:
    """Extract structured findings from ReviewState bridge or session fields.

    Parses the open_findings markdown list (``- F1: summary``) into the same
    shape as _parse_bridge_findings() so downstream builders work unchanged.
    """
    bridge = review_state.get("bridge", {})
    raw = ""
    if isinstance(bridge, dict):
        raw = bridge.get("open_findings", "")
    if not raw:
        cs = review_state.get("current_session", {})
        if isinstance(cs, dict):
            raw = cs.get("open_findings", "")
    if not raw:
        return []
    findings: list[dict[str, str]] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        body = stripped[2:].strip()
        fid_match = re.match(r"(F\d+)\s*:\s*(.*)", body)
        if fid_match:
            fid = fid_match.group(1)
            desc = fid_match.group(2).strip()
        else:
            fid = f"F{len(findings) + 1}"
            desc = body
        summary = desc[:80] + ("..." if len(desc) > 80 else "")
        findings.append({"id": fid, "summary": summary})
    return findings


def _extract_typed_runtime_counts(
    review_state: dict[str, Any] | None,
) -> dict[str, int]:
    """Extract derived live/planned runtime counts from typed ReviewState."""
    if review_state is None:
        return {}
    doctor = _extract_typed_doctor(review_state)
    runtime_counts = doctor.get("runtime_counts", {})
    if isinstance(runtime_counts, dict) and runtime_counts:
        return {
            str(key): int(value or 0)
            for key, value in runtime_counts.items()
            if isinstance(key, str)
        }
    return build_runtime_counts(
        bridge_liveness=(
            review_state.get("bridge")
            if isinstance(review_state.get("bridge"), dict)
            else {}
        ),
        collaboration=(
            review_state.get("collaboration")
            if isinstance(review_state.get("collaboration"), dict)
            else {}
        ),
        publisher_running=bool(doctor.get("publisher_running")),
        reviewer_supervisor_running=bool(
            doctor.get("reviewer_supervisor_running")
        ),
    )
