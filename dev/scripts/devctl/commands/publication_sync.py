"""devctl publication-sync command."""

from __future__ import annotations

import json

from ..common import emit_output, pipe_output, write_output
from ..publication_sync.core import build_publication_sync_report, record_publication_sync
from ..time_utils import utc_timestamp

IMPACT_PREVIEW_LIMIT = 12


def _error_report(args, message: str) -> dict:
    return {
        "command": "publication-sync",
        "timestamp": utc_timestamp(),
        "ok": False,
        "exit_ok": False,
        "fail_on_stale": bool(getattr(args, "fail_on_stale", False)),
        "registry_path": getattr(args, "registry_path", None),
        "head_ref": getattr(args, "head_ref", "HEAD"),
        "publication_filter": getattr(args, "publication", None),
        "publication_count": 0,
        "stale_publication_count": 0,
        "error_count": 1,
        "errors": [message],
        "record_update": None,
        "publications": [],
    }


def _render_md(report: dict) -> str:
    lines = ["# devctl publication-sync", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- exit_ok: {report['exit_ok']}")
    lines.append(f"- fail_on_stale: {report['fail_on_stale']}")
    lines.append(f"- registry_path: {report['registry_path']}")
    lines.append(f"- head_ref: {report['head_ref']}")
    if report.get("resolved_head_ref"):
        lines.append(f"- resolved_head_ref: {report['resolved_head_ref']}")
    if report.get("publication_filter"):
        lines.append(f"- publication_filter: {report['publication_filter']}")
    lines.append(f"- publications: {report['publication_count']}")
    lines.append(f"- stale_publications: {report['stale_publication_count']}")
    lines.append(f"- errors: {report['error_count']}")

    if report.get("record_update"):
        record = report["record_update"]
        lines.append("")
        lines.append("## Recorded Sync")
        lines.append(f"- publication: {record['publication']}")
        lines.append(f"- source_ref: {record['source_ref']}")
        if record.get("external_ref"):
            lines.append(f"- external_ref: {record['external_ref']}")
        lines.append(f"- last_synced_at: {record['last_synced_at']}")

    if report["errors"]:
        lines.append("")
        lines.append("## Errors")
        for message in report["errors"]:
            lines.append(f"- {message}")

    for item in report["publications"]:
        lines.append("")
        lines.append(f"## {item['id']}")
        lines.append(f"- title: {item['title']}")
        lines.append(f"- stale: {item['stale']}")
        lines.append(f"- public_url: {item['public_url']}")
        lines.append(f"- external_repo: {item['external_repo']}")
        if item.get("external_branch"):
            lines.append(f"- external_branch: {item['external_branch']}")
        lines.append(f"- watched_paths: {len(item['watched_paths'])}")
        lines.append(f"- changed_path_count: {item['changed_path_count']}")
        lines.append(f"- impacted_path_count: {item['impacted_path_count']}")
        lines.append(f"- source_ref: {item['source_ref']}")
        if item.get("resolved_source_ref"):
            lines.append(f"- resolved_source_ref: {item['resolved_source_ref']}")
        if item.get("external_ref"):
            lines.append(f"- external_ref: {item['external_ref']}")
        if item.get("last_synced_at"):
            lines.append(f"- last_synced_at: {item['last_synced_at']}")
        if item.get("notes"):
            lines.append(f"- notes: {item['notes']}")
        if item["errors"]:
            lines.extend(f"- error: {message}" for message in item["errors"])
        if item["impacted_paths"]:
            lines.append("- impacted_paths:")
            for path in item["impacted_paths"][:IMPACT_PREVIEW_LIMIT]:
                lines.append(f"  - {path}")
            remaining = len(item["impacted_paths"]) - IMPACT_PREVIEW_LIMIT
            if remaining > 0:
                lines.append(f"  - ... {remaining} more")
        lines.append(
            "- record_hint: "
            "python3 dev/scripts/devctl.py publication-sync "
            f"--publication {item['id']} --record-source-ref HEAD "
            "--record-external-ref <external-site-commit>"
        )

    return "\n".join(lines)


def run(args) -> int:
    """Report or record external publication sync state."""
    if args.record_external_ref and not args.record_source_ref:
        report = _error_report(
            args,
            "--record-external-ref requires --record-source-ref",
        )
    elif args.record_synced_at and not args.record_source_ref:
        report = _error_report(
            args,
            "--record-synced-at requires --record-source-ref",
        )
    elif args.record_source_ref and not args.publication:
        report = _error_report(
            args,
            "--publication is required with --record-source-ref",
        )
    else:
        record_update = None
        errors: list[str] = []
        if args.record_source_ref:
            try:
                record_update = record_publication_sync(
                    publication_id=args.publication,
                    source_ref=args.record_source_ref,
                    external_ref=args.record_external_ref,
                    synced_at=args.record_synced_at,
                    registry_path=args.registry_path,
                )
            except ValueError as exc:
                errors.append(str(exc))

        payload = build_publication_sync_report(
            registry_path=args.registry_path,
            publication_id=args.publication,
            head_ref=args.head_ref,
        )
        payload_errors = [*payload["errors"], *errors]
        error_count = len(payload_errors) + sum(
            len(item.get("errors", [])) for item in payload["publications"]
        )
        stale_publication_count = payload["stale_publication_count"]
        exit_ok = error_count == 0 and (
            not args.fail_on_stale or stale_publication_count == 0
        )
        report = {
            "command": "publication-sync",
            "timestamp": utc_timestamp(),
            **payload,
            "errors": payload_errors,
            "error_count": error_count,
            "fail_on_stale": bool(args.fail_on_stale),
            "exit_ok": exit_ok,
            "record_update": record_update,
        }

    output = json.dumps(report, indent=2) if args.format == "json" else _render_md(report)
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_rc != 0:
        return pipe_rc
    return 0 if report["exit_ok"] else 1
