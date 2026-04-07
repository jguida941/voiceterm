"""Leg 3 tests: typed continuity gates session-resume cache freshness.

These tests lock in the load-bearing consumer for
``WorkIntakePacket.continuity.alignment_status``. When the plan target and
the live review state have drifted, ``try_cache_hit`` must refuse to honor
a cached packet even if head/role/mtime all match, so downstream callers
rebuild the session state against the current target. They replace the
prior strict-xfail hard-trace
``test_alignment_status_is_consumed_by_a_production_decision`` once the
consumer actually exists.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl.commands.governance.session_resume_support import (
    SessionCachePacket,
    try_cache_hit,
)
from dev.scripts.devctl.runtime.work_intake_models import SessionContinuityState


def _write_cache_packet(root: Path, packet: SessionCachePacket) -> None:
    cache_dir = root / "dev" / "reports" / "session_cache" / "latest"
    cache_dir.mkdir(parents=True)
    (cache_dir / "cache.json").write_text(json.dumps(packet.to_dict()))


class TestSessionCacheContinuityGate(unittest.TestCase):
    """``try_cache_hit`` must honor typed continuity state."""

    def _base_packet(self) -> SessionCachePacket:
        return SessionCachePacket(
            head_sha="abc123",
            role="implementer",
            branch="feature/foo",
            review_state_mtime=42.0,
        )

    def test_try_cache_hit_invalidates_on_continuity_drift(self) -> None:
        """Stale ``alignment_status`` forces a cache miss (Leg 3 forcing function)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_cache_packet(root, self._base_packet())
            drift = SessionContinuityState(
                source_plan_path="dev/active/foo.md",
                source_scope="MP-377",
                review_scope="MP-999",
                review_instruction="unrelated work",
                alignment_status="needs_review",
                alignment_reason="plan_review_mismatch",
            )
            result = try_cache_hit(
                root,
                head_sha="abc123",
                role="implementer",
                review_state_mtime=42.0,
                continuity=drift,
            )
            self.assertIsNone(result)

    def test_try_cache_hit_invalidates_on_plan_only_continuity(self) -> None:
        """A ``plan_only`` continuity (no typed review state) also misses."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_cache_packet(root, self._base_packet())
            drift = SessionContinuityState(
                source_plan_path="dev/active/foo.md",
                source_scope="MP-377",
                alignment_status="plan_only",
                alignment_reason="no_typed_review_state",
            )
            result = try_cache_hit(
                root,
                head_sha="abc123",
                role="implementer",
                review_state_mtime=42.0,
                continuity=drift,
            )
            self.assertIsNone(result)

    def test_try_cache_hit_invalidates_on_review_only_continuity(self) -> None:
        """A ``review_only`` continuity (plan resume missing) also misses."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_cache_packet(root, self._base_packet())
            drift = SessionContinuityState(
                review_scope="MP-377",
                review_instruction="continue the thing",
                alignment_status="review_only",
                alignment_reason="no_plan_session_resume",
            )
            result = try_cache_hit(
                root,
                head_sha="abc123",
                role="implementer",
                review_state_mtime=42.0,
                continuity=drift,
            )
            self.assertIsNone(result)

    def test_try_cache_hit_invalidates_on_missing_continuity(self) -> None:
        """A ``missing`` continuity (neither plan nor review) also misses."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_cache_packet(root, self._base_packet())
            drift = SessionContinuityState(
                alignment_status="missing",
                alignment_reason="no_plan_resume_or_review_state",
            )
            result = try_cache_hit(
                root,
                head_sha="abc123",
                role="implementer",
                review_state_mtime=42.0,
                continuity=drift,
            )
            self.assertIsNone(result)

    def test_try_cache_hit_honors_aligned_continuity(self) -> None:
        """A fresh (``aligned``) continuity leaves the cache hit intact."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_cache_packet(root, self._base_packet())
            fresh = SessionContinuityState(
                source_plan_path="dev/active/foo.md",
                source_scope="MP-377",
                review_scope="MP-377",
                review_instruction="continue MP-377",
                alignment_status="aligned",
                alignment_reason="scope_and_instruction_match",
            )
            result = try_cache_hit(
                root,
                head_sha="abc123",
                role="implementer",
                review_state_mtime=42.0,
                continuity=fresh,
            )
            self.assertIsNotNone(result)
            self.assertEqual(result.head_sha, "abc123")
            self.assertEqual(result.branch, "feature/foo")

    def test_try_cache_hit_honors_scope_aligned_continuity(self) -> None:
        """``scope_aligned`` is also a fresh state that leaves the cache intact."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_cache_packet(root, self._base_packet())
            fresh = SessionContinuityState(
                source_scope="MP-377",
                review_scope="MP-377",
                alignment_status="scope_aligned",
                alignment_reason="review_scope_matches_plan_target",
            )
            result = try_cache_hit(
                root,
                head_sha="abc123",
                role="implementer",
                review_state_mtime=42.0,
                continuity=fresh,
            )
            self.assertIsNotNone(result)

    def test_try_cache_hit_without_continuity_preserves_legacy_behavior(self) -> None:
        """Omitting ``continuity`` keeps the head/role/mtime-only gate."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_cache_packet(root, self._base_packet())
            result = try_cache_hit(
                root,
                head_sha="abc123",
                role="implementer",
                review_state_mtime=42.0,
            )
            self.assertIsNotNone(result)
            self.assertEqual(result.head_sha, "abc123")


if __name__ == "__main__":
    unittest.main()
