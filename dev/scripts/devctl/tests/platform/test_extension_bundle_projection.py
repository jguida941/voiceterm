"""Tests for repo-pack-aware ExtensionBundle projection helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from dev.scripts.devctl.platform.extension_bundle_projection import (
    build_extension_bundle_projection,
    render_extension_bundle_projection_markdown,
    resolve_extension_bundle,
)


REPO_ROOT = Path("/Users/jguida941/testing_upgrade/codex-voice")


def test_resolve_extension_bundle_from_repo_policy() -> None:
    bundle = resolve_extension_bundle(repo_root=REPO_ROOT)

    assert bundle.repo_pack_id == "voiceterm"
    assert bundle.surface_ids() == [
        "codex_hooks",
        "claude_settings",
        "mcp_tools",
        "claude_agents",
    ]


def test_resolve_extension_bundle_fails_closed_for_unknown_repo_pack() -> None:
    with pytest.raises(RuntimeError, match="No registered ExtensionBundle"):
        resolve_extension_bundle(repo_root=REPO_ROOT, repo_pack_id="unknown-pack")


def test_projection_reports_surface_presence_and_missing_targets() -> None:
    report = build_extension_bundle_projection(repo_root=REPO_ROOT)

    assert report["ok"] is True
    assert report["repo_pack_id"] == "voiceterm"
    assert report["policy_pack_id"] == "voiceterm"
    assert report["surface_count"] == 4
    assert report["automation_count"] == 3

    surfaces = {entry["surface_id"]: entry for entry in report["surfaces"]}
    assert surfaces["claude_settings"]["state"] == "present"
    assert surfaces["claude_settings"]["target_path"] == ".claude/settings.local.json"
    assert surfaces["codex_hooks"]["state"] == "missing"
    assert surfaces["codex_hooks"]["target_path"] == ".codex/hooks.json"
    assert surfaces["mcp_tools"]["state"] == "missing"
    assert surfaces["claude_agents"]["target_kind"] == "directory"


def test_projection_materializes_governed_automation_commands() -> None:
    report = build_extension_bundle_projection(repo_root=REPO_ROOT)

    automations = {entry["task_id"]: entry for entry in report["automations"]}
    assert automations["full_ci"]["command"] == (
        "python3 dev/scripts/devctl.py check --profile ci"
    )
    assert automations["full_ci"]["execution_modes"] == [
        "local",
        "github_workflow",
        "codex_automation",
    ]
    assert automations["probe_report"]["command"] == (
        "python3 dev/scripts/devctl.py probe-report --format md"
    )


def test_markdown_renderer_includes_surface_and_automation_summary() -> None:
    report = build_extension_bundle_projection(repo_root=REPO_ROOT)

    rendered = render_extension_bundle_projection_markdown(report)

    assert "# devctl extension-bundle" in rendered
    assert "- repo_pack_id: voiceterm" in rendered
    assert "codex_hooks: state=missing" in rendered
    assert ".claude/settings.local.json" in rendered
    assert "full_ci: modes=local, github_workflow, codex_automation" in rendered
