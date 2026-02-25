"""Execution-matrix helpers for `devctl autonomy-benchmark`."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import REPO_ROOT
from .numeric import to_float, to_int


@dataclass(frozen=True)
class BenchmarkScenario:
    tactic: str
    swarm_count: int

    @property
    def label(self) -> str:
        return f"{self.tactic}-swarm{self.swarm_count}"


def tactic_prompt(
    *,
    tactic: str,
    base_prompt: str,
    next_steps: list[str],
    swarm_index: int,
    swarm_count: int,
) -> str:
    step_text = (
        "\n".join(f"- {item}" for item in next_steps) if next_steps else "- none"
    )
    prefix = (
        f"{base_prompt}\n\nSwarm slot {swarm_index + 1}/{swarm_count}.\n"
        "Plan checklist context:\n"
        f"{step_text}\n"
    )
    if tactic == "uniform":
        return prefix + "\nTactic: uniform. Execute this task normally."
    if tactic == "specialized":
        roles = (
            "research and analysis",
            "test and guardrail design",
            "implementation and remediation",
            "docs and evidence packaging",
        )
        role = roles[swarm_index % len(roles)]
        return (
            prefix
            + "\nTactic: specialized.\n"
            + f"Focus area: {role}. Keep outputs scoped to that role."
        )
    if tactic == "research-first":
        boundary = max(1, swarm_count // 2)
        stage = "research phase" if swarm_index < boundary else "execution phase"
        stage_instruction = (
            "Prioritize discovery, risks, and concrete implementation plan."
            if swarm_index < boundary
            else "Prioritize implementation/testing based on prior research outputs."
        )
        return (
            prefix
            + "\nTactic: research-first.\n"
            + f"Stage: {stage}. {stage_instruction}"
        )
    if tactic == "test-first":
        return (
            prefix
            + "\nTactic: test-first.\n"
            + "Prioritize tests and guard checks first, then apply minimal fixes."
        )
    return prefix + "\nTactic: fallback uniform."


def build_swarm_command(
    *,
    args,
    repo: str,
    run_label: str,
    question: str,
    output_md: Path,
    output_json: Path,
) -> list[str]:
    command = [
        "python3",
        "dev/scripts/devctl.py",
        "autonomy-swarm",
        "--repo",
        repo,
        "--run-label",
        run_label,
        "--question",
        question,
        "--branch-base",
        str(args.branch_base),
        "--mode",
        str(args.mode),
        "--agents",
        str(int(args.agents)),
        "--parallel-workers",
        str(int(args.parallel_workers)),
        "--max-rounds",
        str(int(args.max_rounds)),
        "--max-hours",
        str(float(args.max_hours)),
        "--max-tasks",
        str(int(args.max_tasks)),
        "--loop-max-attempts",
        str(int(args.loop_max_attempts)),
        "--agent-timeout-seconds",
        str(int(args.agent_timeout_seconds)),
        "--diff-ref",
        str(args.diff_ref),
        "--format",
        "md",
        "--output",
        str(output_md),
        "--json-output",
        str(output_json),
    ]
    fix_command = str(args.fix_command or "").strip()
    if fix_command:
        command.extend(["--fix-command", fix_command])
    command.append("--post-audit" if bool(args.post_audit) else "--no-post-audit")
    command.append(
        "--reviewer-lane" if bool(args.reviewer_lane) else "--no-reviewer-lane"
    )
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
    if bool(args.dry_run):
        command.append("--dry-run")
    return command


def run_command_timed(
    command: list[str], *, timeout_seconds: int
) -> tuple[int, str, str, float]:
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=max(60, timeout_seconds),
            check=False,
        )
        elapsed = max(time.monotonic() - started, 0.0)
        return (
            int(result.returncode),
            str(result.stdout or ""),
            str(result.stderr or ""),
            elapsed,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = max(time.monotonic() - started, 0.0)
        return 124, str(exc.stdout or ""), str(exc.stderr or ""), elapsed


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    ok_count = sum(1 for row in rows if bool(row.get("ok")))
    failed = total - ok_count
    elapsed_total = sum(
        to_float(row.get("elapsed_seconds"), default=0.0) for row in rows
    )
    agent_exec_total = sum(
        to_int(row.get("executed_agents"), default=0) for row in rows
    )
    agent_ok_total = sum(to_int(row.get("ok_count"), default=0) for row in rows)
    resolved_rows_total = sum(
        to_int(row.get("resolved_count"), default=0) for row in rows
    )
    tasks_total = sum(
        to_int(row.get("tasks_completed_total"), default=0) for row in rows
    )
    rounds_total = sum(
        to_int(row.get("rounds_completed_total"), default=0) for row in rows
    )
    post_audit_ok_total = sum(1 for row in rows if bool(row.get("post_audit_ok")))
    tasks_per_minute = 0.0
    if elapsed_total > 0:
        tasks_per_minute = round(tasks_total / (elapsed_total / 60.0), 3)
    return {
        "swarms_total": total,
        "swarms_ok": ok_count,
        "swarms_failed": failed,
        "swarm_success_pct": round((ok_count / total) * 100.0, 2) if total else 0.0,
        "elapsed_seconds_total": round(elapsed_total, 3),
        "elapsed_seconds_avg": round(elapsed_total / total, 3) if total else 0.0,
        "executed_agents_total": agent_exec_total,
        "agent_ok_total": agent_ok_total,
        "agent_ok_rate_pct": (
            round((agent_ok_total / agent_exec_total) * 100.0, 2)
            if agent_exec_total
            else 0.0
        ),
        "resolved_rows_total": resolved_rows_total,
        "tasks_completed_total": tasks_total,
        "rounds_completed_total": rounds_total,
        "tasks_per_minute": tasks_per_minute,
        "post_audit_ok_total": post_audit_ok_total,
        "work_output_score": tasks_total + resolved_rows_total,
    }
