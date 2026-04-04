"""Extension bundle contract for generating agent-facing surfaces.

Defines the typed contract for a repo-pack's extension bundle: the set of
agent-facing surfaces (hooks, settings, MCP tools, etc.) and governed
automations that can be emitted from a single source of truth.

This module contains only the contract definitions.  Default bundles for
specific repos live in ``extension_bundle_defaults``.  Future generator
code will consume these contracts to produce the actual surface files.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

EXTENSION_BUNDLE_SCHEMA_VERSION = 1
EXTENSION_BUNDLE_CONTRACT_ID = "ExtensionBundle"

VALID_SURFACE_FORMATS = ("json", "yaml")
VALID_EXECUTION_MODES = (
    "local",
    "github_workflow",
    "codex_automation",
    "claude_agent",
)


@dataclass(frozen=True, slots=True)
class ExtensionSurface:
    """One generated agent-facing surface file or directory."""

    surface_id: str
    target_path: str
    source_contract: str
    format: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AutomationSpec:
    """One governed task that can run under multiple execution modes."""

    task_id: str
    devctl_command: str
    execution_modes: tuple[str, ...] = ("local",)
    schedule: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["execution_modes"] = list(self.execution_modes)
        return payload


@dataclass(frozen=True, slots=True)
class ExtensionBundle:
    """Complete extension bundle for one repo-pack.

    Holds every surface and automation that the repo-pack wants to emit.
    Generators (not yet implemented) will consume this contract to write
    the actual files.
    """

    repo_pack_id: str
    surfaces: tuple[ExtensionSurface, ...] = ()
    automations: tuple[AutomationSpec, ...] = ()
    schema_version: int = EXTENSION_BUNDLE_SCHEMA_VERSION
    contract_id: str = EXTENSION_BUNDLE_CONTRACT_ID

    def surface_ids(self) -> list[str]:
        """Return ordered list of surface identifiers."""
        return [s.surface_id for s in self.surfaces]

    def automation_ids(self) -> list[str]:
        """Return ordered list of automation task identifiers."""
        return [a.task_id for a in self.automations]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["surfaces"] = [s.to_dict() for s in self.surfaces]
        payload["automations"] = [a.to_dict() for a in self.automations]
        return payload
