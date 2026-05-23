"""Command surface for typed agent supervision."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...common import add_standard_output_arguments, emit_output, write_output
from ...config import REPO_ROOT
from ...runtime.agent_supervise_driver import (
    AgentSuperviseInput,
    AgentSuperviseLaunchResult,
    AgentSuperviseReport,
    execute_agent_supervision_spawn,
    evaluate_agent_supervision,
)
from ...runtime.lifetime_bypass_mode import (
    BypassReceipt,
    bypass_receipt_from_mapping,
)
from ..development.packet_attention import review_state_payload
from . import peer_spawn as _peer_spawn_command


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
        "--execute",
        action="store_true",
        default=False,
        help="Launch the authorized replacement agent when supervision gates pass",
    )
    parser.add_argument(
        "--new-spawn",
        action="store_true",
        default=False,
        help=(
            "Treat this as a fresh peer spawn rather than a dead-process "
            "recovery. With --execute, runs the canonical peer-spawn driver "
            "directly under the supplied BypassReceipt without requiring a "
            "stale rollout or dead PID."
        ),
    )
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
    new_spawn = bool(getattr(args, "new_spawn", False))
    execute = bool(getattr(args, "execute", False))
    bypass_receipt = _load_bypass_receipt(args)
    if new_spawn and execute:
        return _run_new_spawn(args, bypass_receipt=bypass_receipt)
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
            bypass_receipt=bypass_receipt,
            staleness_threshold_seconds=int(
                getattr(args, "staleness_threshold_seconds", 900) or 900
            ),
        )
    )
    if execute:
        report = execute_agent_supervision_spawn(report)
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
    if report.status in {"healthy", "ignored_helper_closed"}:
        # v4.55.1 priority 1 (rev_pkt_4764/4765): `ignored_helper_closed`
        # is a typed nonblocking outcome for closed read-only helper
        # sidecar audits. CLI exits 0 so the audit caller can chain
        # commands without falsely failing on a dead helper.
        return 0
    if report.status != "spawn_authorized":
        return 1
    if bool(getattr(args, "execute", False)):
        return _execute_exit_code(report.launch_result)
    return 0


def _run_new_spawn(args: Any, *, bypass_receipt: BypassReceipt | None) -> int:
    """Forward a fresh peer spawn to the canonical peer-spawn driver.

    `--new-spawn` is the operator-approved path for spawning a brand new peer
    without first observing a dead/stale process. The gating is the active
    BypassReceipt and operator authorization; freshness checks are skipped.
    """
    from ...runtime.peer_spawn import compose_peer_spawn

    launch_adapter = (
        None
        if bool(getattr(args, "dry_run", False))
        else _peer_spawn_command._build_canonical_launch_adapter()
    )
    report = compose_peer_spawn(
        provider=str(getattr(args, "provider", "") or "codex"),
        role=str(getattr(args, "role", "") or "implementer"),
        bypass_receipt=bypass_receipt,
        row_id=str(getattr(args, "session_id", "") or ""),
        actor=str(getattr(args, "actor", "") or "operator"),
        reason="agent-supervise --new-spawn",
        interaction_mode="remote_control",
        headless=True,
        launch_callable=launch_adapter,
    )
    payload = report.to_dict()
    output = json.dumps(payload, indent=2, sort_keys=True)
    if getattr(args, "format", "md") != "json":
        output = "\n".join(
            [
                "# devctl agent-supervise --new-spawn",
                "",
                f"- ok: {report.ok}",
                f"- trace_path: {report.trace_path}",
                "",
                "Canonical command: `python3 dev/scripts/devctl.py peer-spawn "
                f"--provider {getattr(args, 'provider', 'codex')} "
                f"--role {getattr(args, 'role', 'implementer')} "
                "--bypass-receipt-id <id> --format json`",
            ]
        )
    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return 0 if report.ok else 1


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
    if report.launch_result is not None:
        _render_launch_result(lines, report.launch_result)
    return "\n".join(lines)


def _execute_exit_code(result: AgentSuperviseLaunchResult | None) -> int:
    return 0 if result is not None and result.status == "spawned" else 1


def _render_launch_result(
    lines: list[str],
    result: AgentSuperviseLaunchResult,
) -> None:
    lines.extend(["", "## Launch Result"])
    lines.append(f"- status: {result.status}")
    if result.pid:
        lines.append(f"- pid: {result.pid}")
    if result.error:
        lines.append(f"- error: {result.error}")


__all__ = ["add_parser", "run"]
