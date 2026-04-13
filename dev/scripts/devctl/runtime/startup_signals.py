"""Shared startup quality-signal summaries for bootstrap and startup-context."""

from __future__ import annotations

from pathlib import Path

from .finding_backlog import load_finding_backlog
from .governance_scan import scan_repo_governance_safely
from .startup_signal_io import load_json_file
from .startup_signal_probes import (
    load_code_shape_clusters,
    load_guidance_hotspots,
    load_probe_report_summary,
    load_split_advisor_rows,
)

_INTERESTING_COMMANDS = (
    "check",
    "probe-report",
    "governance-review",
    "context-graph",
    "review-channel",
)


def load_startup_quality_signals(repo_root: Path) -> dict[str, object]:
    """Load bounded startup summaries from recent governance artifacts."""
    signals: dict[str, object] = {}
    probe_report = load_probe_report_summary(repo_root)
    if probe_report:
        signals["probe_report"] = probe_report
    code_shape_clusters = load_code_shape_clusters(repo_root)
    if code_shape_clusters:
        signals["code_shape_clusters"] = code_shape_clusters
    split_advisor = load_split_advisor_rows(repo_root)
    if split_advisor:
        signals["split_advisor"] = split_advisor
    governance_review = _load_governance_review_summary(repo_root)
    if governance_review:
        signals["governance_review"] = governance_review
    finding_backlog = _load_finding_backlog_summary(repo_root)
    if finding_backlog:
        signals["finding_backlog"] = finding_backlog
    guidance_hotspots = load_guidance_hotspots(repo_root)
    if guidance_hotspots:
        signals["guidance_hotspots"] = guidance_hotspots
    watchdog = _load_watchdog_summary(repo_root)
    if watchdog:
        signals["watchdog"] = watchdog
    command_reliability = _load_command_reliability_summary(repo_root)
    if command_reliability:
        signals["command_reliability"] = command_reliability
    return signals


def _load_governance_review_summary(repo_root: Path) -> dict[str, object] | None:
    backlog = load_finding_backlog(
        repo_root=repo_root,
        governance=scan_repo_governance_safely(repo_root),
    )
    payload = _load_json(
        repo_root / "dev" / "reports" / "governance" / "latest" / "review_summary.json"
    )
    stats = payload.get("stats") if isinstance(payload, dict) else None
    if not isinstance(stats, dict) and not backlog.total_findings:
        return None
    response: dict[str, object] = {}
    response["generated_at_utc"] = payload.get("generated_at_utc")
    response["total_findings"] = (
        stats.get("total_findings") if isinstance(stats, dict) else backlog.total_findings
    )
    response["open_finding_count"] = (
        stats.get("open_finding_count")
        if isinstance(stats, dict)
        else len(backlog.open_rows)
    )
    response["fixed_count"] = stats.get("fixed_count") if isinstance(stats, dict) else 0
    response["cleanup_rate_pct"] = (
        stats.get("cleanup_rate_pct") if isinstance(stats, dict) else 0
    )
    response["open_by_severity"] = backlog.severity_counts_dict()
    return response


def _load_finding_backlog_summary(repo_root: Path) -> dict[str, object] | None:
    backlog = load_finding_backlog(
        repo_root=repo_root,
        governance=scan_repo_governance_safely(repo_root),
    )
    if not backlog.total_findings:
        return None
    top_open_findings = [
        {
            "finding_id": finding.finding_id,
            "check_id": finding.check_id,
            "severity": finding.severity,
            "file_path": finding.file_path,
        }
        for finding in backlog.open_findings[:5]
    ]
    return {
        "log_path": backlog.log_path,
        "total_findings": backlog.total_findings,
        "open_finding_count": len(backlog.open_rows),
        "open_by_severity": backlog.severity_counts_dict(),
        "top_open_findings": top_open_findings,
    }


def _load_watchdog_summary(repo_root: Path) -> dict[str, object] | None:
    payload = _load_json(
        repo_root / "dev" / "reports" / "data_science" / "latest" / "summary.json"
    )
    watchdog = payload.get("watchdog_stats") if isinstance(payload, dict) else None
    if not isinstance(watchdog, dict):
        return None
    families = watchdog.get("guard_families")
    top_family = families[0] if isinstance(families, list) and families else None
    return {
        "generated_at": payload.get("generated_at"),
        "total_episodes": watchdog.get("total_episodes"),
        "success_rate_pct": watchdog.get("success_rate_pct"),
        "false_positive_rate_pct": watchdog.get("false_positive_rate_pct"),
        "top_guard_family": (
            top_family.get("guard_family") if isinstance(top_family, dict) else None
        ),
    }


def _load_command_reliability_summary(repo_root: Path) -> dict[str, object] | None:
    payload = _load_json(
        repo_root / "dev" / "reports" / "data_science" / "latest" / "summary.json"
    )
    event_stats = payload.get("event_stats") if isinstance(payload, dict) else None
    if not isinstance(event_stats, dict):
        return None
    rows = event_stats.get("commands")
    commands: list[dict[str, object]] = []
    if isinstance(rows, list):
        selected = [
            row
            for row in rows
            if isinstance(row, dict)
            and str(row.get("command") or "").strip() in _INTERESTING_COMMANDS
        ]
        order = {name: index for index, name in enumerate(_INTERESTING_COMMANDS)}
        selected.sort(key=lambda row: order.get(str(row.get("command")), len(order)))
        commands = [
            {
                "command": row.get("command"),
                "success_rate_pct": row.get("success_rate_pct"),
                "avg_duration_seconds": row.get("avg_duration_seconds"),
            }
            for row in selected[:4]
        ]
    return {
        "generated_at": payload.get("generated_at"),
        "total_events": event_stats.get("total_events"),
        "success_rate_pct": event_stats.get("success_rate_pct"),
        "p95_duration_seconds": event_stats.get("p95_duration_seconds"),
        "commands": commands,
    }


def _load_json(path: Path):
    return load_json_file(path)
