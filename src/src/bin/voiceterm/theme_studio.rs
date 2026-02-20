//! Theme Studio overlay home so deep visual editing has a dedicated entry surface.

use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top, truncate_display,
};
use crate::theme::{
    overlay_close_symbol, overlay_move_hint, overlay_separator, Theme, ThemeColors,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ThemeStudioItem {
    ThemePicker,
    HudStyle,
    HudBorders,
    HudPanel,
    HudAnimate,
    ColorsGlyphs,
    LayoutMotion,
    Close,
}

pub(crate) const THEME_STUDIO_ITEMS: &[ThemeStudioItem] = &[
    ThemeStudioItem::ThemePicker,
    ThemeStudioItem::HudStyle,
    ThemeStudioItem::HudBorders,
    ThemeStudioItem::HudPanel,
    ThemeStudioItem::HudAnimate,
    ThemeStudioItem::ColorsGlyphs,
    ThemeStudioItem::LayoutMotion,
    ThemeStudioItem::Close,
];

pub(crate) const THEME_STUDIO_OPTION_START_ROW: usize = 4;

#[must_use]
pub(crate) fn theme_studio_footer(colors: &ThemeColors) -> String {
    let close = overlay_close_symbol(colors.glyph_set);
    let sep = overlay_separator(colors.glyph_set);
    let move_hint = overlay_move_hint(colors.glyph_set);
    format!("[{close}] close {sep} {move_hint} move {sep} Enter select")
}

pub(crate) fn theme_studio_inner_width_for_terminal(width: usize) -> usize {
    width.clamp(54, 72)
}

pub(crate) fn theme_studio_total_width_for_terminal(width: usize) -> usize {
    theme_studio_inner_width_for_terminal(width).saturating_add(2)
}

pub(crate) fn theme_studio_height() -> usize {
    // Top border + title + separator + options + separator + footer + bottom border
    1 + 1 + 1 + THEME_STUDIO_ITEMS.len() + 1 + 1 + 1
}

#[must_use]
pub(crate) fn theme_studio_item_at(index: usize) -> ThemeStudioItem {
    THEME_STUDIO_ITEMS
        .get(index)
        .copied()
        .unwrap_or(ThemeStudioItem::Close)
}

pub(crate) fn format_theme_studio(theme: Theme, selected_idx: usize, width: usize) -> String {
    let colors = theme.colors();
    let borders = &colors.borders;
    let total_width = theme_studio_total_width_for_terminal(width);
    let inner_width = total_width.saturating_sub(2);
    let mut lines = Vec::new();

    lines.push(frame_top(&colors, borders, total_width));
    lines.push(centered_title_line(
        &colors,
        borders,
        "VoiceTerm - Theme Studio",
        total_width,
    ));
    lines.push(frame_separator(&colors, borders, total_width));

    for (idx, item) in THEME_STUDIO_ITEMS.iter().enumerate() {
        lines.push(format_theme_studio_option_line(
            &colors,
            item,
            idx + 1,
            idx == selected_idx,
            inner_width,
        ));
    }

    lines.push(frame_separator(&colors, borders, total_width));
    let footer = theme_studio_footer(&colors);
    lines.push(centered_title_line(&colors, borders, &footer, total_width));
    lines.push(frame_bottom(&colors, borders, total_width));

    lines.join("\n")
}

fn format_theme_studio_option_line(
    colors: &ThemeColors,
    item: &ThemeStudioItem,
    num: usize,
    selected: bool,
    inner_width: usize,
) -> String {
    let (title, description, coming_soon) = match item {
        ThemeStudioItem::ThemePicker => (
            "Theme picker",
            "Open classic palette browser for quick theme apply.",
            false,
        ),
        ThemeStudioItem::HudStyle => (
            "HUD style",
            "Cycle HUD style (Full, Minimal, Hidden).",
            false,
        ),
        ThemeStudioItem::HudBorders => {
            ("HUD borders", "Cycle Full HUD border style presets.", false)
        }
        ThemeStudioItem::HudPanel => (
            "Right panel",
            "Cycle right panel mode (ribbon/dots/heartbeat/off).",
            false,
        ),
        ThemeStudioItem::HudAnimate => (
            "Panel animation",
            "Toggle panel animation mode (recording-only/always).",
            false,
        ),
        ThemeStudioItem::ColorsGlyphs => (
            "Colors + glyphs",
            "Theme Studio page set coming soon (tokens + iconography).",
            true,
        ),
        ThemeStudioItem::LayoutMotion => (
            "Layout + motion",
            "Theme Studio page set coming soon (layout + animation).",
            true,
        ),
        ThemeStudioItem::Close => ("Close", "Dismiss Theme Studio.", false),
    };
    let marker = if selected { ">" } else { " " };
    let label = format!("{num}. {title}");
    let label_col = 20usize;
    let label_padded = format!("{label:<width$}", width = label_col);
    let fixed_visible = 1 + 1 + label_col + 1; // marker + space + label + space
    let desc_col = inner_width.saturating_sub(fixed_visible);
    let desc = truncate_display(description, desc_col);
    let desc_pad = " ".repeat(desc_col.saturating_sub(display_width(&desc)));
    let row_prefix = if coming_soon { colors.dim } else { "" };
    let row_suffix = if coming_soon { colors.reset } else { "" };

    format!(
        "{}{}{}{}{} {} {} {}{}{}{}{}{}",
        colors.border,
        colors.borders.vertical,
        colors.reset,
        row_prefix,
        marker,
        label_padded,
        desc,
        desc_pad,
        row_suffix,
        colors.border,
        colors.borders.vertical,
        colors.reset,
        colors.reset
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn theme_studio_overlay_contains_expected_rows() {
        let rendered = format_theme_studio(Theme::Codex, 0, 80);
        assert!(rendered.contains("VoiceTerm - Theme Studio"));
        assert!(rendered.contains("1. Theme picker"));
        assert!(rendered.contains("2. HUD style"));
        assert!(rendered.contains("3. HUD borders"));
        assert!(rendered.contains("4. Right panel"));
        assert!(rendered.contains("5. Panel animation"));
        assert!(rendered.contains("6. Colors + glyphs"));
        assert!(rendered.contains("7. Layout + motion"));
        assert!(rendered.contains("8. Close"));
    }

    #[test]
    fn theme_studio_overlay_marks_selected_row() {
        let rendered = format_theme_studio(Theme::Codex, 4, 80);
        assert!(rendered.contains("> 5. Panel animation"));
    }

    #[test]
    fn theme_studio_height_matches_contract() {
        assert_eq!(theme_studio_height(), 14);
    }

    #[test]
    fn theme_studio_item_lookup_defaults_to_close() {
        assert_eq!(theme_studio_item_at(0), ThemeStudioItem::ThemePicker);
        assert_eq!(theme_studio_item_at(7), ThemeStudioItem::Close);
        assert_eq!(theme_studio_item_at(999), ThemeStudioItem::Close);
    }

    #[test]
    fn theme_studio_none_theme_has_no_ansi_sequences() {
        let rendered = format_theme_studio(Theme::None, 0, 80);
        assert!(!rendered.contains("\x1b["));
    }
}
