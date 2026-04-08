"""Surface-projection state contract rows for the platform blueprint.

These contracts declare the typed fields that governance surfaces
(dashboard, session-resume, phone, compact) must wire through their
renderers.  Registering them in the closure guard prevents fields from
landing disconnected across required projections.
"""

from __future__ import annotations

from .contracts import ContractField, ContractSpec


SURFACE_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="CoordinationSnapshot",
        owner_layer="governance_core",
        purpose=(
            "Single bounded coordination authority shared by startup, "
            "review-channel, dashboard, and remote-control bootstrap surfaces."
        ),
        required_fields=(
            ContractField("generated_at_utc", "str", "UTC timestamp when the coordination snapshot was built."),
            ContractField("repo_name", "str", "Resolved repo name for the coordination snapshot."),
            ContractField("repo_root", "str", "Resolved repo root for the coordination snapshot."),
            ContractField("current_branch", "str", "Current branch observed by the reducer."),
            ContractField("head_commit_sha", "str", "Current HEAD commit SHA observed by the reducer."),
            ContractField("active_target", "PlanTargetRef | None", "Current governed plan target."),
            ContractField("current_slice", "str", "Current governed slice or instruction summary."),
            ContractField("scope_paths", "tuple[str, ...]", "Bounded owned path cluster for the slice."),
            ContractField("ownership_status", "str", "Current ownership/conflict posture."),
            ContractField("authority_mode", "str", "Authority model currently governing coordination."),
            ContractField("work_ownership_mode", "str", "Current work-ownership posture."),
            ContractField("sync_cadence_mode", "str", "Current sync cadence between participants."),
            ContractField("declared_topology", "str", "Planned topology declared by runtime state."),
            ContractField("observed_topology", "str", "Observed live topology from active participants."),
            ContractField("recommended_topology", "str", "Safe recommended topology under current truth."),
            ContractField("fanout_posture", "str", "Bounded fanout posture classification."),
            ContractField("safe_to_fanout", "bool", "Whether widening into fanout is currently safe."),
            ContractField("worktree_strategy", "str", "Current worker worktree isolation strategy."),
            ContractField("resync_required", "bool", "Whether operators must resync before fanout."),
            ContractField("resync_reasons", "tuple[str, ...]", "Bounded reasons that force resync."),
            ContractField(
                "observed_active_participant_count",
                "int",
                "Observed active participant count from typed runtime state.",
            ),
            ContractField(
                "declared_participant_count",
                "int",
                "Declared participant count from live collaboration state.",
            ),
            ContractField(
                "planned_delegated_worker_count",
                "int",
                "Planned delegated worker fanout count.",
            ),
            ContractField(
                "live_delegated_worker_count",
                "int",
                "Observed live delegated worker count.",
            ),
            ContractField(
                "active_participants",
                "tuple[str, ...]",
                "Identifiers for the currently active participants.",
            ),
            ContractField("duplicate_worktrees", "tuple[str, ...]", "Duplicate worker worktree conflicts."),
            ContractField("conflict_summaries", "tuple[str, ...]", "Bounded conflict summaries for concurrent work."),
            ContractField("actors", "tuple[CoordinationActorRecord, ...]", "Visible actors and delegated lanes."),
            ContractField("summary", "str", "Compact coordination summary line."),
        ),
        runtime_model=(
            "dev.scripts.devctl.platform.coordination_snapshot_models:"
            "CoordinationSnapshot"
        ),
        startup_surface_tokens=("current_slice", "recommended_topology", "resync_required"),
    ),
    ContractSpec(
        contract_id="ControlPlaneReadModel",
        owner_layer="governance_runtime",
        purpose=(
            "Single frozen resolved control-plane state consumed by "
            "dashboard, operator console, phone, and session-resume "
            "surfaces so every renderer agrees on gate resolution."
        ),
        required_fields=(
            ContractField("timestamp", "str", "UTC timestamp for the resolved snapshot."),
            ContractField("branch", "str", "Current git branch."),
            ContractField("head_sha", "str", "Current HEAD commit SHA."),
            ContractField("worktree_clean", "bool", "Whether the git worktree is clean."),
            ContractField("ahead_of_upstream", "int", "Commits ahead of the upstream tracking branch."),
            ContractField("resolved_phase", "str", "AutoModePhase derived from governance state."),
            ContractField("push_eligible", "bool", "Whether the governed push path is ready."),
            ContractField(
                "implementation_blocked",
                "bool",
                "Whether new implementation work is blocked by reviewer-runtime truth.",
            ),
            ContractField("top_blocker", "str", "Highest-priority blocker preventing push or work."),
            ContractField("next_action", "str", "Human-readable next governance action."),
            ContractField("next_command", "str", "Exact devctl command for the next action."),
            ContractField("reviewer_mode", "str", "Declared reviewer mode."),
            ContractField(
                "operator_interaction_mode",
                "str",
                "Resolved operator interaction mode for governance decisions.",
            ),
            ContractField("reviewer_freshness", "str", "Reviewer heartbeat freshness classification."),
            ContractField("review_accepted", "bool", "Whether the reviewer has accepted the current work."),
            ContractField("last_reviewed_sha", "str", "HEAD SHA at the last reviewer-accepted push."),
            ContractField("attention_status", "str", "Current attention-state classification."),
            ContractField("attention_summary", "str", "Human-readable attention-state summary."),
            ContractField("publisher_running", "bool", "Whether the publisher daemon is alive."),
            ContractField("supervisor_running", "bool", "Whether the supervisor daemon is alive."),
            ContractField("codex_conductor_alive", "bool", "Whether the Codex conductor is alive."),
            ContractField("claude_conductor_alive", "bool", "Whether the Claude conductor is alive."),
            ContractField("pending_action_requests", "int", "Count of pending review-channel action requests."),
            ContractField("last_guard_ok", "bool", "Whether the last guard bundle passed."),
            ContractField(
                "check_details",
                "tuple[dict[str, str], ...]",
                "Per-check status detail rows from the last guard run.",
            ),
            ContractField(
                "reviewer_observation",
                "ReviewerObservation | None",
                "Typed reviewer-observation record for HEAD visibility and review status.",
            ),
            ContractField(
                "coordination",
                "CoordinationSnapshot | None",
                "Shared bounded coordination authority for dashboard/bootstrap parity.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.control_plane_read_model:ControlPlaneReadModel",
        startup_surface_tokens=("push_eligible", "top_blocker", "resolved_phase"),
    ),
    ContractSpec(
        contract_id="AutoModeState",
        owner_layer="governance_runtime",
        purpose=(
            "Typed snapshot of the current auto-mode phase and transition "
            "hint derived from repo-owned governance signals."
        ),
        required_fields=(
            ContractField("phase", "str", "Current auto-mode lifecycle phase."),
            ContractField("phase_started_utc", "str", "UTC timestamp when the current phase started."),
            ContractField(
                "operator_interaction_mode",
                "str",
                "Resolved operator interaction mode for mode-aware transitions.",
            ),
            ContractField("reviewer_alive", "bool", "Whether a reviewer agent is active."),
            ContractField("implementer_alive", "bool", "Whether an implementer agent is active."),
            ContractField("last_commit_sha", "str", "HEAD commit SHA at the time of resolution."),
            ContractField("last_guard_ok", "bool", "Whether the last guard bundle passed."),
            ContractField("pending_action_requests", "int", "Count of pending action requests."),
            ContractField("next_transition", "str", "Human-readable hint for the next expected transition."),
        ),
        runtime_model="dev.scripts.devctl.runtime.auto_mode:AutoModeState",
        startup_surface_tokens=("phase", "next_transition"),
    ),
    ContractSpec(
        contract_id="SessionCachePacket",
        owner_layer="governance_commands",
        purpose=(
            "Compact session-state packet replacing full bootstrap output, "
            "used by session-resume, dashboard, and prompt builders."
        ),
        required_fields=(
            ContractField("generated_at_utc", "str", "UTC timestamp for cache generation."),
            ContractField("role", "str", "Agent role that owns the session."),
            ContractField("branch", "str", "Current git branch."),
            ContractField("head_sha", "str", "Current HEAD commit SHA."),
            ContractField("advisory_action", "str", "Governance advisory action from startup receipt."),
            ContractField("advisory_reason", "str", "Reason for the advisory action."),
            ContractField("blockers", "str", "Comma-separated blocker identifiers or 'none'."),
            ContractField("interaction_mode", "str", "Resolved operator interaction mode."),
            ContractField("current_instruction", "str", "Current reviewer instruction text."),
            ContractField("instruction_revision", "str", "Revision stamp for the current instruction."),
            ContractField("ack_state", "str", "Implementer ACK state for the current instruction."),
            ContractField("open_findings", "str", "Summary of open review findings."),
            ContractField("last_guard_ok", "bool", "Whether the last guard bundle passed."),
            ContractField("review_state_mtime", "float", "Review state file modification time for cache invalidation."),
            ContractField("last_reviewed_sha", "str", "HEAD SHA at the last reviewer-accepted push."),
            ContractField("done_summary", "str", "Summary of completed work from the push pipeline."),
            ContractField("next_action", "str", "Next governance action or devctl command."),
            ContractField("key_rules", "tuple[str, ...]", "Distilled governance key-rule assertions."),
            ContractField("head_at_push_time", "str", "HEAD SHA recorded at last push for drift detection."),
            ContractField(
                "operator_interaction_mode",
                "str",
                "Canonical operator interaction mode from ControlPlaneReadModel.",
            ),
            ContractField("resolved_phase", "str", "Auto-mode phase from ControlPlaneReadModel."),
            ContractField("next_guard_bundle", "str", "Recommended guard bundle for current changed paths."),
            ContractField("next_recommended_command", "str", "Exact devctl command to run next."),
            ContractField(
                "reviewer_observation_status",
                "str",
                "Reviewer observation status: not_seen, pending_review, under_review, or accepted.",
            ),
            ContractField(
                "review_candidate",
                "ReviewCandidateRecord | None",
                "Frozen current review target preferred over raw HEAD diff inference.",
            ),
            ContractField(
                "coordination",
                "CoordinationSnapshot | None",
                "Shared bounded coordination authority for remote-control bootstrap and dashboard parity.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.commands.governance.session_resume_support:"
            "SessionCachePacket"
        ),
        startup_surface_tokens=("last_reviewed_sha", "advisory_action", "blockers"),
    ),
)


def surface_state_contracts() -> tuple[ContractSpec, ...]:
    """Return surface-projection state contract rows."""
    return SURFACE_STATE_CONTRACTS
