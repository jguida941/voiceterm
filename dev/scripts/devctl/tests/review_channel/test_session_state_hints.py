"""Focused tests for review-channel session-state hints."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.review_channel.session_state_hints import (
    detect_session_state_hints,
)


def _write_session(
    tmp_path: Path,
    *,
    provider: str,
    log_text: str,
) -> Path:
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    log_path = sessions_dir / f"{provider}-conductor.log"
    metadata_path = sessions_dir / f"{provider}-conductor.json"
    log_path.write_text(log_text, encoding="utf-8")
    metadata_path.write_text(
        json.dumps({"log_path": str(log_path)}),
        encoding="utf-8",
    )
    return log_path


def test_detect_session_state_hints_ignores_fresh_prompt_during_active_progress(
    tmp_path: Path,
) -> None:
    _write_session(
        tmp_path,
        provider="claude",
        log_text=(
            "Claude Code\n"
            "Honking...\n"
            "esc to interrupt\n"
            "❯ \n"
        ),
    )

    assert detect_session_state_hints(session_output_root=tmp_path) == ()


def test_detect_session_state_hints_ignores_fresh_prompt_only_log(
    tmp_path: Path,
) -> None:
    _write_session(
        tmp_path,
        provider="claude",
        log_text="Claude Code\n❯ \n",
    )

    assert detect_session_state_hints(session_output_root=tmp_path) == ()


def test_detect_session_state_hints_marks_aged_prompt_only_log_as_waiting(
    tmp_path: Path,
    monkeypatch,
) -> None:
    log_path = _write_session(
        tmp_path,
        provider="claude",
        log_text="Claude Code\n❯ \n",
    )

    monkeypatch.setattr(
        "dev.scripts.devctl.review_channel.session_state_hints._log_age_seconds",
        lambda _path: 45 if _path == str(log_path) else None,
    )

    hints = detect_session_state_hints(session_output_root=tmp_path)

    assert len(hints) == 1
    assert hints[0].provider == "claude"
    assert hints[0].state == "waiting_for_user_input"
