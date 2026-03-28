"""Governed `devctl hygiene` command implementation."""

from __future__ import annotations

import json

from ...common import emit_output, pipe_output, write_output
from ...config import REPO_ROOT as CONFIG_REPO_ROOT
from ...governance.branch_matching import head_matches_release_branch
from ...governance.push_policy import load_push_policy
from ...process_sweep.core import scan_repo_hygiene_process_tree
from ...reports_retention import build_reports_hygiene_guard
from ...time_utils import utc_timestamp
from .. import hygiene_audits
from ..hygiene_render import render_md
from . import hygiene_support

REPO_ROOT = CONFIG_REPO_ROOT
STRICT_WARNING_EXEMPTION_SECTIONS = {
    "mutation_badge": "mutation_badge",
    "publications": "publications",
}
RELEASE_MAINTENANCE_WARNING_SOURCES = ("mutation_badge", "publications")
ORPHAN_TEST_MIN_AGE_SECONDS = hygiene_support.ORPHAN_TEST_MIN_AGE_SECONDS
STALE_ACTIVE_TEST_MIN_AGE_SECONDS = hygiene_support.STALE_ACTIVE_TEST_MIN_AGE_SECONDS


class _RepoAuditCall:
    def __init__(self, audit_fn):
        self._audit_fn = audit_fn

    def __call__(self):
        return self._audit_fn(REPO_ROOT)


class _SupportRepoCall:
    def __init__(self, support_fn):
        self._support_fn = support_fn

    def __call__(self, *args, **kwargs):
        _sync_repo_root()
        return self._support_fn(*args, **kwargs)


def _sync_repo_root() -> None:
    hygiene_support.REPO_ROOT = REPO_ROOT


_audit_archive = _RepoAuditCall(hygiene_audits.audit_archive)
_audit_adrs = _RepoAuditCall(hygiene_audits.audit_adrs)
_audit_scripts = _RepoAuditCall(hygiene_audits.audit_scripts)
_audit_publication_sync = _RepoAuditCall(hygiene_audits.audit_publication_sync)
_scan_repo_hygiene_processes = scan_repo_hygiene_process_tree
_scan_voiceterm_test_processes = _scan_repo_hygiene_processes


def _audit_runtime_processes() -> dict:
    _sync_repo_root()
    return hygiene_support._audit_runtime_processes(
        process_scanner=_scan_voiceterm_test_processes
    )


_fix_pycache_dirs = _SupportRepoCall(hygiene_support._fix_pycache_dirs)
_audit_mutation_badge = _SupportRepoCall(hygiene_support._audit_mutation_badge)
_audit_readme_presence = _SupportRepoCall(hygiene_support._audit_readme_presence)


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


def _requested_warning_sources(args) -> tuple[str, ...]:
    return tuple(
        str(source).strip()
        for source in getattr(args, "ignore_warning_source", ()) or ()
        if str(source).strip()
    )


def _auto_ignored_release_warning_sources(
    *,
    strict_release_warnings: bool,
) -> tuple[str, ...]:
    if not strict_release_warnings:
        return ()
    push_policy = load_push_policy()
    if head_matches_release_branch("HEAD", push_policy.release_branch):
        return ()
    return RELEASE_MAINTENANCE_WARNING_SOURCES


def _resolve_ignored_warning_sources(
    args,
    *,
    strict_release_warnings: bool,
) -> tuple[str, ...]:
    ignored_sources = list(_requested_warning_sources(args))
    for source in _auto_ignored_release_warning_sources(
        strict_release_warnings=strict_release_warnings
    ):
        if source not in ignored_sources:
            ignored_sources.append(source)
    return tuple(ignored_sources)


def run(args) -> int:
    """Audit archive/ADR/scripts hygiene and report drift."""
    strict_release_warnings = bool(
        getattr(args, "strict_release_warnings", False)
    )
    strict_warnings = bool(
        getattr(args, "strict_warnings", False) or strict_release_warnings
    )

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
    section_by_source: dict[str, dict[str, object]] = {}
    for name, section in (
        ("archive", archive),
        ("adr", adr),
        ("scripts", scripts),
        ("publications", publications),
        ("runtime_processes", runtime_processes),
        ("reports", reports),
        ("mutation_badge", mutation_badge),
        ("readme_presence", readme_presence),
    ):
        section_by_source[name] = section
    sections = list(section_by_source.values())
    ignored_warning_sources = _resolve_ignored_warning_sources(
        args,
        strict_release_warnings=strict_release_warnings,
    )

    error_count = sum(len(section["errors"]) for section in sections)
    warning_count = sum(len(section["warnings"]) for section in sections)
    warning_fail_count, ignored_warning_count = _strict_warning_counts(
        strict_warnings=strict_warnings,
        ignored_warning_sources=ignored_warning_sources,
        section_by_source=section_by_source,
    )
    ok = error_count == 0 and warning_fail_count == 0

    report: dict[str, object] = {}
    report["command"] = "hygiene"
    report["timestamp"] = utc_timestamp()
    report["ok"] = ok
    report["strict_warnings"] = strict_warnings
    report["strict_release_warnings"] = strict_release_warnings
    report["error_count"] = error_count
    report["warning_count"] = warning_count
    report["warning_fail_count"] = warning_fail_count
    report["ignored_warning_sources"] = list(ignored_warning_sources)
    report["ignored_warning_count"] = ignored_warning_count
    report["archive"] = archive
    report["adr"] = adr
    report["scripts"] = scripts
    report["publications"] = publications
    report["runtime_processes"] = runtime_processes
    report["reports"] = reports
    report["mutation_badge"] = mutation_badge
    report["readme_presence"] = readme_presence
    report["fix"] = fix_report

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
