"""Chat-style conversation panel backed by review-channel packets.

Shows the team conversation timeline where agents (Codex, Claude,
Cursor, Operator) exchange messages. Every message is a real
``devctl review-channel`` packet — the chat view is a skin over
the same guarded state machine.
"""

from __future__ import annotations

from ...collaboration.conversation_state import (
    AGENT_DISPLAY_NAMES,
    AGENT_ROLES,
    ConversationMessage,
    ConversationSnapshot,
)
from ..shared.widgets import compact_display_text, configure_compact_button

try:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtWidgets import (
        QComboBox,
        QFrame,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPlainTextEdit,
        QPushButton,
        QSizePolicy,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QWidget = object


_AGENT_BADGE_COLORS: dict[str, str] = {
    "codex": "#4A90D9",
    "claude": "#D97706",
    "cursor": "#10B981",
    "operator": "#8B5CF6",
    "system": "#6B7280",
}


if _PYQT_AVAILABLE:

    class ConversationPanel(QWidget):
        """Chat-style timeline of review-channel packets.

        API contract:
        - ``set_conversation(snapshot)`` — push new data each poll cycle
        - ``post_requested`` signal — emitted when Send is clicked,
          carrying ``(to_agent, summary, body)`` for the parent to
          route through ``build_review_channel_post_command()``.
        """

        post_requested = pyqtSignal(str, str, str)

        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self._messages_by_id: dict[str, ConversationMessage] = {}

            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(6)

            # Header
            header = QHBoxLayout()
            header.setSpacing(8)
            title = QLabel("Team Conversation")
            title.setObjectName("SectionHeaderLabel")
            header.addWidget(title)
            self._count_badge = QLabel("0")
            self._count_badge.setObjectName("ApprovalCountBadge")
            self._count_badge.setFixedSize(24, 24)
            self._count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.addWidget(self._count_badge)
            header.addStretch(1)
            root.addLayout(header)

            # Message timeline
            splitter = QSplitter(Qt.Orientation.Vertical)
            splitter.setHandleWidth(3)
            splitter.setChildrenCollapsible(False)

            self._timeline = QListWidget()
            self._timeline.setObjectName("ConversationList")
            self._timeline.currentItemChanged.connect(self._on_selection)
            splitter.addWidget(self._timeline)

            # Detail pane for selected message
            self._detail_pane = QFrame()
            self._detail_pane.setObjectName("ApprovalDetailPane")
            detail_layout = QVBoxLayout(self._detail_pane)
            detail_layout.setContentsMargins(12, 10, 12, 10)
            detail_layout.setSpacing(6)

            self._detail_header = QLabel("Select a message to view details")
            self._detail_header.setObjectName("ApprovalDetailHeader")
            self._detail_header.setWordWrap(True)
            detail_layout.addWidget(self._detail_header)

            self._detail_flow = QLabel("")
            self._detail_flow.setObjectName("ApprovalFlowLabel")
            detail_layout.addWidget(self._detail_flow)

            self._detail_body = QLabel("")
            self._detail_body.setObjectName("ApprovalBodyText")
            self._detail_body.setWordWrap(True)
            self._detail_body.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            detail_layout.addWidget(self._detail_body, stretch=1)

            self._detail_status = QLabel("")
            self._detail_status.setObjectName("ApprovalActionLabel")
            detail_layout.addWidget(self._detail_status)

            splitter.addWidget(self._detail_pane)
            splitter.setStretchFactor(0, 3)
            splitter.setStretchFactor(1, 2)
            root.addWidget(splitter, stretch=1)

            # Compose area
            compose = QFrame()
            compose.setObjectName("LaneCard")
            compose_layout = QVBoxLayout(compose)
            compose_layout.setContentsMargins(8, 8, 8, 8)
            compose_layout.setSpacing(6)

            # Agent picker row
            agent_row = QHBoxLayout()
            agent_row.setSpacing(6)
            agent_row.addWidget(QLabel("To:"))
            self._agent_picker = QComboBox()
            self._agent_picker.setObjectName("WorkflowSelector")
            for agent_id, display in AGENT_DISPLAY_NAMES.items():
                if agent_id not in ("operator", "system"):
                    role = AGENT_ROLES.get(agent_id, "")
                    self._agent_picker.addItem(
                        f"{display} ({role})", agent_id
                    )
            agent_row.addWidget(self._agent_picker)
            agent_row.addStretch(1)
            compose_layout.addLayout(agent_row)

            # Instruction input
            self._instruction_input = QPlainTextEdit()
            self._instruction_input.setObjectName("PanelRawText")
            self._instruction_input.setPlaceholderText(
                "Type an instruction for the selected agent..."
            )
            self._instruction_input.setMaximumHeight(80)
            compose_layout.addWidget(self._instruction_input)

            # Send button row
            btn_row = QHBoxLayout()
            btn_row.addStretch(1)
            self._send_btn = QPushButton("Send Task")
            self._send_btn.setObjectName("SmallActionButton")
            self._send_btn.setProperty("accentRole", "primary")
            configure_compact_button(self._send_btn)
            self._send_btn.clicked.connect(self._on_send)
            btn_row.addWidget(self._send_btn)
            compose_layout.addLayout(btn_row)

            root.addWidget(compose)

        # ── Public API ────────────────────────────────────────

        def set_conversation(
            self, snapshot: ConversationSnapshot
        ) -> None:
            """Replace timeline contents, preserving selection."""
            prev_id = self._selected_packet_id()
            self._messages_by_id = {
                m.packet_id: m for m in snapshot.messages
            }

            self._timeline.blockSignals(True)
            self._timeline.clear()
            restore_row: int | None = None

            for idx, msg in enumerate(snapshot.messages):
                from_name = AGENT_DISPLAY_NAMES.get(
                    msg.from_agent, msg.from_agent
                )
                to_name = AGENT_DISPLAY_NAMES.get(
                    msg.to_agent, msg.to_agent
                )
                label = (
                    f"{from_name} \u2192 {to_name}  |  "
                    f"{compact_display_text(msg.summary, limit=80)}"
                )
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, msg.packet_id)
                item.setToolTip(
                    f"[{msg.kind}] {msg.summary}\n"
                    f"Status: {msg.status} | {msg.timestamp}"
                )
                self._timeline.addItem(item)
                if msg.packet_id == prev_id:
                    restore_row = idx

            self._timeline.blockSignals(False)

            if restore_row is not None:
                self._timeline.setCurrentRow(restore_row)
            elif self._timeline.count() > 0:
                self._timeline.setCurrentRow(self._timeline.count() - 1)
            else:
                self._update_detail(None)

            self._count_badge.setText(str(len(snapshot.messages)))

        # ── Internal ──────────────────────────────────────────

        def _selected_packet_id(self) -> str | None:
            current = self._timeline.currentItem()
            if current is None:
                return None
            return current.data(Qt.ItemDataRole.UserRole)

        def _on_selection(
            self,
            current: QListWidgetItem | None,
            _previous: QListWidgetItem | None,
        ) -> None:
            packet_id = (
                current.data(Qt.ItemDataRole.UserRole)
                if current
                else None
            )
            msg = self._messages_by_id.get(packet_id) if packet_id else None
            self._update_detail(msg)

        def _update_detail(self, msg: ConversationMessage | None) -> None:
            if msg is None:
                self._detail_header.setText(
                    "Select a message to view details"
                )
                self._detail_flow.setText("")
                self._detail_body.setText("")
                self._detail_status.setText("")
                return

            from_name = AGENT_DISPLAY_NAMES.get(
                msg.from_agent, msg.from_agent
            )
            to_name = AGENT_DISPLAY_NAMES.get(msg.to_agent, msg.to_agent)
            self._detail_header.setText(f"[{msg.packet_id}] {msg.summary}")
            self._detail_flow.setText(
                f"{from_name} \u2192 {to_name}  |  {msg.kind}"
            )
            self._detail_body.setText(msg.body_preview)
            self._detail_status.setText(
                f"Status: {msg.status}  |  {msg.timestamp}"
            )

        def _on_send(self) -> None:
            text = self._instruction_input.toPlainText().strip()
            if not text:
                return
            to_agent = self._agent_picker.currentData()
            if not to_agent:
                return
            # Use first line as summary, full text as body
            lines = text.split("\n", 1)
            summary = lines[0][:120]
            body = text
            self.post_requested.emit(to_agent, summary, body)
            self._instruction_input.clear()

else:

    class ConversationPanel:  # type: ignore[no-redef]
        """Stub when PyQt6 is not installed."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def set_conversation(self, snapshot: object) -> None:
            pass
