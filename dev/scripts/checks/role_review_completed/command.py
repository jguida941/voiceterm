#!/usr/bin/env python3
"""Require declared review-fleet roles to carry terminal role-review refs."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

_CHECKS_DIR = Path(__file__).resolve().parents[1]
if str(_CHECKS_DIR) not in sys.path:
    sys.path.insert(0, str(_CHECKS_DIR))

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, emit_runtime_error

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_feature_proof_receipt = importlib.import_module(
    "dev.scripts.devctl.runtime.feature_proof_receipt"
)
FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT = (
    _feature_proof_receipt.FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT
)
feature_proof_receipt_from_mapping = (
    _feature_proof_receipt.feature_proof_receipt_from_mapping
)
role_review_terminal_coverage_failure_reasons = importlib.import_module(
    "dev.scripts.devctl.runtime.feature_proof_role_review"
).role_review_terminal_coverage_failure_reasons
RoleReviewCompletedRemediationFinding = importlib.import_module(
    "dev.scripts.devctl.runtime.feature_proof_output_proof"
).RoleReviewCompletedRemediationFinding
append_jsonl = importlib.import_module(
    "dev.scripts.devctl.runtime.relaunch_loop_store"
).append_jsonl

COMMAND = "check_role_review_completed"
DEFAULT_REMEDIATION_LEDGER = (
    "dev/state/role_review_completed_remediation_findings.jsonl"
)


@dataclass(frozen=True)
class RoleReviewCompletedViolation:
    path: str
    commit_sha: str
    feature_id: str
    failure_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["failure_reasons"] = list(self.failure_reasons)
        return payload


@dataclass(frozen=True)
class RoleReviewCompletedReport:
    command: str
    ok: bool
    receipt_root: str
    scan_count: int
    proven_passed_count: int
    violation_count: int
    failure_reasons: tuple[str, ...] = ()
    violations: tuple[dict[str, object], ...] = field(default_factory=tuple)
    ledgered_violation_count: int = 0
    remediation_ledger_path: str = ""
    remediation_findings_written: int = 0
    warnings: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = "CheckRoleReviewCompletedCommand"


def evaluate_role_review_completed(
    *,
    repo_root: Path = REPO_ROOT,
    receipt_root: Path | None = None,
    remediation_ledger: Path | None = None,
    allow_ledgered_findings: bool = True,
) -> RoleReviewCompletedReport:
    root = receipt_root or repo_root / FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT
    ledger = remediation_ledger or repo_root / DEFAULT_REMEDIATION_LEDGER
    ledgered_finding_ids = (
        _ledgered_finding_ids(ledger) if allow_ledgered_findings else frozenset()
    )
    warnings: list[str] = []
    violations: list[RoleReviewCompletedViolation] = []
    ledgered_violation_count = 0
    scan_count = 0
    proven_passed_count = 0
    for path in sorted(root.glob("*.json")):
        scan_count += 1
        relpath = _display_path(path, repo_root)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            receipt = feature_proof_receipt_from_mapping(payload)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            warnings.append(
                f"invalid_feature_proof_receipt:{relpath}:{exc.__class__.__name__}:{exc}"
            )
            continue
        if receipt.real_life_test_status != "proven_passed":
            continue
        proven_passed_count += 1
        failure_reasons = role_review_terminal_coverage_failure_reasons(receipt)
        if not failure_reasons:
            continue
        violation = RoleReviewCompletedViolation(
            path=relpath,
            commit_sha=receipt.commit_sha,
            feature_id=receipt.feature_id,
            failure_reasons=failure_reasons,
        )
        if _remediation_finding(violation.to_dict()).finding_id in ledgered_finding_ids:
            ledgered_violation_count += 1
            continue
        violations.append(violation)
    failure_reasons = tuple(
        sorted(
            {
                reason
                for violation in violations
                for reason in violation.failure_reasons
            }
        )
    )
    return RoleReviewCompletedReport(
        command=COMMAND,
        ok=not violations,
        receipt_root=_display_path(root, repo_root),
        scan_count=scan_count,
        proven_passed_count=proven_passed_count,
        violation_count=len(violations),
        failure_reasons=failure_reasons,
        violations=tuple(violation.to_dict() for violation in violations),
        ledgered_violation_count=ledgered_violation_count,
        remediation_ledger_path=(
            _display_path(ledger, repo_root)
            if allow_ledgered_findings and ledger.exists()
            else ""
        ),
        warnings=tuple(warnings),
    )


def write_remediation_ledger(
    report: RoleReviewCompletedReport,
    *,
    repo_root: Path = REPO_ROOT,
    ledger_path: Path | None = None,
) -> RoleReviewCompletedReport:
    ledger = ledger_path or repo_root / DEFAULT_REMEDIATION_LEDGER
    written = 0
    for violation in report.violations:
        finding = _remediation_finding(violation)
        append_jsonl(ledger, finding.to_dict())
        written += 1
    return RoleReviewCompletedReport(
        command=report.command,
        ok=report.ok,
        receipt_root=report.receipt_root,
        scan_count=report.scan_count,
        proven_passed_count=report.proven_passed_count,
        violation_count=report.violation_count,
        failure_reasons=report.failure_reasons,
        violations=report.violations,
        ledgered_violation_count=report.ledgered_violation_count,
        remediation_ledger_path=_display_path(ledger, repo_root),
        remediation_findings_written=written,
        warnings=report.warnings,
    )


def _remediation_finding(
    violation: dict[str, object],
) -> RoleReviewCompletedRemediationFinding:
    path = str(violation.get("path") or "")
    commit_sha = str(violation.get("commit_sha") or "")
    feature_id = str(violation.get("feature_id") or "")
    failure_reasons = tuple(str(item) for item in violation.get("failure_reasons") or ())
    finding_key = "\n".join((path, commit_sha, feature_id, *failure_reasons))
    digest = hashlib.sha256(finding_key.encode("utf-8")).hexdigest()[:16]
    return RoleReviewCompletedRemediationFinding(
        finding_id=f"role-review-{digest}",
        feature_proof_receipt_path=path,
        commit_sha=commit_sha,
        feature_id=feature_id,
        failure_reasons=failure_reasons,
        evidence_refs=(path,),
        emitted_at_utc=_utc_now(),
    )


def _ledgered_finding_ids(path: Path) -> frozenset[str]:
    finding_ids: set[str] = set()
    try:
        handle = path.open(encoding="utf-8")
    except OSError:
        return frozenset()
    with handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                finding_id = str(payload.get("finding_id") or "").strip()
                if finding_id:
                    finding_ids.add(finding_id)
    return frozenset(finding_ids)


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _render_md(report: RoleReviewCompletedReport) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- receipt_root: `{report.receipt_root}`")
    lines.append(f"- scan_count: {report.scan_count}")
    lines.append(f"- proven_passed_count: {report.proven_passed_count}")
    lines.append(f"- violation_count: {report.violation_count}")
    lines.append(f"- ledgered_violation_count: {report.ledgered_violation_count}")
    if report.remediation_ledger_path:
        lines.append(f"- remediation_ledger_path: `{report.remediation_ledger_path}`")
        lines.append(
            f"- remediation_findings_written: {report.remediation_findings_written}"
        )
    if report.failure_reasons:
        lines.append("")
        lines.append("## Failure Reasons")
        for reason in report.failure_reasons:
            lines.append(f"- {reason}")
    if report.violations:
        lines.append("")
        lines.append("## Violations")
        for violation in report.violations:
            reasons = ",".join(
                str(item) for item in violation.get("failure_reasons", ())
            )
            lines.append(
                "- "
                f"{violation.get('commit_sha')} "
                f"path={violation.get('path')} "
                f"reasons={reasons}"
            )
    if report.warnings:
        lines.append("")
        lines.append("## Warnings")
        for warning in report.warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=COMMAND, description=__doc__)
    parser.add_argument("--receipt-root", default="")
    parser.add_argument(
        "--write-remediation-ledger",
        action="store_true",
        help="Append unledgered violations to the role-review remediation ledger.",
    )
    parser.add_argument("--remediation-ledger", default=DEFAULT_REMEDIATION_LEDGER)
    parser.add_argument(
        "--strict-no-ledger-baseline",
        action="store_true",
        help="Fail on all findings, including findings already present in the remediation ledger.",
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        receipt_root = Path(args.receipt_root) if args.receipt_root else None
        if receipt_root is not None and not receipt_root.is_absolute():
            receipt_root = REPO_ROOT / receipt_root
        ledger_path = Path(args.remediation_ledger)
        if not ledger_path.is_absolute():
            ledger_path = REPO_ROOT / ledger_path
        report = evaluate_role_review_completed(
            receipt_root=receipt_root,
            remediation_ledger=ledger_path,
            allow_ledgered_findings=not args.strict_no_ledger_baseline,
        )
        if args.write_remediation_ledger:
            report = write_remediation_ledger(report, ledger_path=ledger_path)
    # broad-except: allow reason=top-level guard CLI safety fallback=emit_runtime_error
    except Exception as exc:
        return emit_runtime_error(
            COMMAND,
            args.format,
            f"{exc.__class__.__name__}: {exc}",
        )
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2))
    else:
        print(_render_md(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
