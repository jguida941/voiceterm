"""Target-field validation for review-channel packet posts."""

from __future__ import annotations

import re

from ..runtime.anchor_scope import (
    ANCHOR_SCOPE_PLAN,
    ANCHOR_SCOPE_ROLE,
    ANCHOR_SCOPE_SESSION,
    SESSION_TERMINATION_ANCHOR_KINDS,
    VALID_ANCHOR_SCOPES,
)
from ..runtime.collaboration_packet_kinds import (
    TASK_PRODUCED_PACKET_KIND,
    TASK_PROGRESS_PACKET_KIND,
)
from .pending_packet_models import (
    PacketGuardBundleEvidenceFields,
    PacketRuntimeApprovalFields,
    validate_full_guard_bundle_evidence,
)
from .packet_target_runtime import (
    RUNTIME_ACTION_REQUEST_ACTIONS,
    STAGE_PIPELINE_ACTION_REQUEST_ACTIONS,
    validate_action_request_target_fields,
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
NON_AUTHORITATIVE_TARGET_PACKET_KINDS = {
    "finding",
    "automation_opportunity",
    TASK_PRODUCED_PACKET_KIND,
    TASK_PROGRESS_PACKET_KIND,
}
ANCHOR_REF_RE = re.compile(
    r"^(checklist|section|session_resume|progress|audit|packet):[A-Za-z0-9][A-Za-z0-9._-]*$"
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
    if target.anchor_scope and target.anchor_scope not in VALID_ANCHOR_SCOPES:
        raise ValueError(
            f"Unsupported review-channel anchor scope: {target.anchor_scope}"
        )

    if kind in SESSION_TERMINATION_ANCHOR_KINDS:
        _validate_session_termination_anchor_target_fields(
            kind=kind,
            target=target,
            runtime_approval=runtime_approval,
            guard_bundle_evidence=guard_bundle_evidence,
        )
        return

    if target.anchor_scope:
        raise ValueError("--anchor-scope is only valid on session termination anchors.")

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
        validate_action_request_target_fields(
            requested_action=requested_action,
            target=target,
            runtime_approval=runtime_approval,
            guard_bundle_evidence=guard_bundle_evidence,
            resource_target_values_present=_resource_target_values_present(target),
            validate_optional_plan_intent_fields=_validate_optional_plan_intent_fields,
        )
        return

    if kind in NON_AUTHORITATIVE_TARGET_PACKET_KINDS:
        _validate_non_authoritative_target_fields(
            kind=kind,
            target=target,
            runtime_approval=runtime_approval,
            guard_bundle_evidence=guard_bundle_evidence,
        )
        return

    if (
        _resource_target_values_present(target)
        or runtime_approval.has_values()
        or guard_bundle_evidence.has_values()
    ):
        raise ValueError(
            "Target fields are only allowed on plan review packets or "
            "`commit_approval` packets."
        )
    _validate_optional_plan_intent_fields(target)


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


def _validate_session_termination_anchor_target_fields(
    *,
    kind: str,
    target,
    runtime_approval: PacketRuntimeApprovalFields,
    guard_bundle_evidence: PacketGuardBundleEvidenceFields,
) -> None:
    if runtime_approval.has_values() or guard_bundle_evidence.has_values():
        raise ValueError(f"Runtime guard fields are not valid on `{kind}` packets.")
    if target.mutation_op:
        raise ValueError(f"Plan mutation fields are not valid on `{kind}` packets.")
    _validate_optional_plan_intent_fields(target)
    if kind == "stop_anchor" and not (
        target.anchor_scope
        or target.target_role
        or target.target_session_id
        or (target.target_kind == "plan" and target.target_ref)
    ):
        raise ValueError(
            "stop_anchor packets require typed scope: use --session-scoped, "
            "--target-role-scoped, or --plan-scoped with the matching target "
            "fields."
        )
    if not target.anchor_scope:
        return
    if target.anchor_scope == ANCHOR_SCOPE_SESSION:
        if not target.target_session_id:
            raise ValueError("--session-scoped anchors require --target-session-id.")
        return
    if target.anchor_scope == ANCHOR_SCOPE_ROLE:
        if not target.target_role:
            raise ValueError("--target-role-scoped anchors require --target-role.")
        return
    if target.anchor_scope == ANCHOR_SCOPE_PLAN:
        if target.target_kind != "plan" or not target.target_ref:
            raise ValueError(
                "--plan-scoped anchors require --target-kind plan and --target-ref."
            )


def _validate_non_authoritative_target_fields(
    *,
    kind: str,
    target,
    runtime_approval: PacketRuntimeApprovalFields,
    guard_bundle_evidence: PacketGuardBundleEvidenceFields,
) -> None:
    if runtime_approval.has_values() or guard_bundle_evidence.has_values():
        raise ValueError(
            f"Runtime guard fields are not valid on `{kind}` packets."
        )
    if target.mutation_op:
        raise ValueError(
            f"Plan mutation fields are not valid on `{kind}` packets."
        )
    _validate_optional_plan_intent_fields(target)


def _resource_target_values_present(target) -> bool:
    return any(
        (
            target.target_kind,
            target.target_ref,
            target.target_revision,
            target.mutation_op,
        )
    )


def _validate_optional_plan_intent_fields(target) -> None:
    invalid = [
        ref for ref in target.anchor_refs if ANCHOR_REF_RE.fullmatch(ref) is None
    ]
    if invalid:
        raise ValueError("Invalid --anchor-ref value(s): " + ", ".join(invalid))


__all__ = [
    "ANCHOR_REF_RE",
    "NON_AUTHORITATIVE_TARGET_PACKET_KINDS",
    "RUNTIME_ACTION_REQUEST_ACTIONS",
    "STAGE_PIPELINE_ACTION_REQUEST_ACTIONS",
    "VALID_PLAN_MUTATION_OPS",
    "VALID_TARGET_KINDS",
    "validate_target_fields",
]
