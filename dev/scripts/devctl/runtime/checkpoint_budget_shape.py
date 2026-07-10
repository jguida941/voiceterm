"""Typed checkpoint-budget classifier contract."""

from __future__ import annotations

from dataclasses import asdict, dataclass


CHECKPOINT_BUDGET_SHAPE_CONTRACT_ID = "CheckpointBudgetShape"
CHECKPOINT_BUDGET_SHAPE_SCHEMA_VERSION = 1

CHECKPOINT_BUDGET_WITHIN_BUDGET = "within_budget"
CHECKPOINT_BUDGET_COMMIT_GATE_BYPASS = "commit_gate_bypass"
CHECKPOINT_BUDGET_RAW_EXCEEDED = "raw_budget_exceeded"
CHECKPOINT_BUDGET_TYPED_PIPELINE = "typed_checkpoint_pipeline"
CHECKPOINT_BUDGET_PIPELINE_DRIFTED = "typed_checkpoint_pipeline_drifted"
CHECKPOINT_BUDGET_PIPELINE_INCOMPLETE = "typed_checkpoint_pipeline_incomplete"

CHECKPOINT_NEXT_ACTION_NONE = "none"
CHECKPOINT_NEXT_ACTION_CUT_CHECKPOINT = "checkpoint_before_continue"
CHECKPOINT_NEXT_ACTION_RUN_VALIDATION = "run_checkpoint_validation"
CHECKPOINT_NEXT_ACTION_REPAIR = "repair_governed_checkpoint"
CHECKPOINT_NEXT_ACTION_GOVERNED_COMMIT = "governed_checkpoint_commit"


@dataclass(frozen=True, slots=True)
class CheckpointBudgetShape:
    """Classify startup checkpoint pressure without granting raw VCS authority."""

    schema_version: int = CHECKPOINT_BUDGET_SHAPE_SCHEMA_VERSION
    contract_id: str = CHECKPOINT_BUDGET_SHAPE_CONTRACT_ID
    state: str = CHECKPOINT_BUDGET_WITHIN_BUDGET
    reason: str = ""
    checkpoint_required: bool = False
    safe_to_continue_editing: bool = True
    staged_path_count: int = 0
    unstaged_path_count: int = 0
    dirty_path_count: int = 0
    untracked_path_count: int = 0
    pipeline_id: str = ""
    pipeline_state: str = ""
    pipeline_staged_path_count: int = 0
    staged_tree_hash: str = ""
    current_tree_hash: str = ""
    tree_hash_match: bool = False
    typed_pipeline_parked: bool = False
    receipt_backed: bool = False
    guard_action_id: str = ""
    guard_status: str = ""
    guard_ok: bool = False
    validation_receipt_id: str = ""
    validation_receipt_status: str = ""
    validation_checkpoint_sufficient: bool = False
    bootstrap_blocked: bool = False
    next_required_action: str = CHECKPOINT_NEXT_ACTION_NONE
    blocked_raw_actions: tuple[str, ...] = ("git.commit", "vcs.push")
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["blocked_raw_actions"] = list(self.blocked_raw_actions)
        payload["errors"] = list(self.errors)
        return payload


__all__ = [
    "CHECKPOINT_BUDGET_COMMIT_GATE_BYPASS",
    "CHECKPOINT_BUDGET_PIPELINE_DRIFTED",
    "CHECKPOINT_BUDGET_PIPELINE_INCOMPLETE",
    "CHECKPOINT_BUDGET_RAW_EXCEEDED",
    "CHECKPOINT_BUDGET_SHAPE_CONTRACT_ID",
    "CHECKPOINT_BUDGET_SHAPE_SCHEMA_VERSION",
    "CHECKPOINT_BUDGET_TYPED_PIPELINE",
    "CHECKPOINT_BUDGET_WITHIN_BUDGET",
    "CHECKPOINT_NEXT_ACTION_CUT_CHECKPOINT",
    "CHECKPOINT_NEXT_ACTION_GOVERNED_COMMIT",
    "CHECKPOINT_NEXT_ACTION_NONE",
    "CHECKPOINT_NEXT_ACTION_REPAIR",
    "CHECKPOINT_NEXT_ACTION_RUN_VALIDATION",
    "CheckpointBudgetShape",
]
