"""Formatting helpers for devctl step reports."""

from typing import List

from .common import cmd_str


def format_steps_md(steps: List[dict]) -> str:
    """Return a Markdown table of step results."""
    lines = [
        "| Step | Status | Duration (s) | Command |",
        "|------|--------|--------------|---------|",
    ]
    for step in steps:
        status = "OK" if step["returncode"] == 0 else "FAIL"
        if step.get("skipped"):
            status = "SKIP"
        lines.append(
            f"| {step['name']} | {status} | {step['duration_s']} | `{cmd_str(step['cmd'])}` |"
        )

    failed_with_output = [
        step for step in steps if step["returncode"] != 0 and step.get("failure_output")
    ]
    if failed_with_output:
        lines.append("")
        lines.append("## Failure Output")
        lines.append("")
        for step in failed_with_output:
            lines.append(f"### `{step['name']}`")
            lines.append("```text")
            lines.append(step["failure_output"])
            lines.append("```")
            lines.append("")
    return "\n".join(lines)
