"""Checkpoint repair policy kwargs for AgentLoopPolicy."""

from __future__ import annotations

from dataclasses import dataclass, fields

from .checkpoint_repair_authority import GOVERNED_CHECKPOINT_COMMIT


@dataclass(frozen=True, slots=True)
class CheckpointPolicyProjection:
    """Constructor fields for AgentLoopPolicy checkpoint projections."""

    loop_mode: str
    loop_driver_agent: str
    loop_intent: str
    recommended_cadence_seconds: int
    can_run_next_command: bool
    dogfood_record_allowed: bool
    proof_gate: object
    policy_reason: str
    next_loop_command: str

    def as_policy_kwargs(self) -> dict[str, object]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


def operator_override_edit_policy_kwargs(
    ctx,
    driver: str,
    cadence: int,
    proof: object,
    command: str,
    required_action: str,
) -> dict[str, object]:
    """Return edit-only override policy fields for checkpoint/startup blockers."""
    policy_reason = "operator_override_edit_only_allows_scoped_implementation"
    if required_action == GOVERNED_CHECKPOINT_COMMIT:
        policy_reason = "operator_override_edit_only_blocks_governed_checkpoint_commit"
    return CheckpointPolicyProjection(
        loop_mode="operator_override_edit",
        loop_driver_agent=driver,
        loop_intent=str(ctx.loop_intent or ""),
        recommended_cadence_seconds=max(15, min(cadence, 60)),
        can_run_next_command=False,
        dogfood_record_allowed=True,
        proof_gate=proof,
        policy_reason=policy_reason,
        next_loop_command=command,
    ).as_policy_kwargs()


def governed_checkpoint_policy_kwargs(
    ctx,
    driver: str,
    cadence: int,
    proof: object,
    command: str,
) -> dict[str, object]:
    """Return authorized governed checkpoint policy fields."""
    return CheckpointPolicyProjection(
        loop_mode=GOVERNED_CHECKPOINT_COMMIT,
        loop_driver_agent=driver,
        loop_intent=str(ctx.loop_intent or ""),
        recommended_cadence_seconds=max(15, min(cadence, 60)),
        can_run_next_command=True,
        dogfood_record_allowed=True,
        proof_gate=proof,
        policy_reason="checkpoint_repair_receipts_authorize_governed_commit",
        next_loop_command=command,
    ).as_policy_kwargs()


__all__ = [
    "CheckpointPolicyProjection",
    "governed_checkpoint_policy_kwargs",
    "operator_override_edit_policy_kwargs",
]
