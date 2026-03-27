"""Tests for shared finding and decision-packet contracts."""

from __future__ import annotations

from dev.scripts.devctl.runtime import (
    DECISION_PACKET_CONTRACT_ID,
    DECISION_PACKET_SCHEMA_VERSION,
    GUARD_RULE_VERSION,
    DecisionPacketPolicy,
    FINDING_CONTRACT_ID,
    FINDING_SCHEMA_VERSION,
    FindingIdentitySeed,
    GuardFindingPolicy,
    build_finding_id,
    decision_packet_from_finding,
    enrich_probe_hint_contract,
    finding_from_guard_violation,
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
        repo_path="",
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
        repo_path="",
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
    assert packet["rule_summary"] == "Keep the orchestration seam explicit."
    assert "match_evidence" in packet
    assert "rejected_rule_traces" in packet


def test_build_finding_id_is_stable_for_same_inputs() -> None:
    seed = FindingIdentitySeed(
        repo_name="demo-repo",
        repo_path="",
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


def test_finding_id_is_portable_across_checkout_paths() -> None:
    """Finding IDs must not change when the same repo is checked out at
    different filesystem locations.  Using empty ``repo_path`` keeps the
    identity stable; absolute checkout paths would make IDs machine-specific.
    """
    common = dict(
        repo_name="demo-repo",
        repo_path="",
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
    id_stable = build_finding_id(FindingIdentitySeed(**common))

    # Simulates a different checkout location leaking into repo_path.
    common_leaked = {**common, "repo_path": "/Users/alice/repos/demo-repo"}
    id_leaked = build_finding_id(FindingIdentitySeed(**common_leaked))

    # The stable ID should NOT equal the leaked one — this proves that
    # absolute paths contaminate identity and must be avoided.
    assert id_stable != id_leaked


def test_finding_from_guard_violation_code_shape() -> None:
    """Guard violations normalize into FindingRecord with signal_type='guard'."""
    violation = {
        "path": "src/main.py",
        "function_name": "build_report",
        "reason": "crossed_soft_limit",
        "guidance": "Split into focused helpers to stay under the soft limit.",
        "base_lines": 340,
        "current_lines": 380,
        "growth": 40,
    }
    finding = finding_from_guard_violation(
        violation,
        repo_name="demo-repo",
        policy=GuardFindingPolicy(
            guard_command="check_code_shape",
            risk_type="code_shape_violation",
        ),
    )
    payload = finding.to_dict()

    assert payload["schema_version"] == FINDING_SCHEMA_VERSION
    assert payload["contract_id"] == FINDING_CONTRACT_ID
    assert payload["signal_type"] == "guard"
    assert payload["check_id"] == "check_code_shape"
    assert payload["rule_id"] == "check_code_shape"
    assert payload["rule_version"] == GUARD_RULE_VERSION
    assert payload["file_path"] == "src/main.py"
    assert payload["symbol"] == "build_report"
    assert payload["severity"] == "high"
    assert payload["risk_type"] == "code_shape_violation"
    assert payload["source_command"] == "check_code_shape"
    assert payload["finding_id"]
    assert "crossed_soft_limit" in payload["signals"]
    assert any("Split into focused" in s for s in payload["signals"])


def test_finding_from_guard_violation_duplication() -> None:
    """Duplication guard violations include matched duplicate locations."""
    violation = {
        "path": "lib/render.py",
        "function_name": "emit_header",
        "start_line": 42,
        "end_line": 58,
        "line_count": 16,
        "matches": [
            {"path": "lib/export.py", "name": "write_header"},
        ],
    }
    finding = finding_from_guard_violation(
        violation,
        repo_name="demo-repo",
        policy=GuardFindingPolicy(
            guard_command="check_function_duplication",
            risk_type="duplication",
            review_lens="design_quality",
        ),
    )
    payload = finding.to_dict()

    assert payload["signal_type"] == "guard"
    assert payload["check_id"] == "check_function_duplication"
    assert payload["file_path"] == "lib/render.py"
    assert payload["symbol"] == "emit_header"
    assert payload["line"] == 42
    assert payload["end_line"] == 58
    assert any("duplicate:" in s for s in payload["signals"])


def test_guard_and_probe_findings_have_distinct_signal_types() -> None:
    """Guards and probes produce distinct signal_type values so the ledger
    can track enforcement-layer accuracy separately."""
    probe_finding = finding_from_probe_hint(
        {"file": "a.py", "probe": "probe_x", "severity": "medium", "signals": []},
        repo_name="r",
        repo_path="",
        source_command="probe-report",
        source_artifact="probe-report:risk_hints",
    )
    guard_finding = finding_from_guard_violation(
        {"path": "a.py", "reason": "exceeded"},
        repo_name="r",
        policy=GuardFindingPolicy(guard_command="check_x"),
    )
    assert probe_finding.signal_type == "probe"
    assert guard_finding.signal_type == "guard"
    assert probe_finding.finding_id != guard_finding.finding_id
