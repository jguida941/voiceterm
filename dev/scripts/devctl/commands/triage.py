"""devctl triage command implementation."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List

from ..common import pipe_output, run_cmd, write_output
from ..config import REPO_ROOT
from ..status_report import build_project_report
from ..triage_enrich import (
    apply_defaults_to_issues,
    build_issue_rollup,
    extract_cihub_issues,
    load_owner_map,
)
from ..triage_support import (
    build_next_actions,
    classify_issues,
    ingest_cihub_artifacts,
    render_triage_markdown,
    resolve_emit_dir,
    write_bundle,
)


def _build_cihub_command(args) -> List[str]:
    cmd = [args.cihub_bin, "triage"]
    if args.cihub_run:
        cmd.extend(["--run", str(args.cihub_run)])
    else:
        cmd.append("--latest")
    if args.cihub_repo:
        cmd.extend(["--repo", args.cihub_repo])
    return cmd


def _run_cihub_triage(args, emit_dir) -> Dict[str, Any]:
    env = os.environ.copy()
    env["CIHUB_EMIT_TRIAGE"] = "1"
    step = run_cmd(
        "cihub-triage",
        _build_cihub_command(args),
        cwd=REPO_ROOT,
        env=env,
        dry_run=args.dry_run,
    )
    payload: Dict[str, Any] = {"step": step}
    payload.update(ingest_cihub_artifacts(emit_dir))
    return payload


def _resolve_use_cihub(args) -> bool:
    if args.no_cihub:
        return False
    if args.cihub:
        return True
    return shutil.which(args.cihub_bin) is not None


def run(args) -> int:
    """Generate triage report with optional CIHub integration."""
    owner_map, owner_map_warnings = load_owner_map(getattr(args, "owner_map_file", None))
    project_report = build_project_report(
        command="triage",
        include_ci=args.ci,
        ci_limit=args.ci_limit,
        include_dev_logs=getattr(args, "dev_logs", False),
        dev_root=getattr(args, "dev_root", None),
        dev_sessions_limit=getattr(args, "dev_sessions_limit", 5),
    )
    triage_report: Dict[str, Any] = {
        "command": "triage",
        "timestamp": datetime.now().isoformat(),
        "project": project_report,
        "issues": apply_defaults_to_issues(classify_issues(project_report), owner_map),
        "owner_map": owner_map,
        "warnings": owner_map_warnings,
    }
    triage_report["next_actions"] = build_next_actions(triage_report["issues"])

    emit_dir = resolve_emit_dir(args.cihub_emit_dir)
    use_cihub = _resolve_use_cihub(args)
    triage_report["cihub"] = {"enabled": use_cihub, "emit_dir": str(emit_dir)}
    if use_cihub:
        triage_report["cihub"].update(_run_cihub_triage(args, emit_dir))
        step = triage_report["cihub"].get("step", {})
        if isinstance(step, dict) and step.get("returncode") not in (None, 0):
            triage_report["warnings"].append("cihub triage command failed; using local-only signals.")
            triage_report["issues"].append(
                {
                    "category": "infra",
                    "severity": "medium",
                    "owner": owner_map.get("infra", "platform"),
                    "source": "devctl.triage.cihub",
                    "summary": "cihub triage command failed; check cihub version/flags.",
                }
            )
        cihub_issues = extract_cihub_issues(triage_report["cihub"], owner_map)
        triage_report["cihub"]["ingested_issues"] = len(cihub_issues)
        triage_report["issues"].extend(cihub_issues)
    else:
        triage_report["cihub"]["warning"] = "cihub triage skipped."

    if args.require_cihub:
        step = triage_report["cihub"].get("step", {})
        step_failed = isinstance(step, dict) and step.get("returncode") not in (None, 0)
        artifacts = triage_report["cihub"].get("artifacts", {})
        missing_artifacts = not isinstance(artifacts, dict) or not artifacts
        if not use_cihub or step_failed or missing_artifacts:
            triage_report["cihub"]["warning"] = (
                "cihub triage is required but command/artifacts were not successful."
            )
            triage_report["issues"].append(
                {
                    "category": "infra",
                    "severity": "high",
                    "owner": owner_map.get("infra", "platform"),
                    "source": "devctl.triage.cihub",
                    "summary": "Required cihub triage command/artifacts unavailable.",
                }
            )

    triage_report["issues"] = apply_defaults_to_issues(triage_report["issues"], owner_map)
    triage_report["rollup"] = build_issue_rollup(triage_report["issues"])
    triage_report["next_actions"] = build_next_actions(triage_report["issues"])
    if args.emit_bundle:
        triage_report["bundle"] = write_bundle(
            triage_report,
            emit_dir=resolve_emit_dir(args.bundle_dir),
            prefix=args.bundle_prefix,
        )
    else:
        triage_report["bundle"] = {"written": False}

    if args.format == "json":
        output = json.dumps(triage_report, indent=2)
    elif args.format == "md":
        output = render_triage_markdown(triage_report)
    else:
        output = json.dumps(triage_report, indent=2)

    write_output(output, args.output)
    if args.pipe_command:
        pipe_rc = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_rc != 0:
            return pipe_rc

    has_high_issues = any(
        issue.get("severity") == "high" for issue in triage_report.get("issues", [])
    )
    if args.require_cihub and has_high_issues:
        return 1
    return 0
