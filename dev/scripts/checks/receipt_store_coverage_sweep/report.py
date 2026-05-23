"""Report assembly + markdown rendering for the coverage-sweep guard."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, utc_timestamp

from .coverage import violations_for_classification
from .extras import DEFAULT_CLASSIFICATIONS
from .models import (
    COMMAND,
    CONTRACT_ID,
    DISPLAY_TEXT,
    REASON_MISSING_CLASSIFICATION,
    ReceiptStoreCoverage,
    ReceiptStoreCoverageViolation,
)
from .sweep_paths import store_paths_for_scope


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    scope: str = "changed",
    changed_paths: Sequence[str | Path] | None = None,
    classifications: Sequence[ReceiptStoreCoverage] = DEFAULT_CLASSIFICATIONS,
) -> dict[str, object]:
    warnings: list[str] = []
    store_paths = store_paths_for_scope(
        repo_root=repo_root,
        scope=scope,
        changed_paths=changed_paths,
        warnings=warnings,
    )
    by_path = {classification.store_path: classification for classification in classifications}
    stores: list[dict[str, object]] = []
    violations: list[ReceiptStoreCoverageViolation] = []

    for store_path in store_paths:
        classification = by_path.get(store_path)
        if classification is None:
            violations.append(
                ReceiptStoreCoverageViolation(
                    store_path=store_path,
                    reason=REASON_MISSING_CLASSIFICATION,
                    detail=f"{store_path} has no receipt-store coverage classification",
                    remediation=(
                        "Classify writer, reader, schema guard, and provenance/archive "
                        "disposition before this store can become durable authority."
                    ),
                )
            )
            stores.append({"store_path": store_path, "classified": False})
            continue
        stores.append({"classified": True, **classification.to_dict()})
        violations.extend(
            violations_for_classification(classification, repo_root=repo_root)
        )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "scope": scope,
        "store_count": len(stores),
        "stores": stores,
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "warnings": warnings,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- scope: {report.get('scope')}")
    lines.append(f"- store_count: {report.get('store_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)) and violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                f"- {violation.get('store_path')}: {violation.get('reason')} "
                f"({violation.get('detail')})"
            )
    warnings = report.get("warnings")
    if isinstance(warnings, Sequence) and not isinstance(warnings, (str, bytes)) and warnings:
        lines.extend(("", "## Warnings", ""))
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)
