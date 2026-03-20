"""Shared finding and packet contracts for governance evidence surfaces."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypedDict

from .value_coercion import coerce_int, coerce_string, coerce_string_items

FINDING_CONTRACT_ID, FINDING_SCHEMA_VERSION = "Finding", 1
DECISION_PACKET_CONTRACT_ID, DECISION_PACKET_SCHEMA_VERSION = "DecisionPacket", 1
PROBE_REPORT_CONTRACT_ID, PROBE_REPORT_SCHEMA_VERSION = "ProbeReport", 1
PROBE_REVIEW_PACKET_CONTRACT_ID, PROBE_REVIEW_PACKET_SCHEMA_VERSION = "ReviewPacket", 1
PROBE_REVIEW_TARGETS_CONTRACT_ID, PROBE_REVIEW_TARGETS_SCHEMA_VERSION = "ReviewTargets", 1
PROBE_TOPOLOGY_CONTRACT_ID, PROBE_TOPOLOGY_SCHEMA_VERSION = "FileTopology", 1
PROBE_ALLOWLIST_CONTRACT_ID, PROBE_ALLOWLIST_SCHEMA_VERSION = "ProbeAllowlist", 1
PROBE_RULE_VERSION = 1
REVIEW_PACKET_CONTRACT_ID, REVIEW_PACKET_SCHEMA_VERSION = (
    PROBE_REVIEW_PACKET_CONTRACT_ID,
    PROBE_REVIEW_PACKET_SCHEMA_VERSION,
)
REVIEW_TARGETS_CONTRACT_ID, REVIEW_TARGETS_SCHEMA_VERSION = (
    PROBE_REVIEW_TARGETS_CONTRACT_ID,
    PROBE_REVIEW_TARGETS_SCHEMA_VERSION,
)


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


@dataclass(frozen=True, slots=True)
class FindingIdentitySeed:
    """Stable identity inputs for one governance finding.

    repo_path must stay repo-relative (or empty for repo root), never absolute.
    """

    repo_name: str
    repo_path: str
    signal_type: str
    check_id: str
    file_path: str
    symbol: str = ""
    line: int | None = None
    end_line: int | None = None
    risk_type: str = ""
    review_lens: str = ""
    signals: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DecisionPacketPolicy:
    """Policy inputs for projecting a finding into a decision packet."""

    decision_mode: str
    rationale: str
    research_instruction: str = ""
    precedent: str = ""
    invariants: tuple[str, ...] = ()
    validation_plan: tuple[str, ...] = ()


def _positive_int(value: object) -> int | None:
    number = coerce_int(value)
    return number if number > 0 else None


def build_finding_id(seed: FindingIdentitySeed) -> str:
    """Build one deterministic finding identifier for a governance signal."""
    raw = "::".join(
        [
            seed.repo_name,
            seed.repo_path,
            seed.signal_type,
            seed.check_id,
            seed.file_path,
            seed.symbol,
            str(seed.line or ""),
            str(seed.end_line or ""),
            seed.risk_type,
            seed.review_lens,
            "|".join(seed.signals),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class FindingRecord:
    """Canonical evidence row for one governance finding."""

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
    symbol: str = ""
    line: int | None = None
    end_line: int | None = None
    severity: str = "medium"
    risk_type: str = ""
    review_lens: str = ""
    ai_instruction: str = ""
    signals: tuple[str, ...] = ()
    source_command: str = ""
    source_artifact: str = ""

    def to_dict(self) -> FindingPayload:
        payload: FindingPayload = {}
        payload["schema_version"] = self.schema_version
        payload["contract_id"] = self.contract_id
        payload["finding_id"] = self.finding_id
        payload["signal_type"] = self.signal_type
        payload["check_id"] = self.check_id
        payload["rule_id"] = self.rule_id
        payload["rule_version"] = self.rule_version
        payload["repo_name"] = self.repo_name
        payload["repo_path"] = self.repo_path
        payload["file_path"] = self.file_path
        payload["file"] = self.file_path
        payload["probe"] = self.check_id
        payload["symbol"] = self.symbol
        payload["severity"] = self.severity
        payload["risk_type"] = self.risk_type
        payload["review_lens"] = self.review_lens
        payload["ai_instruction"] = self.ai_instruction
        payload["signals"] = list(self.signals)
        payload["source_command"] = self.source_command
        payload["source_artifact"] = self.source_artifact
        if self.line is not None:
            payload["line"] = self.line
        if self.end_line is not None:
            payload["end_line"] = self.end_line
        return payload


@dataclass(frozen=True, slots=True)
class DecisionPacketRecord:
    """Typed packet for an intentional design decision over one finding."""

    schema_version: int
    contract_id: str
    finding_id: str
    check_id: str
    rule_id: str
    rule_version: int
    file_path: str
    symbol: str
    severity: str
    review_lens: str
    risk_type: str
    decision_mode: str
    rationale: str
    ai_instruction: str
    research_instruction: str
    source_artifact: str
    precedent: str = ""
    invariants: tuple[str, ...] = ()
    validation_plan: tuple[str, ...] = ()
    signals: tuple[str, ...] = ()

    def to_dict(self) -> DecisionPacketPayload:
        payload: DecisionPacketPayload = {}
        payload["schema_version"] = self.schema_version
        payload["contract_id"] = self.contract_id
        payload["finding_id"] = self.finding_id
        payload["check_id"] = self.check_id
        payload["rule_id"] = self.rule_id
        payload["rule_version"] = self.rule_version
        payload["file_path"] = self.file_path
        payload["file"] = self.file_path
        payload["probe"] = self.check_id
        payload["symbol"] = self.symbol
        payload["severity"] = self.severity
        payload["review_lens"] = self.review_lens
        payload["risk_type"] = self.risk_type
        payload["decision_mode"] = self.decision_mode
        payload["rationale"] = self.rationale
        payload["ai_instruction"] = self.ai_instruction
        payload["research_instruction"] = self.research_instruction
        payload["source_artifact"] = self.source_artifact
        payload["precedent"] = self.precedent
        payload["invariants"] = list(self.invariants)
        payload["validation_plan"] = list(self.validation_plan)
        payload["signals"] = list(self.signals)
        return payload


def finding_from_probe_hint(
    hint: Mapping[str, object],
    *,
    repo_name: str,
    repo_path: str,
    source_command: str,
    source_artifact: str,
) -> FindingRecord:
    """Normalize one probe hint into the canonical finding contract."""
    file_path = coerce_string(hint.get("file") or hint.get("file_path"))
    symbol = coerce_string(hint.get("symbol"))
    check_id = coerce_string(hint.get("check_id") or hint.get("probe"))
    risk_type = coerce_string(hint.get("risk_type"))
    review_lens = coerce_string(hint.get("review_lens"))
    signals = coerce_string_items(hint.get("signals"))
    line = _positive_int(hint.get("line") or hint.get("start_line"))
    end_line = _positive_int(hint.get("end_line"))
    return FindingRecord(
        schema_version=FINDING_SCHEMA_VERSION,
        contract_id=FINDING_CONTRACT_ID,
        finding_id=build_finding_id(
            FindingIdentitySeed(
                repo_name=repo_name,
                repo_path=repo_path,
                signal_type="probe",
                check_id=check_id,
                file_path=file_path,
                symbol=symbol,
                line=line,
                end_line=end_line,
                risk_type=risk_type,
                review_lens=review_lens,
                signals=signals,
            )
        ),
        signal_type="probe",
        check_id=check_id,
        rule_id=check_id,
        rule_version=PROBE_RULE_VERSION,
        repo_name=repo_name,
        repo_path=repo_path,
        file_path=file_path,
        symbol=symbol,
        line=line,
        end_line=end_line,
        severity=coerce_string(hint.get("severity")) or "medium",
        risk_type=risk_type,
        review_lens=review_lens,
        ai_instruction=coerce_string(hint.get("ai_instruction")),
        signals=signals,
        source_command=source_command,
        source_artifact=source_artifact,
    )


def decision_packet_from_finding(
    finding: Mapping[str, object],
    *,
    policy: DecisionPacketPolicy,
) -> DecisionPacketRecord:
    """Project one canonical finding into a typed design-decision packet."""
    return DecisionPacketRecord(
        schema_version=DECISION_PACKET_SCHEMA_VERSION,
        contract_id=DECISION_PACKET_CONTRACT_ID,
        finding_id=coerce_string(finding.get("finding_id")),
        check_id=coerce_string(finding.get("check_id") or finding.get("probe")),
        rule_id=coerce_string(finding.get("rule_id") or finding.get("check_id") or finding.get("probe")),
        rule_version=coerce_int(finding.get("rule_version")) or PROBE_RULE_VERSION,
        file_path=coerce_string(finding.get("file_path") or finding.get("file")),
        symbol=coerce_string(finding.get("symbol")),
        severity=coerce_string(finding.get("severity")) or "medium",
        review_lens=coerce_string(finding.get("review_lens")) or "design_quality",
        risk_type=coerce_string(finding.get("risk_type")) or "design_decision",
        decision_mode=policy.decision_mode,
        rationale=policy.rationale,
        ai_instruction=coerce_string(finding.get("ai_instruction")),
        research_instruction=policy.research_instruction,
        source_artifact=coerce_string(finding.get("source_artifact")) or "probe-report:risk_hints",
        precedent=policy.precedent,
        invariants=policy.invariants,
        validation_plan=policy.validation_plan,
        signals=coerce_string_items(finding.get("signals")),
    )


def enrich_probe_hint_contract(
    *,
    hint: Mapping[str, object],
    repo_name: str,
    repo_path: str = "",
    source_command: str = "probe-report",
    source_artifact: str = "probe-report:risk_hints",
) -> dict[str, object]:
    """Backward-compatible wrapper that enriches a probe hint into a finding dict."""
    return finding_from_probe_hint(
        hint,
        repo_name=repo_name or "unknown-repo",
        repo_path=repo_path,
        source_command=source_command,
        source_artifact=source_artifact,
    ).to_dict()
