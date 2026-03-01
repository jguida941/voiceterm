"""devctl reports-cleanup command implementation."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from ..common import confirm_or_abort, pipe_output, write_output
from ..config import REPO_ROOT
from ..reports_retention import (
    DEFAULT_RETENTION_KEEP_RECENT,
    DEFAULT_RETENTION_MAX_AGE_DAYS,
    build_reports_cleanup_plan,
)

MD_CANDIDATE_PREVIEW_LIMIT = 20


def _render_md(report: dict) -> str:
    lines = ["# devctl reports-cleanup", ""]
    lines.append(f"- reports_root: {report['reports_root']}")
    lines.append(f"- reports_root_exists: {report['reports_root_exists']}")
    lines.append(f"- max_age_days: {report['max_age_days']}")
    lines.append(f"- keep_recent: {report['keep_recent']}")
    lines.append(f"- managed_run_dirs: {report['managed_run_dirs']}")
    lines.append(f"- candidate_count: {report['candidate_count']}")
    lines.append(f"- candidate_reclaim_estimate: {report['candidate_reclaim_human']}")
    lines.append(f"- dry_run: {report['dry_run']}")
    lines.append(f"- deleted_count: {report['deleted_count']}")
    lines.append(f"- ok: {report['ok']}")

    if report["candidate_count"] > 0:
        lines.append("")
        lines.append("## Candidate Preview")
        for item in report["candidates"][:MD_CANDIDATE_PREVIEW_LIMIT]:
            lines.append(
                f"- {item['relative_path']} (age_days={item['age_days']}, size={item['size_human']})"
            )
        remaining = report["candidate_count"] - MD_CANDIDATE_PREVIEW_LIMIT
        if remaining > 0:
            lines.append(f"- ... {remaining} more candidate directories")

    if report.get("deleted_paths"):
        lines.append("")
        lines.append("## Deleted")
        for path in report["deleted_paths"]:
            lines.append(f"- {path}")

    if report.get("warnings"):
        lines.append("")
        lines.append("## Warnings")
        for warning in report["warnings"]:
            lines.append(f"- {warning}")

    if report.get("errors"):
        lines.append("")
        lines.append("## Errors")
        for error in report["errors"]:
            lines.append(f"- {error}")

    return "\n".join(lines)


def run(args) -> int:
    """Remove stale report run directories with retention safeguards."""
    plan = build_reports_cleanup_plan(
        REPO_ROOT,
        reports_root_arg=args.reports_root,
        max_age_days=int(args.max_age_days),
        keep_recent=int(args.keep_recent),
    )

    errors = list(plan.get("errors", []))
    warnings = list(plan.get("warnings", []))
    deleted_paths: list[str] = []
    deleted_count = 0

    ok = not errors
    if ok and not args.dry_run and plan["candidate_count"] > 0:
        try:
            confirm_or_abort(
                "Delete "
                f"{plan['candidate_count']} stale report directories "
                f"(~{plan['candidate_reclaim_human']})?",
                args.yes,
            )
            for candidate in plan["candidates"]:
                candidate_path = Path(candidate["path"])
                try:
                    shutil.rmtree(candidate_path)
                    deleted_paths.append(candidate["relative_path"])
                    deleted_count += 1
                except OSError as exc:
                    errors.append(f"failed to delete {candidate['relative_path']}: {exc}")
        except SystemExit:
            errors.append("cleanup aborted by user")

    ok = not errors
    report = {
        "command": "reports-cleanup",
        "timestamp": datetime.now().isoformat(),
        "reports_root": plan["reports_root"],
        "reports_root_exists": plan["reports_root_exists"],
        "max_age_days": plan.get("max_age_days", DEFAULT_RETENTION_MAX_AGE_DAYS),
        "keep_recent": plan.get("keep_recent", DEFAULT_RETENTION_KEEP_RECENT),
        "managed_run_dirs": plan.get("managed_run_dirs", 0),
        "candidate_count": plan.get("candidate_count", 0),
        "candidate_reclaim_bytes": plan.get("candidate_reclaim_bytes", 0),
        "candidate_reclaim_human": plan.get("candidate_reclaim_human", "0 B"),
        "candidates": plan.get("candidates", []),
        "subroots": plan.get("subroots", []),
        "dry_run": bool(args.dry_run),
        "deleted_count": deleted_count,
        "deleted_paths": deleted_paths,
        "warnings": warnings,
        "errors": errors,
        "ok": ok,
    }

    output = (
        json.dumps(report, indent=2)
        if args.format == "json"
        else _render_md(report)
    )
    write_output(output, args.output)
    if args.pipe_command:
        pipe_rc = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_rc != 0:
            return pipe_rc
    return 0 if ok else 1
