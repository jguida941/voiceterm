"""Focused regressions for event-backed watch packet loading."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.review_channel.event_watch_support import (
    EventWatchContext,
    load_target_packets,
    watch_snapshot_signature,
)
from dev.scripts.devctl.commands.review_channel.watch_follow_state import (
    WatchFollowRuntimeContext,
    load_initial_watch_bundle,
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
        lambda review_state, **_kwargs: list(review_state["packets"]),
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
        lambda review_state, **_kwargs: list(review_state["packets"]),
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


def test_load_target_packets_does_not_mark_observed_without_matching_actor(
    monkeypatch,
) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_watch_support.filter_inbox_packets",
        lambda review_state, **_kwargs: list(review_state["packets"]),
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_watch_support.mark_action_request_packets_observed",
        lambda **kwargs: calls.append(kwargs) or True,
    )

    bundle, packets = load_target_packets(
        context=EventWatchContext(
            args=SimpleNamespace(target="claude", status="pending", limit=20),
            bundle=_bundle("pkt-readonly"),
            repo_root=Path("/tmp/repo"),
            review_channel_path=Path("/tmp/repo/dev/active/review_channel.md"),
            artifact_paths=SimpleNamespace(
                artifact_root="/tmp/repo/dev/reports/review_channel"
            ),
        ),
        status_filter="pending",
    )

    assert packets[0]["packet_id"] == "pkt-readonly"
    assert bundle.review_state["packets"][0]["packet_id"] == "pkt-readonly"
    assert calls == []


def test_load_target_packets_marks_observed_for_matching_actor(monkeypatch) -> None:
    calls: list[dict[str, object]] = []
    initial = _bundle("pkt-initial")
    refreshed = _bundle("pkt-refreshed")
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_watch_support.filter_inbox_packets",
        lambda review_state, **_kwargs: list(review_state["packets"]),
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_watch_support.mark_action_request_packets_observed",
        lambda **kwargs: calls.append(kwargs) or True,
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_watch_support.refresh_event_bundle",
        lambda **_kwargs: refreshed,
    )

    bundle, packets = load_target_packets(
        context=EventWatchContext(
            args=SimpleNamespace(
                target="claude",
                actor="claude",
                status="pending",
                limit=20,
            ),
            bundle=initial,
            repo_root=Path("/tmp/repo"),
            review_channel_path=Path("/tmp/repo/dev/active/review_channel.md"),
            artifact_paths=SimpleNamespace(
                artifact_root="/tmp/repo/dev/reports/review_channel"
            ),
        ),
        status_filter="pending",
    )

    assert packets[0]["packet_id"] == "pkt-refreshed"
    assert bundle is refreshed
    assert calls[0]["observer"] == "claude"


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

    assert signature[0] == (("pkt-1", "", "", "", "", "", "", "", "", ""),)
    assert signature[1] == 3
    assert signature[2] == "claude-rev"


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

    assert signature[0] == (("pkt-1", "", "", "", "", "", "", "", "", ""),)
    assert signature[1] == 0
    assert signature[2] == "global-rev"


def test_watch_snapshot_signature_changes_on_packet_status_transition() -> None:
    pending = watch_snapshot_signature(
        packets=[
            {
                "packet_id": "pkt-1",
                "latest_event_id": "evt-1",
                "status": "pending",
            }
        ],
        review_state={},
        target="claude",
    )
    acked = watch_snapshot_signature(
        packets=[
            {
                "packet_id": "pkt-1",
                "latest_event_id": "evt-2",
                "status": "acked",
                "acked_at_utc": "2026-04-25T02:00:00Z",
                "acked_by": "claude",
            }
        ],
        review_state={},
        target="claude",
    )

    assert pending != acked


def test_watch_snapshot_signature_changes_on_current_instruction_revision() -> None:
    base = watch_snapshot_signature(
        packets=[],
        review_state={
            "current_session": {
                "current_instruction_revision": "rev-1",
                "implementer_ack_state": "missing",
            }
        },
        target="claude",
    )
    changed = watch_snapshot_signature(
        packets=[],
        review_state={
            "current_session": {
                "current_instruction_revision": "rev-2",
                "implementer_ack_state": "missing",
            }
        },
        target="claude",
    )

    assert base != changed


def test_load_initial_watch_bundle_passes_event_watch_context(monkeypatch) -> None:
    bundle = _bundle("pkt-watch")
    observed: dict[str, object] = {}

    def fake_load_target_packets(*, context, status_filter=None, **_kwargs):
        observed["context"] = context
        observed["status_filter"] = status_filter
        return context.bundle, list(context.bundle.review_state["packets"])

    ctx = WatchFollowRuntimeContext(
        args=SimpleNamespace(target="claude", status="pending", limit=20),
        repo_root=Path("/tmp/repo"),
        review_channel_path=Path("/tmp/repo/dev/active/review_channel.md"),
        artifact_paths=SimpleNamespace(artifact_root="/tmp/repo/dev/reports/review_channel"),
        target="claude",
        status_filter="pending",
        owner=SimpleNamespace(),
        interval=5,
        max_snapshots=1,
        deps=SimpleNamespace(
            load_or_refresh_event_bundle_fn=lambda **_kwargs: bundle,
            load_target_packets_fn=fake_load_target_packets,
        ),
    )

    loaded_bundle, packets, error = load_initial_watch_bundle(ctx)

    assert error is None
    assert loaded_bundle is bundle
    assert packets == list(bundle.review_state["packets"])
    assert isinstance(observed["context"], EventWatchContext)
    assert observed["context"].args.target == "claude"
    assert observed["context"].bundle is bundle
    assert observed["status_filter"] == "pending"
