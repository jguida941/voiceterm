"""Rust audit collection and aggregation helpers for `devctl report`."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .config import REPO_ROOT
from .rust_audit_catalog import RUST_AUDIT_CATEGORY_INFO, RUST_AUDIT_GUARDS
from .rust_audit_render import build_rust_audit_charts, render_rust_audit_markdown


def resolve_rust_audit_mode(mode: str, since_ref: str | None) -> str:
    """Resolve auto mode so callers can pass a stable value downstream."""
    if mode != "auto":
        return mode
    return "commit-range" if since_ref else "absolute"


def _guard_command(
    *,
    guard_name: str,
    mode: str,
    since_ref: str | None,
    head_ref: str,
    dead_code_report_limit: int,
) -> list[str]:
    command = [
        "python3",
        str(REPO_ROOT / RUST_AUDIT_GUARDS[guard_name]["script"]),
        "--format",
        "json",
    ]
    if mode == "absolute":
        command.append("--absolute")
    elif mode == "commit-range":
        if not since_ref:
            raise ValueError("--since-ref is required when rust audit mode is commit-range")
        command.extend(["--since-ref", since_ref, "--head-ref", head_ref])
    if guard_name == "lint_debt":
        command.extend(
            [
                "--report-dead-code",
                "--dead-code-report-limit",
                str(max(0, dead_code_report_limit)),
            ]
        )
    return command


def _parse_guard_payload(
    *,
    guard_name: str,
    result: subprocess.CompletedProcess[str],
) -> tuple[dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if stderr:
        warnings.append(f"{guard_name}: {stderr}")
    if not stdout:
        errors.append(f"{guard_name}: empty JSON output")
        return {"error": "empty JSON output"}, warnings, errors
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        errors.append(f"{guard_name}: invalid JSON output ({exc})")
        return {"error": f"invalid JSON output ({exc})"}, warnings, errors
    if not isinstance(payload, dict):
        errors.append(f"{guard_name}: expected top-level object")
        return {"error": "expected top-level object"}, warnings, errors
    if result.returncode not in (0, 1):
        errors.append(
            f"{guard_name}: command failed with exit={result.returncode}"
        )
    return payload, warnings, errors


def _positive_counts_for_categories(
    report: dict[str, Any],
    categories: tuple[str, ...],
) -> dict[str, int]:
    totals = report.get("totals") if isinstance(report.get("totals"), dict) else {}
    positive: dict[str, int] = {}
    for category in categories:
        key = f"{category}_growth"
        raw = totals.get(key, 0)
        try:
            count = int(raw)
        except (TypeError, ValueError):
            count = 0
        if count > 0:
            positive[category] = count
    return positive


def _build_category_rows(
    guard_reports: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for guard_name, config in RUST_AUDIT_GUARDS.items():
        report = guard_reports.get(guard_name)
        if not isinstance(report, dict):
            continue
        positive = _positive_counts_for_categories(report, config["categories"])
        for category, count in positive.items():
            info = RUST_AUDIT_CATEGORY_INFO[category]
            rows.append(
                {
                    "guard": guard_name,
                    "category": category,
                    "label": info["label"],
                    "severity": info["severity"],
                    "weight": int(info["weight"]),
                    "count": count,
                    "why": info["why"],
                    "fix": info["fix"],
                }
            )
    return sorted(
        rows,
        key=lambda row: (-int(row["count"]) * int(row["weight"]), -int(row["count"]), str(row["label"])),
    )


def _build_hotspots(guard_reports: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    combined: dict[str, dict[str, Any]] = {}
    for guard_name, config in RUST_AUDIT_GUARDS.items():
        report = guard_reports.get(guard_name)
        if not isinstance(report, dict):
            continue
        violations = report.get("violations")
        if not isinstance(violations, list):
            continue
        categories = set(config["categories"])
        for violation in violations:
            if not isinstance(violation, dict):
                continue
            path = str(violation.get("path") or "").strip()
            if not path:
                continue
            growth = violation.get("growth")
            if not isinstance(growth, dict):
                continue
            file_row = combined.setdefault(
                path,
                {
                    "path": path,
                    "score": 0,
                    "count": 0,
                    "guards": set(),
                    "signals": set(),
                },
            )
            for category, raw in growth.items():
                if category not in categories:
                    continue
                try:
                    count = int(raw)
                except (TypeError, ValueError):
                    count = 0
                if count <= 0:
                    continue
                info = RUST_AUDIT_CATEGORY_INFO[category]
                file_row["count"] += count
                file_row["score"] += count * int(info["weight"])
                file_row["signals"].add(str(info["label"]))
                file_row["guards"].add(guard_name)
    rows: list[dict[str, Any]] = []
    for item in combined.values():
        rows.append(
            {
                "path": item["path"],
                "score": int(item["score"]),
                "count": int(item["count"]),
                "guard_count": len(item["guards"]),
                "signals": sorted(item["signals"]),
            }
        )
    return sorted(rows, key=lambda row: (-row["score"], -row["count"], row["path"]))


def collect_rust_audit_report(
    *,
    mode: str,
    since_ref: str | None = None,
    head_ref: str = "HEAD",
    dead_code_report_limit: int = 25,
) -> dict[str, Any]:
    """Run Rust guard scripts and aggregate a report-friendly summary."""
    resolved_mode = resolve_rust_audit_mode(mode, since_ref)
    warnings: list[str] = []
    errors: list[str] = []
    guard_reports: dict[str, dict[str, Any]] = {}
    guard_rows: list[dict[str, Any]] = []
    for guard_name in RUST_AUDIT_GUARDS:
        try:
            command = _guard_command(
                guard_name=guard_name,
                mode=resolved_mode,
                since_ref=since_ref,
                head_ref=head_ref,
                dead_code_report_limit=dead_code_report_limit,
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        payload, guard_warnings, guard_errors = _parse_guard_payload(
            guard_name=guard_name,
            result=result,
        )
        warnings.extend(guard_warnings)
        errors.extend(guard_errors)
        guard_reports[guard_name] = payload
        guard_rows.append(
            {
                "guard": guard_name,
                "ok": bool(payload.get("ok", False)),
                "files_considered": int(payload.get("files_considered", 0) or 0),
                "files_changed": int(payload.get("files_changed", 0) or 0),
                "violations": len(payload.get("violations", []) or []),
                "returncode": int(result.returncode),
            }
        )

    categories = _build_category_rows(guard_reports)
    hotspots = _build_hotspots(guard_reports)
    total_violation_files = len(hotspots)
    total_active_findings = sum(int(row["count"]) for row in categories)
    report = {
        "mode": resolved_mode,
        "since_ref": since_ref,
        "head_ref": head_ref,
        "ok": not errors and all(bool(row["ok"]) for row in guard_rows),
        "collection_ok": not errors,
        "warnings": warnings,
        "errors": errors,
        "summary": {
            "guard_count": len(guard_rows),
            "guard_failures": sum(1 for row in guard_rows if not bool(row["ok"])),
            "active_categories": len(categories),
            "total_active_findings": total_active_findings,
            "total_violation_files": total_violation_files,
            "top_risk_score": int(hotspots[0]["score"]) if hotspots else 0,
        },
        "guards": guard_rows,
        "guard_reports": guard_reports,
        "categories": categories,
        "hotspots": hotspots,
        "charts": [],
    }
    lint_debt_report = guard_reports.get("lint_debt", {})
    if isinstance(lint_debt_report, dict):
        report["summary"]["dead_code_instance_count"] = int(
            lint_debt_report.get("dead_code_instance_count", 0) or 0
        )
        report["summary"]["dead_code_without_reason_count"] = int(
            lint_debt_report.get("dead_code_without_reason_count", 0) or 0
        )
    return report
