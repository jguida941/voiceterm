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


def test_semantic_duplicate_detection_catches_parallel_system_catalog_contracts(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    _write(
        tmp_path / "dev/scripts/devctl/governance/system_catalog_models.py",
        '''
from dataclasses import dataclass

@dataclass(frozen=True)
class CatalogCommand:
    """One devctl command in the static catalog."""

    name: str
    handler_module: str
    read_only: bool = False
'''.strip()
        + "\n",
    )
    _write(
        tmp_path / "dev/scripts/devctl/platform/system_catalog_models.py",
        '''
from dataclasses import dataclass

@dataclass(frozen=True)
class CommandEntry:
    """One registered devctl command."""

    name: str
    path: str
    category: str
    description: str = ""
'''.strip()
        + "\n",
    )
    _commit(tmp_path, "baseline")

    report = build_report(repo_root=tmp_path, absolute=True)

    duplicate_pairs = {
        frozenset((item.left_contract_name, item.right_contract_name))
        for item in report.duplicate_contracts
    }
    assert frozenset(("CatalogCommand", "CommandEntry")) in duplicate_pairs


def test_internal_only_consumers_are_flagged_as_soft_orphans(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write(
        tmp_path / "dev/scripts/devctl/governance/quality_feedback/models.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class QualityFeedbackSnapshot:
    score: float
    generated_at_utc: str
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "dev/scripts/devctl/governance/quality_feedback/report_builder.py",
        """
from .models import QualityFeedbackSnapshot

def build_snapshot() -> QualityFeedbackSnapshot:
    return QualityFeedbackSnapshot(score=98.0, generated_at_utc="2026-04-10T00:00:00Z")
""".strip()
        + "\n",
    )
    _commit(tmp_path, "baseline")

    report = build_report(repo_root=tmp_path, absolute=True)

    findings = {
        item.contract_name: item
        for item in report.orphaned_contracts
    }
    assert "QualityFeedbackSnapshot" in findings
    assert findings["QualityFeedbackSnapshot"].importer_paths == (
        "dev/scripts/devctl/governance/quality_feedback/report_builder.py",
    )


def test_operator_console_contracts_are_scanned(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write(
        tmp_path / "app/operator_console/state/review_state.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class ReviewState:
    session_id: str
    status: str
""".strip()
        + "\n",
    )
    _commit(tmp_path, "baseline")

    report = build_report(repo_root=tmp_path, absolute=True)

    layer_counts = {row.layer: row.contract_count for row in report.layer_counts}
    assert layer_counts["operator_console"] == 1
    assert report.contracts_scanned == 1
    assert report.orphaned_contracts[0].layer == "operator_console"


def test_bidirectional_reference_findings_classify_missing_edges(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    _write(
        tmp_path / "dev/scripts/devctl/runtime/isolated_contract.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class IsolatedContract:
    value: str
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "dev/scripts/devctl/runtime/leaf_contract.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class LeafContract:
    value: str
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "dev/scripts/devctl/governance/use_leaf_contract.py",
        """
from ..runtime.leaf_contract import LeafContract

def build() -> LeafContract:
    return LeafContract(value="ok")
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "dev/scripts/devctl/runtime/dependency_contract.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class DependencyContract:
    value: str
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "dev/scripts/devctl/runtime/forward_only_contract.py",
        """
from dataclasses import dataclass

from .dependency_contract import DependencyContract

@dataclass(frozen=True)
class ForwardOnlyContract:
    value: str

def dependency() -> DependencyContract:
    return DependencyContract(value="ok")
""".strip()
        + "\n",
    )
    _commit(tmp_path, "baseline")

    report = build_report(repo_root=tmp_path, absolute=True)

    findings = {
        item.contract_name: item
        for item in report.bidirectional_reference_findings
    }
    assert findings["IsolatedContract"].missing_directions == (
        "forward",
        "backward",
    )
    assert findings["LeafContract"].missing_directions == ("forward",)
    assert findings["LeafContract"].backward_importer_count == 1
    assert findings["LeafContract"].importer_paths == (
        "dev/scripts/devctl/governance/use_leaf_contract.py",
    )
    assert findings["ForwardOnlyContract"].missing_directions == ("backward",)
    assert findings["ForwardOnlyContract"].forward_reference_count == 1
    assert findings["ForwardOnlyContract"].forward_contracts == (
        "DependencyContract",
    )
