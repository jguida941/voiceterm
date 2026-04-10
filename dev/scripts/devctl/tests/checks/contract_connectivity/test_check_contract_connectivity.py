"""Tests for the contract-connectivity guard."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from dev.scripts.checks.contract_connectivity.report import build_report
from dev.scripts.devctl.tests.vcs._git_helpers import _run_git


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _init_repo(path: Path) -> None:
    _run_git(path, "init", "-q")


def _commit(path: Path, message: str) -> None:
    _run_git(path, "add", "-A")
    env = dict(os.environ)
    env.update(
        {
            "GIT_AUTHOR_NAME": "Tests",
            "GIT_AUTHOR_EMAIL": "tests@example.com",
            "GIT_COMMITTER_NAME": "Tests",
            "GIT_COMMITTER_EMAIL": "tests@example.com",
        }
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", message],
        cwd=path,
        check=True,
        env=env,
    )


def _rev_parse(path: Path, rev: str) -> str:
    return _run_git(path, "rev-parse", rev)


def _seed_repo(path: Path) -> None:
    _write(
        path / "dev/scripts/devctl/runtime/coord_contract.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class CoordContract:
    owner: str
    resync_required: bool
""".strip()
        + "\n",
    )
    _write(
        path / "dev/scripts/devctl/governance/use_coord.py",
        """
from ..runtime.coord_contract import CoordContract

def build() -> CoordContract:
    return CoordContract(owner="codex", resync_required=False)
""".strip()
        + "\n",
    )
    _write(
        path / "dev/scripts/devctl/platform/orphan_contract.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class OrphanContract:
    stray: str
""".strip()
        + "\n",
    )
    _write(
        path / "dev/scripts/devctl/governance/duplicate_a.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class DuplicateA:
    alpha: str
    beta: str
    gamma: str
""".strip()
        + "\n",
    )
    _write(
        path / "dev/scripts/devctl/platform/duplicate_b.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class DuplicateB:
    alpha: str
    beta: str
    gamma: str
""".strip()
        + "\n",
    )
    _write(
        path / "dev/scripts/devctl/runtime/stranded_consumer.py",
        """
def owner(payload: dict[str, object]) -> tuple[str, bool]:
    coordination = payload.get("coordination", {})
    return coordination.get("owner", ""), coordination.get("resync_required", False)
""".strip()
        + "\n",
    )


def test_absolute_report_detects_orphans_duplicates_and_stranded(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _seed_repo(tmp_path)
    _commit(tmp_path, "baseline")

    report = build_report(repo_root=tmp_path, absolute=True)

    assert report.ok is False
    assert len(report.orphaned_contracts) == 1
    assert report.orphaned_contracts[0].contract_name == "OrphanContract"
    assert len(report.duplicate_contracts) == 1
    assert {
        report.duplicate_contracts[0].left_contract_name,
        report.duplicate_contracts[0].right_contract_name,
    } == {"DuplicateA", "DuplicateB"}
    assert len(report.stranded_consumers) == 1
    assert report.stranded_consumers[0].consumer_path.endswith(
        "runtime/stranded_consumer.py"
    )


def test_working_tree_mode_blocks_only_new_orphans(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _seed_repo(tmp_path)
    _commit(tmp_path, "baseline")
    _write(
        tmp_path / "dev/scripts/devctl/runtime/unrelated_edit.py",
        "def noop() -> str:\n    return 'ok'\n",
    )

    report = build_report(repo_root=tmp_path)

    assert report.ok is True
    assert len(report.orphaned_contracts) == 1
    assert len(report.new_orphaned_contracts) == 0
    assert len(report.new_duplicate_contracts) == 0
    assert len(report.new_stranded_consumers) == 0


def test_working_tree_mode_flags_new_orphaned_contract(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _seed_repo(tmp_path)
    _commit(tmp_path, "baseline")
    _write(
        tmp_path / "dev/scripts/devctl/runtime/new_orphan.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class NewOrphan:
    field: str
""".strip()
        + "\n",
    )

    report = build_report(repo_root=tmp_path)

    assert report.ok is False
    assert len(report.orphaned_contracts) == 2
    assert [item.contract_name for item in report.new_orphaned_contracts] == [
        "NewOrphan"
    ]


def test_commit_range_mode_flags_new_orphaned_contract(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _seed_repo(tmp_path)
    _commit(tmp_path, "baseline")
    baseline_ref = _rev_parse(tmp_path, "HEAD")
    _write(
        tmp_path / "dev/scripts/devctl/runtime/range_orphan.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class RangeOrphan:
    field: str
""".strip()
        + "\n",
    )
    _commit(tmp_path, "add range orphan")

    report = build_report(
        repo_root=tmp_path,
        since_ref=baseline_ref,
        head_ref="HEAD",
    )

    assert report.mode == "commit-range"
    assert report.ok is False
    assert [item.contract_name for item in report.new_orphaned_contracts] == [
        "RangeOrphan"
    ]


def test_partial_raw_key_overlap_does_not_flag_stranded_consumer(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    _write(
        tmp_path / "dev/scripts/devctl/runtime/peer_context.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class PeerContext:
    live_agents: tuple[str, ...]
    live_delegated_agents: tuple[str, ...]
    reviewer_mode: str
    effective_reviewer_mode: str
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "dev/scripts/devctl/runtime/partial_consumer.py",
        """
def read_modes(payload: dict[str, object]) -> tuple[str, str]:
    return (
        str(payload.get("reviewer_mode", "")),
        str(payload.get("effective_reviewer_mode", "")),
    )
""".strip()
        + "\n",
    )
    _commit(tmp_path, "baseline")

    report = build_report(repo_root=tmp_path, absolute=True)

    assert [
        item.consumer_path
        for item in report.stranded_consumers
        if item.consumer_path.endswith("runtime/partial_consumer.py")
    ] == []
