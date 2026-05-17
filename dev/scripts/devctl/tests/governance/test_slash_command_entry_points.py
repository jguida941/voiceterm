"""Tests for provider-neutral slash-command entry adapters."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"
REQUIRED_ENTRY_POINTS = {
    "agent-spawn.md",
    "archive-evidence.md",
    "bypass.md",
    "check-it.md",
    "develop.md",
    "goal.md",
    "handshake.md",
    "session-log.md",
}


def test_mp377_slash_entry_points_are_thin_devctl_adapters() -> None:
    present = {path.name for path in COMMANDS_DIR.glob("*.md")}

    assert REQUIRED_ENTRY_POINTS.issubset(present)
    for filename in REQUIRED_ENTRY_POINTS:
        text = (COMMANDS_DIR / filename).read_text(encoding="utf-8")
        compact_text = " ".join(text.lower().split())
        assert "python3 dev/scripts/devctl.py" in text
        assert "This file is only an adapter." in text
        assert "authority lives" in compact_text


def test_mp377_slash_entry_points_are_provider_neutral() -> None:
    for filename in REQUIRED_ENTRY_POINTS:
        text = (COMMANDS_DIR / filename).read_text(encoding="utf-8").lower()
        assert "/claude-" not in text
        assert "/codex-" not in text
        assert "caller == 'claude'" not in text
        assert 'caller == "claude"' not in text
        assert "caller == 'codex'" not in text
        assert 'caller == "codex"' not in text
