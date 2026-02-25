//! Colors page: lists semantic color fields with live swatches.
//!
//! Users navigate a list of 10 semantic color fields and press Enter to open
//! the inline color picker for the selected field.

use crate::theme::color_value::{palette_to_resolved, ColorValue, ResolvedThemeColors, Rgb};
use crate::theme::{RuntimeGlyphSetOverride, RuntimeIndicatorSetOverride, Theme};

use super::color_picker::ColorPickerState;
use super::nav::{select_next, select_prev};

/// Semantic color field identifiers for the editor.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ColorField {
    Recording,
    Processing,
    Success,
    Warning,
    Error,
    Info,
    Dim,
    BgPrimary,
    BgSecondary,
    Border,
}

impl ColorField {
    pub(crate) const ALL: &'static [Self] = &[
        Self::Recording,
        Self::Processing,
        Self::Success,
        Self::Warning,
        Self::Error,
        Self::Info,
        Self::Dim,
        Self::BgPrimary,
        Self::BgSecondary,
        Self::Border,
    ];

    #[must_use]
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Recording => "Recording",
            Self::Processing => "Processing",
            Self::Success => "Success",
            Self::Warning => "Warning",
            Self::Error => "Error",
            Self::Info => "Info",
            Self::Dim => "Dim",
            Self::BgPrimary => "Bg Primary",
            Self::BgSecondary => "Bg Secondary",
            Self::Border => "Border",
        }
    }

    /// Get the current color value for this field from resolved colors.
    #[must_use]
    pub(crate) fn get(self, colors: &ResolvedThemeColors) -> ColorValue {
        match self {
            Self::Recording => colors.recording,
            Self::Processing => colors.processing,
            Self::Success => colors.success,
            Self::Warning => colors.warning,
            Self::Error => colors.error,
            Self::Info => colors.info,
            Self::Dim => colors.dim,
            Self::BgPrimary => colors.bg_primary,
            Self::BgSecondary => colors.bg_secondary,
            Self::Border => colors.border,
        }
    }

    /// Set the color value for this field on resolved colors.
    pub(crate) fn set(self, colors: &mut ResolvedThemeColors, value: ColorValue) {
        match self {
            Self::Recording => colors.recording = value,
            Self::Processing => colors.processing = value,
            Self::Success => colors.success = value,
            Self::Warning => colors.warning = value,
            Self::Error => colors.error = value,
            Self::Info => colors.info = value,
            Self::Dim => colors.dim = value,
            Self::BgPrimary => colors.bg_primary = value,
            Self::BgSecondary => colors.bg_secondary = value,
            Self::Border => colors.border = value,
        }
    }
}

/// Number of non-color selector rows in the colors editor.
const EXTRA_SELECTOR_ITEMS: usize = 2;
/// Total navigable items: color fields + indicator/glyph selectors.
const TOTAL_ITEMS: usize = ColorField::ALL.len() + EXTRA_SELECTOR_ITEMS;

/// State for the Colors editor page.
#[derive(Debug, Clone)]
pub(crate) struct ColorsEditorState {
    pub(crate) selected: usize,
    pub(crate) colors: ResolvedThemeColors,
    pub(crate) picker: Option<ColorPickerState>,
    pub(crate) indicator_set: Option<RuntimeIndicatorSetOverride>,
    pub(crate) glyph_set: Option<RuntimeGlyphSetOverride>,
}

impl ColorsEditorState {
    /// Create a new Colors editor initialized from the given theme.
    #[must_use]
    pub(crate) fn new(theme: Theme) -> Self {
        let overrides = crate::theme::runtime_style_pack_overrides();
        Self {
            selected: 0,
            colors: palette_to_resolved(&theme.colors()),
            picker: None,
            indicator_set: overrides.indicator_set_override,
            glyph_set: overrides.glyph_set_override,
        }
    }

    /// Get the currently selected color field.
    #[must_use]
    pub(crate) fn selected_field(&self) -> ColorField {
        ColorField::ALL
            .get(self.selected)
            .copied()
            .unwrap_or(ColorField::Recording)
    }

    /// Open the color picker for the currently selected field.
    pub(crate) fn open_picker(&mut self) {
        let field = self.selected_field();
        let current = field.get(&self.colors);
        let rgb = match current {
            ColorValue::Rgb(rgb) => rgb,
            _ => Rgb {
                r: 128,
                g: 128,
                b: 128,
            },
        };
        self.picker = Some(ColorPickerState::new(rgb));
    }

    /// Apply the current picker color to the selected field and close picker.
    pub(crate) fn apply_picker(&mut self) {
        if let Some(ref picker) = self.picker {
            let field = self.selected_field();
            field.set(&mut self.colors, ColorValue::Rgb(picker.rgb));
        }
        self.picker = None;
    }

    /// Select previous row.
    pub(crate) fn select_prev(&mut self) {
        select_prev(&mut self.selected);
    }

    /// Select next row.
    pub(crate) fn select_next(&mut self) {
        select_next(&mut self.selected, TOTAL_ITEMS);
    }

    /// Whether the selected item is a color field (vs indicator/glyph selector).
    #[must_use]
    pub(crate) fn is_color_field_selected(&self) -> bool {
        self.selected < ColorField::ALL.len()
    }

    /// Cycle indicator set with Left/Right arrows. Returns true if changed.
    pub(crate) fn cycle_indicator_set(&mut self, direction: i32) -> bool {
        const VALUES: &[Option<RuntimeIndicatorSetOverride>] = &[
            None,
            Some(RuntimeIndicatorSetOverride::Ascii),
            Some(RuntimeIndicatorSetOverride::Dot),
            Some(RuntimeIndicatorSetOverride::Diamond),
        ];
        let idx = VALUES
            .iter()
            .position(|v| *v == self.indicator_set)
            .unwrap_or(0);
        let next = if direction > 0 {
            (idx + 1) % VALUES.len()
        } else {
            (idx + VALUES.len() - 1) % VALUES.len()
        };
        if VALUES[next] != self.indicator_set {
            self.indicator_set = VALUES[next];
            true
        } else {
            false
        }
    }

    /// Cycle glyph set with Left/Right arrows. Returns true if changed.
    pub(crate) fn cycle_glyph_set(&mut self, direction: i32) -> bool {
        const VALUES: &[Option<RuntimeGlyphSetOverride>] = &[
            None,
            Some(RuntimeGlyphSetOverride::Unicode),
            Some(RuntimeGlyphSetOverride::Ascii),
        ];
        let idx = VALUES
            .iter()
            .position(|v| *v == self.glyph_set)
            .unwrap_or(0);
        let next = if direction > 0 {
            (idx + 1) % VALUES.len()
        } else {
            (idx + VALUES.len() - 1) % VALUES.len()
        };
        if VALUES[next] != self.glyph_set {
            self.glyph_set = VALUES[next];
            true
        } else {
            false
        }
    }

    /// Render the colors page as lines.
    #[must_use]
    pub(crate) fn render(&self, fg_escape: &str, dim_escape: &str, reset: &str) -> Vec<String> {
        let mut lines = Vec::new();

        for (i, field) in ColorField::ALL.iter().enumerate() {
            let color = field.get(&self.colors);
            let hex = match color {
                ColorValue::Rgb(rgb) => rgb.to_hex(),
                ColorValue::Ansi16(code) => format!("ANSI {code}"),
                ColorValue::Reset => "reset".to_string(),
                ColorValue::Empty => "(empty)".to_string(),
            };
            let swatch_escape = color.to_escape();
            let marker = if i == self.selected { "▸" } else { " " };
            let edit_hint = if i == self.selected {
                "  [Enter to edit]"
            } else {
                ""
            };

            lines.push(format!(
                " {marker} {:<14} {hex:<10} {swatch_escape}████{reset}{edit_hint}",
                field.label(),
            ));
        }

        // Separator before indicator/glyph selectors.
        lines.push(format!(" {dim_escape}─── Indicators & Glyphs ───{reset}"));

        // Indicator set selector (item index 10).
        let ind_idx = ColorField::ALL.len();
        let ind_marker = if self.selected == ind_idx { "▸" } else { " " };
        let ind_highlight = if self.selected == ind_idx {
            fg_escape
        } else {
            dim_escape
        };
        let ind_label = indicator_set_label(self.indicator_set);
        let ind_preview = indicator_set_preview(self.indicator_set);
        let ind_hint = if self.selected == ind_idx {
            "  [←/→ to cycle]"
        } else {
            ""
        };
        lines.push(format!(
            " {ind_marker} {ind_highlight}Indicators{reset}  {ind_label:<10} {ind_preview}{ind_hint}"
        ));

        // Glyph set selector (item index 11).
        let gly_idx = ind_idx + 1;
        let gly_marker = if self.selected == gly_idx { "▸" } else { " " };
        let gly_highlight = if self.selected == gly_idx {
            fg_escape
        } else {
            dim_escape
        };
        let gly_label = glyph_set_label(self.glyph_set);
        let gly_hint = if self.selected == gly_idx {
            "  [←/→ to cycle]"
        } else {
            ""
        };
        lines.push(format!(
            " {gly_marker} {gly_highlight}Glyph Set{reset}   {gly_label}{gly_hint}"
        ));

        // If picker is open, render it below.
        if let Some(ref picker) = self.picker {
            lines.push(String::new());
            lines.push(format!(
                " {fg_escape}Editing: {}{reset}",
                self.selected_field().label()
            ));
            for line in picker.render(fg_escape, reset) {
                lines.push(format!("  {line}"));
            }
        }

        lines
    }
}

fn indicator_set_label(set: Option<RuntimeIndicatorSetOverride>) -> &'static str {
    match set {
        None => "Theme",
        Some(RuntimeIndicatorSetOverride::Ascii) => "Ascii",
        Some(RuntimeIndicatorSetOverride::Dot) => "Dot",
        Some(RuntimeIndicatorSetOverride::Diamond) => "Diamond",
    }
}

fn indicator_set_preview(set: Option<RuntimeIndicatorSetOverride>) -> &'static str {
    match set {
        None => "◆ ◇ ▸ · ◐ ↺",
        Some(RuntimeIndicatorSetOverride::Ascii) => "* @ > - ~ >",
        Some(RuntimeIndicatorSetOverride::Dot) => "● ◎ ▶ ○ ◐ ↺",
        Some(RuntimeIndicatorSetOverride::Diamond) => "◆ ◇ ▸ · ◈ ▸",
    }
}

fn glyph_set_label(set: Option<RuntimeGlyphSetOverride>) -> &'static str {
    match set {
        None => "Theme default",
        Some(RuntimeGlyphSetOverride::Unicode) => "Unicode",
        Some(RuntimeGlyphSetOverride::Ascii) => "ASCII",
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn colors_editor_initial_state() {
        let editor = ColorsEditorState::new(Theme::Codex);
        assert_eq!(editor.selected, 0);
        assert_eq!(editor.selected_field(), ColorField::Recording);
        assert!(editor.picker.is_none());
    }

    #[test]
    fn colors_editor_navigate_and_select() {
        let mut editor = ColorsEditorState::new(Theme::Codex);
        editor.select_next();
        editor.select_next();
        assert_eq!(editor.selected_field(), ColorField::Success);

        editor.select_prev();
        assert_eq!(editor.selected_field(), ColorField::Processing);
    }

    #[test]
    fn colors_editor_open_and_apply_picker() {
        let mut editor = ColorsEditorState::new(Theme::Codex);
        editor.open_picker();
        assert!(editor.picker.is_some());

        // Modify the picker color.
        if let Some(ref mut picker) = editor.picker {
            picker.rgb = Rgb { r: 255, g: 0, b: 0 };
        }
        editor.apply_picker();
        assert!(editor.picker.is_none());
        assert_eq!(
            editor.colors.recording,
            ColorValue::Rgb(Rgb { r: 255, g: 0, b: 0 })
        );
    }

    #[test]
    fn colors_editor_render_produces_lines() {
        let editor = ColorsEditorState::new(Theme::Codex);
        let lines = editor.render("", "", "");
        // 10 color fields + 1 separator + 2 indicator/glyph selectors = 13
        assert_eq!(lines.len(), ColorField::ALL.len() + 3);
        assert!(lines[0].contains("Recording"));
    }

    #[test]
    fn color_field_all_covers_10_fields() {
        assert_eq!(ColorField::ALL.len(), 10);
    }

    #[test]
    fn colors_editor_navigate_to_indicator_row() {
        let mut editor = ColorsEditorState::new(Theme::Codex);
        for _ in 0..11 {
            editor.select_next();
        }
        // Should be at glyph set row (index 11).
        assert_eq!(editor.selected, 11);
        assert!(!editor.is_color_field_selected());
    }

    #[test]
    fn cycle_indicator_set() {
        let mut editor = ColorsEditorState::new(Theme::Codex);
        assert!(editor.indicator_set.is_none());
        assert!(editor.cycle_indicator_set(1));
        assert_eq!(
            editor.indicator_set,
            Some(RuntimeIndicatorSetOverride::Ascii)
        );
        assert!(editor.cycle_indicator_set(1));
        assert_eq!(editor.indicator_set, Some(RuntimeIndicatorSetOverride::Dot));
        assert!(editor.cycle_indicator_set(-1));
        assert_eq!(
            editor.indicator_set,
            Some(RuntimeIndicatorSetOverride::Ascii)
        );
    }

    #[test]
    fn cycle_glyph_set() {
        let mut editor = ColorsEditorState::new(Theme::Codex);
        assert!(editor.glyph_set.is_none());
        assert!(editor.cycle_glyph_set(1));
        assert_eq!(editor.glyph_set, Some(RuntimeGlyphSetOverride::Unicode));
        assert!(editor.cycle_glyph_set(1));
        assert_eq!(editor.glyph_set, Some(RuntimeGlyphSetOverride::Ascii));
    }
}
