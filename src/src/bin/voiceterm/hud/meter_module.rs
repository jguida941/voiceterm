//! HUD meter module so live microphone levels surface in the status panel.
//!
//! Shows the current audio level with a visual waveform: "-40dB ▁▂▃▅▆"

use super::{display_width, HudModule, HudState};
use crate::theme::waveform_bars;
use std::time::Duration;

/// Audio meter module showing current audio level.
pub struct MeterModule {
    /// Number of waveform bars to show.
    bar_count: usize,
}

impl MeterModule {
    /// Create a new meter module with default settings.
    pub fn new() -> Self {
        Self { bar_count: 6 }
    }

    /// Create a meter module with a specific bar count.
    #[allow(dead_code)]
    pub fn with_bar_count(bar_count: usize) -> Self {
        Self {
            bar_count: bar_count.max(1),
        }
    }

    /// Convert a dB level to a waveform character.
    fn db_to_char(db: f32, bars: &[char; 8]) -> char {
        // Map -60dB to 0dB to waveform characters
        let normalized = ((db + 60.0) / 60.0).clamp(0.0, 1.0);
        let idx = (normalized * (bars.len() - 1) as f32) as usize;
        bars[idx]
    }

    fn render_sparkline(levels: &[f32], bar_count: usize, bars: &[char; 8]) -> String {
        if levels.is_empty() || bar_count == 0 {
            return String::new();
        }
        let mut out = String::with_capacity(bar_count);
        let start = levels.len().saturating_sub(bar_count);
        let slice = &levels[start..];
        let padding = bar_count.saturating_sub(slice.len());
        if padding != 0 {
            out.push_str(&bars[0].to_string().repeat(padding));
        }
        for level in slice {
            out.push(Self::db_to_char(*level, bars));
        }
        out
    }
}

impl Default for MeterModule {
    fn default() -> Self {
        Self::new()
    }
}

impl HudModule for MeterModule {
    fn id(&self) -> &'static str {
        "meter"
    }

    fn render(&self, state: &HudState, max_width: usize) -> String {
        if max_width < self.min_width() {
            return String::new();
        }

        // Only show meter when recording
        if !state.is_recording {
            return String::new();
        }

        let db = state.audio_level_db;
        let db_str = format!("{:>3.0}dB", db);
        let bars = waveform_bars(state.glyph_set);

        // Render a richer sparkline from recent samples when available.
        let waveform = if state.audio_levels.is_empty() {
            let waveform_char = Self::db_to_char(db, bars);
            std::iter::repeat_n(waveform_char, self.bar_count).collect()
        } else {
            Self::render_sparkline(&state.audio_levels, self.bar_count, bars)
        };

        let full = format!("{} {}", db_str, waveform);
        if display_width(&full) <= max_width {
            full
        } else if max_width >= 5 {
            // Just the dB value
            db_str
        } else {
            String::new()
        }
    }

    fn min_width(&self) -> usize {
        // Minimum: "-40dB" = 5 chars
        5
    }

    fn tick_interval(&self) -> Option<Duration> {
        // Update meter at ~12fps for smooth animation
        Some(Duration::from_millis(80))
    }

    fn priority(&self) -> u8 {
        70
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn meter_module_id() {
        let module = MeterModule::new();
        assert_eq!(module.id(), "meter");
    }

    #[test]
    fn meter_module_min_width() {
        let module = MeterModule::new();
        assert_eq!(module.min_width(), 5);
    }

    #[test]
    fn meter_module_priority_is_stable() {
        let module = MeterModule::new();
        assert_eq!(module.priority(), 70);
    }

    #[test]
    fn meter_module_tick_interval() {
        let module = MeterModule::new();
        assert!(module.tick_interval().is_some());
        assert_eq!(module.tick_interval(), Some(Duration::from_millis(80)));
    }

    #[test]
    fn meter_module_render_not_recording() {
        let module = MeterModule::new();
        let state = HudState {
            is_recording: false,
            audio_level_db: -30.0,
            ..Default::default()
        };
        let output = module.render(&state, 20);
        assert!(output.is_empty());
    }

    #[test]
    fn meter_module_render_recording() {
        let module = MeterModule::new();
        let state = HudState {
            is_recording: true,
            audio_level_db: -30.0,
            ..Default::default()
        };
        let output = module.render(&state, 20);
        assert!(output.contains("-30dB") || output.contains("30dB"));
        // Should have waveform chars
        let has_waveform = waveform_bars(state.glyph_set)
            .iter()
            .any(|&c| output.contains(c));
        assert!(has_waveform);
    }

    #[test]
    fn meter_module_render_loud() {
        let module = MeterModule::new();
        let state = HudState {
            is_recording: true,
            audio_level_db: -10.0,
            ..Default::default()
        };
        let output = module.render(&state, 20);
        // Loud signal should show higher bars
        let bars = waveform_bars(state.glyph_set);
        assert!(output.contains(bars[7]) || output.contains(bars[6]) || output.contains(bars[5]));
    }

    #[test]
    fn meter_module_render_quiet() {
        let module = MeterModule::new();
        let state = HudState {
            is_recording: true,
            audio_level_db: -55.0,
            ..Default::default()
        };
        let output = module.render(&state, 20);
        // Quiet signal should show lower bars
        let bars = waveform_bars(state.glyph_set);
        assert!(output.contains(bars[0]) || output.contains(bars[1]));
    }

    #[test]
    fn meter_module_render_narrow() {
        let module = MeterModule::new();
        let state = HudState {
            is_recording: true,
            audio_level_db: -30.0,
            ..Default::default()
        };
        // Too narrow
        let output = module.render(&state, 4);
        assert!(output.is_empty());
    }

    #[test]
    fn meter_module_render_just_db() {
        let module = MeterModule::new();
        let state = HudState {
            is_recording: true,
            audio_level_db: -30.0,
            ..Default::default()
        };
        // Just enough for dB
        let output = module.render(&state, 5);
        assert!(output.contains("dB"));
    }

    #[test]
    fn db_to_char_range() {
        // Test the full range
        assert_eq!(
            MeterModule::db_to_char(-60.0, waveform_bars(crate::theme::GlyphSet::Unicode)),
            '▁'
        );
        assert_eq!(
            MeterModule::db_to_char(0.0, waveform_bars(crate::theme::GlyphSet::Unicode)),
            '█'
        );
        // Middle value
        let mid = MeterModule::db_to_char(-30.0, waveform_bars(crate::theme::GlyphSet::Unicode));
        assert!(waveform_bars(crate::theme::GlyphSet::Unicode).contains(&mid));
    }

    #[test]
    fn custom_bar_count() {
        let module = MeterModule::with_bar_count(10);
        let state = HudState {
            is_recording: true,
            audio_level_db: -30.0,
            ..Default::default()
        };
        let output = module.render(&state, 30);
        // Count waveform chars (excluding dB label)
        let bars = waveform_bars(state.glyph_set);
        let waveform_count = output.chars().filter(|c| bars.contains(c)).count();
        assert_eq!(waveform_count, 10);
    }

    #[test]
    fn meter_module_render_history_sparkline_varies() {
        let module = MeterModule::with_bar_count(6);
        let state = HudState {
            is_recording: true,
            audio_level_db: -20.0,
            audio_levels: vec![-58.0, -50.0, -42.0, -35.0, -20.0, -8.0],
            ..Default::default()
        };
        let output = module.render(&state, 40);
        let bars = waveform_bars(state.glyph_set);
        let waveform: String = output.chars().filter(|c| bars.contains(c)).collect();
        let distinct = waveform.chars().collect::<std::collections::BTreeSet<_>>();
        assert!(distinct.len() > 1);
    }

    #[test]
    fn meter_module_respects_ascii_glyph_set() {
        let module = MeterModule::new();
        let state = HudState {
            is_recording: true,
            glyph_set: crate::theme::GlyphSet::Ascii,
            audio_level_db: -22.0,
            audio_levels: vec![-58.0, -47.0, -36.0, -24.0, -16.0, -8.0],
            ..Default::default()
        };
        let output = module.render(&state, 40);
        let ascii_bars = waveform_bars(crate::theme::GlyphSet::Ascii);
        assert!(ascii_bars.iter().any(|&c| output.contains(c)));
        assert!(!output.contains('▁'));
    }

    #[test]
    fn render_sparkline_returns_empty_for_empty_levels_or_zero_bar_count() {
        let bars = waveform_bars(crate::theme::GlyphSet::Unicode);
        assert!(MeterModule::render_sparkline(&[], 4, bars).is_empty());
        assert!(MeterModule::render_sparkline(&[-20.0], 0, bars).is_empty());
    }

    #[test]
    fn render_sparkline_left_pads_short_history_to_target_width() {
        let bars = waveform_bars(crate::theme::GlyphSet::Unicode);
        let rendered = MeterModule::render_sparkline(&[-35.0, -20.0], 6, bars);
        assert_eq!(rendered.chars().count(), 6);
        assert_eq!(
            rendered.chars().take(4).collect::<String>(),
            bars[0].to_string().repeat(4)
        );
    }

    #[test]
    fn render_sparkline_exact_history_width_adds_no_padding() {
        let bars = waveform_bars(crate::theme::GlyphSet::Unicode);
        let levels = [-20.0, -18.0, -16.0, -14.0, -12.0, -10.0];
        let rendered = MeterModule::render_sparkline(&levels, 6, bars);
        assert_eq!(rendered.chars().count(), 6);
        assert_ne!(rendered.chars().next(), Some(bars[0]));
    }
}
