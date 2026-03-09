"""Theme editor dialog for the Operator Console."""

from __future__ import annotations

from pathlib import Path

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QFileDialog,
        QFormLayout,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPlainTextEdit,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QSplitter,
        QStackedWidget,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False


if _PYQT_AVAILABLE:
    from .theme_controls import ColorPickerButton
    from .theme_engine import BUILTIN_PRESETS, ThemeEngine, get_engine
    from .theme_preview import ThemePreview
    from .theme_tokens import TOKEN_CATEGORIES, TOKEN_SPECS

    _SURFACE_COLOR_GROUPS = (
        (
            "Window + Panels",
            (
                "bg_top",
                "bg_bottom",
                "panel",
                "panel_alt",
                "panel_elevated",
                "panel_surface",
                "panel_surface_alt",
                "panel_inset",
            ),
        ),
        (
            "Toolbar + Header",
            (
                "toolbar_bg",
                "header_from",
                "header_mid",
                "header_to",
            ),
        ),
        (
            "Text + Borders",
            (
                "text",
                "text_muted",
                "text_dim",
                "border",
                "border_soft",
                "menu_border_subtle",
                "card_border",
                "card_hover_border",
                "input_border",
            ),
        ),
    )

    _NAVIGATION_COLOR_GROUPS = (
        (
            "Sidebar + Selection",
            (
                "sidebar_selected_bg",
                "selection_bg",
                "selection_text",
            ),
        ),
        (
            "Splitters + Scrollbars",
            (
                "splitter",
                "splitter_hover",
                "scrollbar_handle_start",
                "scrollbar_handle_stop",
                "scrollbar_handle_hover_start",
                "scrollbar_handle_hover_stop",
                "scrollbar_track_bg",
                "hover_overlay",
            ),
        ),
        (
            "Status + Badges",
            (
                "status_active",
                "status_warning",
                "status_stale",
                "status_idle",
                "badge_bg",
                "badge_border",
            ),
        ),
    )

    _WORKFLOW_COLOR_GROUPS = (
        (
            "Accent + Alerts",
            (
                "accent",
                "accent_soft",
                "accent_deep",
                "warning",
                "danger",
            ),
        ),
        (
            "Buttons + Gradients",
            (
                "button_primary_bg",
                "button_primary_border",
                "button_warning_bg",
                "button_warning_border",
                "button_danger_bg",
                "button_danger_border",
                "button_gradient_top",
                "button_gradient_bottom",
                "button_hover_top",
                "button_hover_bottom",
                "button_primary_gradient_top",
                "button_primary_gradient_bottom",
                "button_warning_gradient_top",
                "button_warning_gradient_bottom",
                "button_danger_gradient_top",
                "button_danger_gradient_bottom",
            ),
        ),
        (
            "Approvals + Risk",
            (
                "risk_high_bg",
                "risk_high_fg",
                "risk_medium_bg",
                "risk_medium_fg",
                "risk_low_bg",
                "risk_low_fg",
                "risk_unknown_bg",
                "risk_unknown_fg",
            ),
        ),
    )

    _QUICK_COLOR_GROUPS = (
        (
            "Core Contrast",
            (
                "panel",
                "text",
                "text_muted",
                "border_soft",
                "toolbar_bg",
            ),
        ),
        (
            "Action Emphasis",
            (
                "accent",
                "button_primary_bg",
                "button_warning_bg",
                "warning",
                "danger",
            ),
        ),
    )

    _QUICK_TOKEN_KEYS = (
        "font_size",
        "font_size_large",
        "border_radius",
        "spacing",
        "input_height",
        "toolbar_height",
        "scrollbar_width",
    )

    class ThemeEditorDialog(QDialog):
        """Full theme editor with a left workbench layout and real preview."""

        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self.setWindowTitle("Theme Editor")
            self.setMinimumSize(1220, 760)
            self.setObjectName("ThemeEditorDialog")

            self._engine: ThemeEngine = get_engine()
            self._updating_controls = False
            self._did_position = False

            self._color_controls: dict[str, ColorPickerButton] = {}
            self._token_controls: dict[str, QWidget] = {}
            self._quick_color_controls: dict[str, ColorPickerButton] = {}
            self._quick_token_controls: dict[str, QWidget] = {}

            self._setup_ui()
            self._sync_from_engine()
            self._engine.theme_changed.connect(self._sync_from_engine)

        def closeEvent(self, event: object) -> None:
            self._engine.set_apply_enabled(True)
            super().closeEvent(event)

        def showEvent(self, event: object) -> None:
            super().showEvent(event)
            if self._did_position:
                return
            parent = self.parentWidget()
            if parent is not None:
                parent_geom = parent.frameGeometry()
                width = max(1080, min(1400, parent_geom.width() - 40))
                height = max(720, min(900, parent_geom.height() - 40))
                self.resize(width, height)
                self.move(parent_geom.left() + 20, parent_geom.top() + 20)
            self._did_position = True

        def _setup_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(12, 12, 12, 12)
            root.setSpacing(12)

            root.addWidget(self._build_toolbar())

            shell = QSplitter(Qt.Orientation.Horizontal)
            shell.setChildrenCollapsible(False)
            shell.addWidget(self._build_editor_workbench())
            shell.addWidget(self._build_upgrade_panel())
            shell.setStretchFactor(0, 5)
            shell.setStretchFactor(1, 3)
            root.addWidget(shell, 1)

        def _build_toolbar(self) -> QWidget:
            bar = QWidget()
            layout = QHBoxLayout(bar)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)

            layout.addWidget(QLabel("Preset"))
            self._preset_combo = QComboBox()
            self._preset_combo.currentTextChanged.connect(self._on_preset_selected)
            layout.addWidget(self._preset_combo, 2)

            self._save_preset_btn = QPushButton("Save Preset")
            self._save_preset_btn.clicked.connect(self._save_preset)
            layout.addWidget(self._save_preset_btn)

            self._delete_preset_btn = QPushButton("Delete Preset")
            self._delete_preset_btn.clicked.connect(self._delete_preset)
            layout.addWidget(self._delete_preset_btn)

            layout.addSpacing(10)

            self._undo_btn = QPushButton("Undo")
            self._undo_btn.clicked.connect(self._undo)
            layout.addWidget(self._undo_btn)

            self._redo_btn = QPushButton("Redo")
            self._redo_btn.clicked.connect(self._redo)
            layout.addWidget(self._redo_btn)

            layout.addSpacing(10)

            self._live_preview = QCheckBox("Live Preview")
            self._live_preview.setChecked(True)
            self._live_preview.toggled.connect(self._toggle_live_preview)
            layout.addWidget(self._live_preview)

            layout.addStretch(1)
            return bar

        def _build_editor_workbench(self) -> QWidget:
            wrapper = QWidget()
            layout = QHBoxLayout(wrapper)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            sidebar = QFrame()
            sidebar.setObjectName("ThemeEditorSidebar")
            sidebar_layout = QVBoxLayout(sidebar)
            sidebar_layout.setContentsMargins(8, 8, 8, 8)
            sidebar_layout.setSpacing(8)

            sidebar_title = QLabel("Editor Pages")
            sidebar_title.setObjectName("SectionHeaderLabel")
            sidebar_layout.addWidget(sidebar_title)

            self._nav_list = QListWidget()
            self._nav_list.setObjectName("ThemeEditorNav")
            sidebar_layout.addWidget(self._nav_list, 1)

            self._page_stack = QStackedWidget()
            pages = (
                ("Guide", self._build_guide_page()),
                ("Surfaces", self._build_surfaces_page()),
                ("Navigation", self._build_navigation_page()),
                ("Workflows", self._build_workflows_page()),
                ("Typography", self._build_typography_page()),
                ("Metrics", self._build_metrics_page()),
                ("Import / Export", self._build_import_export_page()),
            )
            for title, page in pages:
                self._nav_list.addItem(QListWidgetItem(title))
                self._page_stack.addWidget(page)
            self._nav_list.currentRowChanged.connect(self._change_page)
            self._nav_list.setCurrentRow(0)

            layout.addWidget(sidebar)
            layout.addWidget(self._page_stack, 1)
            return wrapper

        def _build_guide_page(self) -> QWidget:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            layout = QVBoxLayout(content)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            intro = QLabel(
                "Use this page to understand what each theme section actually changes before you start editing."
            )
            intro.setObjectName("MutedLabel")
            intro.setWordWrap(True)
            layout.addWidget(intro)

            coverage = self._make_editor_group("Surface Coverage")
            coverage_layout = QVBoxLayout(coverage)
            coverage_text = QLabel(
                "\n".join(
                    [
                        "Backgrounds: window shell, cards, inset panes, and elevated surfaces.",
                        "Text: labels, muted metadata, dim labels, and readable summaries.",
                        "Borders: card outlines, splitters, focus rings, and chrome edges.",
                        "Accent + Alerts: action emphasis, positive state, warning, and destructive signals.",
                        "Buttons + Scrollbar: toolbar buttons, quick actions, and scrollbar handles.",
                        "Workbench: splitter handles, snapped preset controls, and mixed dashboard/report/monitor surfaces.",
                        "Sidebar + Badges: selected nav items, provider badges, and compact chips.",
                        "Risk Badges: approval-risk labels and similar severity surfaces.",
                    ]
                )
            )
            coverage_text.setObjectName("CardDetailLabel")
            coverage_text.setWordWrap(True)
            coverage_layout.addWidget(coverage_text)
            layout.addWidget(coverage)

            semantics = self._make_editor_group("Highlight Semantics")
            semantics_layout = QVBoxLayout(semantics)
            semantics_text = QLabel(
                "Diff colors are semantic. Added diff lines use the active-status green family, "
                "removed diff lines use danger/red, and diff hunks use accent blue. Normal "
                "markdown or bridge prose should stay neutral instead of looking like a failure."
            )
            semantics_text.setObjectName("CardDetailLabel")
            semantics_text.setWordWrap(True)
            semantics_layout.addWidget(semantics_text)
            layout.addWidget(semantics)

            limits = self._make_editor_group("Current Limits")
            limits_layout = QVBoxLayout(limits)
            limits_text = QLabel(
                "The desktop editor already supports shared semantic colors, typography, sizing "
                "tokens, JSON import/export, and QSS color import. It does not yet round-trip "
                "arbitrary per-widget selector trees or full Rust style-pack metadata one-to-one."
            )
            limits_text.setObjectName("CardDetailLabel")
            limits_text.setWordWrap(True)
            limits_layout.addWidget(limits_text)
            layout.addWidget(limits)

            layout.addStretch(1)
            scroll.setWidget(content)
            return scroll

        def _build_color_groups_page(
            self,
            *,
            intro_text: str,
            groups: tuple[tuple[str, tuple[str, ...]], ...],
        ) -> QWidget:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            layout = QVBoxLayout(content)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            intro = QLabel(intro_text)
            intro.setObjectName("MutedLabel")
            intro.setWordWrap(True)
            layout.addWidget(intro)

            for title, keys in groups:
                group = self._make_editor_group(title)
                group_layout = QFormLayout(group)
                for key in keys:
                    btn = self._make_color_control(
                        key,
                        registry=self._color_controls,
                    )
                    group_layout.addRow(QLabel(self._labelize(key)), btn)
                layout.addWidget(group)

            layout.addStretch(1)
            scroll.setWidget(content)
            return scroll

        def _build_surfaces_page(self) -> QWidget:
            return self._build_color_groups_page(
                intro_text=(
                    "Tune the window shell, panel stack, toolbar, and base text/border "
                    "chrome before you move into workflow-specific emphasis."
                ),
                groups=_SURFACE_COLOR_GROUPS,
            )

        def _build_navigation_page(self) -> QWidget:
            return self._build_color_groups_page(
                intro_text=(
                    "Shape how sidebar navigation, tabs, splitters, scrollbar handles, "
                    "badges, and lane-status signals read at a glance."
                ),
                groups=_NAVIGATION_COLOR_GROUPS,
            )

        def _build_workflows_page(self) -> QWidget:
            return self._build_color_groups_page(
                intro_text=(
                    "Focus on action emphasis, approval severity, and workflow-heavy "
                    "surfaces such as launch controls, approval queues, diagnostics, "
                    "and diff-oriented panes."
                ),
                groups=_WORKFLOW_COLOR_GROUPS,
            )

        def _build_typography_page(self) -> QWidget:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            layout = QVBoxLayout(content)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            intro = QLabel(
                "Control text stacks and type scale so the console feels deliberate, not generic."
            )
            intro.setObjectName("MutedLabel")
            intro.setWordWrap(True)
            layout.addWidget(intro)

            for category_name in ("Typography",):
                group = self._make_editor_group(category_name)
                group_layout = QFormLayout(group)
                for key in TOKEN_CATEGORIES[category_name]:
                    spec = TOKEN_SPECS[key]
                    control = self._make_token_control(
                        key,
                        spec,
                        registry=self._token_controls,
                    )
                    group_layout.addRow(QLabel(spec.label), control)
                layout.addWidget(group)

            layout.addStretch(1)
            scroll.setWidget(content)
            return scroll

        def _build_metrics_page(self) -> QWidget:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            layout = QVBoxLayout(content)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            intro = QLabel(
                "Tune spacing, radii, control sizing, and chrome density across the app."
            )
            intro.setObjectName("MutedLabel")
            intro.setWordWrap(True)
            layout.addWidget(intro)

            group = self._make_editor_group("Metrics")
            group_layout = QFormLayout(group)
            for key in TOKEN_CATEGORIES["Metrics"]:
                spec = TOKEN_SPECS[key]
                control = self._make_token_control(
                    key,
                    spec,
                    registry=self._token_controls,
                )
                group_layout.addRow(QLabel(spec.label), control)
            layout.addWidget(group)

            layout.addStretch(1)
            scroll.setWidget(content)
            return scroll

        def _build_import_export_page(self) -> QWidget:
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)
            layout.addWidget(self._build_overlay_import_group())
            layout.addWidget(self._build_overlay_export_group())
            layout.addWidget(self._build_theme_authoring_notes_group())
            layout.addWidget(self._build_file_operations_group())
            layout.addWidget(self._build_json_theme_group())
            layout.addWidget(self._build_qss_import_group())
            layout.addWidget(self._build_qss_preview_group(), 1)

            return widget

        def _build_overlay_import_group(self) -> QWidget:
            overlay_group = self._make_editor_group("VoiceTerm Overlay Import")
            overlay_layout = QVBoxLayout(overlay_group)
            overlay_note = QLabel(
                "Read-path parity imports canonical overlay metadata without inventing a "
                "second desktop schema. Style-pack JSON and theme-file TOML currently "
                "hydrate only the Rust `base_theme`; Rust-only overrides stay listed as "
                "not yet mapped until a documented cross-surface contract exists."
            )
            overlay_note.setObjectName("MutedLabel")
            overlay_note.setWordWrap(True)
            overlay_layout.addWidget(overlay_note)
            overlay_layout.addLayout(self._build_overlay_import_buttons())

            self._overlay_paste = QPlainTextEdit()
            self._overlay_paste.setPlaceholderText(
                '{\n'
                '  "version": 4,\n'
                '  "profile": "ops",\n'
                '  "base_theme": "codex"\n'
                "}\n\n"
                "[meta]\n"
                'name = "Night Ops"\n'
                'base_theme = "claude"\n'
            )
            self._overlay_paste.setMaximumHeight(180)
            overlay_layout.addWidget(self._overlay_paste)

            self._overlay_import_status = QLabel("No overlay metadata imported yet.")
            self._overlay_import_status.setObjectName("CardDetailLabel")
            self._overlay_import_status.setWordWrap(True)
            overlay_layout.addWidget(self._overlay_import_status)
            return overlay_group

        def _build_overlay_import_buttons(self) -> QHBoxLayout:
            overlay_buttons = QHBoxLayout()
            overlay_file_btn = QPushButton("Import Overlay File")
            overlay_file_btn.clicked.connect(self._import_overlay_file)
            overlay_buttons.addWidget(overlay_file_btn)

            overlay_apply_btn = QPushButton("Apply Overlay Metadata")
            overlay_apply_btn.clicked.connect(self._apply_overlay_text)
            overlay_buttons.addWidget(overlay_apply_btn)
            overlay_buttons.addStretch(1)
            return overlay_buttons

        def _build_overlay_export_group(self) -> QWidget:
            overlay_export_group = self._make_editor_group("VoiceTerm Overlay Export")
            overlay_export_layout = QVBoxLayout(overlay_export_group)
            overlay_export_note = QLabel(
                "Write-path parity stays intentionally narrow. The desktop editor only "
                "exports canonical overlay metadata when the current state still maps "
                "exactly to a shared builtin base theme; desktop-only edits remain "
                "blocked until the broader field contract is proven round-trip-safe."
            )
            overlay_export_note.setObjectName("MutedLabel")
            overlay_export_note.setWordWrap(True)
            overlay_export_layout.addWidget(overlay_export_note)
            overlay_export_layout.addLayout(self._build_overlay_export_buttons())

            self._overlay_export_status = QLabel("")
            self._overlay_export_status.setObjectName("CardDetailLabel")
            self._overlay_export_status.setWordWrap(True)
            overlay_export_layout.addWidget(self._overlay_export_status)

            self._overlay_export_preview = QPlainTextEdit()
            self._overlay_export_preview.setReadOnly(True)
            self._overlay_export_preview.setMaximumHeight(140)
            overlay_export_layout.addWidget(self._overlay_export_preview)
            return overlay_export_group

        def _build_overlay_export_buttons(self) -> QHBoxLayout:
            overlay_export_buttons = QHBoxLayout()
            overlay_theme_file_btn = QPushButton("Export Theme File")
            overlay_theme_file_btn.clicked.connect(self._export_overlay_theme_file)
            overlay_export_buttons.addWidget(overlay_theme_file_btn)

            overlay_style_pack_btn = QPushButton("Export Style-Pack JSON")
            overlay_style_pack_btn.clicked.connect(self._export_overlay_style_pack)
            overlay_export_buttons.addWidget(overlay_style_pack_btn)
            overlay_export_buttons.addStretch(1)
            return overlay_export_buttons

        def _build_theme_authoring_notes_group(self) -> QWidget:
            notes = self._make_editor_group("Theme Authoring Notes")
            notes_layout = QVBoxLayout(notes)
            notes_text = QLabel(
                "Import/read parity comes first. JSON themes round-trip the shared semantic "
                "theme contract; pasted QSS currently maps colors onto that same contract "
                "instead of preserving arbitrary per-widget selector trees. Diff colors are "
                "semantic too: red/green only belong to real unified diffs, while normal "
                "markdown and status prose should stay neutral."
            )
            notes_text.setObjectName("MutedLabel")
            notes_text.setWordWrap(True)
            notes_layout.addWidget(notes_text)
            return notes

        def _build_file_operations_group(self) -> QWidget:
            file_group = self._make_editor_group("File Operations")
            file_layout = QHBoxLayout(file_group)

            import_btn = QPushButton("Import JSON File")
            import_btn.clicked.connect(self._import_json_file)
            file_layout.addWidget(import_btn)

            export_btn = QPushButton("Export JSON File")
            export_btn.clicked.connect(self._export_json_file)
            file_layout.addWidget(export_btn)

            export_qss_btn = QPushButton("Export QSS File")
            export_qss_btn.clicked.connect(self._export_qss_file)
            file_layout.addWidget(export_qss_btn)

            file_layout.addStretch(1)
            return file_group

        def _build_json_theme_group(self) -> QWidget:
            json_group = self._make_editor_group("Paste JSON Theme")
            json_layout = QVBoxLayout(json_group)
            self._json_paste = QPlainTextEdit()
            self._json_paste.setPlaceholderText(
                '{\n'
                '  "name": "My Theme",\n'
                '  "colors": { "accent": "#5cb8ff" },\n'
                '  "tokens": { "font_size": 15, "border_radius": 10 }\n'
                '}'
            )
            self._json_paste.setMaximumHeight(180)
            json_layout.addWidget(self._json_paste)
            json_layout.addLayout(self._build_json_theme_buttons())
            return json_group

        def _build_json_theme_buttons(self) -> QHBoxLayout:
            json_buttons = QHBoxLayout()
            apply_json = QPushButton("Apply JSON")
            apply_json.clicked.connect(self._apply_pasted_json)
            json_buttons.addWidget(apply_json)
            clear_json = QPushButton("Clear")
            clear_json.clicked.connect(self._json_paste.clear)
            json_buttons.addWidget(clear_json)
            json_buttons.addStretch(1)
            return json_buttons

        def _build_qss_import_group(self) -> QWidget:
            qss_group = self._make_editor_group("Paste QSS Stylesheet")
            qss_layout = QVBoxLayout(qss_group)
            self._qss_paste = QPlainTextEdit()
            self._qss_paste.setPlaceholderText(
                "Paste a QSS stylesheet to import its colors onto the current token set."
            )
            self._qss_paste.setMaximumHeight(180)
            qss_layout.addWidget(self._qss_paste)
            qss_layout.addLayout(self._build_qss_import_buttons())
            return qss_group

        def _build_qss_import_buttons(self) -> QHBoxLayout:
            qss_buttons = QHBoxLayout()
            apply_qss = QPushButton("Import QSS")
            apply_qss.clicked.connect(self._apply_pasted_qss)
            qss_buttons.addWidget(apply_qss)
            save_qss = QPushButton("Import && Save as Preset")
            save_qss.clicked.connect(self._save_qss_as_preset)
            qss_buttons.addWidget(save_qss)
            clear_qss = QPushButton("Clear")
            clear_qss.clicked.connect(self._qss_paste.clear)
            qss_buttons.addWidget(clear_qss)
            qss_buttons.addStretch(1)
            return qss_buttons

        def _build_qss_preview_group(self) -> QWidget:
            preview_group = self._make_editor_group("Generated QSS Preview")
            preview_layout = QVBoxLayout(preview_group)
            self._qss_preview = QPlainTextEdit()
            self._qss_preview.setReadOnly(True)
            preview_layout.addWidget(self._qss_preview)
            return preview_group

        def _build_upgrade_panel(self) -> QWidget:
            wrapper = QWidget()
            layout = QVBoxLayout(wrapper)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)

            title = QLabel("Theme Upgrades")
            title.setObjectName("SectionHeaderLabel")
            subtitle = QLabel(
                "Use this rail for high-signal tuning and coverage notes. Preview is still available, but it is optional when the live app window is already visible."
            )
            subtitle.setObjectName("MutedLabel")
            subtitle.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(subtitle)

            self._side_panel_tabs = QTabWidget()
            self._side_panel_tabs.setObjectName("MonitorTabs")
            self._side_panel_tabs.setDocumentMode(True)
            self._side_panel_tabs.tabBar().setObjectName("MonitorTabBar")
            self._side_panel_tabs.tabBar().setExpanding(False)
            self._side_panel_tabs.addTab(self._build_quick_tune_page(), "Quick Tune")
            self._side_panel_tabs.addTab(self._build_coverage_page(), "Coverage")
            self._side_panel_tabs.addTab(self._build_preview_panel(), "Preview")
            self._side_panel_tabs.setCurrentIndex(0)
            layout.addWidget(self._side_panel_tabs, 1)
            return wrapper

        def _build_quick_tune_page(self) -> QWidget:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            layout = QVBoxLayout(content)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            intro = QLabel(
                "Fast controls for the theme knobs you are most likely to push while comparing the editor against the live app."
            )
            intro.setObjectName("MutedLabel")
            intro.setWordWrap(True)
            layout.addWidget(intro)

            identity_group = self._make_editor_group("Current Theme")
            identity_layout = QVBoxLayout(identity_group)
            self._selection_summary_label = QLabel("")
            self._selection_summary_label.setObjectName("CardStatusLabel")
            self._selection_summary_label.setWordWrap(True)
            identity_layout.addWidget(self._selection_summary_label)
            self._selection_detail_label = QLabel(
                "Live Preview applies directly to the app window. Use Preview only when you need synthetic coverage that is not open elsewhere."
            )
            self._selection_detail_label.setObjectName("CardDetailLabel")
            self._selection_detail_label.setWordWrap(True)
            identity_layout.addWidget(self._selection_detail_label)
            layout.addWidget(identity_group)

            for title, keys in _QUICK_COLOR_GROUPS:
                group = self._make_editor_group(title)
                group_layout = QFormLayout(group)
                for key in keys:
                    btn = self._make_color_control(
                        key,
                        registry=self._quick_color_controls,
                    )
                    group_layout.addRow(QLabel(self._labelize(key)), btn)
                layout.addWidget(group)

            density_group = self._make_editor_group("Scale + Density")
            density_layout = QFormLayout(density_group)
            for key in _QUICK_TOKEN_KEYS:
                spec = TOKEN_SPECS[key]
                control = self._make_token_control(
                    key,
                    spec,
                    registry=self._quick_token_controls,
                )
                density_layout.addRow(QLabel(spec.label), control)
            layout.addWidget(density_group)

            layout.addStretch(1)
            scroll.setWidget(content)
            return scroll

        def _build_coverage_page(self) -> QWidget:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            layout = QVBoxLayout(content)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            editable = self._make_editor_group("Editable Now")
            editable_layout = QVBoxLayout(editable)
            editable_text = QLabel(
                "Colors: panels, text, tabs, buttons, risk badges, splitters, scrollbars, and status surfaces.\n"
                "Tokens: fonts, size scale, radii, spacing, toolbar height, input height, and scrollbar width.\n"
                "Import / Export: JSON, QSS color import, canonical overlay metadata read/write within the current parity limits."
            )
            editable_text.setObjectName("CardDetailLabel")
            editable_text.setWordWrap(True)
            editable_layout.addWidget(editable_text)
            layout.addWidget(editable)

            pending = self._make_editor_group("Not Wired Yet")
            pending_layout = QVBoxLayout(pending)
            pending_text = QLabel(
                "Animation and motion controls are not wired into the Operator Console theme contract yet, so the editor does not expose fake timing/easing knobs. When motion lands, it should arrive here as real tokens with live preview and round-trip support."
            )
            pending_text.setObjectName("CardDetailLabel")
            pending_text.setWordWrap(True)
            pending_layout.addWidget(pending_text)
            layout.addWidget(pending)

            workflow = self._make_editor_group("How To Use This")
            workflow_layout = QVBoxLayout(workflow)
            workflow_text = QLabel(
                "Quick Tune is for the high-signal adjustments you make repeatedly. The left editor pages stay the authority for full-surface editing. Preview is secondary when the live Operator Console window is already open on another display."
            )
            workflow_text.setObjectName("CardDetailLabel")
            workflow_text.setWordWrap(True)
            workflow_layout.addWidget(workflow_text)
            layout.addWidget(workflow)

            layout.addStretch(1)
            scroll.setWidget(content)
            return scroll

        def _build_preview_panel(self) -> QWidget:
            wrapper = QWidget()
            layout = QVBoxLayout(wrapper)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)

            subtitle = QLabel(
                "Synthetic preview surfaces for components that may not currently be visible in the live app."
            )
            subtitle.setObjectName("MutedLabel")
            subtitle.setWordWrap(True)
            layout.addWidget(subtitle)

            self._preview = ThemePreview()
            layout.addWidget(self._preview, 1)
            return wrapper

        def _make_editor_group(self, title: str) -> QGroupBox:
            group = QGroupBox(title)
            group.setProperty("editorSection", True)
            return group

        def _make_color_control(
            self,
            key: str,
            *,
            registry: dict[str, ColorPickerButton],
        ) -> ColorPickerButton:
            button = ColorPickerButton()
            button.color_changed.connect(
                lambda value, name=key: self._on_color_changed(name, value)
            )
            registry[key] = button
            return button

        def _make_token_control(
            self,
            key: str,
            spec: object,
            *,
            registry: dict[str, QWidget],
        ) -> QWidget:
            if getattr(spec, "value_type") == "int":
                spin = QSpinBox()
                spin.setRange(getattr(spec, "minimum") or 0, getattr(spec, "maximum") or 999)
                spin.setSingleStep(getattr(spec, "step") or 1)
                spin.valueChanged.connect(lambda value, name=key: self._on_token_changed(name, value))
                registry[key] = spin
                return spin

            line = QLineEdit()
            line.textChanged.connect(lambda value, name=key: self._on_token_changed(name, value))
            registry[key] = line
            return line

        def _labelize(self, name: str) -> str:
            return name.replace("_", " ").title()

        def _change_page(self, index: int) -> None:
            if index < 0:
                return
            self._page_stack.setCurrentIndex(index)

        def _toggle_live_preview(self, enabled: bool) -> None:
            self._engine.set_apply_enabled(enabled)
            if enabled:
                self._preview.setStyleSheet("")
            else:
                self._preview.setStyleSheet(self._engine.generate_stylesheet())

        def _on_preset_selected(self, name: str) -> None:
            if self._updating_controls:
                return
            self._engine.apply_theme(name, save=True)
            self._engine.save_current()
            self._refresh_preset_combo()

        def _on_color_changed(self, name: str, value: str) -> None:
            if self._updating_controls:
                return
            self._engine.set_color(name, value)
            self._engine.save_current()

        def _on_token_changed(self, name: str, value: int | str) -> None:
            if self._updating_controls:
                return
            self._engine.set_token(name, value)
            self._engine.save_current()

        def _save_preset(self) -> None:
            name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:")
            if not ok or not name.strip():
                return
            self._engine.save_custom_preset(name.strip())
            self._refresh_preset_combo()

        def _delete_preset(self) -> None:
            name = self._preset_combo.currentText()
            if not name:
                return
            if not self._engine.delete_custom_preset(name):
                QMessageBox.information(
                    self,
                    "Cannot Delete",
                    "Built-in presets cannot be deleted.",
                )
                return
            self._refresh_preset_combo()

        def _undo(self) -> None:
            if self._engine.undo():
                self._engine.save_current()

        def _redo(self) -> None:
            if self._engine.redo():
                self._engine.save_current()

        def _import_json_file(self) -> None:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Import Theme",
                "",
                "JSON Files (*.json);;All Files (*.*)",
            )
            if not filename:
                return
            if not self._engine.import_from_file(filename):
                QMessageBox.warning(self, "Import Failed", "Could not load theme JSON.")
                return
            self._engine.save_current()
            self._refresh_preset_combo()

        def _export_json_file(self) -> None:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Theme (JSON)",
                "",
                "JSON Files (*.json);;All Files (*.*)",
            )
            if not filename:
                return
            self._engine.export_to_file(filename)

        def _export_qss_file(self) -> None:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Theme (QSS)",
                "",
                "Qt Stylesheets (*.qss);;All Files (*.*)",
            )
            if not filename:
                return
            Path(filename).write_text(self._engine.generate_stylesheet(), encoding="utf-8")

        def _export_overlay_theme_file(self) -> None:
            content = self._engine.export_overlay_theme_file()
            if content is None:
                QMessageBox.information(
                    self,
                    "Export Unavailable",
                    self._engine.overlay_export_status(),
                )
                return
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export VoiceTerm Theme File",
                self._engine.suggested_overlay_theme_file_name(),
                "TOML Files (*.toml);;All Files (*.*)",
            )
            if not filename:
                return
            Path(filename).write_text(content, encoding="utf-8")

        def _export_overlay_style_pack(self) -> None:
            content = self._engine.export_overlay_style_pack_json()
            if content is None:
                QMessageBox.information(
                    self,
                    "Export Unavailable",
                    self._engine.overlay_export_status(),
                )
                return
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export VoiceTerm Style-Pack JSON",
                self._engine.suggested_overlay_style_pack_file_name(),
                "JSON Files (*.json);;All Files (*.*)",
            )
            if not filename:
                return
            Path(filename).write_text(content, encoding="utf-8")

        def _apply_pasted_json(self) -> None:
            text = self._json_paste.toPlainText().strip()
            if not text:
                QMessageBox.warning(self, "Empty Input", "Please paste a JSON theme first.")
                return
            if not self._engine.import_from_json(text):
                QMessageBox.warning(
                    self,
                    "Invalid JSON",
                    "Could not parse the JSON theme.\n\nMake sure it includes a 'colors' section.",
                )
                return
            self._engine.save_current()
            self._refresh_preset_combo()

        def _apply_pasted_qss(self) -> None:
            text = self._qss_paste.toPlainText().strip()
            if not text:
                QMessageBox.warning(
                    self,
                    "Empty Input",
                    "Please paste a QSS stylesheet first.",
                )
                return
            if not self._engine.import_from_qss(text):
                QMessageBox.warning(
                    self,
                    "Parse Failed",
                    "Could not parse the QSS stylesheet.",
                )
                return
            self._engine.save_current()
            self._refresh_preset_combo()

        def _save_qss_as_preset(self) -> None:
            text = self._qss_paste.toPlainText().strip()
            if not text:
                QMessageBox.warning(
                    self,
                    "Empty Input",
                    "Please paste a QSS stylesheet first.",
                )
                return
            name, ok = QInputDialog.getText(self, "Save QSS as Preset", "Preset name:")
            if not ok or not name.strip():
                return
            if not self._engine.import_from_qss(text, name.strip()):
                QMessageBox.warning(
                    self,
                    "Parse Failed",
                    "Could not parse the QSS stylesheet.",
                )
                return
            self._engine.save_custom_preset(name.strip())
            self._engine.save_current()
            self._refresh_preset_combo()

        def _import_overlay_file(self) -> None:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Import VoiceTerm Overlay Metadata",
                "",
                "Overlay Metadata (*.json *.toml);;JSON Files (*.json);;TOML Files (*.toml);;All Files (*.*)",
            )
            if not filename:
                return
            if not self._engine.import_from_overlay_file(filename):
                QMessageBox.warning(
                    self,
                    "Import Failed",
                    "Could not parse overlay metadata.\n\n"
                    "Accepted read-path inputs are canonical style-pack JSON and "
                    "theme-file TOML metadata with a valid base_theme.",
                )
                return
            self._engine.save_current()
            self._refresh_preset_combo()

        def _apply_overlay_text(self) -> None:
            text = self._overlay_paste.toPlainText().strip()
            if not text:
                QMessageBox.warning(
                    self,
                    "Empty Input",
                    "Please paste overlay metadata first.",
                )
                return
            if not self._engine.import_from_overlay_text(text):
                QMessageBox.warning(
                    self,
                    "Parse Failed",
                    "Could not parse overlay metadata.\n\n"
                    "Accepted read-path inputs are canonical style-pack JSON and "
                    "theme-file TOML metadata with a valid base_theme.",
                )
                return
            self._engine.save_current()
            self._refresh_preset_combo()

        def _refresh_preset_combo(self) -> None:
            current = self._engine.current_theme
            presets = self._engine.get_preset_names()
            self._preset_combo.blockSignals(True)
            self._preset_combo.clear()
            self._preset_combo.addItems(presets)
            if current in presets:
                self._preset_combo.setCurrentText(current)
            self._preset_combo.blockSignals(False)
            self._delete_preset_btn.setEnabled(current not in BUILTIN_PRESETS)

        def _sync_from_engine(self) -> None:
            self._updating_controls = True
            try:
                state = self._engine.get_state()
                foreground_color = state.colors.get(
                    "text",
                    BUILTIN_PRESETS["Codex"].colors["text"],
                )
                background_color = state.colors.get(
                    "bg_top",
                    BUILTIN_PRESETS["Codex"].colors["bg_top"],
                )
                for registry in (self._color_controls, self._quick_color_controls):
                    for name, button in registry.items():
                        button.set_reference_colors(
                            foreground_color=foreground_color,
                            background_color=background_color,
                        )
                        button.color = state.colors.get(
                            name,
                            BUILTIN_PRESETS["Codex"].colors.get(
                                name,
                                BUILTIN_PRESETS["Codex"].colors["accent"],
                            ),
                        )
                for registry in (self._token_controls, self._quick_token_controls):
                    for name, control in registry.items():
                        value = state.tokens.get(name, "")
                        if isinstance(control, QSpinBox):
                            control.blockSignals(True)
                            control.setValue(int(value))
                            control.blockSignals(False)
                        elif isinstance(control, QLineEdit):
                            control.blockSignals(True)
                            control.setText(value)
                            control.blockSignals(False)

                self._refresh_preset_combo()
                self._qss_preview.setPlainText(self._engine.generate_stylesheet())
                self._undo_btn.setEnabled(self._engine.can_undo())
                self._redo_btn.setEnabled(self._engine.can_redo())
                self._preview.set_preview_theme(state.colors)
                active_selection = self._engine.get_active_selection()
                self._selection_summary_label.setText(
                    f"{active_selection.display_name} theme ({active_selection.kind})"
                )
                self._overlay_import_status.setText(
                    self._engine.last_overlay_import_summary()
                    or "No overlay metadata imported yet."
                )
                self._overlay_export_status.setText(self._engine.overlay_export_status())
                self._overlay_export_preview.setPlainText(
                    self._engine.overlay_theme_file_preview()
                )

                if not self._live_preview.isChecked():
                    self._preview.setStyleSheet(self._engine.generate_stylesheet())
                else:
                    self._preview.setStyleSheet("")
            finally:
                self._updating_controls = False

else:

    class ThemeEditorDialog:  # type: ignore[no-redef]
        """Stub when PyQt6 is not installed."""

        pass
