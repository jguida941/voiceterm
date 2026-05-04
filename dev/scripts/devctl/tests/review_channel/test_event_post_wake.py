"""Regressions for event-backed post packet attention.

Packet posts must keep typed packet attention visible, but packet delivery is
not process authority and must not launch, replace, or externally wake agents.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.review_channel.event_handler import _run_event_action
from dev.scripts.devctl.commands.review_channel.event_post_wake import (
    EventPostWakeDeps,
    maybe_wake_posted_reviewer_packet,
)


def _fail_wake_dependency(**_kwargs):
    raise AssertionError("packet delivery must not call wake/launch dependencies")


def test_maybe_wake_posted_reviewer_packet_records_attention_only() -> None:
    result = maybe_wake_posted_reviewer_packet(
        args=SimpleNamespace(execution_mode="event-backed"),
        repo_root=Path("/tmp/repo"),
        paths={},
        packet={
            "packet_id": "pkt-find-1",
            "to_agent": "codex",
            "kind": "finding",
            "status": "pending",
        },
        deps=EventPostWakeDeps(
            refresh_status_snapshot_fn=_fail_wake_dependency,
            scan_repo_governance_fn=lambda _repo_root: SimpleNamespace(),
            derive_operator_interaction_mode_fn=_fail_wake_dependency,
            maybe_wake_waiting_reviewer_conductor_fn=_fail_wake_dependency,
            maybe_wake_waiting_agent_conductor_fn=_fail_wake_dependency,
        ),
    )

    assert result["attempted"] is False
    assert result["woke"] is False
    assert result["reason"] == "packet_delivery_records_typed_attention_only"
    assert result["wake_method"] == "none"
    assert result["target_agent"] == "codex"
    assert result["packet_id"] == "pkt-find-1"
    assert "does not launch" in result["warnings"][0]


def test_maybe_wake_posted_reviewer_packet_records_provider_attention_only() -> None:
    result = maybe_wake_posted_reviewer_packet(
        args=SimpleNamespace(execution_mode="event-backed"),
        repo_root=Path("/tmp/repo"),
        paths={},
        packet={
            "packet_id": "pkt-claude",
            "to_agent": "claude",
            "kind": "system_notice",
            "requested_action": "review_only",
            "status": "pending",
            "target_role": "dashboard",
            "target_session_id": "session-visible",
        },
        deps=EventPostWakeDeps(
            refresh_status_snapshot_fn=_fail_wake_dependency,
            maybe_wake_waiting_agent_conductor_fn=_fail_wake_dependency,
        ),
    )

    assert result["attempted"] is False
    assert result["woke"] is False
    assert result["reason"] == "packet_delivery_records_typed_attention_only"
    assert result["wake_method"] == "none"
    assert result["target_agent"] == "claude"
    assert result["packet_id"] == "pkt-claude"
    assert result["requested_action"] == "review_only"


def test_maybe_wake_posted_reviewer_packet_skips_synthetic_target() -> None:
    result = maybe_wake_posted_reviewer_packet(
        args=SimpleNamespace(execution_mode="event-backed"),
        repo_root=Path("/tmp/repo"),
        paths={},
        packet={
            "packet_id": "pkt-status",
            "to_agent": "system",
            "kind": "system_notice",
            "status": "pending",
        },
        deps=EventPostWakeDeps(refresh_status_snapshot_fn=_fail_wake_dependency),
    )

    assert result == {
        "attempted": False,
        "woke": False,
        "reason": "non_conductor_target",
        "packet_id": "pkt-status",
        "requested_action": "",
    }


def test_maybe_wake_posted_reviewer_packet_skips_non_pending_packet() -> None:
    result = maybe_wake_posted_reviewer_packet(
        args=SimpleNamespace(execution_mode="event-backed"),
        repo_root=Path("/tmp/repo"),
        paths={},
        packet={
            "packet_id": "pkt-acked",
            "to_agent": "codex",
            "kind": "finding",
            "status": "acked",
        },
        deps=EventPostWakeDeps(refresh_status_snapshot_fn=_fail_wake_dependency),
    )

    assert result == {
        "attempted": False,
        "woke": False,
        "reason": "non_pending_packet",
        "packet_id": "pkt-acked",
        "requested_action": "",
    }


def test_run_event_action_attaches_packet_attention_for_post(monkeypatch) -> None:
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_handler.run_post_action",
        lambda **_kwargs: (
            {"packet": {"packet_id": "pkt-1", "to_agent": "codex"}},
            0,
            {},
        ),
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_handler.maybe_wake_posted_reviewer_packet",
        lambda **_kwargs: {
            "attempted": False,
            "woke": False,
            "reason": "packet_delivery_records_typed_attention_only",
            "packet_id": "pkt-1",
            "requested_action": "",
            "target_agent": "codex",
            "wake_method": "none",
        },
    )

    report, exit_code = _run_event_action(
        args=SimpleNamespace(action="post"),
        repo_root=Path("/tmp/repo"),
        paths={
            "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
            "artifact_paths": SimpleNamespace(
                artifact_root="/tmp/repo/dev/reports/review_channel"
            ),
        },
    )

    assert exit_code == 0
    expected_attention = {
        "attempted": False,
        "woke": False,
        "reason": "packet_delivery_records_typed_attention_only",
        "packet_id": "pkt-1",
        "requested_action": "",
        "target_agent": "codex",
        "wake_method": "none",
    }
    assert report["packet_attention"] == expected_attention
    assert report["reviewer_wake"] == expected_attention


def test_run_event_action_syncs_bridge_when_post_becomes_instruction(
    monkeypatch,
    tmp_path: Path,
) -> None:
    bridge_path = tmp_path / "bridge.md"
    bridge_path.write_text("# Review Bridge\n\nstale\n", encoding="utf-8")
    observed: dict[str, object] = {}

    review_state_payload = {
        "queue": {
            "derived_next_instruction": "- Review the SYSTEM_MAP S0 receipt.",
            "derived_next_instruction_source": {"packet_id": "pkt-instruction"},
        },
        "current_session": {
            "current_instruction": "- Review the SYSTEM_MAP S0 receipt.",
            "current_instruction_revision": "rev-s0",
        },
    }

    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_handler.run_post_action",
        lambda **_kwargs: (
            {
                "packet": {
                    "packet_id": "pkt-instruction",
                    "to_agent": "claude",
                    "kind": "instruction",
                }
            },
            0,
            review_state_payload,
        ),
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_handler.maybe_wake_posted_reviewer_packet",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_handler.compute_non_audit_worktree_hash",
        lambda **_kwargs: "b" * 64,
    )

    def fake_render_bridge_projection(**kwargs):
        observed["review_state"] = kwargs["review_state"]
        observed["last_worktree_hash"] = kwargs["last_worktree_hash"]
        return (
            "# Review Bridge\n\n## Current Instruction For Claude\n\n"
            "- Review the SYSTEM_MAP S0 receipt.\n",
            object(),
        )

    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_handler.render_bridge_projection",
        fake_render_bridge_projection,
    )

    report, exit_code = _run_event_action(
        args=SimpleNamespace(action="post"),
        repo_root=tmp_path,
        paths={
            "review_channel_path": tmp_path / "dev/active/review_channel.md",
            "bridge_path": bridge_path,
            "artifact_paths": SimpleNamespace(
                artifact_root=tmp_path / "dev/reports/review_channel"
            ),
        },
    )

    assert exit_code == 0
    assert report["post_bridge_sync"] == {
        "synced": True,
        "reason": "posted_current_instruction",
        "packet_id": "pkt-instruction",
    }
    assert observed["review_state"] == review_state_payload
    assert observed["last_worktree_hash"] == "b" * 64
    assert "- Review the SYSTEM_MAP S0 receipt." in bridge_path.read_text(
        encoding="utf-8"
    )
