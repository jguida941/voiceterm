"""Tests for provider-neutral development lane contracts."""

from __future__ import annotations

import json

from dev.scripts.devctl.commands.development import scaling_summary_from_contract
from dev.scripts.devctl.runtime.development_collaboration_modes import (
    COLLABORATION_MODE_CONTRACT_ID,
    build_default_collaboration_mode_topology,
    collaboration_mode_report,
)
from dev.scripts.devctl.runtime.development_role_adapters import (
    build_develop_role_adapter_matrix,
    render_develop_role_adapter_matrix_markdown,
)
from dev.scripts.devctl.runtime.development_team import (
    DEVELOPMENT_MODE_CONTRACT_ID,
    build_default_development_team,
)


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
    assert report["selected_mode_id"] == "solo"
    assert report["selected_role_preset_id"] == "dashboard"
    assert report["mutable_fanout_status"] == "blocked_by_read_model_mode"


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
