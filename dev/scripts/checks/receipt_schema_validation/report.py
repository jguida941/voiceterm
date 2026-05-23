"""Report assembly + markdown rendering for the schema validation guard."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, utc_timestamp

from .git_status import git_commit_exists
from .models import (
    COMMAND,
    CONTRACT_ID,
    DEFAULT_FEATURE_PROOF_DIR,
    DISPLAY_TEXT,
    ReceiptSchemaViolation,
)
from .paths import feature_proof_paths_for_scope, repo_relative
from .validation import validate_feature_proof_receipt


def build_report(
    *,
    feature_proof_dir: Path = DEFAULT_FEATURE_PROOF_DIR,
    repo_root: Path = REPO_ROOT,
    scope: str = "all",
    changed_paths: Sequence[str | Path] | None = None,
    commit_exists: Callable[[str], bool] | None = None,
) -> dict[str, object]:
    warnings: list[str] = []
    violations: list[ReceiptSchemaViolation] = []
    receipt_paths = feature_proof_paths_for_scope(
        feature_proof_dir=feature_proof_dir,
        repo_root=repo_root,
        scope=scope,
        changed_paths=changed_paths,
        warnings=warnings,
    )
    resolver = commit_exists or (lambda sha: git_commit_exists(repo_root, sha))

    for path in receipt_paths:
        violations.extend(
            validate_feature_proof_receipt(
                path=path,
                repo_root=repo_root,
                feature_proof_dir=feature_proof_dir,
                commit_exists=resolver,
            )
        )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "feature_proof_dir": str(repo_relative(feature_proof_dir, repo_root)),
        "scope": scope,
        "feature_proof_receipt_count": len(receipt_paths),
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "warnings": warnings,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- feature_proof_dir: `{report.get('feature_proof_dir')}`")
    lines.append(f"- scope: {report.get('scope')}")
    lines.append(f"- feature_proof_receipt_count: {report.get('feature_proof_receipt_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)) and violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                f"- {violation.get('path')}: {violation.get('reason')} "
                f"({violation.get('detail')})"
            )
    warnings = report.get("warnings")
    if isinstance(warnings, Sequence) and not isinstance(warnings, (str, bytes)) and warnings:
        lines.extend(("", "## Warnings", ""))
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)
