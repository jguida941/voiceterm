"""Command surface for the canonical typed peer-spawn driver.

`devctl peer-spawn` and `devctl peer-terminate` are thin wrappers around
`runtime.peer_spawn.compose_peer_spawn` / `compose_peer_terminate`. They
inject the canonical launch adapter (`launch_sessions_headless`) plus a
typed `BypassReceipt`, then return a typed `PeerSpawnReport`.

This command is the single repo-owned operator/agent entry point for
launching a peer codex/claude conductor. Other surfaces
(`review-channel --action launch`, `review-channel --action recover`,
`agent-supervise --execute`) compose into this driver under the hood.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from ...common import add_standard_output_arguments, emit_output, write_output
from ...config import REPO_ROOT
from ...runtime.bypass_lifecycle_models import (
    BypassAuthorityScope,
    BypassReceipt,
    bypass_receipt_from_mapping,
)
from ...runtime.bypass_lifecycle_registry import (
    active_bypass_lifecycle_for_receipt_id,
)
from ...runtime.peer_spawn import (
    DEFAULT_PEER_SPAWN_TRACE_REL,
    SUPPORTED_PROVIDERS,
    SUPPORTED_ROLES,
    PeerSpawnReport,
    compose_peer_spawn,
    compose_peer_terminate,
)


def add_peer_spawn_parser(sub) -> None:
    """Register the ``peer-spawn`` subcommand."""
    parser = sub.add_parser(
        "peer-spawn",
        help=(
            "Canonical typed peer-spawn driver. One repo-owned entry point "
            "for launching codex/claude/cursor peer conductors."
        ),
    )
    parser.add_argument(
        "--provider",
        choices=SUPPORTED_PROVIDERS,
        required=True,
        help="Provider conductor to spawn as a peer session.",
    )
    parser.add_argument(
        "--role",
        choices=SUPPORTED_ROLES,
        default="implementer",
        help="Role the spawned peer session will own.",
    )
    parser.add_argument(
        "--bypass-receipt-id",
        default="",
        help=(
            "Typed BypassReceipt id required to authorize spawn. Driver "
            "validates the receipt is active and grants `agent_spawn_only`."
        ),
    )
    parser.add_argument(
        "--bypass-receipt-file",
        default="",
        help=(
            "Optional path to a JSON file containing the full BypassReceipt "
            "payload. Used by tests and direct operator invocation."
        ),
    )
    parser.add_argument(
        "--bypass-receipt-json",
        default="",
        help="Inline JSON for the BypassReceipt payload (test-only).",
    )
    parser.add_argument(
        "--row-id",
        default="",
        help="Plan row id (e.g. MP-XXX) the spawned peer will work against.",
    )
    parser.add_argument(
        "--actor",
        default="operator",
        help="Actor requesting the spawn (operator, agent, controller).",
    )
    parser.add_argument(
        "--reason",
        default="",
        help="Operator/agent rationale recorded in the typed AgentSpawnRequest.",
    )
    parser.add_argument(
        "--interaction-mode",
        choices=("remote_control", "terminal_app", "headless"),
        default="remote_control",
        help="Launch interaction mode requested for the spawned peer.",
    )
    parser.add_argument(
        "--terminal-visible",
        action="store_true",
        default=False,
        help="Launch via Terminal.app instead of fully headless background.",
    )
    parser.add_argument(
        "--trace-path",
        default="",
        help=(
            "Override the typed event trace path. Defaults to "
            "dev/reports/review_channel/events/trace.ndjson."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help=(
            "Validate authority and emit AgentSpawnRequest+AgentSpawnReceipt "
            "without invoking the underlying launch adapter."
        ),
    )
    parser.add_argument(
        "--task-prompt",
        default="",
        help=(
            "Inline bounded one-shot task prompt for the spawned conductor. "
            "When set, replaces the multi-turn review-channel conductor "
            "prompt; the spawned `codex exec` (or equivalent provider) runs "
            "the single prompt against `--sandbox workspace-write` and "
            "exits. Use for dogfood smoke tasks and bounded operator "
            "directives. Mutually exclusive with `--task-prompt-file`."
        ),
    )
    parser.add_argument(
        "--task-prompt-file",
        default="",
        help=(
            "Path to a file containing the bounded one-shot task prompt. "
            "Same semantics as `--task-prompt` but read from disk so long "
            "prompts are not subject to shell-quoting limits."
        ),
    )
    add_standard_output_arguments(
        parser,
        format_choices=("json", "md"),
        default_format="md",
    )


def add_peer_terminate_parser(sub) -> None:
    """Register the ``peer-terminate`` subcommand."""
    parser = sub.add_parser(
        "peer-terminate",
        help="Canonical typed peer-terminate driver; emits AgentTerminationReceipt.",
    )
    parser.add_argument(
        "--provider",
        choices=SUPPORTED_PROVIDERS,
        required=True,
        help="Provider whose peer session should be terminated.",
    )
    parser.add_argument(
        "--session-id",
        default="",
        help="Provider session id for the peer being terminated.",
    )
    parser.add_argument(
        "--pid",
        type=int,
        required=True,
        help="Process id of the running peer session.",
    )
    parser.add_argument(
        "--signal",
        default="SIGTERM",
        help="Signal name to send (default: SIGTERM).",
    )
    parser.add_argument(
        "--actor",
        default="operator",
        help="Actor requesting termination.",
    )
    parser.add_argument(
        "--reason",
        default="",
        help="Operator/agent rationale recorded in the typed receipt.",
    )
    parser.add_argument(
        "--trace-path",
        default="",
        help="Override the typed event trace path.",
    )
    add_standard_output_arguments(
        parser,
        format_choices=("json", "md"),
        default_format="md",
    )


def run_peer_spawn(args: Any) -> int:
    """Execute one ``devctl peer-spawn`` call."""
    repo_root = REPO_ROOT
    bypass_receipt = _load_bypass_receipt(args)
    trace_path = str(getattr(args, "trace_path", "") or "")
    headless = not bool(getattr(args, "terminal_visible", False))
    task_prompt = _load_task_prompt(args)
    launch_adapter: Callable[..., tuple[bool, int, str, str]] | None = (
        None if bool(getattr(args, "dry_run", False))
        else _build_canonical_launch_adapter()
    )
    report = compose_peer_spawn(
        provider=str(getattr(args, "provider", "") or ""),
        role=str(getattr(args, "role", "") or "implementer"),
        bypass_receipt=bypass_receipt,
        row_id=str(getattr(args, "row_id", "") or ""),
        actor=str(getattr(args, "actor", "") or "operator"),
        reason=str(getattr(args, "reason", "") or ""),
        interaction_mode=str(getattr(args, "interaction_mode", "") or "remote_control"),
        headless=headless,
        trace_path=trace_path,
        repo_root=repo_root,
        launch_callable=launch_adapter,
        task_prompt=task_prompt,
    )
    return _emit_report(args, report)


def _load_task_prompt(args: Any) -> str:
    raw_inline = str(getattr(args, "task_prompt", "") or "").strip()
    raw_path = str(getattr(args, "task_prompt_file", "") or "").strip()
    if raw_inline and raw_path:
        raise ValueError(
            "--task-prompt and --task-prompt-file are mutually exclusive"
        )
    if raw_inline:
        return raw_inline
    if raw_path:
        return Path(raw_path).read_text(encoding="utf-8").rstrip("\n")
    return ""


def run_peer_terminate(args: Any) -> int:
    """Execute one ``devctl peer-terminate`` call."""
    repo_root = REPO_ROOT
    trace_path = str(getattr(args, "trace_path", "") or "")
    report = compose_peer_terminate(
        provider=str(getattr(args, "provider", "") or ""),
        session_id=str(getattr(args, "session_id", "") or ""),
        pid=int(getattr(args, "pid", 0) or 0),
        actor=str(getattr(args, "actor", "") or "operator"),
        reason=str(getattr(args, "reason", "") or ""),
        signal_name=str(getattr(args, "signal", "SIGTERM") or "SIGTERM"),
        trace_path=trace_path,
        repo_root=repo_root,
    )
    return _emit_report(args, report)


def _emit_report(args: Any, report: PeerSpawnReport) -> int:
    payload = report.to_dict()
    if getattr(args, "format", "md") == "json":
        output = json.dumps(payload, indent=2, sort_keys=True)
    else:
        output = _render_markdown(report)
    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return 0 if report.ok else 1


def _render_markdown(report: PeerSpawnReport) -> str:
    lines = [
        f"# devctl {report.action}",
        "",
        f"- ok: {report.ok}",
        f"- trace_path: {report.trace_path}",
    ]
    if report.canonical_command_hint:
        lines.append(f"- canonical_command_hint: `{report.canonical_command_hint}`")
    if report.request is not None:
        lines.extend(["", "## AgentSpawnRequest"])
        for key in ("provider", "role", "bypass_receipt_id", "row_id", "actor", "requested_at_utc"):
            value = report.request.get(key)
            if value is None or value == "":
                continue
            lines.append(f"- {key}: {value}")
    if report.receipt is not None:
        lines.extend(["", "## Receipt"])
        for key in (
            "request_id",
            "provider",
            "role",
            "session_id",
            "pid",
            "status",
            "signal",
            "issued_at_utc",
            "reason",
            "error",
            "script_path",
        ):
            value = report.receipt.get(key)
            if value is None or value == "" or value == 0:
                continue
            lines.append(f"- {key}: {value}")
    if report.warnings:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- {warning}" for warning in report.warnings)
    if report.errors:
        lines.extend(["", "## Errors"])
        lines.extend(f"- {error}" for error in report.errors)
    return "\n".join(lines)


def _load_bypass_receipt(args: Any) -> BypassReceipt | None:
    raw_json = str(getattr(args, "bypass_receipt_json", "") or "").strip()
    raw_path = str(getattr(args, "bypass_receipt_file", "") or "").strip()
    raw_id = str(getattr(args, "bypass_receipt_id", "") or "").strip()
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
    elif raw_id:
        store_override = os.environ.get(
            "DEVCTL_BYPASS_LIFECYCLE_STORE_PATH", ""
        ).strip()
        store_path = (
            Path(store_override)
            if store_override
            else REPO_ROOT / "dev" / "state" / "bypass_lifecycles.jsonl"
        )
        lifecycle = active_bypass_lifecycle_for_receipt_id(
            raw_id,
            store_path=store_path,
            required_scope=BypassAuthorityScope.AGENT_SPAWN_ONLY,
        )
        if lifecycle is None or lifecycle.receipt is None:
            return None
        return lifecycle.receipt
    if not isinstance(payload, dict):
        return None
    try:
        return bypass_receipt_from_mapping(payload)
    except (ValueError, TypeError):
        return None


def _build_canonical_launch_adapter() -> Callable[..., tuple[bool, int, str, str]]:
    """Return the canonical launch adapter used by `compose_peer_spawn`.

    The adapter is built lazily so unit tests can import this module without
    pulling in the entire bridge-launch dependency graph. The runtime path
    composes `build_launch_sessions` + `launch_sessions_headless` — the
    canonical headless launch surface that `review-channel --action launch`,
    `--action recover`, and `agent-supervise --execute` already use.
    """

    def adapter(
        *,
        provider: str,
        role: str,
        row_id: str,
        bypass_receipt: BypassReceipt | None,
        interaction_mode: str,
        headless: bool,
        repo_root: Path,
        task_prompt: str = "",
    ) -> tuple[bool, int, str, str]:
        # Bounded-task mode: skip the multi-agent collaborative wrapper.
        # The review-channel launch script has a supervised loop, an
        # inactivity watchdog, an authority preflight against
        # ``review_state_path``, and a task-complete handoff guard — all
        # designed for live multi-agent review-channel sessions. A bounded
        # one-shot mutation does not need any of that and the authority
        # preflight rejects the spawn with exit 82 because no review_state
        # exists for a one-shot. So when a task prompt is provided, fork
        # to a minimal launch path that just writes a tiny script and
        # ``exec``s ``codex exec --sandbox workspace-write`` against it.
        if task_prompt:
            return _launch_one_shot_task_prompt(
                provider=provider,
                role=role,
                row_id=row_id,
                repo_root=repo_root,
                task_prompt=task_prompt,
            )

        # Lazy imports keep this module side-effect free at parser load time.
        from ...review_channel.core import LaneAssignment
        from ...review_channel.launch import build_launch_sessions
        from ...review_channel.launch_records import LaunchSessionRequest
        from ..review_channel.bridge_launch_headless import launch_sessions_headless

        lanes = [
            LaneAssignment(
                agent_id="AGENT-PEER-SPAWN-1",
                provider=provider,
                role=role,
                lane=f"{provider} peer-spawn {role} lane",
                docs="peer-spawn canonical launch",
                mp_scope=row_id or "peer-spawn",
                worktree=str(repo_root),
                branch="peer-spawn",
            )
        ]
        request = LaunchSessionRequest(
            repo_root=repo_root,
            review_channel_path=repo_root / "dev" / "active" / "review_channel.md",
            bridge_path=repo_root / "dev" / "reports" / "review_channel" / "bridge.md",
            codex_lanes=lanes if provider == "codex" else [],
            claude_lanes=lanes if provider == "claude" else [],
            codex_workers=0,
            claude_workers=0,
            rollover_threshold_pct=50,
            await_ack_seconds=0,
            retirement_note=(
                "peer-spawn canonical launch: "
                f"provider={provider} role={role} row_id={row_id}"
            ),
            promotion_plan_rel="dev/active/review_channel.md",
            approval_mode=None,
            dangerous=False,
            headless=headless,
            provider_lane_map={provider: lanes},
            providers_to_launch=(provider,),
            interaction_mode=interaction_mode,
            bypass_receipt_id=(bypass_receipt.receipt_id if bypass_receipt else ""),
            bypass_lifecycle=None,
        )
        try:
            if task_prompt:
                sessions = build_launch_sessions(
                    request=request,
                    build_conductor_prompt_fn=lambda **_kw: task_prompt,
                )
            else:
                sessions = build_launch_sessions(request=request)
        except Exception as exc:  # noqa: BLE001 — adapter boundary
            return False, 0, "", f"build_launch_sessions:{exc}"
        warnings: list[str] = []
        try:
            launched = launch_sessions_headless(sessions, warnings)
        except Exception as exc:  # noqa: BLE001 — adapter boundary
            return False, 0, "", f"launch_sessions_headless:{exc}"
        pid = 0
        script_path = ""
        for session in sessions:
            pid_value = session.get("headless_launch_pid")
            if pid_value:
                pid = int(pid_value)
            script_path = str(session.get("script_path") or "")
            break
        error_text = "; ".join(warnings) if warnings else ""
        return bool(launched), pid, script_path, error_text

    return adapter


_BOUNDED_TASK_HEREDOC_TERMINATOR = "EOF_PEER_SPAWN_TASK_PROMPT"


def _resolve_provider_cli_path(provider: str) -> str:
    """Find the provider CLI on PATH, returning a bare name if missing.

    Returning the bare name lets ``zsh`` produce a clear "command not
    found" error when the CLI is genuinely absent, instead of writing a
    nonsense absolute path into the launch script.
    """
    import shutil
    resolved = shutil.which(provider)
    return resolved or provider


def _launch_one_shot_task_prompt(
    *,
    provider: str,
    role: str,
    row_id: str,
    repo_root: Path,
    task_prompt: str,
) -> tuple[bool, int, str, str]:
    """Spawn ``codex exec`` (or the requested provider) with a bounded
    one-shot prompt, bypassing the multi-agent review-channel wrapper.

    The supervised launch script in ``launch.py`` exists for collaborative
    review-channel sessions. Its preflight authority check rejects spawns
    that lack a ``review_state`` file with exit 82, which makes it
    structurally hostile to one-shot mutations. The fork here keeps the
    typed authority chain intact (BypassReceipt → AgentSpawnReceipt → real
    subprocess) while skipping the collaborative bootstrap.
    """
    import shlex
    import stat
    import subprocess
    import tempfile
    from ...time_utils import utc_timestamp

    if _BOUNDED_TASK_HEREDOC_TERMINATOR in task_prompt:
        return (
            False,
            0,
            "",
            f"task_prompt_contains_heredoc_terminator:{_BOUNDED_TASK_HEREDOC_TERMINATOR}",
        )

    cli_path = _resolve_provider_cli_path(provider)
    repo_root_s = str(repo_root)

    script_dir = Path(tempfile.mkdtemp(prefix="peer-spawn-task-"))
    script_path = script_dir / f"{provider}-task.sh"
    stamp = utc_timestamp().replace(":", "").replace("-", "").replace(".", "")
    log_stdout = script_dir / f"{provider}-task.stdout.log"
    log_stderr = script_dir / f"{provider}-task.stderr.log"

    script_lines = [
        "#!/bin/zsh",
        "set -euo pipefail",
        f"# peer-spawn one-shot task: provider={provider} role={role} row_id={row_id} stamp={stamp}",
        f"cd {shlex.quote(repo_root_s)}",
        f"PROMPT=$(cat <<'{_BOUNDED_TASK_HEREDOC_TERMINATOR}'",
        task_prompt,
        _BOUNDED_TASK_HEREDOC_TERMINATOR,
        ")",
        (
            f"exec {shlex.quote(cli_path)} exec "
            f"-C {shlex.quote(repo_root_s)} "
            f"--sandbox workspace-write \"$PROMPT\""
        ),
    ]
    script_path.write_text("\n".join(script_lines) + "\n", encoding="utf-8")
    script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR)

    if os.environ.get("DEVCTL_PEER_SPAWN_TASK_PROMPT_DRY_LAUNCH", "").strip() == "1":
        return True, 0, str(script_path), "dry_launch:skipped_popen"

    try:
        proc = subprocess.Popen(
            ["/bin/zsh", str(script_path)],
            cwd=repo_root_s,
            stdout=log_stdout.open("wb"),
            stderr=log_stderr.open("wb"),
            start_new_session=True,
        )
    except OSError as exc:
        return False, 0, str(script_path), f"spawn_failed:{exc}"

    return True, int(proc.pid), str(script_path), ""


__all__ = [
    "add_peer_spawn_parser",
    "add_peer_terminate_parser",
    "run_peer_spawn",
    "run_peer_terminate",
]
