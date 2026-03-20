"""Tests for check_daemon_state_parity.py."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.checks.daemon_state_parity.command import build_report


def _write_repo_fixture(
    root: Path,
    *,
    python_events: tuple[str, ...] = (
        "daemon_started",
        "daemon_stopped",
        "daemon_heartbeat",
    ),
    include_stop_reason: bool = True,
) -> None:
    rust_path = root / "rust" / "src" / "bin" / "voiceterm" / "daemon" / "types.rs"
    python_path = (
        root
        / "dev"
        / "scripts"
        / "devctl"
        / "review_channel"
        / "daemon_reducer.py"
    )
    rust_path.parent.mkdir(parents=True)
    python_path.parent.mkdir(parents=True)

    rust_path.write_text(
        """
pub enum DaemonEvent {
    #[serde(rename = "daemon_ready")]
    Ready,
    #[serde(rename = "daemon_status")]
    Status { uptime_seconds: u64 },
    #[serde(rename = "daemon_shutdown")]
    Shutdown,
}

pub struct AgentInfo {
    pub session_id: String,
    pub provider: String,
    pub label: String,
    pub working_dir: String,
    pub pid: u32,
    pub is_alive: bool,
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    stop_reason_line = "    stop_reason: str | None\n" if include_stop_reason else ""
    python_path.write_text(
        (
            "from typing import TypedDict\n\n"
            f"DAEMON_EVENT_TYPES = frozenset({{{', '.join(repr(item) for item in python_events)}}})\n\n"
            "class DaemonStateDict(TypedDict):\n"
            "    running: bool\n"
            "    pid: int | None\n"
            "    started_at_utc: str | None\n"
            "    last_heartbeat_utc: str | None\n"
            f"{stop_reason_line}"
            "    stopped_at_utc: str | None\n"
        ),
        encoding="utf-8",
    )


def test_daemon_state_parity_all_green(tmp_path: Path) -> None:
    _write_repo_fixture(tmp_path)

    report = build_report(repo_root=tmp_path)

    assert report["ok"] is True
    assert report["violations"] == []


def test_daemon_state_parity_flags_missing_lifecycle_event(tmp_path: Path) -> None:
    _write_repo_fixture(tmp_path, python_events=("daemon_started", "daemon_stopped"))

    report = build_report(repo_root=tmp_path)

    assert report["ok"] is False
    assert any(v["rule"] == "daemon-lifecycle-trio-gap" for v in report["violations"])


def test_daemon_state_parity_flags_missing_state_field(tmp_path: Path) -> None:
    _write_repo_fixture(tmp_path, include_stop_reason=False)

    report = build_report(repo_root=tmp_path)

    assert report["ok"] is False
    assert any(v["rule"] == "daemon-state-field-gap" for v in report["violations"])
