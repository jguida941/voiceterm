"""Publication, quality, audit, probes, and analytics builders for the DashboardSnapshot.

Each function transforms raw artifact data into a typed section dict.
These are data-extraction helpers that the main ``_assemble`` function
(in ``dashboard.py``) calls when building the full snapshot.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .dashboard_utils import (
    _paths,
    _tail_lines,
)
from .dashboard_violations import (
    audit_recent_violations,
    probes_recent_violations,
    violations_to_dashboard_cells,
)

# Re-exported for backward compatibility with existing importers.
from .dashboard_typed_state import (
    _extract_typed_attention,
    _extract_typed_control_packets,
    _extract_typed_doctor,
    _extract_typed_instruction_provenance,
    _extract_typed_packets,
    _extract_typed_priority_decision,
    _extract_typed_session,
)

__all__ = [
    "_extract_typed_attention",
    "_extract_typed_control_packets",
    "_extract_typed_doctor",
    "_extract_typed_instruction_provenance",
    "_extract_typed_packets",
    "_extract_typed_priority_decision",
    "_extract_typed_session",
]


def _publication_effective(
    push_data: dict[str, Any] | None,
    receipt: dict[str, Any] | None,
    git: dict[str, str],
) -> dict[str, Any]:
    if push_data is None and receipt is None:
        return {
            "state": "n/a", "effective": "n/a", "why": "no artifacts",
            "post_push": "n/a", "evidence": "n/a",
            "target_match": {"branch": False, "head": False, "target": False, "remote": False},
        }
    push_ok = (push_data or {}).get("ok")
    push_branch = (push_data or {}).get("branch", "")
    push_head = (push_data or {}).get("head_commit", "")[:7]
    current_head = git.get("head", "")
    current_branch = git.get("branch", "")

    if push_ok is True and push_head == current_head:
        effective = "CURRENT"
        why = "latest push matches HEAD"
    elif push_ok is True:
        effective = "STALE"
        why = "push succeeded but HEAD has moved"
    elif push_ok is False:
        effective = "NOT CURRENT"
        why = (push_data or {}).get("reason", "push failed or blocked")
    else:
        effective = "UNKNOWN"
        why = "unable to determine publication state"

    stages = (push_data or {}).get("push_stages", {})
    post_push = "PASS" if stages.get("post_push_green") else "FAIL"
    published = stages.get("published_remote", False)

    if published and stages.get("post_push_green"):
        state_label = "PUBLISHED_REMOTE / POST_PUSH_GREEN"
    elif published:
        state_label = "PUBLISHED_REMOTE / POST_PUSH_NOT_GREEN"
    else:
        state_label = "NOT_PUBLISHED"

    branch_match = push_branch == current_branch
    head_match = push_head == current_head
    target_match = stages.get("validation_ready", False)
    remote_match = published

    return {
        "state": state_label,
        "effective": effective,
        "why": why,
        "post_push": post_push if push_data else "n/a",
        "evidence": _paths()["push_json"] if push_data else "n/a",
        "target_match": {
            "branch": branch_match,
            "head": head_match,
            "target": target_match,
            "remote": remote_match,
        },
    }


def _build_quality_section(push_data: dict[str, Any] | None) -> dict[str, Any]:
    """Build multi-gate quality section with failing file list and check details."""
    base: dict[str, Any] = {
        "docs_gate": "n/a", "plan_sync": "n/a", "code_shape": "n/a",
        "instr_sync": "n/a", "bridge": "n/a", "clippy": "n/a",
        "failing": [],
        "check_details": [],
    }
    if push_data is None:
        return base
    preflight = push_data.get("preflight_step", {})
    preflight_ok = preflight.get("returncode", -1) == 0 if preflight else None
    base["code_shape"] = "PASS" if preflight_ok else ("FAIL" if preflight_ok is False else "n/a")

    if preflight_ok is False:
        failure_out = preflight.get("failure_output", "")
        base["failing"] = _extract_failing_files(failure_out)
        typed_violations = push_data.get("violations")
        if typed_violations:
            base["check_details"] = _check_details_from_violations(typed_violations)
        else:
            base["check_details"] = _extract_check_details(failure_out)

    return base


def _extract_failing_files(output: str) -> list[str]:
    """Pull file paths from preflight failure output."""
    files: list[str] = []
    for line in output.splitlines():
        stripped = line.strip()
        path_match = re.search(r"((?:dev|rust|app)/\S+\.(?:py|rs|md))", stripped)
        if path_match and path_match.group(1) not in files:
            files.append(path_match.group(1))
            if len(files) >= 5:
                break
    return files


# Pattern matching ``format_steps_text`` output lines:
#   "  FAIL  check_name  -- violation detail"
#   "  PASS  check_name"
_CHECK_LINE_RE = re.compile(
    r"^\s*(PASS|FAIL|SKIP)\s+(\S+)(?:\s+--\s+(.+))?$"
)


def _extract_check_details(output: str) -> list[dict[str, str]]:
    """Parse per-check status and violation summaries from preflight output.

    The preflight ``failure_output`` contains the compact text produced by
    ``format_steps_text`` in ``steps.py``.  Each check line has the form:
        ``  FAIL  check_name  -- one-line violation``
    Only failing checks are included in the result to keep the dashboard
    focused on actionable items.

    Prefer ``_check_details_from_violations`` when typed ``ViolationRecord``
    dicts are available in the push data.
    """
    details: list[dict[str, str]] = []
    for line in output.splitlines():
        m = _CHECK_LINE_RE.match(line)
        if not m:
            continue
        status, name, violation = m.group(1), m.group(2), m.group(3) or ""
        if status != "FAIL":
            continue
        details.append({
            "check": name,
            "status": status,
            "violation": violation.strip(),
        })
        if len(details) >= 10:
            break
    return details


def _check_details_from_violations(
    violations: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Build dashboard cells from typed ViolationRecord-shaped payloads.

    Thin wrapper that delegates to the shared mapper in
    ``dashboard_violations``. The CHECKS path was the original consumer
    of this layout; the audit and probes panels now share the same
    flattening so every dashboard ``recent_violations`` field follows
    one cell shape regardless of which sibling adapter produced it.
    """
    return violations_to_dashboard_cells(violations)


def _extract_push_timers(push_data: dict[str, Any] | None) -> dict[str, Any]:
    """Extract step durations from the push report for publication timing."""
    na: dict[str, Any] = {"fetch_s": "n/a", "preflight_s": "n/a", "push_s": "n/a"}
    if push_data is None:
        return na
    fetch = push_data.get("fetch_step") or {}
    preflight = push_data.get("preflight_step") or {}
    push_step = push_data.get("push_step") or {}
    return {
        "fetch_s": fetch.get("duration_s", "n/a"),
        "preflight_s": preflight.get("duration_s", "n/a"),
        "push_s": push_step.get("duration_s", "n/a"),
    }


def _build_audit_section(gov_data: dict[str, Any] | None) -> dict[str, Any]:
    """Build audit section from governance review summary stats.

    Adds a ``recent_violations`` list of dashboard cells projected from
    the governance-review *recent* window through the shared
    ``ViolationRecord`` adapter. Empty when no governance data is
    loaded so renderers can read the field unconditionally.
    """
    na: dict[str, Any] = {
        "total_findings": "n/a", "fixed_count": "n/a",
        "cleanup_rate_pct": "n/a", "open_finding_count": "n/a",
        "recent_violations": [],
    }
    if gov_data is None:
        return na
    stats = gov_data.get("stats", {})
    return {
        "total_findings": stats.get("total_findings", "n/a"),
        "fixed_count": stats.get("fixed_count", "n/a"),
        "cleanup_rate_pct": stats.get("cleanup_rate_pct", "n/a"),
        "open_finding_count": stats.get("open_finding_count", "n/a"),
        "recent_violations": audit_recent_violations(gov_data),
    }


def _build_probes_section(probe_data: dict[str, Any] | None) -> dict[str, Any]:
    """Build probe quality summary from probe report summary.

    Adds a ``recent_violations`` list of dashboard cells projected from
    the probe-report risk hints through the shared ``ViolationRecord``
    adapter. Empty when no probe data is loaded so renderers can read
    the field unconditionally. ``recent_violations`` is appended after
    the literal so the underlying dict literal stays under the
    ``check_python_dict_schema`` large-dict threshold.
    """
    na: dict[str, Any] = {
        "risk_hints": "n/a", "high": "n/a", "medium": "n/a",
        "probes_enabled": "n/a", "files_scanned": "n/a",
    }
    na["recent_violations"] = []
    if probe_data is None:
        return na
    summary = probe_data.get("summary", {})
    severity = summary.get("hints_by_severity", {})
    section: dict[str, Any] = {
        "risk_hints": summary.get("risk_hints", "n/a"),
        "high": severity.get("high", 0),
        "medium": severity.get("medium", 0),
        "probes_enabled": summary.get("probe_count", "n/a"),
        "files_scanned": summary.get("files_scanned", "n/a"),
    }
    section["recent_violations"] = probes_recent_violations(probe_data)
    return section


def _build_analytics_section(
    ds_data: dict[str, Any] | None,
    gov_data: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build analytics section from data science summary, governance, and event log."""
    na: dict[str, Any] = {
        "avg_time_to_green_s": "n/a", "total_events": "n/a",
        "command_success_rate_pct": "n/a",
        "push_success_values": [], "top_commands": [],
        "cleanup_rate_pct": "n/a",
    }
    if ds_data is None:
        return na

    if repo_root is None:
        from ..config import REPO_ROOT
        repo_root = REPO_ROOT

    watchdog = ds_data.get("watchdog_stats", {})
    events = ds_data.get("event_stats", {})
    top_cmds = _extract_top_commands(events, limit=5)
    push_vals = _extract_push_success_values(repo_root, count=20)
    cleanup = _extract_cleanup_rate(gov_data)
    return {
        "avg_time_to_green_s": watchdog.get("avg_time_to_green_seconds", "n/a"),
        "total_events": events.get("total_events", "n/a"),
        "command_success_rate_pct": events.get("success_rate_pct", "n/a"),
        "push_success_values": push_vals,
        "top_commands": top_cmds,
        "cleanup_rate_pct": cleanup,
    }


def _extract_top_commands(
    event_stats: dict[str, Any], limit: int = 5,
) -> list[tuple[str, float]]:
    """Pull the top N commands by count from data science event_stats."""
    commands = event_stats.get("commands", [])
    result: list[tuple[str, float]] = []
    for entry in commands[:limit]:
        name = entry.get("command", "unknown")
        count = entry.get("count", 0)
        result.append((name, float(count)))
    return result


def _extract_push_success_values(repo_root: Path, count: int = 20) -> list[float]:
    """Read last N push events from the event log and return 1.0 (ok) / 0.0 (fail)."""
    raw_lines = _tail_lines(repo_root / _paths()["events_jsonl"], count=count * 5)
    values: list[float] = []
    for line in raw_lines:
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if entry.get("command") == "push":
            values.append(1.0 if entry.get("success") else 0.0)
    return values[-count:]


def _extract_cleanup_rate(gov_data: dict[str, Any] | None) -> float | str:
    """Extract cleanup rate percentage from governance review data."""
    if gov_data is None:
        return "n/a"
    stats = gov_data.get("stats", {})
    rate = stats.get("cleanup_rate_pct", "n/a")
    if isinstance(rate, (int, float)):
        return float(rate)
    return "n/a"
