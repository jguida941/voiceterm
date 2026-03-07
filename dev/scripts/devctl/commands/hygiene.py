"""`devctl hygiene` command.

Use this command to catch governance drift in archive/ADR/scripts docs and to
surface leaked VoiceTerm test processes that can impact later runs.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Tuple

from ..common import pipe_output, write_output
from ..time_utils import utc_timestamp
from ..config import REPO_ROOT
from ..process_sweep import (
    DEFAULT_ORPHAN_MIN_AGE_SECONDS,
    DEFAULT_STALE_MIN_AGE_SECONDS,
    SECONDS_PER_DAY,
    format_process_rows,
    scan_voiceterm_test_binaries,
    split_orphaned_processes,
    split_stale_processes,
)
from ..reports_retention import build_reports_hygiene_guard
from . import hygiene_audits

ORPHAN_TEST_MIN_AGE_SECONDS = DEFAULT_ORPHAN_MIN_AGE_SECONDS
STALE_ACTIVE_TEST_MIN_AGE_SECONDS = DEFAULT_STALE_MIN_AGE_SECONDS
PROCESS_LINE_MAX_LEN = 180
PROCESS_REPORT_LIMIT = 8


def _is_sandbox_ps_warning(message: str) -> bool:
    lowered = message.lower()
    return "unable to execute ps" in lowered and "operation not permitted" in lowered


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
    """Detect orphaned VoiceTerm test processes and report active ones."""
    test_processes, scan_warnings = _scan_voiceterm_test_processes()
    errors: List[str] = []
    warnings: List[str] = []

    ci_env = os.environ.get("CI", "").strip().lower()
    ci_mode = ci_env in {"1", "true", "yes"}
    for warning in scan_warnings:
        if _is_sandbox_ps_warning(warning):
            # Sandbox sessions may block `ps` entirely; this is non-actionable
            # noise for strict local hygiene runs.
            continue
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
            "Orphaned voiceterm test processes detected (detached PPID=1). "
            "Stop leaked runners before continuing: "
            f"{_format_process_rows(orphaned)}"
        )
    if stale_active:
        errors.append(
            "Stale active voiceterm test processes detected. "
            f"Any process running >= {STALE_ACTIVE_TEST_MIN_AGE_SECONDS}s should be stopped: "
            f"{_format_process_rows(stale_active)}"
        )
    if fresh_active:
        warnings.append(
            "Active voiceterm test processes detected during hygiene run: "
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


MUTATION_BADGE_PATH = ".github/badges/mutation-score.json"
MUTATION_BADGE_MAX_AGE_DAYS = 14
README_REQUIRED_DIRS = ("dev/history", "dev/deferred", "dev/active", "dev/adr")


def _audit_mutation_badge() -> Dict:
    """Warn if the mutation badge JSON is stale or missing."""
    errors: List[str] = []
    warnings: List[str] = []
    badge_path = REPO_ROOT / MUTATION_BADGE_PATH
    if not badge_path.exists():
        return {"errors": errors, "warnings": warnings}
    try:
        mtime = badge_path.stat().st_mtime
        age_days = (time.time() - mtime) / SECONDS_PER_DAY
        if age_days > MUTATION_BADGE_MAX_AGE_DAYS:
            warnings.append(
                f"Mutation badge is {age_days:.0f} days old "
                f"(threshold: {MUTATION_BADGE_MAX_AGE_DAYS} days). "
                "Re-run mutation testing to refresh."
            )
        data = json.loads(badge_path.read_text(encoding="utf-8"))
        if data.get("message", "").lower() == "stale":
            warnings.append("Mutation badge status is marked 'stale'.")
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"Unable to read mutation badge: {exc}")
    return {"errors": errors, "warnings": warnings}


def _audit_readme_presence() -> Dict:
    """Warn if required dev directories are missing README files."""
    errors: List[str] = []
    warnings: List[str] = []
    for dir_path in README_REQUIRED_DIRS:
        full = REPO_ROOT / dir_path
        if not full.is_dir():
            continue
        readme = full / "README.md"
        if not readme.exists():
            warnings.append(f"{dir_path}/README.md is missing.")
    return {"errors": errors, "warnings": warnings}


def run(args) -> int:
    """Audit archive/ADR/scripts hygiene and report drift."""
    strict_warnings = bool(getattr(args, "strict_warnings", False))
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
    mutation_badge = _audit_mutation_badge()
    readme_presence = _audit_readme_presence()
    sections = [
        archive,
        adr,
        scripts,
        runtime_processes,
        reports,
        mutation_badge,
        readme_presence,
    ]

    error_count = sum(len(section["errors"]) for section in sections)
    warning_count = sum(len(section["warnings"]) for section in sections)
    warning_fail_count = warning_count if strict_warnings else 0
    ok = error_count == 0 and warning_fail_count == 0

    report = {
        "command": "hygiene",
        "timestamp": utc_timestamp(),
        "ok": ok,
        "strict_warnings": strict_warnings,
        "error_count": error_count,
        "warning_count": warning_count,
        "warning_fail_count": warning_fail_count,
        "archive": archive,
        "adr": adr,
        "scripts": scripts,
        "runtime_processes": runtime_processes,
        "reports": reports,
        "mutation_badge": mutation_badge,
        "readme_presence": readme_presence,
        "fix": fix_report,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        lines = ["# devctl hygiene", ""]
        lines.append(f"- ok: {ok}")
        lines.append(f"- strict_warnings: {strict_warnings}")
        lines.append(f"- errors: {error_count}")
        lines.append(f"- warnings: {warning_count}")
        if strict_warnings:
            lines.append(f"- warning_fail_count: {warning_fail_count}")
        lines.append("")
        lines.append("## Archive")
        lines.append(f"- entries: {archive['total_entries']}")
        lines.extend(f"- error: {message}" for message in archive["errors"])
        lines.extend(f"- warning: {message}" for message in archive["warnings"])
        lines.append("")
        lines.append("## ADRs")
        lines.append(f"- adrs: {adr['total_adrs']}")
        if adr.get("missing_sequence_ids"):
            lines.append(
                "- missing_sequence_ids: " + ", ".join(adr["missing_sequence_ids"])
            )
        if adr.get("retired_ids"):
            lines.append("- retired_ids: " + ", ".join(adr["retired_ids"]))
        if adr.get("reserved_ids"):
            lines.append("- reserved_ids: " + ", ".join(adr["reserved_ids"]))
        if adr.get("backlog_master_ids"):
            lines.append(
                "- backlog_master_ids: " + ", ".join(adr["backlog_master_ids"])
            )
        if adr.get("backlog_autonomy_ids"):
            lines.append(
                "- backlog_autonomy_ids: " + ", ".join(adr["backlog_autonomy_ids"])
            )
        if adr.get("next_pointer_value") or adr.get("next_pointer_expected"):
            lines.append(
                "- next_pointer: "
                + (adr.get("next_pointer_value") or "missing")
                + " (expected "
                + (adr.get("next_pointer_expected") or "unknown")
                + ")"
            )
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
            f"- voiceterm test processes detected: {runtime_processes['total_detected']}"
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
        lines.append(f"- reclaim estimate: {reports['candidate_reclaim_human']}")
        lines.extend(f"- error: {message}" for message in reports["errors"])
        lines.extend(f"- warning: {message}" for message in reports["warnings"])
        lines.append("")
        lines.append("## Mutation Badge")
        lines.extend(f"- error: {message}" for message in mutation_badge["errors"])
        lines.extend(f"- warning: {message}" for message in mutation_badge["warnings"])
        if not mutation_badge["errors"] and not mutation_badge["warnings"]:
            lines.append("- ok")
        lines.append("")
        lines.append("## README Presence")
        lines.extend(f"- error: {message}" for message in readme_presence["errors"])
        lines.extend(f"- warning: {message}" for message in readme_presence["warnings"])
        if not readme_presence["errors"] and not readme_presence["warnings"]:
            lines.append("- ok")
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
