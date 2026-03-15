"""Shared builders and renderers for aggregated review-probe reports."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from dev.scripts.checks.probe_report_render import (
        aggregate_probe_results,
        render_rich_report,
        render_terminal_report,
    )
except ModuleNotFoundError:  # pragma: no cover
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "checks"))
    probe_report_render = importlib.import_module("probe_report_render")
    aggregate_probe_results = probe_report_render.aggregate_probe_results
    render_rich_report = probe_report_render.render_rich_report
    render_terminal_report = probe_report_render.render_terminal_report

from .common import resolve_repo_python_command
from .config import REPO_ROOT, get_repo_root
from .probe_report_artifacts import write_probe_artifacts
from .probe_topology import (
    build_probe_topology_artifact,
    build_review_packet,
)
from .quality_policy import resolve_quality_policy
from .quality_policy_loader import QUALITY_POLICY_ENV_VAR
from .quality_scan_mode import is_adoption_scan
from .repo_packs.voiceterm import VOICETERM_PATH_CONFIG
from .script_catalog import probe_script_cmd
from .time_utils import utc_timestamp

# Backward-compat alias sourced from repo-pack config
DEFAULT_PROBE_REPORT_OUTPUT_ROOT = VOICETERM_PATH_CONFIG.probe_report_output_root_rel


def resolve_probe_report_path(raw_path: str | Path | None) -> Path:
    """Resolve a probe-report output root relative to the repo."""
    raw = raw_path or DEFAULT_PROBE_REPORT_OUTPUT_ROOT
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return get_repo_root() / path


def _build_summary(
    probe_results: list[dict[str, Any]],
    enriched_hints: list[dict[str, Any]],
) -> dict[str, Any]:
    aggregate = aggregate_probe_results(probe_results)
    review_lens_counts = Counter()
    probe_hint_counts = Counter()
    top_files: list[dict[str, Any]] = []

    for hint in enriched_hints:
        review_lens_counts[str(hint.get("review_lens") or "unknown")] += 1
        probe_hint_counts[str(hint.get("probe") or "unknown")] += 1

    for file_path, hints in sorted(
        aggregate.hints_by_file.items(),
        key=lambda item: (-len(item[1]), item[0]),
    )[:10]:
        top_files.append({"file": file_path, "hint_count": len(hints)})

    summary: dict[str, Any] = {}
    summary["probe_count"] = len(probe_results)
    summary["files_scanned"] = aggregate.total_files_scanned
    summary["files_with_hints"] = len(aggregate.hints_by_file)
    summary["risk_hints"] = aggregate.total_hints
    summary["hints_by_severity"] = aggregate.hints_by_severity
    summary["hints_by_review_lens"] = dict(review_lens_counts)
    summary["hints_by_probe"] = dict(probe_hint_counts)
    summary["top_files"] = top_files
    return summary


def _augment_summary_with_topology(
    *,
    summary: dict[str, Any],
    topology: dict[str, Any],
) -> None:
    hotspots = topology.get("hotspots", [])
    if isinstance(hotspots, list):
        summary["priority_hotspots"] = hotspots
    topology_summary = topology.get("summary", {})
    if isinstance(topology_summary, dict):
        summary["topology"] = topology_summary


def decode_probe_report(
    probe_id: str,
    *,
    result: subprocess.CompletedProcess[str],
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate one probe subprocess result and decode its JSON payload."""
    if result.returncode != 0:
        failure_output = (result.stderr or result.stdout or "").strip()
        detail = f" ({failure_output})" if failure_output else ""
        return None, f"{probe_id} exited {result.returncode}{detail}"

    payload = result.stdout.strip()
    if not payload:
        return None, f"{probe_id} emitted no JSON output"

    try:
        report = json.loads(payload)
    except json.JSONDecodeError as exc:
        return None, f"{probe_id} emitted invalid JSON: {exc}"
    if not isinstance(report, dict):
        report_type = type(report).__name__
        return None, f"{probe_id} emitted {report_type}, expected object"
    return report, None


def enrich_probe_hints(probe_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten probe-local risk hints into the aggregated report shape."""
    risk_hints: list[dict[str, Any]] = []
    for report in probe_results:
        probe_name = str(report.get("command") or "unknown")
        report_hints = report.get("risk_hints")
        if not isinstance(report_hints, list):
            continue
        for raw_hint in report_hints:
            if not isinstance(raw_hint, dict):
                continue
            hint = dict(raw_hint)
            hint["probe"] = probe_name
            risk_hints.append(hint)
    return risk_hints


def build_probe_report(
    *,
    since_ref: str | None,
    head_ref: str = "HEAD",
    emit_artifacts: bool = True,
    output_root: str | Path | None = None,
    policy_path: str | Path | None = None,
    probe_ids: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Run registered probes and return one aggregated report payload."""
    effective_root = get_repo_root()
    quality_policy = resolve_quality_policy(
        repo_root=effective_root,
        policy_path=policy_path,
    )
    warnings = list(quality_policy.warnings)
    active_probe_ids = probe_ids or tuple(spec.script_id for spec in quality_policy.review_probe_checks)
    probe_results: list[dict[str, Any]] = []
    errors: list[str] = []
    for probe_id in active_probe_ids:
        cmd = probe_script_cmd(probe_id, "--format", "json")
        if since_ref:
            cmd.extend(["--since-ref", since_ref, "--head-ref", head_ref])
        env = os.environ.copy()
        env["DEVCTL_REPO_ROOT"] = str(effective_root)
        if policy_path:
            env[QUALITY_POLICY_ENV_VAR] = str(Path(policy_path).expanduser())
        try:
            result = subprocess.run(
                resolve_repo_python_command(cmd, cwd=REPO_ROOT),
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
                check=False,
            )
        except OSError as exc:
            errors.append(f"{probe_id} failed to start: {exc}")
            continue

        report, error = decode_probe_report(probe_id, result=result)
        if error:
            errors.append(error)
            continue
        if report is not None:
            probe_results.append(report)

    risk_hints = enrich_probe_hints(probe_results)
    summary = _build_summary(probe_results, risk_hints)
    topology = build_probe_topology_artifact(
        risk_hints=risk_hints,
        since_ref=since_ref,
        head_ref=head_ref,
    )
    _augment_summary_with_topology(summary=summary, topology=topology)
    warnings.extend(topology.get("warnings", []))
    review_packet = build_review_packet(
        summary=summary,
        topology=topology,
        errors=errors,
        warnings=warnings,
    )

    report: dict[str, Any] = {}
    report["command"] = "probe-report"
    report["generated_at"] = utc_timestamp()
    report["ok"] = not errors
    report["mode"] = (
        "adoption-scan"
        if is_adoption_scan(since_ref=since_ref, head_ref=head_ref)
        else ("commit-range" if since_ref else "working-tree")
    )
    report["since_ref"] = None if report["mode"] == "adoption-scan" else since_ref
    report["head_ref"] = None if report["mode"] == "adoption-scan" else head_ref
    report["repo_policy"] = {
        "repo_name": quality_policy.repo_name,
        "policy_path": str(quality_policy.policy_path),
        "capabilities": {
            "python": quality_policy.capabilities.python,
            "rust": quality_policy.capabilities.rust,
        },
        "quality_scopes": {
            "python_guard_roots": [path.as_posix() for path in quality_policy.scopes.python_guard_roots],
            "python_probe_roots": [path.as_posix() for path in quality_policy.scopes.python_probe_roots],
            "rust_guard_roots": [path.as_posix() for path in quality_policy.scopes.rust_guard_roots],
            "rust_probe_roots": [path.as_posix() for path in quality_policy.scopes.rust_probe_roots],
        },
        "probe_count": len(quality_policy.review_probe_checks),
    }
    report["summary"] = summary
    report["risk_hints"] = risk_hints
    report["topology"] = topology
    report["review_packet"] = review_packet
    report["probe_results"] = probe_results
    report["warnings"] = warnings
    report["errors"] = errors
    report["artifact_paths"] = {}

    if emit_artifacts:
        report["artifact_paths"] = write_probe_artifacts(
            output_root=resolve_probe_report_path(output_root),
            report=report,
            summary_markdown=render_probe_report_markdown(report),
            rich_report_markdown=render_rich_report(report["probe_results"]),
        )

    return report


def render_probe_report_markdown(report: dict[str, Any]) -> str:
    """Render the aggregated probe report in markdown."""
    lines = [render_rich_report(report["probe_results"])]
    packet = report.get("review_packet", {})
    hotspots = packet.get("hotspots", []) if isinstance(packet, dict) else []
    if isinstance(hotspots, list) and hotspots:
        lines.extend(["", "## Senior Review Packet", ""])
        for hotspot in hotspots[:3]:
            if not isinstance(hotspot, dict):
                continue
            lines.append(
                f"- {hotspot.get('file')}: score={hotspot.get('priority_score')}, "
                f"hints={hotspot.get('hint_count')}, "
                f"fan_in={hotspot.get('fan_in')}, fan_out={hotspot.get('fan_out')}"
            )
            lines.append(f"  next: {hotspot.get('bounded_next_slice')}")
    lines.extend(["", "## Command Metadata", ""])
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- probes_run: {report['summary']['probe_count']}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("artifact_paths"):
        lines.append(f"- review_targets_json: {report['artifact_paths']['review_targets_json']}")
        lines.append(f"- summary_json: {report['artifact_paths']['summary_json']}")
        lines.append(f"- summary_md: {report['artifact_paths']['summary_md']}")
        lines.append(f"- topology_json: {report['artifact_paths']['topology_json']}")
        lines.append(f"- review_packet_json: {report['artifact_paths']['review_packet_json']}")
        lines.append(f"- review_packet_md: {report['artifact_paths']['review_packet_md']}")
        lines.append(f"- hotspots_mermaid: {report['artifact_paths']['hotspots_mermaid']}")
        lines.append(f"- hotspots_dot: {report['artifact_paths']['hotspots_dot']}")
    if report["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report["warnings"])
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
    return "\n".join(lines)


def render_probe_report_terminal(report: dict[str, Any]) -> str:
    """Render the aggregated probe report in compact terminal form."""
    lines = [render_terminal_report(report["probe_results"])]
    packet = report.get("review_packet", {})
    first_hotspot = None
    if isinstance(packet, dict):
        hotspots = packet.get("hotspots", [])
        if isinstance(hotspots, list):
            first_hotspot = next(
                (row for row in hotspots if isinstance(row, dict)),
                None,
            )
    if first_hotspot is not None:
        lines.extend(
            [
                "",
                "Top hotspot:",
                (
                    f"- {first_hotspot.get('file')} "
                    f"(score={first_hotspot.get('priority_score')}, "
                    f"hints={first_hotspot.get('hint_count')}, "
                    f"fan_in={first_hotspot.get('fan_in')}, "
                    f"fan_out={first_hotspot.get('fan_out')})"
                ),
            ]
        )
    if report["warnings"]:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {warning}" for warning in report["warnings"])
    if report["errors"]:
        lines.extend(["", "Errors:"])
        lines.extend(f"- {error}" for error in report["errors"])
    return "\n".join(lines)
