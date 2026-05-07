"""Headless launch support with typed proof-of-life for terminal=none sessions.

Extracted from bridge_launch_control.py to stay under the code-shape soft limit.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from ...runtime.enum_compat import StrEnum

_HEADLESS_PROOF_OF_LIFE_WAIT = 0.3
_HEADLESS_PROOF_OF_LIFE_POLLS = 3


class HeadlessLaunchStatus(StrEnum):
    """Typed result of a headless session launch attempt."""

    ALIVE = "alive"                # PID confirmed alive after launch
    PROVIDER_NOT_OBSERVED = "provider_not_observed"  # wrapper alive, provider absent
    DEAD_ON_ARRIVAL = "dead_on_arrival"  # PID died immediately
    SPAWN_FAILED = "spawn_failed"  # subprocess.Popen raised an error
    SCRIPT_MISSING = "script_missing"  # launch script not found


@dataclass(frozen=True, slots=True)
class HeadlessLaunchResult:
    """Proof-of-life outcome for one headless session launch."""

    status: HeadlessLaunchStatus
    pid: int | None = None
    script_path: str = ""
    detail: str = ""


def launch_sessions_headless(
    sessions: list[dict[str, object]],
    warnings: list[str],
) -> bool:
    """Start conductor sessions as detached background processes (no GUI).

    Each session has a ``launch_command`` pointing at a shell script that
    already handles supervised restart.  This path spawns each script in a
    new process group so it survives the parent daemon exiting.

    After spawning, each process is polled for proof-of-life. A process
    that dies immediately is reported as dead_on_arrival instead of
    being silently treated as a healthy launch.
    """
    results = _launch_and_verify_sessions(sessions)
    any_alive = False
    for result in results:
        _attach_headless_launch_result(sessions, result)
        if result.status == HeadlessLaunchStatus.ALIVE:
            any_alive = True
        elif result.status == HeadlessLaunchStatus.DEAD_ON_ARRIVAL:
            warnings.append(
                f"Headless launch proof-of-life failed: PID {result.pid} "
                f"died immediately after spawn ({result.script_path})"
            )
        elif result.status == HeadlessLaunchStatus.PROVIDER_NOT_OBSERVED:
            warnings.append(
                "Headless launch proof-of-life failed: wrapper PID "
                f"{result.pid} survived, but no provider process was observed "
                f"under it ({result.script_path}). {result.detail}".strip()
            )
        elif result.status == HeadlessLaunchStatus.SPAWN_FAILED:
            warnings.append(
                f"Headless launch failed for {result.script_path}: "
                f"{result.detail}"
            )
        elif result.status == HeadlessLaunchStatus.SCRIPT_MISSING:
            warnings.append(
                f"Headless launch skipped: script not found at "
                f"{result.script_path}"
            )
    return any_alive


def _attach_headless_launch_result(
    sessions: list[dict[str, object]],
    result: HeadlessLaunchResult,
) -> None:
    for session in sessions:
        if str(session.get("script_path") or "").strip() != result.script_path:
            continue
        session["headless_launch_status"] = str(result.status)
        if result.pid is not None:
            session["headless_launch_pid"] = result.pid
        break


def _launch_and_verify_sessions(
    sessions: list[dict[str, object]],
) -> list[HeadlessLaunchResult]:
    """Spawn each session and verify proof-of-life via PID polling."""
    results: list[HeadlessLaunchResult] = []
    for session in sessions:
        result = spawn_one_headless_session(session)
        results.append(result)
    return results


def spawn_one_headless_session(
    session: dict[str, object],
) -> HeadlessLaunchResult:
    """Spawn a single headless session and verify its PID is alive."""
    script_path = str(session.get("script_path") or "").strip()
    if not script_path or not Path(script_path).is_file():
        return HeadlessLaunchResult(
            status=HeadlessLaunchStatus.SCRIPT_MISSING,
            script_path=script_path,
        )
    log_path_str = str(session.get("log_path") or "").strip()
    log_handle = None
    try:
        if log_path_str:
            log_path = Path(log_path_str)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_handle = log_path.open("a", encoding="utf-8")
        process = subprocess.Popen(
            ["/bin/zsh", script_path],
            cwd=str(Path(script_path).parent),
            stdout=log_handle or subprocess.DEVNULL,
            stderr=log_handle or subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        if log_handle is not None:
            log_handle.close()
        return HeadlessLaunchResult(
            status=HeadlessLaunchStatus.SPAWN_FAILED,
            script_path=script_path,
            detail=str(exc),
        )
    # Proof-of-life: poll the PID to verify the process survived startup
    if _pid_survived_startup(process.pid):
        provider = str(session.get("provider") or "").strip().lower()
        if provider and not _provider_process_observed(process.pid, provider):
            return HeadlessLaunchResult(
                status=HeadlessLaunchStatus.PROVIDER_NOT_OBSERVED,
                pid=process.pid,
                script_path=script_path,
                detail=f"expected_provider={provider}",
            )
        return HeadlessLaunchResult(
            status=HeadlessLaunchStatus.ALIVE,
            pid=process.pid,
            script_path=script_path,
        )
    return HeadlessLaunchResult(
        status=HeadlessLaunchStatus.DEAD_ON_ARRIVAL,
        pid=process.pid,
        script_path=script_path,
    )


def _pid_survived_startup(pid: int) -> bool:
    """Poll a PID briefly to verify it survived initial startup."""
    for _ in range(_HEADLESS_PROOF_OF_LIFE_POLLS):
        time.sleep(_HEADLESS_PROOF_OF_LIFE_WAIT)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True  # process exists but we lack permission to signal
    return True


def _provider_process_observed(root_pid: int, provider: str) -> bool:
    """Return True when the launched wrapper has a live provider descendant."""
    if provider not in {"claude", "codex", "cursor"}:
        return True
    table = _process_table()
    if not table:
        return True
    descendants = {root_pid, *_descendant_pids(root_pid, table)}
    for pid in descendants:
        command = table.get(pid, (0, ""))[1]
        if _command_invokes_provider(command, provider):
            return True
    return False


def _command_invokes_provider(command: str, provider: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    for part in parts:
        if Path(part).name == provider:
            return True
    return False


def _process_table() -> dict[int, tuple[int, str]]:
    try:
        result = subprocess.run(
            ["ps", "-axo", "pid=,ppid=,command="],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    if result.returncode != 0:
        return {}
    rows: dict[int, tuple[int, str]] = {}
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) < 2:
            continue
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
        except ValueError:
            continue
        rows[pid] = (ppid, parts[2] if len(parts) > 2 else "")
    return rows


def _descendant_pids(
    root_pid: int,
    table: dict[int, tuple[int, str]],
) -> set[int]:
    descendants: set[int] = set()
    frontier = [root_pid]
    while frontier:
        parent = frontier.pop()
        for pid, (ppid, _command) in table.items():
            if ppid != parent or pid in descendants:
                continue
            descendants.add(pid)
            frontier.append(pid)
    return descendants
