"""CLI entrypoint for the ingestion-churn guard."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

_REPO_ROOT_FOR_PATH = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT_FOR_PATH) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_FOR_PATH))

try:
    from check_bootstrap import emit_runtime_error
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import emit_runtime_error

from .models import (
    COMMAND,
    DEFAULT_CLOSURE_RECEIPTS_PATH,
    DEFAULT_FEATURE_PROOF_DIR,
    DEFAULT_LIFECYCLE_RECEIPTS_PATH,
    DEFAULT_MAX_SNAPSHOTS,
    DEFAULT_PLAN_INDEX_PATH,
    DEFAULT_ROW_ID,
    DEFAULT_SNAPSHOTS_PATH,
    DEFAULT_WINDOW_HOURS,
)
from .report import build_report, render_markdown


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail when the same plan source is repeatedly ingested without row advancement."
    )
    parser.add_argument("--snapshots-path", type=Path, default=DEFAULT_SNAPSHOTS_PATH)
    parser.add_argument("--plan-index-path", type=Path, default=DEFAULT_PLAN_INDEX_PATH)
    parser.add_argument(
        "--closure-receipts-path",
        type=Path,
        default=DEFAULT_CLOSURE_RECEIPTS_PATH,
    )
    parser.add_argument(
        "--lifecycle-receipts-path",
        type=Path,
        default=DEFAULT_LIFECYCLE_RECEIPTS_PATH,
    )
    parser.add_argument("--feature-proof-dir", type=Path, default=DEFAULT_FEATURE_PROOF_DIR)
    parser.add_argument("--row-id", default=DEFAULT_ROW_ID)
    parser.add_argument(
        "--all-rows",
        action="store_true",
        help="Audit every row instead of enforcing only the active/current row.",
    )
    parser.add_argument("--window-hours", type=int, default=DEFAULT_WINDOW_HOURS)
    parser.add_argument("--max-snapshots", type=int, default=DEFAULT_MAX_SNAPSHOTS)
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            snapshots_path=args.snapshots_path,
            plan_index_path=args.plan_index_path,
            closure_receipts_path=args.closure_receipts_path,
            lifecycle_receipts_path=args.lifecycle_receipts_path,
            feature_proof_dir=args.feature_proof_dir,
            row_id=args.row_id,
            all_rows=args.all_rows,
            window_hours=args.window_hours,
            max_snapshots=args.max_snapshots,
        )
    except Exception as exc:  # pragma: no cover - defensive guard wrapper
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
