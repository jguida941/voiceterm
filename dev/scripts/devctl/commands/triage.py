"""devctl triage command implementation."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from typing import Any

from ..common import emit_output, pipe_output, run_cmd, write_output
from ..config import REPO_ROOT
from ..metric_writers import append_failure_kb, append_metric
from ..status_report import build_project_report
from ..triage.enrich import (
    apply_defaults_to_issues,
    build_issue_rollup,
    load_owner_map,
)
from ..triage.input_sources import apply_optional_inputs
from ..triage.support import (
    build_next_actions,
    classify_issues,
    render_triage_markdown,
    resolve_emit_dir,
    write_bundle,
)
from .check_support import build_clippy_pedantic_collect_cmd


def run(args) -> int:
    """Generate triage report with optional CIHub integration."""
    owner_map, owner_map_warnings = load_owner_map(getattr(args, "owner_map_file", None))
    pedantic_refresh = None
    if getattr(args, "pedantic", False) and getattr(args, "pedantic_refresh", False):
        pedantic_refresh = run_cmd(
            "pedantic-refresh",
            build_clippy_pedantic_collect_cmd(
                summary_path=getattr(args, "pedantic_summary_json", None),
                lints_path=getattr(args, "pedantic_lints_json", None),
            ),
            cwd=REPO_ROOT,
            dry_run=getattr(args, "dry_run", False),
        )
    project_report = build_project_report(
        command="triage",
        include_ci=args.ci,
        ci_limit=args.ci_limit,
        include_dev_logs=getattr(args, "dev_logs", False),
        dev_root=getattr(args, "dev_root", None),
        dev_sessions_limit=getattr(args, "dev_sessions_limit", 5),
        include_pedantic=getattr(args, "pedantic", False),
        pedantic_summary_path=getattr(args, "pedantic_summary_json", None),
        pedantic_lints_path=getattr(args, "pedantic_lints_json", None),
        pedantic_policy_path=getattr(args, "pedantic_policy_file", None),
        include_probe_report=getattr(args, "probe_report", False),
        probe_since_ref=getattr(args, "probe_since_ref", None),
        probe_head_ref=getattr(args, "probe_head_ref", "HEAD"),
        probe_policy_path=getattr(args, "quality_policy", None),
    )
    pedantic_info = project_report.get("pedantic", {})
    if isinstance(pedantic_info, dict) and pedantic_refresh is not None:
        pedantic_info["refresh"] = pedantic_refresh
    triage_report: dict[str, Any] = {
        "command": "triage",
        "timestamp": datetime.now(UTC).isoformat(),
        "project": project_report,
        "issues": apply_defaults_to_issues(classify_issues(project_report), owner_map),
        "owner_map": owner_map,
        "warnings": owner_map_warnings,
    }
    pedantic_info = project_report.get("pedantic", {})
    if isinstance(pedantic_info, dict):
        triage_report["issues"].extend(apply_defaults_to_issues(pedantic_info.get("issues", []), owner_map))
    triage_report["next_actions"] = build_next_actions(triage_report["issues"])
    apply_optional_inputs(triage_report, args=args, owner_map=owner_map)

    triage_report["issues"] = apply_defaults_to_issues(triage_report["issues"], owner_map)
    triage_report["rollup"] = build_issue_rollup(triage_report["issues"])
    triage_report["next_actions"] = build_next_actions(triage_report["issues"])
    if args.emit_bundle:
        markdown_output = render_triage_markdown(triage_report)
        triage_report["bundle"] = write_bundle(
            triage_report,
            emit_dir=resolve_emit_dir(args.bundle_dir),
            prefix=args.bundle_prefix,
            markdown=markdown_output,
        )
    else:
        triage_report["bundle"] = {"written": False}

    if args.format == "md":
        output = render_triage_markdown(triage_report)
    else:
        output = json.dumps(triage_report, indent=2)

    try:
        append_metric("triage", triage_report)
        for issue in triage_report.get("issues", []):
            append_failure_kb(issue)
    except Exception as exc:  # pragma: no cover - fail-soft telemetry path
        print(
            f"[devctl triage] warning: unable to persist metrics ({exc})",
            file=sys.stderr,
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

    has_high_issues = any(issue.get("severity") == "high" for issue in triage_report.get("issues", []))
    if args.require_cihub and has_high_issues:
        return 1
    return 0
