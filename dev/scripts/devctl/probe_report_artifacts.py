"""Artifact writers for aggregated review-probe reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from dev.scripts.checks.probe_report.contracts import (
        REVIEW_TARGETS_CONTRACT_ID,
        REVIEW_TARGETS_SCHEMA_VERSION,
    )
except ModuleNotFoundError:  # pragma: no cover
    from checks.probe_report.contracts import (
        REVIEW_TARGETS_CONTRACT_ID,
        REVIEW_TARGETS_SCHEMA_VERSION,
    )

from .probe_topology import (
    render_hotspot_dot,
    render_hotspot_mermaid,
    render_review_packet_markdown,
)


def write_probe_artifacts(
    *,
    output_root: Path,
    report: dict[str, Any],
    summary_markdown: str,
    rich_report_markdown: str,
) -> dict[str, str]:
    output_root.mkdir(parents=True, exist_ok=True)
    latest_dir = output_root / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)

    summary_json = latest_dir / "summary.json"
    summary_md = latest_dir / "summary.md"
    review_targets_json = output_root / "review_targets.json"
    topology_json = latest_dir / "file_topology.json"
    review_packet_json = latest_dir / "review_packet.json"
    review_packet_md = latest_dir / "review_packet.md"
    hotspots_mermaid = latest_dir / "hotspots.mmd"
    hotspots_dot = latest_dir / "hotspots.dot"

    summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary_md.write_text(summary_markdown, encoding="utf-8")
    topology_json.write_text(json.dumps(report["topology"], indent=2), encoding="utf-8")
    review_packet_json.write_text(
        json.dumps(report["review_packet"], indent=2),
        encoding="utf-8",
    )
    review_packet_md.write_text(
        render_review_packet_markdown(
            report["review_packet"],
            rich_report_markdown=rich_report_markdown,
        ),
        encoding="utf-8",
    )
    hotspots_mermaid.write_text(
        render_hotspot_mermaid(report["review_packet"]),
        encoding="utf-8",
    )
    hotspots_dot.write_text(
        render_hotspot_dot(report["review_packet"]),
        encoding="utf-8",
    )

    review_targets_payload: dict[str, Any] = {}
    review_targets_payload["schema_version"] = REVIEW_TARGETS_SCHEMA_VERSION
    review_targets_payload["contract_id"] = REVIEW_TARGETS_CONTRACT_ID
    review_targets_payload["command"] = report["command"]
    review_targets_payload["generated_at"] = report["generated_at"]
    review_targets_payload["mode"] = report["mode"]
    review_targets_payload["since_ref"] = report["since_ref"]
    review_targets_payload["head_ref"] = report["head_ref"]
    review_targets_payload["summary"] = report["summary"]
    review_targets_payload["findings"] = report.get("findings", [])
    review_targets_payload["risk_hints"] = report["risk_hints"]
    review_targets_payload["review_packet"] = report["review_packet"]
    review_targets_json.write_text(
        json.dumps(review_targets_payload, indent=2),
        encoding="utf-8",
    )

    paths: dict[str, str] = {}
    paths["summary_json"] = str(summary_json)
    paths["summary_md"] = str(summary_md)
    paths["review_targets_json"] = str(review_targets_json)
    paths["topology_json"] = str(topology_json)
    paths["review_packet_json"] = str(review_packet_json)
    paths["review_packet_md"] = str(review_packet_md)
    paths["hotspots_mermaid"] = str(hotspots_mermaid)
    paths["hotspots_dot"] = str(hotspots_dot)
    return paths
