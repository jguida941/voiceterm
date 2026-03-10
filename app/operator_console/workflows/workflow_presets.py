"""Workflow presets exposed by the Operator Console launchpad module."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowPreset:
    """A bounded markdown-plan workflow the GUI can launch."""

    preset_id: str
    label: str
    plan_doc: str
    mp_scope: str
    summary: str


DEFAULT_WORKFLOW_PRESET_ID = "operator_console"


WORKFLOW_PRESETS: tuple[WorkflowPreset, ...] = (
    WorkflowPreset(
        preset_id="operator_console",
        label="Operator Console",
        plan_doc="dev/active/operator_console.md",
        mp_scope="MP-359",
        summary=(
            "Desktop shell work: simplify the operator flow, keep backend commands "
            "honest, and surface loop/audit state without hidden steps."
        ),
    ),
    WorkflowPreset(
        preset_id="continuous_swarm",
        label="Continuous Swarm",
        plan_doc="dev/active/continuous_swarm.md",
        mp_scope="MP-358",
        summary=(
            "Reviewer/coder continuity work: keep Codex review and Claude coding "
            "moving through the scoped plan with minimal operator babysitting."
        ),
    ),
    WorkflowPreset(
        preset_id="review_channel",
        label="Review Channel",
        plan_doc="dev/active/review_channel.md",
        mp_scope="MP-355",
        summary=(
            "Shared review bridge work: packets, projections, and the live "
            "Codex/Claude/operator coordination lane."
        ),
    ),
    WorkflowPreset(
        preset_id="autonomous_control_plane",
        label="Autonomy Control",
        plan_doc="dev/active/autonomous_control_plane.md",
        mp_scope="MP-338",
        summary=(
            "Controller/autonomy work: guarded swarm runs, controller state, and "
            "loop evidence attached to the active plan."
        ),
    ),
    WorkflowPreset(
        preset_id="cursor_editor",
        label="Cursor Editor",
        plan_doc="dev/active/operator_console.md",
        mp_scope="MP-359",
        summary=(
            "IDE-integrated editing via Cursor: targeted file changes backed by "
            "the same review-channel guard pipeline as Codex and Claude."
        ),
    ),
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
