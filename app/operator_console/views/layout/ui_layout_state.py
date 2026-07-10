"""Layout-state persistence helpers for the Operator Console window."""

from __future__ import annotations

from pathlib import Path

from ...layout.layout_state import (
    LayoutStateSnapshot,
    load_layout_state,
    save_layout_state,
)
from .ui_layouts import (
    DEFAULT_LAYOUT_ID,
    DEFAULT_WORKBENCH_PRESET_ID,
    resolve_layout,
    resolve_workbench_preset,
)
from .workbench_layout import apply_workbench_preset


class LayoutStateMixin:
    """Persist, export, import, and restore workbench layout state."""

    def _apply_pending_layout_state(self) -> None:
        """Apply persisted tab/splitter state after the layout is constructed."""
        state = self._pending_layout_state
        self._pending_layout_state = None
        if state is None or self._layout_mode != "workbench":
            return
        if state.workbench_surface:
            self._select_workbench_surface(state.workbench_surface)
        if state.monitor_surface:
            self._select_monitor_surface(state.monitor_surface)
        if (
            state.lane_splitter_sizes is not None
            and getattr(self, "_workbench_lane_splitter", None) is not None
        ):
            self._workbench_lane_splitter.setSizes(list(state.lane_splitter_sizes))
        if (
            state.utility_splitter_sizes is not None
            and getattr(self, "_workbench_utility_splitter", None) is not None
        ):
            self._workbench_utility_splitter.setSizes(list(state.utility_splitter_sizes))

    def _reset_layout_state(self) -> None:
        """Restore the default layout arrangement and persist it."""
        target_mode = DEFAULT_LAYOUT_ID
        self._workbench_preset = DEFAULT_WORKBENCH_PRESET_ID
        if self._layout_mode != target_mode:
            self._switch_layout(target_mode)
            self._set_combo_data(self.layout_combo, target_mode)
        if self._layout_mode == "workbench":
            apply_workbench_preset(
                self,
                DEFAULT_WORKBENCH_PRESET_ID,
                announce=False,
            )
            self._select_workbench_surface("sessions")
            self._select_monitor_surface("command_output")
        self._persist_layout_state()
        self._record_event(
            "INFO",
            "layout_state_reset",
            "Operator Console layout state reset to defaults",
            details={"layout_mode": self._layout_mode},
        )
        self.statusBar().showMessage("Layout state reset to defaults.")

    def _export_layout_state_snapshot(self) -> None:
        """Write a copy of current layout state to an explicit export path."""
        export_path = self._layout_state_export_path()
        if export_path is None:
            self.statusBar().showMessage("Layout state export is disabled.")
            return
        snapshot = self._capture_layout_state_snapshot()
        try:
            save_layout_state(export_path, snapshot)
        except OSError as exc:
            self._record_event(
                "WARNING",
                "layout_state_export_failed",
                "Failed to export layout state snapshot",
                details={"path": str(export_path), "error": str(exc)},
            )
            self.statusBar().showMessage("Layout state export failed.")
            return
        self._record_event(
            "INFO",
            "layout_state_exported",
            "Exported layout state snapshot",
            details={"path": str(export_path)},
        )
        self.statusBar().showMessage(f"Exported layout state: {export_path}")

    def _import_layout_state_snapshot(self) -> None:
        """Load a previously exported layout snapshot and apply it."""
        export_path = self._layout_state_export_path()
        if export_path is None:
            self.statusBar().showMessage("Layout state import is disabled.")
            return
        snapshot = load_layout_state(export_path)
        if snapshot is None:
            self.statusBar().showMessage(
                f"No readable layout export found at {export_path}."
            )
            return
        self._apply_layout_state_snapshot(snapshot)
        self._record_event(
            "INFO",
            "layout_state_imported",
            "Imported layout state snapshot",
            details={"path": str(export_path)},
        )
        self.statusBar().showMessage(f"Imported layout state: {export_path}")

    def _apply_layout_state_snapshot(self, snapshot: LayoutStateSnapshot) -> None:
        """Apply a captured layout snapshot to the current window state."""
        target_mode = resolve_layout(snapshot.layout_mode).mode_id
        self._workbench_preset = resolve_workbench_preset(
            snapshot.workbench_preset
        ).preset_id
        self._pending_layout_state = snapshot
        if self._layout_mode != target_mode:
            self._switch_layout(target_mode)
        self._set_combo_data(self.layout_combo, target_mode)
        self._apply_pending_layout_state()
        if target_mode == "workbench":
            apply_workbench_preset(self, self._workbench_preset, announce=False)
            if snapshot.lane_splitter_sizes is not None:
                self._workbench_lane_splitter.setSizes(list(snapshot.lane_splitter_sizes))
            if snapshot.utility_splitter_sizes is not None:
                self._workbench_utility_splitter.setSizes(
                    list(snapshot.utility_splitter_sizes)
                )
        self._persist_layout_state()

    def _layout_state_export_path(self) -> Path | None:
        if self._layout_state_path is None:
            return None
        return self._layout_state_path.with_name("layout_state_export.json")

    def _capture_layout_state_snapshot(self) -> LayoutStateSnapshot:
        """Capture current layout identifiers and splitter ratios."""
        return LayoutStateSnapshot(
            layout_mode=self._layout_mode,
            workbench_preset=self._workbench_preset,
            workbench_surface=self._selected_surface_id(
                indexes=getattr(self, "_workbench_surface_indexes", {}),
                current_index=getattr(self._workbench_tabs, "currentIndex", lambda: -1)(),
            ),
            monitor_surface=self._selected_surface_id(
                indexes=getattr(self, "_monitor_surface_indexes", {}),
                current_index=getattr(self._monitor_tabs, "currentIndex", lambda: -1)(),
            ),
            lane_splitter_sizes=self._splitter_sizes(
                getattr(self, "_workbench_lane_splitter", None)
            ),
            utility_splitter_sizes=self._splitter_sizes(
                getattr(self, "_workbench_utility_splitter", None)
            ),
        )

    def _persist_layout_state(self) -> None:
        """Write current layout state to disk for reproducible support reports."""
        if not self._layout_state_ready:
            return
        if self._layout_state_path is None:
            return
        snapshot = self._capture_layout_state_snapshot()
        try:
            save_layout_state(self._layout_state_path, snapshot)
        except OSError as exc:
            self._record_event(
                "WARNING",
                "layout_state_persist_failed",
                "Failed to persist layout state",
                details={
                    "path": str(self._layout_state_path),
                    "error": str(exc),
                },
            )

    @staticmethod
    def _selected_surface_id(indexes: dict[str, int], current_index: int) -> str | None:
        for surface_id, index in indexes.items():
            if index == current_index:
                return surface_id
        return None

    @staticmethod
    def _splitter_sizes(splitter: object) -> tuple[int, int, int] | None:
        if splitter is None:
            return None
        sizes = getattr(splitter, "sizes", None)
        if not callable(sizes):
            return None
        values = sizes()
        if not isinstance(values, list) or len(values) != 3:
            return None
        normalized = [max(int(value), 1) for value in values]
        return (normalized[0], normalized[1], normalized[2])
