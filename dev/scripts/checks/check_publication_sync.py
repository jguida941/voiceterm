"""Validate tracked external publications against watched repo source paths."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.publication_sync import (  # noqa: E402
    DEFAULT_PUBLICATION_SYNC_REGISTRY_REL,
    build_publication_sync_report,
)

IMPACT_PREVIEW_LIMIT = 12


def _render_text(report: dict) -> str:
    lines = ["# check_publication_sync"]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- registry_path: {report['registry_path']}")
    lines.append(f"- head_ref: {report['head_ref']}")
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
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    report = build_publication_sync_report(
        repo_root=REPO_ROOT,
        registry_path=args.registry_path,
        publication_id=args.publication,
        head_ref=args.head_ref,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_text(report))
    return 0 if args.report_only or report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
