"""Shared report-retention helpers for `devctl` cleanup and hygiene warnings."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

DEFAULT_REPORTS_ROOT_RELATIVE = Path("dev/reports")

# Only these roots are considered ephemeral run artifacts.
MANAGED_REPORT_SUBROOTS: Tuple[Path, ...] = (
    Path("autonomy/benchmarks"),
    Path("autonomy/experiments"),
    Path("autonomy/library"),
    Path("autonomy/runs"),
    Path("autonomy/swarms"),
    Path("failures"),
)

# Never delete these paths or their descendants.
PROTECTED_REPORT_PATHS: Tuple[Path, ...] = (
    Path("audits"),
    Path("autonomy/controller_state"),
    Path("autonomy/queue"),
    Path("data_science/history"),
    Path("data_science/latest"),
)

DEFAULT_RETENTION_MAX_AGE_DAYS = 30
DEFAULT_RETENTION_KEEP_RECENT = 10
DEFAULT_HYGIENE_WARN_DIR_THRESHOLD = 150
DEFAULT_HYGIENE_WARN_RECLAIM_BYTES = 512 * 1024 * 1024


def format_bytes(num_bytes: int) -> str:
    """Return a compact human-readable byte string."""
    value = float(max(0, int(num_bytes)))
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{int(num_bytes)} B"


def resolve_reports_root(
    repo_root: Path,
    reports_root_arg: str | None = None,
) -> tuple[Path | None, str | None]:
    """Resolve reports root and ensure it stays under repository root."""
    root = repo_root.resolve()
    raw = (
        Path(reports_root_arg).expanduser()
        if reports_root_arg
        else DEFAULT_REPORTS_ROOT_RELATIVE
    )
    candidate = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None, f"reports root is outside repository root: {candidate}"
    if candidate == root:
        return None, "reports root cannot be repository root"
    if candidate == (root / ".git"):
        return None, "reports root cannot be .git directory"
    return candidate, None


def _is_protected_path(relative_to_reports_root: Path) -> bool:
    for protected in PROTECTED_REPORT_PATHS:
        if (
            relative_to_reports_root == protected
            or protected in relative_to_reports_root.parents
            or relative_to_reports_root in protected.parents
        ):
            return True
    return False


def _estimate_directory_size_bytes(path: Path) -> tuple[int, list[str]]:
    total_bytes = 0
    warnings: list[str] = []
    stack: list[str] = [str(path)]

    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_file(follow_symlinks=False):
                            total_bytes += entry.stat(follow_symlinks=False).st_size
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                    except OSError as exc:
                        warnings.append(f"Unable to inspect {entry.path}: {exc}")
        except OSError as exc:
            warnings.append(f"Unable to scan {current}: {exc}")

    return total_bytes, warnings


def _scan_subroot(
    repo_root: Path,
    reports_root: Path,
    subroot: Path,
    *,
    max_age_days: int,
    keep_recent: int,
    now_utc: datetime,
) -> dict:
    subroot_path = reports_root / subroot
    summary = {
        "subroot": str(subroot),
        "path": str(subroot_path),
        "exists": subroot_path.exists(),
        "run_dirs": 0,
        "candidate_count": 0,
        "candidate_reclaim_bytes": 0,
        "warnings": [],
        "candidates": [],
    }

    if not subroot_path.exists():
        return summary
    if not subroot_path.is_dir():
        summary["warnings"].append(f"Managed reports path is not a directory: {subroot_path}")
        return summary

    entries: list[dict] = []
    for child in subroot_path.iterdir():
        if not child.is_dir():
            continue
        if child.is_symlink():
            summary["warnings"].append(f"Skipping symlink directory: {child}")
            continue
        try:
            stat = child.stat()
        except OSError as exc:
            summary["warnings"].append(f"Unable to stat {child}: {exc}")
            continue

        relative_to_reports = child.relative_to(reports_root)
        age_days = max(0.0, (now_utc.timestamp() - stat.st_mtime) / 86400.0)
        entries.append(
            {
                "path": child,
                "mtime": stat.st_mtime,
                "age_days": age_days,
                "relative_to_reports": relative_to_reports,
                "protected": _is_protected_path(relative_to_reports),
            }
        )

    entries.sort(key=lambda item: item["mtime"], reverse=True)
    summary["run_dirs"] = len(entries)

    for index, item in enumerate(entries):
        keep_recent_guard = index < keep_recent
        stale = item["age_days"] >= max_age_days
        if item["protected"] or keep_recent_guard or not stale:
            continue

        path = item["path"]
        size_bytes, size_warnings = _estimate_directory_size_bytes(path)
        summary["warnings"].extend(size_warnings)

        relative_repo = path.relative_to(repo_root)
        candidate = {
            "path": str(path),
            "relative_path": str(relative_repo),
            "subroot": str(subroot),
            "age_days": round(item["age_days"], 2),
            "modified_at": datetime.fromtimestamp(item["mtime"], tz=timezone.utc).isoformat(),
            "size_bytes": size_bytes,
            "size_human": format_bytes(size_bytes),
        }
        summary["candidates"].append(candidate)
        summary["candidate_count"] += 1
        summary["candidate_reclaim_bytes"] += size_bytes

    return summary


def build_reports_cleanup_plan(
    repo_root: Path,
    *,
    reports_root_arg: str | None = None,
    max_age_days: int = DEFAULT_RETENTION_MAX_AGE_DAYS,
    keep_recent: int = DEFAULT_RETENTION_KEEP_RECENT,
    now_utc: datetime | None = None,
) -> dict:
    """Build a safe cleanup plan for stale report directories."""
    now = now_utc or datetime.now(tz=timezone.utc)
    errors: list[str] = []
    warnings: list[str] = []

    if max_age_days < 0:
        errors.append("max_age_days must be >= 0")
    if keep_recent < 0:
        errors.append("keep_recent must be >= 0")

    reports_root, resolve_error = resolve_reports_root(repo_root, reports_root_arg)
    if resolve_error:
        errors.append(resolve_error)

    report = {
        "reports_root": str(reports_root) if reports_root is not None else str(reports_root_arg),
        "reports_root_exists": bool(reports_root and reports_root.exists()),
        "max_age_days": int(max_age_days),
        "keep_recent": int(keep_recent),
        "managed_subroots": [str(path) for path in MANAGED_REPORT_SUBROOTS],
        "candidate_count": 0,
        "managed_run_dirs": 0,
        "candidate_reclaim_bytes": 0,
        "candidate_reclaim_human": format_bytes(0),
        "subroots": [],
        "candidates": [],
        "warnings": warnings,
        "errors": errors,
        "ok": False,
    }

    if errors or reports_root is None:
        report["ok"] = False
        return report

    if not reports_root.exists():
        warnings.append(f"Reports root does not exist: {reports_root}")
        report["ok"] = True
        return report

    if not reports_root.is_dir():
        errors.append(f"Reports root is not a directory: {reports_root}")
        report["ok"] = False
        return report

    for subroot in MANAGED_REPORT_SUBROOTS:
        summary = _scan_subroot(
            repo_root.resolve(),
            reports_root,
            subroot,
            max_age_days=max_age_days,
            keep_recent=keep_recent,
            now_utc=now,
        )
        report["subroots"].append(summary)
        report["managed_run_dirs"] += int(summary["run_dirs"])
        report["candidate_count"] += int(summary["candidate_count"])
        report["candidate_reclaim_bytes"] += int(summary["candidate_reclaim_bytes"])
        report["candidates"].extend(summary["candidates"])
        warnings.extend(summary["warnings"])

    report["candidate_reclaim_human"] = format_bytes(report["candidate_reclaim_bytes"])
    report["ok"] = not errors
    return report


def build_reports_hygiene_guard(
    repo_root: Path,
    *,
    reports_root_arg: str | None = None,
    max_age_days: int = DEFAULT_RETENTION_MAX_AGE_DAYS,
    keep_recent: int = DEFAULT_RETENTION_KEEP_RECENT,
    warn_run_dir_threshold: int = DEFAULT_HYGIENE_WARN_DIR_THRESHOLD,
    warn_reclaim_bytes: int = DEFAULT_HYGIENE_WARN_RECLAIM_BYTES,
) -> dict:
    """Build a hygiene warning payload for report-growth drift."""
    plan = build_reports_cleanup_plan(
        repo_root,
        reports_root_arg=reports_root_arg,
        max_age_days=max_age_days,
        keep_recent=keep_recent,
    )

    warnings = list(plan.get("warnings", []))
    if plan.get("candidate_count", 0) > 0:
        warnings.append(
            "Report retention drift: "
            f"{plan['candidate_count']} stale run directories are eligible for cleanup "
            f"(~{plan['candidate_reclaim_human']}). Run `python3 dev/scripts/devctl.py "
            "reports-cleanup --dry-run` to review and prune safely."
        )

    if plan.get("managed_run_dirs", 0) >= warn_run_dir_threshold:
        warnings.append(
            "Report footprint is high: "
            f"{plan['managed_run_dirs']} managed run directories under "
            f"{plan['reports_root']} (threshold: {warn_run_dir_threshold})."
        )

    if plan.get("candidate_reclaim_bytes", 0) >= warn_reclaim_bytes:
        warnings.append(
            "Report reclaim estimate exceeds threshold: "
            f"{plan['candidate_reclaim_human']} eligible "
            f"(threshold: {format_bytes(warn_reclaim_bytes)})."
        )

    return {
        "reports_root": plan.get("reports_root"),
        "reports_root_exists": bool(plan.get("reports_root_exists")),
        "max_age_days": int(max_age_days),
        "keep_recent": int(keep_recent),
        "managed_run_dirs": int(plan.get("managed_run_dirs", 0)),
        "candidate_count": int(plan.get("candidate_count", 0)),
        "candidate_reclaim_bytes": int(plan.get("candidate_reclaim_bytes", 0)),
        "candidate_reclaim_human": plan.get("candidate_reclaim_human", format_bytes(0)),
        "warnings": warnings,
        "errors": list(plan.get("errors", [])),
        "subroots": plan.get("subroots", []),
    }
