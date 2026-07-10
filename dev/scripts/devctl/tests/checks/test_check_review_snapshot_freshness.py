"""Tests for the ReviewSnapshot freshness guard."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from dev.scripts.checks.review_snapshot_freshness.command import build_report


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


def test_build_report_accepts_snapshot_only_parent_binding(tmp_path: Path) -> None:
    report = build_report(
        repo_root=tmp_path,
        snapshot_override_text=_FRESH_FILE,
        live_head_sha="9999999999992222222222223333333333334444",
        live_generation_stamp="snap-bbbbbbbbbbbb",
        live_snapshot_parent_sha="abc123def456abc123def456abc123def456dead",
    )
    assert report["ok"] is True
    assert report["errors"] == []
    assert report["snapshot_only_parent_match"] is True


def test_build_report_accepts_receipt_commit_with_snapshot_and_bridge(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)

    snapshot_path = repo_root / "dev/audits/REVIEW_SNAPSHOT.md"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text("# Seed snapshot\n", encoding="utf-8")
    (repo_root / "bridge.md").write_text("seed bridge\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "dev/audits/REVIEW_SNAPSHOT.md", "bridge.md"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Seed receipt artifacts"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    (repo_root / "code.py").write_text("print('governed')\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "code.py"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Code change"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    parent_head = _git_output(repo_root, "rev-parse", "HEAD")
    parent_short = _git_output(repo_root, "rev-parse", "--short", "HEAD")
    snapshot_path.write_text(
        "\n".join(
            [
                "# Example — Review Snapshot",
                "",
                "## Quick status",
                "",
                f"- Branch: `feature/test`",
                f"- HEAD: `{parent_short}` — Code change",
                "- Tree hash: `deadbeef1234`",
                "- Generation stamp: `snap-oldreceipt`",
                "- Generated at (UTC): 2026-04-07T20:00:00Z",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (repo_root / "bridge.md").write_text("receipt bridge refresh\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "dev/audits/REVIEW_SNAPSHOT.md", "bridge.md"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", f"Refresh external review snapshot for {parent_short}"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    report = build_report(
        repo_root=repo_root,
        live_head_sha=_git_output(repo_root, "rev-parse", "HEAD"),
        live_generation_stamp="snap-newreceipt",
    )

    assert report["ok"] is True
    assert report["errors"] == []
    assert report["snapshot_only_parent_match"] is True
    assert str(report["snapshot_only_parent_head"]).startswith(parent_head)


def test_build_report_accepts_snapshot_bound_to_receipt_chain_ancestor(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)

    snapshot_path = repo_root / "dev/audits/REVIEW_SNAPSHOT.md"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text("# Seed snapshot\n", encoding="utf-8")
    bridge_path = repo_root / "bridge.md"
    bridge_path.write_text("seed bridge\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "dev/audits/REVIEW_SNAPSHOT.md", "bridge.md"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Seed receipt artifacts"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    (repo_root / "code.py").write_text("print('governed')\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "code.py"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Code change"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    content_short = _git_output(repo_root, "rev-parse", "--short", "HEAD")

    bridge_path.write_text("receipt bridge refresh 1\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "bridge.md"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"Refresh external review snapshot for {content_short}",
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    first_receipt = _git_output(repo_root, "rev-parse", "HEAD")
    first_receipt_short = _git_output(repo_root, "rev-parse", "--short", "HEAD")

    snapshot_path.write_text(
        "\n".join(
            [
                "# Example — Review Snapshot",
                "",
                "## Quick status",
                "",
                "- Branch: `feature/test`",
                f"- HEAD: `{first_receipt_short}` — Managed receipt",
                "- Tree hash: `deadbeef1234`",
                "- Generation stamp: `snap-receiptchain`",
                "- Generated at (UTC): 2026-04-07T20:00:00Z",
                "",
            ]
        ),
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "dev/audits/REVIEW_SNAPSHOT.md"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"Refresh external review snapshot for {first_receipt_short}",
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    bridge_path.write_text("receipt bridge refresh 2\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "bridge.md"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "Refresh external review snapshot for "
            f"{_git_output(repo_root, 'rev-parse', '--short', 'HEAD')}",
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    report = build_report(
        repo_root=repo_root,
        live_head_sha=_git_output(repo_root, "rev-parse", "HEAD"),
        live_generation_stamp="snap-live-different",
    )

    assert report["ok"] is True
    assert report["errors"] == []
    assert report["snapshot_receipt_chain_match"] is True
    assert first_receipt in report["snapshot_receipt_ancestor_heads"]


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


def _init_git_repo(repo_root: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )


def _git_output(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        check=True,
        capture_output=True,
    )
    return completed.stdout.strip()
