#!/usr/bin/env python3
"""Fail until the current PlanRow has a complete typed proof bundle."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, emit_runtime_error

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.runtime.current_row_proof_bundle import (  # noqa: E402
    DEFAULT_CLOSURE_RECEIPTS_PATH,
    DEFAULT_COLLABORATION_EVIDENCE_PATHS,
    DEFAULT_DOGFOOD_OUTPUT_PATHS,
    DEFAULT_FEATURE_PROOF_DIR,
    DEFAULT_FINAL_GATE_PATHS,
    DEFAULT_GUARD_OUTPUT_PATHS,
    DEFAULT_INGESTION_RECEIPTS_PATH,
    DEFAULT_PLAN_INDEX_PATH,
    DEFAULT_PROJECTION_PATH,
    DEFAULT_ROW_ID,
    DEFAULT_SNAPSHOTS_PATH,
    build_current_row_proof_bundle,
    render_current_row_projection,
    validate_projection_sync,
)


COMMAND = "check_current_row_proof_bundle"


def build_report(
    *,
    row_id: str = DEFAULT_ROW_ID,
    plan_index_path: Path = DEFAULT_PLAN_INDEX_PATH,
    snapshots_path: Path = DEFAULT_SNAPSHOTS_PATH,
    ingestion_receipts_path: Path = DEFAULT_INGESTION_RECEIPTS_PATH,
    closure_receipts_path: Path = DEFAULT_CLOSURE_RECEIPTS_PATH,
    feature_proof_dir: Path = DEFAULT_FEATURE_PROOF_DIR,
    guard_output_paths: Sequence[Path] = DEFAULT_GUARD_OUTPUT_PATHS,
    dogfood_output_paths: Sequence[Path] = DEFAULT_DOGFOOD_OUTPUT_PATHS,
    collaboration_evidence_paths: Sequence[Path] = DEFAULT_COLLABORATION_EVIDENCE_PATHS,
    final_gate_paths: Sequence[Path] = DEFAULT_FINAL_GATE_PATHS,
    projection_path: Path = DEFAULT_PROJECTION_PATH,
    enforce_projection_sync: bool = False,
) -> dict[str, object]:
    report = build_current_row_proof_bundle(
        row_id=row_id,
        plan_index_path=plan_index_path,
        snapshots_path=snapshots_path,
        ingestion_receipts_path=ingestion_receipts_path,
        closure_receipts_path=closure_receipts_path,
        feature_proof_dir=feature_proof_dir,
        guard_output_paths=guard_output_paths,
        dogfood_output_paths=dogfood_output_paths,
        collaboration_evidence_paths=collaboration_evidence_paths,
        final_gate_paths=final_gate_paths,
    )
    if enforce_projection_sync:
        projection = validate_projection_sync(report, projection_path=projection_path)
        report["projection_sync"] = projection
        projection_failures = projection.get("failures")
        if isinstance(projection_failures, list) and projection_failures:
            failures = list(report.get("failures") or [])
            failures.extend(projection_failures)
            report["failures"] = failures
            report["failure_count"] = len(failures)
            report["ok"] = False
            report["status"] = "blocked"
    return report


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        f"# {COMMAND}",
        "",
        f"- ok: {report.get('ok')}",
        f"- row_id: `{report.get('row_id')}`",
        f"- status: `{report.get('status')}`",
        f"- source_snapshot_id: `{report.get('source_snapshot_id')}`",
        f"- ingestion_receipt_id: `{report.get('ingestion_receipt_id')}`",
        f"- next_bounded_command: `{report.get('next_bounded_command')}`",
        f"- failure_count: {report.get('failure_count')}",
    ]
    failures = report.get("failures")
    if isinstance(failures, Sequence) and not isinstance(failures, (str, bytes)):
        lines.extend(["", "## Failures", ""])
        for failure in failures:
            if isinstance(failure, Mapping):
                lines.append(
                    f"- `{failure.get('reason')}`: {failure.get('detail')} "
                    f"Remediation: {failure.get('remediation')}"
                )
    projection_sync = report.get("projection_sync")
    if isinstance(projection_sync, Mapping):
        lines.extend(
            [
                "",
                "## Projection Sync",
                "",
                f"- projection_path: `{projection_sync.get('projection_path')}`",
                f"- projection_in_sync: {projection_sync.get('projection_in_sync')}",
            ]
        )
    lines.extend(["", "## Projection Preview", "", render_current_row_projection(report)])
    return "\n".join(lines)


def _path_list(values: Sequence[str] | None, defaults: Sequence[Path]) -> tuple[Path, ...]:
    if not values:
        return tuple(defaults)
    return tuple(Path(value) for value in values)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--row-id", default=DEFAULT_ROW_ID)
    parser.add_argument("--plan-index-path", type=Path, default=DEFAULT_PLAN_INDEX_PATH)
    parser.add_argument("--snapshots-path", type=Path, default=DEFAULT_SNAPSHOTS_PATH)
    parser.add_argument(
        "--ingestion-receipts-path",
        type=Path,
        default=DEFAULT_INGESTION_RECEIPTS_PATH,
    )
    parser.add_argument(
        "--closure-receipts-path",
        type=Path,
        default=DEFAULT_CLOSURE_RECEIPTS_PATH,
    )
    parser.add_argument("--feature-proof-dir", type=Path, default=DEFAULT_FEATURE_PROOF_DIR)
    parser.add_argument("--guard-output-path", action="append", default=None)
    parser.add_argument("--dogfood-output-path", action="append", default=None)
    parser.add_argument("--collaboration-evidence-path", action="append", default=None)
    parser.add_argument("--final-gate-path", action="append", default=None)
    parser.add_argument("--projection-path", type=Path, default=DEFAULT_PROJECTION_PATH)
    parser.add_argument("--enforce-projection-sync", action="store_true", default=False)
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            row_id=args.row_id,
            plan_index_path=args.plan_index_path,
            snapshots_path=args.snapshots_path,
            ingestion_receipts_path=args.ingestion_receipts_path,
            closure_receipts_path=args.closure_receipts_path,
            feature_proof_dir=args.feature_proof_dir,
            guard_output_paths=_path_list(args.guard_output_path, DEFAULT_GUARD_OUTPUT_PATHS),
            dogfood_output_paths=_path_list(args.dogfood_output_path, DEFAULT_DOGFOOD_OUTPUT_PATHS),
            collaboration_evidence_paths=_path_list(
                args.collaboration_evidence_path,
                DEFAULT_COLLABORATION_EVIDENCE_PATHS,
            ),
            final_gate_paths=_path_list(args.final_gate_path, DEFAULT_FINAL_GATE_PATHS),
            projection_path=args.projection_path,
            enforce_projection_sync=args.enforce_projection_sync,
        )
    except Exception as exc:  # pragma: no cover - defensive guard wrapper
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
