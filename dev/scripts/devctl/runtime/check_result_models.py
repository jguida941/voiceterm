"""Typed check-output contract for devctl check steps.

``CheckResult`` and ``ViolationRecord`` replace ad hoc
``violation_summary`` strings with a typed contract. The shared
text / markdown / JSON renderers live next door in
``check_result_render`` so this module owns the *data model* half of
the MP-381 contract family and the sibling module owns the *projection*
half; both stay under the ``code_shape`` soft limit and
``Finding`` stays separate as governance evidence.
"""

from __future__ import annotations

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
    correlation_id: str = ""
    causation_id: str = ""
    run_id: str = ""

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
    correlation_id: str = "",
    causation_id: str = "",
    run_id: str = "",
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
        correlation_id=correlation_id,
        causation_id=causation_id,
        run_id=run_id,
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


# Shared text / markdown / JSON renderers for ``CheckResult`` live in
# ``check_result_render`` — the data-model half and the projection half
# of the MP-381 contract family stay split so both files remain under
# the ``code_shape`` soft limit and neither depends on the other at
# import time. Callers should ``from ..check_result_render import
# render_check_result_text`` (etc.) rather than re-routing through
# this module.
