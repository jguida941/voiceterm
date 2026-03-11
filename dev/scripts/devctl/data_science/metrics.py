"""Data-science snapshot helpers for devctl command telemetry."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from ..audit_events import resolve_event_log_path
from ..common import resolve_repo_path
from ..config import REPO_ROOT
from ..governance_review_log import (
    DEFAULT_GOVERNANCE_REVIEW_LOG,
    DEFAULT_MAX_GOVERNANCE_REVIEW_ROWS,
    build_governance_review_stats,
    read_governance_review_rows,
    resolve_governance_review_log_path,
)
from .aggregates import build_agent_metrics, build_event_metrics
from .rendering import (
    render_data_science_markdown,
    write_data_science_charts,
)
from .source_rows import (
    collect_benchmark_summary_rows,
    collect_swarm_summary_rows,
    read_jsonl_dict_tail,
)
from ..watchdog import (
    build_watchdog_metrics,
    read_guarded_coding_episodes,
    watchdog_metrics_to_dict,
)
from ..numeric import to_int
from ..time_utils import utc_timestamp

DEFAULT_OUTPUT_ROOT = "dev/reports/data_science"
DEFAULT_SWARM_ROOT = "dev/reports/autonomy/swarms"
DEFAULT_BENCHMARK_ROOT = "dev/reports/autonomy/benchmarks"
DEFAULT_WATCHDOG_ROOT = "dev/reports/autonomy/watchdog/episodes"
DEFAULT_MAX_EVENTS = 20_000
DEFAULT_MAX_SWARM_FILES = 2_000
DEFAULT_MAX_BENCHMARK_FILES = 500
DEFAULT_MAX_WATCHDOG_ROWS = 5_000
DEFAULT_GOVERNANCE_REVIEW_LOG_PATH = str(DEFAULT_GOVERNANCE_REVIEW_LOG)


def _resolve_path(value: str) -> Path:
    return resolve_repo_path(value, repo_root=REPO_ROOT, resolve=True)


def run_data_science_snapshot(
    *,
    trigger_command: str,
    output_root: str | None = None,
    event_log_path: str | None = None,
    swarm_root: str | None = None,
    benchmark_root: str | None = None,
    watchdog_root: str | None = None,
    governance_review_log: str | None = None,
    max_events: int = DEFAULT_MAX_EVENTS,
    max_swarm_files: int = DEFAULT_MAX_SWARM_FILES,
    max_benchmark_files: int = DEFAULT_MAX_BENCHMARK_FILES,
    max_watchdog_rows: int = DEFAULT_MAX_WATCHDOG_ROWS,
    max_governance_review_rows: int = DEFAULT_MAX_GOVERNANCE_REVIEW_ROWS,
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
    watchdog_dir = _resolve_path(watchdog_root or DEFAULT_WATCHDOG_ROOT)
    governance_review_path = resolve_governance_review_log_path(
        governance_review_log or DEFAULT_GOVERNANCE_REVIEW_LOG_PATH,
        repo_root=REPO_ROOT,
    )

    event_rows = read_jsonl_dict_tail(event_log, max_rows=max_events)
    event_stats = build_event_metrics(event_rows)
    agent_rows = collect_swarm_summary_rows(
        swarm_dir, max_files=max_swarm_files
    ) + collect_benchmark_summary_rows(
        benchmark_dir, max_files=max_benchmark_files
    )
    agent_stats = build_agent_metrics(agent_rows)
    watchdog_rows = read_guarded_coding_episodes(
        watchdog_dir, max_rows=max_watchdog_rows
    )
    watchdog_stats = watchdog_metrics_to_dict(build_watchdog_metrics(watchdog_rows))
    governance_review_rows = read_governance_review_rows(
        governance_review_path,
        max_rows=max_governance_review_rows,
    )
    governance_review_stats = build_governance_review_stats(
        governance_review_rows
    ).to_dict()

    report = {
        "generated_at": utc_timestamp(),
        "trigger_command": trigger_command,
        "event_log": str(event_log),
        "event_stats": event_stats,
        "agent_stats": agent_stats,
        "watchdog_stats": watchdog_stats,
        "governance_review_log": str(governance_review_path),
        "governance_review_stats": governance_review_stats,
        "source_roots": {
            "swarm_root": str(swarm_dir),
            "benchmark_root": str(benchmark_dir),
            "watchdog_root": str(watchdog_dir),
            "governance_review_log": str(governance_review_path),
        },
        "source_counts": {
            "event_rows": len(event_rows),
            "agent_rows": len(agent_rows),
            "watchdog_rows": len(watchdog_rows),
            "governance_review_rows": len(governance_review_rows),
        },
    }

    write_data_science_charts(
        event_stats=event_stats,
        agent_stats=agent_stats,
        watchdog_stats=watchdog_stats,
        charts_dir=charts_dir,
    )

    markdown = render_data_science_markdown(report)
    (latest_dir / "summary.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
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

    output_root = (
        str(os.environ.get("DEVCTL_DATA_SCIENCE_OUTPUT_ROOT") or "").strip() or None
    )
    event_log = (
        str(os.environ.get("DEVCTL_DATA_SCIENCE_EVENT_LOG") or "").strip() or None
    )
    swarm_root = (
        str(os.environ.get("DEVCTL_DATA_SCIENCE_SWARM_ROOT") or "").strip() or None
    )
    benchmark_root = (
        str(os.environ.get("DEVCTL_DATA_SCIENCE_BENCHMARK_ROOT") or "").strip() or None
    )
    watchdog_root = (
        str(os.environ.get("DEVCTL_DATA_SCIENCE_WATCHDOG_ROOT") or "").strip() or None
    )
    governance_review_log = (
        str(os.environ.get("DEVCTL_DATA_SCIENCE_GOVERNANCE_REVIEW_LOG") or "").strip()
        or None
    )
    max_events = to_int(
        os.environ.get("DEVCTL_DATA_SCIENCE_MAX_EVENTS"),
        default=DEFAULT_MAX_EVENTS,
    )
    max_swarm_files = to_int(
        os.environ.get("DEVCTL_DATA_SCIENCE_MAX_SWARM_FILES"),
        default=DEFAULT_MAX_SWARM_FILES,
    )
    max_benchmark_files = to_int(
        os.environ.get("DEVCTL_DATA_SCIENCE_MAX_BENCHMARK_FILES"),
        default=DEFAULT_MAX_BENCHMARK_FILES,
    )
    max_watchdog_rows = to_int(
        os.environ.get("DEVCTL_DATA_SCIENCE_MAX_WATCHDOG_ROWS"),
        default=DEFAULT_MAX_WATCHDOG_ROWS,
    )
    max_governance_review_rows = to_int(
        os.environ.get("DEVCTL_DATA_SCIENCE_MAX_GOVERNANCE_REVIEW_ROWS"),
        default=DEFAULT_MAX_GOVERNANCE_REVIEW_ROWS,
    )

    # Fail-open so telemetry refresh never blocks normal devctl flows.
    try:
        run_data_science_snapshot(
            trigger_command=f"devctl:{command}",
            output_root=output_root,
            event_log_path=event_log,
            swarm_root=swarm_root,
            benchmark_root=benchmark_root,
            watchdog_root=watchdog_root,
            governance_review_log=governance_review_log,
            max_events=max_events,
            max_swarm_files=max_swarm_files,
            max_benchmark_files=max_benchmark_files,
            max_watchdog_rows=max_watchdog_rows,
            max_governance_review_rows=max_governance_review_rows,
        )
    # broad-except: allow reason=Telemetry refresh must never block devctl command flow fallback=skip telemetry update and continue command execution.
    except Exception as exc:
        print(
            f"[data-science] telemetry refresh skipped for devctl:{command}: {exc}",
            file=sys.stderr,
        )
        return
