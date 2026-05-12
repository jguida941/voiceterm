"""Command surface for typed agent supervision."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...common import add_standard_output_arguments, emit_output, write_output
from ...config import REPO_ROOT
from ...runtime.agent_supervise_driver import (
    AgentSuperviseInput,
    AgentSuperviseReport,
    evaluate_agent_supervision,
)
from ...runtime.lifetime_bypass_mode import (
    BypassReceipt,
    bypass_receipt_from_mapping,
)
from ..development.packet_attention import review_state_payload


def add_parser(sub) -> None:
    parser = sub.add_parser(
        "agent-supervise",
        help="Evaluate typed process-exit/freeze supervision for an agent",
    )
    parser.add_argument("--actor", default="codex")
    parser.add_argument("--provider", default="codex")
    parser.add_argument("--role", default="reviewer")
    parser.add_argument("--pid", type=int, default=0)
    parser.add_argument("--session-id", default="")
    parser.add_argument("--session-path", default="")
    parser.add_argument("--sessions-root", default="")
    parser.add_argument("--review-state-path", default="")
    parser.add_argument("--bypass-receipt-file", default="")
    parser.add_argument("--bypass-receipt-json", default="")
    parser.add_argument(
        "--staleness-threshold-seconds",
        "--threshold-seconds",
        dest="staleness_threshold_seconds",
        type=int,
        default=900,
    )
    add_standard_output_arguments(
        parser,
        format_choices=("json", "md"),
        default_format="md",
    )


def run(args: Any) -> int:
    report = evaluate_agent_supervision(
        AgentSuperviseInput(
            actor=getattr(args, "actor", "codex"),
            provider=getattr(args, "provider", "codex"),
            role=getattr(args, "role", "reviewer"),
            pid=int(getattr(args, "pid", 0) or 0),
            session_id=getattr(args, "session_id", ""),
            session_path=_path_or_none(getattr(args, "session_path", "")),
            sessions_root=_path_or_none(getattr(args, "sessions_root", "")),
            review_state=_load_review_state(getattr(args, "review_state_path", "")),
            bypass_receipt=_load_bypass_receipt(args),
            staleness_threshold_seconds=int(
                getattr(args, "staleness_threshold_seconds", 900) or 900
            ),
        )
    )
    payload = report.to_dict()
    output = json.dumps(payload, indent=2, sort_keys=True)
    if getattr(args, "format", "md") != "json":
        output = _render_markdown(report)
    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return 0 if report.status in {"healthy", "spawn_authorized"} else 1


def _load_review_state(path: str) -> dict[str, object]:
    raw = str(path or "").strip()
    if not raw:
        payload = review_state_payload(REPO_ROOT)
        return dict(payload) if isinstance(payload, dict) else {}
    try:
        payload = json.loads(Path(raw).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_bypass_receipt(args: Any) -> BypassReceipt | None:
    raw_json = str(getattr(args, "bypass_receipt_json", "") or "").strip()
    raw_path = str(getattr(args, "bypass_receipt_file", "") or "").strip()
    payload: object = None
    if raw_json:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            return None
    elif raw_path:
        try:
            payload = json.loads(Path(raw_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
    if not isinstance(payload, dict):
        return None
    try:
        return bypass_receipt_from_mapping(payload)
    except ValueError:
        return None


def _path_or_none(value: str) -> Path | None:
    raw = str(value or "").strip()
    return Path(raw) if raw else None


def _render_markdown(report: AgentSuperviseReport) -> str:
    lines = [
        "# devctl agent-supervise",
        "",
        f"- status: {report.status}",
        f"- actor: {report.actor}",
        f"- role: {report.role}",
        f"- process_state: {report.process_state}",
        f"- process_exit_detected: {report.process_exit_detected}",
        f"- freeze_detected: {report.freeze_detected}",
        f"- continuation_anchor_packet_id: {report.continuation_anchor_packet_id or '(none)'}",
        f"- rollout_mtime_age_seconds: {report.rollout_mtime_age_seconds}",
        f"- trigger_reason: {report.trigger_reason or '(none)'}",
    ]
    if report.next_command:
        lines.append(f"- next_command: `{report.next_command}`")
    if report.blocked_reasons:
        lines.extend(["", "## Blocked Reasons"])
        lines.extend(f"- {reason}" for reason in report.blocked_reasons)
    if report.spawn_action is not None:
        lines.extend(["", "## Spawn Action"])
        lines.append(f"- bypass_receipt_id: {report.spawn_action.bypass_receipt_id}")
        lines.append(
            "- continuation_anchor_packet_id: "
            f"{report.spawn_action.continuation_anchor_packet_id}"
        )
    return "\n".join(lines)


__all__ = ["add_parser", "run"]
