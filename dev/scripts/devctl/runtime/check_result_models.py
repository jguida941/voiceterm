"""Typed check-output contract for devctl check steps.

CheckResult and ViolationRecord replace ad hoc violation_summary strings
with a typed contract that renders to text, Markdown, or JSON through one
shared renderer.  Finding stays as governance evidence; these models own
the *check output* shape.
"""

from __future__ import annotations

import json as _json_mod
import re as _re_mod
from dataclasses import asdict, dataclass, field
from typing import Any

_re_compile = _re_mod.compile

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
    file_path: str = ""
    line: int = 0
    policy: str = ""
    fix: str = ""
    source: str = ""
    severity: str = ""

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
        if self.file_path:
            result["file_path"] = self.file_path
        if self.line:
            result["line"] = self.line
        if self.policy:
            result["policy"] = self.policy
        if self.fix:
            result["fix"] = self.fix
        if self.source:
            result["source"] = self.source
        if self.severity:
            result["severity"] = self.severity
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


_VIOLATION_DETAIL_RE = _re_compile(
    r"((?:dev|rust|app|src)/\S+\.(?:py|rs|md)):(\d+)"
)


def _extract_violation_detail(step: dict[str, Any]) -> dict[str, str | int]:
    """Extract file_path, line, policy, fix, source, and severity from step data.

    Checks for explicit structured fields first (``violation_detail`` dict),
    then falls back to regex extraction from failure_output text.
    """
    detail = step.get("violation_detail") or {}
    if detail:
        return {
            "file_path": str(detail.get("file_path") or ""),
            "line": int(detail.get("line") or 0),
            "policy": str(detail.get("policy") or ""),
            "fix": str(detail.get("fix") or ""),
            "source": str(detail.get("source") or step.get("name", "")),
            "severity": str(detail.get("severity") or ""),
        }
    output = str(step.get("failure_output") or "")
    m = _VIOLATION_DETAIL_RE.search(output)
    file_path = m.group(1) if m else ""
    line = int(m.group(2)) if m else 0
    return {
        "file_path": file_path,
        "line": line,
        "policy": "",
        "fix": "",
        "source": step.get("name", ""),
        "severity": "",
    }


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

    violations = tuple(_build_violation(s) for s in failed_steps)

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


def _build_violation(step: dict[str, Any]) -> ViolationRecord:
    """Build a ViolationRecord from one failed step dict."""
    detail = _extract_violation_detail(step)
    return ViolationRecord(
        step_name=step["name"],
        exit_code=step["returncode"],
        summary=_extract_violation_summary(step),
        error=str(step.get("error") or "").strip(),
        failure_output=str(step.get("failure_output") or "").strip(),
        file_path=str(detail.get("file_path") or ""),
        line=int(detail.get("line") or 0),
        policy=str(detail.get("policy") or ""),
        fix=str(detail.get("fix") or ""),
        source=str(detail.get("source") or ""),
        severity=str(detail.get("severity") or ""),
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
    violation_by_step = {v.step_name: v for v in result.violations}
    for step in result.steps:
        status = step.get("status", _step_status(step))
        line = f"  {status:<4}  {step['name']}"
        if status == "FAIL":
            summary = step.get("violation_summary", "")
            if summary:
                line += f"  -- {summary}"
        lines.append(line)
        if status == "FAIL":
            _append_violation_detail_text(lines, violation_by_step.get(step["name"]))
    lines.append("")
    return "\n".join(lines)


def _append_violation_detail_text(
    lines: list[str], violation: ViolationRecord | None,
) -> None:
    """Append file/line/policy/fix detail lines for a violation if present."""
    if violation is None:
        return
    parts: list[str] = []
    if violation.file_path:
        loc = violation.file_path
        if violation.line:
            loc += f":{violation.line}"
        parts.append(f"file={loc}")
    if violation.policy:
        parts.append(f"policy={violation.policy}")
    if violation.severity:
        parts.append(f"severity={violation.severity}")
    if violation.fix:
        parts.append(f"fix={violation.fix}")
    if parts:
        lines.append(f"          {' | '.join(parts)}")


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

    violations_with_detail = [
        v for v in result.violations if v.file_path or v.policy
    ]
    if violations_with_detail:
        lines.append("")
        lines.append("## Violation Detail")
        lines.append("")
        lines.append("| Step | File | Line | Policy | Severity | Fix |")
        lines.append("|------|------|------|--------|----------|-----|")
        for v in violations_with_detail:
            lines.append(
                f"| {v.step_name} | {v.file_path} | {v.line or ''} "
                f"| {v.policy} | {v.severity} | {v.fix} |"
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


def render_check_result_json(
    result: CheckResult,
    *,
    indent: int | None = 2,
) -> str:
    """Serialize a CheckResult into the canonical JSON projection.

    Symmetric companion to ``render_check_result_text`` and
    ``render_check_result_md`` so every consumer of the shared
    ``CheckResult`` / ``ViolationRecord`` family has one obvious entry
    point per output mode (text / md / json) instead of mixing
    ``render_*`` calls with ad hoc ``json.dumps(result.to_dict())``.

    The serialization passes through ``CheckResult.to_dict`` so the
    schema (schema_version / contract_id / per-step shape / nested
    ViolationRecord projection) stays driven by the dataclass contract.
    Pass ``indent=None`` for the compact one-line form used by event
    logs and packet payloads; the default ``indent=2`` is the
    operator-readable form used by report files.
    """
    return _json_mod.dumps(result.to_dict(), indent=indent, sort_keys=True)
