"""Control QSS: buttons, inputs, combos, spinboxes, scrollbars."""

from __future__ import annotations


def qss_controls(color: dict[str, str], token: dict[str, str]) -> str:
    return (
        _button_rules(color, token)
        + _field_rules(color, token)
        + _combo_rules(color, token)
        + _scrollbar_rules(color, token)
    )


def _button_rules(color: dict[str, str], token: dict[str, str]) -> str:
    return f"""
    /* ── Default Button (flatter editor-style chrome) ───────── */

    QPushButton {{
        background: {color["panel_surface"]};
        color: {color["text_muted"]};
        border: {token["border_width"]}px solid {color["border_soft"]};
        border-radius: {token["border_radius"]}px;
        padding: {token["padding_small"]}px {token["padding_large"]}px;
        font-weight: 600;
        font-size: {token["font_size_small"]}px;
        min-width: {token["button_min_width"]}px;
        min-height: 26px;
    }}

    QPushButton:hover {{
        background: {color["panel_inset"]};
        color: {color["text"]};
        border-color: {color["accent"]};
    }}

    QPushButton:pressed {{
        background: {color["panel_surface_alt"]};
        color: {color["text"]};
        border-color: {color["accent"]};
    }}

    /* ── Small Action Button (toolbar icons) ────────────────── */

    QPushButton#SmallActionButton {{
        color: {color["text"]};
        background: {color["panel_inset"]};
        border-color: {color["input_border"]};
        padding: {token["padding_small"]}px {token["padding"]}px;
        font-size: {token["font_size_small"]}px;
        border-radius: {token["border_radius_small"]}px;
        min-height: 0px;
        min-width: 0px;
        font-weight: 700;
    }}

    QPushButton#SmallActionButton:hover {{
        background: {color["panel_surface_alt"]};
        border-color: {color["card_hover_border"]};
        color: {color["text"]};
    }}

    QPushButton#SmallActionButton:pressed {{
        background: {color["panel_surface"]};
        border-color: {color["accent"]};
    }}

    QPushButton#SmallActionButton:checked {{
        color: {color["text"]};
        background: {color["button_primary_bg"]};
        border-color: {color["accent"]};
    }}

    QPushButton#SmallActionButton[accentRole="primary"] {{
        background: {color["panel_surface_alt"]};
        border-color: {color["accent"]};
        color: {color["text"]};
    }}

    QPushButton#SmallActionButton[accentRole="warning"] {{
        background: {color["panel_surface_alt"]};
        border-color: {color["warning"]};
        color: {color["text"]};
    }}

    QPushButton#SmallActionButton[accentRole="danger"] {{
        background: {color["panel_surface_alt"]};
        border-color: {color["danger"]};
        color: {color["text"]};
    }}

    /* ── Primary Accent (filled, prominent) ─────────────────── */

    QPushButton[accentRole="primary"] {{
        color: {color["text"]};
        background: {color["button_primary_bg"]};
        border-color: {color["accent"]};
        font-weight: 700;
    }}

    QPushButton[accentRole="primary"]:hover {{
        background: {color["button_primary_gradient_top"]};
        border-color: {color["accent"]};
        color: {color["text"]};
    }}

    QPushButton[accentRole="primary"]:pressed {{
        background: {color["button_primary_bg"]};
        border-color: {color["accent"]};
    }}

    /* ── Warning Accent ─────────────────────────────────────── */

    QPushButton[accentRole="warning"] {{
        color: {color["text"]};
        background: {color["button_warning_bg"]};
        border-color: {color["warning"]};
        font-weight: 700;
    }}

    QPushButton[accentRole="warning"]:hover {{
        background: {color["button_warning_gradient_top"]};
        border-color: {color["warning"]};
        color: {color["text"]};
    }}

    QPushButton[accentRole="warning"]:pressed {{
        background: {color["button_warning_bg"]};
        border-color: {color["warning"]};
    }}

    /* ── Danger Accent ──────────────────────────────────────── */

    QPushButton[accentRole="danger"] {{
        color: {color["text"]};
        background: {color["button_danger_bg"]};
        border-color: {color["danger"]};
        font-weight: 700;
    }}

    QPushButton[accentRole="danger"]:hover {{
        background: {color["button_danger_gradient_top"]};
        border-color: {color["danger"]};
        color: {color["text"]};
    }}

    QPushButton[accentRole="danger"]:pressed {{
        background: {color["button_danger_bg"]};
        border-color: {color["danger"]};
    }}

    /* ── Disabled State ─────────────────────────────────────── */

    QPushButton:disabled {{
        color: {color["text_dim"]};
        border-color: {color["input_border"]};
        background: {color["panel_inset"]};
    }}

    /* ── Small Toggle Button ────────────────────────────────── */

    QPushButton#SmallToggleButton {{
        font-size: {token["font_size_small"]}px;
        padding: {token["padding_small"]}px {token["padding"]}px;
        border-radius: {token["border_radius_small"]}px;
        min-height: 0px;
        color: {color["text_dim"]};
        background: {color["panel_surface"]};
        border: {token["border_width"]}px solid {color["border_soft"]};
    }}

    QPushButton#SmallToggleButton:hover {{
        color: {color["text"]};
        border-color: {color["accent"]};
        background: {color["panel_inset"]};
    }}
    """


def _field_rules(color: dict[str, str], token: dict[str, str]) -> str:
    return f"""

    QLineEdit,
    QSpinBox,
    QComboBox,
    QListWidget,
    QPlainTextEdit,
    QTextBrowser {{
        background: {color["panel_inset"]};
        color: {color["text"]};
        border: {token["border_width"]}px solid {color["border_soft"]};
        border-radius: {token["border_radius"]}px;
        padding: {token["padding_small"]}px {token["padding"]}px;
        font-size: {token["font_size"]}px;
        min-height: {token["input_height"]}px;
        selection-background-color: {color["selection_bg"]};
        selection-color: {color["selection_text"]};
    }}

    QPlainTextEdit,
    QTextBrowser,
    QListWidget {{
        font-family: {token["font_family_mono"]};
        font-size: {token["font_size"]}px;
    }}

    QLineEdit:focus,
    QSpinBox:focus,
    QComboBox:focus,
    QListWidget:focus,
    QPlainTextEdit:focus,
    QTextBrowser:focus {{
        border: {token["border_width_focus"]}px solid {color["accent"]};
    }}

    QListWidget::item {{
        border-radius: {token["border_radius"]}px;
        padding: {token["padding"]}px;
    }}

    QListWidget::item:selected {{
        background: {color["selection_bg"]};
        color: {color["text"]};
    }}
    """


def _combo_rules(color: dict[str, str], token: dict[str, str]) -> str:
    return f"""

    QComboBox::drop-down,
    QSpinBox::up-button,
    QSpinBox::down-button {{
        border: none;
        background: transparent;
        width: 18px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {color["text_muted"]};
        margin-right: 6px;
    }}

    QComboBox QAbstractItemView {{
        background: {color["panel_surface"]};
        color: {color["text"]};
        border: {token["border_width"]}px solid {color["border_soft"]};
        border-radius: {token["border_radius"]}px;
        padding: {token["padding_small"]}px;
        selection-background-color: {color["selection_bg"]};
        selection-color: {color["selection_text"]};
        outline: none;
    }}

    QComboBox QAbstractItemView::item {{
        padding: {token["padding_small"]}px {token["padding"]}px;
        min-height: {token["input_height"]}px;
        border-radius: {token["border_radius_small"]}px;
    }}

    QComboBox QAbstractItemView::item:selected {{
        background: {color["selection_bg"]};
        color: {color["text"]};
    }}

    QComboBox QAbstractItemView::item:hover {{
        background: {color["hover_overlay"]};
    }}
    """


def _scrollbar_rules(color: dict[str, str], token: dict[str, str]) -> str:
    return f"""
    QScrollBar:vertical {{
        background: {color["scrollbar_track_bg"]};
        width: {token["scrollbar_width"]}px;
        margin: {token["padding"]}px {token["padding_small"]}px {token["padding"]}px {token["padding_small"]}px;
        border-radius: {token["border_radius"]}px;
    }}

    QScrollBar::handle:vertical {{
        background: {color["scrollbar_handle_stop"]};
        min-height: 36px;
        border-radius: {token["border_radius"]}px;
        border: {token["border_width"]}px solid {color["border_soft"]};
    }}

    QScrollBar::handle:vertical:hover {{
        background: {color["scrollbar_handle_hover_stop"]};
        border-color: {color["accent"]};
    }}

    QScrollBar:horizontal {{
        background: {color["scrollbar_track_bg"]};
        height: {token["scrollbar_width"]}px;
        margin: {token["padding_small"]}px {token["padding"]}px {token["padding_small"]}px {token["padding"]}px;
        border-radius: {token["border_radius"]}px;
    }}

    QScrollBar::handle:horizontal {{
        background: {color["scrollbar_handle_stop"]};
        min-width: 36px;
        border-radius: {token["border_radius"]}px;
        border: {token["border_width"]}px solid {color["border_soft"]};
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {color["scrollbar_handle_hover_stop"]};
        border-color: {color["accent"]};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical,
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical,
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: transparent;
        border: none;
    }}
    """
