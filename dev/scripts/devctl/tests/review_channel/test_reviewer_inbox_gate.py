"""Focused tests for the reviewer-checkpoint inbox preflight gate.

The gate is the typed preflight step that refuses a reviewer-checkpoint
write while the reviewer inbox still has live-pending typed packets.
Without this gate, Codex (or Claude on the symmetric path) could write a
new verdict while typed finding packets targeting it sat unread in the
event log -- exactly the governance-platform protocol bug that let
`rev_pkt_0193` and `rev_pkt_0195` sit unread across four review sessions.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from dev.scripts.devctl.review_channel.reviewer_state import (
    ReviewerCheckpointUpdate,
    write_reviewer_checkpoint,
)

from .test_reviewer_checkpoint_inputs import (
    _build_bridge_text,
    _build_review_channel_text,
)


TRACE_REL = "dev/reports/review_channel/events/trace.ndjson"


def _write_pending_packet_targeting(
    root: Path,
    *,
    to_agent: str,
    packet_id: str = "rev_pkt_test_0001",
    expires_at_utc: str | None = None,
) -> None:
    """Append one `packet_posted` row targeting the given reviewer actor."""
    path = root / TRACE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    event: dict[str, object] = {
        "schema_version": 1,
        "event_id": f"evt_{packet_id}",
        "packet_id": packet_id,
        "trace_id": f"trace_{packet_id}",
        "event_type": "packet_posted",
        "status": "pending",
        "from_agent": "claude" if to_agent == "codex" else "codex",
        "to_agent": to_agent,
        "kind": "finding",
        "summary": f"Unread finding targeting {to_agent}",
    }
    if expires_at_utc is not None:
        event["expires_at_utc"] = expires_at_utc
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")


def _seed_bridge_state(root: Path) -> Path:
    """Write the shared bridge + review-channel markdown fixture under ``root``."""
    review_channel_path = root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_build_review_channel_text(), encoding="utf-8")
    bridge_path = root / "bridge.md"
    bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
    return bridge_path


def _make_checkpoint(
    *,
    actor: str = "codex",
    allow_unread_inbox: bool = False,
) -> ReviewerCheckpointUpdate:
    return ReviewerCheckpointUpdate(
        current_verdict="- accepted",
        open_findings="- none",
        current_instruction="- hold steady",
        reviewed_scope_items=("bridge.md",),
        actor=actor,
        allow_unread_inbox=allow_unread_inbox,
    )


def test_reviewer_checkpoint_blocks_when_codex_inbox_has_pending(
    tmp_path: Path,
) -> None:
    """The default ``codex`` reviewer cannot write while codex has unread packets."""
    bridge_path = _seed_bridge_state(tmp_path)
    _write_pending_packet_targeting(
        tmp_path,
        to_agent="codex",
        packet_id="rev_pkt_codex_block",
    )

    with (
        patch("dev.scripts.devctl.review_channel.state.refresh_status_snapshot"),
        pytest.raises(
            ValueError,
            match=r"refused reviewer-checkpoint: reviewer has \d+ unread packets",
        ) as excinfo,
    ):
        write_reviewer_checkpoint(
            repo_root=tmp_path,
            bridge_path=bridge_path,
            reviewer_mode="active_dual_agent",
            reason="manual-review",
            checkpoint=_make_checkpoint(actor="codex"),
        )

    assert "rev_pkt_codex_block" in str(excinfo.value)
    assert "--target codex" in str(excinfo.value)


def test_reviewer_checkpoint_succeeds_when_inbox_empty(
    tmp_path: Path,
) -> None:
    """With no pending packets targeting the actor, the checkpoint goes through."""
    bridge_path = _seed_bridge_state(tmp_path)

    with patch("dev.scripts.devctl.review_channel.state.refresh_status_snapshot"):
        state_write = write_reviewer_checkpoint(
            repo_root=tmp_path,
            bridge_path=bridge_path,
            reviewer_mode="active_dual_agent",
            reason="manual-review",
            checkpoint=_make_checkpoint(actor="codex"),
        )

    assert state_write.reviewer_actor == "codex"
    assert state_write.inbox_override_applied is False
    assert state_write.inbox_override_unread_packet_ids == ()


def test_reviewer_checkpoint_blocks_when_claude_inbox_has_pending(
    tmp_path: Path,
) -> None:
    """Symmetric path: Claude reviewer cannot write while claude has unread packets."""
    bridge_path = _seed_bridge_state(tmp_path)
    _write_pending_packet_targeting(
        tmp_path,
        to_agent="claude",
        packet_id="rev_pkt_claude_block",
    )
    # A codex-targeted packet must NOT block a claude-actor checkpoint --
    # the gate filters by reviewer actor, not global pendings.
    _write_pending_packet_targeting(
        tmp_path,
        to_agent="codex",
        packet_id="rev_pkt_codex_ignored",
    )

    with (
        patch("dev.scripts.devctl.review_channel.state.refresh_status_snapshot"),
        pytest.raises(
            ValueError,
            match=r"refused reviewer-checkpoint: reviewer has \d+ unread packets",
        ) as excinfo,
    ):
        write_reviewer_checkpoint(
            repo_root=tmp_path,
            bridge_path=bridge_path,
            reviewer_mode="active_dual_agent",
            reason="manual-review",
            checkpoint=_make_checkpoint(actor="claude"),
        )

    message = str(excinfo.value)
    assert "rev_pkt_claude_block" in message
    assert "rev_pkt_codex_ignored" not in message
    assert "--target claude" in message


def test_expired_packets_do_not_block_checkpoint(
    tmp_path: Path,
) -> None:
    """Stale/expired packets fall through the separate sweep; the gate allows them."""
    bridge_path = _seed_bridge_state(tmp_path)
    expired_at = (
        datetime.now(timezone.utc) - timedelta(minutes=5)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_pending_packet_targeting(
        tmp_path,
        to_agent="codex",
        packet_id="rev_pkt_expired",
        expires_at_utc=expired_at,
    )

    with patch("dev.scripts.devctl.review_channel.state.refresh_status_snapshot"):
        state_write = write_reviewer_checkpoint(
            repo_root=tmp_path,
            bridge_path=bridge_path,
            reviewer_mode="active_dual_agent",
            reason="manual-review",
            checkpoint=_make_checkpoint(actor="codex"),
        )

    assert state_write.inbox_override_applied is False
    assert state_write.inbox_override_unread_packet_ids == ()


def test_override_flag_allows_unread_inbox_for_emergency_reason(
    tmp_path: Path,
) -> None:
    """Emergency-recovery reason + override flag lets the checkpoint through.

    The override is recorded in the returned audit payload so operators can
    trace which checkpoint was written against an unconsumed inbox.
    """
    bridge_path = _seed_bridge_state(tmp_path)
    _write_pending_packet_targeting(
        tmp_path,
        to_agent="codex",
        packet_id="rev_pkt_override_ok",
    )

    with patch("dev.scripts.devctl.review_channel.state.refresh_status_snapshot"):
        state_write = write_reviewer_checkpoint(
            repo_root=tmp_path,
            bridge_path=bridge_path,
            reviewer_mode="active_dual_agent",
            reason="codex-recovery-override",
            checkpoint=_make_checkpoint(
                actor="codex",
                allow_unread_inbox=True,
            ),
        )

    assert state_write.reviewer_actor == "codex"
    assert state_write.inbox_override_applied is True
    assert state_write.inbox_override_unread_packet_ids == ("rev_pkt_override_ok",)


def test_override_flag_rejected_for_normal_reason(
    tmp_path: Path,
) -> None:
    """`--allow-unread-inbox` with a non-whitelisted reason still blocks."""
    bridge_path = _seed_bridge_state(tmp_path)
    _write_pending_packet_targeting(
        tmp_path,
        to_agent="codex",
        packet_id="rev_pkt_override_rejected",
    )

    with (
        patch("dev.scripts.devctl.review_channel.state.refresh_status_snapshot"),
        pytest.raises(
            ValueError,
            match=r"--allow-unread-inbox requires an emergency-recovery reason",
        ) as excinfo,
    ):
        write_reviewer_checkpoint(
            repo_root=tmp_path,
            bridge_path=bridge_path,
            reviewer_mode="active_dual_agent",
            reason="manual-review",
            checkpoint=_make_checkpoint(
                actor="codex",
                allow_unread_inbox=True,
            ),
        )

    assert "rev_pkt_override_rejected" in str(excinfo.value)
