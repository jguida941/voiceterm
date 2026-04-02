"""Core helpers shared by CodeRabbit workflow gate scripts."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

_LEGACY_MODULE_NAME = "dev.scripts.checks._coderabbit_gate_core_legacy"


def _load_legacy_module() -> ModuleType:
    module_path = Path(__file__).resolve().parent.parent / "coderabbit_gate_core.py"
    spec = importlib.util.spec_from_file_location(_LEGACY_MODULE_NAME, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"unable to load legacy CodeRabbit core: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_LEGACY = _load_legacy_module()

looks_like_sha = _LEGACY.looks_like_sha
parse_iso = _LEGACY.parse_iso
resolve_sha = _LEGACY.resolve_sha
resolve_branch = _LEGACY.resolve_branch
current_branch_name = _LEGACY.current_branch_name
gh_run_list = _LEGACY.gh_run_list
build_report = _LEGACY.build_report


def render_report_md(report: dict[str, Any], *, title: str) -> str:
    """Render a standard gate report in markdown format."""
    lines = [f"# {title}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- workflow: {report.get('workflow')}")
    if report.get("repo"):
        lines.append(f"- repo: {report.get('repo')}")
    lines.append(f"- branch_requested: {report.get('branch_requested') or '(none)'}")
    lines.append(f"- branch: {report.get('branch')}")
    lines.append(f"- allow_branch_fallback: {report.get('allow_branch_fallback')}")
    lines.append(f"- fallback_without_branch: {report.get('fallback_without_branch')}")
    lines.append(f"- sha: {report.get('sha')}")
    lines.append(f"- checked_runs: {report.get('checked_runs')}")
    lines.append(f"- matching_runs: {report.get('matching_runs')}")
    lines.append(f"- reason: {report.get('reason')}")
    warnings = report.get("warnings")
    if isinstance(warnings, list):
        for warning in warnings:
            lines.append(f"- warning: {warning}")
    latest = report.get("latest_match")
    if isinstance(latest, dict) and latest:
        lines.append(
            "- latest_match: "
            + ", ".join(
                [
                    f"status={latest.get('status')}",
                    f"conclusion={latest.get('conclusion')}",
                    f"url={latest.get('url')}",
                    f"created_at={latest.get('created_at')}",
                ]
            )
        )
    return "\n".join(lines)
