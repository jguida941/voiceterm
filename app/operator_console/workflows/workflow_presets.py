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


@dataclass(frozen=True)
class ReviewLaunchTarget:
    """Frozen workflow target used by review launch and chained preflight flows."""

    preset_id: str
    plan_doc: str
    mp_scope: str

    def command_context(
        self,
        *,
        flow: str,
        action: str | None = None,
        live: bool | None = None,
        step: str | None = None,
    ) -> dict[str, object]:
        """Build one process context payload without repeating large dict literals."""
        context: dict[str, object] = {
            "flow": flow,
            "preset_id": self.preset_id,
            "plan_doc": self.plan_doc,
            "mp_scope": self.mp_scope,
        }
        if action is not None:
            context["action"] = action
        if live is not None:
            context["live"] = live
        if step is not None:
            context["step"] = step
        return context


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


def resolve_review_launch_target(
    *,
    fallback_preset_id: str,
    preset_id: str | None = None,
    plan_doc: str | None = None,
    mp_scope: str | None = None,
) -> ReviewLaunchTarget:
    """Resolve the frozen launch target from preset selection or process context."""
    preset = resolve_workflow_preset(preset_id or fallback_preset_id)
    resolved_plan_doc = plan_doc.strip() if isinstance(plan_doc, str) else ""
    resolved_mp_scope = mp_scope.strip() if isinstance(mp_scope, str) else ""
    return ReviewLaunchTarget(
        preset_id=preset.preset_id,
        plan_doc=resolved_plan_doc or preset.plan_doc,
        mp_scope=resolved_mp_scope or preset.mp_scope,
    )
