"""Identity/action/evidence runtime contract rows for the platform blueprint."""

from __future__ import annotations

from ..runtime.agent_loop_bilateral_protocol import (
    AgentLoopBilateralProtocol,
    BilateralProtocolPropertyResult,
)
from .contracts import ContractField, ContractSpec
from .runtime_identity_contract_rows_commit import COMMIT_RECEIPT_CONTRACTS

_AGENT_LOOP_BILATERAL_PROTOCOL_RUNTIME_MODEL = (
    f"{AgentLoopBilateralProtocol.__module__}:{AgentLoopBilateralProtocol.__name__}"
)
_BILATERAL_PROPERTY_RESULTS_TYPE = (
    f"tuple[{BilateralProtocolPropertyResult.__name__}, ...]"
)


RUNTIME_IDENTITY_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="RepoPack",
        owner_layer="repo_packs",
        purpose=(
            "Declares repo policy, docs templates, workflow defaults, and "
            "adoption checks for one repository family."
        ),
        required_fields=(
            ContractField("pack_id", "str", "Stable repo-pack identifier."),
            ContractField(
                "policy_path",
                "str",
                "Path to the repo policy file used by quality/governance commands.",
            ),
            ContractField(
                "workflow_profiles",
                "list[str]",
                "Allowlisted workflow/action profiles exposed for this repo.",
            ),
        ),
        startup_surface_tokens=("pack_id", "policy_path", "workflow_profiles"),
    ),
    ContractSpec(
        contract_id="TypedAction",
        owner_layer="governance_runtime",
        purpose=(
            "Canonical command payload for check, probe, bootstrap, fix, "
            "report, export, review, and remediation actions."
        ),
        required_fields=(
            ContractField("action_id", "str", "Stable typed action identifier."),
            ContractField(
                "repo_pack_id",
                "str",
                "Repo pack responsible for repo-local policy or defaults.",
            ),
            ContractField(
                "parameters",
                "dict[str, object]",
                "Machine-readable action arguments after parsing/validation.",
            ),
            ContractField("requested_by", "str", "Caller identity requesting the action."),
            ContractField(
                "dry_run",
                "bool",
                "Whether execution is report-only and must not mutate state.",
            ),
            ContractField("correlation_id", "str", "Parent lineage shared across related actions, events, and receipts."),
            ContractField("causation_id", "str", "Immediate trigger lineage for this action."),
            ContractField("run_id", "str", "Orchestration run lineage for this action."),
        ),
        runtime_model="dev.scripts.devctl.runtime.action_contracts:TypedAction",
        startup_surface_tokens=("action_id", "repo_pack_id", "correlation_id"),
    ),
    ContractSpec(
        contract_id="RunRecord",
        owner_layer="governance_runtime",
        purpose=(
            "Durable record for one governed execution episode, including "
            "inputs, findings, repairs, and outcomes."
        ),
        required_fields=(
            ContractField("run_id", "str", "Stable execution episode identifier."),
            ContractField("action_id", "str", "Typed action executed for the episode."),
            ContractField(
                "artifact_paths",
                "list[str]",
                "Materialized artifacts emitted during the episode.",
            ),
            ContractField("status", "str", "Execution status for the governed run."),
            ContractField("findings_count", "int", "Finding count emitted during the run."),
            ContractField("started_at", "str", "UTC start timestamp for the run."),
            ContractField("finished_at", "str", "UTC finish timestamp for the run."),
            ContractField("correlation_id", "str", "Parent lineage shared across this run and its receipts."),
            ContractField("causation_id", "str", "Immediate trigger lineage for this run."),
        ),
        runtime_model="dev.scripts.devctl.runtime.action_contracts:RunRecord",
        startup_surface_tokens=("run_id", "status", "correlation_id"),
    ),
    ContractSpec(
        contract_id="CorrelationContext",
        owner_layer="governance_runtime",
        purpose=(
            "Shared lineage context that links typed actions, action results, "
            "run records, receipts, packets, lifecycle events, and projections."
        ),
        required_fields=(
            ContractField("correlation_id", "str", "Parent lineage id for a related action chain."),
            ContractField("causation_id", "str", "Immediate trigger id within the chain."),
            ContractField("run_id", "str", "Bounded orchestration run id for the chain."),
        ),
        runtime_model="dev.scripts.devctl.runtime.correlation_spine:CorrelationContext",
        startup_surface_tokens=("correlation_id", "causation_id", "run_id"),
    ),
    ContractSpec(
        contract_id="EvidenceArchivePolicy",
        owner_layer="governance_runtime",
        purpose=(
            "Retention policy for evidence families; it permits archiving after "
            "typed lifecycle closure while preserving original receipt evidence."
        ),
        required_fields=(
            ContractField("policy_id", "str", "Stable archive policy id."),
            ContractField("evidence_kind", "str", "Evidence family covered by the policy."),
            ContractField("retention_days", "int", "Minimum days before archive eligibility."),
            ContractField("archive_root", "str", "Archive root for compressed evidence bundles."),
            ContractField("compression", "str", "Compression format for archive bundles."),
            ContractField(
                "archive_after_lifecycle_statuses",
                "tuple[str, ...]",
                "Lifecycle states that allow archive movement.",
            ),
            ContractField(
                "delete_source_after_archive",
                "bool",
                "Must remain false for typed receipts; archive never deletes evidence.",
            ),
            ContractField("manifest_required", "bool", "Whether archives require a manifest."),
            ContractField(
                "retrieval_ref_required",
                "bool",
                "Whether archived evidence must retain a retrieval ref.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.evidence_archive:EvidenceArchivePolicy",
        startup_surface_tokens=("policy_id", "evidence_kind", "retention_days"),
    ),
    ContractSpec(
        contract_id="EvidenceArchiveManifest",
        owner_layer="governance_runtime",
        purpose=(
            "Manifest for archived evidence bundles, preserving source hashes, "
            "archive paths, lifecycle state, and retrieval refs."
        ),
        required_fields=(
            ContractField("manifest_id", "str", "Stable archive manifest id."),
            ContractField("policy_id", "str", "Archive policy that produced the manifest."),
            ContractField("archive_path", "str", "Compressed archive bundle path."),
            ContractField("source_root", "str", "Source tree scanned for evidence files."),
            ContractField("head_sha_at_archive", "str", "Repository HEAD at archive time."),
            ContractField("entries", "tuple[EvidenceArchiveEntry, ...]", "Archived evidence entries."),
            ContractField("created_at_utc", "str", "UTC manifest creation timestamp."),
        ),
        runtime_model="dev.scripts.devctl.runtime.evidence_archive:EvidenceArchiveManifest",
        startup_surface_tokens=("manifest_id", "policy_id", "archive_path"),
    ),
    ContractSpec(
        contract_id="EvidenceArchiveReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Receipt proving an evidence archive operation preserved typed receipts "
            "and linked the compressed bundle to its manifest."
        ),
        required_fields=(
            ContractField("receipt_id", "str", "Stable archive receipt id."),
            ContractField("policy_id", "str", "Archive policy applied."),
            ContractField("manifest_id", "str", "Manifest produced by the archive."),
            ContractField("lifecycle_ref", "str", "Typed lifecycle or plan row that closed."),
            ContractField("lifecycle_status", "str", "Observed lifecycle status at archive time."),
            ContractField("archive_path", "str", "Compressed archive bundle path."),
            ContractField("manifest_path", "str", "Machine-readable manifest path."),
            ContractField("compressed", "bool", "Whether archive output is compressed."),
            ContractField("source_deleted", "bool", "Must be false for receipt preservation."),
            ContractField("evidence_refs", "tuple[str, ...]", "Refs proving archive eligibility."),
            ContractField("created_at_utc", "str", "UTC receipt creation timestamp."),
            ContractField("status", "str", "Archive receipt status."),
        ),
        runtime_model="dev.scripts.devctl.runtime.evidence_archive:EvidenceArchiveReceipt",
        startup_surface_tokens=("receipt_id", "manifest_id", "source_deleted"),
    ),
    ContractSpec(
        contract_id="SessionActivityEntry",
        owner_layer="governance_runtime",
        purpose=(
            "One typed per-session activity observation distilled from actions, "
            "dogfood receipts, reviewer audit receipts, packets, commands, and artifacts."
        ),
        required_fields=(
            ContractField("entry_id", "str", "Stable entry id inside the session log."),
            ContractField("session_id", "str", "Session this activity belongs to."),
            ContractField("actor_id", "str", "Actor that owns the session log."),
            ContractField("occurred_at_utc", "str", "UTC timestamp for the observed activity."),
            ContractField("activity_type", "str", "Typed category such as dogfood_self_check or reviewer_audit."),
            ContractField("summary", "str", "Operator-readable summary of what changed or was proven."),
            ContractField("status", "str", "Entry outcome/status."),
            ContractField("target_ref", "str", "Slice, packet, plan row, or artifact target."),
            ContractField("evidence_refs", "tuple[str, ...]", "Typed evidence refs supporting this entry."),
            ContractField("artifact_paths", "tuple[str, ...]", "Repo artifact paths emitted or consumed."),
            ContractField("changed_files", "tuple[str, ...]", "Files changed by the activity when known."),
            ContractField("command_refs", "tuple[str, ...]", "Commands that produced the evidence."),
            ContractField("packet_refs", "tuple[str, ...]", "Review-channel packet refs linked to the activity."),
            ContractField("correlation_id", "str", "Parent lineage shared across related activity."),
            ContractField("causation_id", "str", "Immediate trigger lineage for the activity."),
            ContractField("run_id", "str", "Bounded run lineage for the activity."),
        ),
        runtime_model="dev.scripts.devctl.runtime.session_activity_log:SessionActivityEntry",
        startup_surface_tokens=("entry_id", "session_id", "activity_type"),
    ),
    ContractSpec(
        contract_id="SessionActivityLog",
        owner_layer="governance_runtime",
        purpose=(
            "Per-session operator-readable typed activity trail that summarizes what "
            "was added, verified, and archived without accumulating across sessions."
        ),
        required_fields=(
            ContractField("log_id", "str", "Stable activity log id."),
            ContractField("session_id", "str", "Session this log summarizes."),
            ContractField("actor_id", "str", "Actor that owns the session."),
            ContractField("role", "str", "Session role at time of logging."),
            ContractField("lifecycle_status", "str", "Open/closed/archive lifecycle state."),
            ContractField("started_at_utc", "str", "UTC session start timestamp when known."),
            ContractField("finished_at_utc", "str", "UTC session finish timestamp when closed."),
            ContractField("summary", "str", "Operator-readable session summary."),
            ContractField("entries", "tuple[SessionActivityEntry, ...]", "Session-scoped activity entries."),
            ContractField("evidence_refs", "tuple[str, ...]", "Aggregate refs for entries in this session."),
            ContractField("evidence_archive_ref", "str", "EvidenceArchiveReceipt ref after session close archival."),
        ),
        runtime_model="dev.scripts.devctl.runtime.session_activity_log:SessionActivityLog",
        startup_surface_tokens=("log_id", "session_id", "lifecycle_status"),
    ),
    ContractSpec(
        contract_id="ReviewerResponseShape",
        owner_layer="governance_runtime",
        purpose=(
            "Typed terminal-response policy derived from FinalResponseGateResult; "
            "it blocks status-only reviewer prose while continuation state is live "
            "and routes operator status to SessionActivityLog/typed packets."
        ),
        required_fields=(
            ContractField("actor_id", "str", "Actor whose terminal response is gated."),
            ContractField("role", "str", "Runtime role for the gated actor."),
            ContractField(
                "final_response_allowed",
                "bool",
                "Whether FinalResponseGateResult allows terminal completion prose.",
            ),
            ContractField(
                "continuation_state",
                "str",
                "Continuation state such as must_continue or may_stop.",
            ),
            ContractField(
                "response_mode",
                "str",
                "Allowed terminal response mode derived from typed controller state.",
            ),
            ContractField(
                "status_prose_allowed",
                "bool",
                "Whether status-update prose is allowed in the terminal response.",
            ),
            ContractField(
                "completion_prose_allowed",
                "bool",
                "Whether final completion prose is allowed.",
            ),
            ContractField(
                "required_next_action",
                "str",
                "Action the actor must take instead of terminal prose.",
            ),
            ContractField(
                "next_required_command",
                "str",
                "Typed next command to continue the active goal.",
            ),
            ContractField(
                "continuation_goal",
                "str",
                "Typed goal or packet that must be continued before terminal prose.",
            ),
            ContractField(
                "blocking_packet_id",
                "str",
                "Packet id blocking a terminal response, when one is present.",
            ),
            ContractField(
                "operator_status_source",
                "str",
                "Typed status source, normally a SessionActivityLog ref.",
            ),
            ContractField(
                "proposed_response_text_observed",
                "bool",
                "Whether the response-shape gate inspected a concrete response candidate.",
            ),
            ContractField(
                "proposed_response_text_source",
                "str",
                "Typed source for the response candidate inspected by the gate.",
            ),
            ContractField(
                "allowed_response_kinds",
                "tuple[str, ...]",
                "Typed response kinds allowed for the current continuation state.",
            ),
            ContractField(
                "forbidden_markers",
                "tuple[str, ...]",
                "Marker classes rejected in terminal prose while the gate is live.",
            ),
            ContractField(
                "violations",
                "tuple[str, ...]",
                "Response-shape violations found in a proposed terminal message.",
            ),
            ContractField(
                "status",
                "str",
                "Allowed/blocked status for a proposed terminal message.",
            ),
            ContractField("summary", "str", "Human-readable shape summary."),
        ),
        runtime_model="dev.scripts.devctl.runtime.reviewer_response_shape:ReviewerResponseShape",
        startup_surface_tokens=(
            "response_mode",
            "status_prose_allowed",
            "completion_prose_allowed",
        ),
    ),
    ContractSpec(
        contract_id="RoleInstructionCard",
        owner_layer="governance_runtime",
        purpose=(
            "Operator-editable typed instruction card for one custom role; "
            "markdown and slash surfaces may project it but do not own it."
        ),
        required_fields=(
            ContractField("card_id", "str", "Stable card id."),
            ContractField("role_id", "str", "Custom role id this card applies to."),
            ContractField("instruction_kind", "str", "Typed instruction category."),
            ContractField("rules", "tuple[str, ...]", "Instruction rules."),
            ContractField("guard_refs", "tuple[str, ...]", "RoleGuard refs enforcing the card."),
            ContractField("source_ref", "str", "Typed source or action that produced the card."),
            ContractField("active", "bool", "Whether the card is active."),
        ),
        runtime_model="dev.scripts.devctl.runtime.role_customization:RoleInstructionCard",
        startup_surface_tokens=("card_id", "role_id", "instruction_kind"),
    ),
    ContractSpec(
        contract_id="RoleGuard",
        owner_layer="governance_runtime",
        purpose=(
            "Typed enforcement rule attached to a custom role and executed at "
            "existing packet, response, profile, or mutation chokepoints."
        ),
        required_fields=(
            ContractField("guard_id", "str", "Stable guard id."),
            ContractField("role_id", "str", "Custom role id this guard applies to."),
            ContractField("enforcement_point", "str", "Existing chokepoint that runs the guard."),
            ContractField("violation_action", "str", "Fail-closed or report-only action."),
            ContractField("rule_refs", "tuple[str, ...]", "Instruction card refs covered by this guard."),
            ContractField("severity", "str", "Guard severity."),
            ContractField("active", "bool", "Whether the guard is active."),
        ),
        runtime_model="dev.scripts.devctl.runtime.role_customization:RoleGuard",
        startup_surface_tokens=("guard_id", "role_id", "enforcement_point"),
    ),
    ContractSpec(
        contract_id="CustomRoleDefinition",
        owner_layer="governance_runtime",
        purpose=(
            "Operator-defined role overlay mapped onto an existing "
            "DevelopmentModeTopology workstream instead of mutating TandemRole."
        ),
        required_fields=(
            ContractField("role_id", "str", "Custom role id."),
            ContractField(
                "base_workstream_id",
                "str",
                "Existing workstream authority lane the role overlays.",
            ),
            ContractField("display_name", "str", "Operator-facing role name."),
            ContractField("description", "str", "Optional role description."),
            ContractField(
                "base_tandem_role",
                "str",
                "Compatibility role for older tandem-loop consumers when present.",
            ),
            ContractField("capabilities", "tuple[str, ...]", "Custom role capabilities."),
            ContractField(
                "instruction_card_ids",
                "tuple[str, ...]",
                "RoleInstructionCard ids applied to this role.",
            ),
            ContractField("guard_ids", "tuple[str, ...]", "RoleGuard ids for this role."),
            ContractField(
                "slash_command_refs",
                "tuple[str, ...]",
                "Universal slash command entry points for editing this role.",
            ),
            ContractField("active", "bool", "Whether the custom role is active."),
        ),
        runtime_model="dev.scripts.devctl.runtime.role_customization:CustomRoleDefinition",
        startup_surface_tokens=("role_id", "base_workstream_id", "active"),
    ),
    ContractSpec(
        contract_id="RoleCreationAction",
        owner_layer="governance_runtime",
        purpose=(
            "Typed action payload that creates a custom role definition, "
            "instruction cards, guards, and universal slash command refs in one "
            "validated unit."
        ),
        required_fields=(
            ContractField("action_id", "str", "Stable role creation action id."),
            ContractField("role", "CustomRoleDefinition", "Custom role produced by the action."),
            ContractField(
                "instruction_cards",
                "tuple[RoleInstructionCard, ...]",
                "Instruction cards produced by the action.",
            ),
            ContractField("guards", "tuple[RoleGuard, ...]", "Role guards produced by the action."),
            ContractField("requested_by", "str", "Actor or operator requesting role creation."),
            ContractField("status", "str", "Accepted or rejected status."),
            ContractField("validation_errors", "tuple[str, ...]", "Validation errors."),
        ),
        runtime_model="dev.scripts.devctl.runtime.role_customization:RoleCreationAction",
        startup_surface_tokens=("action_id", "requested_by", "status"),
    ),
    ContractSpec(
        contract_id="PeerHeartbeatEvidence",
        owner_layer="governance_runtime",
        purpose=(
            "Bilateral heartbeat TTL evidence derived from peer_heartbeat and "
            "peer_offline review-channel packets while composing with existing session liveness."
        ),
        required_fields=(
            ContractField("actor_id", "str", "Actor resolving peer heartbeat state."),
            ContractField("actor_session_id", "str", "Current session id for the resolving actor."),
            ContractField("peer_actor_id", "str", "Peer actor expected to emit heartbeats."),
            ContractField("peer_session_id", "str", "Peer-targeted session id carried by the heartbeat packet."),
            ContractField("heartbeat_packet_id", "str", "Latest peer_heartbeat packet id."),
            ContractField("peer_offline_packet_id", "str", "peer_offline packet id when offline evidence exists."),
            ContractField("heartbeat_observed_at_utc", "str", "UTC time the heartbeat was posted or observed."),
            ContractField("expires_at_utc", "str", "UTC time the heartbeat expires."),
            ContractField("ttl_seconds", "int", "TTL fallback used when the packet has no explicit expiry."),
            ContractField("status", "str", "alive, expired, missing, session_mismatch, or peer_offline."),
            ContractField("peer_offline", "bool", "Whether the resolved evidence treats the peer as offline."),
            ContractField("summary", "str", "Operator-readable heartbeat resolution summary."),
        ),
        runtime_model="dev.scripts.devctl.runtime.peer_heartbeat:PeerHeartbeatEvidence",
        startup_surface_tokens=("actor_id", "peer_actor_id", "status"),
    ),
    ContractSpec(
        contract_id=AgentLoopBilateralProtocol.__name__,
        owner_layer="governance_runtime",
        purpose=(
            "Seven-property bilateral agent-loop protocol that binds cross-agent "
            "handoff authority to typed state, provider-neutral lane evidence, "
            "display-only projections, command evidence, and receipts."
        ),
        required_fields=(
            ContractField(
                "actor_id",
                "str",
                "Actor resolving or producing the protocol verdict.",
            ),
            ContractField(
                "peer_actor_id",
                "str",
                "Peer actor on the bilateral handoff path.",
            ),
            ContractField(
                "plan_row_id",
                "str",
                "Plan row covered by the bilateral protocol verdict.",
            ),
            ContractField("status", "str", "satisfied or violated."),
            ContractField(
                "property_results",
                _BILATERAL_PROPERTY_RESULTS_TYPE,
                "One machine-checkable verdict per bilateral protocol property.",
            ),
            ContractField(
                "failing_property_ids",
                "tuple[str, ...]",
                "Property ids that failed.",
            ),
            ContractField(
                "composability_contracts",
                "tuple[str, ...]",
                "Existing typed contracts composed by this protocol.",
            ),
            ContractField(
                "authority_refs",
                "tuple[str, ...]",
                "Typed authority refs; chat/memory/projection refs fail.",
            ),
            ContractField(
                "typed_action_refs",
                "tuple[str, ...]",
                "Typed actions or packets for serious actions.",
            ),
            ContractField(
                "handoff_refs",
                "tuple[str, ...]",
                "Continuation, stop, or lifecycle handoff refs.",
            ),
            ContractField(
                "resume_packet_refs",
                "tuple[str, ...]",
                "Typed packets that let a later agent resume.",
            ),
            ContractField(
                "lane_resumption_refs",
                "tuple[str, ...]",
                "Provider-neutral lane/session evidence refs.",
            ),
            ContractField(
                "projection_refs",
                "tuple[str, ...]",
                "Display-only projection refs.",
            ),
            ContractField(
                "command_evidence_refs",
                "tuple[str, ...]",
                "Evidence consumed before mutation commands.",
            ),
            ContractField(
                "receipt_refs",
                "tuple[str, ...]",
                "Receipts binding the action proof chain.",
            ),
            ContractField(
                "repo_state_ref",
                "str",
                "Repo-state ref bound by the receipt chain.",
            ),
            ContractField("actor_ref", "str", "Actor ref bound by the receipt chain."),
            ContractField(
                "guard_result_ref",
                "str",
                "Guard result ref bound by the receipt chain.",
            ),
            ContractField(
                "command_ref",
                "str",
                "Command ref bound by the receipt chain.",
            ),
            ContractField("proof_ref", "str", "Proof ref bound by the receipt chain."),
            ContractField("summary", "str", "Operator-readable protocol verdict."),
        ),
        runtime_model=_AGENT_LOOP_BILATERAL_PROTOCOL_RUNTIME_MODEL,
        startup_surface_tokens=("actor_id", "peer_actor_id", "status"),
    ),
    ContractSpec(
        contract_id="PreDecisionComposabilityWindow",
        owner_layer="governance_runtime",
        purpose=(
            "Typed pre-decision window over task_started packets that records "
            "composability anchors, duplicate-hunt evidence, reviewer ack/objection, "
            "and whether commit should remain blocked."
        ),
        required_fields=(
            ContractField("actor_id", "str", "Actor proposing the architectural slice."),
            ContractField("reviewer_id", "str", "Reviewer actor expected to ack or object."),
            ContractField("plan_row_id", "str", "Plan row covered by the pre-decision window."),
            ContractField("task_started_packet_id", "str", "task_started packet opening the window."),
            ContractField("ack_packet_id", "str", "Reviewer ack packet id when present."),
            ContractField("objection_packet_id", "str", "Reviewer objection packet id when present."),
            ContractField("opened_at_utc", "str", "UTC timestamp when the window opened."),
            ContractField("closes_at_utc", "str", "UTC timestamp when the window closes."),
            ContractField("window_seconds", "int", "Window duration in seconds."),
            ContractField("composability_anchors", "tuple[str, ...]", "Typed anchors codex must compose with."),
            ContractField("duplicate_hunt_ref", "str", "Duplicate-hunt evidence ref."),
            ContractField("status", "str", "Resolved pre-decision state."),
            ContractField("commit_blocked", "bool", "Whether commit should remain blocked."),
            ContractField("summary", "str", "Operator-readable window decision summary."),
        ),
        runtime_model="dev.scripts.devctl.runtime.pre_decision_window:PreDecisionComposabilityWindow",
        startup_surface_tokens=("plan_row_id", "status", "commit_blocked"),
    ),
    *COMMIT_RECEIPT_CONTRACTS,
    ContractSpec(
        contract_id="GoalProgressReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Operator-visible progress receipt derived from goal_progress packets "
            "and linked to the active continuation_anchor stop gate."
        ),
        required_fields=(
            ContractField("actor_id", "str", "Actor whose continuation goal is progressing."),
            ContractField("continuation_goal", "str", "Current continuation goal ref."),
            ContractField("continuation_anchor_packet_id", "str", "Active continuation_anchor packet id."),
            ContractField("latest_progress_packet_id", "str", "Newest goal_progress packet used as evidence."),
            ContractField("plan_row_id", "str", "Plan row or section anchor advanced by the progress packet."),
            ContractField("completed_units", "int", "Completed units parsed from progress evidence."),
            ContractField("total_units", "int", "Total units parsed from progress evidence."),
            ContractField("progress_percentage_toward_goal", "int", "Operator-visible progress percentage."),
            ContractField("status", "str", "missing, in_progress, complete, or invalid_progress."),
            ContractField("updated_at_utc", "str", "UTC timestamp of the progress evidence."),
            ContractField("summary", "str", "Operator-readable progress summary."),
            ContractField("evidence_refs", "tuple[str, ...]", "Typed evidence refs supporting progress."),
            ContractField("packet_refs", "tuple[str, ...]", "Packet refs supporting progress."),
        ),
        runtime_model="dev.scripts.devctl.runtime.goal_progress_receipt:GoalProgressReceipt",
        startup_surface_tokens=("continuation_goal", "progress_percentage_toward_goal", "status"),
    ),
    ContractSpec(
        contract_id="ActionResult",
        owner_layer="governance_runtime",
        purpose=(
            "Canonical result envelope for any command, service call, or "
            "agent action so all consumers parse one outcome shape."
        ),
        required_fields=(
            ContractField("action_id", "str", "Typed action that produced this result."),
            ContractField("ok", "bool", "Whether the action succeeded."),
            ContractField("status", "str", "Execution status label."),
            ContractField("reason", "str", "Failure or outcome reason code."),
            ContractField(
                "retryable",
                "bool",
                "Whether the caller can retry with the same inputs.",
            ),
            ContractField(
                "partial_progress",
                "bool",
                "Whether some work completed before failure.",
            ),
            ContractField(
                "operator_guidance",
                "str",
                "Human-readable next-step guidance on failure.",
            ),
            ContractField("warnings", "list[str]", "Non-fatal advisory messages."),
            ContractField(
                "errors",
                "list[dict[str, object]]",
                "Structured failure details with reason/remediation evidence.",
            ),
            ContractField(
                "reason_chain",
                "list[str]",
                "Ordered machine-readable reason path for blockers.",
            ),
            ContractField(
                "remediation",
                "str",
                "Machine-readable remediation or next bounded action.",
            ),
            ContractField(
                "auto_executable",
                "bool",
                "Whether the remediation can be run by automation without a new operator decision.",
            ),
            ContractField("findings_count", "int", "Findings emitted during the action."),
            ContractField(
                "artifact_paths",
                "list[str]",
                "Materialized artifacts produced by the action.",
            ),
            ContractField("correlation_id", "str", "Parent lineage shared with the producing TypedAction."),
            ContractField("causation_id", "str", "Immediate trigger lineage for this result."),
            ContractField("run_id", "str", "Orchestration run lineage for this result."),
        ),
        runtime_model="dev.scripts.devctl.runtime.action_contracts:ActionResult",
        startup_surface_tokens=("status", "reason", "correlation_id"),
    ),
    ContractSpec(
        contract_id="ArtifactStore",
        owner_layer="governance_runtime",
        purpose=(
            "Stable storage contract for reports, projections, review "
            "packets, snapshots, and benchmark evidence."
        ),
        required_fields=(
            ContractField("root", "str", "Root path for managed artifacts."),
            ContractField(
                "retention_policy",
                "dict[str, object]",
                "Retention/deletion rules enforced for this artifact family.",
            ),
            ContractField("managed_kinds", "list[str]", "Artifact kinds stored under the root."),
        ),
        runtime_model="dev.scripts.devctl.runtime.action_contracts:ArtifactStore",
        startup_surface_tokens=("root", "managed_kinds", "retention_policy"),
    ),
    ContractSpec(
        contract_id="Finding",
        owner_layer="governance_runtime",
        purpose=(
            "Canonical machine-readable evidence row for one governance "
            "finding across probes, reports, and later review/fix flows."
        ),
        required_fields=(
            ContractField("finding_id", "str", "Stable finding identifier."),
            ContractField(
                "signal_type",
                "str",
                "Signal family that produced the finding, such as probe.",
            ),
            ContractField("check_id", "str", "Check or probe identifier."),
            ContractField("rule_id", "str", "Stable rule identifier."),
            ContractField("rule_version", "int", "Version of the emitting rule."),
            ContractField("repo_name", "str", "Repo identity label."),
            ContractField("repo_path", "str", "Repo provenance path."),
            ContractField("file_path", "str", "Repo-relative file path."),
            ContractField("symbol", "str", "Symbol or file-level target."),
            ContractField("line", "int | None", "Start line for the finding."),
            ContractField("end_line", "int | None", "End line for the finding."),
            ContractField("severity", "str", "Finding severity."),
            ContractField("risk_type", "str", "Normalized risk family."),
            ContractField("review_lens", "str", "Review lens or discipline."),
            ContractField(
                "ai_instruction",
                "str",
                "Machine-readable remediation guidance for AI.",
            ),
            ContractField("signals", "list[str]", "Raw evidence signals."),
            ContractField(
                "source_command",
                "str",
                "Command that emitted or aggregated the finding.",
            ),
            ContractField(
                "source_artifact",
                "str",
                "Artifact family that carried the finding.",
            ),
            ContractField(
                "correlation_id",
                "str",
                "Parent lineage shared with related review and remediation evidence.",
            ),
            ContractField(
                "causation_id",
                "str",
                "Immediate trigger lineage for the finding.",
            ),
            ContractField(
                "run_id",
                "str",
                "Run lineage for the finding-producing check or artifact.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.finding_contracts:FindingRecord",
        startup_surface_tokens=("check_id", "severity", "correlation_id"),
    ),
    ContractSpec(
        contract_id="DecisionPacket",
        owner_layer="governance_runtime",
        purpose=(
            "Typed decision packet projected from one canonical finding for "
            "AI/human architectural review and approval."
        ),
        required_fields=(
            ContractField("finding_id", "str", "Stable source finding identifier."),
            ContractField("check_id", "str", "Check or probe identifier."),
            ContractField("rule_id", "str", "Stable rule identifier."),
            ContractField("rule_version", "int", "Version of the emitting rule."),
            ContractField("file_path", "str", "Repo-relative file path."),
            ContractField("symbol", "str", "Symbol or file-level target."),
            ContractField("severity", "str", "Finding severity."),
            ContractField("review_lens", "str", "Review lens or discipline."),
            ContractField("risk_type", "str", "Normalized decision risk family."),
            ContractField(
                "decision_mode",
                "str",
                "Whether the AI may auto-apply, recommend, or request approval.",
            ),
            ContractField("rationale", "str", "Human/AI rationale for the decision."),
            ContractField(
                "ai_instruction",
                "str",
                "Machine-readable guidance carried forward from the finding.",
            ),
            ContractField(
                "research_instruction",
                "str",
                "Follow-up investigation prompt for the decision-maker.",
            ),
            ContractField(
                "source_artifact",
                "str",
                "Artifact family that carried the packet.",
            ),
            ContractField("precedent", "str", "Prior art or precedent reference."),
            ContractField("invariants", "list[str]", "Constraints the decision must preserve."),
            ContractField(
                "validation_plan",
                "list[str]",
                "Checks to rerun after the selected decision path.",
            ),
            ContractField("signals", "list[str]", "Evidence signals carried into the packet."),
            ContractField(
                "rule_summary",
                "str",
                "Plain-language summary of why this decision rule was selected.",
            ),
            ContractField(
                "match_evidence",
                "list[RuleMatchEvidence]",
                "Structured reasons and concrete facts showing why the selected rule matched.",
            ),
            ContractField(
                "rejected_rule_traces",
                "list[RejectedRuleTrace]",
                "Competing rules that were considered and explicitly rejected.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.finding_contracts:DecisionPacketRecord",
        startup_surface_tokens=("decision_mode", "rule_summary", "validation_plan"),
    ),
    ContractSpec(
        contract_id="FailurePacket",
        owner_layer="governance_runtime",
        purpose=(
            "Canonical failure-evidence packet for test and workflow failures "
            "so triage, reports, and automation consume one structured root-cause surface."
        ),
        required_fields=(
            ContractField("source", "str", "Origin of the failure evidence bundle."),
            ContractField("runner", "str", "Failing test runner or workflow executor."),
            ContractField("generated_at", "str", "UTC timestamp for packet materialization."),
            ContractField("status", "str", "Overall packet status such as failed or passed."),
            ContractField("total_tests", "int", "Total tests observed in the packet."),
            ContractField("failed_tests", "int", "Total failed test cases."),
            ContractField("error_tests", "int", "Total errored test cases."),
            ContractField("skipped_tests", "int", "Total skipped test cases."),
            ContractField("passed_tests", "int", "Total passed test cases."),
            ContractField(
                "primary_test_id",
                "str",
                "Best-effort first or highest-priority failing test identifier.",
            ),
            ContractField(
                "primary_message",
                "str",
                "Best-effort primary assertion/error message for the packet.",
            ),
            ContractField(
                "cases",
                "tuple[FailureCase, ...]",
                "Structured failing test cases with message and traceback excerpts.",
            ),
            ContractField(
                "artifact_paths",
                "list[str]",
                "Artifact paths used to build the packet.",
            ),
            ContractField("warnings", "list[str]", "Non-blocking packet ingestion warnings."),
        ),
        runtime_model="dev.scripts.devctl.runtime.failure_packet:FailurePacket",
        startup_surface_tokens=("runner", "status", "primary_test_id"),
    ),
)
