"""Validate tracked external publications against watched repo source paths."""

from __future__ import annotations

import argparse
import json
import sys

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.governance.branch_matching import (
    head_matches_release_branch,
)
from dev.scripts.devctl.governance.push_policy import load_push_policy
from dev.scripts.devctl.publication_sync.core import (
    DEFAULT_PUBLICATION_SYNC_REGISTRY_REL,
    build_publication_sync_report,
)

IMPACT_PREVIEW_LIMIT = 12


def _render_text(report: dict) -> str:
    lines = ["# check_publication_sync"]
    lines.append(f"- ok: {report['ok']}")
    if "blocking_ok" in report:
        lines.append(f"- blocking_ok: {report['blocking_ok']}")
    lines.append(f"- registry_path: {report['registry_path']}")
    lines.append(f"- head_ref: {report['head_ref']}")
    if report.get("release_branch_aware") is not None:
        lines.append(f"- release_branch_aware: {report['release_branch_aware']}")
    if report.get("release_branch"):
        lines.append(f"- release_branch: {report['release_branch']}")
    if "requires_release_publication_freshness" in report:
        lines.append(
            "- requires_release_publication_freshness: "
            f"{report['requires_release_publication_freshness']}"
        )
    if report.get("resolved_head_ref"):
        lines.append(f"- resolved_head_ref: {report['resolved_head_ref']}")
    if report.get("publication_filter"):
        lines.append(f"- publication_filter: {report['publication_filter']}")
    lines.append(f"- publications: {report['publication_count']}")
    lines.append(f"- stale_publications: {report['stale_publication_count']}")
    lines.append(f"- errors: {report['error_count']}")
    for message in report["errors"]:
        lines.append(f"- error: {message}")
    for item in report["publications"]:
        lines.append(
            f"- publication: {item['id']} stale={item['stale']} impacted={item['impacted_path_count']}"
        )
        for message in item["errors"]:
            lines.append(f"  - error: {message}")
        for path in item["impacted_paths"][:IMPACT_PREVIEW_LIMIT]:
            lines.append(f"  - impacted: {path}")
        remaining = len(item["impacted_paths"]) - IMPACT_PREVIEW_LIMIT
        if remaining > 0:
            lines.append(f"  - impacted: ... {remaining} more")
    return "\n".join(lines)


def _release_branch_freshness_required(head_ref: str) -> tuple[bool, str]:
    push_policy = load_push_policy()
    release_branch = push_policy.release_branch
    return head_matches_release_branch(head_ref, release_branch), release_branch


def _blocking_ok(
    report: dict,
    *,
    report_only: bool,
    release_branch_aware: bool,
    requires_release_publication_freshness: bool,
) -> bool:
    if report_only:
        return True
    if report.get("error_count", 0):
        return False
    if not release_branch_aware or requires_release_publication_freshness:
        return bool(report.get("ok"))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check tracked external publication sync state.",
    )
    parser.add_argument(
        "--publication",
        help="Optional publication id filter from the registry",
    )
    parser.add_argument(
        "--registry-path",
        default=DEFAULT_PUBLICATION_SYNC_REGISTRY_REL,
        help="Publication registry JSON path",
    )
    parser.add_argument(
        "--head-ref",
        default="HEAD",
        help="Git ref compared against recorded publication source refs",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Always exit zero after printing the report",
    )
    parser.add_argument(
        "--release-branch-aware",
        action="store_true",
        help=(
            "Only hard-block stale publication drift when HEAD resolves to the "
            "configured release branch; parse/registry errors still fail everywhere"
        ),
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    report = build_publication_sync_report(
        repo_root=REPO_ROOT,
        registry_path=args.registry_path,
        publication_id=args.publication,
        head_ref=args.head_ref,
    )
    requires_release_publication_freshness = True
    release_branch = ""
    if args.release_branch_aware:
        (
            requires_release_publication_freshness,
            release_branch,
        ) = _release_branch_freshness_required(args.head_ref)
    blocking_ok = _blocking_ok(
        report,
        report_only=args.report_only,
        release_branch_aware=args.release_branch_aware,
        requires_release_publication_freshness=(
            requires_release_publication_freshness
        ),
    )
    output_report = {
        **report,
        "blocking_ok": blocking_ok,
        "release_branch_aware": args.release_branch_aware,
    }
    if args.release_branch_aware:
        output_report["release_branch"] = release_branch
        output_report["requires_release_publication_freshness"] = (
            requires_release_publication_freshness
        )

    if args.format == "json":
        print(json.dumps(output_report, indent=2))
    else:
        print(_render_text(output_report))
    return 0 if blocking_ok else 1
