from __future__ import annotations

import subprocess
from pathlib import Path

from dev.scripts.devctl.remote_evidence_queue import (
    find_finding_affected_paths_in_current_tree,
    freshness_for_finding_in_current_tree,
    remote_validation_receipt_from_mapping,
)
from dev.scripts.devctl.runtime.finding_contracts import FindingRecord


def test_finding_path_present_in_later_tree_stays_relevant(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('old')\n")
    _git(repo, "add", "src/app.py")
    _git(repo, "commit", "-m", "add app")
    applies_to = _git(repo, "rev-parse", "HEAD")

    (repo / "README.md").write_text("docs\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "docs")
    current = _git(repo, "rev-parse", "HEAD")

    finding = _finding("src/app.py")

    assert (
        find_finding_affected_paths_in_current_tree(
            finding,
            applies_to,
            current,
            repo_root=repo,
        )
        == "present"
    )
    assert (
        freshness_for_finding_in_current_tree(
            finding,
            applies_to,
            current,
            repo_root=repo,
        )
        == "stale_but_relevant"
    )


def test_finding_path_absent_in_current_tree_is_superseded(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('old')\n")
    _git(repo, "add", "src/app.py")
    _git(repo, "commit", "-m", "add app")
    applies_to = _git(repo, "rev-parse", "HEAD")

    _git(repo, "rm", "src/app.py")
    _git(repo, "commit", "-m", "remove app")
    current = _git(repo, "rev-parse", "HEAD")

    finding = _finding("src/app.py")

    assert (
        find_finding_affected_paths_in_current_tree(
            finding,
            applies_to,
            current,
            repo_root=repo,
        )
        == "absent"
    )
    assert (
        freshness_for_finding_in_current_tree(
            finding,
            applies_to,
            current,
            repo_root=repo,
        )
        == "stale_and_superseded"
    )


def test_finding_path_renamed_in_current_tree_stays_relevant(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('old')\n")
    _git(repo, "add", "src/app.py")
    _git(repo, "commit", "-m", "add app")
    applies_to = _git(repo, "rev-parse", "HEAD")

    _git(repo, "mv", "src/app.py", "src/main.py")
    _git(repo, "commit", "-m", "rename app")
    current = _git(repo, "rev-parse", "HEAD")

    finding = _finding("src/app.py")

    assert (
        find_finding_affected_paths_in_current_tree(
            finding,
            applies_to,
            current,
            repo_root=repo,
        )
        == "moved"
    )
    assert (
        freshness_for_finding_in_current_tree(
            finding,
            applies_to,
            current,
            repo_root=repo,
        )
        == "stale_but_relevant"
    )


def test_current_tree_freshness_for_same_tree(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('old')\n")
    _git(repo, "add", "src/app.py")
    _git(repo, "commit", "-m", "add app")
    current = _git(repo, "rev-parse", "HEAD")

    assert (
        freshness_for_finding_in_current_tree(
            _finding("src/app.py"),
            current,
            current,
            repo_root=repo,
        )
        == "current"
    )


def test_remote_validation_receipt_mapping_normalizes_fields() -> None:
    receipt = remote_validation_receipt_from_mapping(
        {
            "receipt_id": "rv-1",
            "status": "completed_failed",
            "applies_to_tree": "tree-a",
            "current_tree": "tree-b",
            "freshness": "stale_but_relevant",
            "failed_checks": ["mutation"],
            "recommended_next_actions": ["repair finding"],
            "blocked_actions": ["close current slice"],
            "artifact_bundle_ref": "artifact:bundle-1",
            "plan_row_id": "PKT-BIND-REV-PKT-3996",
        }
    )

    assert receipt.contract_id == "RemoteValidationReceipt"
    assert receipt.status == "completed_failed"
    assert receipt.freshness == "stale_but_relevant"
    assert receipt.failed_checks == ("mutation",)
    assert receipt.recommended_next_action == ("repair finding",)
    assert receipt.blocked_actions == ("close current slice",)


def _git_repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "codex@example.test")
    _git(tmp_path, "config", "user.name", "Codex")
    return tmp_path


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _finding(path: str) -> FindingRecord:
    return FindingRecord(
        schema_version=1,
        contract_id="Finding",
        finding_id="finding-1",
        signal_type="probe",
        check_id="check",
        rule_id="rule",
        rule_version=1,
        repo_name="repo",
        repo_path="",
        file_path=path,
    )
