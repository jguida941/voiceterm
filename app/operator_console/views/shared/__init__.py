"""Shared Operator Console widgets and text helpers."""

from .swarm_status_widgets import apply_swarm_status_widgets
from .ui_scroll import (
    append_plain_text_preserving_scroll,
    replace_plain_text_preserving_scroll,
)
from .widgets import (
    AgentSummaryCard,
    CollapsibleKVRow,
    FlippableTextCard,
    KeyValuePanel,
    ProviderBadge,
    SectionHeader,
    StatusIndicator,
    build_compact_button_grid,
    compact_display_text,
    configure_compact_button,
)

__all__ = [
    "AgentSummaryCard",
    "CollapsibleKVRow",
    "FlippableTextCard",
    "KeyValuePanel",
    "ProviderBadge",
    "SectionHeader",
    "StatusIndicator",
    "append_plain_text_preserving_scroll",
    "apply_swarm_status_widgets",
    "build_compact_button_grid",
    "compact_display_text",
    "configure_compact_button",
    "replace_plain_text_preserving_scroll",
]
