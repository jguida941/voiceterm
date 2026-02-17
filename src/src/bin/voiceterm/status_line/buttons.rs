//! Status-line button layout and hitbox logic so keyboard/mouse actions map reliably.

use crate::buttons::ButtonAction;
use crate::config::{HudRightPanel, HudStyle, LatencyDisplayMode, VoiceSendMode};
use crate::status_style::StatusType;
use crate::theme::{filled_indicator, BorderSet, Theme, ThemeColors};

use super::animation::{get_processing_spinner, heartbeat_glyph, recording_pulse_on};
use super::layout::breakpoints;
use super::state::{ButtonPosition, RecordingState, StatusLineState, VoiceMode, WakeWordHudState};
use super::text::{display_width, truncate_display};

// Keep right-panel color bands responsive to normal speaking dynamics.
const LEVEL_WARNING_DB: f32 = -30.0;
const LEVEL_ERROR_DB: f32 = -18.0;
// Keep the minimal dB lane stable even before the first meter sample arrives.
const MINIMAL_DB_FLOOR: f32 = -60.0;
// Speech-relative STT speed bands (RTF scaled by 1000, e.g. 250 => 0.25x realtime).
const LATENCY_RTF_WARNING_X1000: u32 = 350;
const LATENCY_RTF_ERROR_X1000: u32 = 650;
// Keep hidden-launcher text/button close to terminal-native dull gray.
const HIDDEN_LAUNCHER_MUTED_ANSI: &str = "\x1b[90m";

/// Get clickable button positions for the current state.
/// Returns button positions for full HUD mode (row 2 from bottom) and minimal mode (row 1).
/// Hidden mode exposes an "open" launcher and optional "hide" control while idle.
pub fn get_button_positions(
    state: &StatusLineState,
    theme: Theme,
    width: usize,
) -> Vec<ButtonPosition> {
    match state.hud_style {
        HudStyle::Full => {
            if width < breakpoints::COMPACT {
                return Vec::new();
            }
            let colors = theme.colors();
            let inner_width = width.saturating_sub(2);
            let (_, buttons) =
                format_button_row_with_positions(state, &colors, inner_width, 2, true, false);
            buttons
        }
        HudStyle::Minimal => {
            let colors = theme.colors();
            let (_, button) = format_minimal_strip_with_button(state, &colors, width);
            button.into_iter().collect()
        }
        HudStyle::Hidden => {
            if state.recording_state != RecordingState::Idle {
                return Vec::new();
            }
            let colors = theme.colors();
            let (_, buttons) = format_hidden_launcher_with_buttons(state, &colors, width);
            buttons
        }
    }
}

#[inline]
fn base_mode_indicator(mode: VoiceMode, colors: &ThemeColors) -> &'static str {
    match mode {
        VoiceMode::Auto => colors.indicator_auto,
        VoiceMode::Manual => colors.indicator_manual,
        VoiceMode::Idle => colors.indicator_idle,
    }
}

#[inline]
fn recording_mode_indicator(mode: VoiceMode, colors: &ThemeColors) -> &'static str {
    filled_indicator(base_mode_indicator(mode, colors))
}

#[inline]
fn with_color(text: &str, color: &str, colors: &ThemeColors) -> String {
    if color.is_empty() {
        text.to_string()
    } else {
        format!("{color}{text}{}", colors.reset)
    }
}

fn minimal_strip_text(state: &StatusLineState, colors: &ThemeColors) -> String {
    // Use animated indicators for recording and processing states
    // Minimal mode: theme-colored indicators for all states
    let (indicator, label, indicator_color, label_color) = match state.recording_state {
        RecordingState::Recording => (
            recording_mode_indicator(state.voice_mode, colors),
            "REC",
            recording_indicator_color(colors),
            colors.recording,
        ),
        RecordingState::Processing => (
            get_processing_spinner(),
            "processing",
            colors.processing,
            colors.processing,
        ),
        RecordingState::Responding => ("↺", "responding", colors.info, colors.info),
        RecordingState::Idle => match state.voice_mode {
            VoiceMode::Auto => (colors.indicator_auto, "AUTO", colors.info, colors.info),
            VoiceMode::Manual => (colors.indicator_manual, "PTT", colors.border, colors.border),
            VoiceMode::Idle => (colors.indicator_idle, "IDLE", colors.dim, colors.dim),
        },
    };

    let indicator_text = with_color(indicator, indicator_color, colors);
    let label_text = with_color(label, label_color, colors);
    let mut line = format!("{indicator_text} {label_text}");

    match state.recording_state {
        RecordingState::Recording => {
            let db = state
                .meter_db
                .or_else(|| state.meter_levels.last().copied())
                .unwrap_or(MINIMAL_DB_FLOOR);
            line.push(' ');
            line.push_str(colors.dim);
            line.push('·');
            line.push_str(colors.reset);
            line.push(' ');
            line.push_str(colors.info);
            line.push_str(&format!("{db:>3.0}dB"));
            line.push_str(colors.reset);
        }
        RecordingState::Processing | RecordingState::Responding | RecordingState::Idle => {}
    }

    if let Some(panel) = minimal_right_panel(state, colors) {
        line.push(' ');
        line.push_str(colors.dim);
        line.push('·');
        line.push_str(colors.reset);
        line.push(' ');
        line.push_str(&panel);
    }

    if let Some(status) = minimal_status_text(state, colors) {
        if !status.is_empty() {
            line.push(' ');
            line.push_str(colors.dim);
            line.push('·');
            line.push_str(colors.reset);
            line.push(' ');
            line.push_str(&status);
        }
    }

    line
}

fn minimal_status_text(state: &StatusLineState, colors: &ThemeColors) -> Option<String> {
    if state.queue_depth > 0 {
        return Some(format!(
            "{}Queued {}{}",
            colors.warning, state.queue_depth, colors.reset
        ));
    }

    if state.message.is_empty() {
        return if state.recording_state == RecordingState::Idle {
            Some(format!("{}Ready{}", colors.success, colors.reset))
        } else {
            None
        };
    }

    let status_type = StatusType::from_message(&state.message);
    if state.recording_state != RecordingState::Idle {
        return match status_type {
            StatusType::Warning => Some(format!(
                "{}{}{}",
                colors.warning, state.message, colors.reset
            )),
            StatusType::Error => Some(format!("{}{}{}", colors.error, state.message, colors.reset)),
            StatusType::Info => Some(format!("{}{}{}", colors.info, state.message, colors.reset)),
            // Recording/processing/success are already represented by the left state lane while active.
            StatusType::Recording | StatusType::Processing | StatusType::Success => None,
        };
    }

    let colored = match status_type {
        StatusType::Success => format!("{}Ready{}", colors.success, colors.reset),
        StatusType::Info => format!("{}{}{}", colors.info, state.message, colors.reset),
        StatusType::Warning => format!("{}{}{}", colors.warning, state.message, colors.reset),
        StatusType::Error => format!("{}{}{}", colors.error, state.message, colors.reset),
        StatusType::Recording | StatusType::Processing => format!(
            "{}{}{}",
            status_type.color(colors),
            state.message,
            colors.reset
        ),
    };
    Some(colored)
}

fn minimal_right_panel(state: &StatusLineState, colors: &ThemeColors) -> Option<String> {
    if state.hud_right_panel == HudRightPanel::Off {
        return None;
    }
    let recording_active = state.recording_state == RecordingState::Recording;
    let animate_panel = !state.hud_right_panel_recording_only || recording_active;

    let panel = match state.hud_right_panel {
        HudRightPanel::Ribbon => {
            let levels = if animate_panel {
                &state.meter_levels
            } else {
                &[][..]
            };
            let waveform = minimal_waveform(levels, 6, colors);
            format!(
                "{}[{}{}{}]{}",
                colors.dim, colors.reset, waveform, colors.dim, colors.reset
            )
        }
        HudRightPanel::Dots => {
            let level = if animate_panel {
                state.meter_db.unwrap_or(-60.0)
            } else {
                -60.0
            };
            minimal_pulse_dots(level, colors)
        }
        HudRightPanel::Heartbeat => {
            let animate =
                should_animate_heartbeat(state.hud_right_panel_recording_only, recording_active);
            let (glyph, is_peak) = heartbeat_glyph(animate);
            let color = if is_peak { colors.info } else { colors.dim };
            format!(
                "{}[{}{}{}{}]{}",
                colors.dim, colors.reset, color, glyph, colors.reset, colors.reset
            )
        }
        HudRightPanel::Off => return None,
    };
    Some(panel)
}

#[inline]
fn should_animate_heartbeat(recording_only: bool, recording_active: bool) -> bool {
    !recording_only || recording_active
}

#[inline]
fn recording_indicator_color(colors: &ThemeColors) -> &str {
    if recording_pulse_on() {
        colors.recording
    } else {
        colors.dim
    }
}

fn minimal_waveform(levels: &[f32], width: usize, colors: &ThemeColors) -> String {
    const GLYPHS: [char; 8] = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
    if width == 0 {
        return String::new();
    }
    if levels.is_empty() {
        // Match full HUD behavior: keep idle placeholder in theme accent.
        return format!("{}{}{}", colors.success, "▁".repeat(width), colors.reset);
    }

    let mut out = String::with_capacity(width * 8);
    let start = levels.len().saturating_sub(width);
    let slice = &levels[start..];
    if slice.len() < width {
        out.push_str(colors.dim);
        out.push_str(&"▁".repeat(width - slice.len()));
        out.push_str(colors.reset);
    }
    for db in slice {
        let normalized = ((*db + 60.0) / 60.0).clamp(0.0, 1.0);
        let idx = (normalized * (GLYPHS.len() as f32 - 1.0)) as usize;
        let color = meter_level_color(*db, colors);
        out.push_str(color);
        out.push(GLYPHS[idx]);
        out.push_str(colors.reset);
    }
    out
}

fn minimal_pulse_dots(level_db: f32, colors: &ThemeColors) -> String {
    let normalized = ((level_db + 60.0) / 60.0).clamp(0.0, 1.0);
    let active = (normalized * 5.0).round() as usize;
    let color = meter_level_color(level_db, colors);
    let mut result = String::with_capacity(64);
    result.push_str(colors.dim);
    result.push('[');
    result.push_str(colors.reset);
    for idx in 0..5 {
        if idx < active {
            result.push_str(color);
            result.push('•');
            result.push_str(colors.reset);
        } else {
            result.push_str(colors.dim);
            result.push('·');
            result.push_str(colors.reset);
        }
    }
    result.push_str(colors.dim);
    result.push(']');
    result.push_str(colors.reset);
    result
}

#[inline]
fn meter_level_color(level_db: f32, colors: &ThemeColors) -> &str {
    if level_db < LEVEL_WARNING_DB {
        colors.success
    } else if level_db < LEVEL_ERROR_DB {
        colors.warning
    } else {
        colors.error
    }
}

pub(super) fn format_minimal_strip_with_button(
    state: &StatusLineState,
    colors: &ThemeColors,
    width: usize,
) -> (String, Option<ButtonPosition>) {
    if width == 0 {
        return (String::new(), None);
    }

    let base = minimal_strip_text(state, colors);
    let focused = state.hud_button_focus == Some(ButtonAction::HudBack);
    let button = format_button(colors, "back", colors.border, focused);
    let button_width = display_width(&button);

    // Require room for at least one space between status and button.
    if width >= button_width + 2 {
        let button_start = width.saturating_sub(button_width) + 1;
        let status_width = button_start.saturating_sub(2);
        let status = truncate_display(&base, status_width);
        let status_width = display_width(&status);
        let padding = button_start.saturating_sub(1 + status_width);
        let line = format!("{status}{}{}", " ".repeat(padding), button);
        let button_pos = ButtonPosition {
            start_x: button_start as u16,
            end_x: (button_start + button_width - 1) as u16,
            row: 1,
            action: ButtonAction::HudBack,
        };
        return (line, Some(button_pos));
    }

    let line = truncate_display(&base, width);
    (line, None)
}

fn hidden_launcher_text(state: &StatusLineState, colors: &ThemeColors) -> String {
    let base = if state.message.is_empty() {
        "VoiceTerm hidden · ? help · ^O settings".to_string()
    } else {
        format!("VoiceTerm · {}", state.message)
    };
    with_color(&base, hidden_muted_color(colors), colors)
}

#[inline]
pub(super) fn hidden_muted_color(colors: &ThemeColors) -> &str {
    if colors.reset.is_empty() {
        ""
    } else {
        HIDDEN_LAUNCHER_MUTED_ANSI
    }
}

fn hidden_launcher_button(colors: &ThemeColors, label: &str, focused: bool) -> String {
    if focused {
        return format_button(colors, label, colors.info, true);
    }
    with_color(&format!("[{label}]"), hidden_muted_color(colors), colors)
}

fn hidden_launcher_button_defs(
    state: &StatusLineState,
    colors: &ThemeColors,
) -> Vec<(ButtonAction, String)> {
    let mut defs = Vec::with_capacity(2);
    defs.push((
        ButtonAction::ToggleHudStyle,
        hidden_launcher_button(
            colors,
            "open",
            state.hud_button_focus == Some(ButtonAction::ToggleHudStyle),
        ),
    ));
    if !state.hidden_launcher_collapsed {
        defs.push((
            ButtonAction::CollapseHiddenLauncher,
            hidden_launcher_button(
                colors,
                "hide",
                state.hud_button_focus == Some(ButtonAction::CollapseHiddenLauncher),
            ),
        ));
    }
    defs
}

pub(super) fn format_hidden_launcher_with_buttons(
    state: &StatusLineState,
    colors: &ThemeColors,
    width: usize,
) -> (String, Vec<ButtonPosition>) {
    if width == 0 {
        return (String::new(), Vec::new());
    }

    let base = if state.hidden_launcher_collapsed {
        String::new()
    } else {
        hidden_launcher_text(state, colors)
    };
    let button_defs = hidden_launcher_button_defs(state, colors);
    let button_row = button_defs
        .iter()
        .map(|(_, rendered)| rendered.as_str())
        .collect::<Vec<_>>()
        .join(" ");
    let button_row_width = display_width(&button_row);

    if width >= button_row_width + 2 {
        let button_start = width.saturating_sub(button_row_width) + 1;
        let status_width = button_start.saturating_sub(2);
        let status = truncate_display(&base, status_width);
        let status_width = display_width(&status);
        let padding = button_start.saturating_sub(1 + status_width);
        let line = format!("{status}{}{}", " ".repeat(padding), button_row);
        let mut button_positions = Vec::with_capacity(button_defs.len());
        let mut cursor = button_start;
        for (idx, (action, rendered)) in button_defs.iter().enumerate() {
            let button_width = display_width(rendered);
            button_positions.push(ButtonPosition {
                start_x: cursor as u16,
                end_x: (cursor + button_width - 1) as u16,
                row: 1,
                action: *action,
            });
            cursor += button_width;
            if idx + 1 < button_defs.len() {
                cursor += 1;
            }
        }
        return (line, button_positions);
    }

    let line = truncate_display(&base, width);
    (line, Vec::new())
}

/// Format the shortcuts row with dimmed styling and return button positions.
pub(super) fn format_shortcuts_row_with_positions(
    state: &StatusLineState,
    colors: &ThemeColors,
    borders: &BorderSet,
    inner_width: usize,
    trailing_panel: Option<&str>,
) -> (String, Vec<ButtonPosition>) {
    let row_width = inner_width.saturating_sub(1);
    // Row 2 from bottom of HUD (row 1 = bottom border)
    let (shortcuts_str, buttons) =
        format_button_row_with_positions(state, colors, row_width, 2, true, false);

    // Add leading space to match main row's left margin
    let shortcuts = truncate_display(&format!(" {}", shortcuts_str), inner_width);
    let shortcuts_width = display_width(&shortcuts);
    let mut interior = shortcuts.clone();

    // Keep shortcut/button geometry stable: only append trailing panel if there is spare room.
    if let Some(panel) = trailing_panel {
        if !panel.is_empty() {
            let panel = truncate_display(panel, inner_width);
            let panel_width = display_width(&panel);
            if panel_width > 0 && shortcuts_width + 1 + panel_width <= inner_width {
                // Right-align the visualization panel to keep it anchored in the corner.
                let gap = inner_width.saturating_sub(shortcuts_width + panel_width);
                interior = format!("{shortcuts}{}{}", " ".repeat(gap), panel);
            }
        }
    }

    let line = wrap_shortcuts_row(&interior, colors, borders, inner_width);

    (line, buttons)
}

/// Format the shortcuts row with dimmed styling.
#[cfg(test)]
fn format_shortcuts_row(
    state: &StatusLineState,
    colors: &ThemeColors,
    borders: &BorderSet,
    inner_width: usize,
) -> String {
    let (line, _) = format_shortcuts_row_with_positions(state, colors, borders, inner_width, None);
    line
}

/// Legacy format_shortcuts_row without position tracking.
#[cfg(test)]
fn format_shortcuts_row_legacy(
    state: &StatusLineState,
    colors: &ThemeColors,
    borders: &BorderSet,
    inner_width: usize,
) -> String {
    let shortcuts_str = format_button_row(state, colors, inner_width);

    // Add leading space to match main row's left margin
    let interior = format!(" {}", shortcuts_str);
    wrap_shortcuts_row(&interior, colors, borders, inner_width)
}

/// Button definition for position tracking.
struct ButtonDef {
    label: &'static str,
    action: ButtonAction,
}

/// Build buttons with their labels and actions based on current state.
fn get_button_defs(state: &StatusLineState) -> Vec<ButtonDef> {
    let voice_label = if state.auto_voice_enabled {
        "auto"
    } else {
        "ptt"
    };
    let send_label = match state.send_mode {
        VoiceSendMode::Auto => "send",
        VoiceSendMode::Insert => "edit",
    };

    vec![
        ButtonDef {
            label: "rec",
            action: ButtonAction::VoiceTrigger,
        },
        ButtonDef {
            label: voice_label,
            action: ButtonAction::ToggleAutoVoice,
        },
        ButtonDef {
            label: send_label,
            action: ButtonAction::ToggleSendMode,
        },
        ButtonDef {
            label: "set",
            action: ButtonAction::SettingsToggle,
        },
        ButtonDef {
            label: "hud",
            action: ButtonAction::ToggleHudStyle,
        },
        ButtonDef {
            label: "help",
            action: ButtonAction::HelpToggle,
        },
        ButtonDef {
            label: "theme",
            action: ButtonAction::ThemePicker,
        },
    ]
}

const ROW_ITEM_SEPARATOR: &str = " · ";
const COMPACT_ITEM_SEPARATOR: &str = " ";
const COMPACT_BUTTON_INDICES: [usize; 6] = [0, 1, 2, 3, 5, 6];
#[cfg(test)]
const LEGACY_COMPACT_ITEM_INDICES: [usize; 5] = [0, 1, 2, 3, 5];

fn wrap_shortcuts_row(
    interior: &str,
    colors: &ThemeColors,
    borders: &BorderSet,
    inner_width: usize,
) -> String {
    let interior_width = display_width(interior);
    let padding_needed = inner_width.saturating_sub(interior_width);
    let padding = " ".repeat(padding_needed);
    format!(
        "{}{}{}{}{}{}{}{}",
        colors.border,
        borders.vertical,
        colors.reset,
        interior,
        padding,
        colors.border,
        borders.vertical,
        colors.reset,
    )
}

#[inline]
fn recording_button_highlight(colors: &ThemeColors) -> &str {
    colors.recording
}

fn button_highlight<'a>(
    state: &StatusLineState,
    colors: &'a ThemeColors,
    action: ButtonAction,
) -> &'a str {
    match action {
        ButtonAction::VoiceTrigger => match state.recording_state {
            RecordingState::Recording => recording_button_highlight(colors),
            RecordingState::Processing => colors.processing,
            RecordingState::Responding => colors.info,
            RecordingState::Idle => colors.border,
        },
        ButtonAction::ToggleAutoVoice => {
            if state.auto_voice_enabled {
                colors.info
            } else {
                colors.border
            }
        }
        ButtonAction::ToggleSendMode => match state.send_mode {
            VoiceSendMode::Auto => colors.success,
            VoiceSendMode::Insert => colors.warning,
        },
        ButtonAction::SettingsToggle
        | ButtonAction::ToggleHudStyle
        | ButtonAction::CollapseHiddenLauncher
        | ButtonAction::HudBack
        | ButtonAction::HelpToggle
        | ButtonAction::ThemePicker => colors.border,
    }
}

fn format_queue_badge(state: &StatusLineState, colors: &ThemeColors) -> Option<String> {
    (state.queue_depth > 0)
        .then(|| format!("{}Q:{}{}", colors.warning, state.queue_depth, colors.reset))
}

fn format_wake_badge(state: &StatusLineState, colors: &ThemeColors) -> Option<String> {
    match state.wake_word_state {
        WakeWordHudState::Off => None,
        WakeWordHudState::Listening => {
            // Keep a calm baseline, then pulse into a brighter accent so listening
            // is visible without looking "always hot".
            let (color, emphasis) = if recording_pulse_on() {
                (colors.success, "\x1b[1m")
            } else {
                (colors.border, "")
            };
            Some(format!("{color}{emphasis}Wake: ON{}", colors.reset))
        }
        WakeWordHudState::Paused => Some(format!("{}Wake: PAUSED{}", colors.warning, colors.reset)),
    }
}

fn format_ready_badge(
    state: &StatusLineState,
    colors: &ThemeColors,
    enabled: bool,
) -> Option<String> {
    (enabled && state.recording_state == RecordingState::Idle && state.queue_depth == 0)
        .then(|| format!("{}Ready{}", colors.success, colors.reset))
}

#[derive(Copy, Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
enum LatencySeverity {
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

fn rtf_latency_severity(rtf_x1000: u32) -> LatencySeverity {
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

fn format_latency_badge(
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

/// Format button row and return (formatted_string, button_positions).
/// Button positions are relative to the row start (after border character).
fn format_button_row_with_positions(
    state: &StatusLineState,
    colors: &ThemeColors,
    inner_width: usize,
    hud_row: u16,
    show_latency_badge: bool,
    show_ready_badge: bool,
) -> (String, Vec<ButtonPosition>) {
    let button_defs = get_button_defs(state);
    let mut items = Vec::new();
    let mut positions = Vec::new();

    // Track current x position (1-based, after border + leading space = column 3)
    let mut current_x: u16 = 3; // border(1) + space(1) + first char at (3)
    let separator_visible_width = 3u16; // " · " = 3 visible chars

    for (idx, def) in button_defs.iter().enumerate() {
        if idx > 0 {
            current_x += separator_visible_width;
        }

        let focused = state.hud_button_focus == Some(def.action);
        let formatted = format_button(
            colors,
            def.label,
            button_highlight(state, colors, def.action),
            focused,
        );
        let visible_width = def.label.len() as u16 + 2; // [label] = label + 2 brackets

        // Record position
        positions.push(ButtonPosition {
            start_x: current_x,
            end_x: current_x + visible_width - 1,
            row: hud_row,
            action: def.action,
        });

        items.push(formatted);
        current_x += visible_width;
    }

    if let Some(queue_badge) = format_queue_badge(state, colors) {
        items.push(queue_badge);
    }
    if let Some(wake_badge) = format_wake_badge(state, colors) {
        items.push(wake_badge);
    }

    let ready_badge = format_ready_badge(state, colors, show_ready_badge);
    let latency_badge = if show_latency_badge {
        format_latency_badge(state, colors, true)
    } else {
        None
    };
    match (ready_badge, latency_badge) {
        (Some(ready), Some(latency)) => {
            items.push(format!("{ready} {latency}"));
        }
        (Some(ready), None) => {
            items.push(ready);
        }
        (None, Some(latency)) => {
            items.push(latency);
        }
        (None, None) => {}
    }

    let row = items.join(ROW_ITEM_SEPARATOR);

    if display_width(&row) <= inner_width {
        return (row, positions);
    }

    // Compact mode: fewer buttons, recalculate positions
    let mut compact_items = Vec::new();
    let mut compact_positions = Vec::new();
    current_x = 3;
    for (i, &idx) in COMPACT_BUTTON_INDICES.iter().enumerate() {
        if i > 0 {
            current_x += 1; // space separator in compact mode
        }

        let def = &button_defs[idx];

        let focused = state.hud_button_focus == Some(def.action);
        let formatted = format_button(
            colors,
            def.label,
            button_highlight(state, colors, def.action),
            focused,
        );
        let visible_width = def.label.len() as u16 + 2;

        compact_positions.push(ButtonPosition {
            start_x: current_x,
            end_x: current_x + visible_width - 1,
            row: hud_row,
            action: def.action,
        });

        compact_items.push(formatted);
        current_x += visible_width;
    }

    if let Some(queue_badge) = format_queue_badge(state, colors) {
        compact_items.push(queue_badge);
    }
    if let Some(wake_badge) = format_wake_badge(state, colors) {
        compact_items.push(wake_badge);
    }

    let compact_row = truncate_display(&compact_items.join(COMPACT_ITEM_SEPARATOR), inner_width);
    (compact_row, compact_positions)
}

#[cfg(test)]
fn format_button_row(state: &StatusLineState, colors: &ThemeColors, inner_width: usize) -> String {
    let (row, _) = format_button_row_with_positions(state, colors, inner_width, 2, true, false);
    row
}

#[cfg(test)]
fn format_button_row_legacy(
    state: &StatusLineState,
    colors: &ThemeColors,
    inner_width: usize,
) -> String {
    let mut items = Vec::new();

    // rec - RED when recording, yellow when processing, dim when idle
    let rec_color = match state.recording_state {
        RecordingState::Recording => colors.recording,
        RecordingState::Processing => colors.processing,
        RecordingState::Responding => colors.info,
        RecordingState::Idle => "",
    };
    items.push(format_button(colors, "rec", rec_color, false));

    // auto/ptt - blue when auto-voice, dim when ptt
    let (voice_label, voice_color) = if state.auto_voice_enabled {
        ("auto", colors.info) // blue = auto-voice on
    } else {
        ("ptt", "") // dim = push-to-talk mode
    };
    items.push(format_button(colors, voice_label, voice_color, false));

    // send mode: auto/insert - green when auto-send, yellow when insert
    let (send_label, send_color) = match state.send_mode {
        VoiceSendMode::Auto => ("send", colors.success), // green = auto-send
        VoiceSendMode::Insert => ("edit", colors.warning), // yellow = insert/edit mode
    };
    items.push(format_button(colors, send_label, send_color, false));

    // Static buttons - always dim
    items.push(format_button(colors, "set", "", false));
    items.push(format_button(colors, "hud", "", false));
    items.push(format_button(colors, "help", "", false));
    items.push(format_button(colors, "theme", "", false));

    // Queue badge - modern pill style
    if let Some(queue_badge) = format_queue_badge(state, colors) {
        items.push(queue_badge);
    }
    if let Some(wake_badge) = format_wake_badge(state, colors) {
        items.push(wake_badge);
    }

    if let Some(latency_badge) = format_latency_badge(state, colors, false) {
        items.push(latency_badge);
    }

    let row = items.join(ROW_ITEM_SEPARATOR);
    if display_width(&row) <= inner_width {
        return row;
    }

    // Compact: keep essentials (rec/auto/send/settings/help)
    let mut compact: Vec<String> = LEGACY_COMPACT_ITEM_INDICES
        .iter()
        .map(|idx| items[*idx].clone())
        .collect();
    if let Some(queue_badge) = format_queue_badge(state, colors) {
        compact.push(queue_badge);
    }
    if let Some(wake_badge) = format_wake_badge(state, colors) {
        compact.push(wake_badge);
    }
    truncate_display(&compact.join(COMPACT_ITEM_SEPARATOR), inner_width)
}

/// Format a clickable button - colored label when active, dim otherwise.
/// Style: `[label]` - brackets for clickable appearance, no shortcut prefix.
#[inline]
pub(super) fn format_button(
    colors: &ThemeColors,
    label: &str,
    highlight: &str,
    focused: bool,
) -> String {
    // Keep one active color context through bracket+label to avoid transient
    // default-color flashes in terminals that repaint aggressively.
    let mut content = String::with_capacity(16 + label.len());
    if !highlight.is_empty() {
        content.push_str(highlight);
    }
    content.push_str(label);
    format_shortcut_pill(&content, colors, focused)
}

/// Format a button in clickable pill style with brackets.
/// Style: `[label]` with dim (or focused) brackets.
fn format_shortcut_pill(content: &str, colors: &ThemeColors, focused: bool) -> String {
    let bracket_color = if focused { colors.info } else { colors.dim };
    let mut result =
        String::with_capacity(content.len() + bracket_color.len() * 3 + colors.reset.len() + 2);
    result.push_str(bracket_color);
    result.push('[');
    result.push_str(content);
    result.push_str(bracket_color);
    result.push(']');
    result.push_str(colors.reset);
    result
}

/// Legacy format with shortcut key prefix (for help display).
#[inline]
#[allow(dead_code)]
fn format_shortcut_colored(
    colors: &ThemeColors,
    key: &str,
    label: &str,
    highlight: &str,
) -> String {
    let mut content = String::with_capacity(48);
    content.push_str(colors.dim);
    content.push_str(key);
    content.push_str(colors.reset);
    content.push(' ');
    if highlight.is_empty() {
        content.push_str(colors.dim);
        content.push_str(label);
        content.push_str(colors.reset);
    } else {
        content.push_str(highlight);
        content.push_str(label);
        content.push_str(colors.reset);
    }
    format_shortcut_pill(&content, colors, false)
}

#[cfg(test)]
mod tests;
