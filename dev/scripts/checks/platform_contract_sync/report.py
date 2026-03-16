"""Report assembly and rendering for platform-contract sync enforcement."""

from __future__ import annotations

from dev.scripts.devctl.platform.blueprint import build_platform_blueprint

from .support import evaluate_platform_contract_sync


def build_report() -> dict[str, object]:
    """Run the contract-sync checks over the current platform blueprint."""
    blueprint = build_platform_blueprint()
    coverage_rows, violations = evaluate_platform_contract_sync(blueprint)
    return {
        "command": "check_platform_contract_sync",
        "ok": not violations,
        "schema_version": blueprint.schema_version,
        "checked_contracts": len(coverage_rows),
        "violations": list(violations),
        "coverage": list(coverage_rows),
    }


def render_md(report: dict[str, object]) -> str:
    lines = ["# check_platform_contract_sync", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- checked_contracts: {report.get('checked_contracts', 0)}")
    lines.append(f"- violations: {len(report.get('violations', []))}")
    lines.extend(("", "## Coverage", ""))
    for row in report.get("coverage", []):
        if not isinstance(row, dict):
            continue
        marker = "PASS" if row.get("ok") else "FAIL"
        lines.append(
            f"- [{marker}] {row.get('contract_id')} ↔ {row.get('surface')}: {row.get('detail')}"
        )
    violations = report.get("violations", [])
    if isinstance(violations, list) and violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, dict):
                continue
            missing = ", ".join(violation.get("missing_fields", ())) or "none"
            extra = ", ".join(violation.get("extra_fields", ())) or "none"
            lines.append(
                f"- `{violation.get('contract_id')}` ({violation.get('surface')}): "
                f"{violation.get('detail')} missing={missing}; extra={extra}"
            )
    return "\n".join(lines)
