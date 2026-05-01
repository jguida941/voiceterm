"""Tests for provider-neutral development lane contracts."""

from __future__ import annotations

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


def test_workstream_dict_keeps_authority_and_evidence_separate() -> None:
    team = build_default_development_team()
    payload = team.to_dict()
    first = payload["workstreams"][0]

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
