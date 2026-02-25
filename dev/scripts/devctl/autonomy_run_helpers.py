"""Helper utilities for `devctl swarm_run`."""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import REPO_ROOT
from .numeric import to_int

CHECKBOX_PATTERN = re.compile(r"^\s*-\s*\[\s\]\s+(?P<text>.+?)\s*$")


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def fallback_repo_from_origin() -> str | None:
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


def collect_next_steps(plan_text: str, *, limit: int) -> list[str]:
    steps: list[str] = []
    for line in plan_text.splitlines():
        match = CHECKBOX_PATTERN.match(line)
        if not match:
            continue
        normalized = re.sub(r"\s+", " ", match.group("text")).strip()
        if not normalized:
            continue
        steps.append(normalized)
        if len(steps) >= max(1, limit):
            break
    return steps


def derive_prompt(
    *,
    plan_doc: str,
    mp_scope: str,
    next_steps: list[str],
    explicit_question: str | None,
) -> str:
    explicit = str(explicit_question or "").strip()
    if explicit:
        return explicit

    lines = [
        f"Execute the next tracked checklist items for `{plan_doc}` under `{mp_scope}`.",
        "",
        "Target steps:",
    ]
    if not next_steps:
        lines.append(
            "- (no unchecked checklist items found; run governance + produce audit evidence)"
        )
    else:
        for item in next_steps:
            lines.append(f"- {item}")
    return "\n".join(lines)


def run_command(command: list[str], *, timeout_seconds: int = 0) -> dict[str, Any]:
    timeout = timeout_seconds if timeout_seconds > 0 else None
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        return {
            "command": command,
            "returncode": int(result.returncode),
            "ok": result.returncode == 0,
            "stdout": str(result.stdout or ""),
            "stderr": str(result.stderr or ""),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": 124,
            "ok": False,
            "stdout": str(exc.stdout or ""),
            "stderr": str(exc.stderr or ""),
            "timeout_error": f"timeout after {timeout_seconds}s",
        }


def build_swarm_command(
    args,
    *,
    prompt_path: Path,
    run_label: str,
    output_md: Path,
    output_json: Path,
    agent_override: int | None = None,
) -> list[str]:
    command: list[str] = [
        "python3",
        "dev/scripts/devctl.py",
        "autonomy-swarm",
        "--run-label",
        run_label,
        "--output-root",
        str(args.swarm_output_root),
        "--question-file",
        str(prompt_path),
        "--branch-base",
        str(args.branch_base),
        "--mode",
        str(args.mode),
        "--diff-ref",
        str(args.diff_ref),
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
        "--parallel-workers",
        str(int(args.parallel_workers)),
        "--agent-timeout-seconds",
        str(int(args.agent_timeout_seconds)),
        "--post-audit",
        "--reviewer-lane",
        "--audit-source-root",
        str(args.audit_source_root),
        "--audit-library-root",
        str(args.audit_library_root),
        "--audit-event-log",
        str(args.audit_event_log),
        "--format",
        "md",
        "--output",
        str(output_md),
        "--json-output",
        str(output_json),
    ]
    if args.repo:
        command.extend(["--repo", str(args.repo)])
    fix_command = str(args.fix_command or "").strip()
    if fix_command:
        command.extend(["--fix-command", fix_command])
    effective_agents = to_int(agent_override, default=0)
    if effective_agents > 0:
        command.extend(["--agents", str(effective_agents)])
    elif args.agents is not None:
        command.extend(["--agents", str(int(args.agents))])
    else:
        command.extend(
            [
                "--min-agents",
                str(int(args.min_agents)),
                "--max-agents",
                str(int(args.max_agents)),
            ]
        )
        command.append("--adaptive" if bool(args.adaptive) else "--no-adaptive")
    token_budget = to_int(args.token_budget, default=0)
    if token_budget > 0:
        command.extend(
            [
                "--token-budget",
                str(token_budget),
                "--per-agent-token-cost",
                str(int(args.per_agent_token_cost)),
            ]
        )
    target_paths = list(args.target_paths or [])
    if target_paths:
        command.extend(["--target-paths", *target_paths])
    command.append("--charts" if bool(args.charts) else "--no-charts")
    command.append("--audit-charts" if bool(args.charts) else "--no-audit-charts")
    if bool(args.dry_run):
        command.append("--dry-run")
    return command


def governance_commands(args, *, run_dir: Path) -> list[tuple[str, list[str]]]:
    return [
        (
            "check_active_plan_sync",
            ["python3", "dev/scripts/checks/check_active_plan_sync.py"],
        ),
        (
            "check_multi_agent_sync",
            ["python3", "dev/scripts/checks/check_multi_agent_sync.py"],
        ),
        (
            "docs_check_strict_tooling",
            ["python3", "dev/scripts/devctl.py", "docs-check", "--strict-tooling"],
        ),
        (
            "orchestrate_status",
            [
                "python3",
                "dev/scripts/devctl.py",
                "orchestrate-status",
                "--format",
                "md",
                "--output",
                str(run_dir / "orchestrate-status.md"),
            ],
        ),
        (
            "orchestrate_watch",
            [
                "python3",
                "dev/scripts/devctl.py",
                "orchestrate-watch",
                "--stale-minutes",
                str(int(args.stale_minutes)),
                "--format",
                "md",
                "--output",
                str(run_dir / "orchestrate-watch.md"),
            ],
        ),
    ]
