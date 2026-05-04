"""Execution orchestration for check-router command plans."""

from __future__ import annotations

import json

from ...common import emit_output, pipe_output, run_cmd, write_output
from ...config import REPO_ROOT
from .progress import emit_progress
from .router_phases import router_batches, router_execution_summary
from .router_plan import build_planned_rows
from .router_steps import dry_run_step_result, execute_router_row
from .steps import run_step_specs


def execute_planned_rows(
    *,
    planned_rows: list[dict[str, str]],
    args,
    bundle_error: str | None,
) -> tuple[list[dict], bool]:
    steps: list[dict] = []
    ok = bundle_error is None
    execute = bool(getattr(args, "execute", False))
    if execute and bundle_error is None:
        return _execute_rows(planned_rows, args)
    if execute and bundle_error is not None:
        ok = False
    return steps, ok


def emit_router_report(args, report: dict, *, render_md) -> int:
    output = (
        json.dumps(report, indent=2)
        if args.format == "json"
        else render_md(report)
    )
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_rc != 0:
        return pipe_rc
    return 0 if bool(report.get("ok")) else 1


def _execute_rows(planned_rows: list[dict[str, str]], args) -> tuple[list[dict], bool]:
    steps: list[dict] = []
    ok = True
    keep_going = bool(getattr(args, "keep_going", False))
    dry_run = bool(getattr(args, "dry_run", False))
    if dry_run and args.format == "json":
        return (
            [
                dry_run_step_result(
                    f"router-{index:02d}",
                    row,
                    repo_root=REPO_ROOT,
                )
                for index, row in enumerate(planned_rows, start=1)
            ],
            True,
        )
    if _parallel_enabled(args, keep_going=keep_going):
        return _execute_rows_parallel(
            planned_rows,
            args,
            dry_run=dry_run,
            max_workers=max(1, int(getattr(args, "parallel_workers", 4))),
        )
    for index, row in enumerate(planned_rows, start=1):
        result = _execute_row(index=index, row=row, args=args, dry_run=dry_run)
        steps.append(result)
        if result["returncode"] != 0:
            ok = False
            if not keep_going:
                break
    return steps, ok


def _parallel_enabled(args, *, keep_going: bool) -> bool:
    if not keep_going:
        return False
    if bool(getattr(args, "no_parallel", False)):
        return False
    return max(1, int(getattr(args, "parallel_workers", 4))) > 1


def _execute_rows_parallel(
    planned_rows: list[dict[str, str]],
    args,
    *,
    dry_run: bool,
    max_workers: int,
) -> tuple[list[dict], bool]:
    steps: list[dict] = []
    current = 0
    total = len(planned_rows)
    for batch in router_batches(planned_rows):
        step_specs = [
            {
                "name": f"router-{current + index:02d}",
                "cmd": ["bash", "-lc", row["command"]],
                "cwd": REPO_ROOT,
            }
            for index, row in enumerate(batch.rows, start=1)
        ]
        emit_progress(
            step_specs,
            current=current,
            total=total,
            is_parallel=batch.parallel_enabled,
        )
        batch_steps = run_step_specs(
            step_specs,
            dry_run=dry_run,
            parallel_enabled=batch.parallel_enabled,
            max_workers=max_workers,
        )
        for step, row in zip(batch_steps, batch.rows, strict=False):
            step["source"] = row["source"]
            step["router_command"] = row["command"]
            step["parallel_safety"] = row.get("parallel_safety", "parallel_safe")
            step["parallel_reason"] = row.get("parallel_reason", "")
        steps.extend(batch_steps)
        current += len(batch.rows)
    ok = all(int(step.get("returncode") or 0) == 0 for step in steps)
    return steps, ok


def _execute_row(
    *,
    index: int,
    row: dict[str, str],
    args,
    dry_run: bool,
) -> dict:
    return execute_router_row(
        index=index,
        row=row,
        dry_run=dry_run,
        json_format=args.format == "json",
        repo_root=REPO_ROOT,
        runner=run_cmd,
    )


__all__ = [
    "build_planned_rows",
    "emit_router_report",
    "execute_planned_rows",
    "router_execution_summary",
]
