"""Python guard aggregation helpers for `devctl report`."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .config import REPO_ROOT
from .governance.guard_findings import build_guard_findings
from .quality_policy import resolve_quality_policy
from .quality_policy_loader import QUALITY_POLICY_ENV_VAR

PYTHON_GUARD_SPECS: dict[str, dict[str, Any]] = {
    "python_dict_schema": {
        "label": "dict schema",
        "script": "dev/scripts/checks/check_python_dict_schema.py",
        "weights": {
            "large_dict_literals": 140,
            "weak_dict_any_aliases": 220,
        },
    },
    "python_global_mutable": {
        "label": "default traps",
        "script": "dev/scripts/checks/check_python_global_mutable.py",
        "weights": {
            "global_statements": 280,
            "mutable_default_args": 260,
            "function_call_default_args": 240,
            "dataclass_mutable_defaults": 260,
            "dataclass_call_defaults": 240,
        },
    },
    "python_design_complexity": {
        "label": "design complexity",
        "script": "dev/scripts/checks/check_python_design_complexity.py",
        "weights": {
            "high_branch_functions": 210,
            "high_return_functions": 180,
        },
    },
    "python_cyclic_imports": {
        "label": "cyclic imports",
        "script": "dev/scripts/checks/check_python_cyclic_imports.py",
        "weights": {
            "cyclic_imports": 320,
        },
    },
    "parameter_count": {
        "label": "parameter count",
        "script": "dev/scripts/checks/check_parameter_count.py",
        "weights": {
            "high_param_functions": 180,
        },
    },
    "nesting_depth": {
        "label": "nesting depth",
        "script": "dev/scripts/checks/check_nesting_depth.py",
        "weights": {
            "deeply_nested_functions": 170,
        },
    },
    "god_class": {
        "label": "god class",
        "script": "dev/scripts/checks/check_god_class.py",
        "weights": {
            "god_classes": 210,
        },
    },
    "python_broad_except": {
        "label": "broad except",
        "script": "dev/scripts/checks/check_python_broad_except.py",
        "violation_weight": 230,
        "detail_weights": {
            "bare": 290,
            "BaseException": 260,
            "Exception": 230,
        },
    },
    "python_subprocess_policy": {
        "label": "subprocess policy",
        "script": "dev/scripts/checks/check_python_subprocess_policy.py",
        "violation_weight": 250,
        "detail_weights": {
            "missing_check": 250,
        },
    },
}


def resolve_python_guard_mode(since_ref: str | None) -> str:
    """Return collection mode based on commit-range settings."""
    return "commit-range" if since_ref else "working-tree"


def _guard_command(
    *,
    script: str,
    since_ref: str | None,
    head_ref: str,
) -> list[str]:
    command = ["python3", str(REPO_ROOT / script), "--format", "json"]
    if since_ref:
        command.extend(["--since-ref", since_ref, "--head-ref", head_ref])
    return command


def _guard_env(policy_path: str | None) -> dict[str, str] | None:
    if not policy_path:
        return None
    env = os.environ.copy()
    env[QUALITY_POLICY_ENV_VAR] = str(Path(policy_path).expanduser())
    return env


def _parse_guard_payload(
    *,
    guard_key: str,
    result: subprocess.CompletedProcess[str],
) -> tuple[dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if stderr:
        warnings.append(f"{guard_key}: {stderr}")
    if not stdout:
        errors.append(f"{guard_key}: empty JSON output")
        return {"error": "empty JSON output"}, warnings, errors
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        errors.append(f"{guard_key}: invalid JSON output ({exc})")
        return {"error": f"invalid JSON output ({exc})"}, warnings, errors
    if not isinstance(payload, dict):
        errors.append(f"{guard_key}: expected top-level object")
        return {"error": "expected top-level object"}, warnings, errors
    if result.returncode not in (0, 1):
        errors.append(f"{guard_key}: command failed with exit={result.returncode}")
    return payload, warnings, errors


def _build_hotspots(
    guard_reports: dict[str, dict[str, Any]],
    *,
    top_n: int,
) -> tuple[list[dict[str, Any]], int]:
    combined: dict[str, dict[str, Any]] = {}
    total_findings = 0
    for guard_key, spec in PYTHON_GUARD_SPECS.items():
        report = guard_reports.get(guard_key)
        if not isinstance(report, dict):
            continue
        weights = spec.get("weights", {})
        if not isinstance(weights, dict):
            continue
        detail_weights = spec.get("detail_weights", {})
        if not isinstance(detail_weights, dict):
            detail_weights = {}
        violation_weight = int(spec.get("violation_weight", 120))
        label = str(spec.get("label") or guard_key)
        violations = report.get("violations")
        if not isinstance(violations, list):
            continue
        for violation in violations:
            if not isinstance(violation, dict):
                continue
            path = str(violation.get("path") or "").strip()
            growth = violation.get("growth")
            if not path:
                continue
            row = combined.setdefault(
                path,
                {
                    "path": path,
                    "score": 0,
                    "count": 0,
                    "guards": set(),
                    "signals": set(),
                },
            )
            if not isinstance(growth, dict):
                kind = str(violation.get("kind") or "").strip()
                reason = str(violation.get("reason") or "").strip()
                if kind:
                    detail = kind
                elif "check=" in reason:
                    detail = "missing_check"
                else:
                    detail = "violation"
                weight = int(detail_weights.get(detail, violation_weight))
                signal = f"{label}:{detail}"
                row["count"] += 1
                row["score"] += weight
                row["guards"].add(guard_key)
                row["signals"].add(signal)
                total_findings += 1
                continue
            for category, raw in growth.items():
                try:
                    count = int(raw)
                except (TypeError, ValueError):
                    count = 0
                if count <= 0:
                    continue
                weight = int(weights.get(str(category), 120))
                signal = f"{label}:{category}"
                row["count"] += count
                row["score"] += count * weight
                row["guards"].add(guard_key)
                row["signals"].add(signal)
                total_findings += count
    rows: list[dict[str, Any]] = []
    for row in combined.values():
        rows.append(
            {
                "path": row["path"],
                "score": int(row["score"]),
                "count": int(row["count"]),
                "guard_count": len(row["guards"]),
                "signals": sorted(row["signals"]),
            }
        )
    rows.sort(key=lambda item: (-item["score"], -item["count"], item["path"]))
    if top_n > 0:
        rows = rows[:top_n]
    return rows, total_findings


def collect_python_guard_report(
    *,
    since_ref: str | None = None,
    head_ref: str = "HEAD",
    top_n: int = 20,
    policy_path: str | None = None,
) -> dict[str, Any]:
    """Run Python clean-code guards and aggregate a backlog summary."""
    warnings: list[str] = []
    errors: list[str] = []
    guard_reports: dict[str, dict[str, Any]] = {}
    guard_rows: list[dict[str, Any]] = []
    quality_policy = resolve_quality_policy(
        repo_root=REPO_ROOT,
        policy_path=policy_path,
    )
    for guard_key, spec in PYTHON_GUARD_SPECS.items():
        command = _guard_command(
            script=str(spec["script"]),
            since_ref=since_ref,
            head_ref=head_ref,
        )
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            env=_guard_env(policy_path),
            check=False,
        )
        payload, guard_warnings, guard_errors = _parse_guard_payload(
            guard_key=guard_key,
            result=result,
        )
        warnings.extend(guard_warnings)
        errors.extend(guard_errors)
        guard_reports[guard_key] = payload
        guard_rows.append(
            {
                "guard": guard_key,
                "label": spec["label"],
                "ok": bool(payload.get("ok", False)),
                "files_considered": int(payload.get("files_considered", 0) or 0),
                "files_changed": int(payload.get("files_changed", 0) or 0),
                "violations": len(payload.get("violations", []) or []),
                "returncode": int(result.returncode),
            }
        )
    hotspots, total_findings = _build_hotspots(guard_reports, top_n=max(0, top_n))
    guard_findings = build_guard_findings(
        guard_reports,
        repo_name=quality_policy.repo_name,
        source_artifact="python-guard-backlog:violations",
    )
    report = {
        "mode": resolve_python_guard_mode(since_ref),
        "since_ref": since_ref,
        "head_ref": head_ref,
        "ok": not errors and all(bool(row["ok"]) for row in guard_rows),
        "collection_ok": not errors,
        "warnings": warnings,
        "errors": errors,
        "summary": {
            "guard_count": len(guard_rows),
            "guard_failures": sum(1 for row in guard_rows if not bool(row["ok"])),
            "active_paths": len(hotspots),
            "total_active_findings": int(total_findings),
            "top_risk_score": int(hotspots[0]["score"]) if hotspots else 0,
        },
        "guards": guard_rows,
        "guard_reports": guard_reports,
        "guard_findings": guard_findings,
        "hotspots": hotspots,
    }
    return report


def render_python_guard_markdown(report: dict[str, Any]) -> list[str]:
    """Render markdown lines for a Python guard backlog report."""
    summary = report.get("summary", {})
    lines = ["## Python Guard Backlog"]
    lines.append(f"- mode: {report.get('mode', 'unknown')}")
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- guards: {summary.get('guard_count', 0)}")
    lines.append(f"- guard_failures: {summary.get('guard_failures', 0)}")
    lines.append(f"- active_paths: {summary.get('active_paths', 0)}")
    lines.append(f"- total_active_findings: {summary.get('total_active_findings', 0)}")
    lines.append(f"- top_risk_score: {summary.get('top_risk_score', 0)}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")
    warnings = report.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        lines.append(f"- warnings: {len(warnings)}")
    errors = report.get("errors", [])
    if isinstance(errors, list) and errors:
        lines.append(f"- errors: {len(errors)}")
    hotspots = report.get("hotspots", [])
    if isinstance(hotspots, list) and hotspots:
        lines.append("- top_hotspots:")
        for row in hotspots[:5]:
            if not isinstance(row, dict):
                continue
            lines.append(
                "  - "
                f"{row.get('path')}: score={row.get('score')} "
                f"count={row.get('count')} guards={row.get('guard_count')}"
            )
    return lines
