"""Tests for `devctl.governance.draft` scan and render helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from dev.scripts.devctl.governance.draft import (
    render_governance_draft_markdown,
    scan_repo_governance,
)
from dev.scripts.devctl.runtime.project_governance import (
    project_governance_from_mapping,
)


def _mock_subprocess_run(*_args, **_kwargs):
    """Return a fake CompletedProcess with returncode=1 so git calls yield empty strings."""

    class _FakeResult:
        returncode = 1
        stdout = ""

    return _FakeResult()


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_scan_repo_governance_with_empty_policy(tmp_path: Path) -> None:
    gov = scan_repo_governance(tmp_path, policy={})

    # repo_name defaults to the directory name when policy is empty
    assert gov.repo_identity.repo_name == tmp_path.name

    # contract_id is always the canonical constant
    assert gov.contract_id == "ProjectGovernance"

    # path_roots fields are empty because no standard dirs exist
    assert gov.path_roots.active_docs == ""
    assert gov.path_roots.reports == ""
    assert gov.path_roots.scripts == ""
    assert gov.path_roots.checks == ""
    assert gov.path_roots.workflows == ""
    assert gov.path_roots.guides == ""
    assert gov.path_roots.config == ""

    # bridge is inactive when bridge.md does not exist
    assert gov.bridge_config.bridge_active is False

    # startup_order is empty when bootstrap files are absent
    assert gov.startup_order == ()


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_scan_repo_governance_with_standard_layout(tmp_path: Path) -> None:
    # Create a standard directory layout
    (tmp_path / "dev" / "active").mkdir(parents=True)
    (tmp_path / "dev" / "reports").mkdir(parents=True)
    (tmp_path / "dev" / "scripts" / "checks").mkdir(parents=True)
    (tmp_path / "dev" / "guides").mkdir(parents=True)
    (tmp_path / "dev" / "config").mkdir(parents=True)
    (tmp_path / ".github" / "workflows").mkdir(parents=True)

    # Create bootstrap authority files
    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (tmp_path / "dev" / "active" / "INDEX.md").write_text(
        "# Index\n", encoding="utf-8"
    )
    (tmp_path / "dev" / "active" / "MASTER_PLAN.md").write_text(
        "# Master Plan\n", encoding="utf-8"
    )

    # Create bridge file with active_dual_agent mode
    (tmp_path / "bridge.md").write_text(
        "# Code Audit\n- Reviewer mode: `active_dual_agent`\n",
        encoding="utf-8",
    )

    gov = scan_repo_governance(tmp_path, policy={})

    # path_roots populated for existing dirs
    assert gov.path_roots.active_docs == "dev/active"
    assert gov.path_roots.reports == "dev/reports"
    assert gov.path_roots.scripts == "dev/scripts"
    assert gov.path_roots.checks == "dev/scripts/checks"
    assert gov.path_roots.workflows == ".github/workflows"
    assert gov.path_roots.guides == "dev/guides"
    assert gov.path_roots.config == "dev/config"

    # plan_registry populated for existing files
    assert gov.plan_registry.registry_path == "dev/active/INDEX.md"
    assert gov.plan_registry.tracker_path == "dev/active/MASTER_PLAN.md"
    assert gov.plan_registry.index_path == "dev/active/INDEX.md"

    # bridge is active and mode parsed from bridge.md
    assert gov.bridge_config.bridge_active is True
    assert gov.bridge_config.bridge_mode == "active_dual_agent"

    # startup_order lists all three bootstrap files in canonical order
    assert "AGENTS.md" in gov.startup_order
    assert "dev/active/INDEX.md" in gov.startup_order
    assert "dev/active/MASTER_PLAN.md" in gov.startup_order

    # docs_authority is AGENTS.md when file exists
    assert gov.docs_authority == "AGENTS.md"


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_scan_repo_governance_policy_fields(tmp_path: Path) -> None:
    policy = {
        "repo_name": "TestRepo",
        "surface_generation": {
            "repo_pack_metadata": {
                "pack_id": "test-pack",
                "pack_version": "1.0",
            },
        },
        "ai_guard_overrides": {
            "custom_guard": {"extra_args": ["--strict"]},
        },
    }

    gov = scan_repo_governance(tmp_path, policy=policy)

    assert gov.repo_identity.repo_name == "TestRepo"
    assert gov.repo_pack.pack_id == "test-pack"
    assert gov.repo_pack.pack_version == "1.0"
    assert gov.bundle_overrides.overrides == {}


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_governance_draft_command_quality_policy_passthrough(tmp_path: Path) -> None:
    """M1 regression: --quality-policy must change emitted payload through the real command path."""
    import argparse
    import json

    policy_file = tmp_path / "override_policy.json"
    policy_file.write_text(
        json.dumps({
            "schema_version": 1,
            "repo_name": "CommandOverride",
            "surface_generation": {
                "repo_pack_metadata": {
                    "pack_id": "cmd-override-pack",
                    "pack_version": "3.3.3",
                },
            },
        }),
        encoding="utf-8",
    )

    from dev.scripts.devctl.commands.governance.draft import run

    captured: list[dict] = []
    original_emit = __import__(
        "dev.scripts.devctl.commands.governance.common",
        fromlist=["emit_governance_command_output"],
    ).emit_governance_command_output

    def _capture_emit(args, *, command, json_payload, markdown_output, **kw):
        captured.append(dict(json_payload))
        return 0

    args = argparse.Namespace(
        repo_root=str(tmp_path),
        quality_policy=str(policy_file),
        format="json",
        output=None,
        pipe_command=None,
        pipe_args=None,
    )

    with patch(
        "dev.scripts.devctl.commands.governance.draft.emit_governance_command_output",
        _capture_emit,
    ):
        exit_code = run(args)

    assert exit_code == 0
    assert len(captured) == 1
    payload = captured[0]
    assert payload["repo_identity"]["repo_name"] == "CommandOverride"
    assert payload["repo_pack"]["pack_id"] == "cmd-override-pack"
    assert payload["repo_pack"]["pack_version"] == "3.3.3"


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_enabled_checks_parity_with_resolved_policy(tmp_path: Path) -> None:
    """M2 regression: enabled_checks must match resolved quality-policy IDs, not just types."""
    from dev.scripts.devctl.governance.draft import _scan_enabled_checks

    # Use the real repo root so resolve_quality_policy finds devctl_repo_policy.json
    from dev.scripts.devctl.config import REPO_ROOT

    checks = _scan_enabled_checks(Path(REPO_ROOT), policy_path=None)

    # Resolved policy for this repo includes VoiceTerm-only guards
    assert "ide_provider_isolation" in checks.guard_ids
    assert "tandem_consistency" in checks.guard_ids
    assert "naming_consistency" in checks.guard_ids
    assert len(checks.guard_ids) >= 30
    assert len(checks.probe_ids) >= 20


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_render_governance_draft_markdown(tmp_path: Path) -> None:
    gov = scan_repo_governance(tmp_path, policy={"repo_name": "RenderTest"})

    md = render_governance_draft_markdown(gov)

    assert "# governance-draft" in md
    assert "RenderTest" in md
    assert "## Repo Identity" in md
    assert "## Repo Pack" in md
    assert "## Path Roots" in md
    assert "## Plan Registry" in md
    assert "## Bridge Config" in md
    assert "## Enabled Checks" in md
    assert "## Startup Order" in md


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_scan_repo_governance_roundtrips_through_mapping(tmp_path: Path) -> None:
    # Create minimal layout so some fields are populated
    (tmp_path / "dev" / "active").mkdir(parents=True)
    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")

    original = scan_repo_governance(tmp_path, policy={"repo_name": "Roundtrip"})

    serialized = original.to_dict()
    restored = project_governance_from_mapping(serialized)

    assert restored.contract_id == original.contract_id
    assert restored.schema_version == original.schema_version
    assert restored.repo_identity.repo_name == original.repo_identity.repo_name
    assert restored.repo_pack.pack_id == original.repo_pack.pack_id
    assert restored.path_roots.active_docs == original.path_roots.active_docs
    assert restored.bridge_config.bridge_active == original.bridge_config.bridge_active
    assert restored.bridge_config.bridge_mode == original.bridge_config.bridge_mode
    assert restored.startup_order == original.startup_order
    assert restored.docs_authority == original.docs_authority
    assert restored.bundle_overrides.overrides == original.bundle_overrides.overrides
