"""Tests for shared VCS helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.runtime import vcs


def _completed(cmd: list[str], returncode: int, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr=stderr)


def test_run_git_capture_retries_transient_index_lock() -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, **_kwargs):
        calls.append(list(cmd))
        if len(calls) == 1:
            return _completed(
                list(cmd),
                128,
                stderr=(
                    "fatal: Unable to create '.git/index.lock': File exists. "
                    "Another git process seems to be running in this repository."
                ),
            )
        return _completed(list(cmd), 0, stdout="ok")

    with patch.object(vcs.subprocess, "run", side_effect=fake_run), patch.object(
        vcs.time,
        "sleep",
    ) as sleep_mock:
        code, stdout, stderr = vcs.run_git_capture(
            ["add", "--", "tracked.txt"],
            repo_root=Path("/tmp/repo"),
        )

    assert code == 0
    assert stdout == "ok"
    assert stderr == ""
    assert len(calls) == 2
    sleep_mock.assert_called_once_with(vcs.INDEX_LOCK_RETRY_DELAYS[0])


def test_run_git_capture_does_not_retry_sandbox_index_denial() -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, **_kwargs):
        calls.append(list(cmd))
        return _completed(
            list(cmd),
            128,
            stderr="fatal: Unable to create '.git/index.lock': Operation not permitted",
        )

    with patch.object(vcs.subprocess, "run", side_effect=fake_run), patch.object(
        vcs.time,
        "sleep",
    ) as sleep_mock:
        code, _stdout, stderr = vcs.run_git_capture(
            ["add", "--", "tracked.txt"],
            repo_root=Path("/tmp/repo"),
        )

    assert code == 128
    assert "Operation not permitted" in stderr
    assert len(calls) == 1
    sleep_mock.assert_not_called()
