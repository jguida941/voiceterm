"""Tests for the ExtensionBundle contract scaffold."""

from __future__ import annotations

from dev.scripts.devctl.platform.extension_bundle import (
    EXTENSION_BUNDLE_CONTRACT_ID,
    EXTENSION_BUNDLE_SCHEMA_VERSION,
    AutomationSpec,
    ExtensionBundle,
    ExtensionSurface,
)
from dev.scripts.devctl.platform.extension_bundle_defaults import (
    VOICETERM_EXTENSION_BUNDLE,
)


def test_voiceterm_bundle_surface_ids() -> None:
    expected = ["codex_hooks", "claude_settings", "mcp_tools", "claude_agents"]
    assert VOICETERM_EXTENSION_BUNDLE.surface_ids() == expected


def test_voiceterm_bundle_automation_ids() -> None:
    expected = ["lint_and_fix", "full_ci", "probe_report"]
    assert VOICETERM_EXTENSION_BUNDLE.automation_ids() == expected


def test_schema_version_and_contract_id() -> None:
    assert VOICETERM_EXTENSION_BUNDLE.schema_version == EXTENSION_BUNDLE_SCHEMA_VERSION
    assert VOICETERM_EXTENSION_BUNDLE.contract_id == EXTENSION_BUNDLE_CONTRACT_ID


def test_frozen_dataclass_rejects_mutation() -> None:
    import pytest

    with pytest.raises(AttributeError):
        VOICETERM_EXTENSION_BUNDLE.repo_pack_id = "other"  # type: ignore[misc]

    surface = VOICETERM_EXTENSION_BUNDLE.surfaces[0]
    with pytest.raises(AttributeError):
        surface.surface_id = "changed"  # type: ignore[misc]

    automation = VOICETERM_EXTENSION_BUNDLE.automations[0]
    with pytest.raises(AttributeError):
        automation.task_id = "changed"  # type: ignore[misc]


def test_to_dict_round_trip() -> None:
    payload = VOICETERM_EXTENSION_BUNDLE.to_dict()
    assert payload["repo_pack_id"] == "voiceterm"
    assert len(payload["surfaces"]) == 4
    assert len(payload["automations"]) == 3
    assert payload["schema_version"] == EXTENSION_BUNDLE_SCHEMA_VERSION
    assert payload["contract_id"] == EXTENSION_BUNDLE_CONTRACT_ID
    # Automations should serialize execution_modes as lists (JSON-friendly)
    for auto in payload["automations"]:
        assert isinstance(auto["execution_modes"], list)


def test_empty_bundle_defaults() -> None:
    bundle = ExtensionBundle(repo_pack_id="empty")
    assert bundle.surface_ids() == []
    assert bundle.automation_ids() == []
    assert bundle.schema_version == EXTENSION_BUNDLE_SCHEMA_VERSION
