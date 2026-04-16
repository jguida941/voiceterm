"""Review-channel runtime-state contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec


REVIEW_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
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
        contract_id="PushAuthorizationRecord",
        owner_layer="governance_runtime",
        purpose=(
            "Frozen publication proof for one reviewed commit, including the "
            "exact authorized HEAD, approved publish identity, and guard verdict."
        ),
        required_fields=(
            ContractField("authorization_id", "str", "Stable identifier for one persisted publication authorization."),
            ContractField("pipeline_id", "str", "Owning remote commit pipeline id."),
            ContractField("generation_id", "str", "Generation token bound to the approval and publish target."),
            ContractField("authorized_head_sha", "str", "Exact commit SHA authorized for publication."),
            ContractField("approved_target_identity", "str", "Exact approved publish identity carried into push."),
            ContractField("worktree_identity", "str", "Exact worktree identity authorized to publish the reviewed commit."),
            ContractField("review_verdict", "str", "Approval verdict that authorized publication."),
            ContractField("approval_mode", "str", "Authorization mode: commit_pipeline_approval or override_push."),
            ContractField("guard_action_id", "str", "Guard action id that covered the authorized commit."),
            ContractField("guard_status", "str", "Guard result status for the authorized commit."),
            ContractField("guard_reason", "str", "Guard result reason for the authorized commit."),
            ContractField("request_packet_id", "str", "Optional packet id for the request that led to this authorization."),
            ContractField("decision_packet_id", "str", "Applied packet id that granted publication authority."),
            ContractField("approved_by", "str", "Actor who approved the publication authority."),
            ContractField("approved_at_utc", "str", "UTC timestamp when publication authority was granted."),
            ContractField("expires_at_utc", "str", "UTC expiry for the authorization, if any."),
            ContractField("override_reason", "str", "Recorded rationale when publication authority came from an override."),
            ContractField("publication_owner", "str", "Agent lane that owns the publication workflow for this authorization."),
            ContractField("target_executor_lane", "str", "Executor lane authorized to run the push for this commit."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.remote_commit_pipeline_models:"
            "PushAuthorizationRecord"
        ),
        startup_surface_tokens=("authorization_id", "authorized_head_sha", "approval_mode"),
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
                "zref",
                "str",
                "Compact human-readable handle derived from snapshot_id and head_sha prefixes.",
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
                "push_authorization",
                "PushAuthorizationRecord | None",
                "Current publication receipt preferred over live reviewer-liveness inference when push is already authorized.",
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
                "coordination",
                "CoordinationSnapshot | None",
                "Shared bounded coordination authority mirrored into review-state projections for status, doctor, and dashboard parity.",
            ),
            ContractField(
                "authority_snapshot",
                "AuthoritySnapshot | None",
                "Reduced next-turn authority contract mirrored into review-state projections.",
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
                "packet_inbox",
                "PacketInboxState",
                "Canonical per-agent attention/wake contract derived from typed review packets.",
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
            ContractField(
                "remote_control_attachment",
                "RemoteControlAttachmentState | None",
                "Optional typed attachment for an external phone-steered remote-control session.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.review_state_models:ReviewerRuntimeContract",
        startup_surface_tokens=(
            "reviewer_mode",
            "reviewer_freshness",
            "publish_clear",
            "remote_control_attachment",
        ),
    ),
)
