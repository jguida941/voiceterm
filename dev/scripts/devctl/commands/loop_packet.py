"""devctl loop-packet command implementation."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from ..common import pipe_output, write_output
from .loop_packet_helpers import (
    DEFAULT_SOURCE_CANDIDATES,
    RISK_CONFIDENCE,
    _auto_send_eligible,
    _build_live_triage_source,
    _build_packet_body,
    _choose_source,
    _discover_artifact_sources,
    _freshness_hours,
    _truncate_chars,
)


def _render_markdown(report: dict[str, Any]) -> str:
    lines = ["# devctl loop-packet", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- source_command: {report.get('source_command')}")
    lines.append(f"- source_path: {report.get('source_path')}")
    lines.append(f"- risk: {report.get('risk')}")
    lines.append(f"- confidence: {report.get('confidence')}")
    lines.append(f"- freshness_hours: {report.get('freshness_hours')}")
    lines.append(f"- auto_send: {report.get('terminal_packet', {}).get('auto_send')}")
    lines.append(f"- summary: {report.get('summary')}")
    warnings = report.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        lines.append("- warnings: " + " | ".join(str(row) for row in warnings))
    lines.append("")
    lines.append("## Draft")
    lines.append("")
    draft = (
        report.get("terminal_packet", {}).get("draft_text")
        if isinstance(report.get("terminal_packet"), dict)
        else ""
    )
    lines.append(str(draft or "").strip() or "(none)")
    lines.append("")
    lines.append("## Next Actions")
    lines.append("")
    for row in report.get("next_actions", []):
        lines.append(f"- {row}")
    return "\n".join(lines)


def run(args) -> int:
    """Build a guarded terminal feedback packet from triage/loop sources."""
    if args.max_age_hours <= 0:
        print("Error: --max-age-hours must be > 0")
        return 2
    if args.max_draft_chars < 200:
        print("Error: --max-draft-chars must be >= 200")
        return 2

    source_inputs = list(args.source_json or []) or list(DEFAULT_SOURCE_CANDIDATES)
    source_rows, source_warnings, checked_paths = _discover_artifact_sources(source_inputs)
    source_row = _choose_source(rows=source_rows, prefer_source=args.prefer_source)
    if source_row is None:
        source_row = _build_live_triage_source()
        source_warnings.append("no artifact source found; generated live triage source")

    payload = dict(source_row.get("payload") or {})
    source_command = str(source_row.get("command") or "triage")
    source_path = str(source_row.get("path") or "<unknown>")

    timestamp = source_row.get("timestamp")
    now_utc = datetime.now(timezone.utc)
    if not isinstance(timestamp, datetime):
        report = {
            "command": "loop-packet",
            "timestamp": now_utc.isoformat().replace("+00:00", "Z"),
            "ok": False,
            "reason": "source_timestamp_missing",
            "source_command": source_command,
            "source_path": source_path,
            "checked_paths": checked_paths,
            "warnings": source_warnings + ["source timestamp missing or invalid"],
        }
        output = json.dumps(report, indent=2) if args.format == "json" else _render_markdown(report)
        write_output(output, args.output)
        if args.pipe_command:
            pipe_rc = pipe_output(output, args.pipe_command, args.pipe_args)
            if pipe_rc != 0:
                return pipe_rc
        return 1

    freshness_hours = _freshness_hours(timestamp, now_utc)
    if freshness_hours > float(args.max_age_hours):
        report = {
            "command": "loop-packet",
            "timestamp": now_utc.isoformat().replace("+00:00", "Z"),
            "ok": False,
            "reason": "source_stale",
            "source_command": source_command,
            "source_path": source_path,
            "freshness_hours": round(freshness_hours, 3),
            "max_age_hours": float(args.max_age_hours),
            "checked_paths": checked_paths,
            "warnings": source_warnings,
        }
        output = json.dumps(report, indent=2) if args.format == "json" else _render_markdown(report)
        write_output(output, args.output)
        if args.pipe_command:
            pipe_rc = pipe_output(output, args.pipe_command, args.pipe_args)
            if pipe_rc != 0:
                return pipe_rc
        return 1

    risk, raw_draft, next_actions = _build_packet_body(
        source_command=source_command,
        payload=payload,
    )
    confidence = RISK_CONFIDENCE.get(risk, RISK_CONFIDENCE["medium"])
    auto_send = bool(args.allow_auto_send) and _auto_send_eligible(source_command, payload, risk)
    draft_text = _truncate_chars(raw_draft, int(args.max_draft_chars))
    packet_seed = "|".join(
        [
            source_command,
            str(payload.get("timestamp") or ""),
            source_path,
            draft_text,
        ]
    )
    packet_id = hashlib.sha256(packet_seed.encode("utf-8")).hexdigest()[:16]
    summary = (
        f"packet {packet_id} ready from {source_command} "
        f"(risk={risk}, auto_send={'yes' if auto_send else 'no'})"
    )

    report = {
        "command": "loop-packet",
        "timestamp": now_utc.isoformat().replace("+00:00", "Z"),
        "ok": True,
        "reason": "packet_ready",
        "source_command": source_command,
        "source_path": source_path,
        "source_timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "freshness_hours": round(freshness_hours, 3),
        "max_age_hours": float(args.max_age_hours),
        "checked_paths": checked_paths,
        "risk": risk,
        "confidence": confidence,
        "next_actions": next_actions,
        "summary": summary,
        "warnings": source_warnings,
        "packet": {
            "schema_version": 1,
            "packet_id": packet_id,
            "created_at": now_utc.isoformat().replace("+00:00", "Z"),
            "channel": "terminal-draft",
            "source": {
                "command": source_command,
                "path": source_path,
                "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
            },
            "guard": {
                "risk": risk,
                "confidence": confidence,
                "draft_only": not auto_send,
                "auto_send_permitted": auto_send,
            },
            "next_actions": next_actions,
            "evidence": [
                f"source_command={source_command}",
                f"source_path={source_path}",
                f"freshness_hours={round(freshness_hours, 3)}",
            ],
        },
        "terminal_packet": {
            "packet_id": packet_id,
            "source_command": source_command,
            "draft_text": draft_text,
            "auto_send": auto_send,
        },
    }

    output = json.dumps(report, indent=2) if args.format == "json" else _render_markdown(report)
    write_output(output, args.output)
    if args.pipe_command:
        pipe_rc = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_rc != 0:
            return pipe_rc
    return 0
