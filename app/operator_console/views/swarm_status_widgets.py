"""Shared Start Swarm status widget updates."""

from __future__ import annotations

from .widgets import compact_display_text

try:
    from PyQt6.QtWidgets import QLabel
except ImportError:  # pragma: no cover - optional dependency path
    QLabel = object


def apply_swarm_status_widgets(
    *,
    dot: QLabel,
    status_label: QLabel,
    detail_label: QLabel,
    command_label: QLabel,
    level: str,
    label: str,
    detail: str,
    command_preview: str | None = None,
    detail_tooltip_target: object | None = None,
) -> None:
    """Apply a shared Start Swarm status payload to a workspace card."""
    dot.setProperty("statusLevel", level)
    style = dot.style()
    if style is not None:
        style.unpolish(dot)
        style.polish(dot)
    dot.update()
    status_label.setText(label)
    status_label.setToolTip(detail)
    detail_label.setText(compact_display_text(detail, limit=150))
    detail_label.setToolTip(detail)
    if detail_tooltip_target is not None:
        detail_tooltip_target.setToolTip(detail)
    if command_preview:
        command_label.setText(compact_display_text(command_preview, limit=120))
        command_label.setToolTip(command_preview)
