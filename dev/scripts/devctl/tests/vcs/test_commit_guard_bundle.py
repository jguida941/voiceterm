"""Tests for governed commit guard-bundle recovery behavior."""

from __future__ import annotations

import subprocess
from pathlib import Path

from dev.scripts.devctl.commands.vcs.commit_guard_bundle import (
    run_guard_bundle_with_result,
)


def _completed(cmd: list[str], returncode: int, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr=stderr)


def test_guard_bundle_auto_retries_host_cleanup_age_out() -> None:
    calls: list[list[str]] = []

    def fake_runner(cmd, **_kwargs):
        calls.append(list(cmd))
        if len(calls) == 1:
            return _completed(
                list(cmd),
                1,
                stdout=(
                    "host-process-cleanup-post: Recent detached repo-related "
                    "processes were not killed yet"
                ),
            )
        if len(calls) == 2:
            return _completed(list(cmd), 0, stdout='{"ok": true}')
        return _completed(list(cmd), 0, stdout='{"success": true}')

    exit_code, result = run_guard_bundle_with_result(
        repo_root=Path("/tmp/repo"),
        runner=fake_runner,
    )

    assert exit_code == 0
    assert result.ok is True
    assert result.auto_executable is True
    assert result.remediation == "host_process_cleanup_post_age_retry"
    assert result.errors[0]["reason"] == "host_process_cleanup_post_age_out"
    assert "auto_retry_succeeded" in result.reason_chain
    assert calls[1][2] == "process-watch"
    assert len(calls) == 3


def test_guard_bundle_reports_host_cleanup_retry_failure() -> None:
    calls: list[list[str]] = []

    def fake_runner(cmd, **_kwargs):
        calls.append(list(cmd))
        if len(calls) == 1:
            return _completed(
                list(cmd),
                1,
                stderr=(
                    "host-process-cleanup-post: Recent detached repo-related "
                    "processes were not killed yet"
                ),
            )
        return _completed(list(cmd), 1, stdout='{"ok": false}')

    exit_code, result = run_guard_bundle_with_result(
        repo_root=Path("/tmp/repo"),
        runner=fake_runner,
    )

    assert exit_code == 1
    assert result.ok is False
    assert result.reason == "guard_bundle_failed"
    assert result.errors[0]["details"]["second_attempt_status"] == "not_run"
    assert "auto_retry_failed" in result.reason_chain
    assert len(calls) == 2
