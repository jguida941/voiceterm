#!/usr/bin/env python3
"""Periodic duplication audit wrapper for jscpd reports."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from check_duplication_audit_support import (
        derive_status,
        find_shared_logic_candidates,
        render_markdown,
        run_python_fallback,
    )
except ModuleNotFoundError:  # pragma: no cover - package import
    from dev.scripts.checks.check_duplication_audit_support import (
        derive_status,
        find_shared_logic_candidates,
        render_markdown,
        run_python_fallback,
    )

if __package__:
    from .candidates import (
        _shared_logic_candidate_paths,
        _should_require_duplication_report,
    )
    from .report import (
        _extract_duplication_percent,
        _extract_duplicates_count,
        _load_report,
        _path_for_report,
    )
    from .runner import _run_jscpd
else:  # pragma: no cover - standalone script fallback
    from candidates import (
        _shared_logic_candidate_paths,
        _should_require_duplication_report,
    )
    from report import (
        _extract_duplication_percent,
        _extract_duplicates_count,
        _load_report,
        _path_for_report,
    )
    from runner import _run_jscpd

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
DEFAULT_SOURCE_ROOT = REPO_ROOT / "rust" / "src"
DEFAULT_REPORT_DIR = REPO_ROOT / "dev" / "reports" / "duplication"
DEFAULT_REPORT_PATH = DEFAULT_REPORT_DIR / "jscpd-report.json"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        default=str(DEFAULT_SOURCE_ROOT),
        help="Directory to scan for duplication (default: rust/src)",
    )
    parser.add_argument(
        "--report-path",
        default=str(DEFAULT_REPORT_PATH),
        help="jscpd JSON report path",
    )
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=168.0,
        help="Maximum acceptable report age in hours",
    )
    parser.add_argument(
        "--run-jscpd",
        action="store_true",
        help="Run jscpd before evaluating report freshness",
    )
    parser.add_argument(
        "--run-python-fallback",
        action="store_true",
        help=(
            "When jscpd is unavailable and --allow-missing-tool is set, "
            "generate report evidence via a built-in line-window scanner"
        ),
    )
    parser.add_argument(
        "--allow-missing-tool",
        action="store_true",
        help="Treat missing jscpd binary as warning when --run-jscpd is requested",
    )
    parser.add_argument(
        "--jscpd-bin",
        default="jscpd",
        help="jscpd binary name/path",
    )
    parser.add_argument("--min-lines", type=int, default=10)
    parser.add_argument("--min-tokens", type=int, default=100)
    parser.add_argument(
        "--max-duplication-percent",
        type=float,
        default=10.0,
        help="Fail when jscpd total percentage is above this value",
    )
    parser.add_argument(
        "--check-shared-logic",
        action="store_true",
        help=(
            "Scan newly added Python/tooling files for advisory shared-logic "
            "candidates that should likely extend existing helpers/scaffolds."
        ),
    )
    parser.add_argument(
        "--since-ref",
        help="Optional git base ref for new-file shared-logic scanning.",
    )
    parser.add_argument(
        "--head-ref",
        default="HEAD",
        help="Git head ref used with --since-ref (default: HEAD).",
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        help="Optional explicit repository-relative paths for shared-logic scanning.",
    )
    parser.add_argument(
        "--shared-logic-min-overlap-lines",
        type=int,
        default=8,
        help="Minimum normalized shared lines for helper-overlap warnings.",
    )
    parser.add_argument(
        "--shared-logic-min-overlap-ratio",
        type=float,
        default=0.60,
        help="Minimum helper-overlap ratio for advisory shared-logic warnings.",
    )
    parser.add_argument(
        "--shared-logic-min-shared-imports",
        type=int,
        default=3,
        help="Minimum shared project imports for orchestration-clone warnings.",
    )
    parser.add_argument(
        "--shared-logic-min-import-ratio",
        type=float,
        default=0.75,
        help="Minimum project-import overlap ratio for orchestration-clone warnings.",
    )
    parser.add_argument(
        "--shared-logic-min-shared-markers",
        type=int,
        default=2,
        help="Minimum shared runner markers for orchestration-clone warnings.",
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    now = datetime.now(timezone.utc)

    source_root = Path(args.source_root)
    report_path = Path(args.report_path)
    report_dir = report_path.parent
    errors: list[str] = []
    warnings: list[str] = []
    jscpd_status = "not_requested"
    shared_logic_candidates: list[dict] = []

    if args.run_jscpd:
        ok, run_error, run_status = _run_jscpd(
            source_root=source_root,
            report_dir=report_dir,
            report_path=report_path,
            jscpd_bin=args.jscpd_bin,
            min_lines=args.min_lines,
            min_tokens=args.min_tokens,
        )
        if run_status is not None:
            jscpd_status = run_status
        if not ok and run_error:
            if run_status == "missing_tool" and args.allow_missing_tool:
                warnings.append(run_error)
                if args.run_python_fallback:
                    fallback_ok, fallback_error, fallback_status = run_python_fallback(
                        source_root=source_root,
                        report_path=report_path,
                        min_lines=args.min_lines,
                        path_for_report=_path_for_report,
                    )
                    jscpd_status = fallback_status
                    if not fallback_ok and fallback_error:
                        errors.append(fallback_error)
            else:
                errors.append(run_error)

    report_required = _should_require_duplication_report(args, report_path)
    report_exists = report_path.exists()
    payload: dict | None = {}
    if report_required or report_exists:
        payload, load_error = _load_report(report_path)
        if load_error is not None:
            errors.append(load_error)
            payload = {}

    report_age_hours: float | None = None
    blocked_by_tooling = bool(
        jscpd_status == "missing_tool" and args.run_jscpd and not report_exists
    )
    if report_exists:
        mtime = datetime.fromtimestamp(report_path.stat().st_mtime, tz=timezone.utc)
        report_age_hours = max(0.0, (now - mtime).total_seconds() / 3600.0)
        if report_age_hours > args.max_age_hours:
            errors.append(
                f"jscpd report is stale ({report_age_hours:.2f}h > {args.max_age_hours:.2f}h): "
                f"{_path_for_report(report_path)}"
            )

    duplication_percent = _extract_duplication_percent(payload or {})
    duplicates_count = _extract_duplicates_count(payload or {})
    if report_exists and duplication_percent is None:
        warnings.append("jscpd report is missing `statistics.total.percentage`")
    elif (
        duplication_percent is not None
        and duplication_percent > args.max_duplication_percent
    ):
        errors.append(
            "duplication percent exceeds threshold "
            f"({duplication_percent:.2f}% > {args.max_duplication_percent:.2f}%)"
        )

    if args.check_shared_logic:
        candidate_paths, discovery_errors = _shared_logic_candidate_paths(args)
        errors.extend(discovery_errors)
        if not discovery_errors:
            shared_logic_candidates = find_shared_logic_candidates(
                repo_root=REPO_ROOT,
                candidate_paths=candidate_paths,
                path_for_report=_path_for_report,
                min_line_overlap=args.shared_logic_min_overlap_lines,
                min_line_ratio=args.shared_logic_min_overlap_ratio,
                min_shared_imports=args.shared_logic_min_shared_imports,
                min_import_ratio=args.shared_logic_min_import_ratio,
                min_shared_markers=args.shared_logic_min_shared_markers,
            )
            warnings.extend(item["summary"] for item in shared_logic_candidates)

    status = derive_status(
        errors=errors,
        warnings=warnings,
        blocked_by_tooling=blocked_by_tooling,
        duplication_percent=duplication_percent,
        max_duplication_percent=args.max_duplication_percent,
        report_age_hours=report_age_hours,
        max_age_hours=args.max_age_hours,
        report_exists=report_exists,
    )

    report = {
        "command": "check_duplication_audit",
        "timestamp": now.isoformat(),
        "ok": len(errors) == 0,
        "status": status,
        "blocked_by_tooling": blocked_by_tooling,
        "source_root": _path_for_report(source_root),
        "report_path": _path_for_report(report_path),
        "run_jscpd": args.run_jscpd,
        "run_python_fallback": args.run_python_fallback,
        "allow_missing_tool": args.allow_missing_tool,
        "jscpd_status": jscpd_status,
        "report_exists": report_exists,
        "report_age_hours": report_age_hours,
        "max_age_hours": args.max_age_hours,
        "duplication_percent": duplication_percent,
        "max_duplication_percent": args.max_duplication_percent,
        "duplicates_count": duplicates_count,
        "check_shared_logic": args.check_shared_logic,
        "shared_logic_candidate_count": len(shared_logic_candidates),
        "shared_logic_candidates": shared_logic_candidates,
        "errors": errors,
        "warnings": warnings,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
