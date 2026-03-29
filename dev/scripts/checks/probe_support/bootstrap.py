"""Shared bootstrap for review probes.

Probes are heuristic scanners that detect risk patterns and emit structured
review targets. Unlike hard guards (check_*.py), probes always exit 0 and
produce ``risk_hints`` instead of ``violations``.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

try:
    from check_bootstrap import utc_timestamp
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import utc_timestamp

SEVERITY_LEVELS = ("low", "medium", "high", "critical")


class _PythonCallSiteCounter(ast.NodeVisitor):
    """Collect Python call-site counts by symbol name."""

    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()

    def visit_Call(self, node: ast.Call) -> None:
        symbol: str | None = None
        if isinstance(node.func, ast.Name):
            symbol = node.func.id
        elif isinstance(node.func, ast.Attribute):
            symbol = node.func.attr
        if symbol:
            self.counts[symbol] += 1
        self.generic_visit(node)


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
    parser.add_argument("--head-ref", default="HEAD", help="Head ref used with --since-ref")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def load_current_text_by_path(
    *,
    changed_paths: list[Path],
    since_ref: str | None,
    head_ref: str,
    read_text_from_ref: Callable[[Path, str], str | None],
    read_text_from_worktree: Callable[[Path], str | None],
    include_path: Callable[[Path], bool] | None = None,
) -> dict[str, str]:
    """Load current text for the changed file set."""
    current_text_by_path: dict[str, str] = {}
    for path in changed_paths:
        if include_path is not None and not include_path(path):
            continue
        if since_ref:
            current_text = read_text_from_ref(path, head_ref)
        else:
            current_text = read_text_from_worktree(path)
        if current_text is None:
            continue
        current_text_by_path[path.as_posix()] = current_text
    return current_text_by_path


def count_python_call_sites_by_symbol(text_by_path: Mapping[str, str]) -> Counter[str]:
    """Count Python call sites across a file corpus by called symbol name."""
    counts: Counter[str] = Counter()
    for text in text_by_path.values():
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        collector = _PythonCallSiteCounter()
        collector.visit(tree)
        counts.update(collector.counts)
    return counts


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
