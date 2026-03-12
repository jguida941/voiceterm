"""Shared data collection for `status` and `report`.

Markdown rendering lives in `status_report_render.py` so this module stays
focused on probe orchestration.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from .collect import (
    collect_ci_runs,
    collect_clippy_pedantic_summary,
    collect_git_status,
    collect_mutation_summary,
)
from .collect_dev_logs import collect_dev_log_summary
from .python_guard_report import collect_python_guard_report
from .quality_backlog_report import collect_quality_backlog
from .review_probe_report import build_probe_report
from .rust_audit_report import collect_rust_audit_report
from .status_report_render import render_project_markdown as _render_project_markdown
from .time_utils import utc_timestamp

DEFAULT_COLLECT_WORKERS = 4
Probe = tuple[str, Callable[[], Any]]
render_project_markdown = _render_project_markdown


def _run_probes_serial(probes: list[Probe]) -> dict[str, Any]:
    """Run collection probes sequentially, returning {key: result}."""
    results: dict[str, Any] = {}
    for key, func in probes:
        try:
            results[key] = func()
        except Exception as exc:
            results[key] = {"error": f"probe '{key}' failed: {exc}"}
    return results


def _run_probes_parallel(probes: list[Probe], max_workers: int) -> dict[str, Any]:
    """Run independent collection probes in parallel while preserving key mapping."""
    if not probes:
        return {}
    if len(probes) <= 1 or max_workers <= 1:
        return _run_probes_serial(probes)
    worker_count = min(max_workers, len(probes))
    results: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = {pool.submit(func): key for key, func in probes}
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as exc:
                results[key] = {"error": f"probe '{key}' failed: {exc}"}
    return results


def build_project_report(
    *,
    command: str,
    include_ci: bool,
    ci_limit: int,
    include_dev_logs: bool,
    dev_root: str | None,
    dev_sessions_limit: int,
    include_pedantic: bool = False,
    pedantic_summary_path: str | None = None,
    pedantic_lints_path: str | None = None,
    pedantic_policy_path: str | None = None,
    include_rust_audits: bool = False,
    rust_audit_mode: str = "auto",
    rust_audit_since_ref: str | None = None,
    rust_audit_head_ref: str = "HEAD",
    rust_audit_dead_code_limit: int = 25,
    include_quality_backlog: bool = False,
    quality_backlog_top_n: int = 40,
    quality_backlog_include_tests: bool = False,
    include_python_guard_backlog: bool = False,
    python_guard_backlog_top_n: int = 20,
    python_guard_since_ref: str | None = None,
    python_guard_head_ref: str = "HEAD",
    python_guard_policy_path: str | None = None,
    include_probe_report: bool = False,
    probe_since_ref: str | None = None,
    probe_head_ref: str = "HEAD",
    probe_policy_path: str | None = None,
    probe_emit_artifacts: bool = False,
    parallel: bool = True,
    max_workers: int = DEFAULT_COLLECT_WORKERS,
) -> dict:
    """Collect the standard project snapshot used by both commands."""
    probes: list[Probe] = [
        ("git", collect_git_status),
        ("mutants", collect_mutation_summary),
    ]
    if include_ci:
        probes.append(("ci", lambda: collect_ci_runs(ci_limit)))
    if include_dev_logs:
        probes.append(
            (
                "dev_logs",
                lambda: collect_dev_log_summary(
                    dev_root=dev_root,
                    session_limit=dev_sessions_limit,
                ),
            )
        )
    if include_pedantic:
        probes.append(
            (
                "pedantic",
                lambda: collect_clippy_pedantic_summary(
                    summary_path=pedantic_summary_path,
                    lints_path=pedantic_lints_path,
                    policy_path=pedantic_policy_path,
                ),
            )
        )
    if include_rust_audits:
        probes.append(
            (
                "rust_audits",
                lambda: collect_rust_audit_report(
                    mode=rust_audit_mode,
                    since_ref=rust_audit_since_ref,
                    head_ref=rust_audit_head_ref,
                    dead_code_report_limit=rust_audit_dead_code_limit,
                ),
            )
        )
    if include_quality_backlog:
        probes.append(
            (
                "quality_backlog",
                lambda: collect_quality_backlog(
                    top_n=quality_backlog_top_n,
                    include_tests=quality_backlog_include_tests,
                ),
            )
        )
    if include_python_guard_backlog:
        probes.append(
            (
                "python_guard_backlog",
                lambda: collect_python_guard_report(
                    since_ref=python_guard_since_ref,
                    head_ref=python_guard_head_ref,
                    top_n=python_guard_backlog_top_n,
                    policy_path=python_guard_policy_path,
                ),
            )
        )
    if include_probe_report:
        probes.append(
            (
                "probe_report",
                lambda: build_probe_report(
                    since_ref=probe_since_ref,
                    head_ref=probe_head_ref,
                    policy_path=probe_policy_path,
                    emit_artifacts=probe_emit_artifacts,
                ),
            )
        )

    collected = _run_probes_parallel(probes, max_workers=max_workers) if parallel else _run_probes_serial(probes)
    report: dict = {
        "command": command,
        "timestamp": utc_timestamp(),
    }
    for key, _func in probes:
        report[key] = collected[key]
    return report
