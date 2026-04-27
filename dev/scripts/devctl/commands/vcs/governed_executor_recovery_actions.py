"""Typed action builder for bounded governed-push recovery repair."""

from __future__ import annotations

from dataclasses import dataclass

from ...runtime import TypedAction

RECOVERY_LOOP_REPAIR_ACTION_ID = "vcs.recovery_loop_repair"


@dataclass(frozen=True, slots=True)
class RecoveryLoopRepairActionInputs:
    """Structured inputs for bounded pre-validation review-loop repair."""

    repo_pack_id: str
    branch: str
    remote: str
    max_steps: int = 5
    time_budget_seconds: int = 30
    requested_by: str = "devctl.push"


def build_recovery_loop_repair_action(
    *,
    inputs: RecoveryLoopRepairActionInputs | None = None,
    **kwargs: object,
) -> TypedAction:
    """Build the canonical typed action for push recovery-loop repair."""
    resolved = inputs if inputs is not None else _inputs_from_kwargs(kwargs)
    parameters: dict[str, object] = {}
    parameters["branch"] = resolved.branch
    parameters["remote"] = resolved.remote
    parameters["max_steps"] = resolved.max_steps
    parameters["time_budget_seconds"] = resolved.time_budget_seconds
    return TypedAction(
        schema_version=1,
        contract_id="TypedAction",
        action_id=RECOVERY_LOOP_REPAIR_ACTION_ID,
        repo_pack_id=resolved.repo_pack_id,
        parameters=parameters,
        requested_by=resolved.requested_by,
        dry_run=False,
    )


def _inputs_from_kwargs(kwargs: dict[str, object]) -> RecoveryLoopRepairActionInputs:
    expected = {
        "repo_pack_id",
        "branch",
        "remote",
        "max_steps",
        "time_budget_seconds",
        "requested_by",
    }
    unexpected = sorted(kwargs.keys() - expected)
    if unexpected:
        raise TypeError(
            "Unexpected recovery-loop repair action inputs: " + ", ".join(unexpected)
        )
    return RecoveryLoopRepairActionInputs(
        repo_pack_id=str(kwargs["repo_pack_id"]),
        branch=str(kwargs["branch"]),
        remote=str(kwargs["remote"]),
        max_steps=int(kwargs.get("max_steps", 5) or 5),
        time_budget_seconds=int(kwargs.get("time_budget_seconds", 30) or 30),
        requested_by=str(kwargs.get("requested_by", "devctl.push")),
    )


__all__ = [
    "RECOVERY_LOOP_REPAIR_ACTION_ID",
    "RecoveryLoopRepairActionInputs",
    "build_recovery_loop_repair_action",
]
