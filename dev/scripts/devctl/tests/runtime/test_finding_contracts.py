"""Tests for shared finding and decision-packet contracts."""

from __future__ import annotations

from dev.scripts.devctl.runtime.finding_contracts import (
    DECISION_PACKET_CONTRACT_ID,
    DECISION_PACKET_SCHEMA_VERSION,
    DecisionPacketPolicy,
    FINDING_CONTRACT_ID,
    FINDING_SCHEMA_VERSION,
    FindingIdentitySeed,
    build_finding_id,
    decision_packet_from_finding,
    enrich_probe_hint_contract,
    finding_from_probe_hint,
)


def test_finding_from_probe_hint_builds_canonical_contract() -> None:
    finding = finding_from_probe_hint(
        {
            "file": "demo.py",
            "symbol": "render_status",
            "probe": "probe_identifier_density",
            "line": "14",
            "risk_type": "design_smell",
            "severity": "high",
            "review_lens": "design_quality",
            "ai_instruction": "extract shared helper",
            "signals": ["dense identifiers", "repeated domain words"],
        },
        repo_name="demo-repo",
        repo_path="/tmp/demo-repo",
        source_command="probe-report",
        source_artifact="probe-report:risk_hints",
    ).to_dict()

    assert finding["schema_version"] == FINDING_SCHEMA_VERSION
    assert finding["contract_id"] == FINDING_CONTRACT_ID
    assert finding["signal_type"] == "probe"
    assert finding["check_id"] == "probe_identifier_density"
    assert finding["rule_id"] == "probe_identifier_density"
    assert finding["file_path"] == "demo.py"
    assert finding["file"] == "demo.py"
    assert finding["probe"] == "probe_identifier_density"
    assert finding["line"] == 14
    assert finding["source_artifact"] == "probe-report:risk_hints"
    assert finding["finding_id"]


def test_decision_packet_from_finding_preserves_identity_and_provenance() -> None:
    finding = enrich_probe_hint_contract(
        hint={
            "file": "demo.py",
            "symbol": "render_status",
            "probe": "probe_identifier_density",
            "severity": "medium",
            "risk_type": "design_smell",
            "review_lens": "design_quality",
            "signals": ["dense identifiers"],
            "ai_instruction": "extract shared helper",
        },
        repo_name="demo-repo",
        repo_path="/tmp/demo-repo",
    )

    packet = decision_packet_from_finding(
        finding,
        policy=DecisionPacketPolicy(
            decision_mode="recommend_only",
            rationale="Keep the orchestration seam explicit.",
            research_instruction="Consider a typed presenter object.",
            precedent="Similar presenter boundaries already exist.",
            invariants=("Preserve the public render contract.",),
            validation_plan=("Run `python3 dev/scripts/devctl.py check --profile ci`.",),
        ),
    ).to_dict()

    assert packet["schema_version"] == DECISION_PACKET_SCHEMA_VERSION
    assert packet["contract_id"] == DECISION_PACKET_CONTRACT_ID
    assert packet["finding_id"] == finding["finding_id"]
    assert packet["check_id"] == finding["check_id"]
    assert packet["rule_id"] == finding["rule_id"]
    assert packet["file_path"] == "demo.py"
    assert packet["probe"] == "probe_identifier_density"
    assert packet["source_artifact"] == "probe-report:risk_hints"


def test_build_finding_id_is_stable_for_same_inputs() -> None:
    seed = FindingIdentitySeed(
        repo_name="demo-repo",
        repo_path="/tmp/demo-repo",
        signal_type="probe",
        check_id="probe_identifier_density",
        file_path="demo.py",
        symbol="render_status",
        line=14,
        end_line=None,
        risk_type="design_smell",
        review_lens="design_quality",
        signals=("dense identifiers",),
    )
    first = build_finding_id(seed)
    second = build_finding_id(seed)

    assert first == second
