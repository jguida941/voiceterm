"""`devctl hygiene` command.

Use this command to catch governance drift in archive/ADR/scripts docs and to
surface leaked VoiceTerm test processes that can impact later runs.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Tuple

from ..common import pipe_output, write_output
from ..config import REPO_ROOT
from ..reports_retention import build_reports_hygiene_guard
from ..process_sweep import (
    DEFAULT_ORPHAN_MIN_AGE_SECONDS,
    DEFAULT_STALE_MIN_AGE_SECONDS,
    format_process_rows,
    scan_voiceterm_test_binaries,
    split_orphaned_processes,
    split_stale_processes,
)
from . import hygiene_audits

ORPHAN_TEST_MIN_AGE_SECONDS = DEFAULT_ORPHAN_MIN_AGE_SECONDS
STALE_ACTIVE_TEST_MIN_AGE_SECONDS = DEFAULT_STALE_MIN_AGE_SECONDS
PROCESS_LINE_MAX_LEN = 180
PROCESS_REPORT_LIMIT = 8


def _audit_archive() -> Dict:
    """Compatibility wrapper used by existing tests."""
    return hygiene_audits.audit_archive(REPO_ROOT)


def _audit_adrs() -> Dict:
    """Compatibility wrapper used by existing tests."""
    return hygiene_audits.audit_adrs(REPO_ROOT)


def _audit_scripts() -> Dict:
    """Compatibility wrapper used by existing tests."""
    return hygiene_audits.audit_scripts(REPO_ROOT)


def _format_process_rows(rows: List[Dict]) -> str:
    return format_process_rows(
        rows,
        line_max_len=PROCESS_LINE_MAX_LEN,
        row_limit=PROCESS_REPORT_LIMIT,
    )


def _scan_voiceterm_test_processes() -> Tuple[List[Dict], List[str]]:
    return scan_voiceterm_test_binaries()


def _audit_runtime_processes() -> Dict:
    """Detect orphaned test runners and report active ones."""
    test_processes, scan_warnings = _scan_voiceterm_test_processes()
    errors: List[str] = []
    warnings: List[str] = []

    ci_env = os.environ.get("CI", "").strip().lower()
    ci_mode = ci_env in {"1", "true", "yes"}
    for warning in scan_warnings:
        if ci_mode:
            errors.append(f"Runtime process sweep unavailable in CI: {warning}")
        else:
            warnings.append(warning)

    orphaned, active = split_orphaned_processes(
        test_processes,
        min_age_seconds=ORPHAN_TEST_MIN_AGE_SECONDS,
    )
    stale_active, fresh_active = split_stale_processes(
        active,
        min_age_seconds=STALE_ACTIVE_TEST_MIN_AGE_SECONDS,
    )

    if orphaned:
        errors.append(
            "Orphaned voiceterm test binaries detected (detached PPID=1). "
            "Stop leaked runners before continuing: "
            f"{_format_process_rows(orphaned)}"
        )
    if stale_active:
        errors.append(
            "Stale active voiceterm test binaries detected. "
            f"Any process running >= {STALE_ACTIVE_TEST_MIN_AGE_SECONDS}s should be stopped: "
            f"{_format_process_rows(stale_active)}"
        )
    if fresh_active:
        warnings.append(
            "Active voiceterm test binaries detected during hygiene run: "
            f"{_format_process_rows(fresh_active)}"
        )

    return {
        "total_detected": len(test_processes),
        "orphaned": orphaned,
        "stale_active": stale_active,
        "active": fresh_active,
        "errors": errors,
        "warnings": warnings,
    }


def _fix_pycache_dirs(pycache_dirs: List[str]) -> Dict:
    """Remove detected `__pycache__` dirs under repo-root-safe paths."""
    removed: List[str] = []
    failed: List[str] = []
    skipped: List[str] = []
    repo_root_resolved = REPO_ROOT.resolve()

    for relative_path in pycache_dirs:
        candidate = REPO_ROOT / relative_path
        if candidate.name != "__pycache__":
            skipped.append(f"{relative_path} (name is not __pycache__)")
            continue
        try:
            resolved = candidate.resolve()
        except OSError as exc:
            failed.append(f"{relative_path} (resolve failed: {exc})")
            continue
        try:
            resolved.relative_to(repo_root_resolved)
        except ValueError:
            failed.append(f"{relative_path} (outside repo root)")
            continue
        if not candidate.exists():
            skipped.append(f"{relative_path} (already absent)")
            continue
        if not candidate.is_dir():
            failed.append(f"{relative_path} (not a directory)")
            continue
        if candidate.is_symlink():
            failed.append(f"{relative_path} (symlink deletion is blocked)")
            continue
        try:
            shutil.rmtree(candidate)
        except OSError as exc:
            failed.append(f"{relative_path} ({exc})")
            continue
        removed.append(relative_path)

    return {
        "requested": True,
        "removed": removed,
        "failed": failed,
        "skipped": skipped,
    }


def run(args) -> int:
    """Audit archive/ADR/scripts hygiene and report drift."""
    archive = _audit_archive()
    adr = _audit_adrs()
    scripts = _audit_scripts()
    fix_report = {"requested": False, "removed": [], "failed": [], "skipped": []}
    if getattr(args, "fix", False):
        fix_report = _fix_pycache_dirs(scripts.get("pycache_dirs", []))
        scripts = _audit_scripts()
        if fix_report["failed"]:
            scripts["errors"] = [
                *scripts.get("errors", []),
                "Unable to remove some Python cache directories: "
                + "; ".join(fix_report["failed"]),
            ]
    runtime_processes = _audit_runtime_processes()
    reports = build_reports_hygiene_guard(REPO_ROOT)
    sections = [archive, adr, scripts, runtime_processes, reports]

    error_count = sum(len(section["errors"]) for section in sections)
    warning_count = sum(len(section["warnings"]) for section in sections)
    ok = error_count == 0

    report = {
        "command": "hygiene",
        "timestamp": datetime.now().isoformat(),
        "ok": ok,
        "error_count": error_count,
        "warning_count": warning_count,
        "archive": archive,
        "adr": adr,
        "scripts": scripts,
        "runtime_processes": runtime_processes,
        "reports": reports,
        "fix": fix_report,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        lines = ["# devctl hygiene", ""]
        lines.append(f"- ok: {ok}")
        lines.append(f"- errors: {error_count}")
        lines.append(f"- warnings: {warning_count}")
        lines.append("")
        lines.append("## Archive")
        lines.append(f"- entries: {archive['total_entries']}")
        lines.extend(f"- error: {message}" for message in archive["errors"])
        lines.extend(f"- warning: {message}" for message in archive["warnings"])
        lines.append("")
        lines.append("## ADRs")
        lines.append(f"- adrs: {adr['total_adrs']}")
        lines.extend(f"- error: {message}" for message in adr["errors"])
        lines.extend(f"- warning: {message}" for message in adr["warnings"])
        lines.append("")
        lines.append("## Scripts")
        lines.append(f"- top-level scripts: {len(scripts['top_level_scripts'])}")
        lines.append(f"- check scripts: {len(scripts['check_scripts'])}")
        lines.extend(f"- error: {message}" for message in scripts["errors"])
        lines.extend(f"- warning: {message}" for message in scripts["warnings"])
        lines.append("")
        lines.append("## Runtime Processes")
        lines.append(
            f"- voiceterm test binaries detected: {runtime_processes['total_detected']}"
        )
        lines.extend(f"- error: {message}" for message in runtime_processes["errors"])
        lines.extend(
            f"- warning: {message}" for message in runtime_processes["warnings"]
        )
        lines.append("")
        lines.append("## Reports")
        lines.append(f"- reports root: {reports['reports_root']}")
        lines.append(f"- reports root exists: {reports['reports_root_exists']}")
        lines.append(f"- managed run dirs: {reports['managed_run_dirs']}")
        lines.append(f"- stale cleanup candidates: {reports['candidate_count']}")
        lines.append(
            f"- reclaim estimate: {reports['candidate_reclaim_human']}"
        )
        lines.extend(f"- error: {message}" for message in reports["errors"])
        lines.extend(f"- warning: {message}" for message in reports["warnings"])
        if fix_report["requested"]:
            lines.append("")
            lines.append("## Fix")
            lines.append(f"- removed_pycache_dirs: {len(fix_report['removed'])}")
            lines.extend(f"- removed: {path}" for path in fix_report["removed"])
            lines.extend(f"- skipped: {path}" for path in fix_report["skipped"])
            lines.extend(f"- error: {path}" for path in fix_report["failed"])
        output = "\n".join(lines)

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    return 0 if ok else 1
