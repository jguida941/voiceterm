"""Tests for event-backed packet expiry materialization."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands.review_channel.event_handler import _run_event_action
from dev.scripts.devctl.review_channel.events import load_events, resolve_artifact_paths
from dev.scripts.devctl.review_channel.packet_expiry_materialization import (
    materialize_expired_packet_events,
)


def _review_channel_path(root: Path) -> Path:
    path = root / "dev/active/review_channel.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Review Channel\n", encoding="utf-8")
    return path


def _posted_event(packet_id: str, *, expires_at_utc: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "event_id": f"rev_evt_{int(packet_id.rsplit('_', 1)[-1]):04d}",
        "session_id": "session-post",
        "project_id": "project-test",
        "packet_id": packet_id,
        "trace_id": f"trace_{packet_id}",
        "timestamp_utc": "2026-04-29T01:00:00Z",
        "source": "review_channel",
        "plan_id": "MP-377",
        "controller_run_id": "run-1",
        "event_type": "packet_posted",
        "from_agent": "codex",
        "to_agent": "claude",
        "kind": "finding",
        "summary": f"Expired packet {packet_id}",
        "body": "This packet should archive through an explicit event.",
        "evidence_refs": [],
        "guidance_refs": [],
        "context_pack_refs": [],
        "confidence": 1.0,
        "requested_action": "review_only",
        "policy_hint": "review_only",
        "approval_required": False,
        "target_kind": "packet",
        "target_ref": packet_id,
        "target_revision": "",
        "target_role": "implementer",
        "target_session_id": "session-claude",
        "anchor_refs": [],
        "intake_ref": "",
        "mutation_op": "",
        "semantic_zref": f"packet:{packet_id}",
        "source_identity": {},
        "status": "pending",
        "idempotency_key": f"post-{packet_id}",
        "nonce": "nonce",
        "expires_at_utc": expires_at_utc,
        "metadata": {},
    }


def _write_events(path: Path, events: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n",
        encoding="utf-8",
    )


def test_materialize_expired_packet_events_appends_lifecycle_event(
    tmp_path: Path,
) -> None:
    review_channel_path = _review_channel_path(tmp_path)
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    _write_events(
        Path(artifact_paths.event_log_path),
        [
            _posted_event(
                "rev_pkt_0001",
                expires_at_utc="2000-01-01T00:00:00Z",
            )
        ],
    )

    bundle, materialization = materialize_expired_packet_events(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )

    events = load_events(Path(artifact_paths.event_log_path))
    packet = bundle.review_state["packets"][0]

    assert materialization.materialized_packet_count == 1
    assert materialization.packet_ids == ("rev_pkt_0001",)
    assert [event["event_type"] for event in events] == [
        "packet_posted",
        "packet_expired",
    ]
    assert events[-1]["metadata"]["materialized_from_event_id"] == "rev_evt_0001"
    assert events[-1]["target_role"] == "implementer"
    assert events[-1]["target_session_id"] == "session-claude"
    assert bundle.review_state["queue"]["stale_packet_count"] == 0
    assert packet["status"] == "expired"
    assert packet["lifecycle_current_state"] == "archived"
    assert packet["acted_on_events"][0]["event_id"] == "rev_evt_0002"
    assert packet["disposition"]["sink"] == "archived"


def test_materialize_expired_packet_events_is_idempotent(tmp_path: Path) -> None:
    review_channel_path = _review_channel_path(tmp_path)
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    _write_events(
        Path(artifact_paths.event_log_path),
        [
            _posted_event(
                "rev_pkt_0001",
                expires_at_utc="2000-01-01T00:00:00Z",
            )
        ],
    )

    materialize_expired_packet_events(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    _, second = materialize_expired_packet_events(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )

    events = load_events(Path(artifact_paths.event_log_path))
    assert second.materialized_packet_count == 0
    assert [event["event_type"] for event in events] == [
        "packet_posted",
        "packet_expired",
    ]


def test_expire_packets_action_materializes_bounded_events(tmp_path: Path) -> None:
    review_channel_path = _review_channel_path(tmp_path)
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    _write_events(
        Path(artifact_paths.event_log_path),
        [
            _posted_event(
                "rev_pkt_0001",
                expires_at_utc="2000-01-01T00:00:00Z",
            ),
            _posted_event(
                "rev_pkt_0002",
                expires_at_utc="2000-01-01T00:00:00Z",
            ),
        ],
    )
    args = build_parser().parse_args(
        [
            "review-channel",
            "--action",
            "expire-packets",
            "--limit",
            "1",
            "--terminal",
            "none",
            "--format",
            "json",
        ]
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    events = load_events(Path(artifact_paths.event_log_path))
    materialization = report["packet_expiry_materialization"]

    assert exit_code == 0
    assert report["action"] == "expire-packets"
    assert materialization["materialized_packet_count"] == 1
    assert materialization["remaining_expired_pending_count"] == 1
    assert [event["event_type"] for event in events].count("packet_expired") == 1
    assert len(report["packets"]) == 1


def test_status_action_does_not_materialize_expiry_events(tmp_path: Path) -> None:
    review_channel_path = _review_channel_path(tmp_path)
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    _write_events(
        Path(artifact_paths.event_log_path),
        [
            _posted_event(
                "rev_pkt_0001",
                expires_at_utc="2000-01-01T00:00:00Z",
            )
        ],
    )
    args = build_parser().parse_args(
        [
            "review-channel",
            "--action",
            "status",
            "--terminal",
            "none",
            "--format",
            "json",
        ]
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    events = load_events(Path(artifact_paths.event_log_path))

    assert exit_code == 0
    assert report["action"] == "status"
    assert report["packet_expiry_materialization"] is None
    assert [event["event_type"] for event in events] == ["packet_posted"]
    assert report["queue"]["stale_packet_count"] == 1


def test_sync_status_action_does_not_materialize_expiry_events(tmp_path: Path) -> None:
    review_channel_path = _review_channel_path(tmp_path)
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    _write_events(
        Path(artifact_paths.event_log_path),
        [
            _posted_event(
                "rev_pkt_0001",
                expires_at_utc="2000-01-01T00:00:00Z",
            )
        ],
    )
    args = build_parser().parse_args(
        [
            "review-channel",
            "--action",
            "sync-status",
            "--terminal",
            "none",
            "--format",
            "json",
        ]
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    events = load_events(Path(artifact_paths.event_log_path))

    assert exit_code == 0
    assert report["action"] == "sync-status"
    assert report["status"] == "ok"
    assert report["exit_ok"] is True
    assert report["exit_code"] == 0
    assert "packet_expiry_materialization" not in report
    assert [event["event_type"] for event in events] == ["packet_posted"]


def test_read_only_status_suppresses_projection_writes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    review_channel_path = _review_channel_path(tmp_path)
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    _write_events(
        Path(artifact_paths.event_log_path),
        [
            _posted_event(
                "rev_pkt_0001",
                expires_at_utc="2000-01-01T00:00:00Z",
            )
        ],
    )
    monkeypatch.setenv("DEVCTL_NO_ARTIFACT_WRITES", "1")
    args = build_parser().parse_args(
        [
            "review-channel",
            "--action",
            "status",
            "--terminal",
            "none",
            "--format",
            "json",
        ]
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["action"] == "status"
    assert not Path(artifact_paths.state_path).exists()
    assert not Path(report["projection_paths"]["review_state_path"]).exists()
    assert not Path(report["projection_paths"]["full_path"]).exists()


def test_sync_status_accepts_for_agent_alias() -> None:
    args = build_parser().parse_args(
        [
            "review-channel",
            "--action",
            "sync-status",
            "--for-agent",
            "codex",
            "--terminal",
            "none",
            "--format",
            "json",
        ]
    )

    assert args.for_agent == "codex"
