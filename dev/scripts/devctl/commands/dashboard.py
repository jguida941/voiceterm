"""devctl dashboard command — governance snapshot from existing artifacts."""

from __future__ import annotations

import json
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
_PUSH_JSON = "dev/reports/push/latest.json"
_RECEIPT_JSON = "dev/reports/startup/latest/receipt.json"
_AGENTS_JSON = "dev/reports/review_channel/latest/registry/agents.json"
_PIPELINE_JSON = "dev/reports/review_channel/latest/commit_pipeline.json"
_BRIDGE_MD = "bridge.md"
_MASTER_PLAN = "dev/active/MASTER_PLAN.md"


def _read_json(path: Path) -> dict[str, Any] | None:
    """Read a JSON artifact, returning None on any failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def _git_short() -> dict[str, str]:
    """Return branch, HEAD short sha, and dirty state from git."""
    result: dict[str, str] = {
        "branch": "unknown",
        "head": "unknown",
        "dirty": "unknown",
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
            result["dirty"] = "DIRTY" if len(lines) > 1 else "CLEAN"
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, timeout=5, cwd=str(REPO_ROOT),
        )
        parts = log.stdout.strip().split(None, 1)
        if parts:
            result["head"] = parts[0]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return result


def _parse_bridge(path: Path) -> dict[str, str]:
    """Extract lightweight coordination fields from bridge.md."""
    fields: dict[str, str] = {
        "last_poll": "n/a",
        "last_poll_utc": "",
        "reviewer_mode": "n/a",
        "instruction": "n/a",
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
    return fields


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


def build_snapshot(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Build a DashboardSnapshot dict from existing artifacts and git state."""
    git = _git_short()
    compact = _read_json(repo_root / _COMPACT_JSON)
    push_data = _read_json(repo_root / _PUSH_JSON)
    receipt = _read_json(repo_root / _RECEIPT_JSON)
    agents = _read_json(repo_root / _AGENTS_JSON)
    pipeline = _read_json(repo_root / _PIPELINE_JSON)
    bridge = _parse_bridge(repo_root / _BRIDGE_MD)
    plan = _parse_plan_progress(repo_root)

    return _assemble(git, compact, push_data, receipt, agents, pipeline, bridge, plan)


def _assemble(
    git: dict[str, str],
    compact: dict[str, Any] | None,
    push_data: dict[str, Any] | None,
    receipt: dict[str, Any] | None,
    agents: dict[str, Any] | None,
    pipeline: dict[str, Any] | None,
    bridge: dict[str, str],
    plan: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Assemble the typed DashboardSnapshot from raw sources."""
    session = (compact or {}).get("current_session", {})
    doctor = (compact or {}).get("doctor", {})
    instruction_rev = session.get("current_instruction_revision", "n/a")

    reviewer_agent = _find_agent(agents, "codex")
    implementer_agent = _find_agent(agents, "claude")

    receipt_push = (receipt or {}).get("push_action", "n/a")

    publication_effective = _publication_effective(push_data, receipt, git)
    quality = _build_quality_section(push_data)

    # Derive top blocker from quality failures or open findings
    top_blocker = _derive_top_blocker(quality, session, doctor)

    # Compute last-change age from bridge poll timestamp
    poll_utc = bridge.get("last_poll_utc", "")
    last_change_age = _age_seconds(poll_utc)

    return {
        "schema_version": 2,
        "contract_id": "DashboardSnapshot",
        "timestamp": utc_timestamp(),
        "repo": {
            "name": _repo_name(),
            "branch": git["branch"],
            "head": git["head"],
            "worktree": git["dirty"],
        },
        "now": _build_now_section(
            bridge, reviewer_agent, implementer_agent, session,
            top_blocker, last_change_age,
        ),
        "review": _build_review_section(bridge, reviewer_agent, implementer_agent, session),
        "workers": _build_workers_section(agents),
        "plan": _build_plan_section(plan or {}, session),
        "publication": publication_effective,
        "quality": quality,
        "coordination": _build_coordination_section(session, instruction_rev, receipt_push, bridge, doctor),
        "flow": _build_flow_section(receipt, push_data, session),
    }


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

    return {
        "owner": owner,
        "owner_provider": owner_provider,
        "next_action": next_action,
        "top_blocker": top_blocker,
        "last_change_age_s": last_change_age,
        "last_change_label": _format_age(last_change_age),
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
    plan: dict[str, str], session: dict[str, Any],
) -> dict[str, Any]:
    """Build the PLAN section from master plan data and session findings."""
    findings_text = (session.get("open_findings") or "").strip()
    finding_count = 0
    if findings_text and findings_text.lower() != "none":
        finding_count = len([
            ln for ln in findings_text.splitlines()
            if ln.strip().startswith("- F") or ln.strip().startswith("-")
        ])
    return {
        "slice": plan.get("slice", "n/a"),
        "progress": plan.get("progress", "n/a"),
        "open_findings": finding_count,
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


def _build_coordination_section(
    session: dict[str, Any],
    instruction_rev: str,
    receipt_push: str,
    bridge: dict[str, str],
    doctor: dict[str, Any],
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


def run(args) -> int:
    """Build and render the governance dashboard."""
    from .dashboard_render import render_json, render_markdown, render_terminal

    snapshot = build_snapshot()

    fmt = getattr(args, "format", "terminal")
    if fmt == "json":
        output = render_json(snapshot)
    elif fmt == "md":
        output = render_markdown(snapshot)
    else:
        output = render_terminal(snapshot)

    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return 0
