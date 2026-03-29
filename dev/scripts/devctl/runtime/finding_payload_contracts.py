"""Typed payload shapes for finding and decision-packet contracts."""

from __future__ import annotations

from typing import TypedDict


class FindingPayload(TypedDict, total=False):
    schema_version: int
    contract_id: str
    finding_id: str
    signal_type: str
    check_id: str
    rule_id: str
    rule_version: int
    repo_name: str
    repo_path: str
    file_path: str
    file: str
    probe: str
    symbol: str
    line: int
    end_line: int
    severity: str
    risk_type: str
    review_lens: str
    ai_instruction: str
    signals: list[str]
    source_command: str
    source_artifact: str


class DecisionPacketPayload(TypedDict, total=False):
    schema_version: int
    contract_id: str
    finding_id: str
    check_id: str
    rule_id: str
    rule_version: int
    file_path: str
    file: str
    probe: str
    symbol: str
    severity: str
    review_lens: str
    risk_type: str
    decision_mode: str
    rationale: str
    ai_instruction: str
    research_instruction: str
    source_artifact: str
    precedent: str
    invariants: list[str]
    validation_plan: list[str]
    signals: list[str]
    rule_summary: str
    match_evidence: list["RuleMatchEvidencePayload"]
    rejected_rule_traces: list["RejectedRuleTracePayload"]


__all__ = ["DecisionPacketPayload", "FindingPayload"]
