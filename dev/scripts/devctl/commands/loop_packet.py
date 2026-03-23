"""devctl loop-packet command implementation."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from ..runtime.machine_output import ArtifactOutputOptions, emit_machine_artifact_output
from .loop_packet_helpers import (
    DEFAULT_SOURCE_CANDIDATES,
    RISK_CONFIDENCE,
    _auto_send_eligible,
    _build_live_triage_source,
    _build_packet_body,
    _choose_source,
    _discover_artifact_sources,
    _freshness_hours,
    _guidance_decision_modes,
    _guidance_requires_approval,
    _truncate_chars,
)


@dataclass(frozen=True)
class _LoopPacketContext:
    now_iso: str
    source_command: str
    source_path: str
    source_timestamp: str
    freshness_hours: float
    max_age_hours: float
    checked_paths: list[str]
    risk: str
    confidence: float
    next_actions: list[str]
    probe_guidance: list[dict[str, Any]]
    summary: str
    source_warnings: list[str]
    packet_id: str
    draft_text: str
    auto_send: bool


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
        report.get("terminal_packet", {}).get("draft_text") if isinstance(report.get("terminal_packet"), dict) else ""
    )
    lines.append(str(draft or "").strip() or "(none)")
    lines.append("")
    lines.append("## Next Actions")
    lines.append("")
    for row in report.get("next_actions", []):
        lines.append(f"- {row}")
    context_packet = report.get("context_packet")
    if isinstance(context_packet, dict) and context_packet.get("markdown"):
        lines.append("")
        lines.append(context_packet["markdown"])
    return "\n".join(lines)


def _build_guidance_contract(probe_guidance: list[dict[str, Any]]) -> dict[str, Any]:
    decision_modes = _guidance_decision_modes(probe_guidance)
    return {
        "guidance_attached_count": len(probe_guidance),
        "guidance_adoption_required": bool(probe_guidance),
        "decision_modes": list(decision_modes),
        "approval_required": _guidance_requires_approval(probe_guidance),
    }


def _build_packet_payload(context: _LoopPacketContext) -> dict[str, Any]:
    packet = {
        "schema_version": 1,
        "packet_id": context.packet_id,
        "created_at": context.now_iso,
        "channel": "terminal-draft",
        "source": {
            "command": context.source_command,
            "path": context.source_path,
            "timestamp": context.source_timestamp,
        },
        "guard": {
            "risk": context.risk,
            "confidence": context.confidence,
            "draft_only": not context.auto_send,
            "auto_send_permitted": context.auto_send,
        },
    }
    packet["next_actions"] = context.next_actions
    packet["probe_guidance"] = context.probe_guidance
    packet["guidance_contract"] = _build_guidance_contract(context.probe_guidance)
    packet["evidence"] = [
        f"source_command={context.source_command}",
        f"source_path={context.source_path}",
        f"freshness_hours={round(context.freshness_hours, 3)}",
    ]
    return packet


def _build_terminal_packet(context: _LoopPacketContext) -> dict[str, Any]:
    return {
        "packet_id": context.packet_id,
        "source_command": context.source_command,
        "draft_text": context.draft_text,
        "auto_send": context.auto_send,
        "probe_guidance_count": len(context.probe_guidance),
        "guidance_adoption_required": bool(context.probe_guidance),
        "guidance_decision_modes": list(_guidance_decision_modes(context.probe_guidance)),
        "guidance_requires_approval": _guidance_requires_approval(context.probe_guidance),
    }


def _build_ready_report(
    context: _LoopPacketContext,
    *,
    context_packet: Any,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "command": "loop-packet",
        "timestamp": context.now_iso,
        "ok": True,
        "reason": "packet_ready",
        "source_command": context.source_command,
    }
    report["source_path"] = context.source_path
    report["source_timestamp"] = context.source_timestamp
    report["freshness_hours"] = round(context.freshness_hours, 3)
    report["max_age_hours"] = context.max_age_hours
    report["checked_paths"] = context.checked_paths
    report["risk"] = context.risk
    report["confidence"] = context.confidence
    report["next_actions"] = context.next_actions
    report["probe_guidance"] = context.probe_guidance
    report["guidance_contract"] = _build_guidance_contract(context.probe_guidance)
    report["summary"] = context.summary
    report["warnings"] = context.source_warnings
    report["context_packet"] = asdict(context_packet) if context_packet is not None else None
    report["packet"] = _build_packet_payload(context)
    report["terminal_packet"] = _build_terminal_packet(context)
    return report


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

    payload = dict(source_row.payload or {})
    source_command = source_row.command or "triage"
    source_path = source_row.path or "<unknown>"

    timestamp = source_row.timestamp
    now_utc = datetime.now(UTC)
    if not isinstance(timestamp, datetime):
        report = {
            "command": "loop-packet",
            "timestamp": now_utc.isoformat().replace("+00:00", "Z"),
            "ok": False,
            "reason": "source_timestamp_missing",
            "source_command": source_command,
            "source_path": source_path,
            "checked_paths": checked_paths,
            "warnings": [*source_warnings, "source timestamp missing or invalid"],
        }
        return emit_machine_artifact_output(
            args,
            command="loop-packet",
            json_payload=report,
            human_output=_render_markdown(report),
            options=ArtifactOutputOptions(ok=False, summary={"reason": report["reason"]}),
        )

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
        return emit_machine_artifact_output(
            args,
            command="loop-packet",
            json_payload=report,
            human_output=_render_markdown(report),
            options=ArtifactOutputOptions(
                ok=False,
                summary={"reason": report["reason"], "risk": "stale"},
            ),
        )

    risk, raw_draft, next_actions, context_packet, probe_guidance = _build_packet_body(
        source_command=source_command,
        payload=payload,
    )
    confidence = RISK_CONFIDENCE.get(risk, RISK_CONFIDENCE["medium"])
    auto_send = bool(args.allow_auto_send) and _auto_send_eligible(
        source_command,
        payload,
        risk,
        probe_guidance=probe_guidance,
    )
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
        f"packet {packet_id} ready from {source_command} " f"(risk={risk}, auto_send={'yes' if auto_send else 'no'})"
    )
    route_context = _LoopPacketContext(
        now_iso=now_utc.isoformat().replace("+00:00", "Z"),
        source_command=source_command,
        source_path=source_path,
        source_timestamp=timestamp.isoformat().replace("+00:00", "Z"),
        freshness_hours=freshness_hours,
        max_age_hours=float(args.max_age_hours),
        checked_paths=checked_paths,
        risk=risk,
        confidence=confidence,
        next_actions=next_actions,
        probe_guidance=probe_guidance,
        summary=summary,
        source_warnings=source_warnings,
        packet_id=packet_id,
        draft_text=draft_text,
        auto_send=auto_send,
    )
    report = _build_ready_report(
        route_context,
        context_packet=context_packet,
    )

    return emit_machine_artifact_output(
        args,
        command="loop-packet",
        json_payload=report,
        human_output=_render_markdown(report),
        options=ArtifactOutputOptions(
            summary={
                "risk": risk,
                "confidence": confidence,
                "auto_send": auto_send,
            }
        ),
    )
