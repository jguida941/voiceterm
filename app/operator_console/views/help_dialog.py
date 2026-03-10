"""In-app help and developer guidance for the Operator Console."""

from __future__ import annotations

from ..theme import available_theme_ids
from .layout.ui_layouts import available_layout_ids, resolve_layout

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QPushButton,
        QTabWidget,
        QTextBrowser,
        QVBoxLayout,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False


def _overview_markdown() -> str:
    return """# Quick Start

This dialog is the plain-language guide.

- **Codex** is the reviewer lane.
- **Claude** is the implementer lane.
- **Operator** is the human control lane.
- **Bridge** shows the wrapped markdown bridge snapshot.
- **Launcher Output** shows typed command output.
- **Diagnostics** shows high-level app events and warnings.

## Read The Colors

- Status dots show lane health, not blame.
- Red and green diff colors only appear when the raw text is an actual unified diff.
- Normal markdown bullets should stay neutral text now.

## What The Sidebar \"Square\" Was

The square at the lower-left of some raw panes was the horizontal scrollbar
handle. Wrapped bridge text is now used for the common human-reading path so
it does not look like a mystery button.

## Current Limits

- Rust still owns PTY/runtime/session behavior.
- `devctl` still owns launch, rollover, CI, triage, and process actions.
- The desktop app is a repo-aware control shell, not a second control plane.
"""


def _controls_markdown() -> str:
    layout_rows = "\n".join(
        f"- **{resolve_layout(layout_id).display_name}**: {resolve_layout(layout_id).description}"
        for layout_id in available_layout_ids()
    )
    return f"""# Controls

## Toolbar

- **Refresh** reloads the latest repo-visible snapshot immediately.
- **Dry** runs the shared review-channel launcher in dry-run mode.
- **Live** launches the real review-channel flow through the shared command path.
- **Roll** requests a guarded rollover through the same typed command path.
- **Read** switches between simple and technical wording for summaries and footer text.
- **Theme** switches the active desktop palette.
- **Layout** changes how the same persistent panes are arranged.
- **Thr%** is the rollover threshold percentage.
- **ACK** is the wait window for acknowledgements during rollover.

## Layout Modes

{layout_rows}

## Workbench

- **Workbench** is the resize-first surface. It keeps the three main lanes on top and the guided home, reports, and monitor surfaces below.
- Use the preset buttons to snap back to known-good ratios after dragging splitters around.

## Detail Buttons

Use the `...` button on a lane card when you need structured details plus raw
text for just that one lane.

## Start Surface

The `Home` screen is the guided entry surface. Use it when you want the app to
explain the current state before you drop into raw monitors.
"""


def _theme_markdown() -> str:
    theme_list = ", ".join(available_theme_ids())
    return f"""# Theme System

## What The Theme Editor Edits Today

- Semantic colors used across toolbar, cards, nav, scrollbars, badges, and dialogs.
- Shared typography and sizing tokens such as font sizes, radii, padding, and scrollbar width.
- Component style families for borders, buttons, toolbar actions, inputs, and tabs.
- Motion settings for previewable fades and pulse feedback in the editor playground.
- Imported JSON themes and pasted QSS color mappings.

## What QSS Import Does Not Do Yet

- It does **not** round-trip arbitrary per-widget selector trees.
- It maps imported colors onto the current shared semantic theme contract.
- Full VoiceTerm style-pack parity is still an active roadmap item.
- Motion settings are previewable in the editor today, but not every live Operator Console surface consumes them yet.

## Why The Highlight Colors Matter

Diff colors are semantic:

- green = added lines in a real diff
- red = removed lines in a real diff
- blue = diff hunks
- neutral text = normal markdown, status notes, or prose

## Built-In Theme IDs

{theme_list}
"""


def _mobile_markdown() -> str:
    return """# Mobile Relay

## What Exists Today

- The repo now has a first-party merged mobile read surface: `devctl mobile-status`.
- `mobile-status` combines autonomy `phone-status` with review-channel state and emits `dev/reports/mobile/latest/{full,compact,actions}.json`.
- The Operator Console now prefers that emitted bundle first, then falls back to rebuilding the merged view when the bundle is absent.

## How `code-link-ide` Fits

- `integrations/code-link-ide` is a federated reference repo.
- Use it for transport, pairing, audit-log, and client-pattern ideas.
- Do **not** wire the desktop app directly to submodule runtime code.

## Practical Direction

- Read path first: desktop + phone should agree on the same emitted `mobile-status` bundle, with `phone-status` still available as the raw controller fallback.
- Push path second: add `ntfy` or another notifier on top of that same payload.
- Guarded actions still need to stay on the typed `controller-action` / `devctl` path.
"""


def _developer_markdown() -> str:
    return """# Developer Model

This tab is the technical version of how the app runs.

## Ownership

- Rust owns PTY/runtime/session behavior.
- `devctl` owns command policy and the typed review-channel control surface.
- PyQt owns presentation, bounded workflow controls, and repo-visible operator decisions.

## Read Paths

- `code_audit.md`
- `review_state.json` when present
- `dev/reports/autonomy/queue/phone/latest.json` for iPhone-safe controller state
- repo-visible operator decision artifacts
- repo-visible diagnostics logs when `--dev-log` is enabled

## Refresh And Execution

- The window refreshes from snapshot state on a 2-second timer.
- Commands still route through the shared command builder and repo-owned scripts.
- The GUI should explain actions, not bypass them.

## Why There Are Help And Developer Menus

The app is expected to teach the workflow in-place. Operators should not need
to jump out to repo docs just to understand the visible surfaces or color
semantics.
"""


if _PYQT_AVAILABLE:

    class OperatorHelpDialog(QDialog):
        """Non-modal in-app guidance surface for operators and developers."""

        _TOPICS = (
            ("overview", "Overview", _overview_markdown),
            ("controls", "Controls", _controls_markdown),
            ("theme", "Theme", _theme_markdown),
            ("mobile", "Mobile", _mobile_markdown),
            ("developer", "Developer", _developer_markdown),
        )

        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("OperatorHelpDialog")
            self.setWindowTitle("Operator Console Guide")
            self.setMinimumSize(900, 620)
            self._topic_indexes: dict[str, int] = {}

            root = QVBoxLayout(self)
            root.setContentsMargins(14, 14, 14, 14)
            root.setSpacing(10)

            self._tabs = QTabWidget()
            self._tabs.setObjectName("HelpTabs")
            self._tabs.setDocumentMode(True)
            self._tabs.tabBar().setObjectName("MonitorTabBar")

            for index, (topic_id, label, render) in enumerate(self._TOPICS):
                browser = QTextBrowser()
                browser.setObjectName("HelpBrowser")
                browser.setReadOnly(True)
                browser.setOpenExternalLinks(False)
                browser.setMarkdown(render())
                self._tabs.addTab(browser, label)
                self._tabs.tabBar().setTabToolTip(
                    index,
                    f"{label} guidance for the Operator Console.",
                )
                self._topic_indexes[topic_id] = index

            root.addWidget(self._tabs, stretch=1)

            buttons = QHBoxLayout()
            buttons.addStretch(1)
            close_button = QPushButton("Close")
            close_button.setObjectName("SmallActionButton")
            close_button.clicked.connect(self.accept)
            buttons.addWidget(close_button)
            root.addLayout(buttons)

        def show_topic(self, topic_id: str) -> None:
            index = self._topic_indexes.get(topic_id, 0)
            self._tabs.setCurrentIndex(index)

else:

    class OperatorHelpDialog:  # type: ignore[no-redef]
        """Stub when PyQt6 is unavailable."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def show_topic(self, topic_id: str) -> None:
            pass
