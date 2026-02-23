"""`devctl hygiene` command.

Use this command to catch governance drift in archive/ADR/scripts docs and to
surface leaked VoiceTerm test processes that can impact later runs.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple

from ..common import pipe_output, write_output
from ..config import REPO_ROOT
from ..process_sweep import (
    DEFAULT_ORPHAN_MIN_AGE_SECONDS,
    format_process_rows,
    scan_matching_processes,
    split_orphaned_processes,
)
from . import hygiene_audits

# Match only VoiceTerm test binaries so warnings stay relevant.
VOICETERM_TEST_BIN_RE = re.compile(r"target/(?:debug|release)/deps/voiceterm-[0-9a-f]{8,}")
ORPHAN_TEST_MIN_AGE_SECONDS = DEFAULT_ORPHAN_MIN_AGE_SECONDS
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
    return scan_matching_processes(VOICETERM_TEST_BIN_RE)


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

    if orphaned:
        errors.append(
            "Orphaned voiceterm test binaries detected (detached PPID=1). "
            "Stop leaked runners before continuing: "
            f"{_format_process_rows(orphaned)}"
        )
    if active:
        warnings.append(
            "Active voiceterm test binaries detected during hygiene run: "
            f"{_format_process_rows(active)}"
        )

    return {
        "total_detected": len(test_processes),
        "orphaned": orphaned,
        "active": active,
        "errors": errors,
        "warnings": warnings,
    }


def run(args) -> int:
    """Audit archive/ADR/scripts hygiene and report drift."""
    archive = _audit_archive()
    adr = _audit_adrs()
    scripts = _audit_scripts()
    runtime_processes = _audit_runtime_processes()
    sections = [archive, adr, scripts, runtime_processes]

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
        lines.append(f"- voiceterm test binaries detected: {runtime_processes['total_detected']}")
        lines.extend(f"- error: {message}" for message in runtime_processes["errors"])
        lines.extend(f"- warning: {message}" for message in runtime_processes["warnings"])
        output = "\n".join(lines)

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    return 0 if ok else 1
