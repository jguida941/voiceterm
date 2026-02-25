"""devctl autonomy-swarm command implementation."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..autonomy_swarm_helpers import (
    build_swarm_charts,
    collect_refactor_metadata,
    recommend_agent_count,
    render_swarm_markdown,
    resolve_path,
    slug,
)
from ..autonomy_swarm_post_audit import build_post_audit_payload as _post_audit_payload
from ..autonomy_swarm_post_audit import run_post_audit_digest as _run_post_audit_digest
from ..common import pipe_output, write_output
from ..numeric import to_int
from .autonomy_swarm_core import AgentTask as _AgentTask
from .autonomy_swarm_core import fallback_repo_from_origin as _fallback_repo_from_origin
from .autonomy_swarm_core import run_one_agent as _run_one_agent
from .autonomy_swarm_core import validate_args as _validate_args

try:
    from dev.scripts.checks.coderabbit_ralph_loop_core import resolve_repo
except ModuleNotFoundError:
    from checks.coderabbit_ralph_loop_core import resolve_repo


def run(args) -> int:
    """Run an adaptive autonomy swarm and emit a human-readable report bundle."""
    arg_error = _validate_args(args)
    if arg_error:
        print(arg_error)
        return 2

    repo = resolve_repo(args.repo)
    if not repo:
        repo = _fallback_repo_from_origin()
    if not repo:
        print(
            "Error: unable to resolve repository (pass --repo or set GITHUB_REPOSITORY)."
        )
        return 2

    now = datetime.now(timezone.utc)
    run_label = slug(
        str(args.run_label or now.strftime("%Y%m%d-%H%M%SZ")), fallback="swarm"
    )
    output_root = resolve_path(str(args.output_root))
    swarm_dir = output_root / run_label
    chart_dir = swarm_dir / "charts"
    swarm_dir.mkdir(parents=True, exist_ok=True)

    args.repo = repo
    metadata, warnings = collect_refactor_metadata(args)
    selected_agents, rationale, score_components = recommend_agent_count(metadata, args)

    requested_agents = to_int(args.agents, default=selected_agents)
    if requested_agents <= 0:
        requested_agents = selected_agents

    post_audit_payload = _post_audit_payload(enabled=bool(args.post_audit))

    reviewer_enabled = (
        bool(args.reviewer_lane) and bool(args.post_audit) and not bool(args.plan_only)
    )
    if bool(args.reviewer_lane) and not bool(args.post_audit):
        warnings.append("reviewer lane disabled because --post-audit is disabled")

    worker_agent_count = selected_agents
    if reviewer_enabled:
        if selected_agents > 1:
            worker_agent_count = selected_agents - 1
        else:
            reviewer_enabled = False
            warnings.append("reviewer lane skipped because selected agent count is 1")

    rows: list[dict[str, Any]] = []
    if not bool(args.plan_only):
        tasks = [
            _AgentTask(
                index=index,
                name=f"AGENT-{index}",
                output_dir=swarm_dir / f"AGENT-{index}",
            )
            for index in range(1, worker_agent_count + 1)
        ]
        worker_count = min(worker_agent_count, max(1, int(args.parallel_workers)))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(_run_one_agent, task, args, run_label) for task in tasks
            ]
            for future in futures:
                rows.append(future.result())
        rows.sort(key=lambda item: int(item.get("index") or 0))

        if bool(args.post_audit):
            try:
                post_audit_payload = _run_post_audit_digest(args, run_label)
            except Exception as exc:  # pragma: no cover - defensive fail-open guard
                post_audit_payload = _post_audit_payload(
                    enabled=True,
                    ok=False,
                    errors=[f"post-audit failed: {exc}"],
                )
                warnings.append(f"post-audit failed: {exc}")

        if reviewer_enabled:
            reviewer_ok = bool(post_audit_payload.get("ok"))
            reviewer_reason = (
                "post_audit_ok"
                if reviewer_ok
                else str((post_audit_payload.get("errors") or ["post_audit_failed"])[0])
            )
            rows.append(
                {
                    "agent": "AGENT-REVIEW",
                    "index": worker_agent_count + 1,
                    "returncode": 0 if reviewer_ok else 1,
                    "ok": reviewer_ok,
                    "resolved": reviewer_ok,
                    "reason": reviewer_reason,
                    "rounds_completed": 0,
                    "tasks_completed": 0,
                    "report_json": str(post_audit_payload.get("summary_json") or ""),
                    "report_md": str(post_audit_payload.get("summary_md") or ""),
                    "stdout_log": "",
                    "stderr_log": "",
                }
            )
            rows.sort(key=lambda item: int(item.get("index") or 0))
    elif bool(args.post_audit):
        post_audit_payload = _post_audit_payload(
            enabled=True,
            warnings=["post-audit skipped for --plan-only"],
        )

    ok_count = sum(1 for row in rows if bool(row.get("ok")))
    resolved_count = sum(1 for row in rows if bool(row.get("resolved")))
    overall_ok = all(bool(row.get("ok")) for row in rows) if rows else True

    report: dict[str, Any] = {
        "command": "autonomy-swarm",
        "timestamp": now.isoformat().replace("+00:00", "Z"),
        "ok": overall_ok,
        "run_label": run_label,
        "output_root": str(output_root),
        "swarm_dir": str(swarm_dir),
        "summary": {
            "requested_agents": requested_agents,
            "selected_agents": selected_agents,
            "worker_agents": worker_agent_count,
            "reviewer_lane": reviewer_enabled,
            "executed_agents": len(rows),
            "ok_count": ok_count,
            "resolved_count": resolved_count,
            "plan_only": bool(args.plan_only),
        },
        "metadata": metadata,
        "score_components": score_components,
        "allocation_rationale": rationale,
        "execution": {
            "mode": str(args.mode),
            "fix_command_configured": bool(str(args.fix_command or "").strip()),
            "branch_base": str(args.branch_base),
            "parallel_workers": int(args.parallel_workers),
            "max_rounds": int(args.max_rounds),
            "max_hours": float(args.max_hours),
            "max_tasks": int(args.max_tasks),
            "loop_max_attempts": int(args.loop_max_attempts),
            "dry_run": bool(args.dry_run),
        },
        "warnings": warnings,
        "agents": rows,
        "charts": [],
        "post_audit": post_audit_payload,
    }

    if bool(args.charts):
        chart_paths, chart_warning = build_swarm_charts(report, chart_dir)
        report["charts"] = chart_paths
        if chart_warning:
            report["warnings"].append(chart_warning)

    summary_json = swarm_dir / "summary.json"
    summary_md = swarm_dir / "summary.md"
    summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary_md.write_text(render_swarm_markdown(report), encoding="utf-8")

    output = (
        json.dumps(report, indent=2)
        if args.format == "json"
        else render_swarm_markdown(report)
    )
    write_output(output, args.output)
    if args.json_output:
        write_output(json.dumps(report, indent=2), args.json_output)
    if args.pipe_command:
        pipe_code = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_code != 0:
            return pipe_code
    return 0 if report["ok"] else 1
