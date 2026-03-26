"""Focused tests for governed review-state path resolution."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.runtime.project_governance import (
    PROJECT_GOVERNANCE_CONTRACT_ID,
    PROJECT_GOVERNANCE_SCHEMA_VERSION,
    ArtifactRoots,
    BridgeConfig,
    BundleOverrides,
    EnabledChecks,
    MemoryRoots,
    PathRoots,
    PlanRegistry,
    ProjectGovernance,
    RepoIdentity,
    RepoPackRef,
)
from dev.scripts.devctl.runtime.review_state_locator import (
    resolve_review_state_path,
    review_state_relative_candidates,
)


def _governance(*, review_root: str = "") -> ProjectGovernance:
    return ProjectGovernance(
        schema_version=PROJECT_GOVERNANCE_SCHEMA_VERSION,
        contract_id=PROJECT_GOVERNANCE_CONTRACT_ID,
        repo_identity=RepoIdentity(repo_name="portable-repo"),
        repo_pack=RepoPackRef(pack_id="portable-pack"),
        path_roots=PathRoots(),
        plan_registry=PlanRegistry(),
        artifact_roots=ArtifactRoots(review_root=review_root),
        memory_roots=MemoryRoots(),
        bridge_config=BridgeConfig(),
        enabled_checks=EnabledChecks(),
        bundle_overrides=BundleOverrides(overrides={}),
    )


def _write_review_state(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"bridge": {"reviewer_mode": "active_dual_agent"}}),
        encoding="utf-8",
    )


def test_resolve_review_state_path_uses_governed_review_root(tmp_path: Path) -> None:
    path = tmp_path / "portable" / "review_state.json"
    _write_review_state(path)

    resolved = resolve_review_state_path(
        tmp_path,
        governance=_governance(review_root="portable"),
    )

    assert resolved == path


def test_resolve_review_state_path_fails_closed_without_governed_root_or_override(
    tmp_path: Path,
) -> None:
    _write_review_state(
        tmp_path / "dev" / "reports" / "review_channel" / "latest" / "review_state.json"
    )

    resolved = resolve_review_state_path(
        tmp_path,
        governance=_governance(),
    )

    assert resolved is None
    assert review_state_relative_candidates(governance=_governance()) == ()


@patch(
    "dev.scripts.devctl.runtime.review_state_locator.active_path_config_is_overridden",
    return_value=True,
)
@patch("dev.scripts.devctl.runtime.review_state_locator.active_path_config")
def test_resolve_review_state_path_uses_explicit_repo_pack_override(
    active_path_config_mock,
    _active_path_config_is_overridden_mock,
    tmp_path: Path,
) -> None:
    active_path_config_mock.return_value = SimpleNamespace(
        review_state_candidates=("custom/review_state.json",),
    )
    path = tmp_path / "custom" / "review_state.json"
    _write_review_state(path)

    resolved = resolve_review_state_path(
        tmp_path,
        governance=_governance(),
    )

    assert resolved == path
