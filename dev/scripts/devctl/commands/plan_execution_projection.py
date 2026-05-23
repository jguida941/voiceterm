"""Render and advance the current-row execution projection from typed proof state."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from ..runtime.current_row_proof_bundle import (
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
    REQUIRED_GUARD_IDS,
    build_current_row_proof_bundle,
    render_current_row_projection,
)
from .plan_execution_projection_receipt import run_current_row_receipt
from . import plan_execution_projection_steps as step_actions


def add_parser(sub: argparse._SubParsersAction) -> None:
    render_cmd = sub.add_parser(
        "render-current-row-projection",
        help="Render the generated current-row execution projection from typed state",
    )
    render_cmd.add_argument("--row-id", default=DEFAULT_ROW_ID)
    render_cmd.add_argument("--format", choices=("md", "json"), default="md")
    render_cmd.add_argument("--output", type=Path, default=DEFAULT_PROJECTION_PATH)
    render_cmd.add_argument("--write", action="store_true", default=False)

    step_cmd = sub.add_parser(
        "current-row-proof-step",
        help="Run one required current-row guard and record typed proof output",
    )
    step_cmd.add_argument("--row-id", default=DEFAULT_ROW_ID)
    step_cmd.add_argument("--guard-id", choices=REQUIRED_GUARD_IDS, required=True)
    step_cmd.add_argument("--guard-output", type=Path, default=DEFAULT_GUARD_OUTPUT_PATHS[0])
    step_cmd.add_argument("--projection-output", type=Path, default=DEFAULT_PROJECTION_PATH)
    step_cmd.add_argument("--plan-index-path", type=Path, default=DEFAULT_PLAN_INDEX_PATH)
    step_cmd.add_argument("--snapshots-path", type=Path, default=DEFAULT_SNAPSHOTS_PATH)
    step_cmd.add_argument(
        "--ingestion-receipts-path",
        type=Path,
        default=DEFAULT_INGESTION_RECEIPTS_PATH,
    )
    step_cmd.add_argument(
        "--closure-receipts-path",
        type=Path,
        default=DEFAULT_CLOSURE_RECEIPTS_PATH,
    )
    step_cmd.add_argument("--feature-proof-dir", type=Path, default=DEFAULT_FEATURE_PROOF_DIR)
    step_cmd.add_argument("--dogfood-output", type=Path, default=DEFAULT_DOGFOOD_OUTPUT_PATHS[0])
    step_cmd.add_argument(
        "--collaboration-evidence",
        type=Path,
        default=DEFAULT_COLLABORATION_EVIDENCE_PATHS[0],
    )
    step_cmd.add_argument("--final-gate-output", type=Path, default=DEFAULT_FINAL_GATE_PATHS[0])
    step_cmd.add_argument("--format", choices=("json", "md"), default="json")

    dogfood_cmd = sub.add_parser(
        "current-row-proof-dogfood",
        help="Run current-row dogfood and record typed dogfood output",
    )
    dogfood_cmd.add_argument("--row-id", default=DEFAULT_ROW_ID)
    dogfood_cmd.add_argument("--dogfood-output", type=Path, default=DEFAULT_DOGFOOD_OUTPUT_PATHS[0])
    dogfood_cmd.add_argument("--projection-output", type=Path, default=DEFAULT_PROJECTION_PATH)
    dogfood_cmd.add_argument("--plan-index-path", type=Path, default=DEFAULT_PLAN_INDEX_PATH)
    dogfood_cmd.add_argument("--snapshots-path", type=Path, default=DEFAULT_SNAPSHOTS_PATH)
    dogfood_cmd.add_argument(
        "--ingestion-receipts-path",
        type=Path,
        default=DEFAULT_INGESTION_RECEIPTS_PATH,
    )
    dogfood_cmd.add_argument(
        "--closure-receipts-path",
        type=Path,
        default=DEFAULT_CLOSURE_RECEIPTS_PATH,
    )
    dogfood_cmd.add_argument("--feature-proof-dir", type=Path, default=DEFAULT_FEATURE_PROOF_DIR)
    dogfood_cmd.add_argument("--guard-output", type=Path, default=DEFAULT_GUARD_OUTPUT_PATHS[0])
    dogfood_cmd.add_argument(
        "--collaboration-evidence",
        type=Path,
        default=DEFAULT_COLLABORATION_EVIDENCE_PATHS[0],
    )
    dogfood_cmd.add_argument("--final-gate-output", type=Path, default=DEFAULT_FINAL_GATE_PATHS[0])
    dogfood_cmd.add_argument("--command-timeout-seconds", type=int, default=300)
    dogfood_cmd.add_argument("--route-timeout-seconds", type=int, default=900)
    dogfood_cmd.add_argument("--format", choices=("json", "md"), default="json")

    receipt_cmd = sub.add_parser(
        "current-row-proof-receipt",
        help="Write the current-row FeatureProofReceipt from typed proof evidence",
    )
    receipt_cmd.add_argument("--row-id", default=DEFAULT_ROW_ID)
    receipt_cmd.add_argument("--feature-proof-dir", type=Path, default=DEFAULT_FEATURE_PROOF_DIR)
    receipt_cmd.add_argument("--projection-output", type=Path, default=DEFAULT_PROJECTION_PATH)
    receipt_cmd.add_argument("--plan-index-path", type=Path, default=DEFAULT_PLAN_INDEX_PATH)
    receipt_cmd.add_argument("--snapshots-path", type=Path, default=DEFAULT_SNAPSHOTS_PATH)
    receipt_cmd.add_argument(
        "--ingestion-receipts-path",
        type=Path,
        default=DEFAULT_INGESTION_RECEIPTS_PATH,
    )
    receipt_cmd.add_argument(
        "--closure-receipts-path",
        type=Path,
        default=DEFAULT_CLOSURE_RECEIPTS_PATH,
    )
    receipt_cmd.add_argument("--guard-output", type=Path, default=DEFAULT_GUARD_OUTPUT_PATHS[0])
    receipt_cmd.add_argument("--dogfood-output", type=Path, default=DEFAULT_DOGFOOD_OUTPUT_PATHS[0])
    receipt_cmd.add_argument(
        "--collaboration-evidence",
        type=Path,
        default=DEFAULT_COLLABORATION_EVIDENCE_PATHS[0],
    )
    receipt_cmd.add_argument("--final-gate-output", type=Path, default=DEFAULT_FINAL_GATE_PATHS[0])
    receipt_cmd.add_argument("--test-node", action="append", default=[])
    receipt_cmd.add_argument("--evidence-artifact", action="append", default=[])
    receipt_cmd.add_argument("--dogfood-evidence-ref", default="")
    receipt_cmd.add_argument("--implementer-actor", default="codex")
    receipt_cmd.add_argument("--review-fleet-actor", default="codex")
    receipt_cmd.add_argument("--review-fleet-role", action="append", default=[])
    receipt_cmd.add_argument("--commit-sha", default="")
    receipt_cmd.add_argument("--format", choices=("json", "md"), default="json")


def run(args) -> int:
    if getattr(args, "command", "") == "current-row-proof-step":
        step_actions.subprocess = subprocess
        return step_actions.run_current_row_proof_step(args)
    if getattr(args, "command", "") == "current-row-proof-dogfood":
        step_actions.subprocess = subprocess
        return step_actions.run_current_row_dogfood(args)
    if getattr(args, "command", "") == "current-row-proof-receipt":
        return run_current_row_receipt(args)
    report = build_current_row_proof_bundle(row_id=str(args.row_id))
    if args.format == "json":
        output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    else:
        output = render_current_row_projection(report)
    if args.write:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        print(str(output_path))
        return 0
    print(output, end="" if output.endswith("\n") else "\n")
    return 0


__all__ = ["add_parser", "run"]
