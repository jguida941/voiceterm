"""Shared explainability payloads and records for finding contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


class RuleMatchEvidencePayload(TypedDict, total=False):
    rule_id: str
    summary: str
    evidence: list[str]


class RejectedRuleTracePayload(TypedDict, total=False):
    rule_id: str
    summary: str
    rejected_because: str
    evidence: list[str]


@dataclass(frozen=True, slots=True)
class RuleMatchEvidenceRecord:
    """One plain-language explanation for why a rule matched."""

    rule_id: str
    summary: str
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> RuleMatchEvidencePayload:
        payload: RuleMatchEvidencePayload = {}
        payload["rule_id"] = self.rule_id
        payload["summary"] = self.summary
        payload["evidence"] = list(self.evidence)
        return payload


@dataclass(frozen=True, slots=True)
class RejectedRuleTraceRecord:
    """One plain-language explanation for why a competing rule was rejected."""

    rule_id: str
    summary: str
    rejected_because: str
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> RejectedRuleTracePayload:
        payload: RejectedRuleTracePayload = {}
        payload["rule_id"] = self.rule_id
        payload["summary"] = self.summary
        payload["rejected_because"] = self.rejected_because
        payload["evidence"] = list(self.evidence)
        return payload


__all__ = [
    "RejectedRuleTracePayload",
    "RejectedRuleTraceRecord",
    "RuleMatchEvidencePayload",
    "RuleMatchEvidenceRecord",
]
