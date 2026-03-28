#!/usr/bin/env python3
"""Render helpers for the bundle-registry DRY guard."""

from __future__ import annotations


def render_markdown(report: dict) -> str:
    lines = [
        "# check_bundle_registry_dry",
        "",
        f"- ok: {report['ok']}",
        f"- max_widely_shared_commands: {report['max_widely_shared_commands']}",
        f"- bundle_count: {report['bundle_count']}",
        f"- widely_shared_count: {report['widely_shared_count']}",
        f"- composition_layers_declared: {len(report['composition_layers_declared'])}",
        f"- composition_layers_used: {', '.join(report['composition_layers_used']) or 'none'}",
        f"- uses_composition: {report['uses_composition']}",
        f"- violations: {len(report['violations'])}",
    ]
    violations = report.get("violations", [])
    if violations:
        lines.extend(["", "## Violations"])
        for violation in violations:
            lines.append(
                "- [{rule}] `{command_text}` appears in {bundle_count} bundles -> {hint}".format(
                    rule=violation["rule"],
                    command_text=violation["command_text"],
                    bundle_count=violation["bundle_count"],
                    hint=violation["hint"],
                )
            )
    return "\n".join(lines)
