"""Layout mode registry for the Operator Console layout package.

Defines the available spatial arrangements (tabbed, sidebar, grid,
analytics).  Layout building is handled by PageBuilderMixin in
ui_pages.py; this module owns the descriptor data and resolution
helpers so the rest of the codebase can reference modes without
importing Qt.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LayoutDescriptor:
    """Metadata for one spatial layout mode."""

    mode_id: str
    display_name: str
    description: str


@dataclass(frozen=True)
class WorkbenchPresetDescriptor:
    """Metadata and splitter ratios for one workbench snap preset."""

    preset_id: str
    display_name: str
    description: str
    root_sizes: tuple[int, int]
    lane_sizes: tuple[int, int, int]
    utility_sizes: tuple[int, int, int]


LAYOUT_REGISTRY: tuple[LayoutDescriptor, ...] = (
    LayoutDescriptor("tabbed", "Tabbed", "Dashboard / Monitor / Activity tabs"),
    LayoutDescriptor(
        "sidebar", "Sidebar", "Navigation sidebar with content panel"
    ),
    LayoutDescriptor(
        "grid", "Grid", "All panels visible in a tiled grid"
    ),
    LayoutDescriptor(
        "analytics",
        "Analytics",
        "CI/CD and code metrics dashboard",
    ),
    LayoutDescriptor(
        "workbench",
        "Workbench",
        "Resizable shared-screen workbench with snap presets",
    ),
)

DEFAULT_LAYOUT_ID = "workbench"
DEFAULT_WORKBENCH_PRESET_ID = "balanced"

WORKBENCH_PRESET_REGISTRY: tuple[WorkbenchPresetDescriptor, ...] = (
    WorkbenchPresetDescriptor(
        "balanced",
        "Balanced",
        "Compact lane strip above a broad monitor-first utility row.",
        root_sizes=(22, 78),
        lane_sizes=(4, 5, 4),
        utility_sizes=(8, 2, 2),
    ),
    WorkbenchPresetDescriptor(
        "lanes",
        "Lane Focus",
        "Give the reviewer, operator, and implementer lanes more space without letting the logs collapse.",
        root_sizes=(32, 68),
        lane_sizes=(5, 6, 5),
        utility_sizes=(7, 2, 1),
    ),
    WorkbenchPresetDescriptor(
        "launch",
        "Launch Center",
        "Keep Monitor dominant while the sidecars stay docked and secondary.",
        root_sizes=(18, 82),
        lane_sizes=(4, 5, 4),
        utility_sizes=(9, 2, 1),
    ),
    WorkbenchPresetDescriptor(
        "activity",
        "Activity Focus",
        "Bias the lower row toward the report workspace while keeping Monitor primary.",
        root_sizes=(24, 76),
        lane_sizes=(4, 5, 4),
        utility_sizes=(6, 4, 2),
    ),
)


def available_layout_ids() -> tuple[str, ...]:
    """Return all registered layout mode IDs in display order."""
    return tuple(d.mode_id for d in LAYOUT_REGISTRY)


def available_workbench_preset_ids() -> tuple[str, ...]:
    """Return all registered workbench preset IDs in display order."""
    return tuple(d.preset_id for d in WORKBENCH_PRESET_REGISTRY)


def resolve_layout(mode_id: str) -> LayoutDescriptor:
    """Look up a layout descriptor by mode_id, falling back to the default."""
    for desc in LAYOUT_REGISTRY:
        if desc.mode_id == mode_id:
            return desc
    for desc in LAYOUT_REGISTRY:
        if desc.mode_id == DEFAULT_LAYOUT_ID:
            return desc
    return LAYOUT_REGISTRY[0]


def resolve_workbench_preset(preset_id: str) -> WorkbenchPresetDescriptor:
    """Look up a workbench preset, falling back to the default."""
    for desc in WORKBENCH_PRESET_REGISTRY:
        if desc.preset_id == preset_id:
            return desc
    return WORKBENCH_PRESET_REGISTRY[0]
