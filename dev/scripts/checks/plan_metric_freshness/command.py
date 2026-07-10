"""Validate plan-cited metric counts against live repository counts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

try:
    from check_bootstrap import REPO_ROOT, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, utc_timestamp


@dataclass(frozen=True)
class MetricDefinition:
    metric_id: str
    label: str
    token: str
    roots: tuple[str, ...]
    threshold_ratio: float = 0.10


@dataclass(frozen=True)
class MetricClaim:
    metric_id: str
    source_path: str
    line: int
    cited_count: int
    text: str


DEFAULT_METRICS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        metric_id="P140",
        label="from-mapping occurrences",
        token="_from" "_mapping",
        roots=("dev/scripts",),
    ),
)

DEFAULT_PLAN_SOURCES: tuple[str, ...] = (
    "dev/active/MASTER_PLAN.md",
    "dev/state/plan_index.jsonl",
)


def count_token_occurrences(
    repo_root: Path,
    definition: MetricDefinition,
    *,
    excluded_paths: set[str] | None = None,
) -> int:
    total = 0
    exclusions = excluded_paths or set()
    for root in definition.roots:
        root_path = repo_root / root
        if not root_path.exists():
            continue
        paths = [root_path] if root_path.is_file() else root_path.rglob("*")
        for path in paths:
            if not path.is_file():
                continue
            rel = _relative_path(repo_root, path)
            if rel in exclusions or "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            total += text.count(definition.token)
    return total


def collect_metric_claims(
    repo_root: Path,
    metric_ids: Sequence[str],
    *,
    plan_sources: Sequence[str] = DEFAULT_PLAN_SOURCES,
) -> list[MetricClaim]:
    claims: list[MetricClaim] = []
    for source in plan_sources:
        path = repo_root / source
        if not path.exists():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for metric_id in metric_ids:
                claims.extend(_claims_from_line(source, line_number, line, metric_id))
    return claims


def build_report(
    repo_root: Path = REPO_ROOT,
    *,
    metrics: Sequence[MetricDefinition] = DEFAULT_METRICS,
    plan_sources: Sequence[str] = DEFAULT_PLAN_SOURCES,
) -> dict:
    metric_by_id = {definition.metric_id: definition for definition in metrics}
    excluded_paths = {
        "dev/scripts/checks/plan_metric_freshness/command.py",
        "dev/scripts/devctl/tests/checks/test_check_plan_metric_freshness.py",
    }
    actual_counts = {
        metric_id: count_token_occurrences(
            repo_root,
            definition,
            excluded_paths=excluded_paths,
        )
        for metric_id, definition in metric_by_id.items()
    }
    claims = collect_metric_claims(
        repo_root,
        tuple(metric_by_id),
        plan_sources=plan_sources,
    )
    rows: list[dict] = []
    violations: list[dict] = []
    for claim in claims:
        definition = metric_by_id[claim.metric_id]
        actual = actual_counts[claim.metric_id]
        delta = abs(actual - claim.cited_count)
        ratio = (delta / actual) if actual else (1.0 if claim.cited_count else 0.0)
        row = {
            "metric_id": claim.metric_id,
            "label": definition.label,
            "source_path": claim.source_path,
            "line": claim.line,
            "cited_count": claim.cited_count,
            "actual_count": actual,
            "delta": delta,
            "drift_ratio": ratio,
            "threshold_ratio": definition.threshold_ratio,
            "ok": ratio <= definition.threshold_ratio,
            "text": claim.text,
        }
        rows.append(row)
        if not row["ok"]:
            violations.append(row)
    report = {
        "command": "check_plan_metric_freshness",
        "timestamp": utc_timestamp(),
        "ok": len(violations) == 0,
        "metric_count": len(metrics),
        "claim_count": len(rows),
        "violations": violations,
        "metrics": [
            {
                "metric_id": definition.metric_id,
                "label": definition.label,
                "roots": list(definition.roots),
                "actual_count": actual_counts[definition.metric_id],
                "threshold_ratio": definition.threshold_ratio,
            }
            for definition in metrics
        ],
        "claims": rows,
    }
    return report


def render_markdown(report: dict) -> str:
    lines = ["# check_plan_metric_freshness", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- metric_count: {report['metric_count']}")
    lines.append(f"- claim_count: {report['claim_count']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report["metrics"]:
        lines.extend(["", "## Metrics"])
        for metric in report["metrics"]:
            roots = ", ".join(f"`{root}`" for root in metric["roots"])
            lines.append(
                f"- `{metric['metric_id']}` {metric['label']}: "
                f"actual={metric['actual_count']} roots={roots}"
            )
    if report["violations"]:
        lines.extend(["", "## Violations"])
        for violation in report["violations"]:
            percent = violation["drift_ratio"] * 100
            threshold = violation["threshold_ratio"] * 100
            lines.append(
                f"- `{violation['metric_id']}` at "
                f"`{violation['source_path']}:{violation['line']}` cited "
                f"{violation['cited_count']} but live count is "
                f"{violation['actual_count']} ({percent:.1f}% drift; "
                f"threshold {threshold:.1f}%)."
            )
    return "\n".join(lines)


def _claims_from_line(
    source_path: str,
    line_number: int,
    line: str,
    metric_id: str,
) -> list[MetricClaim]:
    if metric_id not in line:
        return []
    if _is_retracted_metric_line(line):
        return []
    claims: list[MetricClaim] = []
    metric_pattern = re.compile(
        rf"\b{re.escape(metric_id)}\b[^\n]{{0,80}}?(?:TRUE\s+COUNT|COUNT|=)\s*=?\s*(\d+)",
        re.IGNORECASE,
    )
    for match in metric_pattern.finditer(line):
        claims.append(
            MetricClaim(
                metric_id=metric_id,
                source_path=source_path,
                line=line_number,
                cited_count=int(match.group(1)),
                text=line.strip(),
            )
        )
    return claims


def _is_retracted_metric_line(line: str) -> bool:
    lowered = line.lower()
    if "true count" in lowered:
        return False
    return "claim wrong" in lowered or "falsified" in lowered


def _relative_path(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
