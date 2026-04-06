"""State runtime contract rows for the platform blueprint."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec


RUNTIME_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="CheckResult",
        owner_layer="governance_runtime",
        purpose="Typed check-output envelope carrying step results, enriched status, and ViolationRecords for renderers and downstream consumers.",
        required_fields=(
            ContractField("timestamp", "str", "UTC timestamp for the run."),
            ContractField("success", "bool", "Whether all steps passed."),
            ContractField("total", "int", "Total step count."),
            ContractField("passed", "int", "Passed step count."),
            ContractField("failed", "int", "Failed step count."),
            ContractField("skipped", "int", "Skipped step count."),
            ContractField("steps", "tuple[dict, ...]", "Enriched step dicts with status and violation_summary."),
            ContractField("violations", "tuple[ViolationRecord, ...]", "Typed violation records from failed steps."),
        ),
        runtime_model="dev.scripts.devctl.runtime.check_result_models:CheckResult",
        startup_surface_tokens=("success", "total", "failed"),
    ),
    ContractSpec(
        contract_id="ControlState",
        owner_layer="governance_runtime",
        purpose=(
            "Machine-readable status snapshot for runs, queue state, "
            "approvals, warnings, and errors across clients."
        ),
        required_fields=(
            ContractField("timestamp", "str", "UTC timestamp for the snapshot."),
            ContractField(
                "approvals",
                "ApprovalPolicyState",
                "Approval/waiver state projected into every frontend.",
            ),
            ContractField(
                "active_runs",
                "tuple[ActiveRunState, ...]",
                "Current governed runs visible to CLI/UI clients.",
            ),
            ContractField(
                "review_bridge",
                "ReviewBridgeState",
                "Shared review-channel liveness and heartbeat state.",
            ),
            ContractField(
                "agents",
                "tuple[ReviewAgentState, ...]",
                "Visible review/loop agents participating in the control plane.",
            ),
            ContractField(
                "sources",
                "ControlStateSources",
                "Bounded source paths used to derive the control snapshot.",
            ),
            ContractField(
                "operator_context",
                "OperatorContext",
                "Typed operator-presence metadata for mode-aware governance decisions.",
            ),
            ContractField(
                "warnings",
                "tuple[str, ...]",
                "Non-blocking warnings carried with the control snapshot.",
            ),
            ContractField(
                "errors",
                "tuple[str, ...]",
                "Blocking errors carried with the control snapshot.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.control_state:ControlState",
        startup_surface_tokens=("approvals", "active_runs", "review_bridge"),
    ),
    ContractSpec(
        contract_id="ReviewCandidateRecord",
        owner_layer="governance_runtime",
        purpose=(
            "Frozen reviewer handoff target for dirty-tree or commit-range slices, "
            "including changed paths, worktree hash, and candidate validity."
        ),
        required_fields=(
            ContractField("candidate_id", "str", "Stable identifier for one frozen review target."),
            ContractField("instruction_revision", "str", "Instruction revision the candidate was produced against."),
            ContractField("artifact_kind", "str", "Candidate source kind: dirty_tree or commit_range."),
            ContractField("base_sha", "str", "Reviewer baseline SHA when one exists."),
            ContractField("head_sha", "str", "Current HEAD SHA at candidate emission."),
            ContractField("worktree_hash", "str", "Non-audit worktree hash for dirty-tree review."),
            ContractField("changed_paths", "tuple[str, ...]", "Frozen changed-path set the reviewer must inspect."),
            ContractField("tests_run", "tuple[str, ...]", "Test commands the implementer reported for the slice."),
            ContractField("guards_run", "tuple[str, ...]", "Guard/check commands the implementer reported for the slice."),
            ContractField("implementer_status_written", "bool", "Whether Claude published substantive status for the slice."),
            ContractField("ready_for_review", "bool", "Whether the candidate is currently ready for reviewer inspection."),
            ContractField("valid", "bool", "Whether the candidate remains valid under current runtime truth."),
            ContractField("invalidation_reason", "str", "Reason the frozen candidate is no longer valid."),
            ContractField("implementer_state_hash", "str", "Implementer state hash bound to the candidate."),
            ContractField("emitted_at_utc", "str", "UTC timestamp when the candidate was emitted."),
            ContractField("scope_paths", "tuple[str, ...]", "Scoped instruction paths expected in the candidate target."),
            ContractField("missing_scope_paths", "tuple[str, ...]", "Scoped instruction paths missing from the candidate target."),
        ),
        runtime_model="dev.scripts.devctl.runtime.review_state_models:ReviewCandidateRecord",
        startup_surface_tokens=("candidate_id", "artifact_kind", "valid"),
    ),
    ContractSpec(
        contract_id="ReviewState",
        owner_layer="governance_runtime",
        purpose=(
            "Machine-readable review-channel snapshot for session metadata, "
            "queue state, packets, bridge status, and agent registry."
        ),
        required_fields=(
            ContractField("action", "str", "Review-channel action that produced the snapshot."),
            ContractField("timestamp", "str", "UTC timestamp for the snapshot."),
            ContractField(
                "snapshot_id",
                "str",
                "Shared surface-generation stamp carried across startup, doctor, bridge projection, and commit pipeline surfaces.",
            ),
            ContractField(
                "ok",
                "bool",
                "Whether the review snapshot resolved without blocking errors.",
            ),
            ContractField(
                "review",
                "ReviewSessionState",
                "Typed review session metadata shared by CLI/UI clients.",
            ),
            ContractField(
                "queue",
                "ReviewQueueState",
                "Pending packet counts and derived next-instruction state.",
            ),
            ContractField(
                "current_session",
                "ReviewCurrentSessionState",
                "Typed current instruction and implementer ACK state used by current-status readers.",
            ),
            ContractField(
                "collaboration",
                "CollaborationSessionState",
                "Typed collaboration/session contract separating live participants from delegated planned work.",
            ),
            ContractField(
                "bridge",
                "ReviewBridgeState",
                "Review bridge lifecycle and freshness state.",
            ),
            ContractField(
                "review_candidate",
                "ReviewCandidateRecord | None",
                "Frozen current review target preferred over raw HEAD diff inference.",
            ),
            ContractField(
                "reviewer_runtime",
                "ReviewerRuntimeContract",
                "Typed reviewer lifecycle owner projected from review-channel state.",
            ),
            ContractField(
                "commit_pipeline",
                "RemoteCommitPipelineContract",
                "Typed remote commit/push lifecycle owner mirrored into review-state projections.",
            ),
            ContractField(
                "attention",
                "ReviewAttentionState | None",
                "Current top-priority attention state, if any.",
            ),
            ContractField(
                "recovery_assessment",
                "RecoveryAssessmentState | None",
                "Canonical typed diagnosis/decision pair that explanatory review surfaces project instead of recomputing local recovery prose.",
            ),
            ContractField(
                "packets",
                "tuple[ReviewPacketState, ...]",
                "Typed review-channel packets, including approval state.",
            ),
            ContractField(
                "registry",
                "AgentRegistryState",
                "Current agent-registry snapshot for the review surface.",
            ),
            ContractField(
                "warnings",
                "tuple[str, ...]",
                "Non-blocking warnings carried with the review snapshot.",
            ),
            ContractField(
                "errors",
                "tuple[str, ...]",
                "Blocking errors carried with the review snapshot.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.review_state_models:ReviewState",
        startup_surface_tokens=(
            "snapshot_id",
            "bridge",
            "current_session",
            "reviewer_runtime",
            "commit_pipeline",
        ),
    ),
    ContractSpec(
        contract_id="ReviewerRuntimeContract",
        owner_layer="governance_runtime",
        purpose=(
            "Typed owner for reviewer lifecycle truth, including freshness, "
            "rollover state, session ownership, recovery allowance, and "
            "publish-clear review acceptance."
        ),
        required_fields=(
            ContractField("reviewer_mode", "str", "Declared reviewer mode."),
            ContractField(
                "effective_reviewer_mode",
                "str",
                "Live reviewer mode after launch/runtime truth demotion.",
            ),
            ContractField(
                "reviewer_freshness",
                "str",
                "Reviewer heartbeat freshness classification.",
            ),
            ContractField(
                "stale_reason",
                "str",
                "Attention-state reason when the lifecycle is not healthy.",
            ),
            ContractField(
                "conductor_visibility",
                "str",
                "Typed visibility classification for the current repo-owned conductor sessions.",
            ),
            ContractField(
                "implementer_ack_current",
                "bool",
                "Whether the current implementer ACK matches the live instruction revision.",
            ),
            ContractField(
                "implementation_blocked",
                "bool",
                "Whether new implementation work is fail-closed by reviewer-runtime truth.",
            ),
            ContractField(
                "implementation_block_reason",
                "str",
                "Reason the current reviewer-runtime state blocks new implementation work.",
            ),
            ContractField(
                "last_poll",
                "ReviewerLastPollState",
                "Last reviewer poll timestamp plus computed age.",
            ),
            ContractField(
                "rollover",
                "ReviewerRolloverState",
                "Current rollover id, ACK state, and trigger.",
            ),
            ContractField(
                "session_owner",
                "ReviewerSessionOwnerState",
                "Repo-owned reviewer session ownership and terminal identity.",
            ),
            ContractField(
                "recovery_action_allowed",
                "str",
                "Current recovery command allowed by peer-recovery dispatch.",
            ),
            ContractField(
                "review_acceptance",
                "ReviewerAcceptanceState",
                "Reviewer verdict/findings projection plus acceptance boolean.",
            ),
            ContractField(
                "publish_clear",
                "bool",
                "Whether reviewer lifecycle state is fully green for push/review gates.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.review_state_models:ReviewerRuntimeContract",
        startup_surface_tokens=(
            "reviewer_mode",
            "reviewer_freshness",
            "publish_clear",
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
