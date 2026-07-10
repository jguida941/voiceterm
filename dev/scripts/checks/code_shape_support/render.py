"""Markdown report renderer for check_code_shape."""

from __future__ import annotations


def _render_function_violation(v: dict) -> str:
    return (
        f"- `{v['path']}::{v['function_name']}` "
        f"({v['reason']}): {v['guidance']} "
        f"[policy: {v['policy_source']}]"
    )


def _render_override_cap_violation(v: dict) -> str:
    current_caps = ", ".join(v.get("current_triggered_caps", []))
    current_summary = (
        "current override "
        f"soft={v['current_override_soft']} "
        f"({v['current_soft_ratio']:.2f}x), "
        f"hard={v['current_override_hard']} "
        f"({v['current_hard_ratio']:.2f}x)"
    )
    baseline_soft_ratio = v.get("baseline_soft_ratio")
    baseline_hard_ratio = v.get("baseline_hard_ratio")
    if baseline_soft_ratio is not None and baseline_hard_ratio is not None:
        baseline_summary = (
            "; baseline "
            f"soft={v['baseline_override_soft']} "
            f"({baseline_soft_ratio:.2f}x), "
            f"hard={v['baseline_override_hard']} "
            f"({baseline_hard_ratio:.2f}x)"
        )
    else:
        baseline_summary = ""
    return (
        f"- `{v['path']}` ({v['reason']}; {current_caps}): "
        f"{v['guidance']} [{current_summary}{baseline_summary}; "
        f"policy: {v['policy_source']}]"
    )


def _render_mixed_concerns_violation(v: dict) -> str:
    cluster_summary = "; ".join(v.get("signals", []))
    return (
        f"- `{v['path']}` ({v['reason']}): "
        f"{cluster_summary}; {v['guidance']} "
        f"[policy: {v['policy_source']}]"
    )


def _render_growth_violation(v: dict) -> str:
    growth = v["growth"]
    growth_label = "n/a" if growth is None else f"{growth:+d}"
    return (
        f"- `{v['path']}` ({v['reason']}): "
        f"{v['base_lines']} -> {v['current_lines']} "
        f"(growth {growth_label}); {v['guidance']} "
        f"[policy: {v['policy_source']}]"
    )


def _render_violation(v: dict) -> str:
    if "function_name" in v:
        return _render_function_violation(v)
    family = v.get("violation_family")
    if family == "override_cap":
        return _render_override_cap_violation(v)
    if family == "mixed_concerns":
        return _render_mixed_concerns_violation(v)
    return _render_growth_violation(v)


def render_md(report: dict) -> str:
    lines = ["# check_code_shape", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(
        f"- files_using_path_overrides: {report['files_using_path_overrides']}"
    )
    lines.append(f"- function_policies_applied: {report['function_policies_applied']}")
    lines.append(f"- function_exceptions_used: {report['function_exceptions_used']}")
    lines.append(f"- function_violations: {report['function_violations']}")
    lines.append(f"- mixed_concern_violations: {report['mixed_concern_violations']}")
    lines.append(
        f"- stale_override_review_window_days: {report['stale_override_review_window_days']}"
    )
    lines.append(
        f"- stale_override_candidates_scanned: {report['stale_override_candidates_scanned']}"
    )
    lines.append(
        f"- stale_override_candidates_skipped: {report['stale_override_candidates_skipped']}"
    )
    lines.append(f"- files_skipped_non_source: {report['files_skipped_non_source']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- warnings: {len(report['warnings'])}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")

    if report["warnings"]:
        lines.append("")
        lines.append("## Warnings")
        for warning in report["warnings"]:
            caps = ", ".join(warning.get("triggered_caps", [])) or "override"
            lines.append(
                f"- `{warning['path']}` ({caps}): {warning['detail']}"
            )

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        for v in report["violations"]:
            lines.append(_render_violation(v))
    return "\n".join(lines)
