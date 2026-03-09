use std::sync::OnceLock;

use crate::hud::{HudRegistry, HudState, LatencyModule, MeterModule, Mode as HudMode, QueueModule};

use super::single_line::{format_message, format_shortcuts_list, format_transition_suffix};
use super::*;

struct CompactModeParts<'a> {
    indicator: &'a str,
    label: &'a str,
    color: &'a str,
}

fn compact_mode_parts<'a>(
    state: &'a StatusLineState,
    colors: &'a ThemeColors,
) -> CompactModeParts<'a> {
    match state.recording_state {
        RecordingState::Recording => CompactModeParts {
            indicator: recording_mode_indicator(state.voice_mode, colors),
            label: "",
            color: recording_indicator_color(colors),
        },
        RecordingState::Processing => CompactModeParts {
            indicator: processing_mode_indicator(colors),
            label: "",
            color: colors.processing,
        },
        RecordingState::Responding => CompactModeParts {
            indicator: colors.indicator_responding,
            label: "",
            color: colors.info,
        },
        RecordingState::Idle => {
            let (indicator, color, label) = match state.voice_mode {
                VoiceMode::Auto => (colors.indicator_auto, colors.info, "A"),
                VoiceMode::Manual => (colors.indicator_manual, "", "M"),
                VoiceMode::Idle => (colors.indicator_idle, "", ""),
            };
            CompactModeParts {
                indicator,
                label,
                color,
            }
        }
    }
}

fn format_compact_indicator(parts: &CompactModeParts<'_>, colors: &ThemeColors) -> String {
    if parts.color.is_empty() {
        parts.indicator.to_string()
    } else {
        format!("{}{}{}", parts.color, parts.indicator, colors.reset)
    }
}

fn format_compact_mode(parts: &CompactModeParts<'_>, colors: &ThemeColors) -> String {
    if parts.label.is_empty() {
        format_compact_indicator(parts, colors)
    } else if parts.color.is_empty() {
        format!("{} {}", parts.indicator, parts.label)
    } else {
        format!(
            "{}{} {}{}",
            parts.color, parts.indicator, parts.label, colors.reset
        )
    }
}

/// Format minimal status for very narrow terminals.
pub(super) fn format_minimal(
    state: &StatusLineState,
    colors: &ThemeColors,
    width: usize,
) -> String {
    let indicator = format_compact_indicator(&compact_mode_parts(state, colors), colors);

    let msg = if state.message.is_empty() {
        if state.voice_mode == VoiceMode::Auto {
            "auto".to_string()
        } else {
            format!("{}Ready{}", colors.success, colors.reset)
        }
    } else {
        state.message.clone()
    };

    let available = width.saturating_sub(2);
    format!("{} {}", indicator, truncate_display(&msg, available))
}

/// Format compact status for narrow terminals.
pub(super) fn format_compact(
    state: &StatusLineState,
    colors: &ThemeColors,
    theme: Theme,
    width: usize,
) -> String {
    let mode = format_compact_mode(&compact_mode_parts(state, colors), colors);
    let mode_width = display_width(&mode);
    let module_budget = width.saturating_sub(mode_width + 1);

    let registry = compact_hud_registry(state, module_budget);
    let hud_state = HudState {
        mode: match state.voice_mode {
            VoiceMode::Auto => HudMode::Auto,
            VoiceMode::Manual => HudMode::Manual,
            VoiceMode::Idle => HudMode::Insert,
        },
        is_recording: state.recording_state == RecordingState::Recording,
        audio_level_db: state.meter_db.unwrap_or(-60.0),
        audio_levels: state.meter_levels.clone(),
        queue_depth: state.queue_depth,
        last_latency_ms: state.last_latency_ms,
        latency_history_ms: state.latency_history_ms.clone(),
        glyph_set: colors.glyph_set,
    };
    let modules = registry.render_all(
        &hud_state,
        module_budget,
        &format!(" {} ", overlay_separator(colors.glyph_set)),
    );
    let left = if modules.is_empty() {
        mode
    } else {
        format!("{} {}", mode, modules)
    };

    let msg = format_message(state, colors, theme, width);
    let left_width = display_width(&left);
    let available = width.saturating_sub(left_width + 1);
    format!("{} {}", left, truncate_display(&msg, available))
}

#[derive(Debug, Clone, Copy)]
enum CompactHudProfile {
    Recording,
    Busy,
    Idle,
}

pub(super) fn compact_hud_registry(
    state: &StatusLineState,
    module_budget: usize,
) -> &'static HudRegistry {
    let profile = if state.recording_state == RecordingState::Recording && module_budget >= 12 {
        CompactHudProfile::Recording
    } else if state.queue_depth > 0 {
        CompactHudProfile::Busy
    } else {
        CompactHudProfile::Idle
    };
    compact_hud_registry_for_profile(profile)
}

fn compact_hud_registry_for_profile(profile: CompactHudProfile) -> &'static HudRegistry {
    static RECORDING: OnceLock<HudRegistry> = OnceLock::new();
    static BUSY: OnceLock<HudRegistry> = OnceLock::new();
    static IDLE: OnceLock<HudRegistry> = OnceLock::new();

    match profile {
        CompactHudProfile::Recording => RECORDING.get_or_init(|| {
            let mut registry = HudRegistry::new();
            registry.register(Box::new(MeterModule::with_bar_count(8)));
            registry.register(Box::new(LatencyModule::new()));
            registry.register(Box::new(QueueModule::new()));
            registry
        }),
        CompactHudProfile::Busy => BUSY.get_or_init(|| {
            let mut registry = HudRegistry::new();
            registry.register(Box::new(QueueModule::new()));
            registry.register(Box::new(LatencyModule::new()));
            registry
        }),
        CompactHudProfile::Idle => IDLE.get_or_init(|| {
            let mut registry = HudRegistry::new();
            registry.register(Box::new(LatencyModule::new()));
            registry
        }),
    }
}

/// Format compact left section for medium terminals.
pub(super) fn format_left_compact(state: &StatusLineState, colors: &ThemeColors) -> String {
    let parts = compact_mode_parts(state, colors);
    let mode_indicator = format_compact_indicator(&parts, colors);
    let mode_label = parts.label;
    let transition = format_transition_suffix(state, colors);

    if mode_label.is_empty() {
        format!(
            "{}{} {} {:.0}dB",
            mode_indicator,
            transition,
            inline_separator(colors.glyph_set),
            state.sensitivity_db
        )
    } else {
        format!(
            "{}{mode_label}{} {} {:.0}dB",
            mode_indicator,
            transition,
            inline_separator(colors.glyph_set),
            state.sensitivity_db
        )
    }
}

/// Format compact shortcuts with modern separator.
pub(super) fn format_shortcuts_compact(colors: &ThemeColors) -> String {
    let sep = colored_overlay_separator(colors);
    format_shortcuts_list(colors, SHORTCUTS_COMPACT, &sep)
}
