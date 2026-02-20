//! Theme Studio overlay home so deep visual editing has a dedicated entry surface.

use crate::config::{HudBorderStyle, HudRightPanel, HudStyle};
use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top, truncate_display,
};
use crate::theme::{
    overlay_close_symbol, overlay_move_hint, overlay_separator, RuntimeBorderStyleOverride,
    RuntimeGlyphSetOverride, RuntimeIndicatorSetOverride, RuntimeProgressBarFamilyOverride,
    RuntimeProgressStyleOverride, RuntimeVoiceSceneStyleOverride, Theme, ThemeColors,
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
    ProgressSpinner,
    ProgressBars,
    ThemeBorders,
    VoiceScene,
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
    ThemeStudioItem::ProgressSpinner,
    ThemeStudioItem::ProgressBars,
    ThemeStudioItem::ThemeBorders,
    ThemeStudioItem::VoiceScene,
    ThemeStudioItem::Close,
];

pub(crate) const THEME_STUDIO_OPTION_START_ROW: usize = 4;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) struct ThemeStudioView {
    pub(crate) theme: Theme,
    pub(crate) selected: usize,
    pub(crate) hud_style: HudStyle,
    pub(crate) hud_border_style: HudBorderStyle,
    pub(crate) hud_right_panel: HudRightPanel,
    pub(crate) hud_right_panel_recording_only: bool,
    pub(crate) border_style_override: Option<RuntimeBorderStyleOverride>,
    pub(crate) glyph_set_override: Option<RuntimeGlyphSetOverride>,
    pub(crate) indicator_set_override: Option<RuntimeIndicatorSetOverride>,
    pub(crate) progress_style_override: Option<RuntimeProgressStyleOverride>,
    pub(crate) progress_bar_family_override: Option<RuntimeProgressBarFamilyOverride>,
    pub(crate) voice_scene_style_override: Option<RuntimeVoiceSceneStyleOverride>,
}

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

pub(crate) fn format_theme_studio(view: &ThemeStudioView, width: usize) -> String {
    let colors = view.theme.colors();
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
            view,
            &colors,
            item,
            idx + 1,
            idx == view.selected,
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
    view: &ThemeStudioView,
    colors: &ThemeColors,
    item: &ThemeStudioItem,
    num: usize,
    selected: bool,
    inner_width: usize,
) -> String {
    let (title, description, coming_soon): (&str, String, bool) = match item {
        ThemeStudioItem::ThemePicker => (
            "Theme picker",
            "Open classic palette browser for quick theme apply.".to_string(),
            false,
        ),
        ThemeStudioItem::HudStyle => (
            "HUD style",
            format!(
                "Current: {}. Cycle HUD style (Full, Minimal, Hidden).",
                view.hud_style
            ),
            false,
        ),
        ThemeStudioItem::HudBorders => (
            "HUD borders",
            format!(
                "Current: {}. Cycle Full HUD border style presets.",
                view.hud_border_style
            ),
            false,
        ),
        ThemeStudioItem::HudPanel => (
            "Right panel",
            format!(
                "Current: {}. Cycle right panel mode (ribbon/dots/heartbeat/off).",
                view.hud_right_panel
            ),
            false,
        ),
        ThemeStudioItem::HudAnimate => (
            "Panel animation",
            format!(
                "Current: {}. Toggle panel animation mode (recording-only/always).",
                panel_animation_mode_label(view.hud_right_panel_recording_only)
            ),
            false,
        ),
        ThemeStudioItem::ColorsGlyphs => (
            "Glyph profile",
            format!(
                "Current: {}. Cycle glyph profile (theme/unicode/ascii).",
                glyph_profile_label(view.glyph_set_override)
            ),
            false,
        ),
        ThemeStudioItem::LayoutMotion => (
            "Indicator set",
            format!(
                "Current: {}. Cycle indicator set (theme/ascii/dot/diamond).",
                indicator_set_label(view.indicator_set_override)
            ),
            false,
        ),
        ThemeStudioItem::ProgressSpinner => (
            "Progress spinner",
            format!(
                "Current: {}. Cycle spinner style (theme/braille/dots/line/block).",
                progress_spinner_label(view.progress_style_override)
            ),
            false,
        ),
        ThemeStudioItem::ProgressBars => (
            "Progress bars",
            format!(
                "Current: {}. Cycle bar family (theme/bar/compact/blocks/braille).",
                progress_bar_family_label(view.progress_bar_family_override)
            ),
            false,
        ),
        ThemeStudioItem::ThemeBorders => (
            "Theme borders",
            format!(
                "Current: {}. Cycle theme border profile (theme/single/rounded/double/heavy/none).",
                theme_border_label(view.border_style_override)
            ),
            false,
        ),
        ThemeStudioItem::VoiceScene => (
            "Voice scene",
            format!(
                "Current: {}. Cycle scene style (theme/pulse/static/minimal).",
                voice_scene_label(view.voice_scene_style_override)
            ),
            false,
        ),
        ThemeStudioItem::Close => ("Close", "Dismiss Theme Studio.".to_string(), false),
    };
    let marker = if selected { ">" } else { " " };
    let label = format!("{num}. {title}");
    let label_col = 20usize;
    let label_padded = format!("{label:<width$}", width = label_col);
    let fixed_visible = 1 + 1 + label_col + 1; // marker + space + label + space
    let desc_col = inner_width.saturating_sub(fixed_visible);
    let desc = truncate_display(&description, desc_col);
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

fn panel_animation_mode_label(recording_only: bool) -> &'static str {
    if recording_only {
        "Recording-only"
    } else {
        "Always"
    }
}

fn glyph_profile_label(override_value: Option<RuntimeGlyphSetOverride>) -> &'static str {
    match override_value {
        None => "Theme",
        Some(RuntimeGlyphSetOverride::Unicode) => "Unicode",
        Some(RuntimeGlyphSetOverride::Ascii) => "Ascii",
    }
}

fn indicator_set_label(override_value: Option<RuntimeIndicatorSetOverride>) -> &'static str {
    match override_value {
        None => "Theme",
        Some(RuntimeIndicatorSetOverride::Ascii) => "Ascii",
        Some(RuntimeIndicatorSetOverride::Dot) => "Dot",
        Some(RuntimeIndicatorSetOverride::Diamond) => "Diamond",
    }
}

fn theme_border_label(override_value: Option<RuntimeBorderStyleOverride>) -> &'static str {
    match override_value {
        None => "Theme",
        Some(RuntimeBorderStyleOverride::Single) => "Single",
        Some(RuntimeBorderStyleOverride::Rounded) => "Rounded",
        Some(RuntimeBorderStyleOverride::Double) => "Double",
        Some(RuntimeBorderStyleOverride::Heavy) => "Heavy",
        Some(RuntimeBorderStyleOverride::None) => "None",
    }
}

fn progress_spinner_label(override_value: Option<RuntimeProgressStyleOverride>) -> &'static str {
    match override_value {
        None => "Theme",
        Some(RuntimeProgressStyleOverride::Braille) => "Braille",
        Some(RuntimeProgressStyleOverride::Dots) => "Dots",
        Some(RuntimeProgressStyleOverride::Line) => "Line",
        Some(RuntimeProgressStyleOverride::Block) => "Block",
    }
}

fn progress_bar_family_label(
    override_value: Option<RuntimeProgressBarFamilyOverride>,
) -> &'static str {
    match override_value {
        None => "Theme",
        Some(RuntimeProgressBarFamilyOverride::Bar) => "Bar",
        Some(RuntimeProgressBarFamilyOverride::Compact) => "Compact",
        Some(RuntimeProgressBarFamilyOverride::Blocks) => "Blocks",
        Some(RuntimeProgressBarFamilyOverride::Braille) => "Braille",
    }
}

fn voice_scene_label(override_value: Option<RuntimeVoiceSceneStyleOverride>) -> &'static str {
    match override_value {
        None => "Theme",
        Some(RuntimeVoiceSceneStyleOverride::Pulse) => "Pulse",
        Some(RuntimeVoiceSceneStyleOverride::Static) => "Static",
        Some(RuntimeVoiceSceneStyleOverride::Minimal) => "Minimal",
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::{HudBorderStyle, HudRightPanel, HudStyle};
    use crate::theme::{
        RuntimeBorderStyleOverride, RuntimeGlyphSetOverride, RuntimeIndicatorSetOverride,
        RuntimeProgressBarFamilyOverride, RuntimeProgressStyleOverride,
        RuntimeVoiceSceneStyleOverride,
    };

    fn sample_view(theme: Theme) -> ThemeStudioView {
        ThemeStudioView {
            theme,
            selected: 0,
            hud_style: HudStyle::Full,
            hud_border_style: HudBorderStyle::Theme,
            hud_right_panel: HudRightPanel::Ribbon,
            hud_right_panel_recording_only: true,
            border_style_override: None,
            glyph_set_override: None,
            indicator_set_override: None,
            progress_style_override: None,
            progress_bar_family_override: None,
            voice_scene_style_override: None,
        }
    }

    #[test]
    fn theme_studio_overlay_contains_expected_rows() {
        let rendered = format_theme_studio(&sample_view(Theme::Codex), 80);
        assert!(rendered.contains("VoiceTerm - Theme Studio"));
        assert!(rendered.contains("1. Theme picker"));
        assert!(rendered.contains("2. HUD style"));
        assert!(rendered.contains("3. HUD borders"));
        assert!(rendered.contains("4. Right panel"));
        assert!(rendered.contains("5. Panel animation"));
        assert!(rendered.contains("6. Glyph profile"));
        assert!(rendered.contains("7. Indicator set"));
        assert!(rendered.contains("8. Progress spinner"));
        assert!(rendered.contains("9. Progress bars"));
        assert!(rendered.contains("10. Theme borders"));
        assert!(rendered.contains("11. Voice scene"));
        assert!(rendered.contains("12. Close"));
    }

    #[test]
    fn theme_studio_overlay_marks_selected_row() {
        let mut view = sample_view(Theme::Codex);
        view.selected = 4;
        let rendered = format_theme_studio(&view, 80);
        assert!(rendered.contains("> 5. Panel animation"));
    }

    #[test]
    fn theme_studio_overlay_shows_live_visual_values() {
        let view = ThemeStudioView {
            theme: Theme::Codex,
            selected: 0,
            hud_style: HudStyle::Hidden,
            hud_border_style: HudBorderStyle::Double,
            hud_right_panel: HudRightPanel::Dots,
            hud_right_panel_recording_only: false,
            border_style_override: Some(RuntimeBorderStyleOverride::Heavy),
            glyph_set_override: Some(RuntimeGlyphSetOverride::Ascii),
            indicator_set_override: Some(RuntimeIndicatorSetOverride::Diamond),
            progress_style_override: Some(RuntimeProgressStyleOverride::Line),
            progress_bar_family_override: Some(RuntimeProgressBarFamilyOverride::Blocks),
            voice_scene_style_override: Some(RuntimeVoiceSceneStyleOverride::Pulse),
        };
        let rendered = format_theme_studio(&view, 80);
        assert!(rendered.contains("Current: Hidden"));
        assert!(rendered.contains("Current: Double"));
        assert!(rendered.contains("Current: Dots"));
        assert!(rendered.contains("Current: Always"));
        assert!(rendered.contains("Current: Ascii"));
        assert!(rendered.contains("Current: Diamond"));
        assert!(rendered.contains("Current: Line"));
        assert!(rendered.contains("Current: Blocks"));
        assert!(rendered.contains("Current: Heavy"));
        assert!(rendered.contains("Current: Pulse"));
    }

    #[test]
    fn theme_studio_height_matches_contract() {
        assert_eq!(theme_studio_height(), 18);
    }

    #[test]
    fn theme_studio_item_lookup_defaults_to_close() {
        assert_eq!(theme_studio_item_at(0), ThemeStudioItem::ThemePicker);
        assert_eq!(theme_studio_item_at(11), ThemeStudioItem::Close);
        assert_eq!(theme_studio_item_at(999), ThemeStudioItem::Close);
    }

    #[test]
    fn theme_studio_none_theme_has_no_ansi_sequences() {
        let rendered = format_theme_studio(&sample_view(Theme::None), 80);
        assert!(!rendered.contains("\x1b["));
    }
}
