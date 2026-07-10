"""Shared helpers for decision-surface explainability records."""

from __future__ import annotations

from .finding_contracts import RejectedRuleTraceRecord, RuleMatchEvidenceRecord


def rule_match_evidence(
    rule_id: str,
    summary: str,
    *evidence: str,
) -> RuleMatchEvidenceRecord:
    """Build one accepted-rule evidence record."""
    return RuleMatchEvidenceRecord(
        rule_id=rule_id,
        summary=summary,
        evidence=tuple(item for item in evidence if item),
    )


def rejected_rule_trace(
    rule_id: str,
    summary: str,
    rejected_because: str,
    *evidence: str,
) -> RejectedRuleTraceRecord:
    """Build one rejected-rule trace record."""
    return RejectedRuleTraceRecord(
        rule_id=rule_id,
        summary=summary,
        rejected_because=rejected_because,
        evidence=tuple(item for item in evidence if item),
    )


__all__ = ["rejected_rule_trace", "rule_match_evidence"]
