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
            fields["last_poll"] = stripped.split(":", 1)[1].strip().strip("`")
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

    return _assemble(git, compact, push_data, receipt, agents, pipeline, bridge)


def _assemble(
    git: dict[str, str],
    compact: dict[str, Any] | None,
    push_data: dict[str, Any] | None,
    receipt: dict[str, Any] | None,
    agents: dict[str, Any] | None,
    pipeline: dict[str, Any] | None,
    bridge: dict[str, str],
) -> dict[str, Any]:
    """Assemble the typed DashboardSnapshot from raw sources."""
    session = (compact or {}).get("current_session", {})
    instruction_rev = session.get("current_instruction_revision", "n/a")

    reviewer_agent = _find_agent(agents, "codex")
    implementer_agent = _find_agent(agents, "claude")

    push_ok = (push_data or {}).get("ok", None)
    push_status = (push_data or {}).get("status", "n/a")
    receipt_push = (receipt or {}).get("push_action", "n/a")

    publication_effective = _publication_effective(push_data, receipt, git)

    return {
        "schema_version": 1,
        "contract_id": "DashboardSnapshot",
        "timestamp": utc_timestamp(),
        "repo": {
            "name": _repo_name(),
            "branch": git["branch"],
            "head": git["head"],
            "worktree": git["dirty"],
        },
        "review": _build_review_section(bridge, reviewer_agent, implementer_agent, session),
        "workers": _build_workers_section(agents),
        "publication": publication_effective,
        "quality": _build_quality_section(push_data),
        "coordination": {
            "pending_findings": (session.get("open_findings") or "None").strip(),
            "next_action": receipt_push,
            "instruction_rev": instruction_rev,
        },
        "flow": _build_flow_section(receipt, push_data, session),
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
    if not agents_data:
        return []
    return [
        {
            "id": a.get("agent_id", "unknown"),
            "role": a.get("lane_title", "unknown"),
            "provider": a.get("provider", "unknown"),
            "state": a.get("job_state", "unknown"),
        }
        for a in agents_data.get("agents", [])
    ]


def _publication_effective(
    push_data: dict[str, Any] | None,
    receipt: dict[str, Any] | None,
    git: dict[str, str],
) -> dict[str, Any]:
    if push_data is None and receipt is None:
        return {"effective": "n/a", "why": "no artifacts", "post_push": "n/a", "evidence": "n/a"}
    push_ok = (push_data or {}).get("ok")
    push_branch = (push_data or {}).get("branch", "")
    push_head = (push_data or {}).get("head_commit", "")[:7]
    current_head = git.get("head", "")

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

    post_push_stages = (push_data or {}).get("push_stages", {})
    post_push = "PASS" if post_push_stages.get("post_push_green") else "FAIL"

    return {
        "effective": effective,
        "why": why,
        "post_push": post_push if push_data else "n/a",
        "evidence": _PUSH_JSON if push_data else "n/a",
    }


def _build_quality_section(push_data: dict[str, Any] | None) -> dict[str, Any]:
    if push_data is None:
        return {"docs_gate": "n/a", "plan_sync": "n/a", "code_shape": "n/a"}
    preflight = push_data.get("preflight_step", {})
    preflight_ok = preflight.get("returncode", -1) == 0 if preflight else None
    return {
        "docs_gate": "n/a",
        "plan_sync": "n/a",
        "code_shape": "PASS" if preflight_ok else ("FAIL" if preflight_ok is False else "n/a"),
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
