"""Typed check-output contract for devctl check steps.

CheckResult and ViolationRecord replace ad hoc violation_summary strings
with a typed contract that renders to text, Markdown, or JSON through one
shared renderer.  Finding stays as governance evidence; these models own
the *check output* shape.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

CHECK_RESULT_CONTRACT_ID = "CheckResult"
CHECK_RESULT_SCHEMA_VERSION = 1

_VIOLATION_SUMMARY_MAX_LEN = 120


# -------------------------------------------------------
# Core data models
# -------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ViolationRecord:
    """One violation extracted from a failed check step."""

    step_name: str
    exit_code: int
    summary: str
    error: str = ""
    failure_output: str = ""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "step_name": self.step_name,
            "exit_code": self.exit_code,
            "summary": self.summary,
        }
        if self.error:
            result["error"] = self.error
        if self.failure_output:
            result["failure_output"] = self.failure_output
        return result


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Typed result envelope for one devctl check run."""

    schema_version: int
    contract_id: str
    command: str
    timestamp: str
    success: bool
    total: int
    passed: int
    failed: int
    skipped: int
    steps: tuple[dict[str, Any], ...]
    violations: tuple[ViolationRecord, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["steps"] = list(self.steps)
        result["violations"] = [v.to_dict() for v in self.violations]
        return result


# -------------------------------------------------------
# Step introspection helpers
# -------------------------------------------------------


def _step_status(step: dict[str, Any]) -> str:
    """Return a human-readable status label for one check step."""
    if step.get("skipped"):
        return "SKIP"
    return "PASS" if step["returncode"] == 0 else "FAIL"


def _extract_violation_summary(step: dict[str, Any]) -> str:
    """Build a bounded one-line summary from a failed step."""
    error = str(step.get("error") or "").strip()
    if error:
        return error[:_VIOLATION_SUMMARY_MAX_LEN]
    failure_output = str(step.get("failure_output") or "").strip()
    if not failure_output:
        return f"exit {step['returncode']}"
    for line in reversed(failure_output.splitlines()):
        candidate = line.strip()
        if candidate:
            return candidate[:_VIOLATION_SUMMARY_MAX_LEN]
    return f"exit {step['returncode']}"


# -------------------------------------------------------
# Builder: steps -> CheckResult
# -------------------------------------------------------


def build_check_result(
    *,
    steps: list[dict[str, Any]],
    timestamp: str,
    command: str = "check",
) -> CheckResult:
    """Build a typed CheckResult from raw step dicts."""
    passed = sum(1 for s in steps if s["returncode"] == 0 and not s.get("skipped"))
    failed_steps = [s for s in steps if s["returncode"] != 0 and not s.get("skipped")]
    skipped = sum(1 for s in steps if s.get("skipped"))

    violations = tuple(
        ViolationRecord(
            step_name=s["name"],
            exit_code=s["returncode"],
            summary=_extract_violation_summary(s),
            error=str(s.get("error") or "").strip(),
            failure_output=str(s.get("failure_output") or "").strip(),
        )
        for s in failed_steps
    )

    enriched = tuple(_enrich_step(s) for s in steps)
    return CheckResult(
        schema_version=CHECK_RESULT_SCHEMA_VERSION,
        contract_id=CHECK_RESULT_CONTRACT_ID,
        command=command,
        timestamp=timestamp,
        success=len(failed_steps) == 0,
        total=len(steps),
        passed=passed,
        failed=len(failed_steps),
        skipped=skipped,
        steps=enriched,
        violations=violations,
    )


def _enrich_step(step: dict[str, Any]) -> dict[str, Any]:
    """Add status and violation_summary fields to a step dict."""
    entry = dict(step)
    entry["status"] = _step_status(step)
    if step["returncode"] != 0:
        entry["violation_summary"] = _extract_violation_summary(step)
    else:
        entry["violation_summary"] = ""
    return entry


# -------------------------------------------------------
# Shared renderer: text / md / json
# -------------------------------------------------------


def render_check_result_text(result: CheckResult) -> str:
    """Compact terminal-friendly summary."""
    if not result.steps:
        return "no check steps ran"
    header = f"check summary: {result.passed}/{result.total} passed"
    if result.failed:
        header += f", {result.failed} failed"
    if result.skipped:
        header += f", {result.skipped} skipped"
    lines = ["", header, "-" * len(header)]
    for step in result.steps:
        status = step.get("status", _step_status(step))
        line = f"  {status:<4}  {step['name']}"
        if status == "FAIL":
            summary = step.get("violation_summary", "")
            if summary:
                line += f"  -- {summary}"
        lines.append(line)
    lines.append("")
    return "\n".join(lines)


def render_check_result_md(result: CheckResult) -> str:
    """Markdown table of step results with failure-output appendix."""
    from ..common import cmd_str

    lines = [
        "| Step | Status | Duration (s) | Command |",
        "|------|--------|--------------|---------|",
    ]
    for step in result.steps:
        status = step.get("status", _step_status(step))
        lines.append(
            f"| {step['name']} | {status} | {step.get('duration_s', 0)} "
            f"| `{cmd_str(step.get('cmd', []))}` |"
        )

    failed_with_output = [
        step for step in result.steps
        if step.get("returncode", 0) != 0 and step.get("failure_output")
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
