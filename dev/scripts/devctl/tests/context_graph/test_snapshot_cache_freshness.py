"""Tests for snapshot cache freshness validation (rev_pkt_0832).

Verifies that both ``snapshot_cache_is_fresh`` and ``resolve_head_sha``
correctly reject stale or HEAD-mismatched snapshots so that context
queries never silently serve data from weeks-old commits.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.context_graph.snapshot_payload import (
    _SNAPSHOT_CACHE_MAX_AGE,
    resolve_head_sha,
    snapshot_cache_is_fresh,
)


def _snapshot_path(commit_hash: str, timestamp: datetime) -> Path:
    """Build a synthetic snapshot path matching the real naming convention."""
    slug = timestamp.strftime("%Y%m%dT%H%M%SZ")
    return Path(f"/tmp/snapshots/{commit_hash}_{slug}.json")


class TestSnapshotCacheIsFresh(unittest.TestCase):
    """Verify snapshot_cache_is_fresh rejects stale/mismatched snapshots."""

    def test_matching_head_and_recent_timestamp_returns_true(self) -> None:
        now = datetime.now(timezone.utc)
        path = _snapshot_path("abc123", now - timedelta(minutes=10))
        self.assertTrue(snapshot_cache_is_fresh(path, "abc123"))

    def test_different_head_sha_returns_false(self) -> None:
        now = datetime.now(timezone.utc)
        path = _snapshot_path("abc123", now - timedelta(minutes=1))
        self.assertFalse(snapshot_cache_is_fresh(path, "def456"))

    def test_empty_head_sha_returns_false(self) -> None:
        now = datetime.now(timezone.utc)
        path = _snapshot_path("abc123", now)
        self.assertFalse(snapshot_cache_is_fresh(path, ""))

    def test_snapshot_older_than_threshold_returns_false(self) -> None:
        old_time = datetime.now(timezone.utc) - _SNAPSHOT_CACHE_MAX_AGE - timedelta(minutes=5)
        path = _snapshot_path("abc123", old_time)
        self.assertFalse(snapshot_cache_is_fresh(path, "abc123"))

    def test_snapshot_just_inside_threshold_returns_true(self) -> None:
        # Use a 30-second buffer inside the threshold to avoid clock-race
        boundary = datetime.now(timezone.utc) - _SNAPSHOT_CACHE_MAX_AGE + timedelta(seconds=30)
        path = _snapshot_path("abc123", boundary)
        self.assertTrue(snapshot_cache_is_fresh(path, "abc123"))

    def test_malformed_filename_no_underscore_returns_false(self) -> None:
        path = Path("/tmp/snapshots/abc123.json")
        self.assertFalse(snapshot_cache_is_fresh(path, "abc123"))

    def test_malformed_timestamp_returns_false(self) -> None:
        path = Path("/tmp/snapshots/abc123_not-a-timestamp.json")
        self.assertFalse(snapshot_cache_is_fresh(path, "abc123"))

    def test_full_length_sha_matches(self) -> None:
        sha = "feb1f8a164467ff2a0e75e1a04fdb932c99a2a60"
        now = datetime.now(timezone.utc)
        path = _snapshot_path(sha, now - timedelta(minutes=30))
        self.assertTrue(snapshot_cache_is_fresh(path, sha))

    def test_full_length_sha_mismatch(self) -> None:
        old_sha = "feb1f8a164467ff2a0e75e1a04fdb932c99a2a60"
        new_sha = "9a4238f18f377b34741e72fd0effc1498eecbc82"
        now = datetime.now(timezone.utc)
        path = _snapshot_path(old_sha, now - timedelta(minutes=5))
        self.assertFalse(snapshot_cache_is_fresh(path, new_sha))


class TestResolveHeadSha(unittest.TestCase):
    """Verify resolve_head_sha handles subprocess failures gracefully."""

    def test_returns_empty_string_on_os_error(self) -> None:
        with patch("subprocess.run", side_effect=OSError("no git")):
            result = resolve_head_sha(Path("/nonexistent"))
        self.assertEqual(result, "")

    def test_returns_empty_string_on_nonzero_exit(self) -> None:
        mock_result = type("R", (), {"returncode": 128, "stdout": ""})()
        with patch("subprocess.run", return_value=mock_result):
            result = resolve_head_sha(Path("/tmp"))
        self.assertEqual(result, "")

    def test_returns_stripped_sha_on_success(self) -> None:
        mock_result = type("R", (), {
            "returncode": 0,
            "stdout": "  abc123def456  \n",
        })()
        with patch("subprocess.run", return_value=mock_result):
            result = resolve_head_sha(Path("/tmp"))
        self.assertEqual(result, "abc123def456")
