"""Formatting helpers for devctl step reports."""

from typing import List

from .common import cmd_str

_VIOLATION_SUMMARY_MAX_LEN = 120


def _step_status(step: dict) -> str:
    """Return a human-readable status label for one check step."""
    if step.get("skipped"):
        return "SKIP"
    return "PASS" if step["returncode"] == 0 else "FAIL"


def _violation_summary(step: dict) -> str:
    """Extract a one-line violation summary from a failed step."""
    if step["returncode"] == 0:
        return ""
    error = str(step.get("error") or "").strip()
    if error:
        return error[:_VIOLATION_SUMMARY_MAX_LEN]
    failure_output = str(step.get("failure_output") or "").strip()
    if not failure_output:
        return f"exit {step['returncode']}"
    # Pick the last non-empty line as the most actionable summary
    last_line = ""
    for line in reversed(failure_output.splitlines()):
        candidate = line.strip()
        if candidate:
            last_line = candidate
            break
    return last_line[:_VIOLATION_SUMMARY_MAX_LEN] if last_line else f"exit {step['returncode']}"


def format_steps_md(steps: List[dict]) -> str:
    """Return a Markdown table of step results."""
    lines = [
        "| Step | Status | Duration (s) | Command |",
        "|------|--------|--------------|---------|",
    ]
    for step in steps:
        status = _step_status(step)
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


def format_steps_text(steps: List[dict]) -> str:
    """Return a compact terminal-friendly summary with check names and status."""
    if not steps:
        return "no check steps ran"
    passed = sum(1 for s in steps if s["returncode"] == 0 and not s.get("skipped"))
    failed = sum(1 for s in steps if s["returncode"] != 0 and not s.get("skipped"))
    skipped = sum(1 for s in steps if s.get("skipped"))
    total = len(steps)
    header = f"check summary: {passed}/{total} passed"
    if failed:
        header += f", {failed} failed"
    if skipped:
        header += f", {skipped} skipped"
    lines = ["", header, "-" * len(header)]
    for step in steps:
        status = _step_status(step)
        line = f"  {status:<4}  {step['name']}"
        if status == "FAIL":
            summary = _violation_summary(step)
            if summary:
                line += f"  -- {summary}"
        lines.append(line)
    lines.append("")
    return "\n".join(lines)


def enrich_steps_for_json(steps: List[dict]) -> List[dict]:
    """Add status and violation_summary fields to step dicts for JSON output."""
    enriched = []
    for step in steps:
        entry = dict(step)
        entry["status"] = _step_status(step)
        entry["violation_summary"] = _violation_summary(step) if step["returncode"] != 0 else ""
        enriched.append(entry)
    return enriched
