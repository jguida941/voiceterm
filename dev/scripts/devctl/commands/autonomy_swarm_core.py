"""Core execution helpers for the `devctl autonomy-swarm` command."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..autonomy_swarm_helpers import slug
from ..config import REPO_ROOT


@dataclass(frozen=True)
class AgentTask:
    index: int
    name: str
    output_dir: Path


def safe_int(value: Any, default: int = 0) -> int:
    """Convert value to int with a stable fallback."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def agent_plan_id(run_label: str, index: int) -> str:
    """Build a deterministic per-agent plan identifier."""
    return slug(f"{run_label}-agent-{index:02d}", fallback=f"agent-{index:02d}")


def build_autonomy_loop_command(args, task: AgentTask, run_label: str) -> list[str]:
    """Construct an `autonomy-loop` invocation for one swarm worker."""
    packet_out = task.output_dir / "packets"
    queue_out = task.output_dir / "queue"
    md_output = task.output_dir / "autonomy-loop.md"
    json_output = task.output_dir / "autonomy-loop.json"

    command = [
        "python3",
        "dev/scripts/devctl.py",
        "autonomy-loop",
        "--plan-id",
        agent_plan_id(run_label, task.index),
        "--repo",
        str(args.repo),
        "--branch-base",
        str(args.branch_base),
        "--mode",
        str(args.mode),
        "--max-rounds",
        str(int(args.max_rounds)),
        "--max-hours",
        str(float(args.max_hours)),
        "--max-tasks",
        str(int(args.max_tasks)),
        "--checkpoint-every",
        str(int(args.checkpoint_every)),
        "--loop-max-attempts",
        str(int(args.loop_max_attempts)),
        "--packet-out",
        str(packet_out),
        "--queue-out",
        str(queue_out),
        "--format",
        "md",
        "--output",
        str(md_output),
        "--json-output",
        str(json_output),
    ]
    fix_command = str(args.fix_command or "").strip()
    if fix_command:
        command.extend(["--fix-command", fix_command])
    if bool(args.dry_run):
        command.append("--dry-run")
    return command


def run_one_agent(task: AgentTask, args, run_label: str) -> dict[str, Any]:
    """Execute one worker and return a normalized result row."""
    task.output_dir.mkdir(parents=True, exist_ok=True)
    command = build_autonomy_loop_command(args, task, run_label)
    stdout_log = task.output_dir / "stdout.log"
    stderr_log = task.output_dir / "stderr.log"
    json_report = task.output_dir / "autonomy-loop.json"

    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=max(60, safe_int(args.agent_timeout_seconds, default=1800)),
            check=False,
        )
        stdout_text = str(result.stdout or "")
        stderr_text = str(result.stderr or "")
        stdout_log.write_text(stdout_text, encoding="utf-8")
        stderr_log.write_text(stderr_text, encoding="utf-8")
        rc = int(result.returncode)
        timeout_error = None
    except subprocess.TimeoutExpired as exc:
        stdout_text = str(exc.stdout or "")
        stderr_text = str(exc.stderr or "")
        stdout_log.write_text(stdout_text, encoding="utf-8")
        stderr_log.write_text(stderr_text, encoding="utf-8")
        rc = 124
        timeout_error = f"timeout after {args.agent_timeout_seconds}s"

    payload: dict[str, Any] = {}
    if json_report.exists():
        try:
            parsed = json.loads(json_report.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                payload = parsed
        except (OSError, json.JSONDecodeError):
            payload = {}

    stderr_head = stderr_text.strip().splitlines()[0] if stderr_text.strip() else ""
    stdout_head = stdout_text.strip().splitlines()[0] if stdout_text.strip() else ""
    row = {
        "agent": task.name,
        "index": task.index,
        "returncode": rc,
        "ok": bool(payload.get("ok", False)) if payload else False,
        "resolved": bool(payload.get("resolved", False)) if payload else False,
        "reason": str(
            payload.get("reason")
            or timeout_error
            or stderr_head
            or stdout_head
            or "unknown"
        ),
        "rounds_completed": safe_int(payload.get("rounds_completed"), default=0),
        "tasks_completed": safe_int(payload.get("tasks_completed"), default=0),
        "report_json": str(json_report),
        "report_md": str(task.output_dir / "autonomy-loop.md"),
        "stdout_log": str(stdout_log),
        "stderr_log": str(stderr_log),
    }
    if timeout_error:
        row["timeout_error"] = timeout_error
    return row


def validate_args(args) -> str | None:
    """Validate command arguments and return a user-facing error message."""
    if args.agents is not None and int(args.agents) < 1:
        return "Error: --agents must be >= 1"
    if int(args.min_agents) < 1:
        return "Error: --min-agents must be >= 1"
    if int(args.max_agents) < int(args.min_agents):
        return "Error: --max-agents must be >= --min-agents"
    if int(args.parallel_workers) < 1:
        return "Error: --parallel-workers must be >= 1"
    if int(args.max_rounds) < 1 or int(args.max_tasks) < 1:
        return "Error: --max-rounds and --max-tasks must be >= 1"
    if float(args.max_hours) <= 0:
        return "Error: --max-hours must be > 0"
    if int(args.loop_max_attempts) < 1:
        return "Error: --loop-max-attempts must be >= 1"
    mode = str(args.mode)
    fix_command = str(args.fix_command or "").strip()
    if mode in {"plan-then-fix", "fix-only"} and not fix_command:
        return (
            "Error: --fix-command is required when --mode is plan-then-fix/fix-only "
            "(otherwise no remediation can run)"
        )
    return None


def fallback_repo_from_origin() -> str | None:
    """Resolve `owner/repo` from `remote.origin.url`."""
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    raw = str(result.stdout or "").strip()
    if not raw:
        return None
    match = re.search(
        r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$", raw
    )
    if not match:
        return None
    owner = str(match.group("owner")).strip()
    repo = str(match.group("repo")).strip()
    if not owner or not repo:
        return None
    return f"{owner}/{repo}"
