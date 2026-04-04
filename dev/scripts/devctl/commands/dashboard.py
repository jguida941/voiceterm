"""devctl dashboard command — governance snapshot from existing artifacts."""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..common import emit_output, write_output
from ..config import REPO_ROOT
from ..time_utils import utc_timestamp


# Artifact paths relative to repo root
_COMPACT_JSON = "dev/reports/review_channel/latest/compact.json"
_FULL_JSON = "dev/reports/review_channel/latest/full.json"
_PUSH_JSON = "dev/reports/push/latest.json"
_RECEIPT_JSON = "dev/reports/startup/latest/receipt.json"
_AGENTS_JSON = "dev/reports/review_channel/latest/registry/agents.json"
_PIPELINE_JSON = "dev/reports/review_channel/latest/commit_pipeline.json"
_PUBLISHER_HB = "dev/reports/review_channel/latest/publisher_heartbeat.json"
_SUPERVISOR_HB = "dev/reports/review_channel/latest/reviewer_supervisor_heartbeat.json"
_EVENTS_JSONL = "dev/reports/audits/devctl_events.jsonl"
_BRIDGE_MD = "bridge.md"
_MASTER_PLAN = "dev/active/MASTER_PLAN.md"
_GOVERNANCE_REVIEW_JSON = "dev/reports/governance/latest/review_summary.json"
_PROBE_SUMMARY_JSON = "dev/reports/probes/latest/summary.json"
_DATA_SCIENCE_JSON = "dev/reports/data_science/latest/summary.json"
_CODEX_CONDUCTOR_SESSION = "dev/reports/review_channel/latest/sessions/codex-conductor.json"
_CLAUDE_CONDUCTOR_SESSION = "dev/reports/review_channel/latest/sessions/claude-conductor.json"


def _read_json(path: Path) -> dict[str, Any] | None:
    """Read a JSON artifact, returning None on any failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None


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


def _age_seconds(utc_stamp: str) -> int | None:
    """Compute seconds elapsed since a UTC ISO-8601 timestamp, or None."""
    if not utc_stamp or utc_stamp == "n/a":
        return None
    try:
        ts = datetime.fromisoformat(utc_stamp.replace("Z", "+00:00"))
        return max(0, int((datetime.now(timezone.utc) - ts).total_seconds()))
    except (ValueError, TypeError):
        return None


def _format_age(seconds: int | None) -> str:
    """Human-readable short age string: '42s ago', '12m ago', '3h ago'."""
    if seconds is None:
        return "--"
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    return f"{seconds // 3600}h ago"


def _format_duration(seconds: int | None) -> str:
    """Human-readable short duration without 'ago': '42s', '45m', '2h 15m'."""
    if seconds is None:
        return "--"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    if mins:
        return f"{hours}h {mins}m"
    return f"{hours}h"


def _session_age(repo_root: Path) -> dict[str, Any]:
    """Read publisher heartbeat and compute session duration from started_at_utc."""
    data = _read_json(repo_root / _PUBLISHER_HB)
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
    path = repo_root / _MASTER_PLAN
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
    publisher = _read_heartbeat(repo_root / _PUBLISHER_HB)
    supervisor = _read_heartbeat(repo_root / _SUPERVISOR_HB)

    codex_conductor = _read_conductor_liveness(repo_root / _CODEX_CONDUCTOR_SESSION)
    claude_conductor = _read_conductor_liveness(repo_root / _CLAUDE_CONDUCTOR_SESSION)

    # Extract attention from full.json (compact does not carry it)
    full_data = _read_json(repo_root / _FULL_JSON)
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


def _tail_lines(path: Path, count: int = 10) -> list[str]:
    """Read the last *count* lines of a file without loading the entire file.

    Uses a seek-from-end strategy to handle large JSONL logs efficiently.
    Returns an empty list on any IO failure.
    """
    try:
        size = path.stat().st_size
    except OSError:
        return []
    if size == 0:
        return []
    # Read a generous trailing chunk — each JSONL line is typically under 1 KB
    chunk_size = min(size, count * 2048)
    try:
        with open(path, "rb") as fh:
            fh.seek(max(0, size - chunk_size))
            raw = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return []
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    return lines[-count:]


def _build_timeline_section(repo_root: Path) -> list[dict[str, str]]:
    """Build the TIMELINE section from the last 10 devctl event log entries."""
    raw_lines = _tail_lines(repo_root / _EVENTS_JSONL, count=10)
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


def _extract_time_from_iso(ts: str) -> str:
    """Pull HH:MM:SS from an ISO-8601 timestamp string."""
    if not ts:
        return "--:--:--"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return "--:--:--"


def build_snapshot(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Build a DashboardSnapshot dict from existing artifacts and git state."""
    git = _git_short()
    compact = _read_json(repo_root / _COMPACT_JSON)
    push_data = _read_json(repo_root / _PUSH_JSON)
    receipt = _read_json(repo_root / _RECEIPT_JSON)
    agents = _read_json(repo_root / _AGENTS_JSON)
    pipeline = _read_json(repo_root / _PIPELINE_JSON)
    bridge = _parse_bridge(repo_root / _BRIDGE_MD)
    bridge_findings = _parse_bridge_findings(repo_root / _BRIDGE_MD)
    plan = _parse_plan_progress(repo_root)
    gov_data = _read_json(repo_root / _GOVERNANCE_REVIEW_JSON)
    probe_data = _read_json(repo_root / _PROBE_SUMMARY_JSON)
    ds_data = _read_json(repo_root / _DATA_SCIENCE_JSON)

    session_info = _session_age(repo_root)

    return _assemble(
        git, compact, push_data, receipt, agents, pipeline, bridge, plan,
        gov_data=gov_data, probe_data=probe_data, ds_data=ds_data,
        bridge_findings=bridge_findings,
        session_info=session_info,
        repo_root=repo_root,
    )


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
) -> dict[str, Any]:
    """Assemble the typed DashboardSnapshot from raw sources."""
    session = (compact or {}).get("current_session", {})
    doctor = (compact or {}).get("doctor", {})
    instruction_rev = session.get("current_instruction_revision", "n/a")

    reviewer_agent = _find_agent(agents, "codex")
    implementer_agent = _find_agent(agents, "claude")

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

    snapshot: dict[str, Any] = {
        "schema_version": 2,
        "contract_id": "DashboardSnapshot",
        "timestamp": utc_timestamp(),
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
        "analytics": _build_analytics_section(ds_data),
        "coordination": _build_coordination_section(session, instruction_rev, receipt_push, bridge, doctor, session_info or {}),
        "codex_activity": _build_codex_activity_section(bridge),
        "flow": _build_flow_section(receipt, push_data, session),
        "timeline": _build_timeline_section(repo_root),
    }
    snapshot["summary"] = _compile_summary(snapshot)
    return snapshot


def _compile_summary(snapshot: dict) -> dict:
    """Compile raw dashboard state into prioritized operator conclusions.

    Reads only from the already-assembled snapshot sections — no new artifact
    IO.  Every derived field is deterministic from snapshot data.
    """
    quality = snapshot.get("quality", {})
    health = snapshot.get("health", {})
    now = snapshot.get("now", {})
    review = snapshot.get("review", {})
    coordination = snapshot.get("coordination", {})
    publication = snapshot.get("publication", {})

    # --- infra_state: based on daemon running counts ---
    active_daemons = health.get("active_daemons", 0)
    if active_daemons >= 2:
        infra_state = "healthy"
    elif active_daemons == 1:
        infra_state = "degraded"
    else:
        infra_state = "down"
    infra_label = (
        f"{active_daemons} daemon{'s' if active_daemons != 1 else ''} running"
    )

    # --- quality failures ---
    failing = quality.get("failing", [])
    quality_gates = ["docs_gate", "plan_sync", "bridge", "code_shape",
                     "instr_sync", "clippy"]
    gate_failures = [
        g for g in quality_gates if quality.get(g, "").upper() == "FAIL"
    ]
    has_quality_fail = bool(gate_failures)

    # --- reviewer staleness ---
    attention_status = health.get("attention_status", "n/a")
    attention_not_healthy = attention_status not in ("healthy", "n/a")
    reviewer_age_label = coordination.get("reviewer_age", "--")
    reviewer_overdue = _is_reviewer_overdue(reviewer_age_label)

    # --- overall_state ---
    if has_quality_fail or attention_not_healthy:
        overall_state = "blocked"
    elif reviewer_overdue:
        overall_state = "waiting"
    elif now.get("owner") == "Implementer":
        overall_state = "active"
    else:
        overall_state = "healthy"

    # --- block_class ---
    block_parts: list[str] = []
    if has_quality_fail:
        block_parts.append("quality")
    if reviewer_overdue:
        block_parts.append("reviewer")
    pub_state = publication.get("effective", "n/a")
    if pub_state in ("NOT CURRENT", "STALE"):
        block_parts.append("push")
    block_class = " + ".join(block_parts) if block_parts else "none"

    # --- next_actor ---
    if reviewer_overdue:
        next_actor = "reviewer"
    elif now.get("owner", "").lower() == "implementer":
        next_actor = "implementer"
    else:
        next_actor = "operator"

    # --- next_command_hint ---
    if has_quality_fail:
        next_command_hint = "fix code-shape debt"
    elif reviewer_overdue:
        next_command_hint = "relaunch Codex"
    elif pub_state in ("NOT CURRENT", "STALE"):
        next_command_hint = "run check --profile ci"
    else:
        next_command_hint = "continue current slice"

    # --- primary_blocker ---
    top_blocker = now.get("top_blocker", "none")
    if top_blocker and top_blocker != "none":
        primary_blocker = top_blocker
    elif gate_failures:
        fail_file = failing[0] if failing else "unknown"
        primary_blocker = f"{gate_failures[0]} fail in {fail_file}"
    else:
        primary_blocker = "none"

    # --- secondary_blocker ---
    if attention_not_healthy:
        secondary_blocker = f"Attention {attention_status}"
    elif reviewer_overdue:
        secondary_blocker = f"Reviewer heartbeat stale ({reviewer_age_label})"
    else:
        secondary_blocker = "none"

    # --- one_line ---
    one_line = _build_one_line(
        overall_state, infra_state, now, reviewer_overdue,
        has_quality_fail, gate_failures, pub_state,
    )

    return {
        "overall_state": overall_state,
        "block_class": block_class,
        "next_actor": next_actor,
        "next_command_hint": next_command_hint,
        "infra_state": infra_state,
        "infra_label": infra_label,
        "primary_blocker": primary_blocker,
        "secondary_blocker": secondary_blocker,
        "one_line": one_line,
    }


def _is_reviewer_overdue(age_label: str) -> bool:
    """Return True when the reviewer age label indicates staleness (>10 min)."""
    if not age_label or age_label == "--":
        return False
    if age_label.endswith("h ago"):
        return True
    if age_label.endswith("m ago"):
        try:
            minutes = int(age_label.replace("m ago", "").strip())
            return minutes > 10
        except ValueError:
            return False
    return False


def _build_one_line(
    overall_state: str,
    infra_state: str,
    now: dict[str, Any],
    reviewer_overdue: bool,
    has_quality_fail: bool,
    gate_failures: list[str],
    pub_state: str,
) -> str:
    """Compile all summary signals into one readable operator sentence."""
    parts: list[str] = []
    owner = now.get("owner", "unknown")
    parts.append(f"{owner} active")
    parts.append(f"infra {infra_state}")
    if reviewer_overdue:
        parts.append("reviewer stale")
    if has_quality_fail:
        gates = ", ".join(gate_failures)
        parts.append(f"quality gate failing on {gates}")
    if pub_state in ("NOT CURRENT", "STALE"):
        parts.append("push blocked")
    if overall_state == "healthy":
        parts.append("all green")
    return "; ".join(parts) + "."


def _derive_top_blocker(
    quality: dict[str, Any], session: dict[str, Any], doctor: dict[str, Any],
) -> str:
    """Identify the single most important blocker from quality gates and findings."""
    # Quality gate failures first
    failing = quality.get("failing", [])
    if failing:
        return f"code-shape debt in {failing[0]}"
    # Doctor blocked reason
    blocked = doctor.get("blocked_reason", "")
    if blocked and blocked != "pipeline_unavailable":
        return blocked
    # Open findings
    findings = session.get("open_findings", "")
    if findings and findings.strip().lower() not in ("none", ""):
        first_line = findings.strip().splitlines()[0].lstrip("- ").strip()
        return first_line[:60] + ("..." if len(first_line) > 60 else "")
    return "none"


def _build_now_section(
    bridge: dict[str, str],
    reviewer: dict[str, Any],
    implementer: dict[str, Any],
    session: dict[str, Any],
    top_blocker: str,
    last_change_age: int | None,
) -> dict[str, Any]:
    """Build the NOW section: who owns the loop right now and what they should do."""
    impl_state = implementer.get("job_state", "n/a")
    owner = "Implementer" if impl_state == "implementing" else "Reviewer"
    reviewer_provider = reviewer.get("provider", "n/a")
    impl_provider = implementer.get("provider", "n/a")
    owner_provider = impl_provider if owner == "Implementer" else reviewer_provider

    # Derive next action from session state
    next_action = session.get("implementer_status", "")
    if not next_action or next_action == "n/a":
        next_action = "review worker results and checkpoint"
    else:
        first_line = next_action.strip().splitlines()[0].lstrip("- ").strip()
        next_action = first_line[:60] + ("..." if len(first_line) > 60 else "")

    # Truncate bridge instruction to 100 chars for the NOW section
    instr_full = bridge.get("instruction_full", "n/a")
    if instr_full and instr_full != "n/a":
        first_line = instr_full.strip().splitlines()[0].lstrip("- ").strip()
        instr_text = first_line[:100] + ("..." if len(first_line) > 100 else "")
    else:
        instr_text = "n/a"

    return {
        "owner": owner,
        "owner_provider": owner_provider,
        "next_action": next_action,
        "top_blocker": top_blocker,
        "last_change_age_s": last_change_age,
        "last_change_label": _format_age(last_change_age),
        "instruction_text": instr_text,
    }


def _find_agent(agents_data: dict[str, Any] | None, provider: str) -> dict[str, Any]:
    """Find an agent entry by provider name."""
    if not agents_data:
        return {}
    for agent in agents_data.get("agents", []):
        if agent.get("provider") == provider:
            return agent
    return {}


def _build_review_section(
    bridge: dict[str, str],
    reviewer: dict[str, Any],
    implementer: dict[str, Any],
    session: dict[str, Any],
) -> dict[str, Any]:
    reviewer_state = reviewer.get("job_state", "n/a")
    implementer_state = implementer.get("job_state", "n/a")
    current_turn = "Implementer" if implementer_state == "implementing" else "Reviewer"
    instruction_text = session.get("current_instruction", bridge.get("instruction", "n/a"))
    if instruction_text and len(instruction_text) > 120:
        instruction_text = instruction_text[:120] + "..."
    return {
        "reviewer_state": reviewer_state,
        "reviewer_provider": reviewer.get("provider", "n/a"),
        "implementer_state": implementer_state,
        "implementer_provider": implementer.get("provider", "n/a"),
        "current_turn": current_turn,
        "instruction": instruction_text,
        "last_poll": bridge.get("last_poll", "n/a"),
        "mode": bridge.get("reviewer_mode", "n/a"),
    }


def _build_workers_section(agents_data: dict[str, Any] | None) -> list[dict[str, str]]:
    """Build worker rows with scope, state, age, and last update summary."""
    if not agents_data:
        return []
    workers = []
    for idx, a in enumerate(agents_data.get("agents", []), start=1):
        updated = a.get("updated_at", "")
        age = _age_seconds(updated)
        workers.append({
            "id": f"W{idx}",
            "agent_id": a.get("agent_id", "unknown"),
            "scope": a.get("lane_title", a.get("current_job", "unknown")),
            "provider": a.get("provider", "unknown"),
            "state": a.get("job_state", "unknown").upper(),
            "age": _format_age(age),
            "last_update": a.get("waiting_on", ""),
        })
    return workers


def _build_plan_section(
    plan: dict[str, str],
    session: dict[str, Any],
    bridge_findings: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build the PLAN section from master plan data, session findings, and bridge detail."""
    findings_text = (session.get("open_findings") or "").strip()
    finding_count = 0
    if findings_text and findings_text.lower() != "none":
        finding_count = len([
            ln for ln in findings_text.splitlines()
            if ln.strip().startswith("- F") or ln.strip().startswith("-")
        ])
    # Prefer bridge-parsed structured findings when available
    detail = bridge_findings or []
    if detail:
        finding_count = len(detail)
    return {
        "slice": plan.get("slice", "n/a"),
        "progress": plan.get("progress", "n/a"),
        "open_findings": finding_count,
        "findings_detail": detail,
        "pending": 0,
    }


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

    # Publication state label combining push + post-push
    if published and stages.get("post_push_green"):
        state_label = "PUBLISHED_REMOTE / POST_PUSH_GREEN"
    elif published:
        state_label = "PUBLISHED_REMOTE / POST_PUSH_NOT_GREEN"
    else:
        state_label = "NOT_PUBLISHED"

    # Target match fields
    branch_match = push_branch == current_branch
    head_match = push_head == current_head
    target_match = stages.get("validation_ready", False)
    remote_match = published

    return {
        "state": state_label,
        "effective": effective,
        "why": why,
        "post_push": post_push if push_data else "n/a",
        "evidence": _PUSH_JSON if push_data else "n/a",
        "target_match": {
            "branch": branch_match,
            "head": head_match,
            "target": target_match,
            "remote": remote_match,
        },
    }


def _build_quality_section(push_data: dict[str, Any] | None) -> dict[str, Any]:
    """Build multi-gate quality section with failing file list."""
    base = {
        "docs_gate": "n/a", "plan_sync": "n/a", "code_shape": "n/a",
        "instr_sync": "n/a", "bridge": "n/a", "clippy": "n/a",
        "failing": [],
    }
    if push_data is None:
        return base
    preflight = push_data.get("preflight_step", {})
    preflight_ok = preflight.get("returncode", -1) == 0 if preflight else None
    base["code_shape"] = "PASS" if preflight_ok else ("FAIL" if preflight_ok is False else "n/a")

    # Extract failing files from preflight output
    if preflight_ok is False:
        failure_out = preflight.get("failure_output", "")
        failing_files = _extract_failing_files(failure_out)
        base["failing"] = failing_files

    return base


def _extract_failing_files(output: str) -> list[str]:
    """Pull file paths from preflight failure output."""
    files: list[str] = []
    for line in output.splitlines():
        stripped = line.strip()
        # Look for paths like dev/scripts/... or rust/src/...
        path_match = re.search(r"((?:dev|rust|app)/\S+\.(?:py|rs|md))", stripped)
        if path_match and path_match.group(1) not in files:
            files.append(path_match.group(1))
            if len(files) >= 5:
                break
    return files


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
    """Build audit section from governance review summary stats."""
    na: dict[str, Any] = {
        "total_findings": "n/a", "fixed_count": "n/a",
        "cleanup_rate_pct": "n/a", "open_finding_count": "n/a",
    }
    if gov_data is None:
        return na
    stats = gov_data.get("stats", {})
    return {
        "total_findings": stats.get("total_findings", "n/a"),
        "fixed_count": stats.get("fixed_count", "n/a"),
        "cleanup_rate_pct": stats.get("cleanup_rate_pct", "n/a"),
        "open_finding_count": stats.get("open_finding_count", "n/a"),
    }


def _build_probes_section(probe_data: dict[str, Any] | None) -> dict[str, Any]:
    """Build probe quality summary from probe report summary."""
    na: dict[str, Any] = {
        "risk_hints": "n/a", "high": "n/a", "medium": "n/a",
        "probes_enabled": "n/a", "files_scanned": "n/a",
    }
    if probe_data is None:
        return na
    summary = probe_data.get("summary", {})
    severity = summary.get("hints_by_severity", {})
    return {
        "risk_hints": summary.get("risk_hints", "n/a"),
        "high": severity.get("high", 0),
        "medium": severity.get("medium", 0),
        "probes_enabled": summary.get("probe_count", "n/a"),
        "files_scanned": summary.get("files_scanned", "n/a"),
    }


def _build_analytics_section(ds_data: dict[str, Any] | None) -> dict[str, Any]:
    """Build analytics section from data science summary."""
    na: dict[str, Any] = {
        "avg_time_to_green_s": "n/a", "total_events": "n/a",
        "command_success_rate_pct": "n/a",
    }
    if ds_data is None:
        return na
    watchdog = ds_data.get("watchdog_stats", {})
    events = ds_data.get("event_stats", {})
    return {
        "avg_time_to_green_s": watchdog.get("avg_time_to_green_seconds", "n/a"),
        "total_events": events.get("total_events", "n/a"),
        "command_success_rate_pct": events.get("success_rate_pct", "n/a"),
    }


def _build_coordination_section(
    session: dict[str, Any],
    instruction_rev: str,
    receipt_push: str,
    bridge: dict[str, str],
    doctor: dict[str, Any],
    session_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build compact coordination section with dual-field layout."""
    findings = (session.get("open_findings") or "None").strip()
    finding_lines = [
        ln for ln in findings.splitlines() if ln.strip().startswith("-")
    ] if findings.lower() != "none" else []

    # Compute reviewer age from bridge poll
    reviewer_age = _age_seconds(bridge.get("last_poll_utc", ""))

    return {
        "pending_packets": 0,
        "instruction_rev": instruction_rev,
        "reviewer_age": _format_age(reviewer_age),
        "implementer_state": "current" if session.get("implementer_ack_state") == "current" else "stale",
        "pending_findings": f"{len(finding_lines)} findings" if finding_lines else "0 findings",
        "next_action": receipt_push,
        "session_age": (session_info or {}).get("session_label", "--"),
        "session_started": (session_info or {}).get("started_time", ""),
    }


def _build_flow_section(
    receipt: dict[str, Any] | None,
    push_data: dict[str, Any] | None,
    session: dict[str, Any],
) -> dict[str, Any]:
    stages = {
        "review": "unknown",
        "implement": "unknown",
        "verify": "unknown",
        "checkpoint": "unknown",
        "push": "unknown",
    }
    if receipt:
        if receipt.get("push_eligible_now"):
            stages["checkpoint"] = "pass"
        if receipt.get("review_gate_allows_push"):
            stages["review"] = "pass"
        if receipt.get("safe_to_continue_editing"):
            stages["implement"] = "active"
    if push_data:
        push_ok = push_data.get("ok")
        stages["push"] = "pass" if push_ok else "blocked"
    impl_state = session.get("implementer_status", "")
    if impl_state:
        stages["implement"] = "active"
    return stages


def _build_codex_activity_section(bridge: dict[str, str]) -> dict[str, Any]:
    """Build REVIEWER (Codex) activity section from bridge.md parsed fields.

    Answers the operator's core question: 'Is Codex doing anything?'
    """
    poll_utc = bridge.get("last_poll_utc", "")
    poll_age = _format_age(_age_seconds(poll_utc))

    verdict_raw = bridge.get("verdict", "n/a")
    verdict_first_line = _first_meaningful_line(verdict_raw)
    verdict_summary = verdict_first_line[:80] + ("..." if len(verdict_first_line) > 80 else "")

    findings_raw = bridge.get("findings_raw", "")
    finding_lines = [
        ln for ln in findings_raw.splitlines()
        if ln.strip().startswith("- F") or ln.strip().startswith("-")
    ] if findings_raw else []
    findings_posted = len(finding_lines)

    scope_raw = bridge.get("reviewed_scope_raw", "")
    scope_lines = [
        ln for ln in scope_raw.splitlines()
        if ln.strip().startswith("- ") or ln.strip().startswith("*")
    ] if scope_raw else []
    reviewed_files = len(scope_lines)

    instr_full = bridge.get("instruction_full", "n/a")
    instr_first = _first_meaningful_line(instr_full)
    instruction_summary = instr_first[:80] + ("..." if len(instr_first) > 80 else "")

    return {
        "last_poll_age": poll_age,
        "last_verdict": verdict_summary if verdict_summary != "n/a" else "n/a",
        "reviewed_files": reviewed_files,
        "instruction_summary": instruction_summary if instruction_summary != "n/a" else "n/a",
        "findings_posted": findings_posted,
    }


def _first_meaningful_line(text: str) -> str:
    """Return the first non-empty line from text, stripping leading '- '."""
    if not text or text == "n/a":
        return "n/a"
    for line in text.splitlines():
        stripped = line.strip().lstrip("- ").strip()
        if stripped:
            return stripped
    return "n/a"


def run(args) -> int:
    """Build and render the governance dashboard."""
    from .dashboard_render import render_json, render_markdown, render_terminal

    snapshot = build_snapshot()

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
