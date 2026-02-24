"""Rendering helpers for `devctl mutation-loop` outputs."""

from __future__ import annotations

from typing import Any


def render_attempt_lines(attempts: list[dict[str, Any]]) -> list[str]:
    if not attempts:
        return ["- none"]
    lines: list[str] = []
    for row in attempts:
        lines.append(
            "- "
            + f"#{row.get('attempt')} "
            + f"run_id={row.get('run_id')} "
            + f"sha={row.get('run_sha')} "
            + f"score={row.get('score')} "
            + f"status={row.get('status')}"
        )
        if row.get("run_url"):
            lines.append(f"  url: {row.get('run_url')}")
        if row.get("message"):
            lines.append(f"  note: {row.get('message')}")
    return lines


def render_playbook(report: dict) -> str:
    hotspots = report.get("last_hotspots", [])
    lines = [
        "# mutation-loop-playbook",
        "",
        f"- branch: {report.get('branch')}",
        f"- threshold: {report.get('threshold')}",
        f"- last_score: {report.get('last_score', 'n/a')}",
        f"- reason: {report.get('reason')}",
        "",
        "## Hotspots",
        "",
    ]
    if not isinstance(hotspots, list) or not hotspots:
        lines.append("- none")
    else:
        for row in hotspots[:20]:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- "
                + f"path={row.get('path')} "
                + f"survivors={row.get('survivors')}"
            )
    lines.extend(
        [
            "",
            "## Suggested Remediations",
            "",
            "1. Add targeted tests around top survivor hotspots first.",
            "2. Re-run mutation workflow and verify score trend improves.",
            "3. Promote to fix mode only when policy gates are explicitly enabled.",
        ]
    )
    return "\n".join(lines)


def render_markdown(report: dict) -> str:
    lines = ["# devctl mutation-loop", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- mode: {report.get('mode')}")
    lines.append(f"- notify: {report.get('notify')}")
    lines.append(f"- repo: {report.get('repo')}")
    lines.append(f"- branch: {report.get('branch')}")
    lines.append(f"- workflow: {report.get('workflow')}")
    lines.append(f"- threshold: {report.get('threshold')}")
    lines.append(f"- max_attempts: {report.get('max_attempts')}")
    lines.append(f"- completed_attempts: {report.get('completed_attempts')}")
    lines.append(f"- last_score: {report.get('last_score', 'n/a')}")
    lines.append(f"- reason: {report.get('reason')}")
    notify_result = report.get("notify_result")
    if isinstance(notify_result, dict):
        lines.append(f"- notify_result_ok: {notify_result.get('ok')}")
        lines.append(
            "- notify_target: "
            + f"{notify_result.get('target_kind') or 'n/a'}:{notify_result.get('target_id') or 'n/a'}"
        )
        if notify_result.get("comment_url"):
            lines.append(f"- notify_comment_url: {notify_result.get('comment_url')}")
        if notify_result.get("error"):
            lines.append(f"- notify_error: {notify_result.get('error')}")
    lines.append("")
    lines.append("## Attempts")
    lines.append("")
    lines.extend(render_attempt_lines(report.get("attempts", [])))
    warnings = report.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        lines.append("")
        lines.append("## Warnings")
        lines.append("")
        lines.extend(f"- {warning}" for warning in warnings)
    bundle = report.get("bundle", {})
    if isinstance(bundle, dict) and bundle:
        lines.append("")
        lines.append("## Bundle")
        lines.append("")
        for key in ("markdown", "json", "playbook"):
            value = bundle.get(key)
            if value:
                lines.append(f"- {key}: {value}")
    return "\n".join(lines)
