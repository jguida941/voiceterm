"""Focused tests for reviewer prompt session-resume preamble rendering."""

from __future__ import annotations

from dev.scripts.devctl.commands.governance.session_resume_support import (
    SessionCachePacket,
)
from dev.scripts.devctl.platform.coordination_snapshot_models import (
    CoordinationSnapshot,
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


def test_format_session_resume_preamble_for_implementer_includes_coordination() -> None:
    packet = SessionCachePacket(
        role="implementer",
        coordination=CoordinationSnapshot(
            current_slice="Continue the coordination bootstrap slice.",
            declared_topology="multi_agent_orchestrated",
            observed_topology="single_agent",
            recommended_topology="single_agent",
            fanout_posture="planned_scaffolding_only",
            safe_to_fanout=False,
            worktree_strategy="isolated_worker_worktrees",
            resync_required=True,
            resync_reasons=("declared_topology:multi_agent_orchestrated",),
        ),
    )

    preamble = _format_session_resume_preamble(packet)

    assert "Coordination:" in preamble
    assert "Current governed slice" in preamble
    assert "safe_to_fanout=False" in preamble
    assert "Review the diff with:" not in preamble
