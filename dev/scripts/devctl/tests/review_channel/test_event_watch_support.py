"""Focused regressions for event-backed watch packet loading."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.review_channel.event_watch_support import (
    EventWatchContext,
    load_target_packets,
    watch_snapshot_signature,
)


def _bundle(packet_id: str):
    return SimpleNamespace(
        review_state={
            "packets": [
                {
                    "packet_id": packet_id,
                    "to_agent": "claude",
                    "status": "pending",
                }
            ]
        }
    )


def test_load_target_packets_accepts_legacy_watch_follow_arguments(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_watch_support.filter_inbox_packets",
        lambda review_state, *, target, status, limit: list(review_state["packets"]),
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_watch_support.mark_action_request_packets_observed",
        lambda **_kwargs: False,
    )

    bundle, packets = load_target_packets(
        context=EventWatchContext.from_legacy(
            args=SimpleNamespace(target="claude", status="pending", limit=20),
            bundle=_bundle("pkt-legacy"),
            repo_root=Path("/tmp/repo"),
            review_channel_path=Path("/tmp/repo/dev/active/review_channel.md"),
            artifact_paths=SimpleNamespace(
                artifact_root="/tmp/repo/dev/reports/review_channel"
            ),
        ),
        status_filter="pending",
    )

    assert packets[0]["packet_id"] == "pkt-legacy"
    assert bundle.review_state["packets"][0]["packet_id"] == "pkt-legacy"


def test_load_target_packets_accepts_context_argument(monkeypatch) -> None:
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_watch_support.filter_inbox_packets",
        lambda review_state, *, target, status, limit: list(review_state["packets"]),
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_watch_support.mark_action_request_packets_observed",
        lambda **_kwargs: False,
    )

    bundle, packets = load_target_packets(
        context=EventWatchContext(
            args=SimpleNamespace(target="claude", status="pending", limit=20),
            bundle=_bundle("pkt-context"),
            repo_root=Path("/tmp/repo"),
            review_channel_path=Path("/tmp/repo/dev/active/review_channel.md"),
            artifact_paths=SimpleNamespace(artifact_root="/tmp/repo/dev/reports/review_channel"),
        ),
        status_filter="pending",
    )

    assert packets[0]["packet_id"] == "pkt-context"
    assert bundle.review_state["packets"][0]["packet_id"] == "pkt-context"


def test_watch_snapshot_signature_prefers_target_attention_revision() -> None:
    signature = watch_snapshot_signature(
        packets=[{"packet_id": "pkt-1"}],
        review_state={
            "queue": {"stale_packet_count": 3},
            "packet_inbox": {
                "attention_revision": "global-rev",
                "agents": [
                    {
                        "agent": "codex",
                        "attention_revision": "codex-rev",
                    },
                    {
                        "agent": "claude",
                        "attention_revision": "claude-rev",
                    },
                ],
            },
        },
        target="claude",
    )

    assert signature == (frozenset({"pkt-1"}), 3, "claude-rev")


def test_watch_snapshot_signature_falls_back_to_global_attention_revision() -> None:
    signature = watch_snapshot_signature(
        packets=[{"packet_id": "pkt-1"}],
        review_state={
            "queue": {"stale_packet_count": 0},
            "packet_inbox": {
                "attention_revision": "global-rev",
                "agents": [
                    {
                        "agent": "codex",
                        "attention_revision": "codex-rev",
                    }
                ],
            },
        },
        target="claude",
    )

    assert signature == (frozenset({"pkt-1"}), 0, "global-rev")
