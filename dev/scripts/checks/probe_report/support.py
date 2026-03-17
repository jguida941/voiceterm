"""Shared support helpers for probe report rendering."""

from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ALLOWLIST_FILENAME = ".probe-allowlist.json"
DECISION_MODES = frozenset({"auto_apply", "recommend_only", "approval_required"})
DEFAULT_DECISION_VALIDATION_PLAN = (
    "Run `python3 dev/scripts/devctl.py check --profile ci` after applying the selected option.",
    "Run `python3 dev/scripts/devctl.py probe-report --format md` to refresh decision packets and hotspot ordering.",
)


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


def extract_source_snippet(
    file_path: str,
    symbol: str,
    repo_root: Path | None,
    *,
    context_lines: int = 3,
) -> str | None:
    """Extract a source code snippet around the named symbol."""
    if repo_root is None:
        return None
    full_path = repo_root / file_path
    if not full_path.exists():
        return None
    try:
        lines = full_path.read_text().splitlines()
    except OSError:
        return None

    target_line = next(
        (
            index
            for index, line in enumerate(lines)
            if f"def {symbol}(" in line or f"class {symbol}" in line or f"fn {symbol}(" in line
        ),
        None,
    )
    if target_line is None:
        return None

    start = max(0, target_line - context_lines)
    end = min(len(lines), target_line + context_lines + 10)
    snippet_lines = []
    for index in range(start, end):
        marker = ">>>" if index == target_line else "   "
        snippet_lines.append(f"{marker} {index + 1:4d} | {lines[index]}")

    lang = "rust" if file_path.endswith(".rs") else "python"
    return f"```{lang}\n" + "\n".join(snippet_lines) + "\n```"


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

    def matches(self, hint: dict[str, Any]) -> bool:
        return self.file == hint.get("file") and self.symbol == hint.get("symbol")

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "file": self.file,
            "symbol": self.symbol,
            "probe": self.probe,
            "disposition": self.disposition,
            "reason": self.reason,
        }
        if self.research_instruction:
            payload["research_instruction"] = self.research_instruction
        if self.disposition == "design_decision" or self.decision_mode != "recommend_only":
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

    @classmethod
    def from_hint(
        cls,
        hint: dict[str, Any],
        *,
        disposition: str = "suppressed",
    ) -> AllowlistEntry:
        return cls(
            file=hint.get("file", ""),
            symbol=hint.get("symbol", ""),
            probe=hint.get("probe", ""),
            disposition=disposition,
            reason="intentional — [add your reason here]",
        )


@dataclass(frozen=True)
class DecisionPacket:
    """Typed decision payload for intentional architecture/design findings."""

    file: str
    symbol: str
    probe: str
    severity: str
    review_lens: str
    risk_type: str
    decision_mode: str
    rationale: str
    ai_instruction: str
    research_instruction: str
    precedent: str
    invariants: tuple[str, ...] = ()
    validation_plan: tuple[str, ...] = ()
    signals: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "file": self.file,
            "symbol": self.symbol,
            "probe": self.probe,
            "severity": self.severity,
            "review_lens": self.review_lens,
            "risk_type": self.risk_type,
            "decision_mode": self.decision_mode,
            "rationale": self.rationale,
            "ai_instruction": self.ai_instruction,
            "research_instruction": self.research_instruction,
            "precedent": self.precedent,
            "invariants": list(self.invariants),
            "validation_plan": list(self.validation_plan),
            "signals": list(self.signals),
        }
        return payload


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
    packet = DecisionPacket(
        file=str(hint.get("file") or ""),
        symbol=str(hint.get("symbol") or ""),
        probe=str(hint.get("probe") or entry.probe),
        severity=str(hint.get("severity") or "medium"),
        review_lens=str(hint.get("review_lens") or "design_quality"),
        risk_type=str(hint.get("risk_type") or "design_decision"),
        decision_mode=entry.decision_mode,
        rationale=entry.reason or "Intentional design boundary; review the trade-offs before changing it.",
        ai_instruction=str(hint.get("ai_instruction") or ""),
        research_instruction=entry.research_instruction,
        precedent=entry.precedent,
        invariants=entry.invariants,
        validation_plan=entry.validation_plan or DEFAULT_DECISION_VALIDATION_PLAN,
        signals=tuple(str(signal) for signal in hint.get("signals", [])),
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


def get_git_diff_for_file(file_path: str, repo_root: Path | None) -> str | None:
    """Get the git diff for a specific file."""
    if repo_root is None:
        return None
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD", "--", file_path],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            check=False,
        )
    except OSError:
        return None
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


@dataclass
class AggregatedReport:
    """Aggregated multi-probe report data."""

    probe_results: list[dict[str, Any]] = field(default_factory=list)
    total_files_scanned: int = 0
    total_hints: int = 0
    hints_by_severity: dict[str, int] = field(default_factory=dict)
    hints_by_file: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


def aggregate_probe_results(reports: list[dict[str, Any]]) -> AggregatedReport:
    """Combine multiple probe JSON reports into a single view."""
    aggregated = AggregatedReport(probe_results=reports)
    severity_counts: dict[str, int] = defaultdict(int)
    file_hints: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for report in reports:
        aggregated.total_files_scanned += int(report.get("files_scanned", 0))
        for hint in report.get("risk_hints", []):
            aggregated.total_hints += 1
            severity = hint.get("severity", "medium")
            severity_counts[severity] += 1
            file_path = hint.get("file", "unknown")
            enriched_hint = {**hint, "probe": report.get("command", "unknown")}
            file_hints[file_path].append(enriched_hint)

    aggregated.hints_by_severity = dict(severity_counts)
    aggregated.hints_by_file = dict(file_hints)
    return aggregated
