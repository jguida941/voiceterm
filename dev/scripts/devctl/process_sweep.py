"""Shared process-sweep helpers used by `devctl check` and `devctl hygiene`.

Why this exists:
- `cargo test` runs can be interrupted (Ctrl+C, terminal close, crashed shell)
- sometimes `cargo test` appears to "hang" and people force-stop it, which has
  the same orphan-process risk as a normal interrupt
- interrupted runs can leave detached `voiceterm-*` test binaries alive
- both orphaned and stale long-running test processes can keep using CPU/memory
  and make later runs flaky
- `check` uses this to clean before/after runs; `hygiene` uses it to report leaks
- this cleanup applies to local dev runs and AI-agent runs so one stuck test does
  not silently impact everyone else sharing the repo/worktree
- one shared implementation keeps the same cleanup/report rules for devs and AI
"""

from __future__ import annotations

import os
import re
import signal
import subprocess
from typing import Pattern

PROCESS_SWEEP_CMD = ["ps", "-axo", "pid=,ppid=,etime=,command="]
DEFAULT_ORPHAN_MIN_AGE_SECONDS = 60
DEFAULT_STALE_MIN_AGE_SECONDS = 600
# Match both full-path and basename launch styles:
# - /tmp/.../target/debug/deps/voiceterm-deadbeef --test-threads=4
# - voiceterm-deadbeef --nocapture
VOICETERM_TEST_BINARY_RE = re.compile(r"(?:^|/|\s)voiceterm-[0-9a-f]{8,}(?:\s|$)")


def parse_etime_seconds(raw: str) -> int | None:
    """Convert `ps etime` text into seconds so age checks are easy."""
    trimmed = raw.strip()
    if not trimmed:
        return None

    days = 0
    rest = trimmed
    if "-" in trimmed:
        day_part, rest = trimmed.split("-", 1)
        if not day_part.isdigit():
            return None
        days = int(day_part)

    chunks = rest.split(":")
    if len(chunks) == 2:
        mm, ss = chunks
        if not (mm.isdigit() and ss.isdigit()):
            return None
        seconds = int(mm) * 60 + int(ss)
    elif len(chunks) == 3:
        hh, mm, ss = chunks
        if not (hh.isdigit() and mm.isdigit() and ss.isdigit()):
            return None
        seconds = int(hh) * 3600 + int(mm) * 60 + int(ss)
    else:
        return None

    return days * 86400 + seconds


def scan_matching_processes(command_regex: Pattern[str], *, skip_pid: int | None = None) -> tuple[list[dict], list[str]]:
    """Read `ps` output and return rows whose command matches `command_regex`."""
    warnings: list[str] = []
    try:
        result = subprocess.run(
            PROCESS_SWEEP_CMD,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        warnings.append(f"Process sweep skipped: unable to execute ps ({exc})")
        return [], warnings

    if result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else "unknown ps error"
        warnings.append(f"Process sweep skipped: ps returned {result.returncode} ({stderr})")
        return [], warnings

    this_pid = os.getpid() if skip_pid is None else skip_pid
    rows: list[dict] = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(None, 3)
        if len(parts) != 4:
            continue
        pid_raw, ppid_raw, etime, command = parts
        if not (pid_raw.isdigit() and ppid_raw.isdigit()):
            continue
        if "ps -axo pid=,ppid=,etime=,command=" in command:
            continue
        if not command_regex.search(command):
            continue

        pid = int(pid_raw)
        if pid == this_pid:
            continue

        elapsed = parse_etime_seconds(etime)
        rows.append(
            {
                "pid": pid,
                "ppid": int(ppid_raw),
                "etime": etime,
                "elapsed_seconds": elapsed if elapsed is not None else -1,
                "command": command,
            }
        )

    rows.sort(key=lambda row: row["elapsed_seconds"], reverse=True)
    return rows, warnings


def scan_voiceterm_test_binaries(*, skip_pid: int | None = None) -> tuple[list[dict], list[str]]:
    """Return process rows for VoiceTerm test binaries using canonical matching."""
    return scan_matching_processes(VOICETERM_TEST_BINARY_RE, skip_pid=skip_pid)


def split_orphaned_processes(
    rows: list[dict], *, min_age_seconds: int = DEFAULT_ORPHAN_MIN_AGE_SECONDS
) -> tuple[list[dict], list[dict]]:
    """Split rows into `orphaned` vs `active` using PPID=1 + minimum age."""
    orphaned = [
        row
        for row in rows
        if row["ppid"] == 1 and row["elapsed_seconds"] >= min_age_seconds
    ]
    active = [row for row in rows if row not in orphaned]
    return orphaned, active


def split_stale_processes(
    rows: list[dict], *, min_age_seconds: int = DEFAULT_STALE_MIN_AGE_SECONDS
) -> tuple[list[dict], list[dict]]:
    """Split rows into `stale` vs `recent` using elapsed runtime age."""
    stale = [
        row
        for row in rows
        if row["elapsed_seconds"] >= 0 and row["elapsed_seconds"] >= min_age_seconds
    ]
    recent = [row for row in rows if row not in stale]
    return stale, recent


def kill_processes(rows: list[dict], *, kill_signal: int = signal.SIGKILL) -> tuple[list[int], list[str]]:
    """Best-effort kill for rows we already decided are safe to stop."""
    killed_pids: list[int] = []
    warnings: list[str] = []
    for row in rows:
        pid = row["pid"]
        try:
            os.kill(pid, kill_signal)
            killed_pids.append(pid)
        except ProcessLookupError:
            continue
        except PermissionError as exc:
            warnings.append(f"pid={pid} permission denied ({exc})")
        except OSError as exc:
            warnings.append(f"pid={pid} kill failed ({exc})")
    return killed_pids, warnings


def format_process_rows(rows: list[dict], *, line_max_len: int = 180, row_limit: int = 8) -> str:
    """Render short process summaries for human-readable warnings/errors."""

    def truncate(command: str) -> str:
        if len(command) <= line_max_len:
            return command
        return command[: line_max_len - 3] + "..."

    return "; ".join(
        f"pid={row['pid']} ppid={row['ppid']} etime={row['etime']} cmd={truncate(row['command'])}"
        for row in rows[:row_limit]
    )
