//! Status-line animation frames so recording/processing states feel alive.

use crate::theme::{
    heartbeat_frames, processing_spinner_symbol, transition_pulse_markers, GlyphSet, ThemeColors,
};
use std::time::{SystemTime, UNIX_EPOCH};

// Recording blink tuned to readable cadence:
// - 0.8 Hz (1250 ms period) keeps attention without looking jittery.
// - 70% ON / 30% OFF follows ISO 9241-303 guidance for readability during blinking.
const RECORDING_PULSE_PERIOD_MS: u64 = 1250;
const RECORDING_PULSE_ON_MS: u64 = 875;

/// Get the current animation frame based on system time.
/// Returns a frame index that cycles through the given frame count.
#[inline]
fn get_animation_frame(frame_count: usize, cycle_ms: u64) -> usize {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis() as u64)
        .unwrap_or(0);
    ((now / cycle_ms) % frame_count as u64) as usize
}

/// Get the processing spinner character.
#[inline]
pub(super) fn get_processing_spinner(colors: &ThemeColors) -> &'static str {
    let frame = get_animation_frame(10, 100);
    processing_spinner_symbol(colors, frame)
}

#[inline]
pub(super) fn heartbeat_frame_index(glyph_set: GlyphSet) -> usize {
    let frames = heartbeat_frames(glyph_set);
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default();
    (now.as_secs() % frames.len() as u64) as usize
}

pub(super) fn heartbeat_glyph(animate: bool, glyph_set: GlyphSet) -> (char, bool) {
    let frames = heartbeat_frames(glyph_set);
    let frame_idx = if animate {
        heartbeat_frame_index(glyph_set)
    } else {
        0
    };
    let glyph = frames.get(frame_idx).copied().unwrap_or(frames[0]);
    (glyph, frame_idx == 2)
}

#[inline]
pub(super) fn recording_pulse_on() -> bool {
    let now_ms = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis() as u64)
        .unwrap_or(0);
    recording_pulse_on_at(now_ms)
}

#[inline]
fn recording_pulse_on_at(now_ms: u64) -> bool {
    (now_ms % RECORDING_PULSE_PERIOD_MS) < RECORDING_PULSE_ON_MS
}

pub(super) fn transition_marker(progress: f32, glyph_set: GlyphSet) -> &'static str {
    let markers = transition_pulse_markers(glyph_set);
    if progress <= 0.0 {
        ""
    } else if progress > 0.66 {
        markers[0]
    } else if progress > 0.33 {
        markers[1]
    } else {
        ""
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::theme::Theme;
    use std::time::{Duration, Instant};

    const STATE_TRANSITION_DURATION: Duration = Duration::from_millis(360);

    fn state_transition_progress(started_at: Option<Instant>, now: Instant) -> f32 {
        let Some(started_at) = started_at else {
            return 0.0;
        };
        let elapsed = now.saturating_duration_since(started_at);
        if elapsed >= STATE_TRANSITION_DURATION {
            return 0.0;
        }
        let t = elapsed.as_secs_f32() / STATE_TRANSITION_DURATION.as_secs_f32();
        // Ease-out for a quick initial pulse that decays smoothly.
        let eased = 1.0 - (1.0 - t).powf(3.0);
        (1.0 - eased).clamp(0.0, 1.0)
    }

    #[test]
    fn processing_spinner_in_range() {
        let colors = Theme::Codex.colors();
        let indicator = get_processing_spinner(&colors);
        assert!(matches!(
            indicator,
            "⠋" | "⠙" | "⠹" | "⠸" | "⠼" | "⠴" | "⠦" | "⠧" | "⠇" | "⠏"
        ));
    }

    #[test]
    fn processing_spinner_respects_theme_override_symbol() {
        let mut colors = Theme::Codex.colors();
        colors.indicator_processing = "~";
        assert_eq!(get_processing_spinner(&colors), "~");
    }

    #[test]
    fn heartbeat_frame_index_in_range() {
        let frames = heartbeat_frames(crate::theme::GlyphSet::Unicode);
        let idx = heartbeat_frame_index(crate::theme::GlyphSet::Unicode);
        assert!(idx < frames.len());
    }

    #[test]
    fn transition_progress_is_bounded() {
        let now = Instant::now();
        let p_start = state_transition_progress(Some(now), now);
        let p_mid = state_transition_progress(Some(now), now + Duration::from_millis(160));
        let p_end = state_transition_progress(Some(now), now + Duration::from_millis(720));
        assert!((0.9..=1.0).contains(&p_start));
        assert!(p_mid > 0.0 && p_mid < 1.0);
        assert_eq!(p_end, 0.0);
    }

    #[test]
    fn transition_marker_steps_down() {
        assert_eq!(transition_marker(0.9, GlyphSet::Unicode), "✦");
        assert_eq!(transition_marker(0.5, GlyphSet::Unicode), "•");
        assert_eq!(transition_marker(0.1, GlyphSet::Unicode), "");
        assert_eq!(transition_marker(0.0, GlyphSet::Unicode), "");
    }

    #[test]
    fn recording_pulse_on_respects_on_off_windows_and_wrap() {
        assert!(recording_pulse_on_at(0));
        assert!(recording_pulse_on_at(RECORDING_PULSE_ON_MS - 1));
        assert!(!recording_pulse_on_at(RECORDING_PULSE_ON_MS));
        assert!(!recording_pulse_on_at(RECORDING_PULSE_PERIOD_MS - 1));
        assert!(recording_pulse_on_at(RECORDING_PULSE_PERIOD_MS));
        assert!(!recording_pulse_on_at(1_000));
    }

    #[test]
    fn transition_marker_thresholds_are_exclusive() {
        assert_eq!(transition_marker(0.66, GlyphSet::Unicode), "•");
        assert_eq!(transition_marker(0.33, GlyphSet::Unicode), "");
    }

    #[test]
    fn transition_marker_ascii_fallback() {
        assert_eq!(transition_marker(0.9, GlyphSet::Ascii), "*");
        assert_eq!(transition_marker(0.5, GlyphSet::Ascii), "*");
    }

    #[test]
    fn transition_progress_half_duration_matches_easing_curve() {
        let now = Instant::now();
        let half = now + Duration::from_millis(180);
        let progress = state_transition_progress(Some(now), half);
        assert!((progress - 0.125).abs() < 0.02, "progress={progress}");
    }
}
