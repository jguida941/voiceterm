"""Target-field validation for review-channel packet posts."""

from __future__ import annotations

import re

from .pending_packet_models import (
    PacketGuardBundleEvidenceFields,
    PacketRuntimeApprovalFields,
    validate_full_guard_bundle_evidence,
)

VALID_TARGET_KINDS = {
    "artifact",
    "code",
    "plan",
    "policy",
    "runbook",
    "runtime",
}
VALID_PLAN_MUTATION_OPS = {
    "append_audit_evidence",
    "append_progress_log",
    "rewrite_section_note",
    "rewrite_session_resume",
    "set_checklist_state",
}
RUNTIME_TARGET_PACKET_KINDS = {"commit_approval"}
RUNTIME_ACTION_REQUEST_ACTIONS = {
    "commit",
    "kill_process",
    "push",
    "run_check",
    "stage_commit_pipeline",
}
PIPELINE_ACTION_REQUEST_ACTIONS = {"commit", "push"}
STAGE_PIPELINE_ACTION_REQUEST_ACTIONS = {"stage_commit_pipeline"}
ANCHOR_REF_RE = re.compile(
    r"^(checklist|section|session_resume|progress|audit):[A-Za-z0-9][A-Za-z0-9._-]*$"
)


def validate_target_fields(
    *,
    kind: str,
    requested_action: str,
    target,
    runtime_approval: PacketRuntimeApprovalFields,
    guard_bundle_evidence: PacketGuardBundleEvidenceFields,
) -> None:
    if target.target_kind and target.target_kind not in VALID_TARGET_KINDS:
        raise ValueError(
            f"Unsupported review-channel target kind: {target.target_kind}"
        )

    if kind in {"plan_gap_review", "plan_patch_review", "plan_ready_gate"}:
        _validate_plan_target_fields(kind=kind, target=target)
        if runtime_approval.has_values() or guard_bundle_evidence.has_values():
            raise ValueError(
                "Runtime guard fields are only allowed on runtime packet kinds."
            )
        return

    if kind in RUNTIME_TARGET_PACKET_KINDS:
        _validate_runtime_approval_target_fields(
            target=target,
            runtime_approval=runtime_approval,
            guard_bundle_evidence=guard_bundle_evidence,
        )
        return

    if kind == "action_request":
        _validate_action_request_target_fields(
            requested_action=requested_action,
            target=target,
            runtime_approval=runtime_approval,
            guard_bundle_evidence=guard_bundle_evidence,
        )
        return

    if (
        target.has_values()
        or runtime_approval.has_values()
        or guard_bundle_evidence.has_values()
    ):
        raise ValueError(
            "Target fields are only allowed on plan review packets or "
            "`commit_approval` packets."
        )


def _validate_plan_target_fields(*, kind: str, target) -> None:
    if target.target_kind != "plan":
        raise ValueError("Plan review packets must set --target-kind plan.")
    if not target.target_ref:
        raise ValueError("Plan review packets require --target-ref.")
    if not target.target_revision:
        raise ValueError("Plan review packets require --target-revision.")
    if not target.anchor_refs:
        raise ValueError("Plan review packets require at least one --anchor-ref.")
    invalid = [
        ref for ref in target.anchor_refs if ANCHOR_REF_RE.fullmatch(ref) is None
    ]
    if invalid:
        raise ValueError("Invalid --anchor-ref value(s): " + ", ".join(invalid))
    if not target.intake_ref:
        raise ValueError("Plan review packets require --intake-ref.")

    if kind == "plan_patch_review":
        if target.mutation_op not in VALID_PLAN_MUTATION_OPS:
            raise ValueError(
                "Plan patch review packets require a valid --mutation-op."
            )
        return
    if target.mutation_op:
        raise ValueError(
            "--mutation-op is only valid on `plan_patch_review` packets."
        )


def _validate_runtime_approval_target_fields(
    *,
    target,
    runtime_approval: PacketRuntimeApprovalFields,
    guard_bundle_evidence: PacketGuardBundleEvidenceFields,
) -> None:
    if target.target_kind != "runtime":
        raise ValueError("Commit approval packets must set --target-kind runtime.")
    if not target.target_ref:
        raise ValueError("Commit approval packets require --target-ref.")
    if not target.target_revision:
        raise ValueError("Commit approval packets require --target-revision.")
    if not target.target_ref.startswith("remote_commit_pipeline:"):
        raise ValueError(
            "Commit approval packets must target `remote_commit_pipeline:<pipeline_id>`."
        )
    if target.anchor_refs or target.intake_ref or target.mutation_op:
        raise ValueError(
            "Plan mutation fields are not valid on `commit_approval` packets."
        )
    if not runtime_approval.pipeline_generation:
        raise ValueError("Commit approval packets require --pipeline-generation.")
    if not runtime_approval.staged_snapshot_hash:
        raise ValueError("Commit approval packets require --staged-snapshot-hash.")
    if not runtime_approval.guard_results_summary:
        raise ValueError("Commit approval packets require --guard-results-summary.")
    if guard_bundle_evidence.has_values():
        validate_full_guard_bundle_evidence(guard_bundle_evidence)


def _validate_action_request_target_fields(
    *,
    requested_action: str,
    target,
    runtime_approval: PacketRuntimeApprovalFields,
    guard_bundle_evidence: PacketGuardBundleEvidenceFields,
) -> None:
    action = (requested_action or "").strip()
    if action not in RUNTIME_ACTION_REQUEST_ACTIONS:
        if (
            target.has_values()
            or runtime_approval.has_values()
            or guard_bundle_evidence.has_values()
        ):
            raise ValueError(
                "Target fields on `action_request` packets are only allowed "
                "for runtime actions: "
                + ", ".join(sorted(RUNTIME_ACTION_REQUEST_ACTIONS))
                + "."
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
        if not target.target_ref.startswith("devctl_commit:"):
            raise ValueError(
                "Stage-commit action_request packets must target "
                "`devctl_commit:<head_sha>`."
            )
        if runtime_approval.has_values():
            raise ValueError(
                "Stage-commit action_request packets do not carry runtime "
                "approval fields until a commit pipeline exists."
            )
        validate_full_guard_bundle_evidence(guard_bundle_evidence, required=True)
        return

    if action in PIPELINE_ACTION_REQUEST_ACTIONS:
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
        return

    if runtime_approval.has_values() or guard_bundle_evidence.has_values():
        raise ValueError(
            "Runtime guard fields are only allowed on commit/push "
            "action_request packets, stage-commit action_request packets, or "
            "`commit_approval` packets."
        )


__all__ = [
    "ANCHOR_REF_RE",
    "RUNTIME_ACTION_REQUEST_ACTIONS",
    "VALID_PLAN_MUTATION_OPS",
    "VALID_TARGET_KINDS",
    "validate_target_fields",
]
