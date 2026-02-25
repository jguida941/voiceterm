"""Scenario execution helpers for `devctl autonomy-benchmark`."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .autonomy_benchmark_helpers import load_json, slug
from .autonomy_benchmark_matrix import (
    BenchmarkScenario,
    build_swarm_command,
    run_command_timed,
    summarize_rows,
    tactic_prompt,
)
from .autonomy_benchmark_render import render_markdown as _render_markdown
from .numeric import to_float, to_int


def _first_line(text: str) -> str:
    rows = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    return rows[0] if rows else ""


def run_swarm_once(
    *,
    args,
    repo: str,
    benchmark_label: str,
    scenario: BenchmarkScenario,
    swarm_index: int,
    base_prompt: str,
    next_steps: list[str],
    scenario_dir: Path,
) -> dict[str, Any]:
    swarm_name = f"swarm-{swarm_index + 1:03d}"
    run_label = slug(
        f"{benchmark_label}-{scenario.tactic}-n{scenario.swarm_count}-{swarm_name}",
        fallback=f"{scenario.tactic}-{swarm_name}",
    )
    output_md = scenario_dir / f"{swarm_name}.md"
    output_json = scenario_dir / f"{swarm_name}.json"
    stdout_log = scenario_dir / f"{swarm_name}.stdout.log"
    stderr_log = scenario_dir / f"{swarm_name}.stderr.log"

    question = tactic_prompt(
        tactic=scenario.tactic,
        base_prompt=base_prompt,
        next_steps=next_steps,
        swarm_index=swarm_index,
        swarm_count=scenario.swarm_count,
    )
    command = build_swarm_command(
        args=args,
        repo=repo,
        run_label=run_label,
        question=question,
        output_md=output_md,
        output_json=output_json,
    )
    timeout = max(60, int(args.agent_timeout_seconds))
    rc, stdout_text, stderr_text, elapsed_seconds = run_command_timed(
        command, timeout_seconds=timeout
    )
    stdout_log.write_text(stdout_text, encoding="utf-8")
    stderr_log.write_text(stderr_text, encoding="utf-8")

    payload = load_json(output_json) or {}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    agents = payload.get("agents") if isinstance(payload.get("agents"), list) else []
    post_audit = (
        payload.get("post_audit") if isinstance(payload.get("post_audit"), dict) else {}
    )
    tasks_completed_total = sum(
        to_int(item.get("tasks_completed"), default=0)
        for item in agents
        if isinstance(item, dict)
    )
    rounds_completed_total = sum(
        to_int(item.get("rounds_completed"), default=0)
        for item in agents
        if isinstance(item, dict)
    )
    swarm_ok = bool(payload.get("ok")) and rc == 0
    failure_reason = (
        _first_line(stderr_text)
        or _first_line(stdout_text)
        or str(payload.get("reason") or "")
        or f"returncode={rc}"
    )
    return {
        "swarm_index": swarm_index + 1,
        "swarm_name": swarm_name,
        "scenario_label": scenario.label,
        "run_label": run_label,
        "ok": swarm_ok,
        "returncode": rc,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "executed_agents": to_int(summary.get("executed_agents"), default=0),
        "ok_count": to_int(summary.get("ok_count"), default=0),
        "resolved_count": to_int(summary.get("resolved_count"), default=0),
        "selected_agents": to_int(summary.get("selected_agents"), default=0),
        "worker_agents": to_int(summary.get("worker_agents"), default=0),
        "reviewer_lane": bool(summary.get("reviewer_lane")),
        "tasks_completed_total": tasks_completed_total,
        "rounds_completed_total": rounds_completed_total,
        "post_audit_ok": bool(post_audit.get("ok")),
        "reason": "ok" if swarm_ok else failure_reason,
        "command": " ".join(command),
        "summary_md": str(output_md),
        "summary_json": str(output_json),
        "stdout_log": str(stdout_log),
        "stderr_log": str(stderr_log),
    }


def run_scenario_payload(
    *,
    args,
    repo: str,
    benchmark_label: str,
    scenario: BenchmarkScenario,
    base_prompt: str,
    next_steps: list[str],
    benchmark_dir: Path,
) -> dict[str, Any]:
    scenario_dir = benchmark_dir / "scenarios" / scenario.label
    scenario_dir.mkdir(parents=True, exist_ok=True)
    max_workers = max(1, min(scenario.swarm_count, int(args.max_concurrent_swarms)))

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                run_swarm_once,
                args=args,
                repo=repo,
                benchmark_label=benchmark_label,
                scenario=scenario,
                swarm_index=index,
                base_prompt=base_prompt,
                next_steps=next_steps,
                scenario_dir=scenario_dir,
            )
            for index in range(scenario.swarm_count)
        ]
        for future in futures:
            rows.append(future.result())

    rows.sort(key=lambda row: int(row.get("swarm_index") or 0))
    summary = summarize_rows(rows)
    payload = {
        "label": scenario.label,
        "tactic": scenario.tactic,
        "swarm_count": scenario.swarm_count,
        "max_concurrent_swarms": max_workers,
        "summary": summary,
        "swarms": rows,
        "scenario_dir": str(scenario_dir),
    }
    scenario_json = scenario_dir / "summary.json"
    scenario_md = scenario_dir / "summary.md"
    scenario_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    scenario_md.write_text(_render_markdown({"scenarios": [payload]}), encoding="utf-8")
    payload["summary_json"] = str(scenario_json)
    payload["summary_md"] = str(scenario_md)
    return payload


def leaders(scenarios: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not scenarios:
        return {}

    def metric_value(row: dict[str, Any], metric: str) -> float:
        summary = row.get("summary") if isinstance(row.get("summary"), dict) else {}
        return to_float(summary.get(metric), default=0.0)

    by_work = max(scenarios, key=lambda row: metric_value(row, "work_output_score"))
    by_throughput = max(
        scenarios, key=lambda row: metric_value(row, "tasks_per_minute")
    )
    by_success = max(scenarios, key=lambda row: metric_value(row, "swarm_success_pct"))
    return {
        "best_work_output": {
            "label": by_work.get("label"),
            "metric": "work_output_score",
            "value": metric_value(by_work, "work_output_score"),
        },
        "best_tasks_per_minute": {
            "label": by_throughput.get("label"),
            "metric": "tasks_per_minute",
            "value": metric_value(by_throughput, "tasks_per_minute"),
        },
        "best_success_rate": {
            "label": by_success.get("label"),
            "metric": "swarm_success_pct",
            "value": metric_value(by_success, "swarm_success_pct"),
        },
    }
