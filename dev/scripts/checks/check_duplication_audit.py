#!/usr/bin/env python3
"""Periodic duplication audit wrapper for jscpd reports."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from check_duplication_audit_support import (
    derive_status,
    find_shared_logic_candidates,
    render_markdown,
    run_python_fallback,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE_ROOT = REPO_ROOT / "rust" / "src"
DEFAULT_REPORT_DIR = REPO_ROOT / "dev" / "reports" / "duplication"
DEFAULT_REPORT_PATH = DEFAULT_REPORT_DIR / "jscpd-report.json"


def _path_for_report(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


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


def _load_report(path: Path) -> tuple[dict | None, str | None]:
    if not path.exists():
        return None, _missing_report_message(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return None, f"failed to parse jscpd report: {exc}"
    if not isinstance(payload, dict):
        return None, "jscpd report root must be a JSON object"
    return payload, None


def _extract_duplication_percent(payload: dict) -> float | None:
    stats = payload.get("statistics")
    if not isinstance(stats, dict):
        return None
    total = stats.get("total")
    if not isinstance(total, dict):
        return None
    percent = total.get("percentage")
    if isinstance(percent, (int, float)):
        return float(percent)
    return None


def _extract_duplicates_count(payload: dict) -> int | None:
    duplicates = payload.get("duplicates")
    if isinstance(duplicates, list):
        return len(duplicates)
    return None


def _missing_report_message(path: Path) -> str:
    return (
        f"missing report file: {_path_for_report(path)}; run with --run-jscpd "
        "(requires jscpd, install via `npm install -g jscpd`) or pass --report-path "
        "to an existing jscpd JSON report"
    )


def _missing_tool_message(jscpd_bin: str, report_path: Path) -> str:
    return (
        f"jscpd binary not found: {jscpd_bin}; install via `npm install -g jscpd` "
        f"or provide report evidence at {_path_for_report(report_path)}. "
        "For constrained environments, rerun with --run-jscpd --allow-missing-tool."
    )


def _run_jscpd(
    *,
    source_root: Path,
    report_dir: Path,
    report_path: Path,
    jscpd_bin: str,
    min_lines: int,
    min_tokens: int,
) -> tuple[bool, str | None, str | None]:
    resolved_bin = shutil.which(jscpd_bin)
    if resolved_bin is None:
        return False, _missing_tool_message(jscpd_bin, report_path), "missing_tool"

    report_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        resolved_bin,
        source_root.as_posix(),
        "--min-lines",
        str(min_lines),
        "--min-tokens",
        str(min_tokens),
        "--format",
        "rust",
        "--reporters",
        "json",
        "--output",
        report_dir.as_posix(),
    ]
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr or proc.stdout).splitlines()[-10:])
        return (
            False,
            f"jscpd failed (exit {proc.returncode}): {tail}",
            "execution_failed",
        )
    if not report_path.exists():
        return (
            False,
            f"jscpd completed but report file missing: {_path_for_report(report_path)}",
            "missing_report",
        )
    return True, None, "ok"


def _normalize_candidate_paths(explicit_paths: list[str] | None) -> list[Path]:
    if not explicit_paths:
        return []
    return sorted(Path(path) for path in explicit_paths)


def _discover_new_paths(
    *,
    since_ref: str | None,
    head_ref: str,
) -> tuple[list[Path], list[str]]:
    errors: list[str] = []
    paths: set[Path] = set()
    diff_cmd = ["git", "diff", "--name-only", "--diff-filter=A"]
    if since_ref:
        diff_cmd.extend([since_ref, head_ref])
    else:
        diff_cmd.append("HEAD")
    diff_proc = subprocess.run(
        diff_cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if diff_proc.returncode != 0:
        errors.append(diff_proc.stderr.strip() or "git diff failed")
    else:
        paths.update(Path(line.strip()) for line in diff_proc.stdout.splitlines() if line.strip())

    untracked_proc = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if untracked_proc.returncode != 0:
        errors.append(untracked_proc.stderr.strip() or "git ls-files failed")
    else:
        paths.update(
            Path(line.strip()) for line in untracked_proc.stdout.splitlines() if line.strip()
        )
    return sorted(paths), errors


def _shared_logic_candidate_paths(args) -> tuple[list[Path], list[str]]:
    explicit_paths = _normalize_candidate_paths(args.paths)
    if explicit_paths:
        return explicit_paths, []
    return _discover_new_paths(since_ref=args.since_ref, head_ref=args.head_ref)


def _should_require_duplication_report(args, report_path: Path) -> bool:
    if args.check_shared_logic and not args.run_jscpd and not report_path.exists():
        return False
    return True


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
