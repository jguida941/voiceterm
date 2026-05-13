"""Runtime target validation for review-channel packet posts."""

from __future__ import annotations

from .pending_packet_models import (
    PacketGuardBundleEvidenceFields,
    PacketRuntimeApprovalFields,
    validate_full_guard_bundle_evidence,
)

RUNTIME_ACTION_REQUEST_ACTIONS = {
    "commit",
    "kill_process",
    "push",
    "run_check",
    "stage_commit_pipeline",
}
PIPELINE_ACTION_REQUEST_ACTIONS = {"commit", "push"}
STAGE_PIPELINE_ACTION_REQUEST_ACTIONS = {"stage_commit_pipeline"}


def validate_action_request_target_fields(
    *,
    requested_action: str,
    target,
    runtime_approval: PacketRuntimeApprovalFields,
    guard_bundle_evidence: PacketGuardBundleEvidenceFields,
    resource_target_values_present: bool,
    validate_optional_plan_intent_fields,
) -> None:
    action = (requested_action or "").strip()
    if action not in RUNTIME_ACTION_REQUEST_ACTIONS:
        _validate_non_runtime_action_request(
            action=action,
            target=target,
            runtime_approval=runtime_approval,
            guard_bundle_evidence=guard_bundle_evidence,
            resource_target_values_present=resource_target_values_present,
            validate_optional_plan_intent_fields=validate_optional_plan_intent_fields,
        )
        return

    if target.target_kind != "runtime":
        raise ValueError(
            "Runtime action_request packets must set --target-kind runtime."
        )
    if not target.target_ref:
        raise ValueError("Runtime action_request packets require --target-ref.")
    if not target.target_revision:
        raise ValueError("Runtime action_request packets require --target-revision.")
    if target.anchor_refs or target.intake_ref or target.mutation_op:
        raise ValueError(
            "Plan mutation fields are not valid on runtime action_request packets."
        )

    if action in STAGE_PIPELINE_ACTION_REQUEST_ACTIONS:
        _validate_stage_pipeline_action_request(
            target=target,
            runtime_approval=runtime_approval,
            guard_bundle_evidence=guard_bundle_evidence,
        )
        return
    if action in PIPELINE_ACTION_REQUEST_ACTIONS:
        _validate_pipeline_action_request(
            target=target,
            runtime_approval=runtime_approval,
            guard_bundle_evidence=guard_bundle_evidence,
        )
        return
    if runtime_approval.has_values() or guard_bundle_evidence.has_values():
        raise ValueError(
            "Runtime guard fields are only allowed on commit/push "
            "action_request packets, stage-commit action_request packets, or "
            "`commit_approval` packets."
        )


def _validate_non_runtime_action_request(
    *,
    action: str,
    target,
    runtime_approval: PacketRuntimeApprovalFields,
    guard_bundle_evidence: PacketGuardBundleEvidenceFields,
    resource_target_values_present: bool,
    validate_optional_plan_intent_fields,
) -> None:
    if (
        resource_target_values_present
        or runtime_approval.has_values()
        or guard_bundle_evidence.has_values()
    ):
        raise ValueError(
            "Resource target fields on `action_request` packets are only "
            "allowed for runtime actions: "
            + ", ".join(sorted(RUNTIME_ACTION_REQUEST_ACTIONS))
            + "."
        )
    if not (target.target_role or target.target_session_id):
        raise ValueError(
            "Non-runtime action_request packets require route scope "
            "(--target-role or --target-session-id). Use an instruction "
            "packet for unscoped guidance."
        )
    validate_optional_plan_intent_fields(target)


def _validate_stage_pipeline_action_request(
    *,
    target,
    runtime_approval: PacketRuntimeApprovalFields,
    guard_bundle_evidence: PacketGuardBundleEvidenceFields,
) -> None:
    if not target.target_ref.startswith("devctl_commit:"):
        raise ValueError(
            "Stage-commit action_request packets must target "
            "`devctl_commit:<head_sha>`."
        )
    if runtime_approval.has_values():
        if not runtime_approval.pipeline_generation:
            raise ValueError(
                "Stage-commit action_request packets with pipeline evidence "
                "require --pipeline-generation."
            )
        if not runtime_approval.staged_snapshot_hash:
            raise ValueError(
                "Stage-commit action_request packets with pipeline evidence "
                "require --staged-snapshot-hash."
            )
    validate_full_guard_bundle_evidence(guard_bundle_evidence, required=True)


def _validate_pipeline_action_request(
    *,
    target,
    runtime_approval: PacketRuntimeApprovalFields,
    guard_bundle_evidence: PacketGuardBundleEvidenceFields,
) -> None:
    if not target.target_ref.startswith("remote_commit_pipeline:"):
        raise ValueError(
            "Commit/push action_request packets must target "
            "`remote_commit_pipeline:<pipeline_id>`."
        )
    if not runtime_approval.pipeline_generation:
        raise ValueError(
            "Commit/push action_request packets require --pipeline-generation."
        )
    if not runtime_approval.staged_snapshot_hash:
        raise ValueError(
            "Commit/push action_request packets require --staged-snapshot-hash."
        )
    if not runtime_approval.guard_results_summary:
        raise ValueError(
            "Commit/push action_request packets require --guard-results-summary."
        )
    if guard_bundle_evidence.has_values():
        validate_full_guard_bundle_evidence(guard_bundle_evidence)
