"""Execution orchestration for check-router command plans."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
import time

from ...common import emit_output, pipe_output, run_cmd, write_output
from ...config import REPO_ROOT
from .progress import emit_progress
from .router_phases import router_batches, router_execution_summary
from .router_plan import build_planned_rows
from .router_steps import dry_run_step_result, execute_router_row
from .steps import run_step_specs

DEFAULT_ROUTER_COMMAND_TIMEOUT_SECONDS = 300
DEFAULT_ROUTER_ROUTE_TIMEOUT_SECONDS = 1800

_EXPLICIT_TIMEOUT_RE = re.compile(r"--timeout-seconds\s+(\d+)")


@dataclass(frozen=True)
class RouterTimeoutStep:
    name: str
    cmd: list[str]
    cwd: str
    returncode: int
    duration_s: float
    skipped: bool
    timed_out: bool
    timeout_seconds: int
    source: str
    router_command: str
    parallel_safety: str
    parallel_reason: str
    failure_output: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def execute_planned_rows(
    *,
    planned_rows: list[dict[str, str]],
    args,
    bundle_error: str | None,
) -> tuple[list[dict], bool]:
    steps: list[dict] = []
    ok = bundle_error is None
    _attach_execution_policy(
        planned_rows,
        command_timeout_seconds=_positive_int_arg(
            getattr(args, "command_timeout_seconds", None),
            DEFAULT_ROUTER_COMMAND_TIMEOUT_SECONDS,
        ),
    )
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
    route_timeout_seconds = _positive_int_arg(
        getattr(args, "route_timeout_seconds", None),
        DEFAULT_ROUTER_ROUTE_TIMEOUT_SECONDS,
    )
    route_deadline = (
        time.monotonic() + route_timeout_seconds
        if route_timeout_seconds > 0
        else None
    )
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
            route_deadline=route_deadline,
        )
    for index, row in enumerate(planned_rows, start=1):
        if _route_budget_exhausted(route_deadline):
            result = _route_timeout_step(
                index=index,
                row=row,
                repo_root=REPO_ROOT,
                route_timeout_seconds=route_timeout_seconds,
            )
        else:
            _cap_row_timeout_to_remaining_route_budget(row, route_deadline)
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
    route_deadline: float | None,
) -> tuple[list[dict], bool]:
    steps: list[dict] = []
    current = 0
    total = len(planned_rows)
    route_timeout_seconds = _positive_int_arg(
        getattr(args, "route_timeout_seconds", None),
        DEFAULT_ROUTER_ROUTE_TIMEOUT_SECONDS,
    )
    for batch in router_batches(planned_rows):
        if _route_budget_exhausted(route_deadline):
            steps.append(
                _route_timeout_step(
                    index=current + 1,
                    row=batch.rows[0],
                    repo_root=REPO_ROOT,
                    route_timeout_seconds=route_timeout_seconds,
                )
            )
            break
        for row in batch.rows:
            _cap_row_timeout_to_remaining_route_budget(row, route_deadline)
        step_specs = [
            {
                "name": f"router-{current + index:02d}",
                "cmd": ["bash", "-lc", row["command"]],
                "cwd": REPO_ROOT,
                "timeout_seconds": row.get("timeout_seconds"),
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


def router_execution_policy(args) -> dict[str, object]:
    return {
        "contract_id": "CheckRouterExecutionPolicy",
        "command_timeout_seconds": _positive_int_arg(
            getattr(args, "command_timeout_seconds", None),
            DEFAULT_ROUTER_COMMAND_TIMEOUT_SECONDS,
        ),
        "route_timeout_seconds": _positive_int_arg(
            getattr(args, "route_timeout_seconds", None),
            DEFAULT_ROUTER_ROUTE_TIMEOUT_SECONDS,
        ),
        "timeout_returncode": 124,
        "timeout_is_failure": True,
    }


def _attach_execution_policy(
    planned_rows: list[dict[str, str]],
    *,
    command_timeout_seconds: int,
) -> None:
    for row in planned_rows:
        row["timeout_seconds"] = _timeout_seconds_for_command(
            str(row.get("command") or ""),
            default_timeout_seconds=command_timeout_seconds,
        )


def _timeout_seconds_for_command(
    command: str,
    *,
    default_timeout_seconds: int,
) -> int:
    explicit_match = _EXPLICIT_TIMEOUT_RE.search(command)
    if explicit_match:
        explicit_timeout = int(explicit_match.group(1))
        return max(default_timeout_seconds, explicit_timeout + 60)
    if "dev/scripts/devctl.py check --profile release" in command:
        return max(default_timeout_seconds, 3600)
    if "dev/scripts/devctl.py check --profile ci" in command:
        return max(default_timeout_seconds, 1800)
    if "dev/scripts/devctl.py check " in command:
        return max(default_timeout_seconds, 900)
    return default_timeout_seconds


def _positive_int_arg(value: object, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else 0


def _route_budget_exhausted(route_deadline: float | None) -> bool:
    return route_deadline is not None and time.monotonic() >= route_deadline


def _cap_row_timeout_to_remaining_route_budget(
    row: dict[str, str],
    route_deadline: float | None,
) -> None:
    if route_deadline is None:
        return
    remaining = max(1, int(route_deadline - time.monotonic()))
    current = _positive_int_arg(row.get("timeout_seconds"), remaining)
    row["timeout_seconds"] = min(current, remaining)


def _route_timeout_step(
    *,
    index: int,
    row: dict[str, str],
    repo_root,
    route_timeout_seconds: int,
) -> dict[str, object]:
    return RouterTimeoutStep(
        name=f"router-{index:02d}",
        cmd=["bash", "-lc", row["command"]],
        cwd=str(repo_root),
        returncode=124,
        duration_s=0.0,
        skipped=False,
        timed_out=True,
        timeout_seconds=route_timeout_seconds,
        source=row["source"],
        router_command=row["command"],
        parallel_safety=row.get("parallel_safety", "parallel_safe"),
        parallel_reason=row.get("parallel_reason", ""),
        failure_output=(
            "check-router route budget exhausted before this guard could run: "
            f"route_timeout_seconds={route_timeout_seconds}"
        ),
    ).to_dict()


__all__ = [
    "build_planned_rows",
    "emit_router_report",
    "execute_planned_rows",
    "router_execution_policy",
    "router_execution_summary",
]
