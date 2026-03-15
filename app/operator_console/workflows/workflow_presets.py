"""Workflow presets exposed by the Operator Console launchpad module."""

from __future__ import annotations

from dataclasses import dataclass

from dev.scripts.devctl.repo_packs import workflow_preset_definitions


@dataclass(frozen=True)
class WorkflowPreset:
    """A bounded markdown-plan workflow the GUI can launch."""

    preset_id: str
    label: str
    plan_doc: str
    mp_scope: str
    summary: str


DEFAULT_WORKFLOW_PRESET_ID = "operator_console"


WORKFLOW_PRESETS: tuple[WorkflowPreset, ...] = tuple(
    WorkflowPreset(
        preset_id=definition.preset_id,
        label=definition.label,
        plan_doc=definition.plan_doc,
        mp_scope=definition.mp_scope,
        summary=definition.summary,
    )
    for definition in workflow_preset_definitions()
)


def available_workflow_presets() -> tuple[WorkflowPreset, ...]:
    """Return the workflow presets shown in the GUI."""
    return WORKFLOW_PRESETS


def resolve_workflow_preset(preset_id: str) -> WorkflowPreset:
    """Resolve a workflow preset, falling back to the default preset."""
    normalized = preset_id.strip().lower()
    for preset in WORKFLOW_PRESETS:
        if preset.preset_id == normalized:
            return preset
    return WORKFLOW_PRESETS[0]
