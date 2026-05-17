"""Tests for typed session liveness reconciliation."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.runtime.session_liveness_reconciler import (
    reconcile_session_liveness,
)


def _write_attachment(
    root: Path,
    *,
    provider: str = "codex",
    status: str = "attached",
    host_pid: int | None = None,
    last_seen_utc: str = "2020-01-01T00:00:00Z",
    remote_session_id: str = "session-test",
) -> Path:
    sessions = root / "sessions"
    sessions.mkdir(parents=True, exist_ok=True)
    path = sessions / f"{provider}-remote-control.json"
    payload = {
        "provider": provider,
        "role": "implementer",
        "attachment_id": f"remote-attach-{provider}",
        "session_name": f"{provider}-session",
        "remote_session_id": remote_session_id,
        "session_url": "",
        "status": status,
        "transport": "review_channel_artifact",
        "attached_at_utc": "2020-01-01T00:00:00Z",
        "last_seen_utc": last_seen_utc,
        "metadata_path": str(path),
        "launcher_source": "test",
        "host_pid": host_pid,
        "host_session_label": "",
        "heartbeat_ttl_seconds": 60,
        "previous_operator_mode": "",
        "entrypoint": "",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def test_reconciler_detaches_expired_attachment_when_kill_stale(tmp_path: Path) -> None:
    root = tmp_path / "latest"
    path = _write_attachment(root, host_pid=None)

    result = reconcile_session_liveness(
        session_output_root=root,
        kill_stale=True,
        generated_at_utc="2026-05-14T00:00:00Z",
        process_probe=lambda _pid: False,
    )

    assert result.ok is True
    assert result.stale_count == 1
    assert result.cleared_attachment_count == 1
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == "detached"
    assert payload["physical_remote_control_confirmed"] is False
    assert result.rows[0].reason == "attachment_heartbeat_expired"


def test_reconciler_dry_run_does_not_write_attachment(tmp_path: Path) -> None:
    root = tmp_path / "latest"
    path = _write_attachment(root, host_pid=999)

    result = reconcile_session_liveness(
        session_output_root=root,
        kill_stale=True,
        dry_run=True,
        process_probe=lambda _pid: False,
    )

    assert result.stale_count == 1
    assert result.cleared_attachment_count == 0
    assert result.rows[0].action == "would_detach"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == "attached"


def test_reconciler_kills_live_pid_when_attachment_is_expired(tmp_path: Path) -> None:
    root = tmp_path / "latest"
    _write_attachment(root, host_pid=12345)
    killed: list[int] = []

    result = reconcile_session_liveness(
        session_output_root=root,
        kill_stale=True,
        process_probe=lambda _pid: True,
        process_killer=lambda pid: killed.append(pid) or "",
    )

    assert killed == [12345]
    assert result.killed_pid_count == 1
    assert result.cleared_attachment_count == 1
    assert result.rows[0].action == "killed_and_detached"


def test_reconciler_keeps_fresh_attachment_with_live_pid(tmp_path: Path) -> None:
    root = tmp_path / "latest"
    path = _write_attachment(
        root,
        host_pid=12345,
        last_seen_utc="2030-01-01T00:00:00Z",
        remote_session_id="session-current",
    )

    result = reconcile_session_liveness(
        session_output_root=root,
        kill_stale=True,
        process_probe=lambda _pid: True,
    )

    assert result.stale_count == 0
    assert result.cleared_attachment_count == 0
    assert result.rows[0].action == "none"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == "attached"
