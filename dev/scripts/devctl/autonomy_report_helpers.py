"""Data collection helpers for `devctl autonomy-report`."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .autonomy_report_render import build_charts
from .autonomy_report_summaries import summarize_source
from .config import REPO_ROOT
from .numeric import to_int, to_optional_float

DEFAULT_SOURCE_ROOT = "dev/reports/autonomy"
DEFAULT_LIBRARY_ROOT = "dev/reports/autonomy/library"
DEFAULT_EVENT_LOG = "dev/reports/audits/devctl_events.jsonl"

SOURCE_PATTERNS: dict[str, tuple[str, ...]] = {
    "triage_loop": ("triage-loop-live.json", "*triage-loop*.json"),
    "mutation_loop": ("mutation-loop-live.json", "*mutation-loop*.json"),
    "autonomy_loop": (
        "autonomy-loop-live.json",
        "*autonomy-loop*.json",
        "**/controller-summary.json",
    ),
    "orchestrate_status": (
        "orchestrate-status-end.json",
        "orchestrate-status-start.json",
        "*orchestrate-status*.json",
    ),
    "orchestrate_watch": (
        "orchestrate-watch-end.json",
        "orchestrate-watch-start.json",
        "*orchestrate-watch*.json",
    ),
    "phone_status": ("queue/phone/latest.json", "**/phone/latest.json"),
}


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def freshness_hours(path: Path, now: datetime) -> float:
    age_seconds = max(now.timestamp() - path.stat().st_mtime, 0.0)
    return round(age_seconds / 3600.0, 3)


def _find_latest_by_patterns(
    source_root: Path, patterns: tuple[str, ...]
) -> Path | None:
    candidates: dict[str, Path] = {}
    for pattern in patterns:
        for candidate in source_root.glob(pattern):
            if candidate.is_file():
                candidates[str(candidate.resolve())] = candidate
        for candidate in source_root.rglob(pattern):
            if candidate.is_file():
                candidates[str(candidate.resolve())] = candidate
    if not candidates:
        return None
    return max(candidates.values(), key=lambda item: item.stat().st_mtime)


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, str(exc)
    except json.JSONDecodeError as exc:
        return None, f"invalid json ({exc})"
    if not isinstance(payload, dict):
        return None, "expected top-level object"
    return payload, None


def _copy_source(path: Path, destination_root: Path, label: str) -> str:
    destination_root.mkdir(parents=True, exist_ok=True)
    destination = destination_root / f"{label}-{path.name}"
    shutil.copy2(path, destination)
    return str(destination)


def _read_event_count(event_log: Path) -> tuple[int, str | None]:
    if not event_log.exists():
        return 0, "event log not found"
    try:
        lines = event_log.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return 0, str(exc)
    return sum(1 for line in lines if line.strip()), None


def _refresh_orchestrate_snapshots(source_root: Path, warnings: list[str]) -> None:
    status_json = source_root / "orchestrate-status-end.json"
    watch_json = source_root / "orchestrate-watch-end.json"
    source_root.mkdir(parents=True, exist_ok=True)
    commands = [
        [
            "python3",
            "dev/scripts/devctl.py",
            "orchestrate-status",
            "--format",
            "json",
            "--output",
            str(status_json),
        ],
        [
            "python3",
            "dev/scripts/devctl.py",
            "orchestrate-watch",
            "--stale-minutes",
            "120",
            "--format",
            "json",
            "--output",
            str(watch_json),
        ],
    ]
    for command in commands:
        result = subprocess.run(
            command, cwd=REPO_ROOT, capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            warning = (result.stderr or result.stdout or "unknown error").strip()
            warnings.append(f"refresh failed ({' '.join(command[2:4])}): {warning}")


def collect_report(args) -> tuple[dict[str, Any], Path, Path]:
    now = datetime.now(timezone.utc)
    source_root = resolve_path(str(args.source_root))
    library_root = resolve_path(str(args.library_root))
    run_label = (
        str(args.run_label).strip()
        if args.run_label
        else now.strftime("%Y%m%d-%H%M%SZ")
    )
    bundle_dir = library_root / run_label
    sources_dir = bundle_dir / "sources"
    charts_dir = bundle_dir / "charts"

    warnings: list[str] = []
    errors: list[str] = []

    if args.refresh_orchestrate:
        _refresh_orchestrate_snapshots(source_root, warnings)

    bundle_dir.mkdir(parents=True, exist_ok=True)

    source_report: dict[str, Any] = {}
    found_count = 0
    for key, patterns in SOURCE_PATTERNS.items():
        latest = _find_latest_by_patterns(source_root, patterns)
        if latest is None:
            source_report[key] = {
                "found": False,
                "path": None,
                "freshness_hours": None,
                "summary": None,
                "copied_path": None,
            }
            continue

        found_count += 1
        payload, load_error = _load_json(latest)
        if load_error:
            errors.append(f"{key}: {load_error}")
            source_report[key] = {
                "found": True,
                "path": str(latest),
                "freshness_hours": freshness_hours(latest, now),
                "summary": None,
                "copied_path": None,
            }
            continue

        assert payload is not None
        copied_path = (
            _copy_source(latest, sources_dir, key) if args.copy_sources else None
        )
        source_report[key] = {
            "found": True,
            "path": str(latest),
            "freshness_hours": freshness_hours(latest, now),
            "summary": summarize_source(key, payload),
            "copied_path": copied_path,
        }

    event_log = resolve_path(str(args.event_log))
    event_count, event_error = _read_event_count(event_log)
    if event_error:
        warnings.append(f"event log: {event_error}")

    triage_summary = source_report.get("triage_loop", {}).get("summary") or {}
    mutation_summary = source_report.get("mutation_loop", {}).get("summary") or {}
    autonomy_summary = source_report.get("autonomy_loop", {}).get("summary") or {}
    watch_summary = source_report.get("orchestrate_watch", {}).get("summary") or {}
    status_summary = source_report.get("orchestrate_status", {}).get("summary") or {}
    phone_summary = source_report.get("phone_status", {}).get("summary") or {}

    metrics = {
        "triage_unresolved_count": to_int(
            triage_summary.get("unresolved_count"), default=0
        ),
        "mutation_score_gap_pct": to_optional_float(
            mutation_summary.get("score_gap_pct"), default=None
        ),
        "autonomy_rounds_completed": to_int(
            autonomy_summary.get("rounds_completed"), default=0
        ),
        "autonomy_tasks_completed": to_int(
            autonomy_summary.get("tasks_completed"), default=0
        ),
        "autonomy_resolved": bool(autonomy_summary.get("resolved", False)),
        "orchestrate_errors_count": to_int(
            status_summary.get("errors_count"), default=0
        )
        + to_int(watch_summary.get("errors_count"), default=0),
        "stale_agent_count": to_int(
            watch_summary.get("stale_agent_count"), default=0
        ),
        "overdue_instruction_ack_count": to_int(
            watch_summary.get("overdue_instruction_ack_count"), default=0
        ),
        "phone_reason": str(phone_summary.get("reason") or "unknown"),
        "event_count": event_count,
    }

    if found_count == 0:
        errors.append(f"no source artifacts found under {source_root}")

    report: dict[str, Any] = {
        "command": "autonomy-report",
        "timestamp": iso_z(now),
        "ok": not errors,
        "run_label": run_label,
        "bundle_dir": str(bundle_dir),
        "source_root": str(source_root),
        "library_root": str(library_root),
        "event_log": str(event_log),
        "sources": source_report,
        "metrics": metrics,
        "warnings": warnings,
        "errors": errors,
        "charts": [],
    }

    if args.charts:
        chart_paths, chart_warning = build_charts(report, charts_dir)
        report["charts"] = chart_paths
        if chart_warning:
            warnings.append(chart_warning)

    return report, bundle_dir, charts_dir
