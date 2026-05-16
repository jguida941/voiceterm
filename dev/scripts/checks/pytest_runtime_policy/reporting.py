"""Report building and markdown rendering for pytest runtime policy."""

from __future__ import annotations

from . import bundle_scan, config_policy


def build_report() -> dict[str, object]:
    violations = [*bundle_scan.bundle_violations(), *config_policy.config_violations()]
    return {
        "command": "check_pytest_runtime_policy",
        "ok": not violations,
        "violations": violations,
        "bundle_count": len(bundle_scan.bundle_registry()),
        "pytest_config": "pytest.ini",
    }


def render_md(report: dict[str, object]) -> str:
    lines = [
        "# check_pytest_runtime_policy",
        "",
        f"- ok: {report['ok']}",
        f"- bundle_count: {report['bundle_count']}",
        f"- pytest_config: {report['pytest_config']}",
    ]
    violations = report["violations"]
    if isinstance(violations, list) and violations:
        lines.extend(["", "## Violations"])
        for item in violations:
            lines.append(f"- {item}")
    return "\n".join(lines)
