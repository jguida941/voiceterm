"""Tests for provider-neutral development lane contracts."""

from __future__ import annotations

import json

from dev.scripts.devctl.commands.development import scaling_summary_from_contract
from dev.scripts.devctl.runtime.development_collaboration_modes import (
    COLLABORATION_MODE_CONTRACT_ID,
    build_default_collaboration_mode_topology,
    collaboration_mode_report,
)
from dev.scripts.devctl.runtime.development_collaboration_profiles import (
    PROFILE_CONTRACT_ID,
    build_agent_collaboration_profile,
    profile_template,
)
from dev.scripts.devctl.runtime.development_role_adapters import (
    build_develop_role_adapter_matrix,
    render_develop_role_adapter_matrix_markdown,
)
from dev.scripts.devctl.runtime.master_plan_contract import PlanRow
from dev.scripts.devctl.runtime.development_team import (
    DEVELOPMENT_MODE_CONTRACT_ID,
    build_default_development_team,
)


def _collaboration_review_state() -> dict[str, object]:
    return {
        "collaboration": {
            "contract_id": "CollaborationSession",
            "session_id": "collab-session",
            "plan_id": "MP-377",
            "status": "active",
            "reviewer_mode": "remote_control",
            "operator_mode": "operator_present",
            "lead_agent": "operator",
            "review_agent": "codex",
            "coding_agent": "claude",
            "current_slice": "MP377-P0-T22Y-J",
            "topology_mode": "paired_remote_control",
            "work_ownership_mode": "exclusive_slice",
            "mutation_owner": "claude",
            "verification_owner": "codex",
            "watcher_owner": "claude",
            "peer_review": {
                "current_instruction": "do not surface this full instruction",
                "current_instruction_revision": "rev-sync-1",
                "open_findings": "2",
                "implementer_status": "active",
                "implementer_ack": "acked",
                "implementer_ack_state": "current",
                "last_reviewed_scope": "dev/scripts/devctl/runtime",
            },
            "arbitration": {
                "status": "clear",
                "summary": "no arbitration required",
                "owner": "system",
            },
            "ready_gates": [
                {
                    "gate_id": "runtime_truth",
                    "status": "ready",
                    "summary": "typed runtime evidence present",
                }
            ],
            "actor_authorities": [
                {
                    "actor_id": "codex",
                    "provider": "codex",
                    "role": "reviewer",
                    "live": True,
                    "status": "active",
                    "source": "CollaborationSession",
                    "session_id": "codex-session",
                    "grants": [
                        {
                            "capability": "runtime.observe",
                            "granted": True,
                            "source": "test",
                        },
                        {
                            "capability": "mutation.write",
                            "granted": False,
                            "source": "test",
                        },
                    ],
                }
            ],
            "session_posture": {
                "contract_id": "SessionPosture",
                "interaction_mode": "remote_control",
                "reviewer_mode": "dual_agent",
                "effective_reviewer_mode": "dual_agent",
                "actors": [
                    {
                        "actor_id": "claude-session",
                        "provider": "claude",
                        "role": "implementer",
                        "occupied_lane": "remote_control",
                        "presence": "live",
                        "live": True,
                        "source": "test",
                    }
                ],
            },
        }
    }


def test_default_development_team_is_provider_neutral() -> None:
    team = build_default_development_team()

    assert team.contract_id == DEVELOPMENT_MODE_CONTRACT_ID
    assert "provider name never grants authority" in team.assignment_policy
    assert "may occupy any workstream" in team.provider_policy
    assert team.default_worker_fanout == 0


def test_default_development_team_uses_clear_workstream_names() -> None:
    team = build_default_development_team()
    names = {item.display_name for item in team.workstreams}

    assert names == {
        "Coordinator",
        "Builder",
        "Reviewer",
        "Plan Intake Steward",
        "Researcher",
        "Knowledge Synthesizer",
        "Architect",
        "Quality Engineer",
        "Dogfood Tester",
        "Runtime Watcher",
        "Operator",
    }


def test_live_tree_owner_is_the_only_default_live_writer() -> None:
    team = build_default_development_team()
    live_writers = [
        item
        for item in team.workstreams
        if item.authority.lease_kind == "live_tree"
    ]

    assert [item.workstream_id for item in live_writers] == ["builder"]
    builder = live_writers[0]
    assert builder.authority.exclusive is True
    assert set(builder.authority.capabilities) == {"repo.stage", "repo.commit"}
    assert "self_accept_review" in builder.blocked_actions


def test_learning_workstreams_make_prevention_load_bearing() -> None:
    team = build_default_development_team()
    workstreams = {item.workstream_id: item for item in team.workstreams}

    synthesizer = workstreams["knowledge_synthesizer"]
    architect = workstreams["architect"]
    quality = workstreams["quality_engineer"]
    assert "KnowledgeSynthesisRecord" in synthesizer.evidence.writes
    assert "PointerRefIndexEntry" in synthesizer.evidence.writes
    assert "make_graph_authority" in synthesizer.blocked_actions
    assert "PatternObservation" in architect.evidence.writes
    assert "PlanRow" in architect.evidence.writes
    assert "GuardSmartnessReport" in quality.evidence.writes
    assert "promote_without_replay" in quality.blocked_actions


def test_plan_intake_steward_ingests_packet_intent_before_expiry() -> None:
    team = build_default_development_team()
    workstreams = {item.workstream_id: item for item in team.workstreams}
    intake = workstreams["plan_intake_steward"]

    assert (
        "packet outcome without durable typed owner" in team.learning_loop.issue_sources
    )
    assert "PlanRow" in intake.evidence.writes
    assert "FindingReview" in intake.evidence.writes
    assert "GuardPromotionCandidate" in intake.evidence.writes
    assert "PacketDurableIngestionReceipt" in intake.evidence.writes
    assert "outcome_promoted_without_durable_row" in intake.routing.selection_signals
    assert "write_plan_row" in intake.allowed_actions
    assert "record_finding_review" in intake.allowed_actions
    assert "packet_as_source_of_truth" in intake.blocked_actions
    assert "expire_before_durable_ingestion" in intake.blocked_actions


def test_external_research_requires_route_grant_and_provenance() -> None:
    team = build_default_development_team()
    workstreams = {item.workstream_id: item for item in team.workstreams}
    researcher = workstreams["researcher"]

    assert team.external_research.route_grant_required is True
    assert "operator-approved web search results" in team.external_research.allowed_sources
    assert "source_url_or_repo_ref" in team.external_research.required_evidence
    assert "external_source_as_runtime_authority" in team.external_research.blocked_uses
    assert "ResearchRouteGrant" in researcher.evidence.reads
    assert "web_search_without_route_grant" in researcher.blocked_actions


def test_knowledge_flow_feeds_graph_pointer_plan_and_guard_surfaces() -> None:
    team = build_default_development_team()

    assert "GuardPromotionQueue" in team.knowledge_flow.canonical_sinks
    assert "ContextGraphSnapshot" in team.knowledge_flow.generated_projections
    assert "SystemMapSnapshot" in team.knowledge_flow.generated_projections
    assert "PointerRefIndex" in team.knowledge_flow.pointer_surfaces
    assert "ZGraph-compatible generated encoding" in team.knowledge_flow.pointer_surfaces
    assert "graph_as_authority_store" in team.knowledge_flow.forbidden_uses
    assert "generated projections rebuilt from canonical sinks" in (
        team.knowledge_flow.promotion_gates
    )


def test_scaling_contract_uses_honest_architecture_modes() -> None:
    team = build_default_development_team()
    mode_ids = {item.mode_id for item in team.scaling.modes}
    scaling_blob = json.dumps(team.scaling.to_dict(), sort_keys=True)

    assert mode_ids == {
        "controller_only",
        "intake_fanout",
        "review_fanout",
        "research_fanout",
        "watcher_fanout",
        "isolated_builder_fanout",
        "leased_live_tree_builder",
    }
    assert "single_agent" not in scaling_blob
    assert "PacketBacklogPressure" in team.scaling.pressure_inputs
    assert "PacketDebtRemediationReport" in team.scaling.pressure_inputs
    assert "WorkerPacket" in team.scaling.route_outputs
    assert "PacketCreationBinding" in team.scaling.route_outputs
    assert "PacketDurableIngestionReceipt" in team.scaling.route_outputs
    assert "PacketDebtRemediationReport" in team.scaling.route_outputs
    assert "AgentDispatchRouter.safe_to_fanout" in team.scaling.pressure_inputs
    assert "responds_to_packet_id or causal_packet_ids" in scaling_blob


def test_scaling_keeps_mutation_single_owner_while_fanning_out_intake() -> None:
    team = build_default_development_team()
    modes = {item.mode_id: item for item in team.scaling.modes}
    safety_blob = " ".join(team.scaling.safety_gates)

    assert "live-tree mutation requires exactly one active session-bound MutationLease" in (
        team.scaling.safety_gates
    )
    assert "AgentDispatchRouter.safe_to_fanout=true" in safety_blob
    assert "OrphanSnapshot" in " ".join(team.scaling.pressure_inputs)
    assert "OrphanSnapshot clear" in modes["isolated_builder_fanout"].required_gates
    assert "disjoint path_scope" in modes["isolated_builder_fanout"].required_gates
    assert "session-bound MutationLease" in modes["leased_live_tree_builder"].required_gates
    assert "PacketDurableIngestionReceipt" in modes["intake_fanout"].evidence_outputs


def test_collaboration_modes_are_read_only_role_presets() -> None:
    topology = build_default_collaboration_mode_topology()
    mode_ids = {item.mode_id for item in topology.modes}
    role_ids = {item.preset_id for item in topology.role_presets}
    report = collaboration_mode_report(max_workers=2)

    assert topology.contract_id == COLLABORATION_MODE_CONTRACT_ID
    assert "explains requested topology only" in topology.authority_policy
    assert topology.default_worker_fanout == 0
    assert mode_ids == {
        "solo",
        "pair_review",
        "dashboard_led",
        "intake_fanout",
        "research_fanout",
        "review_fanout",
        "watcher_fanout",
        "agent_sync",
        "isolated_builder_fanout",
        "dogfood_campaign",
    }
    assert role_ids == {
        "dashboard",
        "implementer",
        "reviewer",
        "architect",
        "researcher",
        "intake",
        "tester",
        "watcher",
        "operator",
    }
    assert topology.packet_pressure_policy.soft_attention_budget == 12
    assert topology.packet_pressure_policy.hard_attention_budget == 15
    assert topology.packet_pressure_policy.near_ttl_minutes == 10
    dashboard = next(item for item in topology.role_presets if item.preset_id == "dashboard")
    assert dashboard.attention_subscription == "AgentAttentionLoop"
    assert dashboard.timing_policy == "typed_event_driven_no_independent_poll"
    assert "packet_arrival" in dashboard.attention_events
    agent_sync = next(item for item in topology.modes if item.mode_id == "agent_sync")
    assert agent_sync.audit_role == "architect"
    assert agent_sync.max_audit_agent_count == 3
    assert "AgentMindSlice" in agent_sync.coordination_surfaces
    assert "advisory attention context only" in agent_sync.peer_polling_policy
    assert "stop_anchor" in agent_sync.stop_anchor_packet_kinds
    assert "packet_ack_or_apply" in agent_sync.stop_anchor_targets
    assert "plan_row_completed" in agent_sync.stop_anchor_targets
    assert "provider_label_grants_mutation" in agent_sync.blocked_when
    assert {budget.role for budget in agent_sync.role_count_budgets} == role_ids
    assert profile_template()["collaboration_mode"] == "agent_sync"
    assert report["selected_mode_id"] == "solo"
    assert report["selected_role_preset_id"] == "dashboard"
    assert report["mutable_fanout_status"] == "blocked_by_read_model_mode"


def test_agent_sync_profile_resolves_role_counts_without_granting_authority() -> None:
    profile = build_agent_collaboration_profile(
        profile_id="agent-sync",
        selected_mode_id="agent_sync",
        selected_role_preset_id="architect",
        providers=("codex", "claude"),
        role_bindings=(
            "implementer=claude:impl-session",
            "reviewer=codex",
            "architect=codex",
            "researcher=codex",
            "watcher=claude",
        ),
        role_counts=(
            "architect=3",
            "researcher=2",
            "watcher=1",
            "tester=4",
            "implementer=3",
        ),
        agent_mind_providers=("claude", "codex"),
        remote_provider="claude",
        source_packet_id="rev_pkt_source",
        target_packet_id="rev_pkt_target",
        stop_at_packet_id="rev_pkt_stop",
        stop_at_mp_row_id="MP377-DONE",
        review_state={
            "packets": [
                {
                    "packet_id": "rev_pkt_stop",
                    "status": "acked",
                    "lifecycle_current_state": "acknowledged",
                }
            ]
        },
        plan_rows=(
            PlanRow(
                row_id="MP377-DONE",
                title="Done row",
                status="completed",
                sdlc_stage="test",
            ),
        ),
        source_ref="plan:source",
        target_ref="plan:target",
        emit_template=True,
    )

    payload = profile.to_dict()
    budgets = {row["role"]: row for row in payload["resolved_role_budgets"]}
    assert payload["contract_id"] == PROFILE_CONTRACT_ID
    assert payload["selected_mode_id"] == "agent_sync"
    assert payload["selected_role_preset_id"] == "architect"
    assert payload["providers"] == ["codex", "claude"]
    assert payload["agent_mind_providers"] == ["claude", "codex"]
    assert payload["remote_provider"] == "claude"
    assert payload["stop_at_packet_id"] == "rev_pkt_stop"
    assert payload["stop_at_mp_row_id"] == "MP377-DONE"
    assert payload["stop_anchor_request"]["status"] == "stop_anchor_due"
    assert payload["stop_anchor_request"]["stop_packet_kind"] == "stop_anchor"
    assert payload["architecture_agent_count"] == 3
    assert payload["review_agent_count"] == 0
    assert payload["role_bindings"][0] == {
        "role": "implementer",
        "provider": "claude",
        "session_id": "impl-session",
        "source": "request",
    }
    assert budgets["architect"]["resolved_count"] == 3
    assert budgets["researcher"]["resolved_count"] == 2
    assert budgets["watcher"]["resolved_count"] == 1
    assert budgets["tester"]["resolved_count"] == 4
    assert budgets["implementer"]["mutable_lane_limit"] == 0
    assert payload["validation_errors"] == []
    assert payload["ok"] is True
    assert any("--agent claude" in command for command in payload["command_plan"])
    assert any("--packet-id rev_pkt_source" in command for command in payload["command_plan"])
    stop_commands = [
        command
        for command in payload["command_plan"]
        if "--kind stop_anchor" in command
    ]
    assert stop_commands
    assert all("--target-role" in command for command in stop_commands)
    assert all("--target-kind" not in command for command in stop_commands)
    assert all("--target-ref" not in command for command in stop_commands)
    assert any(
        "--actor claude --role implementer --session-id impl-session" in command
        for command in payload["command_plan"]
    )
    assert payload["template"]["collaboration_mode"] == "agent_sync"


def test_agent_sync_profile_exposes_compact_collaboration_session_state() -> None:
    profile = build_agent_collaboration_profile(
        profile_id="agent-sync",
        selected_mode_id="agent_sync",
        selected_role_preset_id="architect",
        role_bindings=("implementer=claude",),
        review_state=_collaboration_review_state(),
    )

    payload = profile.to_dict()
    session = payload["collaboration_session"]
    assert session["contract_id"] == "CollaborationSession"
    assert session["session_id"] == "collab-session"
    assert session["topology_mode"] == "paired_remote_control"
    assert session["owners"] == {
        "mutation_owner": "claude",
        "verification_owner": "codex",
        "watcher_owner": "claude",
    }
    assert session["peer_review"]["current_instruction_revision"] == "rev-sync-1"
    assert session["peer_review"]["implementer_ack_state"] == "current"
    assert "current_instruction" not in session["peer_review"]
    assert session["arbitration"]["status"] == "clear"
    assert session["ready_gates"][0]["gate_id"] == "runtime_truth"
    assert session["actor_authorities"][0]["actor_id"] == "codex"
    assert session["actor_authorities"][0]["capabilities"] == ["runtime.observe"]
    assert "mutation.write" not in json.dumps(session)
    assert payload["role_bindings"][0]["session_id"] == "claude-session"


def test_agent_sync_profile_reads_enveloped_collaboration_session_state() -> None:
    profile = build_agent_collaboration_profile(
        profile_id="agent-sync",
        selected_mode_id="agent_sync",
        selected_role_preset_id="architect",
        role_bindings=("implementer=claude",),
        review_state={"review_state": _collaboration_review_state()},
    )

    payload = profile.to_dict()
    session = payload["collaboration_session"]
    assert session["contract_id"] == "CollaborationSession"
    assert session["owners"]["mutation_owner"] == "claude"
    assert payload["role_bindings"][0]["session_id"] == "claude-session"


def test_agent_sync_profile_surfaces_peer_wake_commands_without_grants() -> None:
    profile = build_agent_collaboration_profile(
        profile_id="agent-sync",
        selected_mode_id="agent_sync",
        selected_role_preset_id="architect",
        role_bindings=("implementer=claude:impl-session",),
        agent_mind_providers=("claude",),
        review_state={
            "packet_inbox": {
                "agents": [
                    {
                        "agent": "claude",
                        "attention_status": "wake_required",
                        "wake_reason": "packet_arrival",
                        "pending_actionable_packet_ids": ["rev_pkt_wake"],
                        "required_command": (
                            "python3 dev/scripts/devctl.py review-channel "
                            "--action inbox --target claude --actor claude "
                            "--status pending --terminal none --format md"
                        ),
                    }
                ]
            }
        },
        events=(
            {
                "event_type": "packet_posted",
                "event_id": "evt-wake",
                "timestamp_utc": "2026-05-10T05:50:00Z",
                "to_agent": "claude",
                "target_role": "implementer",
                "target_session_id": "impl-session",
                "packet_id": "rev_pkt_wake",
            },
        ),
    )

    payload = profile.to_dict()
    wake = payload["advisory_wake_evidence"][0]
    commands = payload["command_plan"]
    inbox_index = next(
        index for index, command in enumerate(commands) if "--action inbox" in command
    )
    show_index = next(
        index for index, command in enumerate(commands) if "--packet-id rev_pkt_wake" in command
    )
    loop_index = next(
        index for index, command in enumerate(commands) if "--actor claude --role implementer" in command
    )

    assert wake["arrival_kind"] == "packet_arrival"
    assert wake["latest_relevant_packet_id"] == "rev_pkt_wake"
    assert wake["pending_packet_ids"] == ["rev_pkt_wake"]
    assert inbox_index < loop_index
    assert show_index < loop_index
    assert "--packet rev_pkt_wake" in commands[loop_index]
    assert payload["ok"] is True
    forbidden = ("git push", " git commit", "repo.stage", "vcs.stage", "bypass")
    assert not any(term in " ".join(commands) for term in forbidden)


def test_agent_sync_profile_ignores_wake_event_for_other_session() -> None:
    profile = build_agent_collaboration_profile(
        profile_id="agent-sync",
        selected_mode_id="agent_sync",
        selected_role_preset_id="architect",
        role_bindings=("implementer=claude:impl-session",),
        events=(
            {
                "event_type": "packet_posted",
                "event_id": "evt-wake",
                "timestamp_utc": "2026-05-10T05:50:00Z",
                "to_agent": "claude",
                "target_role": "implementer",
                "target_session_id": "other-session",
                "packet_id": "rev_pkt_other",
            },
        ),
    )

    payload = profile.to_dict()
    commands = payload["command_plan"]
    assert payload["advisory_wake_evidence"] == []
    assert not any("--packet rev_pkt_other" in command for command in commands)
    assert not any("--packet-id rev_pkt_other" in command for command in commands)


def test_stop_at_packet_rejected_when_mode_disallows_stop_targets() -> None:
    profile = build_agent_collaboration_profile(
        profile_id="solo-stop",
        selected_mode_id="solo",
        selected_role_preset_id="dashboard",
        stop_at_packet_id="rev_pkt_done",
        review_state={
            "packets": [
                {
                    "packet_id": "rev_pkt_done",
                    "status": "acked",
                    "lifecycle_current_state": "acknowledged",
                }
            ]
        },
    )

    payload = profile.to_dict()
    assert payload["ok"] is False
    assert payload["stop_anchor_request"]["status"] == "invalid_stop_anchor_target"
    assert payload["stop_anchor_request"]["validation_errors"] == payload[
        "validation_errors"
    ]
    assert "packet_ack_or_apply" in payload["validation_errors"][0]
    assert all("--kind stop_anchor" not in command for command in payload["command_plan"])


def test_stop_at_mp_row_rejected_when_mode_disallows_stop_targets() -> None:
    profile = build_agent_collaboration_profile(
        profile_id="solo-stop",
        selected_mode_id="solo",
        selected_role_preset_id="dashboard",
        stop_at_mp_row_id="MP377-DONE",
        plan_rows=(
            PlanRow(
                row_id="MP377-DONE",
                title="Done row",
                status="completed",
                sdlc_stage="test",
            ),
        ),
    )

    payload = profile.to_dict()
    assert payload["ok"] is False
    assert payload["stop_anchor_request"]["status"] == "invalid_stop_anchor_target"
    assert "plan_row_completed" in payload["validation_errors"][0]
    assert all("--kind stop_anchor" not in command for command in payload["command_plan"])


def test_agent_sync_missing_stop_packet_remains_readiness_warning() -> None:
    profile = build_agent_collaboration_profile(
        profile_id="agent-sync",
        selected_mode_id="agent_sync",
        selected_role_preset_id="architect",
        stop_at_packet_id="rev_pkt_missing",
    )

    payload = profile.to_dict()
    assert payload["ok"] is True
    assert payload["validation_errors"] == []
    assert payload["stop_anchor_request"]["status"] == "waiting_packet_not_found"
    assert "not in review_state packets" in payload["validation_warnings"][-1]
    assert all("--kind stop_anchor" not in command for command in payload["command_plan"])


def test_agent_sync_profile_caps_core_roles_by_live_topology_capacity() -> None:
    profile = build_agent_collaboration_profile(
        profile_id="agent-sync",
        selected_mode_id="agent_sync",
        selected_role_preset_id="reviewer",
        role_counts=("reviewer=2",),
        review_state={
            **_collaboration_review_state(),
            "bridge_liveness": {
                "session_liveness_signals": [
                    {
                        "provider": "codex",
                        "role": "reviewer",
                        "state": "alive",
                    }
                ]
            }
        },
    )

    payload = profile.to_dict()
    budget = payload["resolved_role_budgets"][0]
    assert budget["role"] == "reviewer"
    assert budget["requested_count"] == 2
    assert budget["resolved_count"] == 1
    assert budget["live_capacity"] == 1
    assert budget["capacity_source"] == "resolve_role_topology"
    assert budget["status"] == "capacity_limited"
    assert payload["ok"] is False
    assert "live topology capacity" in payload["validation_errors"][0]


def test_role_adapter_matrix_is_shared_for_codex_and_claude() -> None:
    rows = build_develop_role_adapter_matrix(extra_args="")
    by_provider = {
        provider: [row for row in rows if row.provider_id == provider]
        for provider in {row.provider_id for row in rows}
    }
    codex_roles = {row.role_preset: row.collaboration_mode for row in by_provider["codex"]}
    claude_roles = {
        row.role_preset: row.collaboration_mode for row in by_provider["claude"]
    }
    rendered = render_develop_role_adapter_matrix_markdown()

    assert codex_roles == claude_roles
    assert codex_roles["dashboard"] == "dashboard_led"
    assert codex_roles["implementer"] == "pair_review"
    assert codex_roles["tester"] == "review_fanout"
    assert "--actor codex --role-preset dashboard" in rendered
    assert "--actor claude --role-preset dashboard" in rendered


def test_develop_report_summary_consumes_scaling_contract() -> None:
    team = build_default_development_team()
    summary = scaling_summary_from_contract(team.scaling)

    assert "PacketBacklogPressure" in summary["pressure_inputs"]
    assert "PacketDebtRemediationReport" in summary["pressure_inputs"]
    assert "WorkerPacket" in summary["route_outputs"]
    assert "PacketCreationBinding" in summary["route_outputs"]
    assert "intake_fanout" in summary["mode_ids"]
    assert "Leased Live-Tree Builder" in summary["mode_names"]
    assert "live-tree mutation requires exactly one active session-bound MutationLease" in (
        summary["safety_gates"]
    )


def test_workstream_dict_keeps_authority_and_evidence_separate() -> None:
    team = build_default_development_team()
    payload = team.to_dict()
    first = payload["workstreams"][0]

    assert "scaling" in payload
    assert first["assignment_rule"] == "any_actor_with_matching_authority"
    assert first["display_name"] == "Coordinator"
    assert "authority" in first
    assert "evidence" in first
    assert "capabilities" in first["authority"]
    assert "reads" in first["evidence"]


def test_workstream_aliases_match_existing_architecture_terms() -> None:
    team = build_default_development_team()
    aliases = {
        alias
        for item in team.workstreams
        for alias in item.aliases
    }

    assert {
        "conductor",
        "implementer",
        "reviewer",
        "packet",
        "plan-ingest",
        "research",
        "synthesis",
        "pointer",
        "dogfood",
        "remote",
    }.issubset(aliases)
