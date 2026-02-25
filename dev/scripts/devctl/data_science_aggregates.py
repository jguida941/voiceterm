"""Aggregation helpers for devctl data-science snapshots."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def _safe_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    q = min(max(q, 0.0), 1.0)
    idx = q * (len(ordered) - 1)
    lower = int(idx)
    upper = min(lower + 1, len(ordered) - 1)
    frac = idx - lower
    return ordered[lower] * (1.0 - frac) + ordered[upper] * frac


def build_event_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    if total == 0:
        return {
            "total_events": 0,
            "success_rate_pct": 0.0,
            "avg_duration_seconds": 0.0,
            "p50_duration_seconds": 0.0,
            "p95_duration_seconds": 0.0,
            "commands": [],
            "execution_sources": [],
        }

    success = 0
    durations: list[float] = []
    command_counts: Counter[str] = Counter()
    command_success: Counter[str] = Counter()
    command_duration_sum: defaultdict[str, float] = defaultdict(float)
    source_counts: Counter[str] = Counter()

    for row in rows:
        command = str(row.get("command") or "unknown")
        source = str(row.get("execution_source") or "unknown")
        ok = bool(row.get("success"))
        duration = _safe_float(row.get("duration_seconds"), default=0.0)

        command_counts[command] += 1
        source_counts[source] += 1
        command_duration_sum[command] += duration
        durations.append(duration)
        if ok:
            success += 1
            command_success[command] += 1

    command_rows = []
    for command, count in command_counts.most_common(20):
        ok_count = command_success[command]
        command_rows.append(
            {
                "command": command,
                "count": count,
                "success_rate_pct": round((ok_count / count) * 100.0, 2),
                "avg_duration_seconds": round(command_duration_sum[command] / count, 3),
            }
        )

    source_rows = [
        {"execution_source": key, "count": value}
        for key, value in source_counts.most_common()
    ]

    return {
        "total_events": total,
        "success_rate_pct": round((success / total) * 100.0, 2),
        "avg_duration_seconds": round(sum(durations) / total, 3),
        "p50_duration_seconds": round(_quantile(durations, 0.50), 3),
        "p95_duration_seconds": round(_quantile(durations, 0.95), 3),
        "commands": command_rows,
        "execution_sources": source_rows,
    }


def _normalize_score(value: float, min_value: float, max_value: float) -> float:
    if max_value <= min_value:
        return 1.0
    return (value - min_value) / (max_value - min_value)


def build_agent_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"rows": [], "recommendation": None}

    grouped: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_safe_int(row.get("selected_agents"), default=0)].append(row)

    metric_rows: list[dict[str, Any]] = []
    for selected_agents, group_rows in sorted(grouped.items()):
        if selected_agents <= 0:
            continue
        runs = len(group_rows)
        successes = sum(1 for row in group_rows if bool(row.get("ok")))
        tasks_total = sum(
            _safe_int(row.get("tasks_completed_total"), default=0) for row in group_rows
        )
        elapsed_total = sum(
            _safe_float(row.get("elapsed_seconds"), default=0.0)
            for row in group_rows
            if row.get("elapsed_seconds") is not None
        )
        tasks_per_minute = 0.0
        if elapsed_total > 0:
            tasks_per_minute = tasks_total / (elapsed_total / 60.0)
        tasks_per_agent_avg = (tasks_total / runs) / selected_agents if runs else 0.0
        metric_rows.append(
            {
                "selected_agents": selected_agents,
                "runs": runs,
                "success_rate_pct": round((successes / runs) * 100.0, 2) if runs else 0.0,
                "avg_tasks_completed": round(tasks_total / runs, 3) if runs else 0.0,
                "avg_tasks_per_agent": round(tasks_per_agent_avg, 3),
                "tasks_per_minute": round(tasks_per_minute, 3),
            }
        )

    if not metric_rows:
        return {"rows": [], "recommendation": None}

    success_values = [row["success_rate_pct"] for row in metric_rows]
    tpm_values = [row["tasks_per_minute"] for row in metric_rows]
    tpa_values = [row["avg_tasks_per_agent"] for row in metric_rows]
    s_min, s_max = min(success_values), max(success_values)
    tpm_min, tpm_max = min(tpm_values), max(tpm_values)
    tpa_min, tpa_max = min(tpa_values), max(tpa_values)

    for row in metric_rows:
        score = (
            0.45 * _normalize_score(row["success_rate_pct"], s_min, s_max)
            + 0.35 * _normalize_score(row["tasks_per_minute"], tpm_min, tpm_max)
            + 0.20 * _normalize_score(row["avg_tasks_per_agent"], tpa_min, tpa_max)
        )
        row["recommendation_score"] = round(score, 4)

    sorted_rows = sorted(
        metric_rows,
        key=lambda row: (
            row["recommendation_score"],
            row["success_rate_pct"],
            row["runs"],
            -row["selected_agents"],
        ),
        reverse=True,
    )
    recommendation = sorted_rows[0]
    return {
        "rows": sorted(metric_rows, key=lambda row: row["selected_agents"]),
        "recommendation": {
            "selected_agents": recommendation["selected_agents"],
            "recommendation_score": recommendation["recommendation_score"],
            "reason": "max(weighted success/throughput/efficiency score)",
        },
    }
