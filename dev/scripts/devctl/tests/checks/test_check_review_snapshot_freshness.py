"""Tests for the ReviewSnapshot freshness guard."""

from __future__ import annotations

from pathlib import Path

import pytest

from dev.scripts.checks.check_review_snapshot_freshness import build_report


_FRESH_FILE = """# Example — Review Snapshot

## Quick status

- Branch: `feature/test`
- HEAD: `abc123def456` — Test commit
- Tree hash: `deadbeef1234`
- Generation stamp: `snap-aaaaaaaaaaaa`
- Generated at (UTC): 2026-04-07T20:00:00Z
"""

_MISSING_HEAD = """# Example

## Quick status

- Branch: `main`
- Generation stamp: `snap-aaaaaaaaaaaa`
"""

_STALE_HEAD = """# Example

## Quick status

- HEAD: `ffff11112222` — Stale commit
- Generation stamp: `snap-aaaaaaaaaaaa`
"""

_STALE_STAMP = """# Example

## Quick status

- HEAD: `abc123def456` — Test commit
- Generation stamp: `snap-ZZZZZZZZZZZZ`
"""


def test_build_report_ok_when_head_and_stamp_match(tmp_path: Path) -> None:
    report = build_report(
        repo_root=tmp_path,
        snapshot_override_text=_FRESH_FILE,
        live_head_sha="abc123def456abc123def456abc123def456dead",
        live_generation_stamp="snap-aaaaaaaaaaaa",
    )
    assert report["ok"] is True
    assert report["errors"] == []
    assert report["embedded_head"] == "abc123def456"
    assert report["embedded_generation_stamp"] == "snap-aaaaaaaaaaaa"


def test_build_report_fails_when_head_drifted(tmp_path: Path) -> None:
    report = build_report(
        repo_root=tmp_path,
        snapshot_override_text=_STALE_HEAD,
        live_head_sha="1111111111112222222222223333333333334444",
        live_generation_stamp="snap-aaaaaaaaaaaa",
    )
    assert report["ok"] is False
    assert any("snapshot_head_drift" in err for err in report["errors"])  # type: ignore[arg-type]


def test_build_report_fails_when_generation_stamp_drifted(tmp_path: Path) -> None:
    report = build_report(
        repo_root=tmp_path,
        snapshot_override_text=_STALE_STAMP,
        live_head_sha="abc123def456abc123def456abc123def456dead",
        live_generation_stamp="snap-bbbbbbbbbbbb",
    )
    assert report["ok"] is False
    assert any("snapshot_generation_drift" in err for err in report["errors"])  # type: ignore[arg-type]


def test_build_report_fails_when_head_line_missing(tmp_path: Path) -> None:
    report = build_report(
        repo_root=tmp_path,
        snapshot_override_text=_MISSING_HEAD,
        live_head_sha="abc123def456abc123def456abc123def456dead",
        live_generation_stamp="snap-aaaaaaaaaaaa",
    )
    assert report["ok"] is False
    assert any("snapshot_header_missing_head" in err for err in report["errors"])  # type: ignore[arg-type]


def test_build_report_fails_when_snapshot_file_missing(tmp_path: Path) -> None:
    report = build_report(
        repo_root=tmp_path,
        snapshot_override_text=None,
        live_head_sha="abc123def456abc123def456abc123def456dead",
        live_generation_stamp="snap-aaaaaaaaaaaa",
    )
    assert report["ok"] is False
    assert any("snapshot_missing" in err for err in report["errors"])  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "embedded,live,expected_ok",
    [
        ("abc123def456", "abc123def456abc123def456abc123def456dead", True),
        ("abc123def456", "abc123def456deadbeefdeadbeefdeadbeefdead", True),
        ("abc123def456", "999999999999dead", False),
    ],
)
def test_build_report_accepts_short_sha_prefix(
    tmp_path: Path, embedded: str, live: str, expected_ok: bool
) -> None:
    text = _FRESH_FILE.replace("abc123def456", embedded)
    report = build_report(
        repo_root=tmp_path,
        snapshot_override_text=text,
        live_head_sha=live,
        live_generation_stamp="snap-aaaaaaaaaaaa",
    )
    assert report["ok"] is expected_ok
