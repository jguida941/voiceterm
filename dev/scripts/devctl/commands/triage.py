"""devctl triage command implementation."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ..common import pipe_output, run_cmd, write_output
from ..config import REPO_ROOT
from ..metric_writers import append_failure_kb, append_metric
from ..status_report import build_project_report
from ..triage_enrich import (
    apply_defaults_to_issues,
    build_issue_rollup,
    extract_cihub_issues,
    extract_issues_from_file,
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


def _cihub_supports_triage(cihub_bin: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [cihub_bin, "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return False, str(exc)

    combined = "\n".join([result.stdout or "", result.stderr or ""])
    match = re.search(r"\{([^}]+)\}", combined)
    if match:
        commands = {part.strip() for part in match.group(1).split(",")}
        return ("triage" in commands), "parsed-help"

    return ("triage" in combined), "fallback-text-search"


def _resolve_use_cihub(args) -> tuple[bool, str | None]:
    if args.no_cihub:
        return False, None
    cihub_available = shutil.which(args.cihub_bin) is not None
    if not cihub_available:
        return False, "cihub binary not found; skipping CIHub triage."

    supports_triage, source = _cihub_supports_triage(args.cihub_bin)
    if supports_triage:
        return True, None
    return (
        False,
        "cihub binary does not support `triage`; skipping CIHub triage "
        f"(probe={source}).",
    )


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
    use_cihub, cihub_warning = _resolve_use_cihub(args)
    triage_report["cihub"] = {"enabled": use_cihub, "emit_dir": str(emit_dir)}
    if cihub_warning:
        triage_report["cihub"]["warning"] = cihub_warning
        triage_report["warnings"].append(cihub_warning)
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
        if not triage_report["cihub"].get("warning"):
            triage_report["cihub"]["warning"] = "cihub triage skipped."

    external_rows: list[dict[str, Any]] = []
    for raw_path in list(getattr(args, "external_issues_file", []) or []):
        source = f"external.{Path(raw_path).name}"
        row: dict[str, Any] = {"path": raw_path, "source": source}
        external_issues, external_error = extract_issues_from_file(
            raw_path,
            source=source,
            owner_map=owner_map,
        )
        if external_error:
            row["error"] = external_error
            triage_report["warnings"].append(
                f"external issues ingest failed ({raw_path}): {external_error}"
            )
            triage_report["issues"].append(
                {
                    "category": "infra",
                    "severity": "medium",
                    "owner": owner_map.get("infra", "platform"),
                    "source": source,
                    "summary": f"external issues ingest failed for {raw_path}",
                }
            )
        else:
            row["issues"] = len(external_issues)
            triage_report["issues"].extend(external_issues)
        external_rows.append(row)
    triage_report["external_inputs"] = external_rows

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

    try:
        append_metric("triage", triage_report)
        for issue in triage_report.get("issues", []):
            append_failure_kb(issue)
    except Exception as exc:  # pragma: no cover - fail-soft telemetry path
        print(
            f"[devctl triage] warning: unable to persist metrics ({exc})",
            file=sys.stderr,
        )
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
