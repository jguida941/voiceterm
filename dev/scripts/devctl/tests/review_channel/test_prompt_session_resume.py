"""Focused tests for reviewer prompt session-resume preamble rendering."""

from __future__ import annotations

from dev.scripts.devctl.commands.governance.session_resume_support import (
    SessionCachePacket,
)
from dev.scripts.devctl.review_channel.prompt_session_resume import (
    _format_session_resume_preamble,
)
from dev.scripts.devctl.runtime.review_state_models import ReviewCandidateRecord


def test_format_session_resume_preamble_prefers_review_candidate() -> None:
    packet = SessionCachePacket(
        role="reviewer",
        head_sha="bbbbbbbbbbbbbbbb",
        last_reviewed_sha="aaaaaaaaaaaaaaaa",
        review_candidate=ReviewCandidateRecord(
            candidate_id="review-candidate-123",
            instruction_revision="rev-123",
            artifact_kind="dirty_tree",
            base_sha="aaaaaaaaaaaaaaaa",
            head_sha="bbbbbbbbbbbbbbbb",
            worktree_hash="c" * 64,
            changed_paths=("tracked.txt", "bridge.md"),
            implementer_status_written=True,
            ready_for_review=True,
            valid=True,
            implementer_state_hash="state-123",
        ),
    )

    preamble = _format_session_resume_preamble(packet)

    assert "Frozen review candidate" in preamble
    assert "review-candidate-123" in preamble
    assert "dirty-tree state" in preamble
    assert "tracked.txt" in preamble
    assert "Review the diff with:" not in preamble
