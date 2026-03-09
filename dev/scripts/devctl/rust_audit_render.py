"""Markdown and chart rendering helpers for Rust audit summaries."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any


def build_rust_audit_charts(
    audit: dict[str, Any],
    chart_dir: Path,
) -> tuple[list[str], str | None]:
    """Render static audit charts when matplotlib is available."""
    if not os.environ.get("MPLCONFIGDIR"):
        mpl_config_dir = Path(tempfile.gettempdir()) / "voiceterm-mpl"
        mpl_config_dir.mkdir(parents=True, exist_ok=True)
        os.environ["MPLCONFIGDIR"] = str(mpl_config_dir)
    if not os.environ.get("XDG_CACHE_HOME"):
        cache_dir = Path(tempfile.gettempdir()) / "voiceterm-cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ["XDG_CACHE_HOME"] = str(cache_dir)
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as exc:  # pragma: no cover - broad-except: allow reason=optional chart rendering must degrade when matplotlib is unavailable
        return [], f"matplotlib unavailable: {exc}"

    chart_dir.mkdir(parents=True, exist_ok=True)
    chart_paths: list[str] = []

    categories = audit.get("categories")
    if isinstance(categories, list) and categories:
        top_categories = categories[:8]
        labels = [str(row["label"]) for row in top_categories]
        counts = [int(row["count"]) for row in top_categories]
        colors = [
            "#dc2626" if str(row["severity"]) == "high" else "#ea580c"
            for row in top_categories
        ]
        category_chart = chart_dir / "rust_audit_categories.png"
        figure = plt.figure(figsize=(10, 5.5))
        axis = figure.add_subplot(111)
        axis.barh(labels, counts, color=colors)
        axis.set_title("Rust Audit Findings by Category")
        axis.set_xlabel("Findings")
        axis.invert_yaxis()
        figure.tight_layout()
        figure.savefig(category_chart, dpi=150)
        plt.close(figure)
        chart_paths.append(str(category_chart))

    hotspots = audit.get("hotspots")
    if isinstance(hotspots, list) and hotspots:
        top_hotspots = hotspots[:8]
        labels = [str(row["path"]) for row in top_hotspots]
        scores = [int(row["score"]) for row in top_hotspots]
        hotspot_chart = chart_dir / "rust_audit_hotspots.png"
        figure = plt.figure(figsize=(11, 5.5))
        axis = figure.add_subplot(111)
        axis.barh(labels, scores, color="#2563eb")
        axis.set_title("Rust Audit Hotspots (Weighted Risk Score)")
        axis.set_xlabel("Weighted score")
        axis.invert_yaxis()
        figure.tight_layout()
        figure.savefig(hotspot_chart, dpi=150)
        plt.close(figure)
        chart_paths.append(str(hotspot_chart))

    guards = audit.get("guards")
    if isinstance(guards, list) and guards:
        labels = [str(row["guard"]) for row in guards]
        values = [int(row["violations"]) for row in guards]
        guard_chart = chart_dir / "rust_audit_guard_violations.png"
        figure = plt.figure(figsize=(8, 4.5))
        axis = figure.add_subplot(111)
        axis.bar(labels, values, color=["#7c3aed", "#0f766e", "#b91c1c"])
        axis.set_title("Rust Audit Violation Files by Guard")
        axis.set_ylabel("Violation files")
        figure.tight_layout()
        figure.savefig(guard_chart, dpi=150)
        plt.close(figure)
        chart_paths.append(str(guard_chart))

    return chart_paths, None


def render_rust_audit_markdown(audit: dict[str, Any]) -> list[str]:
    """Render a human-readable markdown section for Rust audit output."""
    lines = ["## Rust Audit", ""]
    summary = audit.get("summary") if isinstance(audit.get("summary"), dict) else {}
    lines.append(f"- Audit mode: {audit.get('mode')}")
    lines.append(f"- Audit clean: {audit.get('ok')}")
    lines.append(
        f"- Violation files: {summary.get('total_violation_files', 0)}"
    )
    lines.append(
        f"- Active findings: {summary.get('total_active_findings', 0)}"
    )
    lines.append(f"- Active categories: {summary.get('active_categories', 0)}")
    dead_code_without_reason = summary.get("dead_code_without_reason_count")
    if dead_code_without_reason is not None:
        lines.append(
            f"- Dead-code allows without reason: {dead_code_without_reason}"
        )

    guards = audit.get("guards")
    if isinstance(guards, list) and guards:
        lines.extend(["", "### Guard Status", "", "| Guard | Clean | Files | Violations |", "|---|---|---:|---:|"])
        for row in guards:
            lines.append(
                f"| `{row['guard']}` | {row['ok']} | {row['files_considered']} | {row['violations']} |"
            )

    categories = audit.get("categories")
    if isinstance(categories, list) and categories:
        lines.extend(
            [
                "",
                "### Why These Findings Matter",
                "",
                "| Signal | Count | Severity | Why it matters | Recommended fix |",
                "|---|---:|---|---|---|",
            ]
        )
        for row in categories[:12]:
            lines.append(
                f"| `{row['label']}` | {row['count']} | {row['severity']} | {row['why']} | {row['fix']} |"
            )

    hotspots = audit.get("hotspots")
    if isinstance(hotspots, list) and hotspots:
        lines.extend(
            [
                "",
                "### Top Hotspots",
                "",
                "| File | Weighted score | Findings | Signals |",
                "|---|---:|---:|---|",
            ]
        )
        for row in hotspots[:10]:
            lines.append(
                f"| `{row['path']}` | {row['score']} | {row['count']} | {', '.join(row['signals'][:4])} |"
            )

    charts = audit.get("charts")
    if isinstance(charts, list) and charts:
        lines.extend(["", "### Charts"])
        for chart in charts:
            lines.append(f"- `{chart}`")

    warnings = audit.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.extend(["", "### Rust Audit Warnings"])
        for warning in warnings:
            lines.append(f"- {warning}")

    errors = audit.get("errors")
    if isinstance(errors, list) and errors:
        lines.extend(["", "### Rust Audit Errors"])
        for error in errors:
            lines.append(f"- {error}")

    return lines
