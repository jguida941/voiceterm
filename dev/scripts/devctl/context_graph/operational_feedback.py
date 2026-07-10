"""Bounded operational artifact readers for context escalation packets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..repo_packs import active_path_config, voiceterm_repo_root

_QUALITY_FEEDBACK_SNAPSHOT_REL = Path(
    "dev/reports/governance/quality_feedback_latest/quality_feedback_snapshot.json"
)
_DATA_SCIENCE_SUMMARY_REL = (
    Path(active_path_config().data_science_output_root_rel) / "latest" / "summary.json"
)
_GLOBAL_HISTORY_TRIGGERS = frozenset((
    "swarm-run",
    "review-channel-bootstrap",
    "review-channel-event",
    "review-channel-promotion",
))
_GLOBAL_RECOMMENDATION_TRIGGERS = frozenset((
    "swarm-run",
    "review-channel-bootstrap",
    "review-channel-event",
    "review-channel-promotion",
    "loop-packet",
))
_GLOBAL_WATCHDOG_TRIGGERS = frozenset((
    "ralph-backlog",
    "swarm-run",
    "review-channel-bootstrap",
    "review-channel-event",
    "review-channel-promotion",
    "loop-packet",
))
_GLOBAL_RELIABILITY_TRIGGERS = _GLOBAL_WATCHDOG_TRIGGERS


def recent_fix_history_lines(
    *,
    trigger: str,
    query_terms: tuple[str, ...],
    canonical_refs: tuple[str, ...],
    limit: int = 3,
) -> tuple[str, ...]:
    """Return bounded recent-fix-history bullets for matching prompt scope."""
    payload = _load_json_artifact(
        Path(active_path_config().governance_review_summary_root_rel) / "review_summary.json"
    )
    rows = payload.get("recent_findings") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return ()
    selected = _select_recent_history(
        rows=rows,
        trigger=trigger,
        query_terms=query_terms,
        canonical_refs=canonical_refs,
        limit=limit,
    )
    return tuple(_render_recent_finding(row) for row in selected)


def quality_feedback_lines(
    *,
    trigger: str,
    query_terms: tuple[str, ...],
    limit: int = 2,
) -> tuple[str, ...]:
    """Return bounded quality-feedback recommendation bullets for prompts."""
    payload = _load_json_artifact(_QUALITY_FEEDBACK_SNAPSHOT_REL)
    recommendations = payload.get("recommendations") if isinstance(payload, dict) else None
    if not isinstance(recommendations, list):
        return ()
    selected = _select_recommendations(
        recommendations=recommendations,
        trigger=trigger,
        query_terms=query_terms,
        limit=limit,
    )
    return tuple(_render_recommendation(row) for row in selected)


def watchdog_digest_lines(
    *,
    trigger: str,
    query_terms: tuple[str, ...],
    limit: int = 2,
) -> tuple[str, ...]:
    """Return bounded watchdog episode digests for prompt/context packets."""
    payload = _load_json_artifact(_DATA_SCIENCE_SUMMARY_REL)
    metrics = payload.get("watchdog_stats") if isinstance(payload, dict) else None
    if not isinstance(metrics, dict):
        return ()
    families = metrics.get("guard_families")
    if not isinstance(families, list):
        return ()
    typed = [row for row in families if isinstance(row, dict)]
    matched = [row for row in typed if _watchdog_family_matches(row, query_terms=query_terms)]
    selected = matched
    if not selected and trigger in _GLOBAL_WATCHDOG_TRIGGERS:
        selected = typed[:1]
    if not selected and trigger not in _GLOBAL_WATCHDOG_TRIGGERS:
        return ()
    lines: list[str] = []
    total = metrics.get("total_episodes")
    success_rate = metrics.get("success_rate_pct")
    false_positive_rate = metrics.get("false_positive_rate_pct")
    if isinstance(total, int) and total > 0:
        lines.append(
            f"`watchdog`: {total} episodes, success {success_rate}%, false positives {false_positive_rate}%"
        )
    for row in selected:
        rendered = _render_watchdog_family(row)
        if rendered:
            lines.append(rendered)
        if len(lines) >= max(1, limit):
            break
    return tuple(lines[: max(1, limit)])


def data_science_reliability_lines(
    *,
    trigger: str,
    query_terms: tuple[str, ...],
    limit: int = 2,
) -> tuple[str, ...]:
    """Return bounded command-reliability summaries from data-science output."""
    payload = _load_json_artifact(_DATA_SCIENCE_SUMMARY_REL)
    event_stats = payload.get("event_stats") if isinstance(payload, dict) else None
    if not isinstance(event_stats, dict):
        return ()
    commands = event_stats.get("commands")
    if not isinstance(commands, list):
        return ()
    typed = [row for row in commands if isinstance(row, dict)]
    matched = [row for row in typed if _command_metric_matches(row, query_terms=query_terms)]
    selected = matched
    if not selected and trigger in _GLOBAL_RELIABILITY_TRIGGERS:
        selected = sorted(
            typed,
            key=_command_reliability_sort_key,
        )[:1]
    if not selected and trigger not in _GLOBAL_RELIABILITY_TRIGGERS:
        return ()
    lines: list[str] = []
    total_events = event_stats.get("total_events")
    success_rate = event_stats.get("success_rate_pct")
    p95_duration = event_stats.get("p95_duration_seconds")
    if isinstance(total_events, int) and total_events > 0:
        lines.append(
            f"`telemetry`: {total_events} events, success {success_rate}%, p95 runtime {p95_duration}s"
        )
    for row in selected:
        rendered = _render_command_metric(row)
        if rendered:
            lines.append(rendered)
        if len(lines) >= max(1, limit):
            break
    return tuple(lines[: max(1, limit)])


def _load_json_artifact(relative_path: Path) -> dict[str, Any] | None:
    repo_root = voiceterm_repo_root() or Path(".")
    artifact_path = repo_root / relative_path
    try:
        return json.loads(artifact_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None


def _select_recent_history(
    *,
    rows: list[object],
    trigger: str,
    query_terms: tuple[str, ...],
    canonical_refs: tuple[str, ...],
    limit: int,
) -> tuple[dict[str, Any], ...]:
    recent_rows = [
        row for row in reversed(rows)
        if isinstance(row, dict)
    ]
    matched = [
        row for row in recent_rows
        if _recent_finding_matches(
            row,
            query_terms=query_terms,
            canonical_refs=canonical_refs,
        )
    ]
    if matched:
        return tuple(matched[: max(1, limit)])
    if trigger in _GLOBAL_HISTORY_TRIGGERS:
        return tuple(recent_rows[: max(1, limit)])
    return ()


def _recent_finding_matches(
    row: dict[str, Any],
    *,
    query_terms: tuple[str, ...],
    canonical_refs: tuple[str, ...],
) -> bool:
    file_path = str(row.get("file_path") or "").strip()
    if file_path and file_path in canonical_refs:
        return True
    haystack = " ".join(
        str(row.get(field) or "")
        for field in (
            "file_path",
            "symbol",
            "check_id",
            "verdict",
            "finding_class",
            "prevention_surface",
            "notes",
        )
    ).lower()
    return any(term.lower() in haystack for term in query_terms)


def _render_recent_finding(row: dict[str, Any]) -> str:
    location = str(row.get("file_path") or "(unknown)").strip()
    line = row.get("line")
    if isinstance(line, int):
        location = f"{location}:{line}"
    check_id = str(row.get("check_id") or "unknown").strip()
    verdict = str(row.get("verdict") or "unknown").strip()
    extras: list[str] = []
    guidance_id = str(row.get("guidance_id") or "").strip()
    guidance_followed = row.get("guidance_followed")
    if guidance_id:
        extras.append("guidance followed" if guidance_followed is True else "guidance waived")
    prevention_surface = str(row.get("prevention_surface") or "").strip()
    if prevention_surface:
        extras.append(prevention_surface)
    suffix = f" [{' | '.join(extras)}]" if extras else ""
    return f"`{check_id}` {verdict} at `{location}`{suffix}"


def _watchdog_family_matches(
    row: dict[str, Any],
    *,
    query_terms: tuple[str, ...],
) -> bool:
    family = str(row.get("guard_family") or "").lower()
    return any(term.lower() in family for term in query_terms)


def _render_watchdog_family(row: dict[str, Any]) -> str:
    family = str(row.get("guard_family") or "").strip()
    episodes = row.get("episodes")
    success_rate = row.get("success_rate_pct")
    avg_time = row.get("avg_time_to_green_seconds")
    if not family or not isinstance(episodes, int):
        return ""
    return (
        f"`{family}`: {episodes} episodes, success {success_rate}%, "
        f"avg green {avg_time}s"
    )


def _select_recommendations(
    *,
    recommendations: list[object],
    trigger: str,
    query_terms: tuple[str, ...],
    limit: int,
) -> tuple[dict[str, Any], ...]:
    typed = [row for row in recommendations if isinstance(row, dict)]
    matched = [row for row in typed if _recommendation_matches(row, query_terms=query_terms)]
    if matched:
        ordered = sorted(matched, key=_recommendation_sort_key)
        return tuple(ordered[: max(1, limit)])
    if trigger in _GLOBAL_RECOMMENDATION_TRIGGERS:
        ordered = sorted(typed, key=_recommendation_sort_key)
        return tuple(ordered[: max(1, limit)])
    return ()


def _recommendation_matches(
    row: dict[str, Any],
    *,
    query_terms: tuple[str, ...],
) -> bool:
    haystack = " ".join(
        str(row.get(field) or "")
        for field in ("check_id", "category", "action", "evidence")
    ).lower()
    return any(term.lower() in haystack for term in query_terms)


def _recommendation_sort_key(row: dict[str, Any]) -> tuple[int, str]:
    priority = row.get("priority")
    numeric_priority = priority if isinstance(priority, int) else 9_999
    check_id = str(row.get("check_id") or "unknown").strip()
    return (numeric_priority, check_id)


def _render_recommendation(row: dict[str, Any]) -> str:
    check_id = str(row.get("check_id") or "unknown").strip()
    action = str(row.get("action") or "").strip()
    impact = str(row.get("estimated_impact") or "").strip()
    suffix = f" ({impact} impact)" if impact else ""
    return f"`{check_id}`: {action}{suffix}"


def _command_metric_matches(
    row: dict[str, Any],
    *,
    query_terms: tuple[str, ...],
) -> bool:
    command = str(row.get("command") or "").strip().lower()
    if not command:
        return False
    lowered_terms = tuple(term.lower() for term in query_terms)
    return any(term in command or command in term for term in lowered_terms)


def _command_reliability_sort_key(row: dict[str, Any]) -> tuple[float, int, str]:
    success_rate = row.get("success_rate_pct")
    count = row.get("count")
    command = str(row.get("command") or "").strip()
    numeric_success = float(success_rate) if isinstance(success_rate, int | float) else 100.0
    numeric_count = int(count) if isinstance(count, int) else 0
    return (numeric_success, -numeric_count, command)


def _render_command_metric(row: dict[str, Any]) -> str:
    command = str(row.get("command") or "").strip()
    count = row.get("count")
    success_rate = row.get("success_rate_pct")
    avg_duration = row.get("avg_duration_seconds")
    if not command or not isinstance(count, int):
        return ""
    return (
        f"`{command}`: success {success_rate}%, avg runtime {avg_duration}s "
        f"over {count} runs"
    )
