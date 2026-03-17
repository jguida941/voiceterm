"""Formatting helpers for aggregated probe-report command output."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _append_hotspot_markdown(
    *,
    lines: list[str],
    review_packet: dict[str, Any],
) -> None:
    hotspots = review_packet.get("hotspots", []) if isinstance(review_packet, dict) else []
    if not isinstance(hotspots, list) or not hotspots:
        return
    lines.extend(["", "## Decision Packet", ""])
    for hotspot in hotspots[:3]:
        if not isinstance(hotspot, dict):
            continue
        lines.append(
            f"- {hotspot.get('file')}: score={hotspot.get('priority_score')}, "
            f"hints={hotspot.get('hint_count')}, "
            f"fan_in={hotspot.get('fan_in')}, fan_out={hotspot.get('fan_out')}"
        )
        lines.append(f"  next: {hotspot.get('bounded_next_slice')}")


def _append_decision_packet_markdown(
    *,
    lines: list[str],
    decision_packets: list[dict[str, Any]],
) -> None:
    if not isinstance(decision_packets, list) or not decision_packets:
        return
    lines.extend(["", "## Design Decision Packets", ""])
    for decision in decision_packets[:3]:
        if not isinstance(decision, dict):
            continue
        lines.append(
            f"- [{decision.get('decision_mode')}] "
            f"{decision.get('file')}::{decision.get('symbol')} "
            f"({decision.get('severity')})"
        )
        lines.append(f"  why: {decision.get('rationale')}")


def _append_command_metadata(lines: list[str], report: dict[str, Any]) -> None:
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


def _first_mapping(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((row for row in rows if isinstance(row, dict)), None)


def render_probe_report_markdown(
    report: dict[str, Any],
    *,
    repo_root: Path,
    render_rich_report: Any,
) -> str:
    """Render the aggregated probe report in markdown."""
    lines = [render_rich_report(report["probe_results"], repo_root=repo_root)]
    _append_hotspot_markdown(lines=lines, review_packet=report.get("review_packet", {}))
    _append_decision_packet_markdown(
        lines=lines,
        decision_packets=report.get("decision_packets", []),
    )
    _append_command_metadata(lines, report)
    return "\n".join(lines)


def render_probe_report_terminal(
    report: dict[str, Any],
    *,
    repo_root: Path,
    render_terminal_report: Any,
) -> str:
    """Render the aggregated probe report in compact terminal form."""
    lines = [render_terminal_report(report["probe_results"], repo_root=repo_root)]
    packet = report.get("review_packet", {})
    hotspots = packet.get("hotspots", []) if isinstance(packet, dict) else []
    first_hotspot = _first_mapping(hotspots) if isinstance(hotspots, list) else None
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
    decision_packets = report.get("decision_packets", [])
    first_decision = _first_mapping(decision_packets) if isinstance(decision_packets, list) else None
    if first_decision is not None:
        lines.extend(
            [
                "",
                "Top decision packet:",
                (
                    f"- [{first_decision.get('decision_mode')}] "
                    f"{first_decision.get('file')}::{first_decision.get('symbol')}"
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
