//! Shared mode-indicator helpers used by both full and minimal HUD renderers.

use crate::theme::{filled_indicator, ThemeColors};

use super::animation::{get_processing_spinner, recording_pulse_on};
use super::state::VoiceMode;

#[inline]
fn base_mode_indicator(mode: VoiceMode, colors: &ThemeColors) -> &'static str {
    match mode {
        VoiceMode::Auto => colors.indicator_auto,
        VoiceMode::Manual => colors.indicator_manual,
        VoiceMode::Idle => colors.indicator_idle,
    }
}

#[inline]
pub(super) fn full_mode_voice_label(mode: VoiceMode) -> &'static str {
    match mode {
        VoiceMode::Auto => "AUTO",
        VoiceMode::Manual => "PTT",
        VoiceMode::Idle => "IDLE",
    }
}

#[inline]
pub(super) fn idle_mode_indicator(
    mode: VoiceMode,
    colors: &ThemeColors,
) -> (&'static str, &'static str) {
    match mode {
        VoiceMode::Auto => (colors.indicator_auto, colors.info),
        VoiceMode::Manual => (colors.indicator_manual, ""),
        VoiceMode::Idle => (colors.indicator_idle, ""),
    }
}

#[inline]
pub(super) fn recording_mode_indicator(mode: VoiceMode, colors: &ThemeColors) -> &'static str {
    filled_indicator(base_mode_indicator(mode, colors))
}

#[inline]
pub(super) fn recording_indicator_color(colors: &ThemeColors) -> &str {
    if recording_pulse_on() {
        colors.recording
    } else {
        colors.dim
    }
}

#[inline]
pub(super) fn processing_mode_indicator(colors: &ThemeColors) -> &str {
    get_processing_spinner(colors)
}
