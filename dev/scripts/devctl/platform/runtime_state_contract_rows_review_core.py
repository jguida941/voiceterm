"""Core review-state runtime contract rows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .contracts import ContractField, ContractSpec
from .runtime_state_contract_rows_remote_control import REMOTE_CONTROL_STATE_CONTRACTS

if TYPE_CHECKING:
    from ..runtime.packet_intent_anchor import PlanIterationSession
    from ..runtime.session_posture import SessionPostureActor
    from ..runtime.startup_context_models import ReviewerGateState, StartupContext

    _RUNTIME_MODEL_REFS: tuple[
        type[PlanIterationSession],
        type[SessionPostureActor],
        type[ReviewerGateState],
        type[StartupContext],
    ]

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
                "agent_sync",
                "dict[str, object]",
                (
                    "Typed AgentSyncProjection (v1) — per-agent active-action-"
                    "request snapshot with source_event_id provenance and "
                    "projection refresh_seq. Consumed by sync-status, "
                    "claude-loop, dashboard, and the canonical-active-packet "
                    "predicate. Per Codex rev_pkt_2271/2326/2368."
                ),
            ),
            ContractField(
                "agent_work_board",
                "dict[str, object]",
                (
                    "Typed AgentWorkBoardProjection (v1.1) — observed-runtime "
                    "session/subagent rows with active_packet_id, "
                    "mutation_mode, branch/worktree identity, current "
                    "command/check/file, idle_seconds, blocker, "
                    "source_event_id, and confidence_class. Consumed by "
                    "sync-status MD/JSON, dashboard active_codex_sessions, "
                    "claude-loop, and bridge-poll typed-convergence. "
                    "Per Codex rev_pkt_2279/2287/2293/2374."
                ),
            ),
            ContractField(
                "coordination_state",
                "dict[str, object]",
                (
                    "Typed CoordinationStateProjection — 4-field topology/"
                    "authority split (coordination_topology, authority_mode, "
                    "recovery_eligibility, observed_runtime). Authoritative "
                    "for the multi-agent vs single-agent distinction; "
                    "supersedes legacy reviewer_mode for topology decisions. "
                    "Recovery-command surfaces gate on recovery_eligibility "
                    "to suppress local devctl-commit advice when remote_only "
                    "or blocked. Per Codex rev_pkt_2273/2278/2281/2298/2326/"
                    "2361/2367/2368."
                ),
            ),
            ContractField(
                "authority_snapshot",
                "AuthoritySnapshot | None",
                "Reduced next-turn authority contract mirrored into review-state projections.",
            ),
            ContractField(
                "round_proofs",
                "tuple[RoundProofState, ...]",
                "Typed proof ticks observed during review-channel rounds.",
            ),
            ContractField(
                "agent_loop_decisions",
                "list[dict[str, object]]",
                "Per-agent loop decisions derived from typed runtime and packet attention.",
            ),
            ContractField(
                "agent_dispatch_router",
                "dict[str, object]",
                (
                    "Typed task-to-agent router projection that selects or "
                    "blocks route ownership before AgentLoopDecision executes "
                    "a session turn."
                ),
            ),
            ContractField(
                "session_status_projection",
                "dict[str, object]",
                (
                    "Typed SessionStatusProjection read model answering whether "
                    "provider sessions task_completed, died mid-task, are still "
                    "running, or are detached runtime-only."
                ),
            ),
            ContractField(
                "attention",
                "ReviewAttentionState | None",
                "Current top-priority attention state, if any.",
            ),
            ContractField(
                "attention_windows",
                "dict[str, object]",
                "Per-peer attention window projection derived from typed packet attention.",
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
            "agent_loop_decisions",
            "agent_dispatch_router",
        ),
    ),
    ContractSpec(
        contract_id="SessionStatusProjection",
        owner_layer="governance_runtime",
        purpose=(
            "Single typed read model over CollaborationSession, "
            "AgentSessionOutcome, SessionLivenessSignal, AgentMindSlice, "
            "RecoveryAssessmentState, and SessionActivityEntry evidence that "
            "answers whether an agent task_completed or died mid-task."
        ),
        required_fields=(
            ContractField("generated_at_utc", "str", "UTC projection timestamp."),
            ContractField("status", "str", "Overall session status answer."),
            ContractField("answer", "str", "Operator-readable answer token."),
            ContractField(
                "rows",
                "tuple[SessionStatusRow, ...]",
                "Per-provider status rows with source evidence refs.",
            ),
            ContractField("head_sha", "str", "Repository HEAD observed by the projection."),
            ContractField(
                "worktree_hash",
                "str",
                "Worktree identity observed by the projection.",
            ),
            ContractField(
                "worktree_dirty",
                "bool | None",
                "Whether the live worktree was dirty when known.",
            ),
            ContractField(
                "evidence_refs",
                "tuple[str, ...]",
                "Typed source evidence refs consumed by the projection.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.session_status_projection:SessionStatusProjection",
        startup_surface_tokens=("status", "answer", "rows"),
    ),
    ContractSpec(
        contract_id="AgentDispatchRouter",
        owner_layer="governance_runtime",
        purpose=(
            "Read-only task-to-agent dispatch authority that composes "
            "WorkIntakePacket, review packets, agent work-board identity, "
            "task-router lanes, and guard/bundle dispatch metadata into one "
            "route-selection state."
        ),
        required_fields=(
            ContractField("snapshot_id", "str", "Source review-state snapshot id."),
            ContractField("source_identity", "dict[str, str]", "Source provenance."),
            ContractField(
                "source_contract",
                "str",
                "Source authority contract consumed by the router.",
            ),
            ContractField(
                "source_command",
                "str",
                "Repo-owned command that produced the source router input.",
            ),
            ContractField("repo_id", "str", "Repo-pack/governance identity."),
            ContractField("input_refs", "dict[str, str]", "Packet, plan, and instruction refs consumed by the router."),
            ContractField(
                "session_nodes",
                "tuple[AgentDispatchSessionNode, ...]",
                "Addressable live or recent actor/session nodes available for routing.",
            ),
            ContractField(
                "work_focus",
                "tuple[AgentDispatchWorkFocus, ...]",
                "Current typed packet/plan focus for each session node.",
            ),
            ContractField(
                "peer_links",
                "tuple[AgentDispatchPeerLink, ...]",
                "Typed coordination edges between agent sessions.",
            ),
            ContractField(
                "ambiguous_session_groups",
                "tuple[AgentDispatchAmbiguousGroup, ...]",
                "Fail-closed groups when multiple sessions claim the same packet or actor route.",
            ),
            ContractField(
                "governance_debt",
                "tuple[AgentDispatchGovernanceDebt, ...]",
                "Plan/session/packet binding debt that must be remediated before autonomous dispatch.",
            ),
            ContractField("routes", "tuple[AgentDispatchRoute, ...]", "Candidate actor/session routes."),
            ContractField("rejected_routes", "tuple[AgentDispatchRejection, ...]", "Rejected candidate routes with reasons."),
            ContractField("selected_route_id", "str", "Selected route id when unambiguous."),
            ContractField("selected_route_ids", "tuple[str, ...]", "Selected route ids, one per independent dispatchable work group."),
            ContractField("selection_reason", "str", "Reason for selected route or block."),
            ContractField("router_state", "str", "ready, partial, blocked, ambiguous, or no_dispatchable_work."),
        ),
        runtime_model="dev.scripts.devctl.runtime.agent_dispatch_router_models:AgentDispatchRouter",
        startup_surface_tokens=(
            "router_state",
            "selected_route_id",
            "selected_route_ids",
            "session_nodes",
            "work_focus",
            "ambiguous_session_groups",
            "governance_debt",
            "routes",
            "rejected_routes",
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
            ContractField(
                "session_posture",
                "SessionPosture",
                "Canonical live posture tuple for interaction mode, reviewer mode, and occupied actor lanes.",
            ),
            ContractField(
                "duty_proof",
                "ReviewerDutyProof",
                "Typed proof that the reviewer (or implementer) has performed the live observation duty for the current packet cycle.",
            ),
            ContractField(
                "inbox_observation",
                "InboxObservationState",
                "Typed projection of the actor-scoped inbox observation cursor that anchors wake-evidence and stale-attention detection.",
            ),
            ContractField(
                "agent_runtime_clock",
                "AgentRuntimeClock",
                "Shared monotonic cursor that lets both agents reason over the same runtime tick when proving freshness.",
            ),
            ContractField(
                "packet_attention",
                "PacketAttentionState",
                "Typed packet-attention projection used by the commit gate and reviewer-runtime doctor to decide whether the current actor has observed the canonical active packet.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.review_state_models:ReviewerRuntimeContract",
        startup_surface_tokens=(
            "reviewer_mode",
            "reviewer_freshness",
            "publish_clear",
            "remote_control_attachment",
            "session_posture",
        ),
    ),
    *REMOTE_CONTROL_STATE_CONTRACTS,
    ContractSpec(
        contract_id="SessionPosture",
        owner_layer="governance_runtime",
        purpose=(
            "Canonical proof-tick posture for interaction mode, reviewer "
            "mode, actor liveness, occupied lanes, and separate capability grants."
        ),
        required_fields=(
            ContractField("interaction_mode", "str", "remote_control, dual_agent, single_agent, local_terminal, or unresolved."),
            ContractField("reviewer_mode", "str", "Canonical reviewer mode for this proof tick."),
            ContractField(
                "effective_reviewer_mode",
                "str",
                "Effective reviewer mode after runtime demotion or promotion.",
            ),
            ContractField(
                "actors",
                "tuple[SessionPostureActor, ...]",
                "Actors with current occupied_lane, liveness, and independent granted capabilities.",
            ),
            ContractField("source", "str", "Producer for the posture projection."),
        ),
        runtime_model="dev.scripts.devctl.runtime.session_posture:SessionPosture",
        startup_surface_tokens=(
            "interaction_mode",
            "reviewer_mode",
            "actors",
        ),
    ),
    ContractSpec(
        contract_id="PacketIntentAnchor",
        owner_layer="governance_runtime",
        purpose=(
            "Non-authoritative continuity pointer from a planning packet to "
            "plan intent; pending or expired packets stay anchors, not execution authority."
        ),
        required_fields=(
            ContractField("packet_id", "str", "Review packet id that produced the anchor."),
            ContractField("target_plan", "str", "Plan target referenced by the packet."),
            ContractField("target_task", "str", "Task, intake, or mutation target referenced by the packet."),
            ContractField("anchor_refs", "tuple[str, ...]", "Typed plan anchor refs carried by the packet."),
            ContractField("lifecycle_state", "str", "plan_anchor_pending or applied."),
            ContractField("source_agent", "str", "Agent that posted the source packet."),
            ContractField("disposition", "str", "Packet disposition status when available."),
            ContractField("evidence", "tuple[str, ...]", "Packet and lifecycle evidence refs."),
            ContractField("packet_kind", "str", "Review packet kind that produced the anchor."),
            ContractField("summary", "str", "Bounded packet summary for continuity renderers."),
            ContractField("semantic_zref", "str", "Stable semantic packet pointer for graph/bootstrap surfaces."),
            ContractField("source_identity", "dict[str, str]", "Source proof-tick identity inherited from ReviewState."),
            ContractField("context_pack_refs", "tuple[dict[str, object], ...]", "Context pack refs carried by the source packet."),
        ),
        runtime_model="dev.scripts.devctl.runtime.packet_intent_anchor:PacketIntentAnchor",
        startup_surface_tokens=(
            "packet_id",
            "target_plan",
            "lifecycle_state",
            "packet_kind",
            "semantic_zref",
        ),
    ),
    ContractSpec(
        contract_id="PlanIterationSession",
        owner_layer="governance_runtime",
        purpose=(
            "Minimal alias over plan_gap_review, plan_patch_review, and "
            "plan_ready_gate packet anchors for startup continuity."
        ),
        required_fields=(
            ContractField("status", "str", "empty, plan_anchor_pending, or applied."),
            ContractField("packet_ids", "tuple[str, ...]", "Planning packet ids in the iteration view."),
            ContractField("anchor_refs", "tuple[str, ...]", "Union of typed plan anchors."),
            ContractField("source_packet_kinds", "tuple[str, ...]", "Planning packet kinds represented by the iteration view."),
        ),
        runtime_model="dev.scripts.devctl.runtime.packet_intent_anchor:PlanIterationSession",
        startup_surface_tokens=("status", "packet_ids", "anchor_refs", "source_packet_kinds"),
    ),
)
