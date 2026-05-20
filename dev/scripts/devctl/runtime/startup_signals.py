"""Shared startup quality-signal summaries for bootstrap and startup-context."""

from __future__ import annotations

from pathlib import Path

from .finding_backlog import load_finding_backlog
from .governance_scan import scan_repo_governance_safely
from .startup_signal_contract_connectivity import load_contract_connectivity_summary
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
    contract_connectivity = load_contract_connectivity_summary(repo_root)
    if contract_connectivity:
        signals["contract_connectivity"] = contract_connectivity
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


def compact_startup_quality_signals(
    signals: dict[str, object],
) -> dict[str, object]:
    """Trim quality signals for slim startup/session/bootstrap packets."""
    compact: dict[str, object] = {}
    probe_report = _dict_value(signals.get("probe_report"))
    if probe_report:
        compact["probe_report"] = {
            "generated_at": probe_report.get("generated_at"),
            "files_with_hints": probe_report.get("files_with_hints"),
            "risk_hints": probe_report.get("risk_hints"),
        }
    contract_connectivity = _dict_value(signals.get("contract_connectivity"))
    if contract_connectivity:
        contract_summary = {
            "mode": contract_connectivity.get("mode"),
            "ok": contract_connectivity.get("ok"),
            "severity": contract_connectivity.get("severity"),
            "cache_state": contract_connectivity.get("cache_state"),
        }
        contract_summary.update({
            "cache_generated_at_utc": contract_connectivity.get(
                "cache_generated_at_utc"
            ),
            "worktree_dirty": contract_connectivity.get("worktree_dirty"),
            "contracts_scanned": contract_connectivity.get("contracts_scanned"),
            "current_counts": contract_connectivity.get("current_counts"),
        })
        contract_summary.update({
            "baseline_counts": contract_connectivity.get("baseline_counts"),
            "new_counts": contract_connectivity.get("new_counts"),
            "current_debt_count": contract_connectivity.get("current_debt_count"),
            "baseline_debt_count": contract_connectivity.get("baseline_debt_count"),
            "new_debt_count": contract_connectivity.get("new_debt_count"),
        })
        contract_summary.update({
            "orphan_scope_counts": contract_connectivity.get("orphan_scope_counts"),
            "top_layers": _rows(contract_connectivity.get("top_layers"))[:2],
            "ai_instruction": _clip(
                contract_connectivity.get("ai_instruction"),
                limit=180,
            ),
        })
        compact["contract_connectivity"] = contract_summary
    code_shape_clusters = _rows(signals.get("code_shape_clusters"))
    if code_shape_clusters:
        compact["code_shape_clusters"] = [
            {
                "file": row.get("file"),
                "cluster_count": row.get("cluster_count"),
                "severity": row.get("severity"),
            }
            for row in code_shape_clusters[:1]
        ]
    split_advisor = _rows(signals.get("split_advisor"))
    if split_advisor:
        compact["split_advisor"] = [
            {
                "file": row.get("file"),
                "severity": row.get("severity"),
                "ai_instruction": _clip(row.get("ai_instruction")),
            }
            for row in split_advisor[:1]
        ]
    governance_review = _dict_value(signals.get("governance_review"))
    if governance_review:
        compact["governance_review"] = {
            "generated_at_utc": governance_review.get("generated_at_utc"),
            "total_findings": governance_review.get("total_findings"),
            "open_finding_count": governance_review.get("open_finding_count"),
            "fixed_count": governance_review.get("fixed_count"),
            "cleanup_rate_pct": governance_review.get("cleanup_rate_pct"),
            "open_by_severity": governance_review.get("open_by_severity"),
        }
    guidance_hotspots = _rows(signals.get("guidance_hotspots"))
    if guidance_hotspots:
        compact["guidance_hotspots"] = [
            _compact_guidance_hotspot(guidance_hotspots[0])
        ]
    watchdog = _dict_value(signals.get("watchdog"))
    if watchdog:
        compact["watchdog"] = dict(watchdog)
    command_reliability = _dict_value(signals.get("command_reliability"))
    if command_reliability:
        compact["command_reliability"] = {
            "generated_at": command_reliability.get("generated_at"),
            "total_events": command_reliability.get("total_events"),
            "success_rate_pct": command_reliability.get("success_rate_pct"),
            "p95_duration_seconds": command_reliability.get("p95_duration_seconds"),
            "commands": _rows(command_reliability.get("commands"))[:1],
        }
    return compact


def _compact_guidance_hotspot(row: dict[str, object]) -> dict[str, object]:
    guidance_rows = []
    for guidance in _rows(row.get("guidance"))[:1]:
        guidance_rows.append(
            {
                "probe": guidance.get("probe"),
                "symbol": guidance.get("symbol"),
                "severity": guidance.get("severity"),
                "ai_instruction": _clip(guidance.get("ai_instruction")),
            }
        )
    return {
        "file": row.get("file"),
        "hint_count": row.get("hint_count"),
        "bounded_next_slice": _clip(row.get("bounded_next_slice")),
        "guidance": guidance_rows,
    }


def _dict_value(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [dict(row) for row in value if isinstance(row, dict)]


def _clip(value: object, limit: int = 100) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


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
