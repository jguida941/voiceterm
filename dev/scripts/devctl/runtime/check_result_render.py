"""Shared renderers for the CheckResult / ViolationRecord contract family.

Separates the text/markdown/JSON projection of ``CheckResult`` from the
core data-model module so both files stay under the ``code_shape`` soft
limit while preserving the "one shared renderer family" that MP-381
consumers (checks, probes, governance-review, startup summaries,
dashboards) rely on.

Each exported renderer is the single entry point for its output mode:

- ``render_check_result_text`` — compact terminal body (supports
  violations-only results for adapter-backed consumers such as the
  ``startup-context`` blocker projection).
- ``render_check_result_md`` — markdown step table plus optional
  ``## Violation Detail`` and ``## Failure Output`` sections; the step
  table is omitted entirely when the result carries violations but no
  executed steps.
- ``render_check_result_json`` — canonical JSON projection through
  ``CheckResult.to_dict`` so ``text / md / json`` stay schema-aligned.
"""

from __future__ import annotations

import json as _json_mod

from .check_result_models import CheckResult, ViolationRecord, _step_status


def render_check_result_text(result: CheckResult) -> str:
    """Compact terminal-friendly summary.

    When ``result.steps`` is empty but ``result.violations`` carries at
    least one record, the renderer emits a violations-only section so
    adapter-backed consumers (startup summaries, standalone probe hint
    lists, etc.) can route their findings through the same shared
    renderer as check-backed consumers. A fully empty result (no steps,
    no violations) still returns the historical ``"no check steps ran"``
    marker so existing callers keep their current behavior.
    """
    if not result.steps:
        return _render_violations_only_text(result)
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


def _render_violations_only_text(result: CheckResult) -> str:
    """Render a violations-only text body for a step-less CheckResult.

    Used by the ``render_check_result_text`` fast path when a consumer
    (e.g. the startup-context summary adapter) projects domain findings
    directly into a ``CheckResult`` envelope without a check-step run.
    Keeps the historical empty-result marker when there are also no
    violations so pre-existing callers remain byte-identical.
    """
    if not result.violations:
        return "no check steps ran"
    header = f"violation summary: {len(result.violations)} blocker(s)"
    lines = ["", header, "-" * len(header)]
    for violation in result.violations:
        summary = violation.summary or f"exit {violation.exit_code}"
        lines.append(f"  FAIL  {violation.step_name}  -- {summary}")
        _append_violation_detail_text(lines, violation)
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
    """Markdown table of step results with failure-output appendix.

    When ``result.steps`` is empty, the step table header is omitted so
    violations-only consumers (startup summaries, adapter-backed
    finding lists) render as a clean ``## Violation Detail`` section
    without a hollow step-table preamble. Step-backed callers are
    unaffected.
    """
    from ..common import cmd_str

    lines: list[str] = []
    if result.steps:
        lines.extend([
            "| Step | Status | Duration (s) | Command |",
            "|------|--------|--------------|---------|",
        ])
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
        if lines:
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

    Pass ``indent=None`` for the compact one-line form used by event
    logs and packet payloads; the default ``indent=2`` is the
    operator-readable form used by report files.
    """
    return _json_mod.dumps(result.to_dict(), indent=indent, sort_keys=True)


__all__ = [
    "render_check_result_text",
    "render_check_result_md",
    "render_check_result_json",
]
