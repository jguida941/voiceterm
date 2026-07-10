"""Shared support helpers for bounded CodeRabbit loop checks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class LoopReportRequest:
    repo: str
    branch: str
    workflow: str
    max_attempts: int
    fix_command: str | None
    fix_block_reason: str | None = None
    source_run_id: int | None = None
    source_run_sha: str | None = None
    source_event: str | None = None


def normalize_sha(value: str | None) -> str:
    return str(value or "").strip().lower()


def load_backlog_payload(root: Path) -> tuple[dict, str | None]:
    candidates = sorted(root.rglob("backlog-medium.json"))
    if not candidates:
        return {}, "missing backlog-medium.json in downloaded artifacts"
    path = candidates[0]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return {}, str(exc)
    except json.JSONDecodeError as exc:
        return {}, f"invalid json ({exc})"
    if not isinstance(payload, dict):
        return {}, "backlog payload is not an object"
    return payload, None


def build_report(request: LoopReportRequest) -> dict:
    normalized_source_sha = normalize_sha(request.source_run_sha)
    return {
        "command": "run_coderabbit_ralph_loop",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": False,
        "repo": request.repo,
        "branch": request.branch,
        "workflow": request.workflow,
        "max_attempts": request.max_attempts,
        "completed_attempts": 0,
        "attempts": [],
        "unresolved_count": 0,
        "reason": "",
        "fix_command_configured": bool(request.fix_command),
        "fix_block_reason": request.fix_block_reason,
        "escalation_needed": False,
        "source_run_id": (
            request.source_run_id
            if request.source_run_id and request.source_run_id > 0
            else None
        ),
        "source_run_sha": normalized_source_sha or None,
        "source_event": str(request.source_event or "workflow_dispatch"),
        "source_correlation": (
            "pending" if request.source_run_id else "branch_latest_fallback"
        ),
        "backlog_pr_number": None,
        "backlog_head_sha": None,
    }
