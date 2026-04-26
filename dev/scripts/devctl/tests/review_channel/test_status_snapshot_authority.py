"""Tests for review-channel status authority reduction."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from dev.scripts.devctl.commands.review_channel import _recover
from dev.scripts.devctl.review_channel import status_snapshot_authority
from dev.scripts.devctl.review_channel.recover_support import RecoverSessionBuildInput


def test_operator_mode_prefers_typed_remote_control_liveness(monkeypatch) -> None:
    """Remote-control attachment liveness must override local governance defaults."""
    monkeypatch.setattr(
        status_snapshot_authority,
        "scan_repo_governance_safely",
        lambda _repo_root: None,
    )

    mode = status_snapshot_authority._operator_interaction_mode(
        Path("."),
        review_state_payload={},
        bridge_liveness={
            "reviewer_mode": "active_dual_agent",
            "remote_control_active_providers": ["claude"],
        },
    )

    assert mode == "remote_control"


def test_operator_mode_falls_back_to_reviewer_mode_without_remote_liveness(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        status_snapshot_authority,
        "scan_repo_governance_safely",
        lambda _repo_root: None,
    )

    mode = status_snapshot_authority._operator_interaction_mode(
        Path("."),
        review_state_payload={},
        bridge_liveness={"reviewer_mode": "active_dual_agent"},
    )

    assert mode == "dual_agent"


def test_recover_blocks_remote_visible_launch_before_terminal_profile_lookup(
    monkeypatch,
    tmp_path,
) -> None:
    """Remote-control recover must fail before any Terminal.app interaction."""
    monkeypatch.setattr(
        _recover,
        "resolve_launch_interaction_mode",
        lambda **_kwargs: "remote_control",
    )

    def _fail_profile_lookup() -> list[str]:
        raise AssertionError("Terminal.app profile lookup should not run")

    monkeypatch.setattr(_recover, "list_terminal_profiles", _fail_profile_lookup)

    args = SimpleNamespace(
        terminal="terminal-app",
        terminal_profile="auto-dark",
        operator_interaction_mode="",
    )
    runtime_paths = SimpleNamespace(
        bridge_path=tmp_path / "bridge.md",
        review_channel_path=tmp_path / "review_channel.md",
        status_dir=tmp_path / "status",
        script_dir=tmp_path / "scripts",
    )
    status_snapshot = SimpleNamespace(bridge_liveness={})

    with pytest.raises(ValueError, match="visible_launch_in_remote_control"):
        _recover._build_recover_sessions(
            RecoverSessionBuildInput(
                args=args,
                repo_root=tmp_path,
                runtime_paths=runtime_paths,
                status_snapshot=status_snapshot,
                reviewer_provider="codex",
                recover_provider="claude",
                provider_lane_map={},
            )
        )
