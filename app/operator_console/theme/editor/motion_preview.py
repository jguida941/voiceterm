"""Interactive motion playground used by the Theme Editor preview."""

from __future__ import annotations

try:
    from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt
    from PyQt6.QtWidgets import (
        QFrame,
        QGraphicsOpacityEffect,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False


if _PYQT_AVAILABLE:

    class ThemeMotionPlayground(QWidget):
        """Preview-only motion stage for theme authoring."""

        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self._motion_enabled = True
            self._page_transition = "fade"
            self._page_transition_ms = 160
            self._pulse_duration_ms = 280
            self._hover_emphasis = "soft"
            self._curve_name = "out-cubic"

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)

            controls = QHBoxLayout()
            controls.setContentsMargins(0, 0, 0, 0)
            controls.setSpacing(8)

            front_btn = QPushButton("Front")
            front_btn.clicked.connect(lambda: self._switch_to(0))
            controls.addWidget(front_btn)

            back_btn = QPushButton("Back")
            back_btn.clicked.connect(lambda: self._switch_to(1))
            controls.addWidget(back_btn)

            pulse_btn = QPushButton("Pulse")
            pulse_btn.clicked.connect(self._pulse)
            controls.addWidget(pulse_btn)
            controls.addStretch(1)
            layout.addLayout(controls)

            self._stack = QStackedWidget()
            self._stack.addWidget(self._build_card("Front Card", "Toolbar, sessions, and quick actions"))
            self._stack.addWidget(self._build_card("Back Card", "Approvals, diagnostics, and repo signals"))
            self._stack_effect = QGraphicsOpacityEffect(self._stack)
            self._stack.setGraphicsEffect(self._stack_effect)
            self._stack_effect.setOpacity(1.0)
            layout.addWidget(self._stack)

            self._pulse_bar = QFrame()
            self._pulse_bar.setObjectName("MotionPulseBar")
            self._pulse_bar.setFixedHeight(6)
            self._pulse_bar.setMaximumWidth(64)
            layout.addWidget(self._pulse_bar, alignment=Qt.AlignmentFlag.AlignLeft)

            self._summary = QLabel("")
            self._summary.setObjectName("CardDetailLabel")
            self._summary.setWordWrap(True)
            layout.addWidget(self._summary)
            self._refresh_summary()

        def set_motion_settings(self, motion: dict[str, str]) -> None:
            self._motion_enabled = str(motion.get("motion_enabled", "true")).lower() == "true"
            self._page_transition = str(motion.get("page_transition", "fade"))
            self._hover_emphasis = str(motion.get("hover_emphasis", "soft"))
            self._curve_name = str(motion.get("motion_curve", "out-cubic"))
            self._page_transition_ms = _int_value(motion.get("page_transition_ms"), 160)
            self._pulse_duration_ms = _int_value(motion.get("pulse_duration_ms"), 280)
            self._refresh_summary()

        def _build_card(self, title: str, detail: str) -> QFrame:
            card = QFrame()
            card.setObjectName("LaneCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(6)

            heading = QLabel(title)
            heading.setObjectName("LaneAgentName")
            layout.addWidget(heading)

            summary = QLabel(detail)
            summary.setObjectName("CardDetailLabel")
            summary.setWordWrap(True)
            layout.addWidget(summary)

            status = QLabel("Motion preview follows the active component chrome.")
            status.setObjectName("CardStatusLabel")
            status.setWordWrap(True)
            layout.addWidget(status)
            layout.addStretch(1)
            return card

        def _refresh_summary(self) -> None:
            if not self._motion_enabled:
                self._summary.setText("Motion disabled. Front/back swaps and pulse previews update instantly.")
                return
            self._summary.setText(
                f"{self._page_transition.title()} page transition at {self._page_transition_ms}ms, "
                f"{self._hover_emphasis} pulse at {self._pulse_duration_ms}ms, curve {self._curve_name}."
            )

        def _switch_to(self, index: int) -> None:
            if index == self._stack.currentIndex():
                return
            if not self._motion_enabled or self._page_transition == "none" or self._page_transition_ms <= 0:
                self._stack.setCurrentIndex(index)
                return
            self._animate_page_swap(index)

        def _animate_page_swap(self, index: int) -> None:
            fade_out = QPropertyAnimation(self._stack_effect, b"opacity", self)
            fade_out.setDuration(max(40, self._page_transition_ms // 2))
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.18)
            fade_out.setEasingCurve(_curve_type(self._curve_name))

            fade_in = QPropertyAnimation(self._stack_effect, b"opacity", self)
            fade_in.setDuration(max(40, self._page_transition_ms // 2))
            fade_in.setStartValue(0.18)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(_curve_type(self._curve_name))

            def apply_new_card() -> None:
                self._stack.setCurrentIndex(index)
                fade_in.start()

            fade_out.finished.connect(apply_new_card)
            fade_out.start()
            self._active_animation = fade_out
            self._secondary_animation = fade_in

        def _pulse(self) -> None:
            if not self._motion_enabled or self._hover_emphasis == "none" or self._pulse_duration_ms <= 0:
                return
            target = 150 if self._hover_emphasis == "soft" else 240
            expand = QPropertyAnimation(self._pulse_bar, b"maximumWidth", self)
            expand.setDuration(max(60, self._pulse_duration_ms // 2))
            expand.setStartValue(64)
            expand.setEndValue(target)
            expand.setEasingCurve(_curve_type(self._curve_name))

            collapse = QPropertyAnimation(self._pulse_bar, b"maximumWidth", self)
            collapse.setDuration(max(60, self._pulse_duration_ms // 2))
            collapse.setStartValue(target)
            collapse.setEndValue(64)
            collapse.setEasingCurve(_curve_type(self._curve_name))
            expand.finished.connect(collapse.start)
            expand.start()
            self._active_pulse = expand
            self._secondary_pulse = collapse


    def _int_value(value: object, fallback: int) -> int:
        try:
            return int(str(value))
        except (TypeError, ValueError):
            return fallback


    def _curve_type(name: str) -> QEasingCurve.Type:
        return {
            "linear": QEasingCurve.Type.Linear,
            "out-quad": QEasingCurve.Type.OutQuad,
            "out-cubic": QEasingCurve.Type.OutCubic,
        }.get(name, QEasingCurve.Type.OutCubic)

else:

    class ThemeMotionPlayground:  # type: ignore[no-redef]
        """Stub when PyQt6 is not installed."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def set_motion_settings(self, motion: dict[str, str]) -> None:
            del motion
