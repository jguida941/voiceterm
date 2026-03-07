use crate::audio_meter::format_waveform;

use super::*;

pub(super) fn format_transition_suffix(state: &StatusLineState, colors: &ThemeColors) -> String {
    if state.recording_state != RecordingState::Idle || state.transition_progress <= 0.0 {
        return String::new();
    }
    let marker = transition_marker(state.transition_progress);
    if marker.is_empty() {
        String::new()
    } else {
        format!(" {}{}{}", colors.info, marker, colors.reset)
    }
}

pub(super) fn format_right_shortcuts(colors: &ThemeColors, width: usize) -> String {
    if width >= breakpoints::FULL {
        format_shortcuts(colors)
    } else if width >= breakpoints::MEDIUM {
        format_shortcuts_compact(colors)
    } else {
        String::new()
    }
}

pub(super) fn format_left_section(state: &StatusLineState, colors: &ThemeColors) -> String {
    let transition = format_transition_suffix(state, colors);
    let mode_label = match state.recording_state {
        RecordingState::Recording => format!("REC{transition}"),
        RecordingState::Processing => format!("processing{transition}"),
        RecordingState::Responding => format!("RESP{transition}"),
        RecordingState::Idle => {
            format!("{}{}", full_mode_voice_label(state.voice_mode), transition)
        }
    };

    let sensitivity = format!("{:.0}dB", state.sensitivity_db);

    let duration_part = if let Some(dur) = state.recording_duration {
        format!(" {:.1}s", dur)
    } else {
        String::new()
    };

    match state.recording_state {
        RecordingState::Recording => {
            let indicator = with_color(
                recording_mode_indicator(state.voice_mode, colors),
                recording_indicator_color(colors),
                colors,
            );
            let label = with_color(&mode_label, colors.recording, colors);
            format!("{indicator} {label} │ {sensitivity}{duration_part}")
        }
        RecordingState::Processing => {
            let indicator =
                with_color(processing_mode_indicator(colors), colors.processing, colors);
            let label = with_color(&mode_label, colors.processing, colors);
            format!("{indicator} {label} │ {sensitivity}{duration_part}")
        }
        RecordingState::Responding => {
            let indicator = with_color(colors.indicator_responding, colors.info, colors);
            let label = with_color(&mode_label, colors.info, colors);
            format!("{indicator} {label} │ {sensitivity}{duration_part}")
        }
        RecordingState::Idle => {
            let (idle_indicator, idle_color) = idle_mode_indicator(state.voice_mode, colors);
            let indicator = with_color(idle_indicator, idle_color, colors);
            if idle_color.is_empty() {
                format!("{indicator} {mode_label} │ {sensitivity}{duration_part}")
            } else {
                let label = with_color(&mode_label, idle_color, colors);
                format!("{indicator} {label} │ {sensitivity}{duration_part}")
            }
        }
    }
}

pub(super) fn format_message(
    state: &StatusLineState,
    colors: &ThemeColors,
    theme: Theme,
    width: usize,
) -> String {
    let mut message = if state.message.is_empty() {
        String::new()
    } else {
        state.message.clone()
    };

    if let Some(preview) = state.transcript_preview.as_ref() {
        if message.is_empty() {
            message = preview.clone();
        } else {
            message = format!("{message} \"{preview}\"");
        }
    }

    if message.is_empty() {
        return message;
    }

    let mut prefix = String::new();
    if state.recording_state == RecordingState::Recording && !state.meter_levels.is_empty() {
        let wave_width = if width >= breakpoints::FULL {
            10
        } else if width >= breakpoints::MEDIUM {
            8
        } else {
            6
        };
        let waveform = format_waveform(&state.meter_levels, wave_width, theme);
        if let Some(db) = state.meter_db {
            prefix = format!("{} {}{:>4.0}dB{} ", waveform, colors.info, db, colors.reset);
        } else {
            prefix = format!("{waveform} ");
        }
    }

    let status_type = StatusType::from_message(&message);
    let color = status_type.color(colors);
    let colored_message = if color.is_empty() {
        message
    } else {
        format!("{}{}{}", color, message, colors.reset)
    };

    format!("{prefix}{colored_message}")
}

pub(super) fn format_shortcuts(colors: &ThemeColors) -> String {
    let sep = format!(" {}│{} ", colors.dim, colors.reset);
    format_shortcuts_list(colors, SHORTCUTS, &sep)
}

pub(super) fn format_shortcuts_list(
    colors: &ThemeColors,
    shortcuts: &[(&str, &str)],
    separator: &str,
) -> String {
    let mut parts = Vec::with_capacity(shortcuts.len());
    for (key, action) in shortcuts {
        parts.push(format!("{}{}{} {}", colors.dim, key, colors.reset, action));
    }
    parts.join(separator)
}
