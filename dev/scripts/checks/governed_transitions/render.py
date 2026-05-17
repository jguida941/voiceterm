"""Markdown rendering for the governed transition verifier."""

from __future__ import annotations

from .models import GovernedTransitionReport


def render_md(report: GovernedTransitionReport) -> str:
    status = "OK" if report.ok else "FAIL"
    lines = [
        "# check_governed_transitions",
        "",
        f"Status: {status}",
        f"Transitions: {report.transition_count}",
        f"Path checks: {report.checked_path_count}",
        f"Failures: {report.failure_count}",
        "",
        "## Manifest Modules",
        "",
    ]
    if report.manifest_modules:
        lines.extend(f"- `{module}`" for module in report.manifest_modules)
    else:
        lines.append("- none")
    lines.extend(["", "## Edge Kinds", ""])
    if report.edge_kind_counts:
        lines.extend(
            f"- `{edge_kind}`: {count}"
            for edge_kind, count in report.edge_kind_counts.items()
        )
    else:
        lines.append("- none")

    failing = tuple(check for check in report.path_checks if not check.ok)
    if failing:
        lines.extend(["", "## Failures", ""])
        lines.append("| transition | check | from | to | reason |")
        lines.append("|---|---|---|---|---|")
        for check in failing:
            lines.append(
                "| "
                f"`{check.transition_id}` | `{check.check_kind}` | "
                f"`{check.from_ref}` | `{check.to_ref}` | {check.reason} |"
            )
    else:
        lines.extend(["", "All governed transition paths are graph-walkable."])
    return "\n".join(lines)
