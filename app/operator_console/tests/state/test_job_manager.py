"""Tests for app.operator_console.state.job_manager."""

from __future__ import annotations

import pytest

from app.operator_console.state.job_manager import (
    JobManager,
    JobRecord,
    JobStatus,
    _default_label,
)


# ── JobRecord ───────────────────────────────────────────────────


class TestJobRecord:
    def test_initial_state(self):
        record = JobRecord(
            job_id="j-1",
            command=["echo", "hello"],
            label="Echo",
        )
        assert record.status == JobStatus.QUEUED
        assert record.exit_code is None
        assert record.stdout == ""
        assert record.stderr == ""
        assert record.started_at is None
        assert record.finished_at is None
        assert record.is_terminal is False
        assert record.duration_seconds is None

    def test_is_terminal_for_completed(self):
        record = JobRecord(
            job_id="j-1",
            command=["ls"],
            label="List",
            status=JobStatus.COMPLETED,
        )
        assert record.is_terminal is True

    def test_is_terminal_for_failed(self):
        record = JobRecord(
            job_id="j-1",
            command=["ls"],
            label="List",
            status=JobStatus.FAILED,
        )
        assert record.is_terminal is True

    def test_is_terminal_for_cancelled(self):
        record = JobRecord(
            job_id="j-1",
            command=["ls"],
            label="List",
            status=JobStatus.CANCELLED,
        )
        assert record.is_terminal is True

    def test_is_terminal_for_running(self):
        record = JobRecord(
            job_id="j-1",
            command=["ls"],
            label="List",
            status=JobStatus.RUNNING,
        )
        assert record.is_terminal is False

    def test_duration_when_running(self):
        record = JobRecord(
            job_id="j-1",
            command=["ls"],
            label="List",
            status=JobStatus.RUNNING,
            started_at=100.0,
        )
        duration = record.duration_seconds
        assert duration is not None
        assert duration >= 0.0

    def test_duration_when_finished(self):
        record = JobRecord(
            job_id="j-1",
            command=["ls"],
            label="List",
            status=JobStatus.COMPLETED,
            started_at=100.0,
            finished_at=105.5,
        )
        assert record.duration_seconds == pytest.approx(5.5)

    def test_summary_line_queued(self):
        record = JobRecord(
            job_id="j-1",
            command=["ls"],
            label="List Files",
        )
        line = record.summary_line()
        assert "[QUEUED]" in line
        assert "List Files" in line

    def test_summary_line_completed(self):
        record = JobRecord(
            job_id="j-1",
            command=["ls"],
            label="List Files",
            status=JobStatus.COMPLETED,
            exit_code=0,
            started_at=100.0,
            finished_at=102.3,
        )
        line = record.summary_line()
        assert "[COMPLETED]" in line
        assert "exit=0" in line
        assert "2.3s" in line

    def test_summary_line_failed(self):
        record = JobRecord(
            job_id="j-1",
            command=["false"],
            label="Fail",
            status=JobStatus.FAILED,
            exit_code=1,
            started_at=100.0,
            finished_at=100.1,
        )
        line = record.summary_line()
        assert "[FAILED]" in line
        assert "exit=1" in line


# ── JobManager submission ───────────────────────────────────────


class TestJobManagerSubmit:
    def test_submit_returns_unique_ids(self):
        mgr = JobManager()
        id1 = mgr.submit(["echo", "a"])
        id2 = mgr.submit(["echo", "b"])
        assert id1 != id2
        assert id1.startswith("job-")
        assert id2.startswith("job-")

    def test_submit_creates_queued_record(self):
        mgr = JobManager()
        jid = mgr.submit(["ls", "-la"], label="List", context={"flow": "test"})
        record = mgr.get(jid)
        assert record is not None
        assert record.status == JobStatus.QUEUED
        assert record.command == ["ls", "-la"]
        assert record.label == "List"
        assert record.context == {"flow": "test"}

    def test_submit_uses_default_label(self):
        mgr = JobManager()
        jid = mgr.submit(["/usr/bin/python3", "devctl.py"])
        record = mgr.get(jid)
        assert record is not None
        assert record.label == "python3 devctl.py"

    def test_submit_adds_to_queue(self):
        mgr = JobManager()
        jid = mgr.submit(["echo"])
        assert mgr.queued_count() == 1
        assert mgr.queued_jobs()[0].job_id == jid


# ── Lifecycle transitions ───────────────────────────────────────


class TestJobManagerLifecycle:
    def test_mark_running_transitions_from_queued(self):
        mgr = JobManager()
        jid = mgr.submit(["echo"])
        mgr.mark_running(jid)
        record = mgr.get(jid)
        assert record.status == JobStatus.RUNNING
        assert record.started_at is not None
        assert mgr.running_count() == 1
        assert mgr.queued_count() == 0

    def test_mark_running_rejects_non_queued(self):
        mgr = JobManager()
        jid = mgr.submit(["echo"])
        mgr.mark_running(jid)
        with pytest.raises(ValueError, match="Cannot mark"):
            mgr.mark_running(jid)

    def test_mark_finished_success(self):
        mgr = JobManager()
        jid = mgr.submit(["echo"])
        mgr.mark_running(jid)
        mgr.mark_finished(jid, exit_code=0)
        record = mgr.get(jid)
        assert record.status == JobStatus.COMPLETED
        assert record.exit_code == 0
        assert record.finished_at is not None
        assert mgr.running_count() == 0

    def test_mark_finished_failure(self):
        mgr = JobManager()
        jid = mgr.submit(["false"])
        mgr.mark_running(jid)
        mgr.mark_finished(jid, exit_code=1)
        record = mgr.get(jid)
        assert record.status == JobStatus.FAILED
        assert record.exit_code == 1

    def test_mark_finished_rejects_non_running(self):
        mgr = JobManager()
        jid = mgr.submit(["echo"])
        with pytest.raises(ValueError, match="Cannot finish"):
            mgr.mark_finished(jid, exit_code=0)

    def test_mark_cancelled_from_queued(self):
        mgr = JobManager()
        jid = mgr.submit(["echo"])
        mgr.mark_cancelled(jid)
        record = mgr.get(jid)
        assert record.status == JobStatus.CANCELLED
        assert record.finished_at is not None
        assert mgr.queued_count() == 0

    def test_mark_cancelled_from_running(self):
        mgr = JobManager()
        jid = mgr.submit(["echo"])
        mgr.mark_running(jid)
        mgr.mark_cancelled(jid)
        record = mgr.get(jid)
        assert record.status == JobStatus.CANCELLED
        assert mgr.running_count() == 0

    def test_mark_cancelled_is_idempotent_on_terminal(self):
        mgr = JobManager()
        jid = mgr.submit(["echo"])
        mgr.mark_running(jid)
        mgr.mark_finished(jid, exit_code=0)
        mgr.mark_cancelled(jid)  # should not raise
        assert mgr.get(jid).status == JobStatus.COMPLETED  # unchanged

    def test_unknown_job_id_raises_keyerror(self):
        mgr = JobManager()
        with pytest.raises(KeyError, match="Unknown job"):
            mgr.mark_running("nonexistent")


# ── Output accumulation ─────────────────────────────────────────


class TestJobManagerOutput:
    def test_append_stdout(self):
        mgr = JobManager()
        jid = mgr.submit(["echo"])
        mgr.mark_running(jid)
        mgr.append_stdout(jid, "hello ")
        mgr.append_stdout(jid, "world\n")
        assert mgr.get(jid).stdout == "hello world\n"

    def test_append_stderr(self):
        mgr = JobManager()
        jid = mgr.submit(["echo"])
        mgr.mark_running(jid)
        mgr.append_stderr(jid, "error: ")
        mgr.append_stderr(jid, "oops\n")
        assert mgr.get(jid).stderr == "error: oops\n"


# ── Concurrency and scheduling ──────────────────────────────────


class TestJobManagerConcurrency:
    def test_can_start_respects_limit(self):
        mgr = JobManager(max_concurrent=2)
        assert mgr.can_start() is True

        j1 = mgr.submit(["a"])
        mgr.mark_running(j1)
        assert mgr.can_start() is True

        j2 = mgr.submit(["b"])
        mgr.mark_running(j2)
        assert mgr.can_start() is False

    def test_finishing_frees_slot(self):
        mgr = JobManager(max_concurrent=1)
        j1 = mgr.submit(["a"])
        mgr.mark_running(j1)
        assert mgr.can_start() is False

        mgr.mark_finished(j1, exit_code=0)
        assert mgr.can_start() is True

    def test_next_ready_returns_none_at_capacity(self):
        mgr = JobManager(max_concurrent=1)
        j1 = mgr.submit(["a"])
        mgr.mark_running(j1)
        mgr.submit(["b"])
        assert mgr.next_ready() is None

    def test_next_ready_returns_first_queued(self):
        mgr = JobManager(max_concurrent=2)
        j1 = mgr.submit(["a"])
        j2 = mgr.submit(["b"])
        assert mgr.next_ready() == j1

    def test_next_ready_returns_none_when_empty(self):
        mgr = JobManager()
        assert mgr.next_ready() is None

    def test_drain_ready_returns_multiple(self):
        mgr = JobManager(max_concurrent=3)
        j1 = mgr.submit(["a"])
        j2 = mgr.submit(["b"])
        j3 = mgr.submit(["c"])
        j4 = mgr.submit(["d"])
        ready = mgr.drain_ready()
        assert len(ready) == 3
        assert ready == [j1, j2, j3]

    def test_drain_ready_respects_running_count(self):
        mgr = JobManager(max_concurrent=2)
        j1 = mgr.submit(["a"])
        mgr.mark_running(j1)
        j2 = mgr.submit(["b"])
        j3 = mgr.submit(["c"])
        ready = mgr.drain_ready()
        assert len(ready) == 1
        assert ready == [j2]

    def test_max_concurrent_validation(self):
        with pytest.raises(ValueError, match="max_concurrent"):
            JobManager(max_concurrent=0)


# ── Lookups and history ─────────────────────────────────────────


class TestJobManagerLookups:
    def test_get_returns_none_for_unknown(self):
        mgr = JobManager()
        assert mgr.get("nonexistent") is None

    def test_running_jobs_returns_sorted(self):
        mgr = JobManager(max_concurrent=3)
        j1 = mgr.submit(["a"])
        j2 = mgr.submit(["b"])
        mgr.mark_running(j1)
        mgr.mark_running(j2)
        running = mgr.running_jobs()
        assert len(running) == 2
        assert running[0].job_id == j1
        assert running[1].job_id == j2

    def test_running_jobs_uses_start_order_not_lexicographic_job_id(self):
        mgr = JobManager(max_concurrent=12)
        job_ids = [mgr.submit([f"cmd-{index}"]) for index in range(10)]
        for job_id in job_ids:
            mgr.mark_running(job_id)

        running_ids = [record.job_id for record in mgr.running_jobs()]
        assert running_ids[:3] == ["job-1", "job-2", "job-3"]
        assert running_ids[-1] == "job-10"

    def test_history_returns_newest_first(self):
        mgr = JobManager()
        j1 = mgr.submit(["a"])
        j2 = mgr.submit(["b"])
        mgr.mark_running(j1)
        mgr.mark_finished(j1, exit_code=0)
        mgr.mark_running(j2)
        mgr.mark_finished(j2, exit_code=1)
        hist = mgr.history()
        assert len(hist) == 2
        assert hist[0].job_id == j2  # newest first
        assert hist[1].job_id == j1

    def test_history_limit(self):
        mgr = JobManager()
        j1 = mgr.submit(["a"])
        j2 = mgr.submit(["b"])
        j3 = mgr.submit(["c"])
        for jid in (j1, j2, j3):
            mgr.mark_running(jid)
            mgr.mark_finished(jid, exit_code=0)
        hist = mgr.history(limit=2)
        assert len(hist) == 2

    def test_all_jobs_returns_submission_order(self):
        mgr = JobManager()
        j1 = mgr.submit(["a"])
        j2 = mgr.submit(["b"])
        all_jobs = mgr.all_jobs()
        assert len(all_jobs) == 2
        assert all_jobs[0].job_id == j1
        assert all_jobs[1].job_id == j2

    def test_is_any_running(self):
        mgr = JobManager()
        assert mgr.is_any_running() is False
        jid = mgr.submit(["echo"])
        mgr.mark_running(jid)
        assert mgr.is_any_running() is True

    def test_active_job_for_context(self):
        mgr = JobManager()
        j1 = mgr.submit(["a"], context={"flow": "swarm"})
        j2 = mgr.submit(["b"], context={"flow": "triage"})
        mgr.mark_running(j1)
        mgr.mark_running(j2)
        found = mgr.active_job_for_context("flow", "swarm")
        assert found is not None
        assert found.job_id == j1

    def test_active_job_for_context_returns_none(self):
        mgr = JobManager()
        j1 = mgr.submit(["a"], context={"flow": "triage"})
        mgr.mark_running(j1)
        assert mgr.active_job_for_context("flow", "swarm") is None

    def test_active_job_for_context_ignores_finished(self):
        mgr = JobManager()
        j1 = mgr.submit(["a"], context={"flow": "swarm"})
        mgr.mark_running(j1)
        mgr.mark_finished(j1, exit_code=0)
        assert mgr.active_job_for_context("flow", "swarm") is None


# ── History trimming ────────────────────────────────────────────


class TestJobManagerHistoryTrim:
    def test_trim_removes_oldest_terminal_jobs(self):
        mgr = JobManager(history_limit=2)
        ids = []
        for i in range(4):
            jid = mgr.submit([f"cmd-{i}"])
            mgr.mark_running(jid)
            mgr.mark_finished(jid, exit_code=0)
            ids.append(jid)
        # Only the 2 most recent terminal jobs should survive
        assert mgr.get(ids[0]) is None
        assert mgr.get(ids[1]) is None
        assert mgr.get(ids[2]) is not None
        assert mgr.get(ids[3]) is not None

    def test_trim_does_not_remove_running_jobs(self):
        mgr = JobManager(history_limit=1)
        j1 = mgr.submit(["a"])
        mgr.mark_running(j1)
        j2 = mgr.submit(["b"])
        mgr.mark_running(j2)
        mgr.mark_finished(j2, exit_code=0)
        # j1 is still running, j2 is the only terminal — should not be trimmed
        assert mgr.get(j1) is not None
        assert mgr.get(j2) is not None


# ── _default_label ──────────────────────────────────────────────


class TestDefaultLabel:
    def test_empty_command(self):
        assert _default_label([]) == "Command"

    def test_single_element(self):
        assert _default_label(["python3"]) == "python3"

    def test_strips_path(self):
        assert _default_label(["/usr/bin/python3", "script.py"]) == "python3 script.py"

    def test_two_elements(self):
        assert _default_label(["cargo", "test"]) == "cargo test"
