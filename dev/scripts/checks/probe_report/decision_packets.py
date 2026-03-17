"""Allowlist loading and decision-packet helpers for probe reports."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .contracts import (
    PROBE_ALLOWLIST_CONTRACT_ID,
    PROBE_ALLOWLIST_SCHEMA_VERSION,
    DecisionPacketPolicy,
    DecisionPacketRecord,
    decision_packet_from_finding,
    enrich_probe_hint_contract,
)

ALLOWLIST_FILENAME = ".probe-allowlist.json"
DECISION_MODES = frozenset({"auto_apply", "recommend_only", "approval_required"})
DEFAULT_DECISION_VALIDATION_PLAN = (
    "Run `python3 dev/scripts/devctl.py check --profile ci` after applying the selected option.",
    "Run `python3 dev/scripts/devctl.py probe-report --format md` to refresh decision packets and hotspot ordering.",
)

DecisionPacket = DecisionPacketRecord


def _normalize_decision_mode(raw_mode: Any) -> str:
    mode = str(raw_mode or "recommend_only").strip().lower()
    if mode in DECISION_MODES:
        return mode
    return "recommend_only"


def _normalize_string_tuple(raw_value: Any) -> tuple[str, ...]:
    if not isinstance(raw_value, list):
        return ()
    values: list[str] = []
    for item in raw_value:
        text = str(item).strip()
        if text:
            values.append(text)
    return tuple(values)


@dataclass(frozen=True)
class AllowlistEntry:
    """One entry in the probe allowlist file."""

    file: str
    symbol: str
    probe: str
    disposition: str = "suppressed"
    reason: str = ""
    research_instruction: str = ""
    decision_mode: str = "recommend_only"
    precedent: str = ""
    invariants: tuple[str, ...] = ()
    validation_plan: tuple[str, ...] = ()

    @classmethod
    def from_hint(cls, hint: dict[str, Any]) -> AllowlistEntry:
        return cls(
            file=str(hint.get("file") or hint.get("file_path") or ""),
            symbol=str(hint.get("symbol") or ""),
            probe=str(hint.get("probe") or ""),
        )

    def matches(self, hint: dict[str, Any]) -> bool:
        if self.file != hint.get("file") or self.symbol != hint.get("symbol"):
            return False
        probe_name = str(hint.get("probe") or "").strip()
        return not self.probe or self.probe == probe_name

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "file": self.file,
            "symbol": self.symbol,
            "probe": self.probe,
            "disposition": self.disposition,
        }
        if self.reason:
            payload["reason"] = self.reason
        if self.research_instruction:
            payload["research_instruction"] = self.research_instruction
        if self.decision_mode != "recommend_only":
            payload["decision_mode"] = self.decision_mode
        if self.precedent:
            payload["precedent"] = self.precedent
        if self.invariants:
            payload["invariants"] = list(self.invariants)
        if self.validation_plan:
            payload["validation_plan"] = list(self.validation_plan)
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AllowlistEntry:
        return cls(
            file=data.get("file", ""),
            symbol=data.get("symbol", ""),
            probe=data.get("probe", ""),
            disposition=data.get("disposition", "suppressed"),
            reason=data.get("reason", ""),
            research_instruction=data.get("research_instruction", ""),
            decision_mode=_normalize_decision_mode(data.get("decision_mode")),
            precedent=str(data.get("precedent", "") or ""),
            invariants=_normalize_string_tuple(data.get("invariants")),
            validation_plan=_normalize_string_tuple(data.get("validation_plan")),
        )


@dataclass(frozen=True)
class FilteredFindings:
    """Result of splitting probe findings against the allowlist."""

    active: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    suppressed: list[tuple[dict[str, Any], AllowlistEntry]] = field(default_factory=list)
    design_decisions: list[tuple[dict[str, Any], AllowlistEntry]] = field(default_factory=list)


def build_design_decision_packet(
    *,
    hint: dict[str, Any],
    entry: AllowlistEntry,
) -> dict[str, Any]:
    finding = hint
    if "finding_id" not in finding:
        finding = enrich_probe_hint_contract(hint=hint, repo_name="unknown-repo")
    packet = decision_packet_from_finding(
        finding,
        policy=DecisionPacketPolicy(
            decision_mode=entry.decision_mode,
            rationale=entry.reason or "Intentional design boundary; review the trade-offs before changing it.",
            research_instruction=entry.research_instruction,
            precedent=entry.precedent,
            invariants=entry.invariants,
            validation_plan=entry.validation_plan or DEFAULT_DECISION_VALIDATION_PLAN,
        ),
    )
    return packet.to_dict()


def build_design_decision_packets(
    *,
    hints_by_file: dict[str, list[dict[str, Any]]],
    allowlist: list[AllowlistEntry],
) -> list[dict[str, Any]]:
    findings = filter_findings(hints_by_file, allowlist)
    severity_order = {"high": 0, "medium": 1, "low": 2}
    packets = [
        build_design_decision_packet(hint=hint, entry=entry)
        for hint, entry in findings.design_decisions
    ]
    packets.sort(
        key=lambda row: (
            severity_order.get(str(row.get("severity") or "low"), 3),
            str(row.get("decision_mode") or "recommend_only"),
            str(row.get("file") or ""),
            str(row.get("symbol") or ""),
        )
    )
    return packets


def load_allowlist(repo_root: Path | None) -> list[AllowlistEntry]:
    """Load the probe allowlist from the repo root."""
    if repo_root is None:
        return []
    allowlist_path = repo_root / ALLOWLIST_FILENAME
    if not allowlist_path.exists():
        return []
    try:
        data = json.loads(allowlist_path.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, dict):
        raise ValueError(f"{ALLOWLIST_FILENAME} must contain a JSON object")
    schema_version = data.get("schema_version")
    if schema_version not in (None, PROBE_ALLOWLIST_SCHEMA_VERSION):
        raise ValueError(
            f"{ALLOWLIST_FILENAME} schema_version must be {PROBE_ALLOWLIST_SCHEMA_VERSION}, "
            f"found {schema_version!r}"
        )
    contract_id = str(data.get("contract_id") or "").strip()
    if contract_id and contract_id != PROBE_ALLOWLIST_CONTRACT_ID:
        raise ValueError(
            f"{ALLOWLIST_FILENAME} contract_id must be {PROBE_ALLOWLIST_CONTRACT_ID!r}, "
            f"found {contract_id!r}"
        )
    raw_entries = data.get("entries", []) + data.get("suppressed", [])
    return [AllowlistEntry.from_dict(entry) for entry in raw_entries]


def filter_findings(
    hints_by_file: dict[str, list[dict[str, Any]]],
    allowlist: list[AllowlistEntry],
) -> FilteredFindings:
    """Split hints into active, suppressed, and design-decision buckets."""
    active: dict[str, list[dict[str, Any]]] = {}
    suppressed: list[tuple[dict[str, Any], AllowlistEntry]] = []
    design_decisions: list[tuple[dict[str, Any], AllowlistEntry]] = []

    for file_path, hints in hints_by_file.items():
        active_hints: list[dict[str, Any]] = []
        for hint in hints:
            matched = next((entry for entry in allowlist if entry.matches(hint)), None)
            if matched is None:
                active_hints.append(hint)
                continue
            if matched.disposition == "design_decision":
                design_decisions.append((hint, matched))
            else:
                suppressed.append((hint, matched))
        if active_hints:
            active[file_path] = active_hints

    return FilteredFindings(
        active=active,
        suppressed=suppressed,
        design_decisions=design_decisions,
    )
