"""Concurrent job lifecycle state for the Operator Console jobs package.

Provides a bounded-concurrency job queue that tracks command, context,
stdout/stderr, exit status, and timing for every submitted job.

This module is PyQt-free. The caller still owns QProcess creation and
promotion of queued jobs into running processes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
import itertools


class JobStatus(Enum):
    """Lifecycle states for a managed job."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobRecord:
    """Mutable lifecycle record for one command execution."""

    job_id: str
    command: list[str]
    label: str
    context: dict[str, object] = field(default_factory=dict)
    status: JobStatus = JobStatus.QUEUED
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    created_at: float = field(default_factory=monotonic)
    started_at: float | None = None
    finished_at: float | None = None

    @property
    def is_terminal(self) -> bool:
        """Whether this job has reached a final state."""
        return self.status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        )

    @property
    def duration_seconds(self) -> float | None:
        """Wall-clock duration if started, else None."""
        if self.started_at is None:
            return None
        end = self.finished_at if self.finished_at is not None else monotonic()
        return end - self.started_at

    def summary_line(self) -> str:
        """One-line status for display in job lists."""
        status_tag = self.status.value.upper()
        duration = self.duration_seconds
        dur_text = f" ({duration:.1f}s)" if duration is not None else ""
        exit_text = f" exit={self.exit_code}" if self.exit_code is not None else ""
        return f"[{status_tag}]{dur_text}{exit_text} {self.label}"


class JobManager:
    """Bounded-concurrency job queue with history.

    Manages lifecycle state only — the caller is responsible for creating
    actual OS processes (QProcess, subprocess, etc.) and calling the
    ``mark_*`` / ``append_output`` methods as events arrive.

    Parameters
    ----------
    max_concurrent:
        Maximum number of jobs that may be in RUNNING state simultaneously.
    history_limit:
        Maximum number of terminal jobs to retain in history.
    """

    def __init__(
        self,
        *,
        max_concurrent: int = 3,
        history_limit: int = 50,
    ) -> None:
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be >= 1")
        self._max_concurrent = max_concurrent
        self._history_limit = history_limit
        self._jobs: dict[str, JobRecord] = {}
        self._queue: list[str] = []
        self._running: set[str] = set()
        self._counter = itertools.count(1)

    # ── Properties ──────────────────────────────────────────────

    @property
    def max_concurrent(self) -> int:
        return self._max_concurrent

    # ── Job submission ──────────────────────────────────────────

    def submit(
        self,
        command: list[str],
        *,
        label: str = "",
        context: dict[str, object] | None = None,
    ) -> str:
        """Create a new job and add it to the queue.

        Returns the ``job_id``. The job starts in QUEUED status.
        Call ``next_ready()`` to check whether it can be promoted to RUNNING.
        """
        job_id = f"job-{next(self._counter)}"
        record = JobRecord(
            job_id=job_id,
            command=list(command),
            label=label or _default_label(command),
            context=dict(context) if context else {},
        )
        self._jobs[job_id] = record
        self._queue.append(job_id)
        return job_id

    # ── Lifecycle transitions ───────────────────────────────────

    def mark_running(self, job_id: str) -> None:
        """Transition a QUEUED job to RUNNING."""
        record = self._require(job_id)
        if record.status != JobStatus.QUEUED:
            raise ValueError(
                f"Cannot mark {job_id} running: status is {record.status.value}"
            )
        record.status = JobStatus.RUNNING
        record.started_at = monotonic()
        if job_id in self._queue:
            self._queue.remove(job_id)
        self._running.add(job_id)

    def mark_finished(
        self,
        job_id: str,
        *,
        exit_code: int,
    ) -> None:
        """Transition a RUNNING job to COMPLETED or FAILED based on exit_code."""
        record = self._require(job_id)
        if record.status != JobStatus.RUNNING:
            raise ValueError(
                f"Cannot finish {job_id}: status is {record.status.value}"
            )
        record.exit_code = exit_code
        record.status = JobStatus.COMPLETED if exit_code == 0 else JobStatus.FAILED
        record.finished_at = monotonic()
        self._running.discard(job_id)
        self._trim_history()

    def mark_cancelled(self, job_id: str) -> None:
        """Cancel a QUEUED or RUNNING job."""
        record = self._require(job_id)
        if record.is_terminal:
            return
        record.status = JobStatus.CANCELLED
        record.finished_at = monotonic()
        if job_id in self._queue:
            self._queue.remove(job_id)
        self._running.discard(job_id)

    # ── Output accumulation ─────────────────────────────────────

    def append_stdout(self, job_id: str, text: str) -> None:
        """Append text to a running job's stdout buffer."""
        record = self._require(job_id)
        record.stdout += text

    def append_stderr(self, job_id: str, text: str) -> None:
        """Append text to a running job's stderr buffer."""
        record = self._require(job_id)
        record.stderr += text

    # ── Scheduling queries ──────────────────────────────────────

    def can_start(self) -> bool:
        """Whether we're below the concurrency limit."""
        return len(self._running) < self._max_concurrent

    def has_queued(self) -> bool:
        """Whether any jobs are waiting to run."""
        return len(self._queue) > 0

    def next_ready(self) -> str | None:
        """Return the next queued job_id that can start, or None.

        Does NOT transition the job — call ``mark_running()`` after
        creating the OS process.
        """
        if not self.can_start() or not self._queue:
            return None
        return self._queue[0]

    def drain_ready(self) -> list[str]:
        """Return all queued job_ids that can start now."""
        ready: list[str] = []
        available_slots = self._max_concurrent - len(self._running)
        for index in range(min(available_slots, len(self._queue))):
            ready.append(self._queue[index])
        return ready

    # ── Lookups ─────────────────────────────────────────────────

    def get(self, job_id: str) -> JobRecord | None:
        """Return a job record by id, or None."""
        record = self._jobs.get(job_id)
        return record

    def running_jobs(self) -> list[JobRecord]:
        """All jobs currently in RUNNING state, oldest first."""
        running_records = [
            self._jobs[jid] for jid in self._running if jid in self._jobs
        ]
        running_records.sort(
            key=lambda record: (
                record.started_at if record.started_at is not None else record.created_at,
                record.job_id,
            )
        )
        return running_records

    def running_count(self) -> int:
        """Number of currently running jobs."""
        count = len(self._running)
        return count

    def queued_jobs(self) -> list[JobRecord]:
        """All jobs currently in QUEUED state, in queue order."""
        return [self._jobs[jid] for jid in self._queue if jid in self._jobs]

    def queued_count(self) -> int:
        """Number of jobs waiting to run."""
        count = len(self._queue)
        return count

    def history(self, *, limit: int | None = None) -> list[JobRecord]:
        """Terminal jobs (completed/failed/cancelled), newest first."""
        terminal = [
            record
            for record in self._jobs.values()
            if record.is_terminal
        ]
        terminal.sort(
            key=lambda r: r.finished_at or 0.0,
            reverse=True,
        )
        if limit is not None:
            return terminal[:limit]
        return terminal

    def all_jobs(self) -> list[JobRecord]:
        """All jobs in submission order."""
        jobs = list(self._jobs.values())
        return jobs

    def is_any_running(self) -> bool:
        """Whether any job is currently running."""
        return len(self._running) > 0

    def active_job_for_context(
        self, key: str, value: object
    ) -> JobRecord | None:
        """Find a running job whose context matches ``context[key] == value``."""
        for jid in self._running:
            record = self._jobs.get(jid)
            if record is not None and record.context.get(key) == value:
                return record
        return None

    # ── Internals ───────────────────────────────────────────────

    def _require(self, job_id: str) -> JobRecord:
        record = self._jobs.get(job_id)
        if record is None:
            raise KeyError(f"Unknown job: {job_id}")
        return record

    def _trim_history(self) -> None:
        """Remove the oldest terminal jobs beyond the history limit."""
        terminal = [
            (jid, record)
            for jid, record in self._jobs.items()
            if record.is_terminal
        ]
        if len(terminal) <= self._history_limit:
            return
        terminal.sort(key=lambda pair: pair[1].finished_at or 0.0)
        excess = len(terminal) - self._history_limit
        for jid, _ in terminal[:excess]:
            del self._jobs[jid]


def _default_label(command: list[str]) -> str:
    """Derive a short label from a command list."""
    if not command:
        return "Command"
    basename = command[0].rsplit("/", 1)[-1]
    if len(command) > 1:
        return f"{basename} {command[1]}"
    return basename
