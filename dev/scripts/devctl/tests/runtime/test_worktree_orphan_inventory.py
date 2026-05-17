"""Tests for report-only worktree-orphan inventory scanning."""

from __future__ import annotations

import subprocess
from pathlib import Path

from dev.scripts.devctl.runtime.worktree_orphan_contracts import (
    OrphanInventoryReport,
    build_orphan_inventory_report,
    contract_json_schemas,
    orphan_inventory_report_from_mapping,
)


def test_inventory_reports_bridge_projection_drift_as_governed_auto_sync(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path / "codex-voice")
    _write(repo / "bridge.md", "old ack\n")
    _git(repo, "add", "bridge.md")
    _git(repo, "commit", "-m", "track bridge")
    _write(repo / "bridge.md", "new ack\n")

    report = build_orphan_inventory_report(
        repo_root=repo,
        review_state={},
        generated_at_utc="2026-04-22T18:30:00Z",
    )

    current = _source_by_kind(report, "current_checkout")
    assert current is not None
    assert current.classification.known_governed_auto_sync is True
    assert current.classification.load_bearing is False
    assert current.dirty_path_count == 1


def test_inventory_detects_bounded_same_parent_sibling_clone(
    tmp_path: Path,
) -> None:
    parent = tmp_path
    repo = _init_repo(parent / "codex-voice")
    sibling = _init_repo(parent / "codex-voice 2")
    _git(sibling, "remote", "set-url", "origin", "https://example.invalid/repo.git")
    _write(sibling / "dirty.txt", "changed\n")

    report = build_orphan_inventory_report(
        repo_root=repo,
        review_state={},
        generated_at_utc="2026-04-22T18:31:00Z",
    )

    sibling_source = _source_by_kind(report, "unregistered_sibling_clone")
    assert sibling_source is not None
    assert sibling_source.path == str(sibling.resolve())
    assert sibling_source.classification.load_bearing is True
    assert sibling_source.untracked_path_count == 1


def test_inventory_detects_planned_lane_without_realized_worktree(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path / "codex-voice")
    review_state = {
        "review_state": {
            "coordination": {
                "actors": [
                    {
                        "actor_id": "AGENT-9",
                        "presence": "planned",
                        "lane": "Claude bridge push-safety fixes",
                        "mp_scope": "MP-303, MP-306, MP-355",
                        "worktree": "../codex-voice-wt-a9",
                        "branch": "feature/a9-claude-bridge-push-safety",
                    }
                ]
            }
        }
    }

    report = build_orphan_inventory_report(
        repo_root=repo,
        review_state=review_state,
        generated_at_utc="2026-04-22T18:32:00Z",
    )

    planned = _source_by_kind(report, "planned_delegated_worker_worktree")
    assert planned is not None
    assert planned.source_ref == "planned-lane:AGENT-9"
    assert planned.metadata["realization_status"] == "worktree_missing"
    assert planned.metadata["declared_worktree_path"] == "../codex-voice-wt-a9"


def test_inventory_detects_multi_section_stash_orphan(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path / "codex-voice")
    _write(repo / "tracked.txt", "tracked base\n")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "track file")
    _write(repo / "tracked.txt", "tracked change\n")
    _write(repo / "untracked.txt", "untracked change\n")
    _git(repo, "stash", "push", "--include-untracked", "-m", "inventory fixture")

    report = build_orphan_inventory_report(
        repo_root=repo,
        review_state={},
        generated_at_utc="2026-04-22T18:33:00Z",
    )

    stash = _source_by_kind(report, "stash_orphan")
    assert stash is not None
    assert stash.classification.load_bearing is True
    assert stash.metadata["stash_sections"] == ["working_tree", "index", "untracked"]
    assert "untracked.txt" in stash.metadata["file_paths"]


def test_startup_context_inventory_omits_expensive_stash_file_details(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path / "codex-voice")
    _write(repo / "tracked.txt", "tracked base\n")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "track file")
    _write(repo / "tracked.txt", "tracked change\n")
    _write(repo / "untracked.txt", "untracked change\n")
    _git(repo, "stash", "push", "--include-untracked", "-m", "startup fixture")

    report = build_orphan_inventory_report(
        repo_root=repo,
        review_state={},
        scan_scope="startup_context",
        generated_at_utc="2026-04-22T18:33:30Z",
    )

    stash = _source_by_kind(report, "stash_orphan")
    assert stash is not None
    assert stash.metadata["stash_sections"] == []
    assert stash.metadata["file_paths"] == []
    assert "stash file-path detail omitted" in "; ".join(report.warnings)


def test_orphan_inventory_report_schema_and_round_trip(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "codex-voice")
    report = build_orphan_inventory_report(
        repo_root=repo,
        review_state={},
        generated_at_utc="2026-04-22T18:34:00Z",
    )

    payload = report.to_dict()
    schema = contract_json_schemas()["OrphanInventoryReport"]
    properties = schema["properties"]
    assert isinstance(properties, dict)
    for key in schema["required"]:
        assert key in payload
        assert key in properties

    restored = orphan_inventory_report_from_mapping(payload)
    assert isinstance(restored, OrphanInventoryReport)
    assert restored == report


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    _git(path, "init", "-b", "main")
    _git(path, "config", "user.email", "dev@example.invalid")
    _git(path, "config", "user.name", "Dev")
    _write(path / "README.md", "repo\n")
    _git(path, "add", "README.md")
    _git(path, "commit", "-m", "initial")
    _git(path, "remote", "add", "origin", "https://example.invalid/repo.git")
    return path


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return (completed.stdout or "").strip()


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _source_by_kind(report, kind: str):
    for source in report.sources:
        if source.source_kind == kind:
            return source
    return None
