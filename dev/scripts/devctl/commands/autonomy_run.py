"""devctl swarm_run command implementation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..autonomy_run_helpers import build_swarm_command as _build_swarm_command
from ..autonomy_run_helpers import collect_next_steps as _collect_next_steps
from ..autonomy_run_helpers import derive_prompt as _derive_prompt
from ..autonomy_run_helpers import (
    fallback_repo_from_origin as _fallback_repo_from_origin,
)
from ..autonomy_run_helpers import governance_commands as _governance_commands
from ..autonomy_run_helpers import run_command as _run_command
from ..autonomy_run_helpers import utc_timestamp as _utc_timestamp
from ..autonomy_run_feedback import (
    build_feedback_state as _build_feedback_state,
)
from ..autonomy_run_feedback import summarize_feedback_state as _summarize_feedback_state
from ..autonomy_run_feedback import update_feedback_state as _update_feedback_state
from ..autonomy_run_plan import update_plan_doc as _update_plan_doc
from ..autonomy_run_plan import validate_plan_scope as _validate_plan_scope
from ..autonomy_run_render import render_markdown as _render_markdown
from ..autonomy_swarm_helpers import resolve_path, slug
from ..common import pipe_output, write_output
from ..numeric import to_int

try:
    from dev.scripts.checks.coderabbit_ralph_loop_core import resolve_repo
except ModuleNotFoundError:
    from checks.coderabbit_ralph_loop_core import resolve_repo


def run(args) -> int:
    """Run one guarded autonomy pipeline and emit md/json summaries."""
    plan_doc = resolve_path(str(args.plan_doc))
    index_doc = resolve_path(str(args.index_doc))
    master_plan_doc = resolve_path(str(args.master_plan_doc))

    for path in (plan_doc, index_doc, master_plan_doc):
        if not path.exists():
            print(f"Error: missing required file: {path}")
            return 2
    if int(args.next_steps_limit) < 1:
        print("Error: --next-steps-limit must be >= 1")
        return 2
    mode = str(args.mode)
    fix_command = str(args.fix_command or "").strip()
    if mode in {"plan-then-fix", "fix-only"} and not fix_command:
        print(
            "Error: --fix-command is required when --mode is plan-then-fix/fix-only "
            "(otherwise no remediation can run)"
        )
        return 2

    repo = resolve_repo(args.repo)
    if not repo:
        repo = _fallback_repo_from_origin()
    if not repo:
        print(
            "Error: unable to resolve repository (pass --repo or set GITHUB_REPOSITORY)."
        )
        return 2
    args.repo = repo

    _plan_text, _index_text, plan_rel, warnings, errors = _validate_plan_scope(
        plan_doc=plan_doc,
        index_doc=index_doc,
        master_plan_doc=master_plan_doc,
        mp_scope=str(args.mp_scope),
    )
    if errors:
        print("\n".join(f"Error: {row}" for row in errors))
        return 2

    run_label_seed = slug(
        str(args.run_label or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")),
        fallback="swarm-run",
    )
    run_root = resolve_path(str(args.run_root))
    continuous_enabled = bool(getattr(args, "continuous", False))
    continuous_max_cycles = int(getattr(args, "continuous_max_cycles", 10))
    if continuous_max_cycles < 1:
        print("Error: --continuous-max-cycles must be >= 1")
        return 2
    cycle_limit = continuous_max_cycles if continuous_enabled else 1
    feedback_state, feedback_warnings, feedback_errors = _build_feedback_state(
        args, continuous_enabled=continuous_enabled
    )
    if feedback_errors:
        print("\n".join(f"Error: {row}" for row in feedback_errors))
        return 2

    cycle_reports: list[dict[str, Any]] = []
    stop_reason = "max_cycles_reached"
    aggregate_warnings = list(warnings) + list(feedback_warnings)
    aggregate_errors = list(errors)

    for cycle_index in range(1, cycle_limit + 1):
        current_plan_text = plan_doc.read_text(encoding="utf-8")
        next_steps = _collect_next_steps(current_plan_text, limit=int(args.next_steps_limit))
        if not next_steps:
            if cycle_index == 1:
                aggregate_warnings.append("no unchecked checklist items found in plan doc")
            stop_reason = "plan_complete"
            break

        cycle_run_label = (
            run_label_seed if not continuous_enabled else f"{run_label_seed}-c{cycle_index:02d}"
        )
        run_dir = run_root / cycle_run_label
        log_dir = run_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        cycle_warnings: list[str] = []
        cycle_errors: list[str] = []
        prompt_text = _derive_prompt(
            plan_doc=plan_rel,
            mp_scope=str(args.mp_scope),
            next_steps=next_steps,
            explicit_question=args.question,
        )
        prompt_path = run_dir / "next_steps_prompt.md"
        prompt_path.write_text(prompt_text, encoding="utf-8")

        swarm_md = run_dir / "autonomy-swarm.md"
        swarm_json = run_dir / "autonomy-swarm.json"
        swarm_command = _build_swarm_command(
            args,
            prompt_path=prompt_path,
            run_label=cycle_run_label,
            output_md=swarm_md,
            output_json=swarm_json,
            agent_override=feedback_state.get("next_agents")
            if bool(feedback_state.get("enabled"))
            else None,
        )
        swarm_result = _run_command(
            swarm_command, timeout_seconds=max(60, int(args.agent_timeout_seconds))
        )
        (log_dir / "autonomy-swarm.stdout.log").write_text(
            str(swarm_result.get("stdout") or ""), encoding="utf-8"
        )
        (log_dir / "autonomy-swarm.stderr.log").write_text(
            str(swarm_result.get("stderr") or ""), encoding="utf-8"
        )

        swarm_payload: dict[str, Any] = {}
        if swarm_json.exists():
            try:
                decoded = json.loads(swarm_json.read_text(encoding="utf-8"))
                if isinstance(decoded, dict):
                    swarm_payload = decoded
            except json.JSONDecodeError as exc:
                cycle_errors.append(f"failed to parse swarm summary json: {exc}")
        else:
            cycle_errors.append(f"missing swarm summary json: {swarm_json}")

        governance_steps: list[dict[str, Any]] = []
        if not bool(args.skip_governance):
            for index, (name, command) in enumerate(
                _governance_commands(args, run_dir=run_dir), start=1
            ):
                result = _run_command(command)
                tag = f"{index:02d}-{slug(name, fallback='step')}"
                stdout_log = log_dir / f"{tag}.stdout.log"
                stderr_log = log_dir / f"{tag}.stderr.log"
                stdout_log.write_text(str(result.get("stdout") or ""), encoding="utf-8")
                stderr_log.write_text(str(result.get("stderr") or ""), encoding="utf-8")
                governance_steps.append(
                    {
                        "name": name,
                        "command": " ".join(command),
                        "returncode": to_int(result.get("returncode"), default=1),
                        "ok": bool(result.get("ok")),
                        "stdout_log": str(stdout_log),
                        "stderr_log": str(stderr_log),
                    }
                )
        governance_ok = (
            all(bool(row.get("ok")) for row in governance_steps)
            if governance_steps
            else bool(args.skip_governance)
        )

        swarm_ok = bool(swarm_result.get("ok")) and bool(swarm_payload.get("ok"))
        plan_update = {"ok": True, "updated": False, "warnings": []}
        if not bool(args.skip_plan_update):
            summary = (
                swarm_payload.get("summary", {})
                if isinstance(swarm_payload.get("summary"), dict)
                else {}
            )
            plan_update, plan_update_warnings = _update_plan_doc(
                plan_doc=plan_doc,
                plan_rel=plan_rel,
                run_label=cycle_run_label,
                mp_scope=str(args.mp_scope),
                swarm_ok=swarm_ok,
                governance_ok=governance_ok,
                run_dir=run_dir,
                swarm_summary=summary,
            )
            if plan_update_warnings:
                cycle_errors.extend(plan_update_warnings)

        feedback_update = _update_feedback_state(feedback_state, swarm_payload)
        for warning in feedback_update.get("warnings", []):
            cycle_warnings.append(str(warning))

        cycle_ok = swarm_ok and governance_ok and plan_update["ok"] and not cycle_errors
        cycle_report = {
            "index": cycle_index,
            "run_label": cycle_run_label,
            "run_dir": str(run_dir),
            "next_steps": next_steps,
            "prompt_file": str(prompt_path),
            "swarm": {
                "ok": swarm_ok,
                "command": " ".join(swarm_command),
                "fix_command_configured": bool(fix_command),
                "returncode": to_int(swarm_result.get("returncode"), default=1),
                "summary_json": str(swarm_json),
                "summary_md": str(swarm_md),
                "summary": swarm_payload.get("summary", {}),
                "post_audit": swarm_payload.get("post_audit", {}),
            },
            "governance": {
                "ok": governance_ok,
                "skipped": bool(args.skip_governance),
                "steps": governance_steps,
            },
            "feedback": feedback_update,
            "plan_update": plan_update,
            "warnings": cycle_warnings,
            "errors": cycle_errors,
            "ok": cycle_ok,
        }
        cycle_reports.append(cycle_report)
        aggregate_warnings.extend(cycle_warnings)
        aggregate_errors.extend(cycle_errors)

        if not cycle_ok:
            stop_reason = "cycle_failed"
            break
        if not continuous_enabled:
            stop_reason = "single_cycle_complete"
            break

    if (
        continuous_enabled
        and stop_reason == "max_cycles_reached"
        and len(cycle_reports) >= cycle_limit
    ):
        stop_reason = "max_cycles_reached"
    elif not cycle_reports and stop_reason == "max_cycles_reached":
        stop_reason = "no_cycles_executed"

    last_cycle = cycle_reports[-1] if cycle_reports else {}
    if cycle_reports:
        all_cycles_ok = all(bool(row.get("ok")) for row in cycle_reports)
        if continuous_enabled:
            overall_ok = all_cycles_ok and stop_reason in {"plan_complete", "max_cycles_reached"}
        else:
            overall_ok = bool(last_cycle.get("ok"))
    else:
        overall_ok = stop_reason == "plan_complete" and not aggregate_errors

    summary_dir = (
        Path(str(last_cycle.get("run_dir")))
        if last_cycle.get("run_dir")
        else run_root / run_label_seed
    )
    summary_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "command": "swarm_run",
        "timestamp": _utc_timestamp(),
        "ok": overall_ok,
        "run_label": run_label_seed,
        "repo": repo,
        "plan_doc": plan_rel,
        "mp_scope": str(args.mp_scope),
        "run_dir": str(last_cycle.get("run_dir") or summary_dir),
        "next_steps": last_cycle.get("next_steps", []),
        "prompt_file": str(last_cycle.get("prompt_file") or ""),
        "swarm": last_cycle.get("swarm", {"ok": False}),
        "governance": last_cycle.get(
            "governance",
            {"ok": bool(args.skip_governance), "skipped": bool(args.skip_governance), "steps": []},
        ),
        "plan_update": last_cycle.get(
            "plan_update",
            {"ok": True, "updated": False, "warnings": []},
        ),
        "continuous": {
            "enabled": continuous_enabled,
            "max_cycles": cycle_limit,
            "cycles_completed": len(cycle_reports),
            "stop_reason": stop_reason,
        },
        "feedback_sizing": _summarize_feedback_state(feedback_state),
        "cycles": [
            {
                "index": row.get("index"),
                "run_label": row.get("run_label"),
                "ok": row.get("ok"),
                "run_dir": row.get("run_dir"),
                "swarm_ok": row.get("swarm", {}).get("ok"),
                "governance_ok": row.get("governance", {}).get("ok"),
                "plan_update_ok": row.get("plan_update", {}).get("ok"),
                "feedback_decision": row.get("feedback", {}).get("decision"),
                "feedback_next_agents": row.get("feedback", {}).get("next_agents"),
                "next_steps": row.get("next_steps", []),
            }
            for row in cycle_reports
        ],
        "warnings": aggregate_warnings,
        "errors": aggregate_errors,
    }

    summary_json = summary_dir / "summary.json"
    summary_md = summary_dir / "summary.md"
    summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary_md.write_text(_render_markdown(report), encoding="utf-8")

    output = (
        json.dumps(report, indent=2)
        if args.format == "json"
        else _render_markdown(report)
    )
    write_output(output, args.output)
    if args.json_output:
        write_output(json.dumps(report, indent=2), args.json_output)
    if args.pipe_command:
        pipe_code = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_code != 0:
            return pipe_code
    return 0 if overall_ok else 1
