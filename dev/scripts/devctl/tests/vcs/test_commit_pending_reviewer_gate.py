"""Tests for the fail-closed commit gate on pending reviewer packets.

Verifies that both the governed commit path and the snapshot receipt path
block when actionable reviewer packets exist, even when an attention-revision
lease is held.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.runtime.commit_packet_gate import (
    _has_actionable_attention,
    pending_packet_queue_block_commit,
    pending_reviewer_packets_block_commit,
)
from dev.scripts.devctl.review_channel.pending_packet_models import (
    PendingPacketQueueSnapshot,
)


def _make_inbox_record(
    agent: str = "claude",
    pending_ids: tuple[str, ...] = (),
    wake_reason: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        agent=agent,
        pending_actionable_packet_ids=pending_ids,
        wake_reason=wake_reason,
    )


def _make_review_state(
    agents: list | None = None,
    attention_revision: str = "rev-001",
    packets: list | None = None,
) -> SimpleNamespace:
    if agents is None:
        agents = []
    if packets is None:
        packets = []
    return SimpleNamespace(
        packet_inbox=SimpleNamespace(
            agents=agents,
            attention_revision=attention_revision,
        ),
        packets=packets,
    )


def _make_packet(
    *,
    packet_id: str = "rev_pkt_0001",
    kind: str = "instruction",
    to_agent: str = "claude",
    status: str = "pending",
    requested_action: str = "review_only",
    policy_hint: str = "review_only",
    expires_at_utc: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        packet_id=packet_id,
        kind=kind,
        to_agent=to_agent,
        status=status,
        requested_action=requested_action,
        policy_hint=policy_hint,
        expires_at_utc=expires_at_utc,
    )


# ── Core gate tests ───────────────────────────────────────────


class TestPendingReviewerPacketsBlockCommit(unittest.TestCase):
    """Test the shared fail-closed gate."""

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state"
    )
    def test_blocks_when_pending_packets_exist(self, mock_load):
        mock_load.return_value = _make_review_state(
            agents=[
                _make_inbox_record(
                    agent="claude",
                    pending_ids=("rev_pkt_0703", "rev_pkt_0704"),
                ),
            ],
        )
        result = pending_reviewer_packets_block_commit(
            repo_root=None,
            review_channel_path=Path("/fake/exists"),
            target_agent="claude",
        )
        self.assertIsNotNone(result)
        self.assertIn("Commit blocked", result)
        self.assertIn("rev_pkt_0703", result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state"
    )
    def test_allows_when_no_pending_packets(self, mock_load):
        mock_load.return_value = _make_review_state(
            agents=[_make_inbox_record(agent="claude", pending_ids=())],
        )
        result = pending_reviewer_packets_block_commit(
            repo_root=None,
            review_channel_path=Path("/fake/exists"),
            target_agent="claude",
        )
        self.assertIsNone(result)

    def test_allows_when_no_review_channel_path(self):
        result = pending_reviewer_packets_block_commit(
            repo_root=None, review_channel_path=None,
        )
        self.assertIsNone(result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate.load_pending_packet_queue"
    )
    def test_queue_gate_exempts_authorized_action_request(self, mock_load):
        mock_load.return_value = PendingPacketQueueSnapshot(
            pending_packets=(
                {
                    "packet_id": "rev_pkt_exec",
                    "kind": "action_request",
                    "to_agent": "claude",
                    "status": "pending",
                    "requested_action": "stage_commit_pipeline",
                    "policy_hint": "safe_auto_apply",
                },
            ),
        )
        result = pending_packet_queue_block_commit(
            repo_root=Path("/fake/repo"),
            target_agent="claude",
            exempt_packet_id="rev_pkt_exec",
        )
        self.assertIsNone(result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate.load_pending_packet_queue"
    )
    def test_queue_gate_blocks_other_action_requests(self, mock_load):
        mock_load.return_value = PendingPacketQueueSnapshot(
            pending_packets=(
                {
                    "packet_id": "rev_pkt_other",
                    "kind": "action_request",
                    "to_agent": "claude",
                    "status": "pending",
                    "requested_action": "stage_commit_pipeline",
                    "policy_hint": "safe_auto_apply",
                },
            ),
        )
        result = pending_packet_queue_block_commit(
            repo_root=Path("/fake/repo"),
            target_agent="claude",
            exempt_packet_id="rev_pkt_exec",
        )
        self.assertIsNotNone(result)
        self.assertIn("rev_pkt_other", result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate.load_pending_packet_queue"
    )
    def test_queue_gate_blocks_other_acked_action_requests(self, mock_load):
        mock_load.return_value = PendingPacketQueueSnapshot(
            pending_packets=(),
            control_packets=(
                {
                    "packet_id": "rev_pkt_other",
                    "kind": "action_request",
                    "to_agent": "claude",
                    "status": "acked",
                    "requested_action": "stage_commit_pipeline",
                    "policy_hint": "safe_auto_apply",
                    "execution_started_at_utc": "2026-04-29T16:00:00Z",
                    "expires_at_utc": "2999-01-01T00:00:00Z",
                },
            ),
        )
        result = pending_packet_queue_block_commit(
            repo_root=Path("/fake/repo"),
            target_agent="claude",
            exempt_packet_id="rev_pkt_exec",
        )
        self.assertIsNotNone(result)
        self.assertIn("rev_pkt_other", result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate.load_pending_packet_queue"
    )
    def test_queue_gate_ignores_failed_action_requests(self, mock_load):
        mock_load.return_value = PendingPacketQueueSnapshot(
            pending_packets=(
                {
                    "packet_id": "rev_pkt_failed",
                    "kind": "action_request",
                    "to_agent": "claude",
                    "status": "pending",
                    "requested_action": "stage_commit_pipeline",
                    "policy_hint": "safe_auto_apply",
                    "execution_failed_at_utc": "2026-04-29T16:00:00Z",
                },
            ),
        )
        result = pending_packet_queue_block_commit(
            repo_root=Path("/fake/repo"),
            target_agent="claude",
        )
        self.assertIsNone(result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state"
    )
    def test_blocks_when_review_state_unavailable(self, mock_load):
        mock_load.return_value = None
        result = pending_reviewer_packets_block_commit(
            repo_root=None, review_channel_path=Path("/fake/exists"),
        )
        self.assertIsNotNone(result)
        self.assertIn("could not be loaded", result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state"
    )
    def test_blocks_when_no_packet_inbox(self, mock_load):
        mock_load.return_value = SimpleNamespace(packet_inbox=None)
        result = pending_reviewer_packets_block_commit(
            repo_root=None, review_channel_path=Path("/fake/exists"),
        )
        self.assertIsNotNone(result)
        self.assertIn("no packet inbox", result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state"
    )
    def test_blocks_on_load_error(self, mock_load):
        mock_load.side_effect = ValueError("event log corrupt")
        result = pending_reviewer_packets_block_commit(
            repo_root=None, review_channel_path=Path("/fake/exists"),
        )
        self.assertIsNotNone(result)
        self.assertIn("load failed", result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state"
    )
    def test_blocks_on_finding_pending_wake_reason(self, mock_load):
        mock_load.return_value = _make_review_state(
            agents=[
                _make_inbox_record(
                    agent="claude",
                    pending_ids=(),
                    wake_reason="finding_pending",
                ),
            ],
        )
        result = pending_reviewer_packets_block_commit(
            repo_root=None,
            review_channel_path=Path("/fake/exists"),
            target_agent="claude",
        )
        self.assertIsNotNone(result)
        self.assertIn("Commit blocked", result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state"
    )
    def test_target_agent_filters_to_specific_agent(self, mock_load):
        mock_load.return_value = _make_review_state(
            agents=[
                _make_inbox_record(
                    agent="codex",
                    pending_ids=("rev_pkt_100",),
                ),
                _make_inbox_record(
                    agent="claude",
                    pending_ids=(),
                ),
            ],
        )
        # Targeting claude — codex's packets should not block
        result = pending_reviewer_packets_block_commit(
            repo_root=None,
            review_channel_path=Path("/fake/exists"),
            target_agent="claude",
        )
        self.assertIsNone(result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state"
    )
    def test_review_only_instruction_packets_do_not_block_commit(self, mock_load):
        mock_load.return_value = _make_review_state(
            agents=[
                _make_inbox_record(
                    agent="claude",
                    pending_ids=("rev_pkt_0952",),
                ),
            ],
            packets=[
                _make_packet(
                    packet_id="rev_pkt_0952",
                    kind="instruction",
                    to_agent="claude",
                    requested_action="review_only",
                    policy_hint="review_only",
                ),
            ],
        )

        result = pending_reviewer_packets_block_commit(
            repo_root=None,
            review_channel_path=Path("/fake/exists"),
            target_agent="claude",
        )

        self.assertIsNone(result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state"
    )
    def test_review_only_finding_packets_do_not_block_commit(self, mock_load):
        mock_load.return_value = _make_review_state(
            agents=[
                _make_inbox_record(
                    agent="codex",
                    pending_ids=("rev_pkt_finding",),
                    wake_reason="finding_pending",
                ),
            ],
            packets=[
                _make_packet(
                    packet_id="rev_pkt_finding",
                    kind="finding",
                    to_agent="codex",
                ),
            ],
        )

        result = pending_reviewer_packets_block_commit(
            repo_root=None,
            review_channel_path=Path("/fake/exists"),
            target_agent="codex",
        )

        self.assertIsNone(result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state"
    )
    def test_action_request_packets_still_block_commit(self, mock_load):
        mock_load.return_value = _make_review_state(
            agents=[
                _make_inbox_record(
                    agent="codex",
                    pending_ids=("rev_pkt_action",),
                ),
            ],
            packets=[
                _make_packet(
                    packet_id="rev_pkt_action",
                    kind="action_request",
                    to_agent="codex",
                    requested_action="stage_commit_pipeline",
                    policy_hint="safe_auto_apply",
                ),
            ],
        )

        result = pending_reviewer_packets_block_commit(
            repo_root=None,
            review_channel_path=Path("/fake/exists"),
            target_agent="codex",
        )

        self.assertIsNotNone(result)
        self.assertIn("rev_pkt_action", result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state"
    )
    def test_non_review_only_instruction_packets_still_block_commit(self, mock_load):
        mock_load.return_value = _make_review_state(
            agents=[
                _make_inbox_record(
                    agent="claude",
                    pending_ids=("rev_pkt_0953",),
                ),
            ],
            packets=[
                _make_packet(
                    packet_id="rev_pkt_0953",
                    kind="instruction",
                    to_agent="claude",
                    requested_action="run_check",
                    policy_hint="safe_auto_apply",
                ),
            ],
        )

        result = pending_reviewer_packets_block_commit(
            repo_root=None,
            review_channel_path=Path("/fake/exists"),
            target_agent="claude",
        )

        self.assertIsNotNone(result)
        self.assertIn("rev_pkt_0953", result)

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state"
    )
    def test_empty_target_blocks_with_guidance(self, mock_load):
        mock_load.return_value = _make_review_state(
            agents=[
                _make_inbox_record(
                    agent="codex",
                    pending_ids=("rev_pkt_100",),
                ),
            ],
        )
        # Empty target → fail-closed with explicit guidance
        result = pending_reviewer_packets_block_commit(
            repo_root=None, review_channel_path=Path("/fake/exists"),
        )
        self.assertIsNotNone(result)
        self.assertIn("could not be resolved", result)


# ── Lease-independence test ────────────────────────────────────


class TestLeaseDoesNotSuppressGate(unittest.TestCase):
    """Verify the gate blocks even when a lease would suppress the stale check."""

    @patch(
        "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state"
    )
    def test_held_lease_does_not_suppress_pending_packet_gate(self, mock_load):
        """The key regression: a held lease must NOT allow pending packets through.

        This is the exact scenario from rev_pkt_0707: lease acquired before
        reviewer packets arrive, then reviewer posts findings, but the lease
        suppresses the stale check. The gate must still block.
        """
        mock_load.return_value = _make_review_state(
            agents=[
                _make_inbox_record(
                    agent="claude",
                    pending_ids=("rev_pkt_0703", "rev_pkt_0704"),
                ),
            ],
        )
        # Gate has no lease parameter — it's lease-independent by design
        result = pending_reviewer_packets_block_commit(
            repo_root=None,
            review_channel_path=Path("/fake/exists"),
            target_agent="claude",
        )
        self.assertIsNotNone(result)
        self.assertIn("rev_pkt_0703", result)


# ── Actionable attention helper ────────────────────────────────


class TestHasActionableAttention(unittest.TestCase):
    """Test the attention checker mirrors governed_executor_commit_runtime."""

    def test_pending_ids_trigger_attention(self):
        record = _make_inbox_record(pending_ids=("pkt1",))
        self.assertTrue(_has_actionable_attention(record))

    def test_finding_pending_wake_triggers_attention(self):
        record = _make_inbox_record(wake_reason="finding_pending")
        self.assertTrue(_has_actionable_attention(record))

    def test_empty_inbox_no_attention(self):
        record = _make_inbox_record()
        self.assertFalse(_has_actionable_attention(record))

    def test_irrelevant_wake_reason_no_attention(self):
        record = _make_inbox_record(wake_reason="heartbeat_refresh")
        self.assertFalse(_has_actionable_attention(record))


# ---------------------------------------------------------------------------
# Shared helper: check_commit_packet_gate fail-closed contract
# ---------------------------------------------------------------------------


class TestCheckCommitPacketGateFailClosed(unittest.TestCase):
    """Verify check_commit_packet_gate distinguishes missing vs unreadable."""

    def test_none_path_allows(self):
        from dev.scripts.devctl.runtime.commit_packet_gate import (
            check_commit_packet_gate,
        )

        result = check_commit_packet_gate(
            repo_root=Path("/fake"),
            review_channel_path=None,
            load_review_state_fn=lambda: None,
            resolve_target_fn=lambda _: "",
        )
        self.assertIsNone(result)

    def test_nonexistent_path_allows(self, tmp_path=None):
        from dev.scripts.devctl.runtime.commit_packet_gate import (
            check_commit_packet_gate,
        )

        result = check_commit_packet_gate(
            repo_root=Path("/fake"),
            review_channel_path=Path("/nonexistent/review_channel"),
            load_review_state_fn=lambda: None,
            resolve_target_fn=lambda _: "",
        )
        self.assertIsNone(result)

    def test_existing_path_loader_returns_none_blocks(self):
        """Fail-closed: existing path + None state = unreadable = block."""
        import tempfile

        from dev.scripts.devctl.runtime.commit_packet_gate import (
            check_commit_packet_gate,
        )

        with tempfile.TemporaryDirectory() as td:
            rc_path = Path(td) / "review_channel.md"
            rc_path.write_text("exists")
            result = check_commit_packet_gate(
                repo_root=Path(td),
                review_channel_path=rc_path,
                load_review_state_fn=lambda: None,
                resolve_target_fn=lambda _: "",
            )
        self.assertIsNotNone(result)
        self.assertIn("could not be loaded", result)

    def test_existing_path_loader_raises_blocks(self):
        """Fail-closed: existing path + ValueError = block."""
        import tempfile

        from dev.scripts.devctl.runtime.commit_packet_gate import (
            check_commit_packet_gate,
        )

        def _raise():
            raise ValueError("corrupt bundle")

        with tempfile.TemporaryDirectory() as td:
            rc_path = Path(td) / "review_channel.md"
            rc_path.write_text("exists")
            result = check_commit_packet_gate(
                repo_root=Path(td),
                review_channel_path=rc_path,
                load_review_state_fn=_raise,
                resolve_target_fn=lambda _: "",
            )
        self.assertIsNotNone(result)
        self.assertIn("load failed", result)

    def test_existing_path_no_writable_lane_allows(self):
        """No writable lane resolved = skip gate, allow commit."""
        import tempfile

        from dev.scripts.devctl.runtime.commit_packet_gate import (
            check_commit_packet_gate,
        )

        fake_state = SimpleNamespace()
        with tempfile.TemporaryDirectory() as td:
            rc_path = Path(td) / "review_channel.md"
            rc_path.write_text("exists")
            result = check_commit_packet_gate(
                repo_root=Path(td),
                review_channel_path=rc_path,
                load_review_state_fn=lambda: fake_state,
                resolve_target_fn=lambda _: "",
            )
        self.assertIsNone(result)


class TestMalformedPacketInboxFailsClosed(unittest.TestCase):
    """Regression: malformed packet_inbox.agents must not crash the gate."""

    def test_agents_none_blocks_closed(self):
        """packet_inbox with agents=None must block (fail-closed), not allow."""
        inbox = SimpleNamespace(agents=None, attention_revision="rev-1")
        fake_state = SimpleNamespace(packet_inbox=inbox)
        rc_path = Path("/tmp/fake_review_channel")
        with patch.object(rc_path.__class__, "exists", return_value=True):
            with patch(
                "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state",
                return_value=fake_state,
            ):
                result = pending_reviewer_packets_block_commit(
                    repo_root=Path("/tmp/fake_repo"),
                    review_channel_path=rc_path,
                    target_agent="claude",
                )
        self.assertIsNotNone(result)
        self.assertIn("malformed", result)

    def test_agents_missing_attr_blocks_closed(self):
        """packet_inbox without agents attr must block, not crash or allow."""
        inbox = SimpleNamespace(attention_revision="rev-1")
        fake_state = SimpleNamespace(packet_inbox=inbox)
        rc_path = Path("/tmp/fake_review_channel")
        with patch.object(rc_path.__class__, "exists", return_value=True):
            with patch(
                "dev.scripts.devctl.runtime.commit_packet_gate._load_review_state",
                return_value=fake_state,
            ):
                result = pending_reviewer_packets_block_commit(
                    repo_root=Path("/tmp/fake_repo"),
                    review_channel_path=rc_path,
                    target_agent="claude",
                )
        self.assertIsNotNone(result)
        self.assertIn("malformed", result)


if __name__ == "__main__":
    unittest.main()
