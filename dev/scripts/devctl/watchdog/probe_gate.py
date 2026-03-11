"""Probe quality gate — runs review probes and returns a structured summary.

Used by autonomy-loop rounds (per-round quality check) and swarm post-audit
(aggregate probe health across parallel agents).  Runs the probe suite as a
subprocess so it stays decoupled from the probe implementation.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..config import REPO_ROOT

PROBE_RUNNER = REPO_ROOT / "dev" / "scripts" / "checks" / "run_probe_report.py"
ALLOWLIST_PATH = REPO_ROOT / ".probe-allowlist.json"


@dataclass(frozen=True)
class ProbeScanResult:
    """Summary of one probe scan invocation."""

    total_findings: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    files_affected: int = 0
    files_scanned: int = 0
    probes_run: int = 0
    risk: str = "low"
    findings: tuple[dict[str, str], ...] = ()
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.findings:
            payload["findings"] = list(self.findings)
        else:
            payload.pop("findings", None)
        if not self.error:
            payload.pop("error", None)
        return payload


def run_probe_scan(*, timeout_seconds: int = 120) -> ProbeScanResult:
    """Run the full probe suite and return a structured summary.

    Returns a zero-finding result (not an error) when the probe runner is
    missing — this keeps the gate fail-open so missing probes never block
    autonomy loops.
    """
    if not PROBE_RUNNER.exists():
        return ProbeScanResult(error="probe runner not found")

    try:
        result = subprocess.run(
            [sys.executable, str(PROBE_RUNNER), "--format", "json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ProbeScanResult(error="probe scan timed out")
    except OSError as exc:
        return ProbeScanResult(error=f"probe scan failed: {exc}")

    if not result.stdout.strip():
        return ProbeScanResult(error="probe scan produced no output")

    try:
        reports = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return ProbeScanResult(error=f"probe output parse error: {exc}")
    if not ALLOWLIST_PATH.exists():
        allowlist_entries: list[dict[str, str]] = []
    else:
        try:
            allowlist_data = json.loads(ALLOWLIST_PATH.read_text())
            allowlist_entries = allowlist_data.get("entries", []) + allowlist_data.get(
                "suppressed", []
            )
        except (json.JSONDecodeError, OSError):
            allowlist_entries = []

    all_hints: list[dict[str, str]] = []
    files_scanned = 0
    files_with_findings: set[str] = set()
    severity_counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0}

    for report in reports:
        files_scanned += int(report.get("files_scanned", 0))
        probe_name = report.get("command", "unknown")
        for hint in report.get("risk_hints", []):
            allowlisted = any(
                entry.get("file") == hint.get("file")
                and entry.get("symbol") == hint.get("symbol")
                for entry in allowlist_entries
            )
            if allowlisted:
                continue
            severity = hint.get("severity", "medium")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            files_with_findings.add(hint.get("file", ""))
            all_hints.append(
                {
                    "file": hint.get("file", ""),
                    "symbol": hint.get("symbol", ""),
                    "severity": severity,
                    "probe": hint.get("probe", probe_name),
                    "signal": (hint.get("signals") or [""])[0],
                }
            )

    high_count = severity_counts["high"]
    total_findings = high_count + severity_counts["medium"] + severity_counts["low"]
    if high_count > 0:
        risk = "high"
    elif total_findings > 10:
        risk = "medium"
    else:
        risk = "low"

    return ProbeScanResult(
        total_findings=total_findings,
        high_count=high_count,
        medium_count=severity_counts["medium"],
        low_count=severity_counts["low"],
        files_affected=len(files_with_findings),
        files_scanned=files_scanned,
        probes_run=len(reports),
        risk=risk,
        findings=tuple(all_hints),
    )


@dataclass(frozen=True)
class ProbeAggregation:
    """Swarm-level summary rolled up from multiple per-round probe scans."""

    total_scans: int = 0
    total_findings: int = 0
    total_high: int = 0
    clean_scans: int = 0
    probe_pass_rate_pct: float = 100.0
    risk: str = "low"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def aggregate_probe_scans(scans: list[dict[str, Any]]) -> ProbeAggregation:
    """Aggregate multiple ProbeScanResult dicts into a swarm-level summary.

    Used by post-audit to roll up probe health across all agents/rounds.
    """
    total_scans = len(scans)
    if total_scans == 0:
        return ProbeAggregation()

    total_findings = sum(s.get("total_findings", 0) for s in scans)
    total_high = sum(s.get("high_count", 0) for s in scans)
    clean_scans = sum(1 for s in scans if s.get("high_count", 0) == 0)
    pass_rate = round(clean_scans / total_scans * 100, 1)

    if total_high > 0:
        risk = "high"
    elif total_findings > total_scans * 5:
        risk = "medium"
    else:
        risk = "low"

    return ProbeAggregation(
        total_scans=total_scans,
        total_findings=total_findings,
        total_high=total_high,
        clean_scans=clean_scans,
        probe_pass_rate_pct=pass_rate,
        risk=risk,
    )
