"""`devctl hygiene` command.

Use this command to catch governance drift in archive/ADR/scripts docs and to
surface leaked repo-related host processes that can impact later runs.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Tuple

from ..common import emit_output, pipe_output, write_output
from ..time_utils import utc_timestamp
from ..config import REPO_ROOT
from ..process_sweep.core import (
    DEFAULT_ORPHAN_MIN_AGE_SECONDS,
    DEFAULT_STALE_MIN_AGE_SECONDS,
    SECONDS_PER_DAY,
    format_process_rows,
    scan_repo_hygiene_process_tree,
    split_orphaned_processes,
    split_stale_processes,
)
from ..reports_retention import build_reports_hygiene_guard
from . import hygiene_audits
from .hygiene_render import render_md

ORPHAN_TEST_MIN_AGE_SECONDS = DEFAULT_ORPHAN_MIN_AGE_SECONDS
STALE_ACTIVE_TEST_MIN_AGE_SECONDS = DEFAULT_STALE_MIN_AGE_SECONDS
PROCESS_LINE_MAX_LEN = 180
PROCESS_REPORT_LIMIT = 8
SUPERVISED_CONDUCTOR_SCOPE = "review_channel_conductor"


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


def _audit_publication_sync() -> Dict:
    """Compatibility wrapper for tracked external publication drift."""
    return hygiene_audits.audit_publication_sync(REPO_ROOT)


def _format_process_rows(rows: List[Dict]) -> str:
    return format_process_rows(
        rows,
        line_max_len=PROCESS_LINE_MAX_LEN,
        row_limit=PROCESS_REPORT_LIMIT,
    )


def _scan_repo_hygiene_processes() -> Tuple[List[Dict], List[str]]:
    return scan_repo_hygiene_process_tree()


def _scan_voiceterm_test_processes() -> Tuple[List[Dict], List[str]]:
    """Compatibility wrapper retained for existing hygiene tests."""
    return _scan_repo_hygiene_processes()


def _runtime_process_label(rows: List[Dict]) -> str:
    scopes = {str(row.get("match_scope", "")).strip() for row in rows if row.get("match_scope")}
    return "voiceterm test processes" if not scopes or scopes == {"voiceterm"} else "repo-related host processes"


def _audit_runtime_processes() -> Dict:
    """Detect orphaned repo-related host processes and report active ones."""
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
    supervised_conductors = [
        row
        for row in active
        if row.get("match_scope") == SUPERVISED_CONDUCTOR_SCOPE and row.get("ppid") != 1
    ]
    supervised_conductor_pids = {row["pid"] for row in supervised_conductors}
    active = [row for row in active if row.get("pid") not in supervised_conductor_pids]
    stale_active, fresh_active = split_stale_processes(
        active,
        min_age_seconds=STALE_ACTIVE_TEST_MIN_AGE_SECONDS,
    )
    process_label = _runtime_process_label(test_processes)

    if orphaned:
        prefix = (
            "Orphaned voiceterm test processes detected. Stop leaked runners before continuing: "
            if process_label == "voiceterm test processes"
            else "Orphaned repo-related host processes detected (detached PPID=1). Stop leaked runners before continuing: "
        )
        errors.append(prefix + _format_process_rows(orphaned))
    if stale_active:
        prefix = (
            "Stale active voiceterm test processes detected. "
            if process_label == "voiceterm test processes"
            else "Stale active repo-related host processes detected. "
        )
        errors.append(
            prefix
            + f"Any process running >= {STALE_ACTIVE_TEST_MIN_AGE_SECONDS}s should be stopped: "
            + _format_process_rows(stale_active)
        )
    if fresh_active:
        prefix = (
            "Active voiceterm test processes detected: "
            if process_label == "voiceterm test processes"
            else "Active repo-related host processes detected during hygiene run: "
        )
        warnings.append(prefix + _format_process_rows(fresh_active))

    return {
        "total_detected": len(test_processes),
        "active_supervised_conductors": supervised_conductors,
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
STRICT_WARNING_EXEMPTION_SECTIONS = {"mutation_badge": "mutation_badge"}


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


def _strict_warning_counts(
    *,
    strict_warnings: bool,
    ignored_warning_sources: tuple[str, ...],
    section_by_source: dict[str, dict[str, object]],
) -> tuple[int, int]:
    """Return blocking warning count and ignored warning count."""
    if not strict_warnings:
        return 0, 0

    ignored_warning_count = 0
    for source in ignored_warning_sources:
        section_name = STRICT_WARNING_EXEMPTION_SECTIONS.get(source)
        if not section_name:
            continue
        section = section_by_source.get(section_name, {})
        ignored_warning_count += len(section.get("warnings", []))

    warning_count = sum(
        len(section.get("warnings", [])) for section in section_by_source.values()
    )
    return max(0, warning_count - ignored_warning_count), ignored_warning_count


def run(args) -> int:
    """Audit archive/ADR/scripts hygiene and report drift."""
    strict_warnings = bool(getattr(args, "strict_warnings", False))
    archive = _audit_archive()
    adr = _audit_adrs()
    scripts = _audit_scripts()
    publications = _audit_publication_sync()
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
    section_by_source = {
        "archive": archive,
        "adr": adr,
        "scripts": scripts,
        "publications": publications,
        "runtime_processes": runtime_processes,
        "reports": reports,
        "mutation_badge": mutation_badge,
        "readme_presence": readme_presence,
    }
    sections = list(section_by_source.values())
    ignored_warning_sources = tuple(
        str(source).strip()
        for source in getattr(args, "ignore_warning_source", ()) or ()
        if str(source).strip()
    )

    error_count = sum(len(section["errors"]) for section in sections)
    warning_count = sum(len(section["warnings"]) for section in sections)
    warning_fail_count, ignored_warning_count = _strict_warning_counts(
        strict_warnings=strict_warnings,
        ignored_warning_sources=ignored_warning_sources,
        section_by_source=section_by_source,
    )
    ok = error_count == 0 and warning_fail_count == 0

    report = {
        "command": "hygiene",
        "timestamp": utc_timestamp(),
        "ok": ok,
        "strict_warnings": strict_warnings,
        "error_count": error_count,
        "warning_count": warning_count,
        "warning_fail_count": warning_fail_count,
        "ignored_warning_sources": list(ignored_warning_sources),
        "ignored_warning_count": ignored_warning_count,
        "archive": archive,
        "adr": adr,
        "scripts": scripts,
        "publications": publications,
        "runtime_processes": runtime_processes,
        "reports": reports,
        "mutation_badge": mutation_badge,
        "readme_presence": readme_presence,
        "fix": fix_report,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = render_md(report)

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
    return 0 if ok else 1
