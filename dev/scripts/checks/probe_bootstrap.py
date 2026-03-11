"""Shared bootstrap for review probes.

Probes are heuristic scanners that detect risk patterns and emit structured
review targets. Unlike hard guards (check_*.py), probes always exit 0 and
produce ``risk_hints`` instead of ``violations``.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from typing import Any

try:
    from check_bootstrap import utc_timestamp
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import utc_timestamp

SEVERITY_LEVELS = ("low", "medium", "high", "critical")


@dataclass
class RiskHint:
    """One risk signal detected by a probe."""

    file: str
    symbol: str
    risk_type: str
    severity: str
    signals: list[str]
    ai_instruction: str
    review_lens: str
    attach_docs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProbeReport:
    """Structured output from a single probe run."""

    command: str
    risk_hints: list[RiskHint] = field(default_factory=list)
    files_scanned: int = 0
    files_with_hints: int = 0
    mode: str = "working-tree"
    since_ref: str | None = None
    head_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "timestamp": utc_timestamp(),
            "ok": True,
            "mode": self.mode,
            "since_ref": self.since_ref,
            "head_ref": self.head_ref,
            "risk_hints": [h.to_dict() for h in self.risk_hints],
            "files_scanned": self.files_scanned,
            "files_with_hints": self.files_with_hints,
        }


def build_probe_parser(description: str) -> argparse.ArgumentParser:
    """Build the standard CLI parser shared by all probes."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument(
        "--head-ref", default="HEAD", help="Head ref used with --since-ref"
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def render_probe_md(report: ProbeReport) -> str:
    """Render a probe report as markdown."""
    data = report.to_dict()
    lines = [f"# {data['command']}", ""]
    lines.append(f"- ok: {data['ok']}")
    lines.append(f"- mode: {data['mode']}")
    lines.append(f"- files_scanned: {data['files_scanned']}")
    lines.append(f"- files_with_hints: {data['files_with_hints']}")
    lines.append(f"- risk_hints: {len(data['risk_hints'])}")
    if data.get("since_ref"):
        lines.append(f"- since_ref: {data['since_ref']}")
    if data.get("head_ref") and data["head_ref"] != "HEAD":
        lines.append(f"- head_ref: {data['head_ref']}")

    if data["risk_hints"]:
        lines.append("")
        lines.append("## Risk Hints")
        for hint in data["risk_hints"]:
            signals_str = "; ".join(hint["signals"])
            lines.append(
                f"- [{hint['severity'].upper()}] `{hint['file']}::{hint['symbol']}` "
                f"({hint['risk_type']}): {signals_str}"
            )
            lines.append(f"  AI: {hint['ai_instruction']}")
    return "\n".join(lines)


def emit_probe_report(report: ProbeReport, *, output_format: str) -> int:
    """Print the probe report and return exit code (always 0)."""
    if output_format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(render_probe_md(report))
    return 0
