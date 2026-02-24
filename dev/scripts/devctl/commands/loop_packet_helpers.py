"""Shared helper logic for `devctl loop-packet` packet generation."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from ..config import REPO_ROOT
from ..status_report import build_project_report
from ..triage_enrich import apply_defaults_to_issues, build_issue_rollup
from ..triage_support import build_next_actions, classify_issues

ALLOWED_SOURCE_COMMANDS = {"triage-loop", "mutation-loop", "triage"}
DEFAULT_SOURCE_CANDIDATES = (
    ".cihub/coderabbit/coderabbit-ralph-loop.json",
    ".cihub/mutation/mutation-ralph-loop.json",
    ".cihub/devctl-triage.ai.json",
    "/tmp/coderabbit-ralph-loop.json",
    "/tmp/mutation-ralph-loop.json",
    "/tmp/devctl-triage.ai.json",
)
RISK_CONFIDENCE = {"low": 0.9, "medium": 0.65, "high": 0.45}


def _resolve_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _truncate_chars(value: str, max_chars: int) -> str:
    trimmed = str(value)
    if max_chars <= 0:
        return ""
    if len(trimmed) <= max_chars:
        return trimmed
    return trimmed[: max_chars - 3] + "..."


def _parse_iso_timestamp(raw_value: Any) -> datetime | None:
    text = str(raw_value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _freshness_hours(timestamp: datetime, now_utc: datetime) -> float:
    age_seconds = max((now_utc - timestamp).total_seconds(), 0.0)
    return age_seconds / 3600.0


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, str(exc)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON ({exc})"
    if not isinstance(payload, dict):
        return None, "expected top-level JSON object"
    return payload, None


def _source_command(payload: dict[str, Any]) -> str:
    command = str(payload.get("command") or "").strip().lower()
    if command == "mutation_loop":
        return "mutation-loop"
    return command


def _discover_artifact_sources(
    source_paths: list[str],
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    checked_paths: list[str] = []
    for raw_path in source_paths:
        path = _resolve_path(raw_path)
        checked_paths.append(str(path))
        if not path.exists():
            continue
        payload, read_error = _read_json(path)
        if read_error:
            warnings.append(f"{path}: {read_error}")
            continue
        if not isinstance(payload, dict):
            warnings.append(f"{path}: unexpected non-object payload")
            continue
        command = _source_command(payload)
        if command not in ALLOWED_SOURCE_COMMANDS:
            warnings.append(f"{path}: unsupported command '{command or 'missing'}'")
            continue
        timestamp = _parse_iso_timestamp(payload.get("timestamp"))
        rows.append(
            {
                "path": str(path),
                "command": command,
                "payload": payload,
                "timestamp": timestamp,
                "mtime": path.stat().st_mtime,
            }
        )
    return rows, warnings, checked_paths


def _choose_source(
    *,
    rows: list[dict[str, Any]],
    prefer_source: str,
) -> dict[str, Any] | None:
    if not rows:
        return None
    command_order = [prefer_source] + [
        name for name in ("triage-loop", "mutation-loop", "triage") if name != prefer_source
    ]
    rank = {name: idx for idx, name in enumerate(command_order)}

    def sort_key(row: dict[str, Any]) -> tuple[int, float]:
        command = str(row.get("command") or "")
        command_rank = rank.get(command, len(command_order))
        timestamp = row.get("timestamp")
        if isinstance(timestamp, datetime):
            freshness_seed = timestamp.timestamp()
        else:
            freshness_seed = float(row.get("mtime") or 0.0)
        return command_rank, -freshness_seed

    ordered = sorted(rows, key=sort_key)
    return ordered[0] if ordered else None


def _build_live_triage_source() -> dict[str, Any]:
    project_report = build_project_report(
        command="loop-packet",
        include_ci=True,
        ci_limit=10,
        include_dev_logs=False,
        dev_root=None,
        dev_sessions_limit=5,
    )
    issues = apply_defaults_to_issues(classify_issues(project_report), {})
    payload = {
        "command": "triage",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "project": project_report,
        "issues": issues,
        "rollup": build_issue_rollup(issues),
        "next_actions": build_next_actions(issues),
    }
    return {
        "path": "<generated:live-triage>",
        "command": "triage",
        "payload": payload,
        "timestamp": _parse_iso_timestamp(payload.get("timestamp")),
        "mtime": datetime.now(timezone.utc).timestamp(),
    }


def _triage_loop_packet(payload: dict[str, Any]) -> tuple[str, str, list[str]]:
    unresolved = int(payload.get("unresolved_count") or 0)
    reason = str(payload.get("reason") or "unknown")
    branch = str(payload.get("branch") or "unknown")
    source_run = payload.get("source_run_id")
    context = [
        f"CodeRabbit loop snapshot for branch `{branch}`.",
        f"Reason: `{reason}`.",
        f"Unresolved medium/high findings: `{unresolved}`.",
    ]
    if isinstance(source_run, int) and source_run > 0:
        context.append(f"Source run id: `{source_run}`.")
    risk = "low" if unresolved == 0 else ("high" if unresolved > 8 else "medium")
    actions = []
    if unresolved == 0:
        actions.append("No medium/high backlog remains. Continue with normal CI verification.")
    else:
        actions.append(
            "Review unresolved findings and apply bounded fixes with the same source run correlation."
        )
        actions.append("Re-run report-only loop and verify unresolved count trends downward.")
    draft = "\n".join(
        [
            "Loop feedback packet:",
            *context,
            "",
            "Task: propose the next bounded remediation step with guardrails and verification.",
        ]
    )
    return risk, draft, actions


def _mutation_loop_packet(payload: dict[str, Any]) -> tuple[str, str, list[str]]:
    score = payload.get("last_score")
    threshold = payload.get("threshold")
    reason = str(payload.get("reason") or "unknown")
    branch = str(payload.get("branch") or "unknown")
    score_text = "n/a" if score is None else f"{float(score):.2%}"
    threshold_text = "n/a" if threshold is None else f"{float(threshold):.2%}"
    below_threshold = (
        isinstance(score, (int, float))
        and isinstance(threshold, (int, float))
        and float(score) < float(threshold)
    )
    risk = "high" if below_threshold else "low"
    hotspots = payload.get("last_hotspots") if isinstance(payload.get("last_hotspots"), list) else []
    hotspot_items: list[str] = []
    for row in hotspots[:3]:
        if not isinstance(row, dict):
            continue
        module = str(row.get("module") or row.get("target") or row.get("path") or "unknown")
        missed = row.get("missed")
        if isinstance(missed, int):
            hotspot_items.append(f"{module} (missed={missed})")
        else:
            hotspot_items.append(module)

    actions = []
    if below_threshold:
        actions.append("Prioritize mutation hotspots and add focused tests before enabling fix mode.")
    else:
        actions.append("Mutation score meets threshold. Keep report-only monitoring active.")
    if hotspot_items:
        actions.append("Top hotspots: " + ", ".join(hotspot_items))

    lines = [
        "Loop feedback packet:",
        f"Mutation loop snapshot for branch `{branch}`.",
        f"Reason: `{reason}`.",
        f"Score `{score_text}` vs threshold `{threshold_text}`.",
        "",
        "Task: propose the smallest safe test/code change sequence to improve confidence.",
    ]
    return risk, "\n".join(lines), actions


def _triage_packet(payload: dict[str, Any]) -> tuple[str, str, list[str]]:
    rollup = payload.get("rollup") if isinstance(payload.get("rollup"), dict) else {}
    total = int(rollup.get("total") or 0)
    by_severity = rollup.get("by_severity") if isinstance(rollup.get("by_severity"), dict) else {}
    high = int(by_severity.get("high") or 0)
    medium = int(by_severity.get("medium") or 0)
    if high > 0:
        risk = "high"
    elif medium > 0:
        risk = "medium"
    else:
        risk = "low"
    next_actions = payload.get("next_actions")
    actions = [str(row).strip() for row in next_actions] if isinstance(next_actions, list) else []
    actions = [row for row in actions if row]
    if not actions:
        actions = ["No explicit next actions found; review triage snapshot and owners."]
    lines = [
        "Loop feedback packet:",
        "Triage snapshot from local control-plane signals.",
        f"Issue rollup: total={total}, high={high}, medium={medium}.",
        "",
        "Task: convert this triage snapshot into an ordered, guarded execution plan.",
    ]
    return risk, "\n".join(lines), actions


def _build_packet_body(
    *,
    source_command: str,
    payload: dict[str, Any],
) -> tuple[str, str, list[str]]:
    if source_command == "triage-loop":
        return _triage_loop_packet(payload)
    if source_command == "mutation-loop":
        return _mutation_loop_packet(payload)
    return _triage_packet(payload)


def _auto_send_eligible(source_command: str, payload: dict[str, Any], risk: str) -> bool:
    if risk != "low":
        return False
    if source_command == "triage-loop":
        unresolved = int(payload.get("unresolved_count") or 0)
        return unresolved == 0 and str(payload.get("reason") or "") == "resolved"
    if source_command == "mutation-loop":
        return str(payload.get("reason") or "") == "threshold_met"
    if source_command == "triage":
        rollup = payload.get("rollup") if isinstance(payload.get("rollup"), dict) else {}
        return int(rollup.get("total") or 0) == 0
    return False
