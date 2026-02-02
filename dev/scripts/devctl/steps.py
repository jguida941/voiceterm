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
    return "\n".join(lines)
