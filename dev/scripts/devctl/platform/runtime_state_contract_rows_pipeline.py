"""Remote commit/push pipeline runtime-state contract rows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .contracts import ContractField, ContractSpec, CrossLinkSpec

if TYPE_CHECKING:
    from ..commands.vcs.push_result_typestate import (
        PushFailed,
        PushPartialProgress,
        PushSucceeded,
    )

    _TYPESTATE_RESULT_REFS: tuple[
        type[PushSucceeded],
        type[PushPartialProgress],
        type[PushFailed],
    ]


PIPELINE_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="CheckpointBudgetShape",
        owner_layer="governance_runtime",
        purpose=(
            "Startup checkpoint-budget classifier that separates raw scratch "
            "dirt from a governed checkpoint pipeline parked at the staged "
            "snapshot boundary."
        ),
        required_fields=(
            ContractField("state", "str", "Budget classifier state."),
            ContractField("reason", "str", "Checkpoint pressure reason."),
            ContractField(
                "checkpoint_required",
                "bool",
                "Whether ProjectGovernance says a checkpoint is required.",
            ),
            ContractField(
                "safe_to_continue_editing",
                "bool",
                "Whether more implementation editing is safe before checkpoint.",
            ),
            ContractField(
                "staged_path_count",
                "int",
                "Staged path count from ProjectGovernance push enforcement.",
            ),
            ContractField(
                "unstaged_path_count",
                "int",
                "Unstaged path count from ProjectGovernance push enforcement.",
            ),
            ContractField(
                "dirty_path_count",
                "int",
                "Dirty path count from ProjectGovernance push enforcement.",
            ),
            ContractField(
                "untracked_path_count",
                "int",
                "Untracked path count from ProjectGovernance push enforcement.",
            ),
            ContractField(
                "pipeline_id",
                "str",
                "RemoteCommitPipelineContract id when typed pipeline evidence exists.",
            ),
            ContractField(
                "pipeline_state",
                "str",
                "Remote commit pipeline lifecycle state.",
            ),
            ContractField(
                "pipeline_staged_path_count",
                "int",
                "Staged path count captured by the pipeline intent.",
            ),
            ContractField(
                "staged_tree_hash",
                "str",
                "Pipeline staged tree hash used as repo-state fingerprint.",
            ),
            ContractField(
                "current_tree_hash",
                "str",
                "Current git index tree hash read during classification.",
            ),
            ContractField(
                "tree_hash_match",
                "bool",
                "Whether current_tree_hash matches staged_tree_hash.",
            ),
            ContractField(
                "typed_pipeline_parked",
                "bool",
                "Whether the pipeline state is parked at the checkpoint boundary.",
            ),
            ContractField(
                "receipt_backed",
                "bool",
                "Whether guard or validation receipt evidence is present.",
            ),
            ContractField(
                "guard_action_id",
                "str",
                "Guard ActionResult id when guard receipt evidence exists.",
            ),
            ContractField(
                "guard_status",
                "str",
                "Guard ActionResult status when guard receipt evidence exists.",
            ),
            ContractField(
                "guard_ok",
                "bool",
                "Whether the guard ActionResult reports ok.",
            ),
            ContractField(
                "validation_receipt_id",
                "str",
                "ValidationReceipt id when validation evidence exists.",
            ),
            ContractField(
                "validation_receipt_status",
                "str",
                "ValidationReceipt status when validation evidence exists.",
            ),
            ContractField(
                "validation_checkpoint_sufficient",
                "bool",
                "Whether validation receipt proves checkpoint sufficiency.",
            ),
            ContractField(
                "bootstrap_blocked",
                "bool",
                "Whether startup authority must still block bootstrap work.",
            ),
            ContractField(
                "next_required_action",
                "str",
                "Next governed action implied by the classifier.",
            ),
            ContractField(
                "blocked_raw_actions",
                "tuple[str, ...]",
                "Raw actions still blocked by the classifier.",
            ),
            ContractField(
                "errors",
                "tuple[str, ...]",
                "Fail-closed evidence errors when bootstrap is blocked.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.checkpoint_budget_shape:"
            "CheckpointBudgetShape"
        ),
        startup_surface_tokens=(
            "state",
            "bootstrap_blocked",
            "next_required_action",
        ),
        cross_links=(
            CrossLinkSpec(
                "pipeline_id",
                "RemoteCommitPipelineContract",
                "classifies_pipeline",
                target_node_kind="remote_commit_pipeline",
                target_resolver="pipeline_id",
                required=False,
            ),
        ),
    ),
    ContractSpec(
        contract_id="RemoteCommitPipelineContract",
        owner_layer="governance_runtime",
        purpose=(
            "Typed owner for remote-session staged-work, approval, commit, "
            "push, and recovery lifecycle truth."
        ),
        required_fields=(
            ContractField("pipeline_id", "str", "Stable pipeline identity."),
            ContractField(
                "snapshot_id",
                "str",
                "Shared surface-generation stamp for the current pipeline projection.",
            ),
            ContractField(
                "zref",
                "str",
                "Compact human-readable handle derived from snapshot_id and head_sha prefixes.",
            ),
            ContractField(
                "state",
                "str",
                "Current pipeline lifecycle state.",
            ),
            ContractField(
                "requested_by",
                "str",
                "Actor that requested the current pipeline.",
            ),
            ContractField("branch", "str", "Branch that owns the staged work."),
            ContractField("remote", "str", "Target remote for governed publish."),
            ContractField(
                "intent",
                "CommitIntentState",
                "Immutable staged-work snapshot consumed by guard/approval/commit.",
            ),
            ContractField(
                "guard_action_id",
                "str",
                "Typed guard action id linked to the current intent.",
            ),
            ContractField(
                "guard_result",
                "ActionResult | None",
                "Guard bundle receipt for the current staged intent.",
            ),
            ContractField(
                "validation_receipt",
                "ValidationReceipt | None",
                "Typed validation proof bound to the staged intent and emitted from the routed guard bundle.",
            ),
            ContractField(
                "reviewer_runtime_generation",
                "str",
                "Reviewer-runtime generation bound to the current request.",
            ),
            ContractField(
                "approval_packet_id",
                "str",
                "Approval-request packet id for the current generation.",
            ),
            ContractField(
                "decision_packet_id",
                "str",
                "Operator decision packet id for the current generation.",
            ),
            ContractField(
                "approval_state",
                "str",
                "Approval state for the current generation-bound request.",
            ),
            ContractField(
                "commit_action_id",
                "str",
                "Typed commit action id for the current pipeline.",
            ),
            ContractField(
                "commit_result",
                "ActionResult | None",
                "Commit action receipt when a governed commit has run.",
            ),
            ContractField(
                "commit_sha",
                "str",
                "Recorded commit SHA once the governed commit exists.",
            ),
            ContractField(
                "push_action_id",
                "str",
                "Typed push action id for the current pipeline.",
            ),
            ContractField(
                "push_result",
                "ActionResult | None",
                "Push action receipt when the governed publish path has run.",
            ),
            ContractField(
                "push_pipeline_phases",
                "Mapping[str, object]",
                "Typed push phase boundary state for managed projection sync and post-validation repair.",
            ),
            ContractField(
                "push_failure_transition",
                "Mapping[str, object]",
                "Typed push failure classification and state-transition evidence for automatic local-delivery movement.",
            ),
            ContractField(
                "checkpoint_repair_authority",
                "Mapping[str, object]",
                "CheckpointRepairAuthority proof promoted from a repaired staged checkpoint pipeline.",
            ),
            ContractField(
                "push_report_path",
                "str",
                "Artifact path for the current governed push report.",
            ),
            ContractField(
                "blocked_reason",
                "str",
                "Fail-closed reason when the pipeline cannot advance.",
            ),
            ContractField(
                "recovery_action_allowed",
                "str",
                "Repo-owned recovery action currently allowed for the pipeline.",
            ),
            ContractField(
                "generation_id",
                "str",
                "Generation token that binds staged hash, approval, and execution.",
            ),
            ContractField(
                "approval_expires_at_utc",
                "str",
                "UTC expiry for the current operator approval, if any.",
            ),
            ContractField(
                "approved_target_identity",
                "str",
                "Exact approved staged target identity bound to the approval generation.",
            ),
            ContractField(
                "worktree_identity",
                "str",
                "Exact worktree identity that staged and owns the current pipeline.",
            ),
            ContractField(
                "attention_revision_lease",
                "str",
                "Bounded attention-revision lease held while one governed commit is executing.",
            ),
            ContractField(
                "push_authorization",
                "PushAuthorizationRecord | None",
                "Frozen publication proof for the current governed commit, when one exists.",
            ),
            ContractField(
                "local_delivery_receipt_path",
                "str",
                "Receipt proving the commit was delivered locally while publication remains pending.",
            ),
            ContractField(
                "local_delivery_reason",
                "str",
                "Operator or auto-recovery rationale for marking local delivery.",
            ),
            ContractField(
                "delivered_at_utc",
                "str",
                "UTC timestamp when the pipeline left the active slot as locally delivered.",
            ),
            ContractField(
                "delivered_by",
                "str",
                "Actor that recorded local-delivery terminal state.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.remote_commit_pipeline_models:"
            "RemoteCommitPipelineContract"
        ),
        startup_surface_tokens=(
            "snapshot_id",
            "state",
            "approval_state",
            "blocked_reason",
        ),
    ),
    ContractSpec(
        contract_id="CheckpointRepairAuthority",
        owner_layer="governance_runtime",
        purpose=(
            "Receipt-bound lifecycle promotion that converts a prior checkpoint "
            "guard failure plus fresh matching validation proof into authority "
            "for the governed checkpoint commit path."
        ),
        required_fields=(
            ContractField("pipeline_id", "str", "RemoteCommitPipelineContract id."),
            ContractField(
                "generation_id",
                "str",
                "Pipeline generation that owns the repaired guard proof.",
            ),
            ContractField(
                "original_block_reason",
                "str",
                "Original checkpoint blocker, such as guard_bundle_failed.",
            ),
            ContractField("result", "str", "Repair classification result."),
            ContractField(
                "next_authorized_action",
                "str",
                "Next typed lifecycle action authorized by the receipt.",
            ),
            ContractField(
                "source_action_id",
                "str",
                "ActionResult id for the passing guard bundle.",
            ),
            ContractField(
                "validation_receipt_id",
                "str",
                "ValidationReceipt id bound to the staged tree hash.",
            ),
            ContractField(
                "staged_tree_hash",
                "str",
                "Staged tree hash that the repair proof validates.",
            ),
            ContractField(
                "selected_paths",
                "tuple[str, ...]",
                "Paths included in the repaired checkpoint intent.",
            ),
            ContractField(
                "checkpoint_sufficient",
                "bool",
                "Whether validation proves the repaired checkpoint is sufficient.",
            ),
            ContractField(
                "blocked_raw_actions",
                "tuple[str, ...]",
                "Raw actions still blocked; authority remains governed only.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.checkpoint_repair_authority:"
            "CheckpointRepairAuthority"
        ),
        startup_surface_tokens=(
            "original_block_reason",
            "result",
            "next_authorized_action",
        ),
        cross_links=(
            CrossLinkSpec(
                "pipeline_id",
                "RemoteCommitPipelineContract",
                "promotes_pipeline",
                target_node_kind="remote_commit_pipeline",
                target_resolver="pipeline_id",
                required=True,
            ),
            CrossLinkSpec(
                "source_action_id",
                "ActionResult",
                "proved_by",
                target_node_kind="action_result",
                target_resolver="action_id",
                required=True,
            ),
            CrossLinkSpec(
                "validation_receipt_id",
                "ValidationReceipt",
                "proved_by",
                target_node_kind="validation_receipt",
                target_resolver="receipt_id",
                required=True,
            ),
        ),
    ),
)
