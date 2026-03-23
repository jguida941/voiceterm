"""Report assembly and rendering for platform contract-closure enforcement."""

from __future__ import annotations

from dev.scripts.devctl.config import REPO_ROOT
from dev.scripts.devctl.governance.surfaces import load_surface_policy
from dev.scripts.devctl.platform.blueprint import build_platform_blueprint

from .support import evaluate_platform_contract_closure


def build_report() -> dict[str, object]:
    """Run the contract-closure checks over the current platform blueprint."""
    blueprint = build_platform_blueprint()
    surface_policy = load_surface_policy(repo_root=REPO_ROOT)
    coverage_rows, violations = evaluate_platform_contract_closure(
        blueprint,
        surface_policy,
    )
    return {
        "command": "check_platform_contract_closure",
        "ok": not violations,
        "schema_version": blueprint.schema_version,
        "checked_runtime_contracts": len(
            [row for row in coverage_rows if row.get("kind") == "runtime_contract"]
        ),
        "checked_artifact_schemas": len(
            [row for row in coverage_rows if row.get("kind") == "artifact_schema"]
        ),
        "checked_field_routes": len(
            [row for row in coverage_rows if row.get("kind") == "field_route"]
        ),
        "checked_field_route_families": len(
            [row for row in coverage_rows if row.get("kind") == "field_route_family"]
        ),
        "violations": list(violations),
        "coverage": list(coverage_rows),
    }


def render_md(report: dict[str, object]) -> str:
    lines = ["# check_platform_contract_closure", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(
        f"- checked_runtime_contracts: {report.get('checked_runtime_contracts', 0)}"
    )
    lines.append(
        f"- checked_artifact_schemas: {report.get('checked_artifact_schemas', 0)}"
    )
    lines.append(f"- checked_field_routes: {report.get('checked_field_routes', 0)}")
    lines.append(
        f"- checked_field_route_families: {report.get('checked_field_route_families', 0)}"
    )
    lines.append(f"- violations: {len(report.get('violations', []))}")
    lines.extend(("", "## Coverage", ""))
    for row in report.get("coverage", []):
        if not isinstance(row, dict):
            continue
        marker = "PASS" if row.get("ok") else "FAIL"
        lines.append(
            f"- [{marker}] {row.get('kind')}::{row.get('contract_id', row.get('surface_policy', 'surface'))}: "
            f"{row.get('detail')}"
        )
    violations = report.get("violations", [])
    if isinstance(violations, list) and violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, dict):
                continue
            lines.append(
                f"- {violation.get('kind')}::{violation.get('contract_id', 'surface')}"
                f" [{violation.get('rule')}]: {violation.get('detail')}"
            )
            missing_fields = violation.get("missing_fields")
            extra_fields = violation.get("extra_fields")
            missing_tokens = violation.get("missing_tokens")
            if missing_fields:
                lines.append(f"  missing_fields: {', '.join(missing_fields)}")
            if extra_fields:
                lines.append(f"  extra_fields: {', '.join(extra_fields)}")
            if missing_tokens:
                lines.append(f"  missing_tokens: {', '.join(missing_tokens)}")
    return "\n".join(lines)
