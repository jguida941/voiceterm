"""Menu, dialog, and shell chrome helpers for the layout package."""

from __future__ import annotations

from ...theme import available_theme_ids, resolve_theme
from ..help_dialog import OperatorHelpDialog
from .ui_layouts import available_layout_ids, resolve_layout

try:
    from ...theme.editor.theme_editor import ThemeEditorDialog as _ThemeEditorDialog

    HAS_THEME_EDITOR = True
except ImportError:
    _ThemeEditorDialog = None
    HAS_THEME_EDITOR = False

try:
    from PyQt6.QtGui import QAction, QActionGroup
    from PyQt6.QtWidgets import QComboBox, QDialog
except ImportError:
    QAction = QActionGroup = QComboBox = QDialog = None


class WindowShellMixin:
    """Menu bar, help dialog, theme editor, and simple navigation helpers."""

    def _setup_menu_bar(self) -> None:
        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(True)

        run_menu = menu_bar.addMenu("&Run")
        for label, handler in [
            ("Refresh Snapshot", self.request_manual_refresh),
            ("Workflow Audit", self.run_workflow_audit),
            ("Run Selected Loop", self.run_selected_plan_loop),
            ("Dry Run", self.launch_dry_run),
            ("Live Launch", self.launch_live),
            ("Launch Review", self.start_swarm),
            ("Rollover", self.rollover_live),
            ("CI Status", self.show_ci_status),
            ("Triage", self.run_triage),
            ("Process Audit", self.run_process_audit),
        ]:
            action = QAction(label, self)
            action.triggered.connect(handler)
            run_menu.addAction(action)

        view_menu = menu_bar.addMenu("&View")
        read_menu = view_menu.addMenu("Read Mode")
        read_group = QActionGroup(self)
        read_group.setExclusive(True)
        for mode_id in ("simple", "technical"):
            action = QAction(mode_id.title(), self)
            action.setCheckable(True)
            action.setChecked(mode_id == self.read_mode_combo.currentData())
            action.triggered.connect(
                lambda checked=False, value=mode_id: self._set_combo_data(
                    self.read_mode_combo,
                    value,
                )
            )
            read_group.addAction(action)
            read_menu.addAction(action)

        layout_menu = view_menu.addMenu("Layout")
        layout_group = QActionGroup(self)
        layout_group.setExclusive(True)
        for layout_id in available_layout_ids():
            desc = resolve_layout(layout_id)
            action = QAction(desc.display_name, self)
            action.setCheckable(True)
            action.setChecked(layout_id == self._layout_mode)
            action.triggered.connect(
                lambda checked=False, value=layout_id: self._set_combo_data(
                    self.layout_combo,
                    value,
                )
            )
            layout_group.addAction(action)
            layout_menu.addAction(action)
        layout_menu.addSeparator()
        reset_layout_action = QAction("Reset Saved Layout State", self)
        reset_layout_action.triggered.connect(self._reset_layout_state)
        layout_menu.addAction(reset_layout_action)
        export_layout_action = QAction("Export Layout State Snapshot", self)
        export_layout_action.triggered.connect(self._export_layout_state_snapshot)
        layout_menu.addAction(export_layout_action)
        import_layout_action = QAction("Import Layout State Snapshot", self)
        import_layout_action.triggered.connect(self._import_layout_state_snapshot)
        layout_menu.addAction(import_layout_action)

        theme_menu = menu_bar.addMenu("&Theme")
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        current_theme_id = self.theme_combo.currentData()
        for theme_id in available_theme_ids():
            theme = resolve_theme(theme_id)
            action = QAction(theme.display_name, self)
            action.setCheckable(True)
            action.setChecked(theme_id == current_theme_id)
            action.triggered.connect(
                lambda checked=False, value=theme_id: self._set_combo_data(
                    self.theme_combo,
                    value,
                )
            )
            theme_group.addAction(action)
            theme_menu.addAction(action)

        if getattr(self, "theme_editor_btn", None) is not None:
            theme_menu.addSeparator()
            theme_editor_action = QAction("Open Theme Editor", self)
            theme_editor_action.triggered.connect(self._open_theme_editor)
            theme_menu.addAction(theme_editor_action)

        settings_menu = menu_bar.addMenu("&Settings")
        threshold_menu = settings_menu.addMenu("Threshold")
        threshold_group = QActionGroup(self)
        threshold_group.setExclusive(True)
        for value in (25, 50, 75):
            action = QAction(f"{value}%", self)
            action.setCheckable(True)
            action.setChecked(value == self.threshold_spin.value())
            action.triggered.connect(
                lambda checked=False, current=value: self.threshold_spin.setValue(current)
            )
            threshold_group.addAction(action)
            threshold_menu.addAction(action)

        ack_menu = settings_menu.addMenu("ACK Wait")
        ack_group = QActionGroup(self)
        ack_group.setExclusive(True)
        for value in (60, 180, 300):
            action = QAction(f"{value}s", self)
            action.setCheckable(True)
            action.setChecked(value == self.ack_wait_spin.value())
            action.triggered.connect(
                lambda checked=False, current=value: self.ack_wait_spin.setValue(current)
            )
            ack_group.addAction(action)
            ack_menu.addAction(action)

        help_menu = menu_bar.addMenu("&Help")
        guide_action = QAction("Operator Guide", self)
        guide_action.triggered.connect(lambda: self._open_help_dialog("overview"))
        help_menu.addAction(guide_action)

        controls_action = QAction("Controls Reference", self)
        controls_action.triggered.connect(lambda: self._open_help_dialog("controls"))
        help_menu.addAction(controls_action)

        theme_help_action = QAction("Theme Notes", self)
        theme_help_action.triggered.connect(lambda: self._open_help_dialog("theme"))
        help_menu.addAction(theme_help_action)

        mobile_help_action = QAction("Mobile Relay", self)
        mobile_help_action.triggered.connect(lambda: self._open_help_dialog("mobile"))
        help_menu.addAction(mobile_help_action)

        developer_menu = menu_bar.addMenu("&Developer")
        developer_notes_action = QAction("How This Runs", self)
        developer_notes_action.triggered.connect(
            lambda: self._open_help_dialog("developer")
        )
        developer_menu.addAction(developer_notes_action)

        refresh_action = QAction("Refresh Snapshot", self)
        refresh_action.triggered.connect(self.request_manual_refresh)
        developer_menu.addAction(refresh_action)

    def _open_dashboard_surface(self) -> None:
        self._navigate_primary_surface("dashboard")

    def _open_monitor_surface(self) -> None:
        self._navigate_primary_surface("monitor")

    def _open_activity_surface(self) -> None:
        self._navigate_primary_surface("activity")

    def _set_combo_data(self, combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _open_help_dialog(self, topic_id: str) -> None:
        if self._help_dialog is None:
            dialog = OperatorHelpDialog(self)
            dialog.setModal(False)
            dialog.finished.connect(lambda *_: self._on_help_dialog_closed())
            self._help_dialog = dialog
        else:
            dialog = self._help_dialog

        dialog.show_topic(topic_id)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        self.statusBar().showMessage("Operator guide opened", 3000)

    def _on_help_dialog_closed(self) -> None:
        self._help_dialog = None
        self.statusBar().showMessage("Operator guide closed", 3000)

    def _open_theme_editor(self) -> None:
        """Open the full theme editor dialog."""
        if self._theme_editor_dialog is None:
            dialog = _ThemeEditorDialog(self)
            dialog.setModal(False)
            dialog.finished.connect(lambda *_: self._on_theme_editor_closed())
            self._theme_editor_dialog = dialog
        else:
            dialog = self._theme_editor_dialog

        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        self.statusBar().showMessage("Theme editor opened", 3000)

    def _on_theme_editor_closed(self) -> None:
        """Clear the cached dialog reference after the editor closes."""
        self._theme_editor_dialog = None
        self.statusBar().showMessage("Theme editor closed", 3000)
