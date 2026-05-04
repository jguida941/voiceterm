"""Execution helpers for check-router command plans."""

from __future__ import annotations

import json

from ...common import emit_output, pipe_output, run_cmd, write_output
from ...config import REPO_ROOT
from .router_range import normalize_router_command
from .steps import run_step_specs


def build_planned_rows(
    *,
    bundle_name: str,
    bundle_commands: list[str],
    risk_addons: list[dict],
    policy_path: str | None,
    since_ref: str | None,
    head_ref: str,
) -> list[dict[str, str]]:
    planned_rows = [
        {
            "source": bundle_name,
            "command": normalize_router_command(
                command,
                policy_path,
                since_ref=since_ref,
                head_ref=head_ref,
            ),
        }
        for command in bundle_commands
    ]
    for addon in risk_addons:
        planned_rows.extend(
            {
                "source": addon["id"],
                "command": normalize_router_command(
                    command,
                    policy_path,
                    since_ref=since_ref,
                    head_ref=head_ref,
                ),
            }
            for command in addon["commands"]
        )
    return planned_rows


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
                _dry_run_step_result(f"router-{index:02d}", row)
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
    step_specs = [
        {
            "name": f"router-{index:02d}",
            "cmd": ["bash", "-lc", row["command"]],
            "cwd": REPO_ROOT,
        }
        for index, row in enumerate(planned_rows, start=1)
    ]
    steps = run_step_specs(
        step_specs,
        dry_run=dry_run,
        parallel_enabled=True,
        max_workers=max_workers,
    )
    for step, row in zip(steps, planned_rows, strict=False):
        step["source"] = row["source"]
        step["router_command"] = row["command"]
    ok = all(int(step.get("returncode") or 0) == 0 for step in steps)
    return steps, ok


def _execute_row(
    *,
    index: int,
    row: dict[str, str],
    args,
    dry_run: bool,
) -> dict:
    step_name = f"router-{index:02d}"
    if dry_run and args.format == "json":
        return _dry_run_step_result(step_name, row)
    result = run_cmd(
        step_name,
        ["bash", "-lc", row["command"]],
        cwd=REPO_ROOT,
        dry_run=dry_run,
    )
    result["source"] = row["source"]
    result["router_command"] = row["command"]
    return result


def _dry_run_step_result(name: str, row: dict[str, str]) -> dict[str, object]:
    return dict(
        name=name,
        cmd=["bash", "-lc", row["command"]],
        cwd=str(REPO_ROOT),
        returncode=0,
        duration_s=0.0,
        skipped=True,
        source=row["source"],
        router_command=row["command"],
    )
