"""Build the receipt-store consumer guard report and its markdown rendering."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, utc_timestamp

from .defaults import DEFAULT_CLASSIFICATIONS
from .models import (
    COMMAND,
    CONTRACT_ID,
    DISPLAY_TEXT,
    REASON_MISSING_CLASSIFICATION,
    REASON_NO_READER,
    REASON_NO_WRITER,
    ReceiptStoreClassification,
    ReceiptStoreViolation,
)
from .paths import store_paths_for_scope


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    scope: str = "changed",
    changed_paths: Sequence[str | Path] | None = None,
    classifications: Sequence[ReceiptStoreClassification] = DEFAULT_CLASSIFICATIONS,
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
    violations: list[ReceiptStoreViolation] = []
    for store_path in store_paths:
        classification = by_path.get(store_path)
        if classification is None:
            violations.append(
                ReceiptStoreViolation(
                    store_path=store_path,
                    reason=REASON_MISSING_CLASSIFICATION,
                    detail=f"{store_path} has no receipt consumer classification",
                    remediation="Add a writer/reader classification or evidence-only disposition.",
                )
            )
            stores.append({"store_path": store_path, "classified": False})
            continue
        stores.append({"classified": True, **classification.to_dict()})
        if not classification.writer_refs:
            violations.append(
                ReceiptStoreViolation(
                    store_path=store_path,
                    reason=REASON_NO_WRITER,
                    detail=f"{store_path} has no named writer_refs",
                    remediation="Name the existing writer seam or mark the store evidence_only.",
                )
            )
        if not classification.reader_refs and classification.disposition != "evidence_only":
            violations.append(
                ReceiptStoreViolation(
                    store_path=store_path,
                    reason=REASON_NO_READER,
                    detail=f"{store_path} has no named reader_refs and no evidence_only disposition",
                    remediation="Name an active consumer or add an explicit evidence_only disposition.",
                )
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
    return "\n".join(lines)
