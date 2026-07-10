"""Layout and window-shell views for the Operator Console."""

from __future__ import annotations

from .ui_layout_state import LayoutStateMixin
from .ui_layouts import (
    DEFAULT_LAYOUT_ID,
    DEFAULT_WORKBENCH_PRESET_ID,
    LAYOUT_REGISTRY,
    WORKBENCH_PRESET_REGISTRY,
    LayoutDescriptor,
    WorkbenchPresetDescriptor,
    available_layout_ids,
    available_workbench_preset_ids,
    resolve_layout,
    resolve_workbench_preset,
)

__all__ = [
    "DEFAULT_LAYOUT_ID",
    "DEFAULT_WORKBENCH_PRESET_ID",
    "HAS_THEME_EDITOR",
    "LAYOUT_REGISTRY",
    "LayoutDescriptor",
    "LayoutStateMixin",
    "WORKBENCH_PRESET_REGISTRY",
    "WindowShellMixin",
    "WorkbenchPresetDescriptor",
    "apply_workbench_preset",
    "available_layout_ids",
    "available_workbench_preset_ids",
    "build_workbench_content",
    "resolve_layout",
    "resolve_workbench_preset",
]


def __getattr__(name: str):
    if name in {"HAS_THEME_EDITOR", "WindowShellMixin"}:
        from .ui_window_shell import HAS_THEME_EDITOR, WindowShellMixin

        return {
            "HAS_THEME_EDITOR": HAS_THEME_EDITOR,
            "WindowShellMixin": WindowShellMixin,
        }[name]
    if name in {"apply_workbench_preset", "build_workbench_content"}:
        from .workbench_layout import apply_workbench_preset, build_workbench_content

        return {
            "apply_workbench_preset": apply_workbench_preset,
            "build_workbench_content": build_workbench_content,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
