"""devctl dashboard command — governance snapshot from existing artifacts."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from ..common import emit_output, write_output
from ..config import REPO_ROOT
from ..time_utils import utc_timestamp

# Shared utilities extracted to break circular import with dashboard_builders.
from .dashboard_utils import (
    _age_seconds,
    _extract_time_from_iso,
    _format_age,
    _format_duration,
    _paths,
    _read_json,
    _tail_lines,
)

# Section-builder functions live in dashboard_builders; imported here so
# _assemble can call them, and re-exported for backward-compatible test access.
from .dashboard_builders import (  # noqa: E402
    _build_analytics_section,
    _build_audit_section,
    _build_coordination_section,
    _build_flow_section,
    _build_now_section,
    _build_one_line,
    _build_plan_section,
    _build_probes_section,
    _build_quality_section,
    _build_review_section,
    _build_reviewer_activity_section,
    _build_workers_section,
    _compile_summary,
    _derive_top_blocker,
    _extract_check_details,
    _extract_cleanup_rate,
    _extract_failing_files,
    _extract_push_success_values,
    _extract_push_timers,
    _extract_top_commands,
    _find_agent_by_role,
    _first_meaningful_line,
    _is_reviewer_overdue,
    _publication_effective,
)


def _git_short() -> dict[str, Any]:
    """Return branch, HEAD short sha, dirty state, ahead/behind, dirty count, and recent commits."""
    result: dict[str, Any] = {
        "branch": "unknown",
        "head": "unknown",
        "dirty": "unknown",
        "ahead": 0,
        "behind": 0,
        "dirty_files": 0,
        "recent_commits": [],
    }
    try:
        sb = subprocess.run(
            ["git", "status", "-sb", "--porcelain"],
            capture_output=True, text=True, timeout=5, cwd=str(REPO_ROOT),
            check=False,
        )
        lines = sb.stdout.strip().splitlines()
        if lines:
            header = lines[0].lstrip("# ").strip()
            result["branch"] = header.split("...")[0] if "..." in header else header
            dirty_lines = lines[1:]
            result["dirty"] = "DIRTY" if dirty_lines else "CLEAN"
            result["dirty_files"] = len(dirty_lines)
            ahead, behind = _parse_ahead_behind(header)
            result["ahead"] = ahead
            result["behind"] = behind
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        log = subprocess.run(
            ["git", "log", "--oneline", "-3"],
            capture_output=True, text=True, timeout=5, cwd=str(REPO_ROOT),
            check=False,
        )
        commits: list[dict[str, str]] = []
        for line in log.stdout.strip().splitlines():
            parts = line.split(None, 1)
            if parts:
                commits.append({
                    "sha": parts[0],
                    "message": parts[1] if len(parts) > 1 else "",
                })
        if commits:
            result["head"] = commits[0]["sha"]
            result["recent_commits"] = commits
    except (OSError, subprocess.TimeoutExpired):
        pass
    return result


def _parse_ahead_behind(header: str) -> tuple[int, int]:
    """Extract ahead/behind counts from git status -sb header line.

    Examples:
        'main...origin/main [ahead 5]' -> (5, 0)
        'main...origin/main [ahead 3, behind 2]' -> (3, 2)
        'main...origin/main [behind 1]' -> (0, 1)
        'main...origin/main' -> (0, 0)
    """
    ahead = 0
    behind = 0
    bracket = re.search(r"\[(.+?)\]", header)
    if bracket:
        content = bracket.group(1)
        ahead_match = re.search(r"ahead\s+(\d+)", content)
        if ahead_match:
            ahead = int(ahead_match.group(1))
        behind_match = re.search(r"behind\s+(\d+)", content)
        if behind_match:
            behind = int(behind_match.group(1))
    return ahead, behind


def _parse_bridge(path: Path) -> dict[str, str]:
    """Extract lightweight coordination fields from bridge.md."""
    fields: dict[str, str] = {
        "last_poll": "n/a",
        "last_poll_utc": "",
        "reviewer_mode": "n/a",
        "instruction": "n/a",
        "verdict": "n/a",
        "findings_raw": "",
        "reviewed_scope_raw": "",
        "instruction_full": "n/a",
    }
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return fields
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- Last Codex poll:"):
            raw_poll = stripped.split(":", 1)[1].strip().strip("`")
            fields["last_poll"] = raw_poll
            fields["last_poll_utc"] = raw_poll
        elif stripped.startswith("- Reviewer mode:"):
            fields["reviewer_mode"] = stripped.split(":", 1)[1].strip().strip("`")
    instr_match = re.search(
        r"## Current Instruction For Claude\s*\n(.*?)(?=\n## |\Z)",
        text, re.DOTALL,
    )
    if instr_match:
        raw = instr_match.group(1).strip()
        fields["instruction"] = raw[:120] + ("..." if len(raw) > 120 else "")
        fields["instruction_full"] = raw
    verdict_match = re.search(
        r"## Current Verdict\s*\n(.*?)(?=\n## |\Z)",
        text, re.DOTALL,
    )
    if verdict_match:
        fields["verdict"] = verdict_match.group(1).strip()
    findings_match = re.search(
        r"## Open Findings\s*\n(.*?)(?=\n## |\Z)",
        text, re.DOTALL,
    )
    if findings_match:
        fields["findings_raw"] = findings_match.group(1).strip()
    scope_match = re.search(
        r"## Last Reviewed Scope\s*\n(.*?)(?=\n## |\Z)",
        text, re.DOTALL,
    )
    if scope_match:
        fields["reviewed_scope_raw"] = scope_match.group(1).strip()
    return fields


def _parse_bridge_findings(path: Path) -> list[dict[str, str]]:
    """Extract structured findings from the ## Open Findings section of bridge.md.

    Each finding is returned as {"id": "F1", "summary": "first 80 chars..."}.
    Returns an empty list when bridge.md is missing or the section is empty.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    section_match = re.search(
        r"## Open Findings\s*\n(.*?)(?=\n## |\Z)",
        text, re.DOTALL,
    )
    if not section_match:
        return []
    findings: list[dict[str, str]] = []
    for line in section_match.group(1).splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        body = stripped[2:].strip()
        fid_match = re.match(r"(F\d+)\s*:\s*(.*)", body)
        if fid_match:
            fid = fid_match.group(1)
            desc = fid_match.group(2).strip()
        else:
            fid = f"F{len(findings) + 1}"
            desc = body
        summary = desc[:80] + ("..." if len(desc) > 80 else "")
        findings.append({"id": fid, "summary": summary})
    return findings


def _session_age(repo_root: Path) -> dict[str, Any]:
    """Read publisher heartbeat and compute session duration from started_at_utc."""
    data = _read_json(repo_root / _paths()["publisher_hb"])
    if data is None:
        return {"session_age_s": None, "session_label": "--", "started_at_utc": "", "started_time": ""}
    started = data.get("started_at_utc", "")
    age_s = _age_seconds(started)
    started_time = _extract_time_from_iso(started) if started else ""
    return {
        "session_age_s": age_s,
        "session_label": _format_duration(age_s),
        "started_at_utc": started,
        "started_time": started_time,
    }


def _parse_plan_progress(repo_root: Path) -> dict[str, str]:
    """Extract active slice and progress hints from MASTER_PLAN.md."""
    result = {"slice": "n/a", "progress": "n/a", "open_findings": "0", "pending": "0"}
    path = repo_root / _paths()["master_plan"]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return result
    # Find the first in-progress MP slice
    for line in text.splitlines():
        stripped = line.strip()
        if "IN-PROGRESS" in stripped.upper() or "ACTIVE" in stripped.upper():
            mp_match = re.match(r".*?(MP-\d+\S*)\s*(.*)", stripped)
            if mp_match:
                result["slice"] = f"{mp_match.group(1)} {mp_match.group(2)[:40].strip()}"
                break
    return result


def _repo_name() -> str:
    """Derive repo name from git remote or directory name."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5, cwd=str(REPO_ROOT),
            check=False,
        )
        url = result.stdout.strip()
        if url:
            name = url.rstrip("/").rsplit("/", 1)[-1]
            return name.removesuffix(".git")
    except (OSError, subprocess.TimeoutExpired):
        pass
    return REPO_ROOT.name


def _read_heartbeat(path: Path) -> dict[str, Any]:
    """Read a daemon heartbeat file and derive running state from stopped_at_utc."""
    data = _read_json(path)
    if data is None:
        return {
            "running": False, "pid": 0, "last_heartbeat": "n/a",
            "last_heartbeat_age": "--", "snapshots": 0,
        }
    stopped = data.get("stopped_at_utc", "")
    running = not bool(stopped)
    hb_utc = data.get("last_heartbeat_utc", "n/a")
    return {
        "running": running,
        "pid": data.get("pid", 0),
        "last_heartbeat": hb_utc,
        "last_heartbeat_age": _format_age(_age_seconds(hb_utc)),
        "snapshots": data.get("snapshots_emitted", 0),
    }


def _pid_is_alive(pid: int) -> bool:
    """Check whether a process with the given PID is currently running."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OSError):
        return False


def _read_conductor_liveness(path: Path) -> dict[str, Any]:
    """Read a conductor session JSON and probe whether its PID is still alive."""
    data = _read_json(path)
    if data is None:
        return {"pid": None, "alive": False}
    pid = data.get("session_pid")
    if pid is None or not isinstance(pid, int) or pid <= 0:
        return {"pid": None, "alive": False}
    return {"pid": pid, "alive": _pid_is_alive(pid)}


def _build_health_section(
    repo_root: Path,
    compact: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build the HEALTH section from daemon heartbeats, conductors, and attention."""
    p = _paths()
    publisher = _read_heartbeat(repo_root / p["publisher_hb"])
    supervisor = _read_heartbeat(repo_root / p["supervisor_hb"])

    codex_conductor = _read_conductor_liveness(repo_root / p["codex_conductor_session"])
    claude_conductor = _read_conductor_liveness(repo_root / p["claude_conductor_session"])

    # Extract attention from full.json (compact does not carry it)
    full_data = _read_json(repo_root / p["full_json"])
    attention = (full_data or {}).get("attention", {})
    attention_status = attention.get("status", "n/a")
    attention_summary = attention.get("summary", "n/a")

    active_daemons = sum(1 for d in (publisher, supervisor) if d["running"])

    return {
        "publisher": publisher,
        "supervisor": supervisor,
        "codex_conductor": codex_conductor,
        "claude_conductor": claude_conductor,
        "attention_status": attention_status,
        "attention_summary": attention_summary,
        "active_daemons": active_daemons,
    }


def _build_timeline_section(
    repo_root: Path, *, count: int = 10,
) -> list[dict[str, str]]:
    """Build the TIMELINE section from the last *count* devctl event log entries."""
    raw_lines = _tail_lines(repo_root / _paths()["events_jsonl"], count=count)
    events: list[dict[str, str]] = []
    for line in raw_lines:
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        ts_raw = entry.get("timestamp", "")
        time_label = _extract_time_from_iso(ts_raw)
        success = entry.get("success", False)
        dur = entry.get("duration_seconds")
        dur_label = f"{dur:.1f}s" if isinstance(dur, (int, float)) else "n/a"
        events.append({
            "time": time_label,
            "command": entry.get("command", "unknown"),
            "result": "PASS" if success else "FAIL",
            "duration": dur_label,
        })
    return events


# Sections each view loads.  ``overview`` loads everything (no filtering).
_VIEW_SECTIONS: dict[str, frozenset[str]] = {
    "overview": frozenset(),  # empty means "load all"
    "dev": frozenset({
        "repo", "now", "review", "workers", "plan", "findings",
        "reviewer_activity", "quality", "flow", "timeline", "summary",
        "coordination",
    }),
    "analytics": frozenset({
        "repo", "analytics", "timeline", "summary",
    }),
    "quality": frozenset({
        "repo", "quality", "audit", "summary",
    }),
    "audit": frozenset({
        "repo", "audit", "summary",
    }),
    "publication": frozenset({
        "repo", "publication", "flow", "coordination", "summary",
    }),
    "health": frozenset({
        "repo", "health", "review", "coordination", "summary",
    }),
}


def _view_needs(view: str, section: str) -> bool:
    """Return True when *view* should include *section*."""
    allowed = _VIEW_SECTIONS.get(view, frozenset())
    return not allowed or section in allowed


def build_snapshot(
    *, repo_root: Path = REPO_ROOT, view: str = "overview",
) -> dict[str, Any]:
    """Build a DashboardSnapshot dict from existing artifacts and git state.

    When *view* is not ``overview``, only the artifacts needed for that view
    are loaded; skipped sections appear as empty/default values so renderers
    degrade gracefully.
    """
    git = _git_short()
    needs = _VIEW_SECTIONS.get(view, frozenset())
    load_all = not needs  # overview
    p = _paths()

    compact = _read_json(repo_root / p["compact_json"]) if load_all or (needs & {"review", "now", "coordination", "health", "workers"}) else None
    push_data = _read_json(repo_root / p["push_json"]) if load_all or (needs & {"publication", "quality", "flow"}) else None
    receipt = _read_json(repo_root / p["receipt_json"]) if load_all or (needs & {"publication", "flow", "coordination"}) else None
    agents = _read_json(repo_root / p["agents_json"]) if load_all or (needs & {"review", "workers", "now"}) else None
    pipeline = _read_json(repo_root / p["pipeline_json"]) if load_all or (needs & {"flow"}) else None
    bridge = _parse_bridge(repo_root / p["bridge_md"]) if load_all or (needs & {"review", "now", "coordination", "reviewer_activity", "findings"}) else _empty_bridge()
    bridge_findings = _parse_bridge_findings(repo_root / p["bridge_md"]) if load_all or (needs & {"findings", "plan"}) else []
    plan = _parse_plan_progress(repo_root) if load_all or (needs & {"plan"}) else None
    gov_data = _read_json(repo_root / p["governance_review_json"]) if load_all or (needs & {"audit"}) else None
    probe_data = _read_json(repo_root / p["probe_summary_json"]) if load_all or (needs & {"quality"}) else None
    ds_data = _read_json(repo_root / p["data_science_json"]) if load_all or (needs & {"analytics"}) else None

    session_info = _session_age(repo_root) if load_all or (needs & {"repo", "coordination"}) else None

    snapshot = _assemble(
        git, compact, push_data, receipt, agents, pipeline, bridge, plan,
        gov_data=gov_data, probe_data=probe_data, ds_data=ds_data,
        bridge_findings=bridge_findings,
        session_info=session_info,
        repo_root=repo_root,
        view=view,
    )
    return snapshot


def _empty_bridge() -> dict[str, str]:
    """Return the default bridge fields when bridge parsing is skipped."""
    return {
        "last_poll": "n/a", "last_poll_utc": "", "reviewer_mode": "n/a",
        "instruction": "n/a", "verdict": "n/a", "findings_raw": "",
        "reviewed_scope_raw": "", "instruction_full": "n/a",
    }


def _assemble(
    git: dict[str, str],
    compact: dict[str, Any] | None,
    push_data: dict[str, Any] | None,
    receipt: dict[str, Any] | None,
    agents: dict[str, Any] | None,
    pipeline: dict[str, Any] | None,
    bridge: dict[str, str],
    plan: dict[str, str] | None = None,
    *,
    gov_data: dict[str, Any] | None = None,
    probe_data: dict[str, Any] | None = None,
    ds_data: dict[str, Any] | None = None,
    bridge_findings: list[dict[str, str]] | None = None,
    repo_root: Path = REPO_ROOT,
    session_info: dict[str, Any] | None = None,
    view: str = "overview",
) -> dict[str, Any]:
    """Assemble the typed DashboardSnapshot from raw sources."""
    session = (compact or {}).get("current_session", {})
    doctor = (compact or {}).get("doctor", {})
    instruction_rev = session.get("current_instruction_revision", "n/a")

    reviewer_agent = _find_agent_by_role(agents, "reviewer")
    implementer_agent = _find_agent_by_role(agents, "implementer")

    receipt_push = (receipt or {}).get("push_action", "n/a")

    publication_effective = _publication_effective(push_data, receipt, git)
    publication_effective["timers"] = _extract_push_timers(push_data)
    quality = _build_quality_section(push_data)
    quality["probes"] = _build_probes_section(probe_data)

    # Derive top blocker from quality failures or open findings
    top_blocker = _derive_top_blocker(quality, session, doctor)

    # Compute last-change age from bridge poll timestamp
    poll_utc = bridge.get("last_poll_utc", "")
    last_change_age = _age_seconds(poll_utc)

    # Analytics view loads the full event timeline (not just last 10)
    timeline_count = 100 if view == "analytics" else 10

    snapshot: dict[str, Any] = {
        "schema_version": 2,
        "contract_id": "DashboardSnapshot",
        "timestamp": utc_timestamp(),
        "view": view,
        "repo": {
            "name": _repo_name(),
            "branch": git["branch"],
            "head": git["head"],
            "worktree": git["dirty"],
            "session": (session_info or {}).get("session_label", "--"),
            "ahead": git.get("ahead", 0),
            "behind": git.get("behind", 0),
            "dirty_files": git.get("dirty_files", 0),
            "recent_commits": git.get("recent_commits", []),
        },
        "now": _build_now_section(
            bridge, reviewer_agent, implementer_agent, session,
            top_blocker, last_change_age,
        ),
        "health": _build_health_section(repo_root, compact),
        "review": _build_review_section(bridge, reviewer_agent, implementer_agent, session),
        "workers": _build_workers_section(agents),
        "plan": _build_plan_section(plan or {}, session, bridge_findings or []),
        "findings": bridge_findings or [],
        "publication": publication_effective,
        "quality": quality,
        "audit": _build_audit_section(gov_data),
        "analytics": _build_analytics_section(ds_data, gov_data, repo_root),
        "coordination": _build_coordination_section(session, instruction_rev, receipt_push, bridge, doctor, session_info or {}),
        "reviewer_activity": _build_reviewer_activity_section(bridge, reviewer_agent),
        "flow": _build_flow_section(receipt, push_data, session),
        "timeline": _build_timeline_section(repo_root, count=timeline_count),
    }
    snapshot["summary"] = _compile_summary(snapshot)
    return snapshot


def run(args) -> int:
    """Build and render the governance dashboard."""
    from .dashboard_render import render_json, render_markdown, render_terminal

    view = getattr(args, "view", "overview")
    snapshot = build_snapshot(view=view)

    no_color = getattr(args, "no_color", False)
    fmt = getattr(args, "format", "terminal")
    if fmt == "json":
        output = render_json(snapshot)
    elif fmt == "md":
        output = render_markdown(snapshot)
    else:
        output = render_terminal(snapshot, no_color=no_color)

    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return 0
