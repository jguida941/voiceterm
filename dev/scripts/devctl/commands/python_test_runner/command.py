"""Bounded Python test command implementation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
import json
import os
import sys
import time

from ...common import CommandRunPolicy, run_cmd, write_output
from ...config import REPO_ROOT
from ...runtime.python_test_contract import build_python_test_command
from ...time_utils import utc_timestamp

PYTEST_SUCCESS_OUTPUT_PATTERN = "[100%]"
PYTEST_PASS_SUMMARY_PATTERN = " passed"
PYTEST_FORBIDDEN_OUTPUT_PATTERNS = (
    " failed",
    " error",
    " errors",
    "ERROR",
    "Traceback",
)


@dataclass(frozen=True)
class PytestShardAggregate:
    name: str
    cmd: list[str]
    cwd: str
    returncode: int
    duration_s: float
    skipped: bool
    parallelized: bool
    parallel_workers: int
    shards: list[dict[str, object]]
    failure_output: str = ""


def run(args) -> int:
    resolved = build_python_test_command(
        suite_id=args.suite,
        explicit_targets=tuple(args.path or ()),
        timeout_seconds=args.timeout_seconds,
        per_test_timeout_seconds=args.per_test_timeout_seconds,
        fail_fast=not args.no_fail_fast,
    )
    env = dict(os.environ)
    env["VOICETERM_DEVCTL_LIVE_OUTPUT_TIMEOUT_SECONDS"] = str(
        max(1, resolved.timeout_seconds + 30)
    )
    result = _run_python_tests(resolved, args=args, env=env)
    report = _build_report(resolved, result, dry_run=args.dry_run)
    output = json.dumps(report, indent=2) if args.format == "json" else _render_md(report)
    write_output(output, None)
    return 0 if report["ok"] else 1


def _run_python_tests(resolved, *, args, env: dict[str, str]) -> dict[str, object]:
    workers = max(1, int(getattr(args, "parallel_workers", 1) or 1))
    targets = tuple(resolved.targets)
    if (
        bool(getattr(args, "no_parallel", False))
        or workers <= 1
        or len(targets) <= 1
    ):
        return run_cmd(
            "test-python",
            list(resolved.command),
            cwd=REPO_ROOT,
            env=env,
            dry_run=args.dry_run,
            policy=CommandRunPolicy(
                expected_output_patterns=(
                    PYTEST_SUCCESS_OUTPUT_PATTERN,
                    PYTEST_PASS_SUMMARY_PATTERN,
                ),
                forbidden_output_patterns=PYTEST_FORBIDDEN_OUTPUT_PATTERNS,
            ),
        )
    return _run_python_test_shards(
        resolved,
        env=env,
        dry_run=bool(getattr(args, "dry_run", False)),
        max_workers=workers,
    )


def _run_python_test_shards(
    resolved,
    *,
    env: dict[str, str],
    dry_run: bool,
    max_workers: int,
) -> dict[str, object]:
    shard_specs = _build_shard_specs(resolved)
    worker_count = min(max_workers, len(shard_specs))
    started = time.time()
    print(
        "[test-python] running "
        f"{len(shard_specs)} pytest shards in parallel (workers={worker_count})...",
        file=sys.stderr,
        flush=True,
    )
    indexed_results: list[dict[str, object] | None] = [None] * len(shard_specs)
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = {
            pool.submit(
                run_cmd,
                spec["name"],
                spec["cmd"],
                cwd=REPO_ROOT,
                env=env,
                dry_run=dry_run,
                policy=CommandRunPolicy(
                    live_output=False,
                    expected_output_patterns=(
                        PYTEST_SUCCESS_OUTPUT_PATTERN,
                        PYTEST_PASS_SUMMARY_PATTERN,
                    ),
                    forbidden_output_patterns=PYTEST_FORBIDDEN_OUTPUT_PATTERNS,
                ),
            ): index
            for index, spec in enumerate(shard_specs)
        }
        completed = 0
        for future in as_completed(futures):
            index = futures[future]
            result = future.result()
            result["target"] = shard_specs[index]["target"]
            indexed_results[index] = result
            completed += 1
            _emit_shard_progress(completed, len(shard_specs), result)

    shard_results = _ordered_shard_results(indexed_results)
    duration = round(time.time() - started, 2)
    return _aggregate_shard_results(
        resolved,
        shard_results,
        parallel_workers=worker_count,
        duration_s=duration,
    )


def _build_shard_specs(resolved) -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    for index, target in enumerate(resolved.targets, start=1):
        shard = build_python_test_command(
            suite_id=resolved.suite_id,
            explicit_targets=(target,),
            timeout_seconds=resolved.timeout_seconds,
            per_test_timeout_seconds=resolved.per_test_timeout_seconds,
            fail_fast=resolved.fail_fast,
        )
        command = list(shard.command) + ["-p", "no:cacheprovider"]
        specs.append(
            {
                "name": f"test-python-shard-{index:02d}",
                "cmd": command,
                "target": target,
            }
        )
    return specs


def _emit_shard_progress(completed: int, total: int, result: dict[str, object]) -> None:
    target = str(result.get("target") or "")
    status = "ok" if int(result.get("returncode") or 0) == 0 else "failed"
    duration = result.get("duration_s")
    print(
        f"[test-python] shard {completed}/{total} {status} "
        f"duration={duration}s target={target}",
        file=sys.stderr,
        flush=True,
    )


def _ordered_shard_results(
    indexed_results: list[dict[str, object] | None],
) -> list[dict[str, object]]:
    ordered: list[dict[str, object]] = []
    for result in indexed_results:
        if result is None:
            raise RuntimeError("parallel pytest shard execution returned no result")
        ordered.append(result)
    return ordered


def _aggregate_shard_results(
    resolved,
    shard_results: list[dict[str, object]],
    *,
    parallel_workers: int,
    duration_s: float,
) -> dict[str, object]:
    returncode = 0 if all(int(row.get("returncode") or 0) == 0 for row in shard_results) else 1
    failures = [
        row
        for row in shard_results
        if int(row.get("returncode") or 0) != 0
    ]
    failure_output = ""
    if failures:
        failure_output = "\n\n".join(
            _format_shard_failure(row) for row in failures
        )
    return asdict(
        PytestShardAggregate(
            name="test-python",
            cmd=list(resolved.command),
            cwd=str(REPO_ROOT),
            returncode=returncode,
            duration_s=duration_s,
            skipped=False,
            parallelized=True,
            parallel_workers=parallel_workers,
            shards=shard_results,
            failure_output=failure_output,
        )
    )


def _format_shard_failure(row: dict[str, object]) -> str:
    return "\n".join(
        (
            f"### {row.get('name')} ({row.get('target')})",
            f"- returncode: {row.get('returncode')}",
            f"- duration_s: {row.get('duration_s')}",
            str(row.get("failure_output") or ""),
        )
    ).strip()


def _build_report(resolved, result: dict, *, dry_run: bool) -> dict[str, object]:
    report: dict[str, object] = {}
    report["command"] = "test-python"
    report["timestamp"] = utc_timestamp()
    report["ok"] = result["returncode"] == 0
    report["suite"] = resolved.suite_id
    report["targets"] = list(resolved.targets)
    report["fail_fast"] = resolved.fail_fast
    report["timeout_seconds"] = resolved.timeout_seconds
    report["per_test_timeout_seconds"] = resolved.per_test_timeout_seconds
    report["pytest_command"] = list(resolved.command)
    report["dry_run"] = dry_run
    report["step"] = result
    report["command_output_receipt"] = result.get("command_output_receipt")
    report["parallelized"] = bool(result.get("parallelized", False))
    report["parallel_workers"] = int(result.get("parallel_workers") or 1)
    report["shards"] = list(result.get("shards") or [])
    return report


def _render_md(report: dict[str, object]) -> str:
    step = report["step"] if isinstance(report["step"], dict) else {}
    lines = [
        "# devctl test-python",
        "",
        f"- ok: {report['ok']}",
        f"- suite: {report['suite']}",
        f"- targets: {', '.join(report['targets'])}",
        f"- fail_fast: {report['fail_fast']}",
        f"- timeout_seconds: {report['timeout_seconds']}",
        f"- per_test_timeout_seconds: {report['per_test_timeout_seconds']}",
        f"- parallelized: {report['parallelized']}",
        f"- parallel_workers: {report['parallel_workers']}",
        f"- returncode: {step.get('returncode')}",
        f"- duration_s: {step.get('duration_s')}",
        "",
        "## Command",
        f"- `{' '.join(report['pytest_command'])}`",
    ]
    receipt = report.get("command_output_receipt")
    if isinstance(receipt, dict):
        lines.extend(
            [
                "",
                "## Command Output Receipt",
                f"- receipt_id: `{receipt.get('receipt_id')}`",
                f"- stdout_byte_count: {receipt.get('stdout_byte_count')}",
                f"- capture_scope: {receipt.get('capture_scope')}",
                f"- matched_patterns: {', '.join(receipt.get('matched_patterns') or [])}",
                f"- missing_patterns: {', '.join(receipt.get('missing_patterns') or [])}",
                f"- matched_forbidden_patterns: {', '.join(receipt.get('matched_forbidden_patterns') or [])}",
            ]
        )
    shards = report.get("shards")
    if isinstance(shards, list) and shards:
        lines.extend(["", "## Shards", "| Target | Exit | Duration (s) |", "|---|---:|---:|"])
        for shard in shards:
            if not isinstance(shard, dict):
                continue
            lines.append(
                "| "
                f"`{shard.get('target')}` | "
                f"{shard.get('returncode')} | "
                f"{shard.get('duration_s')} |"
            )
    if step.get("failure_output"):
        lines.extend(["", "## Failure Output", str(step["failure_output"])])
    return "\n".join(lines)
