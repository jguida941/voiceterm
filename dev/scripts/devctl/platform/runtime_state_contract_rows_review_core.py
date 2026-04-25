"""Core review-state runtime contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec

REVIEW_CORE_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="ReviewState",
        owner_layer="governance_runtime",
        purpose=(
            "Machine-readable review-channel snapshot for session metadata, "
            "queue state, packets, bridge status, and agent registry."
        ),
        required_fields=(
            ContractField(
                "action", "str", "Review-channel action that produced the snapshot."
            ),
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
                "source_identity",
                "dict[str, str]",
                "Canonical provenance identity tuple including generation_id when present plus head_sha/worktree_hash.",
            ),
            ContractField(
                "source_contract",
                "str",
                "Canonical contract name for the authority payload that emitted this surface.",
            ),
            ContractField(
                "source_command",
                "str",
                "Canonical repo-owned command string that emitted this review-state surface.",
            ),
            ContractField(
                "observed_fields",
                "tuple[str, ...]",
                "Authority fields observed directly when projecting this review-state surface.",
            ),
            ContractField(
                "inferred_fields",
                "tuple[str, ...]",
                "Derived identity fields inferred from the canonical observed authority tuple.",
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
