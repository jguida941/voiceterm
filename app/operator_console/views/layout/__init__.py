"""Layout and window-shell views for the Operator Console."""

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
from .ui_window_shell import HAS_THEME_EDITOR, WindowShellMixin
from .workbench_layout import apply_workbench_preset, build_workbench_content
