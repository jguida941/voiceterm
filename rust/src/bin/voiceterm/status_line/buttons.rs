//! Status-line button layout and hitbox logic so keyboard/mouse actions map reliably.

mod badges;

use crate::buttons::ButtonAction;
#[cfg(test)]
use crate::config::HudRightPanel;
#[cfg(test)]
use crate::config::LatencyDisplayMode;
use crate::config::{HudStyle, VoiceSendMode};
use crate::status_style::StatusType;
#[cfg(test)]
use crate::theme::VoiceSceneStyle;
use crate::theme::{BorderSet, Theme, ThemeColors};

use super::layout::{breakpoints, effective_hud_style_for_state};
use super::mode_indicator::{
    processing_mode_indicator, recording_indicator_color, recording_mode_indicator,
};
use super::right_panel::format_minimal_right_panel as minimal_right_panel;
#[cfg(test)]
use super::right_panel::{
    meter_level_color, minimal_pulse_dots, minimal_waveform, scene_should_animate,
};
#[cfg(test)]
use super::state::WakeWordHudState;
use super::state::{ButtonPosition, RecordingState, StatusLineState, VoiceMode};
use super::text::{display_width, truncate_display};
use badges::{
    format_dev_badge, format_image_badge, format_latency_badge, format_queue_badge,
    format_ready_badge, format_wake_badge,
};
#[cfg(test)]
use badges::{
    rtf_latency_severity, LatencySeverity, LATENCY_RTF_ERROR_X1000, LATENCY_RTF_WARNING_X1000,
};

// Keep the minimal dB lane stable even before the first meter sample arrives.
const MINIMAL_DB_FLOOR: f32 = -60.0;
const FOCUSED_PILL_EMPHASIS_ANSI: &str = "\x1b[1m";

/// Get clickable button positions for the current state.
/// Returns button positions for full HUD mode (row 2 from bottom) and minimal mode (row 1).
/// Hidden mode exposes an "open" launcher and optional "hide" control while idle.
pub fn get_button_positions(
    state: &StatusLineState,
    theme: Theme,
    width: usize,
) -> Vec<ButtonPosition> {
    if state.claude_prompt_suppressed {
        return Vec::new();
    }
    match effective_hud_style_for_state(state) {
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
            processing_mode_indicator(colors),
            "processing",
            colors.processing,
            colors.processing,
        ),
        RecordingState::Responding => (
            colors.indicator_responding,
            "responding",
            colors.info,
            colors.info,
        ),
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
        colors.dim
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
            if idx > 0 {
                cursor += 1;
            }
            let button_width = display_width(rendered);
            button_positions.push(ButtonPosition {
                start_x: cursor as u16,
                end_x: (cursor + button_width - 1) as u16,
                row: 1,
                action: *action,
            });
            cursor += button_width;
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
            label: "studio",
            action: ButtonAction::ThemePicker,
        },
    ]
}

const ROW_ITEM_SEPARATOR: &str = " · ";
const COMPACT_ITEM_SEPARATOR: &str = " ";
const COMPACT_BUTTON_INDICES: [usize; 6] = [0, 1, 2, 3, 5, 6];

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
    if let Some(image_badge) = format_image_badge(state, colors) {
        items.push(image_badge);
    }
    if let Some(dev_badge) = format_dev_badge(state, colors) {
        items.push(dev_badge);
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
    if let Some(image_badge) = format_image_badge(state, colors) {
        compact_items.push(image_badge);
    }
    if let Some(dev_badge) = format_dev_badge(state, colors) {
        compact_items.push(dev_badge);
    }

    let compact_row = truncate_display(&compact_items.join(COMPACT_ITEM_SEPARATOR), inner_width);
    (compact_row, compact_positions)
}

#[cfg(test)]
fn format_button_row(state: &StatusLineState, colors: &ThemeColors, inner_width: usize) -> String {
    let (row, _) = format_button_row_with_positions(state, colors, inner_width, 2, true, false);
    row
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
    format_shortcut_pill(
        &content,
        colors,
        pill_bracket_color(colors, highlight, focused),
        focused,
    )
}

/// Format a button in clickable pill style with brackets.
/// Style: `[label]` with dim (or focused) brackets.
fn format_shortcut_pill(
    content: &str,
    colors: &ThemeColors,
    bracket_color: &str,
    focused: bool,
) -> String {
    let emphasis = focused && !colors.reset.is_empty();
    let mut result =
        String::with_capacity(content.len() + bracket_color.len() * 3 + colors.reset.len() + 2);
    if emphasis {
        result.push_str(FOCUSED_PILL_EMPHASIS_ANSI);
    }
    result.push_str(bracket_color);
    result.push('[');
    result.push_str(content);
    result.push_str(bracket_color);
    result.push(']');
    result.push_str(colors.reset);
    result
}

fn pill_bracket_color<'a>(colors: &'a ThemeColors, highlight: &'a str, focused: bool) -> &'a str {
    if focused {
        colors.info
    } else if highlight.is_empty() {
        colors.dim
    } else {
        highlight
    }
}

#[cfg(test)]
mod tests;
