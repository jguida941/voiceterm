"""devctl report command implementation."""

import json
import sys
from pathlib import Path

from ..common import emit_output, pipe_output, run_cmd, write_output
from ..config import REPO_ROOT
from ..metric_writers import append_metric
from ..rust_audit.report import build_rust_audit_charts
from ..status_report import build_project_report, render_project_markdown
from .check_support import build_clippy_pedantic_collect_cmd


def _maybe_refresh_pedantic(args) -> dict | None:
    if not getattr(args, "pedantic", False) or not getattr(args, "pedantic_refresh", False):
        return None
    return run_cmd(
        "pedantic-refresh",
        build_clippy_pedantic_collect_cmd(
            summary_path=getattr(args, "pedantic_summary_json", None),
            lints_path=getattr(args, "pedantic_lints_json", None),
        ),
        cwd=REPO_ROOT,
        dry_run=False,
    )


def _maybe_write_bundle(report: dict, args) -> dict:
    if not getattr(args, "emit_bundle", False):
        return {"written": False}
    bundle_dir = Path(str(args.bundle_dir)).expanduser()
    bundle_dir.mkdir(parents=True, exist_ok=True)
    prefix = str(args.bundle_prefix).strip() or "devctl-report"
    base = bundle_dir / prefix
    md_path = base.with_suffix(".md")
    json_path = base.with_suffix(".json")
    bundle = {
        "written": True,
        "markdown_path": str(md_path),
        "json_path": str(json_path),
    }
    report_with_bundle = dict(report)
    report_with_bundle["bundle"] = bundle
    markdown = render_project_markdown(
        report_with_bundle,
        title="devctl report",
        include_ci_details=False,
        ci_details_limit=0,
    )
    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(report_with_bundle, indent=2), encoding="utf-8")
    return bundle


def run(args) -> int:
    """Generate a JSON or markdown report with optional CI/dev-log data."""
    pedantic_refresh = _maybe_refresh_pedantic(args)
    parallel_enabled = not getattr(args, "no_parallel", False)
    report = build_project_report(
        command="report",
        include_ci=args.ci,
        ci_limit=args.ci_limit,
        include_dev_logs=getattr(args, "dev_logs", False),
        dev_root=getattr(args, "dev_root", None),
        dev_sessions_limit=getattr(args, "dev_sessions_limit", 5),
        include_pedantic=getattr(args, "pedantic", False),
        pedantic_summary_path=getattr(args, "pedantic_summary_json", None),
        pedantic_lints_path=getattr(args, "pedantic_lints_json", None),
        pedantic_policy_path=getattr(args, "pedantic_policy_file", None),
        include_rust_audits=getattr(args, "rust_audits", False),
        rust_audit_mode=getattr(args, "rust_audit_mode", "auto"),
        rust_audit_since_ref=getattr(args, "since_ref", None),
        rust_audit_head_ref=getattr(args, "head_ref", "HEAD"),
        include_quality_backlog=getattr(args, "quality_backlog", False),
        quality_backlog_top_n=getattr(args, "quality_backlog_top_n", 40),
        quality_backlog_include_tests=getattr(args, "quality_backlog_include_tests", False),
        include_python_guard_backlog=getattr(args, "python_guard_backlog", False),
        python_guard_backlog_top_n=getattr(args, "python_guard_backlog_top_n", 20),
        python_guard_since_ref=getattr(args, "since_ref", None),
        python_guard_head_ref=getattr(args, "head_ref", "HEAD"),
        python_guard_policy_path=getattr(args, "quality_policy", None),
        include_probe_report=getattr(args, "probe_report", False),
        probe_since_ref=getattr(args, "since_ref", None),
        probe_head_ref=getattr(args, "head_ref", "HEAD"),
        probe_policy_path=getattr(args, "quality_policy", None),
        parallel=parallel_enabled,
    )
    pedantic_info = report.get("pedantic", {})
    if isinstance(pedantic_info, dict) and pedantic_refresh is not None:
        pedantic_info["refresh"] = pedantic_refresh

    rust_audits = report.get("rust_audits", {})
    if isinstance(rust_audits, dict):
        if getattr(args, "with_charts", False):
            chart_dir: Path | None = None
            if getattr(args, "chart_dir", None):
                chart_dir = Path(str(args.chart_dir)).expanduser()
            elif getattr(args, "emit_bundle", False):
                chart_dir = (
                    Path(str(args.bundle_dir)).expanduser()
                    / f"{str(args.bundle_prefix).strip() or 'devctl-report'}-charts"
                )
            if chart_dir is None:
                report.setdefault("warnings", []).append(
                    "Rust audit charts requested without --chart-dir or --emit-bundle; skipping chart generation."
                )
            else:
                chart_paths, chart_warning = build_rust_audit_charts(
                    rust_audits,
                    chart_dir,
                )
                rust_audits["charts"] = chart_paths
                if chart_warning:
                    rust_audits.setdefault("warnings", []).append(chart_warning)
        report["bundle"] = _maybe_write_bundle(report, args)
    else:
        report["bundle"] = _maybe_write_bundle(report, args)

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = render_project_markdown(
            report,
            title="devctl report",
            include_ci_details=False,
            ci_details_limit=0,
        )

    try:
        append_metric("report", report)
    except Exception as exc:  # pragma: no cover - fail-soft telemetry path
        print(
            f"[devctl report] warning: unable to persist metrics ({exc})",
            file=sys.stderr,
        )
    return emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        writer=write_output,
        piper=pipe_output,
    )
