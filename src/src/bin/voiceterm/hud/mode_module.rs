//! HUD mode module so manual/auto/pipeline state is always explicit.
//!
//! Shows the current voice mode: "● AUTO", "○ MANUAL", or "◐ INSERT".

use super::{display_width, HudModule, HudState, Mode};
use crate::theme::GlyphSet;

/// Mode indicator module showing current voice mode.
pub struct ModeModule;

impl ModeModule {
    /// Create a new mode module.
    pub fn new() -> Self {
        Self
    }
}

impl Default for ModeModule {
    fn default() -> Self {
        Self::new()
    }
}

impl HudModule for ModeModule {
    fn id(&self) -> &'static str {
        "mode"
    }

    fn render(&self, state: &HudState, max_width: usize) -> String {
        if max_width < self.min_width() {
            return String::new();
        }

        let (indicator, label) = mode_indicator(state);

        let full = format!("{} {}", indicator, label);
        if display_width(&full) <= max_width {
            full
        } else if max_width >= 1 {
            // Just the indicator
            indicator.to_string()
        } else {
            String::new()
        }
    }

    fn min_width(&self) -> usize {
        // Minimum: indicator only
        1
    }

    fn priority(&self) -> u8 {
        90
    }
}

fn mode_indicator(state: &HudState) -> (&'static str, &'static str) {
    if state.is_recording {
        return match state.glyph_set {
            GlyphSet::Unicode => ("●", "REC"),
            GlyphSet::Ascii => ("*", "REC"),
        };
    }

    match (state.mode, state.glyph_set) {
        (Mode::Auto, GlyphSet::Unicode) => ("◉", "AUTO"),
        (Mode::Manual, GlyphSet::Unicode) => ("○", "MANUAL"),
        (Mode::Insert, GlyphSet::Unicode) => ("◐", "INSERT"),
        (Mode::Auto, GlyphSet::Ascii) => ("@", "AUTO"),
        (Mode::Manual, GlyphSet::Ascii) => (">", "MANUAL"),
        (Mode::Insert, GlyphSet::Ascii) => ("~", "INSERT"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mode_module_id() {
        let module = ModeModule::new();
        assert_eq!(module.id(), "mode");
    }

    #[test]
    fn mode_module_min_width() {
        let module = ModeModule::new();
        assert_eq!(module.min_width(), 1);
    }

    #[test]
    fn mode_module_render_auto() {
        let module = ModeModule::new();
        let state = HudState {
            mode: Mode::Auto,
            ..Default::default()
        };
        let output = module.render(&state, 10);
        assert!(output.contains("AUTO"));
        assert!(output.contains("◉"));
    }

    #[test]
    fn mode_module_render_manual() {
        let module = ModeModule::new();
        let state = HudState {
            mode: Mode::Manual,
            ..Default::default()
        };
        let output = module.render(&state, 10);
        assert!(output.contains("MANUAL"));
        assert!(output.contains("○"));
    }

    #[test]
    fn mode_module_render_recording() {
        let module = ModeModule::new();
        let state = HudState {
            mode: Mode::Auto,
            is_recording: true,
            ..Default::default()
        };
        let output = module.render(&state, 10);
        assert!(output.contains("REC"));
        assert!(output.contains("●"));
    }

    #[test]
    fn mode_module_render_narrow() {
        let module = ModeModule::new();
        let state = HudState::default();
        // Narrow widths still show indicator
        let output = module.render(&state, 2);
        assert!(!output.is_empty());
    }

    #[test]
    fn mode_module_render_just_indicator() {
        let module = ModeModule::new();
        let state = HudState {
            mode: Mode::Auto,
            ..Default::default()
        };
        // Just enough for indicator
        let output = module.render(&state, 1);
        assert_eq!(output, "◉");
    }

    #[test]
    fn mode_module_respects_ascii_glyph_set() {
        let module = ModeModule::new();
        let state = HudState {
            mode: Mode::Manual,
            glyph_set: GlyphSet::Ascii,
            ..Default::default()
        };
        let output = module.render(&state, 10);
        assert_eq!(output, "> MANUAL");

        let recording = HudState {
            mode: Mode::Manual,
            is_recording: true,
            glyph_set: GlyphSet::Ascii,
            ..Default::default()
        };
        assert_eq!(module.render(&recording, 10), "* REC");
    }
}
