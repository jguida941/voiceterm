from __future__ import annotations

import importlib.util
import json
import plistlib
import subprocess
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[5]
SERVICE_PATH = REPO_ROOT / "dev/config/launchd/review_channel_publisher_service.py"
PLIST_TEMPLATE_PATH = (
    REPO_ROOT / "dev/config/launchd/review_channel_publisher.plist.template"
)


def _load_service_module():
    spec = importlib.util.spec_from_file_location(
        "review_channel_publisher_service",
        SERVICE_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _completed(*, stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=[],
        returncode=returncode,
        stdout=stdout,
        stderr="",
    )


def _publisher_state_path(repo_root: Path) -> Path:
    return repo_root / "dev/reports/review_channel/latest/publisher_heartbeat.json"


def _write_publisher_state(
    repo_root: Path,
    *,
    running: bool,
    stop_reason: str = "",
) -> None:
    path = _publisher_state_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "running": running,
        "pid": 4242,
        "started_at_utc": "2026-04-03T00:00:00Z",
        "last_heartbeat_utc": "2026-04-03T00:01:00Z",
        "snapshots_emitted": 3,
        "reviewer_mode": "active_dual_agent",
        "stop_reason": stop_reason,
        "stopped_at_utc": "2026-04-03T00:02:00Z" if stop_reason else "",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _script_path(repo_root: Path) -> Path:
    return repo_root / "dev/config/launchd/review_channel_publisher_service.py"


def test_launchd_plist_template_uses_repo_root_placeholder_and_restart_policy() -> None:
    template = PLIST_TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "__REPO_ROOT__" in template

    payload = plistlib.loads(template.replace("__REPO_ROOT__", "/tmp/repo").encode("utf-8"))

    assert payload["RunAtLoad"] is True
    assert payload["KeepAlive"]["SuccessfulExit"] is False
    assert payload["ThrottleInterval"] == 10
    assert payload["ProgramArguments"][1].endswith(
        "dev/config/launchd/review_channel_publisher_service.py"
    )


def test_launchd_service_starts_follow_when_publisher_is_absent_at_login(
    tmp_path: Path,
) -> None:
    module = _load_service_module()
    repo_root = tmp_path / "repo"
    calls: list[list[str]] = []

    def _run(command, **kwargs):
        del kwargs
        calls.append(command)
        if command[4] == "status":
            return _completed(
                stdout=json.dumps(
                    {"bridge_liveness": {"effective_reviewer_mode": "active_dual_agent"}}
                )
            )
        _write_publisher_state(repo_root, running=False, stop_reason="manual_stop")
        return _completed(returncode=0)

    with patch.object(module.subprocess, "run", side_effect=_run):
        rc = module.main(script_path=_script_path(repo_root))

    assert rc == 0
    assert len(calls) == 2
    assert calls[1][-2:] == ["--follow-inactivity-timeout-seconds", "0"]


def test_launchd_service_noops_when_publisher_is_already_running(tmp_path: Path) -> None:
    module = _load_service_module()
    repo_root = tmp_path / "repo"
    _write_publisher_state(repo_root, running=True)

    with patch.object(module.subprocess, "run") as run_mock:
        rc = module.main(script_path=_script_path(repo_root))

    assert rc == 0
    run_mock.assert_not_called()


def test_launchd_service_noops_when_reviewer_mode_is_inactive(tmp_path: Path) -> None:
    module = _load_service_module()
    repo_root = tmp_path / "repo"
    calls: list[list[str]] = []

    def _run(command, **kwargs):
        del kwargs
        calls.append(command)
        return _completed(
            stdout=json.dumps(
                {"bridge_liveness": {"effective_reviewer_mode": "single_agent"}}
            )
        )

    with patch.object(module.subprocess, "run", side_effect=_run):
        rc = module.main(script_path=_script_path(repo_root))

    assert rc == 0
    assert len(calls) == 1
    assert calls[0][4] == "status"


def test_launchd_service_maps_output_error_to_restart_exit_code(
    tmp_path: Path,
) -> None:
    module = _load_service_module()
    repo_root = tmp_path / "repo"

    def _run(command, **kwargs):
        del kwargs
        if command[4] == "status":
            return _completed(
                stdout=json.dumps(
                    {"bridge_liveness": {"effective_reviewer_mode": "active_dual_agent"}}
                )
            )
        _write_publisher_state(repo_root, running=False, stop_reason="output_error")
        return _completed(returncode=1)

    with patch.object(module.subprocess, "run", side_effect=_run):
        rc = module.main(script_path=_script_path(repo_root))

    assert rc == 75


def test_launchd_service_maps_non_restartable_launch_authority_exit_to_success(
    tmp_path: Path,
) -> None:
    module = _load_service_module()
    repo_root = tmp_path / "repo"

    def _run(command, **kwargs):
        del kwargs
        if command[4] == "status":
            return _completed(
                stdout=json.dumps(
                    {"bridge_liveness": {"effective_reviewer_mode": "active_dual_agent"}}
                )
            )
        _write_publisher_state(repo_root, running=False)
        return _completed(returncode=82)

    with patch.object(module.subprocess, "run", side_effect=_run):
        rc = module.main(script_path=_script_path(repo_root))

    assert rc == 0


def test_launchd_service_maps_timeout_stop_reason_to_restart_exit_code(
    tmp_path: Path,
) -> None:
    module = _load_service_module()
    repo_root = tmp_path / "repo"

    def _run(command, **kwargs):
        del kwargs
        if command[4] == "status":
            return _completed(
                stdout=json.dumps(
                    {"bridge_liveness": {"effective_reviewer_mode": "active_dual_agent"}}
                )
            )
        _write_publisher_state(repo_root, running=False, stop_reason="timed_out")
        return _completed(returncode=0)

    with patch.object(module.subprocess, "run", side_effect=_run):
        rc = module.main(script_path=_script_path(repo_root))

    assert rc == 70
