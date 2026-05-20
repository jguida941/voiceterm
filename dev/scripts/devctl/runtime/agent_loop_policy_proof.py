"""Typed proof gates for autonomous agent loop policy."""

from __future__ import annotations

from dataclasses import dataclass

from .agent_loop_proof_context import LoopProofContext
from .agent_loop_proof_evidence import satisfied_proofs as collect_satisfied_proofs


@dataclass(frozen=True, slots=True)
class AgentLoopProofGate:
    """Typed evidence gate for advancing one autonomous loop round."""

    target_kind: str = ""
    target_ref: str = ""
    proof_state: str = "missing"
    advance_allowed: bool = False
    required_proofs: tuple[str, ...] = ()
    satisfied_proofs: tuple[str, ...] = ()
    missing_proofs: tuple[str, ...] = ()
    reason: str = ""


def proof_gate_for_turn(
    *,
    ctx: LoopProofContext,
    loop_state: str,
    required_action: str,
    active_packet_id: str,
    plan_target_ref: str,
) -> AgentLoopProofGate:
    """Resolve typed proof required before this mode can advance."""
    target_kind, target_ref = target_for_turn(
        ctx=ctx,
        active_packet_id=active_packet_id,
        plan_target_ref=plan_target_ref,
        required_action=required_action,
    )
    required = required_proofs_for_intent(
        ctx.loop_intent,
        loop_state=loop_state,
        required_action=required_action,
        target_kind=target_kind,
    )
    satisfied = collect_satisfied_proofs(
        ctx=ctx,
        active_packet_id=active_packet_id,
        plan_target_ref=plan_target_ref,
        target_kind=target_kind,
        target_ref=target_ref,
    )
    missing = tuple(item for item in required if item not in satisfied)
    proof_state = "not_required" if not required else "satisfied"
    if missing:
        proof_state = "missing"
    return AgentLoopProofGate(
        target_kind=target_kind,
        target_ref=target_ref,
        proof_state=proof_state,
        advance_allowed=bool(required) and not missing,
        required_proofs=required,
        satisfied_proofs=tuple(item for item in required if item in satisfied),
        missing_proofs=missing,
        reason=proof_reason(proof_state, missing),
    )


def target_for_turn(
    *,
    ctx: LoopProofContext,
    active_packet_id: str,
    plan_target_ref: str,
    required_action: str = "",
) -> tuple[str, str]:
    if (
        required_action
        in {"open_packet_body", "ingest_packet_semantics", "absorb_packet"}
        and active_packet_id
    ):
        return "packet", active_packet_id
    if ctx.requested_packet_id:
        return "packet", ctx.requested_packet_id
    if ctx.requested_plan_ref:
        return "plan", ctx.requested_plan_ref
    if active_packet_id:
        return "packet", active_packet_id
    if plan_target_ref:
        return "plan", plan_target_ref
    return "", ""


def required_proofs_for_intent(
    intent: str,
    *,
    loop_state: str,
    required_action: str,
    target_kind: str,
) -> tuple[str, ...]:
    base = ["typed_runtime_clock"]
    if target_kind == "packet":
        base.append("scoped_packet_target")
    elif target_kind == "plan":
        base.append("plan_target")
    if intent in {"iterate", "full-plan"} or required_action == "stop_no_work":
        base.extend(
            [
                "implementer_handoff",
                "guard_bundle_or_attestation",
                "reviewer_semantic_review",
                "round_proof",
            ]
        )
    elif required_action == "launch_peer_digest_sidecar":
        base.extend(["packet_attention_evidence", "peer_digest_sidecar_observation"])
    elif (
        intent in {"wake", "packet", "plan"}
        or loop_state == "work"
        or required_action == "open_packet_body"
    ):
        base.append("packet_attention_evidence")
    return tuple(dict.fromkeys(base))


def proof_reason(proof_state: str, missing: tuple[str, ...]) -> str:
    if proof_state == "not_required":
        return "loop_intent_does_not_require_advance_proof"
    if proof_state == "satisfied":
        return "required_round_proofs_satisfied"
    return "missing_round_proof:" + ",".join(missing)


__all__ = ["AgentLoopProofGate", "proof_gate_for_turn"]
