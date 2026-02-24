//! HUD latency module so recent transcription latency remains visible to users.
//!
//! Shows the last transcription latency: "◷ 1.2s"

use super::{display_width, HudModule, HudState};
use crate::theme::{hud_latency_icon, waveform_bars};

/// Latency indicator module showing last transcription time.
pub struct LatencyModule;

impl LatencyModule {
    /// Create a new latency module.
    pub fn new() -> Self {
        Self
    }

    fn latency_char(ms: u32, state: &HudState) -> char {
        let bars = waveform_bars(state.glyph_set);
        let idx = match ms {
            0..=150 => 0,
            151..=300 => 1,
            301..=500 => 3,
            501..=800 => 5,
            _ => 7,
        };
        bars[idx]
    }

    fn render_sparkline(history: &[u32], width: usize, state: &HudState) -> String {
        if history.is_empty() || width == 0 {
            return String::new();
        }
        let bars = waveform_bars(state.glyph_set);
        let mut out = String::with_capacity(width);
        let start = history.len().saturating_sub(width);
        let slice = &history[start..];
        let padding = width.saturating_sub(slice.len());
        if padding != 0 {
            out.push_str(&bars[0].to_string().repeat(padding));
        }
        for sample in slice {
            out.push(Self::latency_char(*sample, state));
        }
        out
    }
}

impl Default for LatencyModule {
    fn default() -> Self {
        Self::new()
    }
}

impl HudModule for LatencyModule {
    fn id(&self) -> &'static str {
        "latency"
    }

    fn render(&self, state: &HudState, max_width: usize) -> String {
        if max_width < self.min_width() {
            return String::new();
        }

        match state.last_latency_ms {
            Some(ms) => {
                let secs = ms as f32 / 1000.0;
                let icon = hud_latency_icon(state.glyph_set);
                let trend = if state.latency_history_ms.is_empty() {
                    Self::latency_char(ms, state).to_string()
                } else {
                    Self::render_sparkline(&state.latency_history_ms, 4, state)
                };
                let full = if secs >= 10.0 {
                    format!("{icon} {:.0}s {trend}", secs)
                } else {
                    format!("{icon} {:.1}s {trend}", secs)
                };

                if display_width(&full) <= max_width {
                    full
                } else if max_width >= 7 {
                    // Compact format with decimal precision + single trend marker.
                    format!("{icon}{:.1}s{}", secs, Self::latency_char(ms, state))
                } else if max_width >= 6 {
                    // Ultra compact format without decimal + trend marker.
                    format!("{icon}{:.0}s{}", secs, Self::latency_char(ms, state))
                } else if max_width >= 4 {
                    format!("{icon}{:.0}s", secs)
                } else {
                    String::new()
                }
            }
            None => String::new(),
        }
    }

    fn min_width(&self) -> usize {
        // Minimum: "◷ --" = 4 chars
        4
    }

    fn priority(&self) -> u8 {
        220
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn latency_module_id() {
        let module = LatencyModule::new();
        assert_eq!(module.id(), "latency");
    }

    #[test]
    fn latency_module_min_width() {
        let module = LatencyModule::new();
        assert_eq!(module.min_width(), 4);
    }

    #[test]
    fn latency_module_priority_is_stable() {
        let module = LatencyModule::new();
        assert_eq!(module.priority(), 220);
    }

    #[test]
    fn latency_module_tick_interval() {
        let module = LatencyModule::new();
        // Latency is event-driven, no tick
        assert!(module.tick_interval().is_none());
    }

    #[test]
    fn latency_module_render_no_data() {
        let module = LatencyModule::new();
        let state = HudState {
            last_latency_ms: None,
            ..Default::default()
        };
        let output = module.render(&state, 10);
        assert!(output.is_empty());
    }

    #[test]
    fn latency_module_render_with_data() {
        let module = LatencyModule::new();
        let state = HudState {
            last_latency_ms: Some(1200),
            latency_history_ms: vec![220, 350, 900, 1200],
            ..Default::default()
        };
        let output = module.render(&state, 10);
        assert!(output.contains("◷"));
        assert!(output.contains("1.2s") || output.contains("1s"));
    }

    #[test]
    fn latency_module_render_fast() {
        let module = LatencyModule::new();
        let state = HudState {
            last_latency_ms: Some(500),
            latency_history_ms: vec![100, 180, 250, 500],
            ..Default::default()
        };
        let output = module.render(&state, 10);
        assert!(output.contains("0.5s") || output.contains("1s"));
    }

    #[test]
    fn latency_module_render_slow() {
        let module = LatencyModule::new();
        let state = HudState {
            last_latency_ms: Some(15000),
            latency_history_ms: vec![700, 900, 1200, 15000],
            ..Default::default()
        };
        let output = module.render(&state, 10);
        // Should show whole seconds for 10+
        assert!(output.contains("15s"));
    }

    #[test]
    fn latency_module_render_narrow() {
        let module = LatencyModule::new();
        let state = HudState {
            last_latency_ms: Some(1200),
            ..Default::default()
        };
        // Too narrow
        let output = module.render(&state, 3);
        assert!(output.is_empty());
    }

    #[test]
    fn latency_module_render_at_min_width_shows_compact_value() {
        let module = LatencyModule::new();
        let state = HudState {
            last_latency_ms: Some(2500),
            latency_history_ms: vec![200, 350, 500, 2500],
            ..Default::default()
        };
        let output = module.render(&state, 4);
        assert!(!output.is_empty());
        assert!(output.contains("s"));
        assert!(display_width(&output) <= 4);
    }

    #[test]
    fn latency_module_render_width_six_includes_trend_marker() {
        let module = LatencyModule::new();
        let state = HudState {
            last_latency_ms: Some(2500),
            latency_history_ms: vec![200, 350, 500, 2500],
            ..Default::default()
        };
        let output = module.render(&state, 6);
        let expected_trend = LatencyModule::latency_char(2500, &state);
        assert!(!output.is_empty());
        assert!(output.contains("s"));
        assert_eq!(output.chars().last(), Some(expected_trend));
        assert!(display_width(&output) <= 6);
    }

    #[test]
    fn latency_module_render_compact() {
        let module = LatencyModule::new();
        let state = HudState {
            last_latency_ms: Some(1200),
            latency_history_ms: vec![200, 350, 500, 1200],
            ..Default::default()
        };
        // Just enough for compact+trend
        let output = module.render(&state, 6);
        assert!(output.contains("◷"));
        assert!(output.contains("s"));
    }

    #[test]
    fn latency_module_uses_history_sparkline() {
        let module = LatencyModule::new();
        let state = HudState {
            last_latency_ms: Some(800),
            latency_history_ms: vec![120, 220, 450, 820],
            ..Default::default()
        };
        let output = module.render(&state, 16);
        assert!(output.contains('▁') || output.contains('▂') || output.contains('▄'));
    }

    #[test]
    fn latency_module_respects_ascii_glyph_set() {
        let module = LatencyModule::new();
        let state = HudState {
            glyph_set: crate::theme::GlyphSet::Ascii,
            last_latency_ms: Some(1200),
            latency_history_ms: vec![120, 220, 450, 820],
            ..Default::default()
        };
        let output = module.render(&state, 16);
        assert!(output.contains('T'));
        assert!(output.contains('.') || output.contains(':') || output.contains('-'));
    }

    #[test]
    fn latency_char_threshold_buckets_map_to_expected_bars() {
        let state = HudState::default();
        let bars = waveform_bars(state.glyph_set);

        assert_eq!(LatencyModule::latency_char(150, &state), bars[0]);
        assert_eq!(LatencyModule::latency_char(151, &state), bars[1]);
        assert_eq!(LatencyModule::latency_char(300, &state), bars[1]);
        assert_eq!(LatencyModule::latency_char(301, &state), bars[3]);
        assert_eq!(LatencyModule::latency_char(500, &state), bars[3]);
        assert_eq!(LatencyModule::latency_char(501, &state), bars[5]);
        assert_eq!(LatencyModule::latency_char(800, &state), bars[5]);
        assert_eq!(LatencyModule::latency_char(801, &state), bars[7]);
    }

    #[test]
    fn render_sparkline_returns_empty_for_empty_history_or_zero_width() {
        let state = HudState::default();
        assert!(LatencyModule::render_sparkline(&[], 4, &state).is_empty());
        assert!(LatencyModule::render_sparkline(&[120, 220], 0, &state).is_empty());
    }

    #[test]
    fn render_sparkline_left_pads_short_history_with_floor_bar() {
        let state = HudState::default();
        let bars = waveform_bars(state.glyph_set);
        let rendered = LatencyModule::render_sparkline(&[220, 700], 4, &state);
        let expected = format!(
            "{}{}{}{}",
            bars[0],
            bars[0],
            LatencyModule::latency_char(220, &state),
            LatencyModule::latency_char(700, &state)
        );
        assert_eq!(rendered, expected);
    }
}
