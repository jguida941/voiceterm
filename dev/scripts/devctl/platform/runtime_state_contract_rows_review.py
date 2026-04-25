"""Review-channel runtime-state contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec
from .runtime_state_contract_rows_actor_authority import ACTOR_AUTHORITY_CONTRACTS
from .runtime_state_contract_rows_review_core import REVIEW_CORE_STATE_CONTRACTS

REVIEW_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    *ACTOR_AUTHORITY_CONTRACTS,
    ContractSpec(
        contract_id="ReviewCandidateRecord",
        owner_layer="governance_runtime",
        purpose=(
            "Frozen reviewer handoff target for dirty-tree or commit-range slices, "
            "including changed paths, worktree hash, and candidate validity."
        ),
        required_fields=(
            ContractField(
                "candidate_id", "str", "Stable identifier for one frozen review target."
            ),
            ContractField(
                "instruction_revision",
                "str",
                "Instruction revision the candidate was produced against.",
            ),
            ContractField(
                "artifact_kind",
                "str",
                "Candidate source kind: dirty_tree or commit_range.",
            ),
            ContractField("base_sha", "str", "Reviewer baseline SHA when one exists."),
            ContractField("head_sha", "str", "Current HEAD SHA at candidate emission."),
            ContractField(
                "worktree_hash", "str", "Non-audit worktree hash for dirty-tree review."
            ),
            ContractField(
                "changed_paths",
                "tuple[str, ...]",
                "Frozen changed-path set the reviewer must inspect.",
            ),
            ContractField(
                "tests_run",
                "tuple[str, ...]",
                "Test commands the implementer reported for the slice.",
            ),
            ContractField(
                "guards_run",
                "tuple[str, ...]",
                "Guard/check commands the implementer reported for the slice.",
            ),
            ContractField(
                "implementer_status_written",
                "bool",
                "Whether Claude published substantive status for the slice.",
            ),
            ContractField(
                "ready_for_review",
                "bool",
                "Whether the candidate is currently ready for reviewer inspection.",
            ),
            ContractField(
                "valid",
                "bool",
                "Whether the candidate remains valid under current runtime truth.",
            ),
            ContractField(
                "invalidation_reason",
                "str",
                "Reason the frozen candidate is no longer valid.",
            ),
            ContractField(
                "implementer_state_hash",
                "str",
                "Implementer state hash bound to the candidate.",
            ),
            ContractField(
                "emitted_at_utc", "str", "UTC timestamp when the candidate was emitted."
            ),
            ContractField(
                "scope_paths",
                "tuple[str, ...]",
                "Scoped instruction paths expected in the candidate target.",
            ),
            ContractField(
                "missing_scope_paths",
                "tuple[str, ...]",
                "Scoped instruction paths missing from the candidate target.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.review_state_models:ReviewCandidateRecord",
        startup_surface_tokens=("candidate_id", "artifact_kind", "valid"),
    ),
    ContractSpec(
        contract_id="PushAuthorizationRecord",
        owner_layer="governance_runtime",
        purpose=(
            "Frozen publication proof for one reviewed commit, including the "
            "exact authorized HEAD, approved publish identity, and guard verdict."
        ),
        required_fields=(
            ContractField(
                "authorization_id",
                "str",
                "Stable identifier for one persisted publication authorization.",
            ),
            ContractField("pipeline_id", "str", "Owning remote commit pipeline id."),
            ContractField(
                "generation_id",
                "str",
                "Generation token bound to the approval and publish target.",
            ),
            ContractField(
                "authorized_head_sha",
                "str",
                "Exact commit SHA authorized for publication.",
            ),
            ContractField(
                "approved_target_identity",
                "str",
                "Exact approved publish identity carried into push.",
            ),
            ContractField(
                "worktree_identity",
                "str",
                "Exact worktree identity authorized to publish the reviewed commit.",
            ),
            ContractField(
                "review_verdict", "str", "Approval verdict that authorized publication."
            ),
            ContractField(
                "approval_mode",
                "str",
                "Authorization mode: commit_pipeline_approval or override_push.",
            ),
            ContractField(
                "guard_action_id",
                "str",
                "Guard action id that covered the authorized commit.",
            ),
            ContractField(
                "guard_status", "str", "Guard result status for the authorized commit."
            ),
            ContractField(
                "guard_reason", "str", "Guard result reason for the authorized commit."
            ),
            ContractField(
                "request_packet_id",
                "str",
                "Optional packet id for the request that led to this authorization.",
            ),
            ContractField(
                "decision_packet_id",
                "str",
                "Applied packet id that granted publication authority.",
            ),
            ContractField(
                "approved_by", "str", "Actor who approved the publication authority."
            ),
            ContractField(
                "approved_at_utc",
                "str",
                "UTC timestamp when publication authority was granted.",
            ),
            ContractField(
                "expires_at_utc", "str", "UTC expiry for the authorization, if any."
            ),
            ContractField(
                "override_reason",
                "str",
                "Recorded rationale when publication authority came from an override.",
            ),
            ContractField(
                "publication_owner",
                "str",
                "Agent lane that owns the publication workflow for this authorization.",
            ),
            ContractField(
                "target_executor_lane",
                "str",
                "Executor lane authorized to run the push for this commit.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.remote_commit_pipeline_models:"
            "PushAuthorizationRecord"
        ),
        startup_surface_tokens=(
            "authorization_id",
            "authorized_head_sha",
            "approval_mode",
        ),
    ),
    *REVIEW_CORE_STATE_CONTRACTS,
)
