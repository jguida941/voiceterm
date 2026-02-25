"""Data-science snapshot helpers for devctl command telemetry."""

from __future__ import annotations

import json
import os
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit_events import resolve_event_log_path
from .config import REPO_ROOT
from .data_science_aggregates import build_agent_metrics, build_event_metrics
from .data_science_rendering import (
    render_data_science_markdown,
    write_data_science_charts,
)

DEFAULT_OUTPUT_ROOT = "dev/reports/data_science"
DEFAULT_SWARM_ROOT = "dev/reports/autonomy/swarms"
DEFAULT_BENCHMARK_ROOT = "dev/reports/autonomy/benchmarks"
DEFAULT_MAX_EVENTS = 20_000
DEFAULT_MAX_SWARM_FILES = 2_000
DEFAULT_MAX_BENCHMARK_FILES = 500


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


def _iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _read_jsonl_tail(path: Path, *, max_rows: int) -> list[dict[str, Any]]:
    rows: deque[dict[str, Any]] = deque(maxlen=max(1, max_rows))
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                text = line.strip()
                if not text:
                    continue
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
    except OSError:
        return []
    return list(rows)


def _collect_swarm_rows(root: Path, *, max_files: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    paths = sorted(root.glob("*/summary.json"), reverse=True)[: max(1, max_files)]
    for path in paths:
        payload = _read_json(path)
        if payload is None:
            continue
        summary = payload.get("summary")
        if not isinstance(summary, dict):
            continue
        selected_agents = _safe_int(summary.get("selected_agents"), default=0)
        if selected_agents <= 0:
            continue
        agent_rows = payload.get("agents")
        task_total = 0
        if isinstance(agent_rows, list):
            for item in agent_rows:
                if isinstance(item, dict):
                    task_total += _safe_int(item.get("tasks_completed"), default=0)
        rows.append(
            {
                "source": "swarm",
                "selected_agents": selected_agents,
                "tasks_completed_total": task_total,
                "elapsed_seconds": None,
                "ok": bool(payload.get("ok")),
                "path": str(path),
            }
        )
    return rows


def _collect_benchmark_rows(root: Path, *, max_files: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    paths = sorted(root.glob("*/summary.json"), reverse=True)[: max(1, max_files)]
    for path in paths:
        payload = _read_json(path)
        if payload is None:
            continue
        scenarios = payload.get("scenarios")
        if not isinstance(scenarios, list):
            continue
        for scenario in scenarios:
            if not isinstance(scenario, dict):
                continue
            swarms = scenario.get("swarms")
            if not isinstance(swarms, list):
                continue
            for swarm in swarms:
                if not isinstance(swarm, dict):
                    continue
                selected_agents = _safe_int(swarm.get("selected_agents"), default=0)
                if selected_agents <= 0:
                    continue
                rows.append(
                    {
                        "source": "benchmark",
                        "selected_agents": selected_agents,
                        "tasks_completed_total": _safe_int(
                            swarm.get("tasks_completed_total"), default=0
                        ),
                        "elapsed_seconds": _safe_float(
                            swarm.get("elapsed_seconds"), default=0.0
                        ),
                        "ok": bool(swarm.get("ok")),
                        "path": str(path),
                    }
                )
    return rows

def run_data_science_snapshot(
    *,
    trigger_command: str,
    output_root: str | None = None,
    event_log_path: str | None = None,
    swarm_root: str | None = None,
    benchmark_root: str | None = None,
    max_events: int = DEFAULT_MAX_EVENTS,
    max_swarm_files: int = DEFAULT_MAX_SWARM_FILES,
    max_benchmark_files: int = DEFAULT_MAX_BENCHMARK_FILES,
) -> dict[str, Any]:
    output = _resolve_path(output_root or DEFAULT_OUTPUT_ROOT)
    output.mkdir(parents=True, exist_ok=True)
    latest_dir = output / "latest"
    charts_dir = latest_dir / "charts"
    history_dir = output / "history"
    latest_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)

    event_log = (
        _resolve_path(event_log_path)
        if event_log_path
        else resolve_event_log_path().resolve()
    )
    swarm_dir = _resolve_path(swarm_root or DEFAULT_SWARM_ROOT)
    benchmark_dir = _resolve_path(benchmark_root or DEFAULT_BENCHMARK_ROOT)

    event_rows = _read_jsonl_tail(event_log, max_rows=max_events)
    event_stats = build_event_metrics(event_rows)
    agent_rows = _collect_swarm_rows(swarm_dir, max_files=max_swarm_files) + _collect_benchmark_rows(
        benchmark_dir, max_files=max_benchmark_files
    )
    agent_stats = build_agent_metrics(agent_rows)

    report = {
        "generated_at": _iso_utc(),
        "trigger_command": trigger_command,
        "event_log": str(event_log),
        "event_stats": event_stats,
        "agent_stats": agent_stats,
        "source_roots": {
            "swarm_root": str(swarm_dir),
            "benchmark_root": str(benchmark_dir),
        },
        "source_counts": {
            "event_rows": len(event_rows),
            "agent_rows": len(agent_rows),
        },
    }

    write_data_science_charts(
        event_stats=event_stats,
        agent_stats=agent_stats,
        charts_dir=charts_dir,
    )

    markdown = render_data_science_markdown(report)
    (latest_dir / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (latest_dir / "summary.md").write_text(markdown, encoding="utf-8")
    with (history_dir / "snapshots.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(report, sort_keys=True))
        handle.write("\n")

    report["paths"] = {
        "summary_json": str(latest_dir / "summary.json"),
        "summary_md": str(latest_dir / "summary.md"),
        "history_jsonl": str(history_dir / "snapshots.jsonl"),
        "charts_dir": str(charts_dir),
    }
    return report


def maybe_auto_refresh_data_science(
    *,
    command: str,
) -> None:
    if str(os.environ.get("DEVCTL_DATA_SCIENCE_DISABLE") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return

    output_root = str(os.environ.get("DEVCTL_DATA_SCIENCE_OUTPUT_ROOT") or "").strip() or None
    event_log = str(os.environ.get("DEVCTL_DATA_SCIENCE_EVENT_LOG") or "").strip() or None
    swarm_root = str(os.environ.get("DEVCTL_DATA_SCIENCE_SWARM_ROOT") or "").strip() or None
    benchmark_root = (
        str(os.environ.get("DEVCTL_DATA_SCIENCE_BENCHMARK_ROOT") or "").strip() or None
    )
    max_events = _safe_int(
        os.environ.get("DEVCTL_DATA_SCIENCE_MAX_EVENTS"),
        default=DEFAULT_MAX_EVENTS,
    )
    max_swarm_files = _safe_int(
        os.environ.get("DEVCTL_DATA_SCIENCE_MAX_SWARM_FILES"),
        default=DEFAULT_MAX_SWARM_FILES,
    )
    max_benchmark_files = _safe_int(
        os.environ.get("DEVCTL_DATA_SCIENCE_MAX_BENCHMARK_FILES"),
        default=DEFAULT_MAX_BENCHMARK_FILES,
    )

    # Fail-open so telemetry refresh never blocks normal devctl flows.
    try:
        run_data_science_snapshot(
            trigger_command=f"devctl:{command}",
            output_root=output_root,
            event_log_path=event_log,
            swarm_root=swarm_root,
            benchmark_root=benchmark_root,
            max_events=max_events,
            max_swarm_files=max_swarm_files,
            max_benchmark_files=max_benchmark_files,
        )
    except Exception:
        return
