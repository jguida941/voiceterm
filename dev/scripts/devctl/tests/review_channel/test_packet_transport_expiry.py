"""Tests for review-packet transport expiry semantics."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.devctl.review_channel.events import (
    post_packet,
    resolve_artifact_paths,
)
from dev.scripts.devctl.review_channel.packet_contract import (
    PacketPostRequest,
    PacketTargetFields,
)
from dev.scripts.devctl.runtime.packet_transport_expiry import (
    TRANSPORT_EXPIRY_EXPLICIT_METADATA_KEY,
    packet_kind_default_ttl_seconds,
    packet_transport_expires_at,
    packet_transport_expired,
    packet_uses_transport_expiry,
)


def _review_channel_path(root: Path) -> Path:
    path = root / "dev/active/review_channel.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Review Channel\n", encoding="utf-8")
    return path


def test_continuation_anchor_ignores_legacy_auto_ttl_without_explicit_metadata() -> None:
    packet = {
        "kind": "continuation_anchor",
        "expires_at_utc": "2000-01-01T00:00:00Z",
        "metadata": {},
    }

    assert packet_uses_transport_expiry(packet) is False
    assert packet_transport_expired(packet) is False


def test_continuation_anchor_honors_explicit_transport_expiry_metadata() -> None:
    packet = {
        "kind": "continuation_anchor",
        "expires_at_utc": "2000-01-01T00:00:00Z",
        "metadata": {TRANSPORT_EXPIRY_EXPLICIT_METADATA_KEY: True},
    }

    assert packet_uses_transport_expiry(packet) is True
    assert packet_transport_expired(packet) is True


def test_posted_continuation_anchor_defaults_to_no_transport_expiry(
    tmp_path: Path,
) -> None:
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    _bundle, event = post_packet(
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="claude",
            to_agent="codex",
            kind="continuation_anchor",
            summary="Keep working MP-377",
            body="Continue until the typed goal is closed.",
        ),
    )

    assert event["expires_at_utc"] == ""
    assert event["metadata"] == {}


def test_posted_continuation_anchor_records_explicit_transport_expiry(
    tmp_path: Path,
) -> None:
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    _bundle, event = post_packet(
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="claude",
            to_agent="codex",
            kind="continuation_anchor",
            summary="Keep working MP-377 for a bounded window",
            body="Continue until the typed goal is closed or this TTL expires.",
            expires_in_minutes=5,
        ),
    )

    assert event["expires_at_utc"]
    assert event["metadata"][TRANSPORT_EXPIRY_EXPLICIT_METADATA_KEY] is True


def test_posted_action_request_uses_default_transport_expiry(
    tmp_path: Path,
) -> None:
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    _bundle, event = post_packet(
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="codex",
            to_agent="claude",
            kind="action_request",
            summary="Run check",
            body="Run the requested check.",
            target=PacketTargetFields.from_values(target_role="implementer"),
        ),
    )

    assert event["expires_at_utc"]
    assert event["metadata"] == {}


def test_task_produced_uses_thirty_day_ttl_without_explicit_expiry() -> None:
    packet = {
        "kind": "task_produced",
        "posted_at": "2026-05-01T00:00:00Z",
        "status": "pending",
    }

    assert packet_uses_transport_expiry(packet) is True
    assert packet_kind_default_ttl_seconds("task_produced") == 30 * 24 * 60 * 60
    assert (
        packet_transport_expires_at(packet).isoformat()
        == "2026-05-31T00:00:00+00:00"
    )
    assert (
        packet_transport_expired(packet, now=_utc("2026-05-31T00:00:01Z"))
        is True
    )


def test_question_and_finding_use_seven_day_ttl_without_explicit_expiry() -> None:
    for kind in ("question", "finding"):
        packet = {
            "kind": kind,
            "timestamp_utc": "2026-05-01T00:00:00Z",
            "status": "pending",
        }

        assert packet_uses_transport_expiry(packet) is True
        assert packet_kind_default_ttl_seconds(kind) == 7 * 24 * 60 * 60
        assert (
            packet_transport_expires_at(packet).isoformat()
            == "2026-05-08T00:00:00+00:00"
        )


def test_decision_uses_fourteen_day_ttl_even_with_durable_target() -> None:
    packet = {
        "kind": "decision",
        "target_kind": "plan",
        "target_ref": "MP-TEST",
        "posted_at": "2026-05-01T00:00:00Z",
        "status": "pending",
    }

    assert packet_uses_transport_expiry(packet) is True
    assert packet_kind_default_ttl_seconds("decision") == 14 * 24 * 60 * 60
    assert (
        packet_transport_expires_at(packet).isoformat()
        == "2026-05-15T00:00:00+00:00"
    )


def test_posted_question_uses_kind_ttl_not_generic_default(
    tmp_path: Path,
) -> None:
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    _bundle, event = post_packet(
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="codex",
            to_agent="claude",
            kind="question",
            summary="Clarify scope",
            body="Which canonical owner should this use?",
        ),
    )

    assert event["expires_at_utc"]
    assert packet_kind_default_ttl_seconds(event["kind"]) == 7 * 24 * 60 * 60


def _utc(value: str):
    from datetime import datetime

    return datetime.fromisoformat(value.replace("Z", "+00:00"))
