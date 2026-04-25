"""Remote commit/push pipeline runtime-state contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec


PIPELINE_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
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
)
