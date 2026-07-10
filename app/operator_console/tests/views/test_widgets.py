"""Tests for custom operator console widgets."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.operator_console.views.shared.widgets import (
    STATUS_ACTIVE,
    STATUS_IDLE,
    STATUS_STALE,
    STATUS_WARNING,
    AgentSummaryCard,
    FlippableTextCard,
    KeyValuePanel,
    ProviderBadge,
    SectionHeader,
    StatusIndicator,
    build_compact_button_grid,
    compact_display_text,
    configure_compact_button,
)

try:
    from PyQt6.QtWidgets import QApplication
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "PyQt6 is not installed")
class StatusIndicatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_default_level_is_idle(self) -> None:
        dot = StatusIndicator()
        self.assertEqual(dot.level, STATUS_IDLE)
        self.assertEqual(dot.objectName(), "StatusIndicator")
        self.assertEqual(dot.property("statusLevel"), STATUS_IDLE)

    def test_set_level_updates_property(self) -> None:
        dot = StatusIndicator()
        dot.set_level(STATUS_ACTIVE)
        self.assertEqual(dot.level, STATUS_ACTIVE)
        self.assertEqual(dot.property("statusLevel"), STATUS_ACTIVE)
        dot.set_level(STATUS_WARNING)
        self.assertEqual(dot.level, STATUS_WARNING)
        self.assertEqual(dot.property("statusLevel"), STATUS_WARNING)
        dot.set_level(STATUS_STALE)
        self.assertEqual(dot.level, STATUS_STALE)
        self.assertEqual(dot.property("statusLevel"), STATUS_STALE)

    def test_set_same_level_is_noop(self) -> None:
        dot = StatusIndicator()
        dot.set_level(STATUS_IDLE)
        self.assertEqual(dot.level, STATUS_IDLE)

    def test_status_indicator_does_not_use_inline_stylesheet(self) -> None:
        dot = StatusIndicator()
        dot.set_level(STATUS_ACTIVE)
        self.assertEqual(dot.styleSheet(), "")


@unittest.skipIf(QApplication is None, "PyQt6 is not installed")
class SectionHeaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_title_renders_in_label(self) -> None:
        header = SectionHeader("Codex Reviewer")
        self.assertEqual(header.title_label.text(), "Codex Reviewer")

    def test_set_title_updates_label(self) -> None:
        header = SectionHeader("Old")
        header.set_title("Codex Bridge Monitor")
        self.assertEqual(header.title_label.text(), "Codex Bridge Monitor")

    def test_set_status_updates_dot(self) -> None:
        header = SectionHeader("Test")
        header.set_status(STATUS_WARNING)
        self.assertEqual(header.status_dot.level, STATUS_WARNING)


@unittest.skipIf(QApplication is None, "PyQt6 is not installed")
class ProviderBadgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_provider_badge_sets_expected_properties(self) -> None:
        badge = ProviderBadge("Codex")
        self.assertEqual(badge.provider_id, "codex")
        self.assertEqual(badge.text(), "CX")
        self.assertEqual(badge.property("providerId"), "codex")


@unittest.skipIf(QApplication is None, "PyQt6 is not installed")
class CompactButtonGridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_compact_button_treatment_keeps_button_max_width(self) -> None:
        from PyQt6.QtWidgets import QPushButton, QSizePolicy

        button = configure_compact_button(QPushButton("Start Swarm"))

        self.assertEqual(button.objectName(), "SmallActionButton")
        self.assertEqual(
            button.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Maximum,
        )

    def test_button_grid_preserves_compact_buttons(self) -> None:
        from PyQt6.QtWidgets import QPushButton, QSizePolicy

        first = QPushButton("Dashboard")
        second = QPushButton("Monitor")
        grid = build_compact_button_grid((first, second), columns=2)

        self.assertEqual(grid.objectName(), "CompactButtonGrid")
        self.assertEqual(
            first.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Maximum,
        )
        self.assertEqual(
            second.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Maximum,
        )


class CompactDisplayTextTests(unittest.TestCase):
    def test_compact_display_text_preserves_short_copy(self) -> None:
        self.assertEqual(compact_display_text("Short copy", limit=20), "Short copy")

    def test_compact_display_text_collapses_whitespace_and_trims(self) -> None:
        rendered = compact_display_text("A   long\n\nline of   copy that keeps going", limit=18)
        self.assertEqual(rendered, "A long line of...")


@unittest.skipIf(QApplication is None, "PyQt6 is not installed")
class KeyValuePanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_set_rows_populates_kv_layout(self) -> None:
        panel = KeyValuePanel("Test Panel")
        panel.set_rows([("Status", "Active"), ("Last Poll", "2s ago")])
        # Two row widgets should have been added
        self.assertEqual(len(panel._row_widgets), 2)

    def test_set_rows_replaces_previous_rows(self) -> None:
        panel = KeyValuePanel("Test Panel")
        panel.set_rows([("A", "1"), ("B", "2"), ("C", "3")])
        self.assertEqual(len(panel._row_widgets), 3)
        panel.set_rows([("X", "9")])
        self.assertEqual(len(panel._row_widgets), 1)

    def test_set_raw_text_updates_raw_view(self) -> None:
        panel = KeyValuePanel("Test Panel")
        panel.set_raw_text("raw content here")
        self.assertEqual(panel._raw_text.toPlainText(), "raw content here")

    def test_toggle_switches_between_kv_and_raw(self) -> None:
        panel = KeyValuePanel("Test Panel")
        self.assertFalse(panel._showing_raw)
        self.assertEqual(panel._stack.currentIndex(), 0)
        panel._toggle_view()
        self.assertTrue(panel._showing_raw)
        self.assertEqual(panel._stack.currentIndex(), 1)
        panel._toggle_view()
        self.assertFalse(panel._showing_raw)
        self.assertEqual(panel._stack.currentIndex(), 0)

    def test_set_status_propagates_to_header(self) -> None:
        panel = KeyValuePanel("Test Panel")
        panel.set_status(STATUS_ACTIVE)
        self.assertEqual(panel.header.status_dot.level, STATUS_ACTIVE)

    def test_set_title_updates_header_text(self) -> None:
        panel = KeyValuePanel("Test Panel")
        panel.set_title("Operator Bridge State")
        self.assertEqual(panel.header.title_label.text(), "Operator Bridge State")

    def test_kv_label_uses_responsive_width(self) -> None:
        """KV labels should use min/max width instead of fixed width."""
        panel = KeyValuePanel("Test Panel")
        panel.set_rows([("Status", "Active")])
        row = panel._row_widgets[0]
        label = row.findChild(type(panel.header.title_label), "KVLabel")
        self.assertIsNotNone(label)
        self.assertEqual(label.minimumWidth(), 50)
        self.assertEqual(label.maximumWidth(), 80)
        # Must NOT have a fixed width set (minimumWidth != maximumWidth)
        self.assertNotEqual(label.minimumWidth(), label.maximumWidth())

    def test_kv_value_has_expanding_policy(self) -> None:
        """KV value labels should expand to fill available space."""
        from PyQt6.QtWidgets import QSizePolicy

        panel = KeyValuePanel("Test Panel")
        panel.set_rows([("Key", "Some long value text")])
        row = panel._row_widgets[0]
        value = row.findChild(type(panel.header.title_label), "KVValue")
        self.assertIsNotNone(value)
        self.assertEqual(
            value.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Expanding,
        )


@unittest.skipIf(QApplication is None, "PyQt6 is not installed")
class FlippableTextCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_front_face_is_visible_by_default(self) -> None:
        from PyQt6.QtWidgets import QPlainTextEdit

        front = QPlainTextEdit()
        back = QPlainTextEdit()
        card = FlippableTextCard(
            front_widget=front,
            back_widget=back,
            front_title="Codex Stats",
            front_subtitle="Freshness, signals, and screen",
            back_title="Codex Registry",
            back_subtitle="Lane assignments and states",
            provider_name="Codex",
        )

        self.assertFalse(card.showing_back)
        self.assertEqual(card.current_title, "Codex Stats")
        self.assertEqual(card._stack.currentWidget(), front)

    def test_toggle_face_switches_title_and_widget(self) -> None:
        from PyQt6.QtWidgets import QPlainTextEdit

        front = QPlainTextEdit()
        back = QPlainTextEdit()
        card = FlippableTextCard(
            front_widget=front,
            back_widget=back,
            front_title="Claude Stats",
            front_subtitle="Freshness, signals, and screen",
            back_title="Claude Registry",
            back_subtitle="Lane assignments and states",
            provider_name="Claude",
        )

        card.toggle_face()
        self.assertTrue(card.showing_back)
        self.assertEqual(card.current_title, "Claude Registry")
        self.assertEqual(card._stack.currentWidget(), back)

        card.toggle_face()
        self.assertFalse(card.showing_back)
        self.assertEqual(card.current_title, "Claude Stats")
        self.assertEqual(card._stack.currentWidget(), front)


@unittest.skipIf(QApplication is None, "PyQt6 is not installed")
class AgentSummaryCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_update_card_sets_all_fields(self) -> None:
        card = AgentSummaryCard("Codex", role="Reviewer")
        card.set_identity(
            agent_name="Codex",
            role="Reviewer",
            lane_title="Codex Bridge Monitor",
        )
        card.update_card(
            status_level=STATUS_ACTIVE,
            status_text="Reviewing",
            detail_text="Last poll: 2s ago",
        )
        self.assertEqual(card.status_dot.level, STATUS_ACTIVE)
        self.assertEqual(card.status_label.text(), "Reviewing")
        self.assertEqual(card.detail_label.text(), "Last poll: 2s ago")
        self.assertEqual(card.lane_label.text(), "Codex Bridge Monitor")

    def test_default_state_is_idle(self) -> None:
        card = AgentSummaryCard("Claude")
        self.assertEqual(card.status_label.text(), "Idle")

    def test_set_identity_updates_name_role_and_lane(self) -> None:
        card = AgentSummaryCard("Claude")
        card.set_identity(
            agent_name="Claude",
            role="Implementer",
            lane_title="Claude Bridge Monitor",
        )
        self.assertEqual(card.name_label.text(), "Claude")
        self.assertEqual(card.role_badge.text(), "Implementer")
        self.assertEqual(card.lane_label.text(), "Claude Bridge Monitor")


if __name__ == "__main__":
    unittest.main()
