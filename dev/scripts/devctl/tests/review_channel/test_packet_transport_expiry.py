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
