//! Theme Studio overlay home so deep visual editing has a dedicated entry surface.

use crate::config::{HudBorderStyle, HudRightPanel, HudStyle};
use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top, truncate_display,
};
#[cfg(test)]
use crate::theme::StylePackFieldId;
use crate::theme::{
    overlay_close_symbol, overlay_move_hint, overlay_row_marker, overlay_separator,
    resolved_overlay_border_set, RuntimeBannerStyleOverride, RuntimeBorderStyleOverride,
    RuntimeGlyphSetOverride, RuntimeIndicatorSetOverride, RuntimeProgressBarFamilyOverride,
    RuntimeProgressStyleOverride, RuntimeStartupStyleOverride, RuntimeToastPositionOverride,
    RuntimeToastSeverityModeOverride, RuntimeVoiceSceneStyleOverride, Theme, ThemeColors,
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
    ToastPosition,
    StartupSplash,
    ToastSeverity,
    BannerStyle,
    UndoEdit,
    RedoEdit,
    RollbackEdits,
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
    ThemeStudioItem::ToastPosition,
    ThemeStudioItem::StartupSplash,
    ThemeStudioItem::ToastSeverity,
    ThemeStudioItem::BannerStyle,
    ThemeStudioItem::UndoEdit,
    ThemeStudioItem::RedoEdit,
    ThemeStudioItem::RollbackEdits,
    ThemeStudioItem::Close,
];

pub(crate) const THEME_STUDIO_OPTION_START_ROW: usize = 4;
#[cfg(test)]
const STYLE_PACK_STUDIO_PARITY_COMPLETE: bool = true;

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
    pub(crate) toast_position_override: Option<RuntimeToastPositionOverride>,
    pub(crate) startup_style_override: Option<RuntimeStartupStyleOverride>,
    pub(crate) toast_severity_mode_override: Option<RuntimeToastSeverityModeOverride>,
    pub(crate) banner_style_override: Option<RuntimeBannerStyleOverride>,
    pub(crate) undo_available: bool,
    pub(crate) redo_available: bool,
    pub(crate) runtime_overrides_dirty: bool,
}

#[must_use]
pub(crate) fn theme_studio_footer(colors: &ThemeColors) -> String {
    let close = overlay_close_symbol(colors.glyph_set);
    let sep = overlay_separator(colors.glyph_set);
    let move_hint = overlay_move_hint(colors.glyph_set);
    let adjust_hint = match colors.glyph_set {
        crate::theme::GlyphSet::Unicode => "\u{2190}/\u{2192}",
        crate::theme::GlyphSet::Ascii => "left/right",
    };
    format!("[{close}] close {sep} {move_hint} move {sep} {adjust_hint} adjust {sep} Enter select")
}

pub(crate) fn theme_studio_inner_width_for_terminal(width: usize) -> usize {
    width.clamp(60, 82)
}

pub(crate) fn theme_studio_total_width_for_terminal(width: usize) -> usize {
    theme_studio_inner_width_for_terminal(width).saturating_add(2)
}

pub(crate) fn theme_studio_height() -> usize {
    // Top border + title + separator + options + tip + separator + footer + bottom border
    1 + 1 + 1 + THEME_STUDIO_ITEMS.len() + 1 + 1 + 1 + 1
}

#[must_use]
pub(crate) fn theme_studio_item_at(index: usize) -> ThemeStudioItem {
    THEME_STUDIO_ITEMS
        .get(index)
        .copied()
        .unwrap_or(ThemeStudioItem::Close)
}

pub(crate) fn format_theme_studio(view: &ThemeStudioView, width: usize) -> String {
    let mut colors = view.theme.colors();
    colors.borders = resolved_overlay_border_set(view.theme);
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
            idx == view.selected,
            inner_width,
        ));
    }

    lines.push(format_theme_studio_tip_row(view, &colors, inner_width));
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
    selected: bool,
    inner_width: usize,
) -> String {
    const LABEL_WIDTH: usize = 20;
    let (label, value, _tip, read_only) = theme_studio_row(view, item);
    let marker = if selected {
        overlay_row_marker(colors.glyph_set)
    } else {
        " "
    };
    let row_text = format!("{marker} {:<width$} {value}", label, width = LABEL_WIDTH);
    format_theme_studio_menu_row(colors, inner_width, &row_text, selected, read_only)
}

fn format_theme_studio_tip_row(
    view: &ThemeStudioView,
    colors: &ThemeColors,
    inner_width: usize,
) -> String {
    let selected_item = theme_studio_item_at(view.selected);
    let (_label, _value, tip, _read_only) = theme_studio_row(view, &selected_item);
    let text = format!(" tip: {tip}");
    let clipped = truncate_display(&text, inner_width);
    let pad = " ".repeat(inner_width.saturating_sub(display_width(&clipped)));
    format!(
        "{}{}{}{}{}{}{}{}",
        colors.border,
        colors.borders.vertical,
        colors.dim,
        clipped,
        pad,
        colors.border,
        colors.borders.vertical,
        colors.reset
    )
}

fn format_theme_studio_menu_row(
    colors: &ThemeColors,
    inner_width: usize,
    text: &str,
    selected: bool,
    read_only: bool,
) -> String {
    let clipped = truncate_display(text, inner_width);
    let padded = format!(
        "{clipped}{}",
        " ".repeat(inner_width.saturating_sub(display_width(&clipped)))
    );
    let styled = if selected {
        if read_only {
            format!("{}{}{}", colors.dim, padded, colors.reset)
        } else {
            format!("{}{}{}", colors.info, padded, colors.reset)
        }
    } else if read_only {
        format!("{}{}{}", colors.dim, padded, colors.reset)
    } else {
        padded
    };
    format!(
        "{}{}{}{}{}{}{}",
        colors.border,
        colors.borders.vertical,
        colors.reset,
        styled,
        colors.border,
        colors.borders.vertical,
        colors.reset
    )
}

fn theme_studio_row(
    view: &ThemeStudioView,
    item: &ThemeStudioItem,
) -> (&'static str, String, String, bool) {
    match item {
        ThemeStudioItem::ThemePicker => (
            "Theme picker",
            button_label("Open"),
            "Open classic palette browser for quick theme apply.".to_string(),
            false,
        ),
        ThemeStudioItem::HudStyle => (
            "HUD style",
            button_label(&view.hud_style.to_string()),
            "Cycle HUD style (Full, Minimal, Hidden).".to_string(),
            false,
        ),
        ThemeStudioItem::HudBorders => (
            "HUD borders",
            button_label(&view.hud_border_style.to_string()),
            "Cycle Full HUD border style presets.".to_string(),
            false,
        ),
        ThemeStudioItem::HudPanel => (
            "Right panel",
            button_label(&view.hud_right_panel.to_string()),
            "Cycle right-panel mode (Ribbon, Dots, Heartbeat, Off).".to_string(),
            false,
        ),
        ThemeStudioItem::HudAnimate => (
            "Panel animation",
            button_label(panel_animation_mode_label(
                view.hud_right_panel_recording_only,
            )),
            "Toggle panel animation mode (recording-only/always).".to_string(),
            false,
        ),
        ThemeStudioItem::ColorsGlyphs => (
            "Glyph profile",
            button_label(glyph_profile_label(view.glyph_set_override)),
            "Cycle glyph profile (theme/unicode/ascii).".to_string(),
            false,
        ),
        ThemeStudioItem::LayoutMotion => (
            "Indicator set",
            button_label(indicator_set_label(view.indicator_set_override)),
            "Cycle indicator set (theme/ascii/dot/diamond).".to_string(),
            false,
        ),
        ThemeStudioItem::ProgressSpinner => (
            "Progress spinner",
            button_label(progress_spinner_label(view.progress_style_override)),
            "Cycle spinner style (theme/braille/dots/line/block).".to_string(),
            false,
        ),
        ThemeStudioItem::ProgressBars => (
            "Progress bars",
            button_label(progress_bar_family_label(view.progress_bar_family_override)),
            "Cycle bar family (theme/bar/compact/blocks/braille).".to_string(),
            false,
        ),
        ThemeStudioItem::ThemeBorders => (
            "Theme borders",
            button_label(theme_border_label(view.border_style_override)),
            "Cycle theme border profile (theme/single/rounded/double/heavy/none).".to_string(),
            false,
        ),
        ThemeStudioItem::VoiceScene => (
            "Voice scene",
            button_label(voice_scene_label(view.voice_scene_style_override)),
            "Cycle scene style (theme/pulse/static/minimal).".to_string(),
            false,
        ),
        ThemeStudioItem::ToastPosition => (
            "Toast position",
            button_label(toast_position_label(view.toast_position_override)),
            "Cycle toast placement (theme/top-right/bottom-right/top-center/bottom-center)."
                .to_string(),
            false,
        ),
        ThemeStudioItem::StartupSplash => (
            "Startup splash",
            button_label(startup_style_label(view.startup_style_override)),
            "Cycle splash style (theme/full/minimal/hidden).".to_string(),
            false,
        ),
        ThemeStudioItem::ToastSeverity => (
            "Toast severity",
            button_label(toast_severity_mode_label(view.toast_severity_mode_override)),
            "Cycle toast severity display (theme/icon/label/icon+label).".to_string(),
            false,
        ),
        ThemeStudioItem::BannerStyle => (
            "Banner style",
            button_label(banner_style_label(view.banner_style_override)),
            "Cycle startup banner style (theme/full/compact/minimal/hidden).".to_string(),
            false,
        ),
        ThemeStudioItem::UndoEdit => (
            "Undo edit",
            button_label(if view.undo_available { "Undo" } else { "Empty" }),
            "Revert the most recent style-pack override edit.".to_string(),
            !view.undo_available,
        ),
        ThemeStudioItem::RedoEdit => (
            "Redo edit",
            button_label(if view.redo_available { "Redo" } else { "Empty" }),
            "Re-apply the most recently undone override edit.".to_string(),
            !view.redo_available,
        ),
        ThemeStudioItem::RollbackEdits => (
            "Rollback edits",
            button_label(if view.runtime_overrides_dirty {
                "Rollback"
            } else {
                "Clean"
            }),
            "Reset all runtime style-pack overrides to theme defaults.".to_string(),
            !view.runtime_overrides_dirty,
        ),
        ThemeStudioItem::Close => (
            "Close",
            button_label("Close"),
            "Dismiss Theme Studio.".to_string(),
            false,
        ),
    }
}

fn button_label(label: &str) -> String {
    format!("[ {label} ]")
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

fn toast_position_label(override_value: Option<RuntimeToastPositionOverride>) -> &'static str {
    match override_value {
        None => "Theme",
        Some(RuntimeToastPositionOverride::TopRight) => "Top-right",
        Some(RuntimeToastPositionOverride::BottomRight) => "Bottom-right",
        Some(RuntimeToastPositionOverride::TopCenter) => "Top-center",
        Some(RuntimeToastPositionOverride::BottomCenter) => "Bottom-center",
    }
}

fn startup_style_label(override_value: Option<RuntimeStartupStyleOverride>) -> &'static str {
    match override_value {
        None => "Theme",
        Some(RuntimeStartupStyleOverride::Full) => "Full",
        Some(RuntimeStartupStyleOverride::Minimal) => "Minimal",
        Some(RuntimeStartupStyleOverride::Hidden) => "Hidden",
    }
}

fn toast_severity_mode_label(
    override_value: Option<RuntimeToastSeverityModeOverride>,
) -> &'static str {
    match override_value {
        None => "Theme",
        Some(RuntimeToastSeverityModeOverride::Icon) => "Icon",
        Some(RuntimeToastSeverityModeOverride::Label) => "Label",
        Some(RuntimeToastSeverityModeOverride::IconAndLabel) => "Icon+Label",
    }
}

fn banner_style_label(override_value: Option<RuntimeBannerStyleOverride>) -> &'static str {
    match override_value {
        None => "Theme",
        Some(RuntimeBannerStyleOverride::Full) => "Full",
        Some(RuntimeBannerStyleOverride::Compact) => "Compact",
        Some(RuntimeBannerStyleOverride::Minimal) => "Minimal",
        Some(RuntimeBannerStyleOverride::Hidden) => "Hidden",
    }
}

#[cfg(test)]
fn style_pack_field_studio_item(field: StylePackFieldId) -> Option<ThemeStudioItem> {
    match field {
        StylePackFieldId::OverrideBorderStyle => Some(ThemeStudioItem::ThemeBorders),
        StylePackFieldId::OverrideIndicatorSet => Some(ThemeStudioItem::LayoutMotion),
        StylePackFieldId::OverrideGlyphSet => Some(ThemeStudioItem::ColorsGlyphs),
        StylePackFieldId::SurfaceToastPosition => Some(ThemeStudioItem::ToastPosition),
        StylePackFieldId::SurfaceStartupStyle => Some(ThemeStudioItem::StartupSplash),
        StylePackFieldId::SurfaceProgressStyle => Some(ThemeStudioItem::ProgressSpinner),
        StylePackFieldId::SurfaceVoiceSceneStyle => Some(ThemeStudioItem::VoiceScene),
        StylePackFieldId::ComponentOverlayBorder => Some(ThemeStudioItem::ThemeBorders),
        StylePackFieldId::ComponentHudBorder => Some(ThemeStudioItem::HudBorders),
        StylePackFieldId::ComponentToastSeverityMode => Some(ThemeStudioItem::ToastSeverity),
        StylePackFieldId::ComponentBannerStyle => Some(ThemeStudioItem::BannerStyle),
        StylePackFieldId::ComponentProgressBarFamily => Some(ThemeStudioItem::ProgressBars),
    }
}

#[cfg(test)]
fn style_pack_field_studio_mapping_deferred(field: StylePackFieldId) -> bool {
    match field {
        StylePackFieldId::OverrideBorderStyle
        | StylePackFieldId::OverrideIndicatorSet
        | StylePackFieldId::OverrideGlyphSet
        | StylePackFieldId::SurfaceToastPosition
        | StylePackFieldId::SurfaceStartupStyle
        | StylePackFieldId::SurfaceProgressStyle
        | StylePackFieldId::SurfaceVoiceSceneStyle
        | StylePackFieldId::ComponentOverlayBorder
        | StylePackFieldId::ComponentHudBorder
        | StylePackFieldId::ComponentToastSeverityMode
        | StylePackFieldId::ComponentBannerStyle
        | StylePackFieldId::ComponentProgressBarFamily => false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::{HudBorderStyle, HudRightPanel, HudStyle};
    use crate::theme::{
        RuntimeBannerStyleOverride, RuntimeBorderStyleOverride, RuntimeGlyphSetOverride,
        RuntimeIndicatorSetOverride, RuntimeProgressBarFamilyOverride,
        RuntimeProgressStyleOverride, RuntimeStartupStyleOverride, RuntimeToastPositionOverride,
        RuntimeToastSeverityModeOverride, RuntimeVoiceSceneStyleOverride,
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
            toast_position_override: None,
            startup_style_override: None,
            toast_severity_mode_override: None,
            banner_style_override: None,
            undo_available: false,
            redo_available: false,
            runtime_overrides_dirty: false,
        }
    }

    #[test]
    fn theme_studio_overlay_contains_expected_rows() {
        let rendered = format_theme_studio(&sample_view(Theme::Codex), 80);
        assert!(rendered.contains("VoiceTerm - Theme Studio"));
        assert!(rendered.contains("Theme picker"));
        assert!(rendered.contains("HUD style"));
        assert!(rendered.contains("HUD borders"));
        assert!(rendered.contains("Right panel"));
        assert!(rendered.contains("Panel animation"));
        assert!(rendered.contains("Glyph profile"));
        assert!(rendered.contains("Indicator set"));
        assert!(rendered.contains("Progress spinner"));
        assert!(rendered.contains("Progress bars"));
        assert!(rendered.contains("Theme borders"));
        assert!(rendered.contains("Voice scene"));
        assert!(rendered.contains("Toast position"));
        assert!(rendered.contains("Startup splash"));
        assert!(rendered.contains("Toast severity"));
        assert!(rendered.contains("Banner style"));
        assert!(rendered.contains("Undo edit"));
        assert!(rendered.contains("Redo edit"));
        assert!(rendered.contains("Rollback edits"));
        assert!(rendered.contains("Close"));
        assert!(rendered.contains("[ Open ]"));
        assert!(rendered.contains("[ Empty ]"));
        assert!(rendered.contains("[ Clean ]"));
        assert!(rendered.contains("tip: Open classic palette browser"));
    }

    #[test]
    fn theme_studio_overlay_marks_selected_row() {
        let mut view = sample_view(Theme::Codex);
        view.selected = 4;
        let rendered = format_theme_studio(&view, 80);
        let marker = overlay_row_marker(Theme::Codex.colors().glyph_set);
        let selected_label = format!("{marker} Panel animation");
        assert!(rendered.contains(&selected_label));
    }

    #[test]
    fn theme_studio_overlay_shows_selected_row_tip() {
        let mut view = sample_view(Theme::Codex);
        view.selected = 10;
        let rendered = format_theme_studio(&view, 80);
        assert!(rendered.contains("tip: Cycle scene style (theme/pulse/static/minimal)."));
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
            toast_position_override: Some(RuntimeToastPositionOverride::TopCenter),
            startup_style_override: Some(RuntimeStartupStyleOverride::Minimal),
            toast_severity_mode_override: Some(RuntimeToastSeverityModeOverride::IconAndLabel),
            banner_style_override: Some(RuntimeBannerStyleOverride::Compact),
            undo_available: true,
            redo_available: true,
            runtime_overrides_dirty: true,
        };
        let rendered = format_theme_studio(&view, 80);
        assert!(rendered.contains("[ Hidden ]"));
        assert!(rendered.contains("[ Double ]"));
        assert!(rendered.contains("[ Dots ]"));
        assert!(rendered.contains("[ Always ]"));
        assert!(rendered.contains("[ Ascii ]"));
        assert!(rendered.contains("[ Diamond ]"));
        assert!(rendered.contains("[ Line ]"));
        assert!(rendered.contains("[ Blocks ]"));
        assert!(rendered.contains("[ Heavy ]"));
        assert!(rendered.contains("[ Pulse ]"));
        assert!(rendered.contains("[ Top-center ]"));
        assert!(rendered.contains("[ Minimal ]"));
        assert!(rendered.contains("[ Icon+Label ]"));
        assert!(rendered.contains("[ Compact ]"));
        assert!(rendered.contains("[ Undo ]"));
        assert!(rendered.contains("[ Rollback ]"));
    }

    #[test]
    fn theme_studio_height_matches_contract() {
        assert_eq!(theme_studio_height(), 26);
    }

    #[test]
    fn theme_studio_item_lookup_defaults_to_close() {
        assert_eq!(theme_studio_item_at(0), ThemeStudioItem::ThemePicker);
        assert_eq!(theme_studio_item_at(18), ThemeStudioItem::Close);
        assert_eq!(theme_studio_item_at(999), ThemeStudioItem::Close);
    }

    #[test]
    fn theme_studio_none_theme_has_no_ansi_sequences() {
        let rendered = format_theme_studio(&sample_view(Theme::None), 80);
        assert!(!rendered.contains("\x1b["));
    }

    #[test]
    fn theme_studio_footer_respects_ascii_glyph_set() {
        let mut colors = Theme::None.colors();
        colors.glyph_set = crate::theme::GlyphSet::Ascii;
        assert_eq!(
            theme_studio_footer(&colors),
            "[x] close | up/down move | left/right adjust | Enter select"
        );
    }

    #[test]
    fn style_pack_field_mapping_classifies_every_field_exactly_once() {
        for field in StylePackFieldId::all() {
            let mapped = style_pack_field_studio_item(*field).is_some();
            let deferred = style_pack_field_studio_mapping_deferred(*field);
            assert!(
                mapped ^ deferred,
                "field {} must be mapped or deferred (exclusive)",
                field.path()
            );
        }
    }

    #[test]
    fn style_pack_field_mapping_points_to_existing_theme_studio_rows() {
        for field in StylePackFieldId::all() {
            if let Some(item) = style_pack_field_studio_item(*field) {
                assert!(
                    THEME_STUDIO_ITEMS.contains(&item),
                    "field {} maps to non-existent Theme Studio row {:?}",
                    field.path(),
                    item
                );
            }
        }
    }

    #[test]
    fn style_pack_field_mapping_parity_gate_respects_completion_flag() {
        let deferred_count = StylePackFieldId::all()
            .iter()
            .filter(|field| style_pack_field_studio_mapping_deferred(**field))
            .count();
        if STYLE_PACK_STUDIO_PARITY_COMPLETE {
            assert_eq!(
                deferred_count, 0,
                "post-parity gate requires zero deferred style-pack fields"
            );
        } else {
            assert!(
                deferred_count > 0,
                "pre-parity configuration should track deferred style-pack fields"
            );
        }
    }
}
