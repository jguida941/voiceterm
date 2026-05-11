"""Compact proof evidence for agent-loop output surfaces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ...runtime.review_state_round_proof import build_round_proofs_from_review_state


def compact_master_plan_authority(
    master_plan: Mapping[str, Any],
    *,
    target_ref: str = "",
) -> dict[str, Any]:
    """Return output-safe MasterPlan evidence without dumping every PlanRow."""
    rows = _mapping_rows(master_plan.get("rows"))
    matches = [
        _compact_plan_row(row)
        for row in rows
        if target_ref and target_ref in _plan_row_refs(row)
    ]
    return {
        "contract_id": "MasterPlanAuthorityEvidence",
        "authority_state": str(master_plan.get("authority_state") or "unknown"),
        "typed_store_path": str(master_plan.get("typed_store_path") or ""),
        "projection_path": str(master_plan.get("projection_path") or ""),
        "row_count": len(rows),
        "target_ref": target_ref,
        "target_state": _target_state(target_ref=target_ref, matches=matches),
        "matched_rows": matches[:5],
        "omitted_matched_row_count": max(0, len(matches) - 5),
    }


def build_loop_proof_evidence(
    *,
    loop_decision: Mapping[str, Any],
    master_plan_authority: Mapping[str, Any],
    review_state: Mapping[str, Any],
) -> dict[str, Any]:
    """Expose the exact proof sources an agent must inspect after a run."""
    required = _string_items(loop_decision.get("required_proofs"))
    satisfied = _string_items(loop_decision.get("satisfied_proofs"))
    missing = _string_items(loop_decision.get("missing_proofs"))
    return {
        "contract_id": "AgentLoopProofEvidence",
        "proof_state": str(loop_decision.get("proof_state") or "missing"),
        "required_proofs": list(required),
        "satisfied_proofs": list(satisfied),
        "missing_proofs": list(missing),
        "proofs": _proof_entries(
            required=required,
            satisfied=satisfied,
            missing=missing,
            loop_decision=loop_decision,
            master_plan_authority=master_plan_authority,
            review_state=review_state,
        ),
        "runtime_clock": _runtime_clock_evidence(loop_decision),
        "plan_target": _plan_target_evidence(
            loop_decision=loop_decision,
            master_plan_authority=master_plan_authority,
        ),
        "round_proof": _round_proof_evidence(
            loop_decision=loop_decision,
            review_state=review_state,
        ),
    }


def _target_state(*, target_ref: str, matches: Sequence[Mapping[str, Any]]) -> str:
    if not target_ref:
        return "not_requested"
    return "satisfied" if matches else "missing"


def _runtime_clock_evidence(loop_decision: Mapping[str, Any]) -> dict[str, Any]:
    event_id = str(loop_decision.get("source_latest_event_id") or "")
    snapshot_id = str(loop_decision.get("source_snapshot_id") or "")
    return {
        "state": "satisfied" if event_id or snapshot_id else "missing",
        "source_latest_event_id": event_id,
        "snapshot_id": snapshot_id,
    }


def _plan_target_evidence(
    *,
    loop_decision: Mapping[str, Any],
    master_plan_authority: Mapping[str, Any],
) -> dict[str, Any]:
    required = "plan_target" in _string_items(loop_decision.get("required_proofs"))
    return {
        "required": required,
        "state": (
            str(master_plan_authority.get("target_state") or "missing")
            if required
            else "not_required"
        ),
        "target_ref": str(master_plan_authority.get("target_ref") or ""),
        "authority_source": "MasterPlan/PlanRow",
        "typed_store_path": str(master_plan_authority.get("typed_store_path") or ""),
        "row_count": int(master_plan_authority.get("row_count") or 0),
        "matched_rows": list(master_plan_authority.get("matched_rows") or []),
    }


def _round_proof_evidence(
    *,
    loop_decision: Mapping[str, Any],
    review_state: Mapping[str, Any],
) -> dict[str, Any]:
    required = "round_proof" in _string_items(loop_decision.get("required_proofs"))
    target_ref = str(loop_decision.get("target_ref") or "")
    rows = _round_proof_rows(review_state)
    matching_rows = [
        row for row in rows if not target_ref or target_ref in _round_row_refs(row)
    ]
    matches = [_compact_round_row(row) for row in matching_rows]
    satisfied = any(
        str(row.get("proof_state") or row.get("status") or "") in _ROUND_OK_STATES
        for row in matching_rows
    )
    return {
        "required": required,
        "state": (
            "satisfied" if satisfied else "missing"
        ) if required else "not_required",
        "target_ref": target_ref,
        "row_count": len(rows),
        "matched_rows": matches[:5],
        "omitted_matched_row_count": max(0, len(matches) - 5),
    }


def _compact_plan_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "row_id": str(row.get("row_id") or ""),
        "status": str(row.get("status") or ""),
        "target_ref": str(row.get("target_ref") or ""),
        "anchor_refs": list(_string_items(row.get("anchor_refs"))),
        "source_doc_path": str(row.get("source_doc_path") or ""),
        "source_line": int(row.get("source_line") or 0),
    }


def _compact_round_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "proof_id": str(row.get("proof_id") or ""),
        "status": str(row.get("status") or ""),
        "proof_state": str(row.get("proof_state") or ""),
        "actor_id": str(row.get("actor_id") or ""),
        "role": str(row.get("role") or ""),
        "session_id": str(row.get("session_id") or ""),
        "target_ref": str(row.get("target_ref") or ""),
        "handoff_packet_id": str(row.get("handoff_packet_id") or ""),
        "missing_proofs": list(_string_items(row.get("missing_proofs"))),
    }


def _round_proof_rows(
    review_state: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    rows = _mapping_rows(review_state.get("round_proofs"))
    if rows:
        return rows
    return tuple(
        row.to_dict() for row in build_round_proofs_from_review_state(review_state)
    )


def _proof_entries(
    *,
    required: tuple[str, ...],
    satisfied: tuple[str, ...],
    missing: tuple[str, ...],
    loop_decision: Mapping[str, Any],
    master_plan_authority: Mapping[str, Any],
    review_state: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for proof_id in required:
        entries[proof_id] = {
            "required": True,
            "state": _proof_state(
                proof_id=proof_id,
                satisfied=satisfied,
                missing=missing,
            ),
            "evidence": _proof_evidence_ref(
                proof_id=proof_id,
                loop_decision=loop_decision,
                master_plan_authority=master_plan_authority,
                review_state=review_state,
            ),
        }
    return entries


def _proof_state(
    *,
    proof_id: str,
    satisfied: tuple[str, ...],
    missing: tuple[str, ...],
) -> str:
    if proof_id in satisfied:
        return "satisfied"
    if proof_id in missing:
        return "missing"
    return "unknown"


def _proof_evidence_ref(
    *,
    proof_id: str,
    loop_decision: Mapping[str, Any],
    master_plan_authority: Mapping[str, Any],
    review_state: Mapping[str, Any],
) -> dict[str, Any]:
    if proof_id == "typed_runtime_clock":
        return _runtime_clock_evidence(loop_decision)
    if proof_id == "plan_target":
        return _plan_target_evidence(
            loop_decision=loop_decision,
            master_plan_authority=master_plan_authority,
        )
    if proof_id == "round_proof":
        return _round_proof_evidence(
            loop_decision=loop_decision,
            review_state=review_state,
        )
    if proof_id == "scoped_packet_target":
        return {
            "active_packet_id": str(loop_decision.get("active_packet_id") or ""),
            "attention_packet_id": str(loop_decision.get("attention_packet_id") or ""),
            "executing_packet_id": str(loop_decision.get("executing_packet_id") or ""),
        }
    if proof_id in {"packet_attention_evidence", "wake_or_attention_evidence"}:
        operator_override = _operator_override(loop_decision)
        return {
            "wake_required": bool(loop_decision.get("wake_required")),
            "pivot_required": bool(loop_decision.get("pivot_required")),
            "pending_packet_count": int(loop_decision.get("pending_packet_count") or 0),
            "latest_inbox_event_id": str(loop_decision.get("latest_inbox_event_id") or ""),
            "last_observed_event_id": str(loop_decision.get("last_observed_event_id") or ""),
            "operator_override_active": bool(operator_override.get("active")),
            "operator_override_source": str(operator_override.get("source") or ""),
            "operator_override_target_kind": str(
                operator_override.get("target_kind") or ""
            ),
            "operator_override_target_ref": str(
                operator_override.get("target_ref") or ""
            ),
        }
    if proof_id == "implementer_handoff":
        return {"target_ref": str(loop_decision.get("target_ref") or "")}
    if proof_id == "guard_bundle_or_attestation":
        return {"authority_source": "ReviewPacket.guard_evidence"}
    if proof_id == "reviewer_semantic_review":
        return {"authority_source": "ReviewerRuntime.duty_proof"}
    return {"authority_source": "agent_loop_decision"}


def _plan_row_refs(row: Mapping[str, Any]) -> frozenset[str]:
    refs = {
        str(row.get("row_id") or "").strip(),
        str(row.get("target_ref") or "").strip(),
    }
    refs.update(_string_items(row.get("anchor_refs")))
    return frozenset(ref for ref in refs if ref)


def _round_row_refs(row: Mapping[str, Any]) -> frozenset[str]:
    refs = {
        str(row.get("target_ref") or "").strip(),
        str(row.get("packet_id") or "").strip(),
        str(row.get("handoff_packet_id") or "").strip(),
    }
    return frozenset(ref for ref in refs if ref)


def _operator_override(loop_decision: Mapping[str, Any]) -> Mapping[str, Any]:
    value = loop_decision.get("operator_override")
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(row for row in value if isinstance(row, Mapping))


def _string_items(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


_ROUND_OK_STATES = frozenset({"accepted", "satisfied", "complete", "completed"})

__all__ = ["build_loop_proof_evidence", "compact_master_plan_authority"]
