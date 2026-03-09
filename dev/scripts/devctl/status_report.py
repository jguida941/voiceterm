"""Shared data collection + markdown rendering for `status` and `report`.

Why this exists:
- `status` and `report` should show the same fields in the same way
- one renderer prevents accidental output drift over time
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Tuple

from .time_utils import utc_timestamp
from .collect import (
    collect_ci_runs,
    collect_clippy_pedantic_summary,
    collect_dev_log_summary,
    collect_git_status,
    collect_mutation_summary,
)
from .rust_audit_report import collect_rust_audit_report, render_rust_audit_markdown

# Default worker cap for parallel collection probes.
DEFAULT_COLLECT_WORKERS = 4


def _run_probes_serial(probes: List[Tuple[str, Callable[[], Any]]]) -> Dict[str, Any]:
    """Run collection probes sequentially, returning {key: result}."""
    results: Dict[str, Any] = {}
    for key, func in probes:
        try:
            results[key] = func()
        except Exception as exc:
            results[key] = {"error": f"probe '{key}' failed: {exc}"}
    return results


def _run_probes_parallel(
    probes: List[Tuple[str, Callable[[], Any]]],
    max_workers: int,
) -> Dict[str, Any]:
    """Run independent collection probes in parallel while preserving key mapping."""
    if not probes:
        return {}
    if len(probes) <= 1 or max_workers <= 1:
        return _run_probes_serial(probes)

    worker_count = min(max_workers, len(probes))
    results: Dict[str, Any] = {}
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
    parallel: bool = True,
    max_workers: int = DEFAULT_COLLECT_WORKERS,
) -> dict:
    """Collect the standard project snapshot used by both commands."""
    # Build the list of independent collection probes.
    probes: List[Tuple[str, Callable[[], Any]]] = [
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

    # Execute probes (parallel or sequential based on caller preference).
    if parallel:
        collected = _run_probes_parallel(probes, max_workers=max_workers)
    else:
        collected = _run_probes_serial(probes)

    report: dict = {
        "command": command,
        "timestamp": utc_timestamp(),
    }
    # Merge results in deterministic probe-definition order.
    for key, _func in probes:
        report[key] = collected[key]
    return report


def render_project_markdown(
    report: dict,
    *,
    title: str,
    include_ci_details: bool,
    ci_details_limit: int = 5,
) -> str:
    """Render markdown once for both commands so wording stays aligned."""
    lines = [f"# {title}", ""]
    _append_git_lines(lines, report.get("git", {}))
    _append_mutation_lines(lines, report.get("mutants", {}))
    _append_ci_lines(
        lines,
        report.get("ci"),
        include_ci_details=include_ci_details,
        ci_details_limit=ci_details_limit,
    )
    _append_dev_log_lines(lines, report.get("dev_logs"))
    _append_pedantic_lines(lines, report.get("pedantic"))

    if "rust_audits" in report:
        rust_audits = report.get("rust_audits", {})
        if isinstance(rust_audits, dict):
            lines.append("")
            lines.extend(render_rust_audit_markdown(rust_audits))

    report_warnings = report.get("warnings")
    if isinstance(report_warnings, list) and report_warnings:
        lines.append("")
        lines.append("## Report Warnings")
        for warning in report_warnings:
            lines.append(f"- {warning}")

    bundle = report.get("bundle")
    if isinstance(bundle, dict) and bundle.get("written"):
        lines.append("")
        lines.append("## Bundle")
        lines.append(f"- markdown: {bundle.get('markdown_path')}")
        lines.append(f"- json: {bundle.get('json_path')}")

    return "\n".join(lines)


def _append_git_lines(lines: list[str], git_info: Any) -> None:
    if not isinstance(git_info, dict):
        lines.append("- Git: unavailable")
        return
    if "error" in git_info:
        lines.append(f"- Git: {git_info['error']}")
        return
    lines.append(f"- Branch: {git_info.get('branch', 'unknown')}")
    lines.append(f"- Changelog updated: {git_info.get('changelog_updated')}")
    lines.append(f"- Master plan updated: {git_info.get('master_plan_updated')}")
    lines.append(f"- Changed files: {len(git_info.get('changes', []))}")


def _append_mutation_lines(lines: list[str], mutants_info: Any) -> None:
    if not isinstance(mutants_info, dict):
        lines.append("- Mutation score: unavailable")
        return
    if "error" in mutants_info:
        lines.append("- Mutation score: unavailable")
        lines.append(f"- Mutation score note: {mutants_info['error']}")
        return
    results = mutants_info.get("results", {})
    if not isinstance(results, dict):
        results = {}
    score = results.get("score")
    updated_at = results.get("outcomes_updated_at", "unknown")
    age_hours = results.get("outcomes_age_hours")
    score_label = "unknown" if score is None else f"{float(score):.2f}%"
    age_label = "unknown" if age_hours is None else f"{float(age_hours):.2f}h"
    lines.append(f"- Mutation score: {score_label}")
    lines.append(f"- Mutation outcomes: {results.get('outcomes_path', 'unknown')}")
    lines.append(f"- Mutation outcomes updated: {updated_at} ({age_label} old)")
    warning = mutants_info.get("warning")
    if warning:
        lines.append(f"- Mutation score note: {warning}")


def _append_ci_lines(
    lines: list[str],
    ci_info: Any,
    *,
    include_ci_details: bool,
    ci_details_limit: int,
) -> None:
    if ci_info is None:
        return
    if not isinstance(ci_info, dict):
        lines.append("- CI: unavailable")
        return
    if "error" in ci_info:
        lines.append(f"- CI: error ({ci_info['error']})")
        return
    runs = ci_info.get("runs", [])
    lines.append(f"- CI runs: {len(runs)}")
    if not include_ci_details:
        return
    for run in runs[:ci_details_limit]:
        run_title = run.get("displayTitle", "unknown")
        status = run.get("status", "unknown")
        conclusion = run.get("conclusion") or "pending"
        lines.append(f"  - {run_title}: {status}/{conclusion}")


def _append_dev_log_lines(lines: list[str], dev_info: Any) -> None:
    if dev_info is None:
        return
    if not isinstance(dev_info, dict):
        lines.append("- Dev logs: unavailable")
        return
    if "error" in dev_info:
        lines.append(f"- Dev logs: error ({dev_info['error']})")
        return
    lines.append(f"- Dev logs root: {dev_info.get('dev_root')}")
    lines.append(
        "- Dev sessions scanned: "
        f"{dev_info.get('sessions_scanned', 0)}/"
        f"{dev_info.get('session_files_total', 0)}"
    )
    lines.append(
        "- Dev events: "
        f"{dev_info.get('events_scanned', 0)} "
        f"(transcript={dev_info.get('transcript_events', 0)}, "
        f"empty={dev_info.get('empty_events', 0)}, "
        f"error={dev_info.get('error_events', 0)})"
    )
    lines.append(f"- Dev total words: {dev_info.get('total_words', 0)}")
    avg_latency = dev_info.get("avg_latency_ms")
    lines.append(
        "- Dev avg latency: "
        + ("unknown" if avg_latency is None else f"{avg_latency} ms")
    )
    lines.append(f"- Dev parse errors: {dev_info.get('parse_errors', 0)}")
    latest_iso = dev_info.get("latest_event_iso")
    lines.append("- Dev latest event: " + (latest_iso if latest_iso else "none"))


def _append_pedantic_lines(lines: list[str], pedantic_info: Any) -> None:
    if pedantic_info is None:
        return
    if not isinstance(pedantic_info, dict):
        lines.append("- Pedantic advisory: unavailable")
        return
    refresh = pedantic_info.get("refresh")
    if "error" in pedantic_info:
        lines.append(f"- Pedantic advisory: error ({pedantic_info['error']})")
        return
    if not pedantic_info.get("artifact_found", False):
        lines.append("- Pedantic advisory: artifact unavailable")
        warning = pedantic_info.get("warning")
        if warning:
            lines.append(f"- Pedantic advisory note: {warning}")
        _append_pedantic_refresh_line(lines, refresh)
        return
    lines.append(
        "- Pedantic advisory: "
        f"{pedantic_info.get('observed_lints', 0)} lint ids / "
        f"{pedantic_info.get('warnings', 0)} warnings"
    )
    if int(pedantic_info.get("exit_code") or 0) != 0:
        lines.append(
            "- Pedantic advisory note: "
            f"last sweep failed (status={pedantic_info.get('status')}, "
            f"exit={pedantic_info.get('exit_code')})"
        )
    lines.append(
        "- Pedantic policy coverage: "
        f"reviewed={pedantic_info.get('reviewed_lints', 0)}, "
        f"unreviewed={pedantic_info.get('unreviewed_lints', 0)}"
    )
    top_candidates = pedantic_info.get("top_promote_candidates", [])
    if isinstance(top_candidates, list) and top_candidates:
        formatted = ", ".join(
            f"{row.get('lint')}={row.get('count')}"
            for row in top_candidates[:3]
            if isinstance(row, dict)
        )
        if formatted:
            lines.append(f"- Pedantic promote candidates: {formatted}")
    _append_pedantic_refresh_line(lines, refresh)
    policy_warnings = pedantic_info.get("policy_warnings", [])
    if isinstance(policy_warnings, list) and policy_warnings:
        lines.append(f"- Pedantic policy note: {policy_warnings[0]}")


def _append_pedantic_refresh_line(lines: list[str], refresh: Any) -> None:
    if isinstance(refresh, dict):
        lines.append(
            "- Pedantic refresh: "
            f"exit={refresh.get('returncode')} "
            f"skipped={refresh.get('skipped')}"
        )
