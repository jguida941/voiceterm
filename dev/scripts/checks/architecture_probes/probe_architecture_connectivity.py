"""Probe architecture connectivity against the typed registry snapshot."""

from __future__ import annotations

from pathlib import Path
import sys

try:
    from probe_bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.probe_support.bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )

try:
    from dev.scripts.devctl.config import REPO_ROOT
    from dev.scripts.devctl.platform.connectivity_reader_verification import (
        find_missing_connection_findings,
    )
    from dev.scripts.devctl.platform.connectivity_registry import (
        CONNECTIVITY_REGISTRY_READER_IDS,
        CONNECTIVITY_REGISTRY_ROW_READER_IDS,
        build_connectivity_registry_snapshot,
    )
    from dev.scripts.devctl.platform.connectivity_registry_models import (
        ConnectivityRegistrySnapshot,
        MissingConnectionFinding,
    )
except ModuleNotFoundError:  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    from dev.scripts.devctl.config import REPO_ROOT
    from dev.scripts.devctl.platform.connectivity_reader_verification import (
        find_missing_connection_findings,
    )
    from dev.scripts.devctl.platform.connectivity_registry import (
        CONNECTIVITY_REGISTRY_READER_IDS,
        CONNECTIVITY_REGISTRY_ROW_READER_IDS,
        build_connectivity_registry_snapshot,
    )
    from dev.scripts.devctl.platform.connectivity_registry_models import (
        ConnectivityRegistrySnapshot,
        MissingConnectionFinding,
    )

COMMAND = "probe_architecture_connectivity"
ARCHITECTURE_DOCS = [
    "dev/scripts/devctl/platform/connectivity_registry.py",
    "dev/scripts/devctl/platform/connectivity_registry_models.py",
    "dev/scripts/devctl/platform/connectivity_reader_verification.py",
]


def _severity_for_classification(classification: str) -> str:
    if classification == "mistakenly_declared":
        return "high"
    if classification == "aspirational_gap":
        return "medium"
    return "low"


def _finding_file(finding: MissingConnectionFinding) -> str:
    for location in finding.suggested_wire_locations:
        text = str(location).strip()
        if text:
            return text
    return "dev/scripts/devctl/platform/connectivity_registry.py"


def build_architecture_hints(
    *,
    registry: ConnectivityRegistrySnapshot,
    findings: tuple[MissingConnectionFinding, ...],
) -> list[RiskHint]:
    """Convert registry-level missing connections into probe hints."""
    hints: list[RiskHint] = []
    for finding in findings:
        signals = [
            f"contract={finding.contract_id}",
            f"declared_reader={finding.declared_reader_surface}",
            f"classification={finding.classification}",
            f"expected_evidence={finding.expected_evidence_kind}",
        ]
        if finding.justification:
            signals.append(f"justification={finding.justification}")
        if finding.override_ref:
            signals.append(f"override_ref={finding.override_ref}")
        hints.append(
            RiskHint(
                file=_finding_file(finding),
                symbol=f"{finding.contract_id}:{finding.declared_reader_surface}",
                risk_type="architecture_connectivity_gap",
                severity=_severity_for_classification(finding.classification),
                signals=signals,
                ai_instruction=(
                    "Validate the declared reader against "
                    "ConnectivityRegistrySnapshot before changing projection "
                    "or renderer behavior; do not let a surface invent a "
                    "shape that the typed contract registry does not prove."
                ),
                review_lens="architecture",
                attach_docs=ARCHITECTURE_DOCS,
            )
        )
    if registry.warnings:
        hints.append(
            RiskHint(
                file="dev/scripts/devctl/platform/connectivity_registry.py",
                symbol=registry.contract_id,
                risk_type="architecture_registry_warning",
                severity="medium",
                signals=list(registry.warnings),
                ai_instruction=(
                    "Resolve registry warnings before treating generated "
                    "system-map or probe-report projections as architectural "
                    "authority."
                ),
                review_lens="architecture",
                attach_docs=ARCHITECTURE_DOCS,
            )
        )
    return hints


def build_report(*, since_ref: str | None, head_ref: str) -> ProbeReport:
    registry = build_connectivity_registry_snapshot(repo_root=REPO_ROOT)
    findings = tuple(
        find_missing_connection_findings(
            registry=registry,
            required_reader_ids=CONNECTIVITY_REGISTRY_READER_IDS,
            row_reader_ids=CONNECTIVITY_REGISTRY_ROW_READER_IDS,
            repo_root=REPO_ROOT,
        )
    )
    hints = build_architecture_hints(registry=registry, findings=findings)
    files_with_hints = {hint.file for hint in hints}
    return ProbeReport(
        command=COMMAND,
        risk_hints=hints,
        files_scanned=registry.source_contract_count,
        files_with_hints=len(files_with_hints),
        since_ref=since_ref,
        head_ref=head_ref,
    )


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = build_report(since_ref=args.since_ref, head_ref=args.head_ref)
    return emit_probe_report(report, output_format=args.format)


if __name__ == "__main__":
    raise SystemExit(main())
