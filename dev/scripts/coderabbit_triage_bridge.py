#!/usr/bin/env python3
"""Workflow helper for CodeRabbit triage collection/gating/counts."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    from dev.scripts.coderabbit_triage_collect import collect_findings as _collect_findings
    from dev.scripts.coderabbit_triage_support import (
        resolve_pr_number as _resolve_pr_number,
        resolve_repository as _resolve_repository,
    )
except ModuleNotFoundError:  # pragma: no cover - local fallback
    from coderabbit_triage_collect import collect_findings as _collect_findings  # type: ignore
    from coderabbit_triage_support import (  # type: ignore
        resolve_pr_number as _resolve_pr_number,
        resolve_repository as _resolve_repository,
    )


def collect_command(args: argparse.Namespace) -> int:
    event_path = Path(args.event_path)
    event = json.loads(event_path.read_text(encoding="utf-8"))
    event_name = str(args.event_name).strip()
    pushed_sha = str(event.get("after") or "").strip() if event_name == "push" else ""
    warnings: list[str] = []
    repo = _resolve_repository(event, args.repo_input)
    pr_number = _resolve_pr_number(
        event=event,
        event_name=event_name,
        repo=repo,
        pr_input=args.pr_input,
        pushed_sha=pushed_sha,
        warnings=warnings,
    )
    deduped, head_sha = _collect_findings(
        event=event,
        event_name=event_name,
        repo=repo,
        pr_number=pr_number,
        pushed_sha=pushed_sha,
        warnings=warnings,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    priority_path = output_dir / "priority.json"
    backlog_path = output_dir / "backlog-medium.json"
    backlog_md_path = output_dir / "backlog-medium.md"
    triage_md_path = output_dir / "triage.md"

    backlog_items = [
        item
        for item in deduped
        if isinstance(item, dict)
        and str(item.get("severity") or "").lower() in {"critical", "high", "medium"}
    ]
    pr_number_value = int(pr_number) if pr_number.isdigit() else None
    pr_label = pr_number or "n/a"
    now = datetime.now(timezone.utc).isoformat()

    payload = {
        "source": "coderabbit",
        "repository": repo,
        "pr_number": pr_number_value,
        "head_sha": head_sha,
        "generated_at": now,
        "items": deduped,
        "medium_plus_count": len(backlog_items),
        "warning_count": len(warnings),
    }
    priority_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    backlog_payload = {
        "source": "coderabbit",
        "repository": repo,
        "pr_number": pr_number_value,
        "head_sha": head_sha,
        "generated_at": now,
        "items": backlog_items,
        "agent_handoff": {
            "intent": "AI remediation queue for CodeRabbit medium/high findings",
            "recommended_command": (
                "python3 dev/scripts/devctl.py triage "
                "--no-cihub "
                "--external-issues-file .cihub/coderabbit/backlog-medium.json "
                "--emit-bundle "
                "--bundle-dir .cihub/coderabbit "
                "--bundle-prefix coderabbit-backlog "
                "--format md "
                "--output .cihub/coderabbit/backlog-triage.md"
            ),
            "notes": "Validate finding relevance before auto-fix commits.",
        },
    }
    backlog_path.write_text(json.dumps(backlog_payload, indent=2), encoding="utf-8")

    triage_lines = [
        "# CodeRabbit normalized findings",
        "",
        f"- repository: {repo}",
        f"- pr_number: {pr_label}",
        f"- findings: {len(deduped)}",
        f"- medium_plus: {len(backlog_items)}",
        f"- warning_count: {len(warnings)}",
        "",
    ]
    for row in deduped[:60]:
        triage_lines.append(
            f"- [{row.get('severity', 'medium')}] {row.get('category', 'quality')}: {row.get('summary', '')}"
        )
    triage_md_path.write_text("\n".join(triage_lines), encoding="utf-8")

    backlog_lines = [
        "# CodeRabbit medium+ backlog",
        "",
        f"- repository: {repo}",
        f"- pr_number: {pr_label}",
        f"- items: {len(backlog_items)}",
        "",
    ]
    for row in backlog_items[:80]:
        backlog_lines.append(
            f"- [{row.get('severity', 'medium')}] {row.get('category', 'quality')}: {row.get('summary', '')}"
        )
    backlog_md_path.write_text("\n".join(backlog_lines), encoding="utf-8")
    print(f"wrote {priority_path} ({len(deduped)} findings)")
    return 0


def enforce_command(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.priority_file).read_text(encoding="utf-8"))
    items = payload.get("items", [])
    if not isinstance(items, list):
        raise RuntimeError("CodeRabbit priority payload is invalid (items is not a list).")

    blocked: list[dict[str, str]] = []
    for row in items:
        if not isinstance(row, dict):
            continue
        severity = str(row.get("severity") or "medium").lower()
        if severity in {"critical", "high", "medium"}:
            blocked.append(
                {
                    "severity": severity,
                    "category": str(row.get("category") or "quality"),
                    "summary": str(row.get("summary") or "").strip(),
                }
            )

    if blocked:
        print("CodeRabbit gate failed (medium/high findings present):")
        for finding in blocked:
            print(f"- [{finding['severity']}] {finding['category']}: {finding['summary']}")
        return 1

    print("CodeRabbit gate passed (no medium/high findings).")
    return 0


def count_command(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
    items = payload.get("items", [])
    print(len(items) if isinstance(items, list) else 0)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    collect = sub.add_parser("collect", help="Collect/normalize CodeRabbit findings")
    collect.add_argument("--event-path", default=os.getenv("GITHUB_EVENT_PATH", ""))
    collect.add_argument("--event-name", default=os.getenv("GITHUB_EVENT_NAME", ""))
    collect.add_argument("--pr-input", default=os.getenv("PR_INPUT", ""))
    collect.add_argument("--repo-input", default=os.getenv("REPO_INPUT", ""))
    collect.add_argument("--output-dir", default=".cihub/coderabbit")

    enforce = sub.add_parser("enforce", help="Fail when medium/high findings are present")
    enforce.add_argument("--priority-file", default=".cihub/coderabbit/priority.json")

    count = sub.add_parser("count", help="Count issue items in payload")
    count.add_argument("--input-file", default=".cihub/coderabbit/backlog-medium.json")

    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.command == "collect":
        return collect_command(args)
    if args.command == "enforce":
        return enforce_command(args)
    if args.command == "count":
        return count_command(args)
    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
