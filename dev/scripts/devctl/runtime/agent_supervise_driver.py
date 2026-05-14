"""Typed supervision driver for agent process exit and freeze detection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
import shlex
import subprocess
from typing import Protocol

from ..config import REPO_ROOT
from ..commands.rollout_tail.discovery import (
    default_sessions_root,
    discover_latest_session,
    resolve_session_file,
)
from .agent_spawn_authority import SpawnDeadAgentAction, compute_spawn_authority
from .agent_mind_projection_read import (
    agent_mind_latest_age_seconds,
    read_agent_mind_projection,
)
from .control_plane_daemons import pid_is_alive
from .goal_progress_receipt import resolve_goal_progress_receipt
from .governed_exception_base import json_ready_dict
from .lifetime_bypass_mode import BypassReceipt
from .value_coercion import coerce_int, coerce_mapping, coerce_string

AGENT_SUPERVISE_REPORT_CONTRACT_ID = "AgentSuperviseReport"
AGENT_SUPERVISE_REPORT_SCHEMA_VERSION = 1
AGENT_SUPERVISE_LAUNCH_RESULT_CONTRACT_ID = "AgentSuperviseLaunchResult"
AGENT_SUPERVISE_LAUNCH_RESULT_SCHEMA_VERSION = 1
DEFAULT_AGENT_SUPERVISE_STALENESS_SECONDS = 900


class AgentSuperviseLauncher(Protocol):
    """Callable boundary for launching an authorized replacement process."""

    def __call__(
        self,
        args: list[str],
        *,
        cwd: Path,
        stdin: int,
        stdout: int,
        stderr: int,
        start_new_session: bool,
    ) -> subprocess.Popen[object]:
        """Launch a replacement agent command."""


@dataclass(frozen=True, slots=True)
class AgentSuperviseInput:
    """Inputs for one supervision evaluation."""

    actor: str = "codex"
    provider: str = "codex"
    role: str = "reviewer"
    pid: int = 0
    session_id: str = ""
    session_path: Path | None = None
    sessions_root: Path | None = None
    repo_root: Path = REPO_ROOT
    review_state: Mapping[str, object] | None = None
    bypass_receipt: BypassReceipt | None = None
    staleness_threshold_seconds: int = DEFAULT_AGENT_SUPERVISE_STALENESS_SECONDS
    now_utc: datetime | None = None


@dataclass(frozen=True, slots=True)
class AgentSuperviseLaunchResult:
    """Typed result for the report-to-action supervision boundary."""

    status: str
    command: tuple[str, ...] = ()
    pid: int = 0
    reason: str = ""
    error: str = ""
    schema_version: int = AGENT_SUPERVISE_LAUNCH_RESULT_SCHEMA_VERSION
    contract_id: str = AGENT_SUPERVISE_LAUNCH_RESULT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return json_ready_dict(asdict(self))


@dataclass(frozen=True, slots=True)
class AgentSuperviseReport:
    """Machine-readable supervision decision."""

    status: str
    actor: str
    provider: str
    role: str
    process_state: str
    process_exit_detected: bool
    freeze_detected: bool
    session_path: str = ""
    session_id: str = ""
    rollout_mtime_age_seconds: int | None = None
    agent_mind_age_seconds: int | None = None
    activity_age_seconds: int = 0
    staleness_threshold_seconds: int = DEFAULT_AGENT_SUPERVISE_STALENESS_SECONDS
    continuation_anchor_live: bool = False
    continuation_anchor_packet_id: str = ""
    bypass_receipt_id: str = ""
    loop_autonomy_ok: bool | None = None
    trigger_reason: str = ""
    spawn_action: SpawnDeadAgentAction | None = None
    next_command: str = ""
    launch_result: AgentSuperviseLaunchResult | None = None
    blocked_reasons: tuple[str, ...] = ()
    schema_version: int = AGENT_SUPERVISE_REPORT_SCHEMA_VERSION
    contract_id: str = AGENT_SUPERVISE_REPORT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = json_ready_dict(asdict(self))
        if self.spawn_action is not None:
            payload["spawn_action"] = self.spawn_action.to_dict()
        if self.launch_result is not None:
            payload["launch_result"] = self.launch_result.to_dict()
        return payload


def evaluate_agent_supervision(inputs: AgentSuperviseInput) -> AgentSuperviseReport:
    """Return the typed supervision decision for one actor/session."""
    actor = coerce_string(inputs.actor) or "codex"
    provider = coerce_string(inputs.provider) or actor
    role = coerce_string(inputs.role) or "reviewer"
    threshold = max(
        0,
        int(inputs.staleness_threshold_seconds or DEFAULT_AGENT_SUPERVISE_STALENESS_SECONDS),
    )
    now = inputs.now_utc or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    now = now.astimezone(UTC)
    session_path = _resolve_session_path(
        provider=provider,
        session_id=inputs.session_id,
        session_path=inputs.session_path,
        sessions_root=inputs.sessions_root,
    )
    session_id = coerce_string(inputs.session_id) or (
        _session_id_from_path(session_path) if session_path is not None else ""
    )
    rollout_age_seconds = _mtime_age_seconds(session_path, now=now)
    mind_age_seconds = _agent_mind_age_seconds(
        inputs.repo_root,
        provider=provider,
    )
    activity_age_seconds = _activity_age_seconds(
        rollout_age_seconds=rollout_age_seconds,
        agent_mind_age_seconds=mind_age_seconds,
    )
    process_state = _process_state(
        inputs.pid,
        activity_age_seconds=activity_age_seconds,
        threshold=threshold,
    )
    process_exit_detected = process_state == "process_exited"
    freeze_detected = process_state in {
        "process_alive_activity_stale",
        "detached_runtime_only",
    }
    trigger_reason = _trigger_reason(
        process_exit_detected=process_exit_detected,
        freeze_detected=freeze_detected,
        age_seconds=activity_age_seconds,
        threshold=threshold,
    )

    review_state = coerce_mapping(inputs.review_state)
    goal_progress = resolve_goal_progress_receipt(review_state, actor=actor)
    anchor_id = goal_progress.continuation_anchor_packet_id
    continuation_anchor_live = bool(anchor_id)
    loop_autonomy = coerce_mapping(review_state.get("collaboration"))
    loop_autonomy_ok = (
        bool(loop_autonomy.get("loop_autonomy_ok"))
        if "loop_autonomy_ok" in loop_autonomy
        else None
    )
    bypass_receipt = inputs.bypass_receipt
    blocked = _blocked_reasons(
        trigger_reason=trigger_reason,
        continuation_anchor_live=continuation_anchor_live,
        bypass_receipt=bypass_receipt,
        loop_autonomy=loop_autonomy,
    )
    spawn_action: SpawnDeadAgentAction | None = None
    if trigger_reason and not blocked:
        effective_age = max(
            activity_age_seconds,
            threshold if process_exit_detected else activity_age_seconds,
        )
        spawn_action = compute_spawn_authority(
            target_actor_id=actor,
            target_role=role,
            agent_mind_cursor_age_seconds=effective_age,
            continuation_anchor_live=continuation_anchor_live,
            continuation_anchor_packet_id=anchor_id,
            bypass_receipt=bypass_receipt,
            loop_autonomy_state=loop_autonomy,
            staleness_threshold_seconds=threshold,
        )
        if spawn_action is None:
            blocked = ("spawn_authority_denied",)

    status = "healthy"
    next_command = ""
    if trigger_reason:
        if spawn_action is not None:
            status = "spawn_authorized"
            next_command = _launch_command(role=role)
        else:
            status = "blocked"
    return AgentSuperviseReport(
        status=status,
        actor=actor,
        provider=provider,
        role=role,
        process_state=process_state,
        process_exit_detected=process_exit_detected,
        freeze_detected=freeze_detected,
        session_path=str(session_path) if session_path is not None else "",
        session_id=session_id,
        rollout_mtime_age_seconds=rollout_age_seconds,
        agent_mind_age_seconds=mind_age_seconds,
        activity_age_seconds=activity_age_seconds,
        staleness_threshold_seconds=threshold,
        continuation_anchor_live=continuation_anchor_live,
        continuation_anchor_packet_id=anchor_id,
        bypass_receipt_id=bypass_receipt.receipt_id if bypass_receipt is not None else "",
        loop_autonomy_ok=loop_autonomy_ok,
        trigger_reason=trigger_reason,
        spawn_action=spawn_action,
        next_command=next_command,
        blocked_reasons=blocked,
    )


def execute_agent_supervision_spawn(
    report: AgentSuperviseReport,
    *,
    launcher: AgentSuperviseLauncher | None = None,
    cwd: Path = REPO_ROOT,
) -> AgentSuperviseReport:
    """Run the authorized replacement command and attach typed launch proof."""
    command = shlex.split(report.next_command)
    if report.spawn_action is None or not command:
        return replace(
            report,
            launch_result=AgentSuperviseLaunchResult(
                status="not_authorized",
                command=tuple(command),
                reason="spawn_action_missing",
            ),
        )
    launch = launcher or subprocess.Popen
    try:
        process = launch(
            command,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        return replace(
            report,
            launch_result=AgentSuperviseLaunchResult(
                status="spawn_failed",
                command=tuple(command),
                reason="subprocess_launch_failed",
                error=str(exc),
            ),
        )
    return replace(
        report,
        launch_result=AgentSuperviseLaunchResult(
            status="spawned",
            command=tuple(command),
            pid=int(getattr(process, "pid", 0) or 0),
            reason=report.spawn_action.reason,
        ),
    )


def _resolve_session_path(
    *,
    provider: str,
    session_id: str,
    session_path: Path | None,
    sessions_root: Path | None,
) -> Path | None:
    if session_path is not None:
        return session_path
    if coerce_string(session_id):
        return resolve_session_file(
            provider,
            session_id=session_id,
            root=sessions_root or default_sessions_root(provider),
        )
    return discover_latest_session(
        provider,
        root=sessions_root or default_sessions_root(provider),
    )


def _session_id_from_path(path: Path | None) -> str:
    if path is None:
        return ""
    stem = path.stem
    if stem.startswith("rollout-"):
        parts = stem.split("-")
        if len(parts) >= 6:
            return "-".join(parts[-5:])
    return stem


def _mtime_age_seconds(path: Path | None, *, now: datetime) -> int | None:
    if path is None:
        return None
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    except OSError:
        return None
    return max(0, int((now - mtime).total_seconds()))


def _agent_mind_age_seconds(repo_root: Path, *, provider: str) -> int | None:
    age = agent_mind_latest_age_seconds(
        read_agent_mind_projection(repo_root, provider=provider)
    )
    if age is None:
        return None
    return max(0, int(age))


def _activity_age_seconds(
    *,
    rollout_age_seconds: int | None,
    agent_mind_age_seconds: int | None,
) -> int:
    ages = []
    if rollout_age_seconds is not None:
        ages.append(rollout_age_seconds)
    if agent_mind_age_seconds is not None:
        ages.append(agent_mind_age_seconds)
    return min(ages) if ages else 0


def _process_state(
    pid: int,
    *,
    activity_age_seconds: int,
    threshold: int,
) -> str:
    if pid <= 0:
        if activity_age_seconds >= threshold:
            return "detached_runtime_only"
        return "alive"
    if not pid_is_alive(pid):
        return "process_exited"
    if activity_age_seconds >= threshold:
        return "process_alive_activity_stale"
    return "alive"


def _trigger_reason(
    *,
    process_exit_detected: bool,
    freeze_detected: bool,
    age_seconds: int,
    threshold: int,
) -> str:
    if process_exit_detected:
        return "process_exit_detected"
    if freeze_detected:
        return f"freeze_detected:{age_seconds}s>=threshold:{threshold}s"
    return ""


def _blocked_reasons(
    *,
    trigger_reason: str,
    continuation_anchor_live: bool,
    bypass_receipt: BypassReceipt | None,
    loop_autonomy: Mapping[str, object],
) -> tuple[str, ...]:
    if not trigger_reason:
        return ()
    reasons: list[str] = []
    if not continuation_anchor_live:
        reasons.append("continuation_anchor_not_live")
    if bypass_receipt is None:
        reasons.append("bypass_receipt_missing")
    if "loop_autonomy_ok" in loop_autonomy and not bool(
        loop_autonomy.get("loop_autonomy_ok")
    ):
        reasons.append("loop_autonomy_not_green")
    return tuple(reasons)


def _launch_command(*, role: str) -> str:
    normalized_role = role or "reviewer"
    policy_hint = " --policy-hint review_only" if normalized_role == "reviewer" else ""
    return (
        "python3 dev/scripts/devctl.py review-channel --action launch "
        f"--remote-role {normalized_role}{policy_hint} --terminal none --format md"
    )


__all__ = [
    "AGENT_SUPERVISE_LAUNCH_RESULT_CONTRACT_ID",
    "AGENT_SUPERVISE_LAUNCH_RESULT_SCHEMA_VERSION",
    "AGENT_SUPERVISE_REPORT_CONTRACT_ID",
    "AGENT_SUPERVISE_REPORT_SCHEMA_VERSION",
    "DEFAULT_AGENT_SUPERVISE_STALENESS_SECONDS",
    "AgentSuperviseInput",
    "AgentSuperviseLaunchResult",
    "AgentSuperviseLauncher",
    "AgentSuperviseReport",
    "execute_agent_supervision_spawn",
    "evaluate_agent_supervision",
]
