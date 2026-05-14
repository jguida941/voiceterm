"""Receipt-bound promotion for verified checkpoint repair work."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from .action_contracts import ActionOutcome
from .remote_commit_pipeline_models import RemoteCommitPipelineContract
from .value_coercion import coerce_bool, coerce_mapping, coerce_string, coerce_string_items


CHECKPOINT_REPAIR_AUTHORITY_CONTRACT_ID = "CheckpointRepairAuthority"
CHECKPOINT_REPAIR_AUTHORITY_SCHEMA_VERSION = 1
GOVERNED_CHECKPOINT_COMMIT = "governed_checkpoint_commit"
GOVERNED_CHECKPOINT_COMMIT_COMMAND = (
    'python3 dev/scripts/devctl.py commit -m "<descriptive message>"'
)
REPAIR_VERIFIED = "repair_verified"
GUARD_BUNDLE_FAILED = "guard_bundle_failed"


@dataclass(frozen=True, slots=True)
class CheckpointRepairAuthority:
    """Typed authority promotion after a scoped checkpoint repair is verified."""

    schema_version: int = CHECKPOINT_REPAIR_AUTHORITY_SCHEMA_VERSION
    contract_id: str = CHECKPOINT_REPAIR_AUTHORITY_CONTRACT_ID
    pipeline_id: str = ""
    generation_id: str = ""
    original_block_reason: str = ""
    result: str = ""
    next_authorized_action: str = ""
    source_action_id: str = ""
    validation_receipt_id: str = ""
    staged_tree_hash: str = ""
    selected_paths: tuple[str, ...] = ()
    checkpoint_sufficient: bool = False
    blocked_raw_actions: tuple[str, ...] = ("git.commit", "vcs.push")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["selected_paths"] = list(self.selected_paths)
        payload["blocked_raw_actions"] = list(self.blocked_raw_actions)
        return payload


def build_checkpoint_repair_authority(
    *,
    previous_pipeline: RemoteCommitPipelineContract,
    repaired_pipeline: RemoteCommitPipelineContract,
) -> CheckpointRepairAuthority | None:
    """Promote a prior guard failure only when fresh matching proof passes."""
    original_reason = _original_guard_failure_reason(previous_pipeline)
    if not original_reason:
        return None
    if not _has_matching_checkpoint_receipt(repaired_pipeline):
        return None

    guard_result = repaired_pipeline.guard_result
    validation_receipt = repaired_pipeline.validation_receipt
    if guard_result is None or validation_receipt is None:
        return None
    return CheckpointRepairAuthority(
        pipeline_id=repaired_pipeline.pipeline_id,
        generation_id=repaired_pipeline.generation_id,
        original_block_reason=original_reason,
        result=REPAIR_VERIFIED,
        next_authorized_action=GOVERNED_CHECKPOINT_COMMIT,
        source_action_id=guard_result.action_id,
        validation_receipt_id=validation_receipt.receipt_id,
        staged_tree_hash=repaired_pipeline.intent.staged_tree_hash,
        selected_paths=repaired_pipeline.intent.staged_paths,
        checkpoint_sufficient=True,
    )


def checkpoint_repair_authority_from_pipeline(
    pipeline: RemoteCommitPipelineContract,
) -> CheckpointRepairAuthority | None:
    """Read a persisted checkpoint repair promotion from a pipeline."""
    direct = checkpoint_repair_authority_from_mapping(
        pipeline.checkpoint_repair_authority
    )
    if direct is not None:
        return direct
    return checkpoint_repair_authority_from_mapping(pipeline.push_failure_transition)


def checkpoint_repair_authority_from_mapping(
    payload: Mapping[str, object],
) -> CheckpointRepairAuthority | None:
    """Normalize a persisted checkpoint repair promotion mapping."""
    mapping = coerce_mapping(payload)
    if not mapping:
        return None
    if (
        coerce_string(mapping.get("contract_id"))
        != CHECKPOINT_REPAIR_AUTHORITY_CONTRACT_ID
    ):
        return None
    if coerce_string(mapping.get("result")) != REPAIR_VERIFIED:
        return None
    if coerce_string(mapping.get("next_authorized_action")) != GOVERNED_CHECKPOINT_COMMIT:
        return None
    return CheckpointRepairAuthority(
        pipeline_id=coerce_string(mapping.get("pipeline_id")),
        generation_id=coerce_string(mapping.get("generation_id")),
        original_block_reason=coerce_string(mapping.get("original_block_reason")),
        result=REPAIR_VERIFIED,
        next_authorized_action=GOVERNED_CHECKPOINT_COMMIT,
        source_action_id=coerce_string(mapping.get("source_action_id")),
        validation_receipt_id=coerce_string(mapping.get("validation_receipt_id")),
        staged_tree_hash=coerce_string(mapping.get("staged_tree_hash")),
        selected_paths=coerce_string_items(mapping.get("selected_paths")),
        checkpoint_sufficient=coerce_bool(mapping.get("checkpoint_sufficient")),
        blocked_raw_actions=coerce_string_items(mapping.get("blocked_raw_actions"))
        or ("git.commit", "vcs.push"),
    )


def _original_guard_failure_reason(pipeline: RemoteCommitPipelineContract) -> str:
    reason = str(pipeline.blocked_reason or "").strip()
    if reason == GUARD_BUNDLE_FAILED:
        return reason
    guard_result = pipeline.guard_result
    if guard_result is None:
        return ""
    if guard_result.reason == GUARD_BUNDLE_FAILED:
        return GUARD_BUNDLE_FAILED
    return ""


def _has_matching_checkpoint_receipt(
    pipeline: RemoteCommitPipelineContract,
) -> bool:
    guard_result = pipeline.guard_result
    if guard_result is None or not guard_result.ok:
        return False
    if guard_result.status != ActionOutcome.PASS:
        return False
    validation_receipt = pipeline.validation_receipt
    if validation_receipt is None:
        return False
    if not validation_receipt.checkpoint_sufficient:
        return False
    return validation_receipt.staged_tree_hash == pipeline.intent.staged_tree_hash


__all__ = [
    "CHECKPOINT_REPAIR_AUTHORITY_CONTRACT_ID",
    "GOVERNED_CHECKPOINT_COMMIT",
    "GOVERNED_CHECKPOINT_COMMIT_COMMAND",
    "GUARD_BUNDLE_FAILED",
    "REPAIR_VERIFIED",
    "CheckpointRepairAuthority",
    "build_checkpoint_repair_authority",
    "checkpoint_repair_authority_from_mapping",
    "checkpoint_repair_authority_from_pipeline",
]
