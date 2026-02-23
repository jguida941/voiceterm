//! Theme Studio overlay home so deep visual editing has a dedicated entry surface.

use crate::config::{HudBorderStyle, HudRightPanel, HudStyle};
use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top, truncate_display,
};
#[cfg(test)]
use crate::theme::StylePackFieldId;
use crate::theme::{
    overlay_close_symbol, overlay_move_hint, overlay_separator, resolved_overlay_border_set,
    RuntimeBannerStyleOverride, RuntimeBorderStyleOverride, RuntimeGlyphSetOverride,
    RuntimeIndicatorSetOverride, RuntimeProgressBarFamilyOverride, RuntimeProgressStyleOverride,
    RuntimeStartupStyleOverride, RuntimeToastPositionOverride, RuntimeToastSeverityModeOverride,
    RuntimeVoiceSceneStyleOverride, Theme, ThemeColors,
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
        ThemeStudioItem::ToastPosition => (
            "Toast position",
            format!(
                "Current: {}. Cycle toast placement (theme/top-right/bottom-right/top-center/bottom-center).",
                toast_position_label(view.toast_position_override)
            ),
            false,
        ),
        ThemeStudioItem::StartupSplash => (
            "Startup splash",
            format!(
                "Current: {}. Cycle splash style (theme/full/minimal/hidden).",
                startup_style_label(view.startup_style_override)
            ),
            false,
        ),
        ThemeStudioItem::ToastSeverity => (
            "Toast severity",
            format!(
                "Current: {}. Cycle toast severity display (theme/icon/label/icon+label).",
                toast_severity_mode_label(view.toast_severity_mode_override)
            ),
            false,
        ),
        ThemeStudioItem::BannerStyle => (
            "Banner style",
            format!(
                "Current: {}. Cycle startup banner style (theme/full/compact/minimal/hidden).",
                banner_style_label(view.banner_style_override)
            ),
            false,
        ),
        ThemeStudioItem::UndoEdit => (
            "Undo edit",
            format!(
                "Current: {}. Revert the most recent style-pack override edit.",
                edit_history_state_label(view.undo_available)
            ),
            false,
        ),
        ThemeStudioItem::RedoEdit => (
            "Redo edit",
            format!(
                "Current: {}. Re-apply the most recently undone override edit.",
                edit_history_state_label(view.redo_available)
            ),
            false,
        ),
        ThemeStudioItem::RollbackEdits => (
            "Rollback edits",
            format!(
                "Current: {}. Reset all runtime style-pack overrides to theme defaults.",
                runtime_override_state_label(view.runtime_overrides_dirty)
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

fn edit_history_state_label(available: bool) -> &'static str {
    if available {
        "Available"
    } else {
        "Empty"
    }
}

fn runtime_override_state_label(dirty: bool) -> &'static str {
    if dirty {
        "Dirty"
    } else {
        "Clean"
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
        assert!(rendered.contains("12. Toast position"));
        assert!(rendered.contains("13. Startup splash"));
        assert!(rendered.contains("14. Toast severity"));
        assert!(rendered.contains("15. Banner style"));
        assert!(rendered.contains("16. Undo edit"));
        assert!(rendered.contains("17. Redo edit"));
        assert!(rendered.contains("18. Rollback edits"));
        assert!(rendered.contains("19. Close"));
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
            toast_position_override: Some(RuntimeToastPositionOverride::TopCenter),
            startup_style_override: Some(RuntimeStartupStyleOverride::Minimal),
            toast_severity_mode_override: Some(RuntimeToastSeverityModeOverride::IconAndLabel),
            banner_style_override: Some(RuntimeBannerStyleOverride::Compact),
            undo_available: true,
            redo_available: true,
            runtime_overrides_dirty: true,
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
        assert!(rendered.contains("Current: Top-center"));
        assert!(rendered.contains("Current: Minimal"));
        assert!(rendered.contains("Current: Icon+Label"));
        assert!(rendered.contains("Current: Compact"));
        assert!(rendered.contains("Current: Available"));
        assert!(rendered.contains("Current: Dirty"));
    }

    #[test]
    fn theme_studio_height_matches_contract() {
        assert_eq!(theme_studio_height(), 25);
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
