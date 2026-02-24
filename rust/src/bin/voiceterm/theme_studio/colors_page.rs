//! Colors page: lists semantic color fields with live swatches.
//!
//! Users navigate a list of 10 semantic color fields and press Enter to open
//! the inline color picker for the selected field.

use crate::theme::color_value::{palette_to_resolved, ColorValue, ResolvedThemeColors, Rgb};
use crate::theme::{RuntimeGlyphSetOverride, RuntimeIndicatorSetOverride, Theme};

use super::color_picker::ColorPickerState;

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

/// Total navigable items: 10 color fields + 2 glyph/indicator selectors.
const TOTAL_ITEMS: usize = 12;

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
        Self {
            selected: 0,
            colors: palette_to_resolved(&theme.colors()),
            picker: None,
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

    /// Move selection up.
    pub(crate) fn move_up(&mut self) {
        if self.selected > 0 {
            self.selected -= 1;
        }
    }

    /// Move selection down.
    pub(crate) fn move_down(&mut self) {
        if self.selected < ColorField::ALL.len() - 1 {
            self.selected += 1;
        }
    }

    /// Render the colors page as lines.
    #[must_use]
    pub(crate) fn render(&self, fg_escape: &str, _dim_escape: &str, reset: &str) -> Vec<String> {
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
        editor.move_down();
        editor.move_down();
        assert_eq!(editor.selected_field(), ColorField::Success);

        editor.move_up();
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
        assert_eq!(lines.len(), ColorField::ALL.len());
        assert!(lines[0].contains("Recording"));
    }

    #[test]
    fn color_field_all_covers_10_fields() {
        assert_eq!(ColorField::ALL.len(), 10);
    }
}
