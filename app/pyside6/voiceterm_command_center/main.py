"""Main entrypoint for VoiceTerm Command Center."""

from __future__ import annotations

import sys

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from voiceterm_command_center.tabs.catalog_tab import CatalogTab
from voiceterm_command_center.tabs.git_tab import GitTab
from voiceterm_command_center.tabs.quick_ops_tab import QuickOpsTab
from voiceterm_command_center.tabs.runs_tab import RunsTab
from voiceterm_command_center.tabs.terminal_tab import TerminalTab


class CommandCenterWindow(QMainWindow):
    """Main window with tabbed control-plane surfaces."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VoiceTerm Command Center (PySide6)")

        self._tabs = QTabWidget()
        self._tabs.addTab(QuickOpsTab(), "Quick Ops")
        self._tabs.addTab(CatalogTab(), "Catalog")
        self._tabs.addTab(RunsTab(), "GitHub Runs")
        self._tabs.addTab(GitTab(), "Git")
        self._tabs.addTab(TerminalTab(), "Terminal")
        self.setCentralWidget(self._tabs)

        self._settings = QSettings("VoiceTerm", "CommandCenter")
        self._restore_ui_state()

    def closeEvent(self, event) -> None:  # noqa: N802
        self._save_ui_state()
        super().closeEvent(event)

    def _restore_ui_state(self) -> None:
        size = self._settings.value("window_size")
        pos = self._settings.value("window_pos")
        tab_index = self._settings.value("tab_index")
        if size is not None:
            self.resize(size)
        else:
            self.resize(1400, 900)
        if pos is not None:
            self.move(pos)
        if isinstance(tab_index, int):
            self._tabs.setCurrentIndex(tab_index)

    def _save_ui_state(self) -> None:
        self._settings.setValue("window_size", self.size())
        self._settings.setValue("window_pos", self.pos())
        self._settings.setValue("tab_index", self._tabs.currentIndex())


def run() -> int:
    """Run the desktop app."""

    app = QApplication(sys.argv)
    window = CommandCenterWindow()
    window.show()
    return app.exec()
