"""Interactive tutorial overlay for first-time users.

Highlights widgets one at a time with a semi-transparent backdrop
and shows step-by-step guidance. Every step explains the guarded
workflow — users learn that the GUI wraps the same safe devctl
pipeline that AI agents use.
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    from PyQt6.QtCore import QPoint, QRect, QSize, Qt
    from PyQt6.QtGui import QColor, QPainter, QPainterPath, QRegion
    from PyQt6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QWidget = object


@dataclass(frozen=True)
class TutorialStep:
    """One step in the interactive tutorial walkthrough."""

    widget_attr: str
    title: str
    description: str


TUTORIAL_STEPS: tuple[TutorialStep, ...] = (
    TutorialStep(
        widget_attr="",
        title="Welcome to the Operator Console",
        description=(
            "This is your team control center. Codex (reviewer), "
            "Claude (implementer), and Cursor (editor) work together "
            "on your codebase — all backed by guarded devctl commands. "
            "Let's walk through the key surfaces."
        ),
    ),
    TutorialStep(
        widget_attr="workflow_launchpad",
        title="Workflow Launcher",
        description=(
            "Pick a markdown plan, then use Audit, Run Loop, or "
            "Launch Review. Every action runs through the same guards "
            "that protect against bad AI practices. The GUI never "
            "bypasses safety checks."
        ),
    ),
    TutorialStep(
        widget_attr="conversation_panel",
        title="Team Conversation",
        description=(
            "This is where your agents talk. Each message is a real "
            "review-channel packet. You can send instructions to any "
            "agent — type a task, pick the agent, and hit Send. "
            "Guards run before every message is delivered."
        ),
    ),
    TutorialStep(
        widget_attr="task_board_panel",
        title="Task Board",
        description=(
            "Tasks flow through columns: Pending → In Progress → "
            "Review → Done. Each ticket is backed by review-channel "
            "packets. Click a ticket to see its full conversation."
        ),
    ),
    TutorialStep(
        widget_attr="approval_panel",
        title="Approval Queue",
        description=(
            "When agents need your sign-off, approval requests "
            "appear here. You can Approve or Deny with an operator "
            "note. Every decision writes a repo-visible artifact."
        ),
    ),
    TutorialStep(
        widget_attr="",
        title="You're Ready",
        description=(
            "Start by picking a workflow, running an Audit, then "
            "sending your first task to an agent. Everything routes "
            "through the same guarded pipeline — the GUI is a team "
            "interface over your existing devctl tools."
        ),
    ),
)


if _PYQT_AVAILABLE:

    class TutorialOverlay(QWidget):
        """Transparent overlay that highlights widgets step by step."""

        def __init__(self, parent: QWidget) -> None:
            super().__init__(parent)
            self._step_index = 0
            self._target_widget: QWidget | None = None
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self.setStyleSheet("background: transparent;")

            # Tooltip card
            self._card = QFrame(self)
            self._card.setObjectName("TutorialCard")
            self._card.setStyleSheet(
                "QFrame#TutorialCard {"
                "  background: rgba(30, 30, 40, 230);"
                "  border: 2px solid #4A90D9;"
                "  border-radius: 12px;"
                "  padding: 16px;"
                "}"
            )
            card_layout = QVBoxLayout(self._card)
            card_layout.setSpacing(8)

            self._step_counter = QLabel("")
            self._step_counter.setStyleSheet(
                "color: #8B9DC3; font-size: 11px;"
            )
            card_layout.addWidget(self._step_counter)

            self._title_label = QLabel("")
            self._title_label.setStyleSheet(
                "color: #FFFFFF; font-size: 16px; font-weight: bold;"
            )
            self._title_label.setWordWrap(True)
            card_layout.addWidget(self._title_label)

            self._desc_label = QLabel("")
            self._desc_label.setStyleSheet(
                "color: #C8D6E5; font-size: 13px;"
            )
            self._desc_label.setWordWrap(True)
            card_layout.addWidget(self._desc_label)

            # Navigation buttons
            btn_row = QHBoxLayout()
            btn_row.setSpacing(8)

            self._skip_btn = QPushButton("Skip Tutorial")
            self._skip_btn.setStyleSheet(
                "color: #8B9DC3; background: transparent; "
                "border: 1px solid #4A5568; padding: 6px 12px;"
            )
            self._skip_btn.clicked.connect(self._finish)
            btn_row.addWidget(self._skip_btn)

            btn_row.addStretch(1)

            self._next_btn = QPushButton("Next →")
            self._next_btn.setStyleSheet(
                "color: #FFFFFF; background: #4A90D9; "
                "border: none; padding: 6px 16px; border-radius: 6px;"
            )
            self._next_btn.clicked.connect(self._advance)
            btn_row.addWidget(self._next_btn)

            card_layout.addLayout(btn_row)

            self._card.setFixedWidth(380)

            self._show_step(0)

        def start(self) -> None:
            """Show the overlay and begin the tutorial."""
            self.resize(self.parent().size())
            self.show()
            self.raise_()

        def paintEvent(self, event: object) -> None:
            """Draw semi-transparent backdrop with cutout around target."""
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Dark overlay
            painter.fillRect(self.rect(), QColor(0, 0, 0, 140))

            # Cut out the highlighted widget
            if self._target_widget is not None and self._target_widget.isVisible():
                target_rect = self._widget_rect(self._target_widget)
                padded = target_rect.adjusted(-6, -6, 6, 6)

                path = QPainterPath()
                path.addRect(float(self.rect().x()), float(self.rect().y()),
                             float(self.rect().width()), float(self.rect().height()))
                cutout = QPainterPath()
                cutout.addRoundedRect(
                    float(padded.x()), float(padded.y()),
                    float(padded.width()), float(padded.height()),
                    8.0, 8.0,
                )
                path -= cutout

                painter.fillPath(path, QColor(0, 0, 0, 140))

                # Highlight border
                painter.setPen(QColor("#4A90D9"))
                painter.drawRoundedRect(padded, 8.0, 8.0)

            painter.end()

        def resizeEvent(self, event: object) -> None:
            """Reposition card when window resizes."""
            self._position_card()

        # ── Internal ──────────────────────────────────────────

        def _show_step(self, index: int) -> None:
            if index < 0 or index >= len(TUTORIAL_STEPS):
                self._finish()
                return

            self._step_index = index
            step = TUTORIAL_STEPS[index]

            self._step_counter.setText(
                f"Step {index + 1} of {len(TUTORIAL_STEPS)}"
            )
            self._title_label.setText(step.title)
            self._desc_label.setText(step.description)

            is_last = index == len(TUTORIAL_STEPS) - 1
            self._next_btn.setText("Finish" if is_last else "Next →")

            # Resolve target widget
            self._target_widget = None
            if step.widget_attr:
                parent = self.parent()
                self._target_widget = getattr(parent, step.widget_attr, None)

            self._position_card()
            self.update()

        def _advance(self) -> None:
            if self._step_index >= len(TUTORIAL_STEPS) - 1:
                self._finish()
            else:
                self._show_step(self._step_index + 1)

        def _finish(self) -> None:
            self.hide()
            self.deleteLater()

        def _widget_rect(self, widget: QWidget) -> QRect:
            """Map a widget's geometry to overlay coordinates."""
            pos = widget.mapTo(self, QPoint(0, 0))
            return QRect(pos, widget.size())

        def _position_card(self) -> None:
            """Place the tooltip card near the highlighted widget."""
            if self._target_widget and self._target_widget.isVisible():
                rect = self._widget_rect(self._target_widget)
                card_x = rect.right() + 16
                card_y = rect.top()
                # Keep card on screen
                if card_x + self._card.width() > self.width():
                    card_x = rect.left() - self._card.width() - 16
                if card_y + self._card.sizeHint().height() > self.height():
                    card_y = self.height() - self._card.sizeHint().height() - 20
                self._card.move(max(card_x, 10), max(card_y, 10))
            else:
                # Center the card
                self._card.move(
                    (self.width() - self._card.width()) // 2,
                    (self.height() - self._card.sizeHint().height()) // 2,
                )

else:

    class TutorialOverlay:  # type: ignore[no-redef]
        """Stub when PyQt6 is not installed."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def start(self) -> None:
            pass
