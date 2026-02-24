"""Rendering helpers for `devctl audit-scaffold`."""

from __future__ import annotations

import json


def summarize_guard(step: dict) -> tuple[int, int]:
    """Return violation count and path-bearing violation count for one guard step."""
    violations = step.get("violations", [])
    if not isinstance(violations, list):
        return 0, 0
    return len(violations), sum(
        1 for item in violations if isinstance(item, dict) and item.get("path")
    )


def render_summary_table(guard_steps: list[dict]) -> str:
    """Render a markdown summary table for guard step outcomes."""
    lines = [
        "| Guard | Focus | Severity | Return | Violations | Status |",
        "|---|---|---|---:|---:|---|",
    ]
    for step in guard_steps:
        violation_count, _path_count = summarize_guard(step)
        if step.get("skipped"):
            status = "dry-run"
        elif step.get("error"):
            status = "error"
        elif step["returncode"] == 0 and violation_count == 0:
            status = "clean"
        else:
            status = "needs remediation"
        lines.append(
            f"| `{step['name']}` | {step['focus']} | {step['severity']} | "
            f"{step['returncode']} | {violation_count} | {status} |"
        )
    return "\n".join(lines)


def _format_violation_line(violation: dict) -> str:
    path = violation.get("path", "<unknown>")
    reason = violation.get("reason")
    if reason:
        return f"- `{path}` ({reason})"

    growth = violation.get("growth")
    if isinstance(growth, dict):
        growth_bits = [f"{key} {value:+d}" for key, value in growth.items() if isinstance(value, int) and value > 0]
        if growth_bits:
            return f"- `{path}` ({', '.join(growth_bits)})"

    metrics = violation.get("metrics")
    if isinstance(metrics, dict):
        metric_bits = [f"{key}={value}" for key, value in metrics.items() if isinstance(value, int) and value > 0]
        if metric_bits:
            return f"- `{path}` ({', '.join(metric_bits)})"
    return f"- `{path}`"


def render_findings(guard_steps: list[dict]) -> str:
    """Render markdown findings sections for non-clean guard results."""
    lines: list[str] = []
    for step in guard_steps:
        violations = step.get("violations", [])
        if not violations and not step.get("error"):
            continue
        lines.append(f"### {step['name']}")
        lines.append(f"- Focus: {step['focus']}")
        lines.append(f"- Severity: {step['severity']}")
        lines.append(f"- Return code: {step['returncode']}")
        if step.get("error"):
            lines.append(f"- Parse/command issue: {step['error']}")
        if step.get("stderr_tail"):
            lines.append("- stderr tail:")
            lines.append("```text")
            lines.append(step["stderr_tail"])
            lines.append("```")
        if violations:
            lines.append("- Violations:")
            for item in violations[:80]:
                if isinstance(item, dict):
                    lines.append(_format_violation_line(item))
                else:
                    lines.append(f"- {item}")
            remaining = len(violations) - 80
            if remaining > 0:
                lines.append(f"- ... and {remaining} more")
        lines.append("")
    return "\n".join(lines).strip() or "_No findings captured._"


def render_action_items(guard_steps: list[dict]) -> str:
    """Render deduplicated action-item checklist from guard findings."""
    action_lines: list[str] = []
    for step in guard_steps:
        violations = step.get("violations", [])
        if not violations:
            continue
        if step["script_id"] == "code_shape":
            action_lines.append(
                "- [ ] Refactor oversized or growth-violating files listed by `code-shape-guard` into narrower modules/helpers."
            )
        elif step["script_id"] == "rust_lint_debt":
            action_lines.append(
                "- [ ] Reduce newly introduced `#[allow(...)]` and non-test `unwrap/expect` growth reported by `rust-lint-debt-guard`."
            )
        elif step["script_id"] == "rust_best_practices":
            action_lines.append(
                "- [ ] Add missing `reason=` for `#[allow(...)]`, document `unsafe` with `SAFETY:` comments, and add `# Safety` docs for public `unsafe fn` where reported."
            )
        elif step["script_id"] == "rust_audit_patterns":
            action_lines.append(
                "- [ ] Remove known audit anti-patterns (`UTF-8` unsafe slicing, byte-limit truncation misuse, single-pass redaction, deterministic suffix IDs, lossy VAD cast patterns)."
            )
        elif step["script_id"] == "rust_security_footguns":
            action_lines.append(
                "- [ ] Remove risky security footguns introduced in changed Rust files (debug/todo macros, shell `-c` spawn paths, permissive modes, weak-crypto references)."
            )
    if not action_lines:
        return "- [ ] No guard violations were detected in this run."

    deduped: list[str] = []
    for line in action_lines:
        if line not in deduped:
            deduped.append(line)
    return "\n".join(deduped)


def render_generated_doc(
    *,
    template_text: str,
    generated_at: str,
    trigger: str,
    trigger_steps: str,
    range_label: str,
    guard_steps: list[dict],
) -> str:
    """Fill template placeholders using collected guard outputs."""
    replacements = {
        "{{GENERATED_AT}}": generated_at,
        "{{TRIGGER}}": trigger,
        "{{TRIGGER_STEPS}}": trigger_steps,
        "{{RANGE}}": range_label,
        "{{SUMMARY_TABLE}}": render_summary_table(guard_steps),
        "{{FINDINGS}}": render_findings(guard_steps),
        "{{ACTION_ITEMS}}": render_action_items(guard_steps),
    }
    rendered = template_text
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    return rendered


def report_output(report: dict, fmt: str) -> str:
    """Render final command output for md/json modes."""
    if fmt == "json":
        return json.dumps(report, indent=2)

    lines = ["# devctl audit-scaffold", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- output_path: {report['output_path']}")
    lines.append(f"- findings_detected: {report['findings_detected']}")
    lines.append(f"- guards_run: {len(report['guards'])}")
    lines.append(f"- trigger: {report['trigger']}")
    lines.append(f"- trigger_steps: {report['trigger_steps']}")
    lines.append("")
    lines.append("## Guard Status")
    lines.append(render_summary_table(report["guards"]))
    if report.get("errors"):
        lines.append("")
        lines.append("## Errors")
        for error in report["errors"]:
            lines.append(f"- {error}")
    return "\n".join(lines)
