use crate::config::LatencyDisplayMode;
use crate::theme::ThemeColors;

use super::super::state::{RecordingState, StatusLineState, WakeWordHudState};

// Speech-relative STT speed bands (RTF scaled by 1000, e.g. 250 => 0.25x realtime).
pub(super) const LATENCY_RTF_WARNING_X1000: u32 = 350;
pub(super) const LATENCY_RTF_ERROR_X1000: u32 = 650;

pub(super) fn format_queue_badge(state: &StatusLineState, colors: &ThemeColors) -> Option<String> {
    (state.queue_depth > 0)
        .then(|| format!("{}Q:{}{}", colors.warning, state.queue_depth, colors.reset))
}

pub(super) fn format_wake_badge(state: &StatusLineState, colors: &ThemeColors) -> Option<String> {
    match state.wake_word_state {
        WakeWordHudState::Off => None,
        WakeWordHudState::Listening => Some(format!("{}Wake: ON{}", colors.success, colors.reset)),
        WakeWordHudState::Paused => Some(format!("{}Wake: PAUSED{}", colors.warning, colors.reset)),
        WakeWordHudState::Unavailable => Some(format!("{}Wake: ERR{}", colors.error, colors.reset)),
    }
}

pub(super) fn format_image_badge(state: &StatusLineState, colors: &ThemeColors) -> Option<String> {
    state
        .image_mode_enabled
        .then(|| format!("{}IMG{}", colors.info, colors.reset))
}

pub(super) fn format_dev_badge(state: &StatusLineState, colors: &ThemeColors) -> Option<String> {
    state
        .dev_mode_enabled
        .then(|| format!("{}DEV{}", colors.warning, colors.reset))
}

pub(super) fn format_ready_badge(
    state: &StatusLineState,
    colors: &ThemeColors,
    enabled: bool,
) -> Option<String> {
    (enabled && state.recording_state == RecordingState::Idle && state.queue_depth == 0)
        .then(|| format!("{}Ready{}", colors.success, colors.reset))
}

#[derive(Copy, Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub(super) enum LatencySeverity {
    Success,
    Warning,
    Error,
}

fn absolute_latency_severity(latency: u32) -> LatencySeverity {
    if latency < 300 {
        LatencySeverity::Success
    } else if latency < 500 {
        LatencySeverity::Warning
    } else {
        LatencySeverity::Error
    }
}

pub(super) fn rtf_latency_severity(rtf_x1000: u32) -> LatencySeverity {
    if rtf_x1000 < LATENCY_RTF_WARNING_X1000 {
        LatencySeverity::Success
    } else if rtf_x1000 < LATENCY_RTF_ERROR_X1000 {
        LatencySeverity::Warning
    } else {
        LatencySeverity::Error
    }
}

fn latency_severity(state: &StatusLineState, latency: u32) -> LatencySeverity {
    let absolute = absolute_latency_severity(latency);
    state
        .last_latency_rtf_x1000
        .map(rtf_latency_severity)
        .map_or(absolute, |relative| absolute.max(relative))
}

fn latency_badge_color<'a>(
    state: &StatusLineState,
    colors: &'a ThemeColors,
    latency: u32,
) -> &'a str {
    match latency_severity(state, latency) {
        LatencySeverity::Success => colors.success,
        LatencySeverity::Warning => colors.warning,
        LatencySeverity::Error => colors.error,
    }
}

pub(super) fn format_latency_badge(
    state: &StatusLineState,
    colors: &ThemeColors,
    respect_display_mode: bool,
) -> Option<String> {
    if matches!(
        state.recording_state,
        RecordingState::Recording | RecordingState::Processing
    ) {
        return None;
    }
    let latency = state.last_latency_ms?;
    let text = if respect_display_mode {
        match state.latency_display {
            LatencyDisplayMode::Short => format!("{latency}ms"),
            LatencyDisplayMode::Label => format!("Latency: {latency}ms"),
            LatencyDisplayMode::Off => return None,
        }
    } else {
        format!("{latency}ms")
    };
    Some(format!(
        "{}{}{}",
        latency_badge_color(state, colors, latency),
        text,
        colors.reset
    ))
}
