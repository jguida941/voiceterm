"""Agent detail dialog with diff-highlighted raw text view.

Opens from card header buttons to show a deep-dive into a single
agent lane's structured data and raw section text.
"""

from __future__ import annotations

from ..state.models import AgentLaneData
from ..theme.theme_state import BUILTIN_PRESETS
from .widgets import ProviderBadge, StatusIndicator

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
    from PyQt6.QtWidgets import (
        QDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QPlainTextEdit,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False


class DiffHighlighter(QSyntaxHighlighter if _PYQT_AVAILABLE else object):
    """Syntax highlighter that colors unified-diff lines.

    Applied to any QPlainTextEdit whose content may contain diff
    fragments. Added lines get green, removed get red, hunk headers
    get blue, and file headers get bold.
    """

    def __init__(self, document: object, theme_colors: dict[str, str] | None = None) -> None:
        super().__init__(document)
        colors = theme_colors or {}
        document_text = document.toPlainText() if hasattr(document, "toPlainText") else ""
        self._is_diff_document = looks_like_unified_diff(document_text)

        self._added = QTextCharFormat()
        self._added.setForeground(_theme_qcolor(colors, "status_active"))
        self._added.setBackground(_theme_qcolor(colors, "status_active", alpha=25))

        self._removed = QTextCharFormat()
        self._removed.setForeground(_theme_qcolor(colors, "danger"))
        self._removed.setBackground(_theme_qcolor(colors, "danger", alpha=25))

        self._hunk = QTextCharFormat()
        self._hunk.setForeground(_theme_qcolor(colors, "accent"))

        self._header = QTextCharFormat()
        self._header.setForeground(_theme_qcolor(colors, "text"))
        self._header.setFontWeight(QFont.Weight.Bold)

    @property
    def is_diff_document(self) -> bool:
        return self._is_diff_document

    def highlightBlock(self, text: str) -> None:
        if not text or not self._is_diff_document:
            return
        if text.startswith("+++") or text.startswith("---") or text.startswith("diff "):
            self.setFormat(0, len(text), self._header)
        elif text.startswith("+"):
            self.setFormat(0, len(text), self._added)
        elif text.startswith("-"):
            self.setFormat(0, len(text), self._removed)
        elif text.startswith("@@"):
            self.setFormat(0, len(text), self._hunk)


def looks_like_unified_diff(text: str) -> bool:
    """Return True only when a document actually resembles unified diff text."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    has_diff_header = any(line.startswith("diff ") for line in lines)
    has_hunk_header = any(line.startswith("@@") for line in lines)
    has_file_markers = any(line.startswith("+++") for line in lines) and any(
        line.startswith("---") for line in lines
    )
    return has_diff_header or has_hunk_header or has_file_markers


def _theme_qcolor(
    colors: dict[str, str],
    key: str,
    *,
    alpha: int | None = None,
) -> QColor:
    """Resolve a theme color and optionally apply a translucent alpha channel."""

    default_colors = BUILTIN_PRESETS["Codex"].colors
    fallback_color = default_colors["text"]
    color = QColor(colors.get(key, default_colors.get(key, fallback_color)))
    if not color.isValid():
        color = QColor(default_colors.get(key, fallback_color))
    if alpha is not None:
        color.setAlpha(alpha)
    return color


if _PYQT_AVAILABLE:

    class AgentDetailDialog(QDialog):
        """Full-page agent detail with structured data and diff-highlighted raw text."""

        def __init__(
            self,
            lane: AgentLaneData,
            *,
            theme_colors: dict[str, str] | None = None,
            parent: QWidget | None = None,
        ) -> None:
            super().__init__(parent)
            self.setObjectName("AgentDetailDialog")
            self.setWindowTitle(f"{lane.provider_name} \u2014 {lane.role_label}")
            self.resize(700, 540)

            root = QVBoxLayout(self)
            root.setContentsMargins(20, 16, 20, 16)
            root.setSpacing(12)

            # ── Header: dot + name + role + status badge ──────────
            header = QHBoxLayout()
            header.setSpacing(10)

            dot = StatusIndicator()
            dot.set_level(lane.status_hint)
            header.addWidget(dot)

            badge = ProviderBadge(lane.provider_name)
            header.addWidget(badge)

            name = QLabel(lane.provider_name)
            name.setObjectName("DetailAgentName")
            header.addWidget(name)

            role = QLabel(f"\u2014 {lane.role_label}")
            role.setObjectName("DetailRoleLabel")
            header.addWidget(role)

            header.addStretch(1)

            status_badge = QLabel(lane.status_hint.upper())
            status_badge.setObjectName("DetailStatusBadge")
            header.addWidget(status_badge)

            root.addLayout(header)

            if lane.lane_title:
                title_label = QLabel(lane.lane_title)
                title_label.setObjectName("DetailLaneTitle")
                title_label.setWordWrap(True)
                root.addWidget(title_label)

            # ── Tabs: Structured Data | Raw Text ──────────────────
            tabs = QTabWidget()
            tabs.setDocumentMode(True)

            # Data tab — always-expanded KV rows
            data_widget = QWidget()
            data_layout = QVBoxLayout(data_widget)
            data_layout.setContentsMargins(8, 8, 8, 8)
            data_layout.setSpacing(4)

            if lane.rows:
                for key, value in lane.rows:
                    data_layout.addWidget(self._make_detail_row(key, value))
            else:
                empty = QLabel("No structured data available.")
                empty.setObjectName("KVValue")
                data_layout.addWidget(empty)
            data_layout.addStretch(1)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setWidget(data_widget)
            tabs.addTab(scroll, "Structured Data")

            # Raw text tab — diff highlighting applied automatically
            raw_view = QPlainTextEdit()
            raw_view.setObjectName("DiffView")
            raw_view.setReadOnly(True)
            raw_view.setPlainText(lane.raw_text or "(no raw text)")
            self._highlighter = DiffHighlighter(raw_view.document(), theme_colors)
            if self._highlighter.is_diff_document:
                raw_view.setToolTip("Unified diff highlighting is active for this raw text pane.")
            else:
                raw_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
                raw_view.setHorizontalScrollBarPolicy(
                    Qt.ScrollBarPolicy.ScrollBarAlwaysOff
                )
                raw_view.setToolTip(
                    "Wrapped raw text view. Diff colors only appear when the content "
                    "is real unified diff text."
                )
            tabs.addTab(raw_view, "Raw Text")
            tabs.tabBar().setTabToolTip(0, "Structured key/value view for the selected lane.")
            tabs.tabBar().setTabToolTip(
                1,
                "Raw lane text. Diff colors appear only for real unified diffs.",
            )

            root.addWidget(tabs, stretch=1)

            # Close button
            close_btn = QPushButton("Close")
            close_btn.setObjectName("SmallActionButton")
            close_btn.clicked.connect(self.accept)
            root.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        def _make_detail_row(self, key: str, value: str) -> QFrame:
            """Always-expanded KV row with selectable text."""
            row = QFrame()
            row.setObjectName("KVRow")
            layout = QHBoxLayout(row)
            layout.setContentsMargins(4, 6, 4, 6)
            layout.setSpacing(14)

            key_label = QLabel(key)
            key_label.setObjectName("KVLabel")
            key_label.setMinimumWidth(80)
            key_label.setMaximumWidth(140)
            key_label.setSizePolicy(
                QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred
            )
            key_label.setAlignment(
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
            )

            val_label = QLabel(value)
            val_label.setObjectName("KVValue")
            val_label.setWordWrap(True)
            val_label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            val_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

            layout.addWidget(key_label)
            layout.addWidget(val_label, stretch=1)
            return row

else:

    class AgentDetailDialog:  # type: ignore[no-redef]
        """Stub when PyQt6 is not installed."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def exec(self) -> None:
            pass
