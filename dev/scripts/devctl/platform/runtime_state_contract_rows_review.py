"""Review-channel runtime-state contract rows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .contracts import ContractField, ContractSpec
from .runtime_state_contract_rows_actor_authority import ACTOR_AUTHORITY_CONTRACTS
from .runtime_state_contract_rows_packet_debt import PACKET_DEBT_CONTRACTS
from .runtime_state_contract_rows_review_core import REVIEW_CORE_STATE_CONTRACTS
from .runtime_state_contract_rows_session_continuation import (
    AGENT_SESSION_CONTINUATION_CONTRACTS,
)

if TYPE_CHECKING:
    from ..runtime.peer_awareness_policy import (
        PeerAwarenessDecision,
        PeerAwarenessPolicy,
    )
    from ..runtime.session_termination_policy import (
        SessionTerminationPolicy,
        TaskCompleteDecision,
    )

    _RUNTIME_MODEL_REFS: tuple[
        type[PeerAwarenessPolicy],
        type[PeerAwarenessDecision],
        type[SessionTerminationPolicy],
        type[TaskCompleteDecision],
    ]

REVIEW_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    *ACTOR_AUTHORITY_CONTRACTS,
    *PACKET_DEBT_CONTRACTS,
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
        contract_id="AgentSessionOutcome",
        owner_layer="governance_runtime",
        purpose=(
            "Typed receipt for an agent-owned session end state, separating "
            "completed handoff from process death or unresolved liveness."
        ),
        required_fields=(
            ContractField("outcome", "str", "completed_handoff, process_died, or unresolved."),
            ContractField(
                "reason",
                "str",
                "Machine-readable reason for the recorded session outcome.",
            ),
            ContractField("provider", "str", "Provider or agent family that owns the session."),
            ContractField(
                "session_actor_id",
                "str",
                "Portable actor identifier for the session owner.",
            ),
            ContractField(
                "session_actor_role",
                "str",
                "Runtime role carried by session metadata.",
            ),
            ContractField("session_id", "str", "Review-channel session id for the outcome."),
            ContractField("session_name", "str", "Repo-owned conductor session name."),
            ContractField("observed_at_utc", "str", "UTC timestamp when the outcome was observed."),
            ContractField("finished_at_utc", "str", "UTC timestamp bound to session completion."),
            ContractField("source", "str", "Typed source that emitted the outcome receipt."),
            ContractField(
                "source_event_id",
                "str",
                "Event id of the lifecycle event that emitted this outcome.",
            ),
            ContractField(
                "handoff_packet_id",
                "str",
                "Review packet id when the outcome comes from a handoff packet.",
            ),
            ContractField(
                "handoff_requested_action",
                "str",
                "Requested action carried by the packet-backed handoff.",
            ),
            ContractField(
                "target_kind",
                "str",
                "Target kind copied from the packet-backed handoff scope.",
            ),
            ContractField(
                "target_ref",
                "str",
                "Target reference copied from the packet-backed handoff scope.",
            ),
            ContractField(
                "target_revision",
                "str",
                (
                    "Target revision copied from the packet-backed handoff scope; "
                    "metadata-free completed handoffs may be trusted by governed "
                    "push only when this matches the current devctl_commit head "
                    "or managed-receipt source chain."
                ),
            ),
            ContractField(
                "metadata_path",
                "str",
                "Provider session metadata path used to bind current-session state.",
            ),
            ContractField(
                "log_path",
                "str",
                "Provider session log path when known.",
            ),
            ContractField(
                "workspace_root",
                "str",
                "Workspace root recorded by the provider session metadata.",
            ),
            ContractField(
                "prepared_at_utc",
                "str",
                "Prepared-launch timestamp used for current-session validation.",
            ),
            ContractField(
                "prepared_session_token",
                "str",
                "Prepared-launch token used to bind the outcome to current session metadata.",
            ),
            ContractField(
                "prepared_head_sha",
                "str",
                "Prepared-launch HEAD SHA used for current-session validation.",
            ),
            ContractField(
                "prepared_instruction_revision",
                "str",
                "Prepared-launch instruction revision used for current-session validation.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.agent_session_outcome:"
            "AgentSessionOutcomeState"
        ),
        startup_surface_tokens=("outcome", "provider", "session_name"),
    ),
    ContractSpec(
        contract_id="PeerAwarenessPolicy",
        owner_layer="governance_runtime",
        purpose=(
            "Typed peer-poll cadence policy for agent work classes, including "
            "the agent-message and subprocess-heartbeat boundaries that require "
            "review-channel inbox and peer agent-mind observation."
        ),
        required_fields=(
            ContractField("role", "str", "Runtime role covered by the policy."),
            ContractField(
                "work_class",
                "str",
                "Work class such as interactive_turn or long_running_subprocess.",
            ),
            ContractField(
                "peer_provider",
                "str",
                "Peer provider expected for cross-mind polling.",
            ),
            ContractField(
                "cadence_seconds",
                "int",
                "Maximum age of peer-poll evidence before a boundary is due.",
            ),
            ContractField(
                "boundary_events",
                "tuple[str, ...]",
                "Boundary events where the policy is evaluated.",
            ),
            ContractField(
                "required_observations",
                "tuple[str, ...]",
                "Observation families required by the policy.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.peer_awareness_policy:"
            "PeerAwarenessPolicy"
        ),
        startup_surface_tokens=("role", "work_class", "cadence_seconds"),
    ),
    ContractSpec(
        contract_id="PeerAwarenessDecision",
        owner_layer="governance_runtime",
        purpose=(
            "Typed agent-message boundary decision that either opens an "
            "unobserved packet body, polls peer state, or allows current work "
            "to continue."
        ),
        required_fields=(
            ContractField(
                "action",
                "str",
                (
                    "Boundary action: open_packet_body, poll_peer_state, "
                    "or continue_current_work."
                ),
            ),
            ContractField("reason", "str", "Machine-readable reason for the decision."),
            ContractField("boundary", "str", "Boundary that produced the decision."),
            ContractField("peer_provider", "str", "Peer provider selected for polling."),
            ContractField(
                "cadence_seconds",
                "int",
                "Policy cadence applied to this decision.",
            ),
            ContractField("poll_due", "bool", "Whether peer-poll commands must run now."),
            ContractField(
                "body_open_required",
                "bool",
                "Whether packet body observation takes priority.",
            ),
            ContractField(
                "blocking_packet_id",
                "str",
                "Packet id that must be opened before continuing.",
            ),
            ContractField(
                "next_commands",
                "tuple[str, ...]",
                "Bounded repo-owned commands for the next action.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.peer_awareness_policy:"
            "PeerAwarenessDecision"
        ),
        startup_surface_tokens=("action", "reason", "blocking_packet_id"),
    ),
    ContractSpec(
        contract_id="SessionTerminationPolicy",
        owner_layer="governance_runtime",
        purpose=(
            "Typed policy for whether an agent session stops on TASK_COMPLETE "
            "or continues while a bounded continuation anchor packet remains live."
        ),
        required_fields=(
            ContractField(
                "mode",
                "str",
                (
                    "end_on_task_complete, keep_awake_via_packets, or "
                    "session_end_when_anchor_drained."
                ),
            ),
            ContractField("set_by", "str", "Actor that selected the policy."),
            ContractField("set_at_utc", "str", "UTC timestamp when the policy was set."),
            ContractField(
                "anchor_packet_id",
                "str",
                "Optional continuation_anchor packet id that bounds keep-awake mode.",
            ),
            ContractField(
                "target_session_id",
                "str",
                "Exact provider/runtime session id scoped by the policy.",
            ),
            ContractField(
                "expires_at_utc",
                "str",
                "UTC expiry after which the policy falls back to normal termination.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.session_termination_policy:"
            "SessionTerminationPolicy"
        ),
        startup_surface_tokens=("mode", "anchor_packet_id", "target_session_id"),
    ),
    ContractSpec(
        contract_id="TaskCompleteDecision",
        owner_layer="governance_runtime",
        purpose=(
            "Typed TASK_COMPLETE boundary decision, including the continuation "
            "anchor and next command when the session should keep running."
        ),
        required_fields=(
            ContractField(
                "terminate",
                "bool",
                "Whether the TASK_COMPLETE event should terminate the session.",
            ),
            ContractField(
                "reason",
                "str",
                "Machine-readable reason for terminate/continue.",
            ),
            ContractField(
                "policy_mode",
                "str",
                "SessionTerminationPolicy mode used for the decision.",
            ),
            ContractField(
                "anchor_packet_id",
                "str",
                "Active continuation_anchor packet that kept the session alive.",
            ),
            ContractField(
                "blocking_packet_id",
                "str",
                "Blocking packet id when TASK_COMPLETE must wait for review work.",
            ),
            ContractField(
                "target_session_id",
                "str",
                "Session id scoped by the decision.",
            ),
            ContractField(
                "next_command",
                "str",
                "Bounded repo-owned command to run when terminate=false.",
            ),
            ContractField(
                "error_kind",
                "str",
                "Bounded error classification when keep-awake prerequisites are missing.",
            ),
            ContractField(
                "pending_packet_count",
                "int",
                "Number of scoped packets still preventing terminal completion.",
            ),
            ContractField(
                "wake_required",
                "bool",
                "Internal loop-control flag indicating the agent must remain active.",
            ),
            ContractField(
                "pivot_required",
                "bool",
                "Internal loop-control flag indicating the next action must change focus.",
            ),
            ContractField(
                "correlation_id",
                "str",
                "Parent lineage shared with the packet, attention row, or session decision.",
            ),
            ContractField(
                "causation_id",
                "str",
                "Immediate trigger lineage that caused this decision.",
            ),
            ContractField(
                "run_id",
                "str",
                "Session or orchestration run lineage for this decision.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.session_termination_policy:"
            "TaskCompleteDecision"
        ),
        startup_surface_tokens=("terminate", "reason", "correlation_id"),
    ),
    *AGENT_SESSION_CONTINUATION_CONTRACTS,
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
