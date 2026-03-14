"""Markdown rendering helpers for docs-check output."""

from .docs.render_sections import (
    append_deprecated_references,
    append_evolution_gate,
    append_failure_sections,
    append_header,
    append_strict_tooling_sections,
    append_tooling_summary,
)


def render_markdown_report(report: dict) -> str:
    """Render docs-check report payload in markdown format."""
    lines = ["# devctl docs-check", ""]
    append_header(lines, report)
    append_tooling_summary(lines, report)
    append_evolution_gate(lines, report)
    append_strict_tooling_sections(lines, report)
    append_deprecated_references(lines, report)
    append_failure_sections(lines, report)
    lines.append(f"- ok: {report.get('ok')}")
    return "\n".join(lines)
