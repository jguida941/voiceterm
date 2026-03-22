"""Parser wiring for `devctl governance-review`."""

from __future__ import annotations

import argparse

from .common_io import add_standard_output_arguments
from .governance_review_models import (
    VALID_FINDING_CLASSES,
    VALID_PREVENTION_SURFACES,
    VALID_RECURRENCE_RISKS,
)


def add_governance_review_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `governance-review` parser."""
    review_cmd = sub.add_parser(
        "governance-review",
        help=(
            "Record and summarize adjudicated guard/probe findings so false-positive "
            "and cleanup rates can be tracked over time"
        ),
    )
    review_cmd.add_argument(
        "--record",
        action="store_true",
        help="Append one adjudicated finding row before rendering the updated summary",
    )
    review_cmd.add_argument(
        "--log-path",
        help="JSONL path for governance review rows (default: dev/reports/governance/finding_reviews.jsonl)",
    )
    review_cmd.add_argument(
        "--summary-root",
        help="Directory used for latest review summary artifacts (default: dev/reports/governance/latest)",
    )
    review_cmd.add_argument(
        "--max-rows",
        type=int,
        default=5000,
        help="Maximum JSONL rows sampled when rendering the summary",
    )
    review_cmd.add_argument("--finding-id", help="Optional stable finding id override")
    review_cmd.add_argument("--signal-type", choices=["guard", "probe", "audit"])
    review_cmd.add_argument("--check-id", help="Guard/probe id being adjudicated")
    review_cmd.add_argument(
        "--verdict",
        choices=[
            "confirmed_issue",
            "false_positive",
            "fixed",
            "waived",
            "deferred",
            "unknown",
        ],
    )
    review_cmd.add_argument("--path", help="Repo-relative file path for the finding")
    review_cmd.add_argument("--symbol", help="Optional symbol/function/class name")
    review_cmd.add_argument("--line", type=int, help="Optional 1-based line number")
    review_cmd.add_argument("--severity", choices=["low", "medium", "high", "critical"])
    review_cmd.add_argument("--risk-type", help="Optional risk type/category label")
    review_cmd.add_argument(
        "--source-command",
        help="Command or surface that produced the finding (for example probe-report)",
    )
    review_cmd.add_argument(
        "--scan-mode",
        choices=["working-tree", "commit-range", "adoption-scan", "absolute", "external"],
        help="Scan mode used when the finding was produced",
    )
    review_cmd.add_argument("--repo-name", help="Optional repo name override")
    review_cmd.add_argument("--repo-path", help="Optional repo path override")
    review_cmd.add_argument("--notes", help="Optional short adjudication note")
    review_cmd.add_argument(
        "--finding-class",
        choices=VALID_FINDING_CLASSES,
        help=(
            "Failure classification for the finding "
            "(required with --record for architectural absorption)"
        ),
    )
    review_cmd.add_argument(
        "--recurrence-risk",
        choices=VALID_RECURRENCE_RISKS,
        help=(
            "Recurrence risk classification for the finding "
            "(required with --record)"
        ),
    )
    review_cmd.add_argument(
        "--prevention-surface",
        choices=VALID_PREVENTION_SURFACES,
        help=(
            "Approved systemic prevention surface or 'none' with waiver "
            "(required with --record)"
        ),
    )
    review_cmd.add_argument(
        "--waiver-reason",
        help=(
            "Required when prevention-surface is none or the verdict is "
            "waived/deferred"
        ),
    )
    add_standard_output_arguments(
        review_cmd,
        format_choices=("json", "md"),
        default_format="md",
    )
