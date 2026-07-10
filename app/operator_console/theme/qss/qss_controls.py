"""Control QSS: buttons, inputs, combos, spinboxes, scrollbars."""

from __future__ import annotations

from ..config.style_resolver import (
    resolved_border_width,
    resolved_radius,
    theme_choice,
)


def qss_controls(
    color: dict[str, str],
    token: dict[str, str],
    components: dict[str, str],
    motion: dict[str, str],
) -> str:
    del motion
    return (
        _button_rules(color, token, components)
        + _field_rules(color, token, components)
        + _combo_rules(color, token, components)
        + _scrollbar_rules(color, token, components)
    )


def _button_rules(
    color: dict[str, str],
    token: dict[str, str],
    components: dict[str, str],
) -> str:
    radius = resolved_radius(token, components)
    radius_small = resolved_radius(token, components, size="small")
    border_width = resolved_border_width(token, components)
    button_style = theme_choice(components, "button_style", "soft-fill")
    toolbar_button_style = theme_choice(components, "toolbar_button_style", "chip")

    default_button_background = color["panel_surface"]
    default_button_text = color["text_muted"]
    default_button_border = color["border_soft"]
    if button_style == "outline":
        default_button_background = "transparent"
        default_button_text = color["text"]
        default_button_border = color["card_border"]
    elif button_style == "solid":
        default_button_background = color["panel_surface_alt"]
        default_button_text = color["text"]
        default_button_border = color["card_hover_border"]

    toolbar_background = color["panel_inset"]
    toolbar_border = color["input_border"]
    toolbar_hover_background = color["panel_surface_alt"]
    if toolbar_button_style == "outline":
        toolbar_background = "transparent"
        toolbar_border = color["border_soft"]
        toolbar_hover_background = color["panel_surface"]
    elif toolbar_button_style == "ghost":
        toolbar_background = "transparent"
        toolbar_border = "transparent"
        toolbar_hover_background = color["hover_overlay"]

    primary_background = color["button_primary_bg"]
    primary_color = color["text"]
    warning_background = color["button_warning_bg"]
    warning_color = color["text"]
    danger_background = color["button_danger_bg"]
    danger_color = color["text"]
    if button_style == "outline":
        primary_background = "transparent"
        primary_color = color["accent"]
        warning_background = "transparent"
        warning_color = color["warning"]
        danger_background = "transparent"
        danger_color = color["danger"]
    elif button_style == "solid":
        primary_background = color["button_primary_gradient_top"]
        warning_background = color["button_warning_gradient_top"]
        danger_background = color["button_danger_gradient_top"]

    return f"""
    /* ── Default Button (flatter editor-style chrome) ───────── */

    QPushButton {{
        background: {default_button_background};
        color: {default_button_text};
        border: {border_width}px solid {default_button_border};
        border-radius: {radius}px;
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
        background: {toolbar_background};
        border-color: {toolbar_border};
        padding: {token["padding_small"]}px {token["padding"]}px;
        font-size: {token["font_size_small"]}px;
        border-radius: {radius_small}px;
        min-height: 0px;
        min-width: 0px;
        font-weight: 700;
    }}

    QPushButton#SmallActionButton:hover {{
        background: {toolbar_hover_background};
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
        background: {toolbar_hover_background};
        border-color: {color["accent"]};
        color: {primary_color};
    }}

    QPushButton#SmallActionButton[accentRole="warning"] {{
        background: {toolbar_hover_background};
        border-color: {color["warning"]};
        color: {warning_color};
    }}

    QPushButton#SmallActionButton[accentRole="danger"] {{
        background: {toolbar_hover_background};
        border-color: {color["danger"]};
        color: {danger_color};
    }}

    /* ── Primary Accent (filled, prominent) ─────────────────── */

    QPushButton[accentRole="primary"] {{
        color: {primary_color};
        background: {primary_background};
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
        color: {warning_color};
        background: {warning_background};
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
        color: {danger_color};
        background: {danger_background};
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
        border-radius: {radius_small}px;
        min-height: 0px;
        color: {color["text_dim"]};
        background: {color["panel_surface"]};
        border: {border_width}px solid {color["border_soft"]};
    }}

    QPushButton#SmallToggleButton:hover {{
        color: {color["text"]};
        border-color: {color["accent"]};
        background: {color["panel_inset"]};
    }}
    """


def _field_rules(
    color: dict[str, str],
    token: dict[str, str],
    components: dict[str, str],
) -> str:
    radius = resolved_radius(token, components)
    border_width = resolved_border_width(token, components)
    focus_border_width = resolved_border_width(token, components, focus=True)
    input_style = theme_choice(components, "input_style", "inset")
    input_background = color["panel_inset"]
    input_border = color["border_soft"]
    input_radius = f"{radius}px"
    input_extra = ""
    if input_style == "outline":
        input_background = color["panel_surface"]
        input_border = color["card_border"]
    elif input_style == "flat":
        input_background = "transparent"
        input_radius = "0px"
        input_extra = (
            "        border-top: 0px solid transparent;\n"
            "        border-left: 0px solid transparent;\n"
            "        border-right: 0px solid transparent;\n"
        )
    return f"""

    QLineEdit,
    QSpinBox,
    QComboBox,
    QListWidget,
    QPlainTextEdit,
    QTextBrowser {{
        background: {input_background};
        color: {color["text"]};
        border: {border_width}px solid {input_border};
{input_extra}        border-radius: {input_radius};
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
        border: {focus_border_width}px solid {color["accent"]};
    }}

    QListWidget::item {{
        border-radius: {radius}px;
        padding: {token["padding"]}px;
    }}

    QListWidget::item:selected {{
        background: {color["selection_bg"]};
        color: {color["text"]};
    }}
    """


def _combo_rules(
    color: dict[str, str],
    token: dict[str, str],
    components: dict[str, str],
) -> str:
    radius = resolved_radius(token, components)
    radius_small = resolved_radius(token, components, size="small")
    border_width = resolved_border_width(token, components)
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
        border: {border_width}px solid {color["border_soft"]};
        border-radius: {radius}px;
        padding: {token["padding_small"]}px;
        selection-background-color: {color["selection_bg"]};
        selection-color: {color["selection_text"]};
        outline: none;
    }}

    QComboBox QAbstractItemView::item {{
        padding: {token["padding_small"]}px {token["padding"]}px;
        min-height: {token["input_height"]}px;
        border-radius: {radius_small}px;
    }}

    QComboBox QAbstractItemView::item:selected {{
        background: {color["selection_bg"]};
        color: {color["text"]};
    }}

    QComboBox QAbstractItemView::item:hover {{
        background: {color["hover_overlay"]};
    }}
    """


def _scrollbar_rules(
    color: dict[str, str],
    token: dict[str, str],
    components: dict[str, str],
) -> str:
    radius = resolved_radius(token, components)
    border_width = resolved_border_width(token, components)
    return f"""
    QScrollBar:vertical {{
        background: {color["scrollbar_track_bg"]};
        width: {token["scrollbar_width"]}px;
        margin: {token["padding"]}px {token["padding_small"]}px {token["padding"]}px {token["padding_small"]}px;
        border-radius: {radius}px;
    }}

    QScrollBar::handle:vertical {{
        background: {color["scrollbar_handle_stop"]};
        min-height: 36px;
        border-radius: {radius}px;
        border: {border_width}px solid {color["border_soft"]};
    }}

    QScrollBar::handle:vertical:hover {{
        background: {color["scrollbar_handle_hover_stop"]};
        border-color: {color["accent"]};
    }}

    QScrollBar:horizontal {{
        background: {color["scrollbar_track_bg"]};
        height: {token["scrollbar_width"]}px;
        margin: {token["padding_small"]}px {token["padding"]}px {token["padding_small"]}px {token["padding"]}px;
        border-radius: {radius}px;
    }}

    QScrollBar::handle:horizontal {{
        background: {color["scrollbar_handle_stop"]};
        min-width: 36px;
        border-radius: {radius}px;
        border: {border_width}px solid {color["border_soft"]};
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
