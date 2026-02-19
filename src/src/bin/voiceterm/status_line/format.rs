//! Status-line formatter so full/minimal HUD modes share consistent semantics.

use std::sync::OnceLock;

use crate::audio_meter::format_waveform;
use crate::config::{HudBorderStyle, HudRightPanel, HudStyle};
use crate::hud::{HudRegistry, HudState, LatencyModule, MeterModule, Mode as HudMode, QueueModule};
use crate::status_style::StatusType;
use crate::theme::{
    filled_indicator, waveform_bars, BorderSet, Theme, ThemeColors, BORDER_DOUBLE, BORDER_HEAVY,
    BORDER_NONE, BORDER_ROUNDED, BORDER_SINGLE,
};

use super::animation::{
    get_processing_spinner, heartbeat_glyph, recording_pulse_on, transition_marker,
};
use super::buttons::{
    format_hidden_launcher_with_buttons, format_minimal_strip_with_button,
    format_shortcuts_row_with_positions, hidden_muted_color,
};
use super::layout::breakpoints;
#[cfg(test)]
use super::state::Pipeline;
use super::state::{RecordingState, StatusBanner, StatusLineState, VoiceMode};
use super::text::{display_width, truncate_display};

const MAIN_ROW_DURATION_PLACEHOLDER: &str = "--.-s";
const MAIN_ROW_DURATION_TEXT_WIDTH: usize = MAIN_ROW_DURATION_PLACEHOLDER.len();
const MAIN_ROW_DURATION_TEXT_WIDTH_AUTO: usize = MAIN_ROW_DURATION_TEXT_WIDTH + 1;
const MAIN_ROW_RIGHT_GUTTER: usize = 1;
const MAIN_ROW_METER_TEXT_WIDTH: usize = 5;
const RIGHT_PANEL_MAX_WAVEFORM_WIDTH: usize = 20;
const RIGHT_PANEL_MIN_CONTENT_WIDTH: usize = 4;
// Keep main-row separators anchored to stable columns so they do not jitter
// across recording/processing state transitions.
const MAIN_ROW_MODE_LANE_WIDTH: usize = 9;
const MODE_LABEL_WIDTH: usize = 8;
// Keep right-panel color bands responsive to normal speaking dynamics.
const LEVEL_WARNING_DB: f32 = -30.0;
const LEVEL_ERROR_DB: f32 = -18.0;
const METER_DB_FLOOR: f32 = -60.0;

/// Keyboard shortcuts to display.
const SHORTCUTS: &[(&str, &str)] = &[
    ("Ctrl+R", "rec"),
    ("Ctrl+V", "auto"),
    ("Ctrl+T", "send"),
    ("Ctrl+G", "theme+"),
    ("Ctrl+U", "hud"),
    ("Ctrl+O", "settings"),
    ("?", "help"),
    ("Ctrl+Y", "theme"),
];

/// Compact shortcuts for narrow terminals.
const SHORTCUTS_COMPACT: &[(&str, &str)] = &[
    ("^R", "rec"),
    ("^V", "auto"),
    ("^T", "send"),
    ("^G", "th+"),
    ("^U", "hud"),
    ("^O", "settings"),
    ("?", "help"),
    ("^Y", "theme"),
];

fn resolve_hud_border_set<'a>(
    state: &StatusLineState,
    theme_borders: &'a BorderSet,
) -> &'a BorderSet {
    match state.hud_border_style {
        HudBorderStyle::Theme => theme_borders,
        HudBorderStyle::Single => &BORDER_SINGLE,
        HudBorderStyle::Rounded => &BORDER_ROUNDED,
        HudBorderStyle::Double => &BORDER_DOUBLE,
        HudBorderStyle::Heavy => &BORDER_HEAVY,
        HudBorderStyle::None => &BORDER_NONE,
    }
}

fn borderless_row(width: usize) -> String {
    " ".repeat(width)
}

fn full_mode_voice_label(mode: VoiceMode) -> &'static str {
    match mode {
        VoiceMode::Auto => "AUTO",
        VoiceMode::Manual => "PTT",
        VoiceMode::Idle => "IDLE",
    }
}

fn idle_mode_indicator(mode: VoiceMode, colors: &ThemeColors) -> (&'static str, &'static str) {
    match mode {
        VoiceMode::Auto => (colors.indicator_auto, colors.info),
        VoiceMode::Manual => (colors.indicator_manual, ""),
        VoiceMode::Idle => (colors.indicator_idle, ""),
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
fn recording_indicator_color(colors: &ThemeColors) -> &str {
    if recording_pulse_on() {
        colors.recording
    } else {
        colors.dim
    }
}

#[inline]
fn processing_mode_indicator(colors: &ThemeColors) -> &str {
    get_processing_spinner(colors)
}

#[inline]
fn with_color(text: &str, color: &str, colors: &ThemeColors) -> String {
    if color.is_empty() {
        text.to_string()
    } else {
        format!("{color}{text}{}", colors.reset)
    }
}

/// Format hidden mode strip - grey/obscure, only shows essential info when active.
/// More subtle than minimal mode - all dim colors for minimal distraction.
fn format_hidden_strip(state: &StatusLineState, colors: &ThemeColors, width: usize) -> String {
    if width == 0 {
        return String::new();
    }

    // Hidden mode stays subtle while preserving theme-specific recording identity.
    let mut line = match state.recording_state {
        RecordingState::Recording => {
            let indicator = recording_mode_indicator(state.voice_mode, colors);
            format!("{indicator} rec")
        }
        RecordingState::Processing => format!("{} ...", processing_mode_indicator(colors)),
        RecordingState::Responding => format!("{} rsp", colors.indicator_responding),
        RecordingState::Idle => return String::new(),
    };

    // Add duration for recording, keep it minimal
    if state.recording_state == RecordingState::Recording {
        if let Some(dur) = state.recording_duration {
            line.push_str(&format!(" {:.0}s", dur));
        }
    }

    let muted = with_color(&line, hidden_muted_color(colors), colors);
    truncate_display(&muted, width)
}

/// Format the status as a multi-row banner with themed borders.
///
/// Layout (4 rows for Full mode):
/// ```text
/// ╭──────────────────────────────────────────────────── VoiceTerm ─╮
/// │ ● AUTO │ Rust │ ▁▂▃▅▆▇█▅  -51dB  Status message here          │
/// │ [rec] · [auto] · [send] · [set] · [hud] · [help] · [theme]   │
/// ╰──────────────────────────────────────────────────────────────╯
/// ```
///
/// Minimal mode: Theme-colored strip with indicator + status (e.g., "● PTT · Ready")
/// Hidden mode: Branded launcher with `open`/`hide` controls when idle; dim indicator when recording (e.g., "● rec 5s")
pub fn format_status_banner(state: &StatusLineState, theme: Theme, width: usize) -> StatusBanner {
    // When a Claude interactive prompt is detected, suppress the HUD to prevent
    // occluding approval/permission prompts (MP-226). Render no HUD rows so the
    // PTY gets the full terminal height for the prompt.
    if state.claude_prompt_suppressed {
        return StatusBanner::new(Vec::new());
    }

    let colors = theme.colors();
    let borders = resolve_hud_border_set(state, &colors.borders);
    let borderless =
        state.hud_style == HudStyle::Full && state.hud_border_style == HudBorderStyle::None;

    // Handle HUD style
    match state.hud_style {
        HudStyle::Hidden => {
            if state.recording_state != RecordingState::Idle {
                let line = format_hidden_strip(state, &colors, width);
                StatusBanner::new(vec![line])
            } else {
                // Idle hidden mode still renders a branded launcher to stay discoverable.
                let (line, buttons) = format_hidden_launcher_with_buttons(state, &colors, width);
                StatusBanner::with_buttons(vec![line], buttons)
            }
        }
        HudStyle::Minimal => {
            let (line, button) = format_minimal_strip_with_button(state, &colors, width);
            StatusBanner::with_buttons(vec![line], button.into_iter().collect())
        }
        HudStyle::Full => {
            // For very narrow terminals, fall back to simple single-line
            if width < breakpoints::COMPACT {
                let line = format_status_line(state, theme, width);
                return StatusBanner::new(vec![line]);
            }

            let inner_width = width.saturating_sub(2); // Account for left/right borders

            let main_row_panel =
                format_right_panel(state, &colors, theme, inner_width.saturating_sub(12));
            // Get shortcuts row with button positions
            let (shortcuts_line, buttons) =
                format_shortcuts_row_with_positions(state, &colors, borders, inner_width, None);

            let lines = vec![
                if borderless {
                    borderless_row(width)
                } else {
                    format_top_border(&colors, borders, width)
                },
                format_main_row(
                    state,
                    &colors,
                    borders,
                    inner_width,
                    if main_row_panel.is_empty() {
                        None
                    } else {
                        Some(main_row_panel.as_str())
                    },
                ),
                shortcuts_line,
                if borderless {
                    borderless_row(width)
                } else {
                    format_bottom_border(&colors, borders, width)
                },
            ];

            StatusBanner::with_buttons(lines, buttons)
        }
    }
}

/// Format the top border with VoiceTerm badge.
fn format_top_border(colors: &ThemeColors, borders: &BorderSet, width: usize) -> String {
    let brand_label = format_brand_label(colors);
    let label_width = display_width(&brand_label);

    // Calculate border segments
    // Total: top_left(1) + left_segment + label + right_segment + top_right(1) = width
    let left_border_len = 2;
    let right_border_len = width.saturating_sub(left_border_len + label_width + 2); // +2 for corners

    let left_segment: String = std::iter::repeat_n(borders.horizontal, left_border_len).collect();
    let right_segment: String = std::iter::repeat_n(borders.horizontal, right_border_len).collect();

    format!(
        "{}{}{}{}{}{}{}",
        colors.border,
        borders.top_left,
        left_segment,
        colors.reset,
        brand_label,
        colors.border,
        right_segment,
    ) + &format!("{}{}", borders.top_right, colors.reset)
}

fn format_brand_label(colors: &ThemeColors) -> String {
    format!(
        " {}Voice{}{}Term{} ",
        colors.info, colors.reset, colors.recording, colors.reset
    )
}

fn format_duration_section(state: &StatusLineState, colors: &ThemeColors) -> String {
    let width = if state.auto_voice_enabled {
        MAIN_ROW_DURATION_TEXT_WIDTH_AUTO
    } else {
        MAIN_ROW_DURATION_TEXT_WIDTH
    };
    if let Some(dur) = state.recording_duration {
        let bounded = dur.max(0.0);
        let text = if bounded < 100.0 {
            format!("{bounded:.1}s")
        } else if bounded < 10_000.0 {
            format!("{bounded:.0}s")
        } else {
            "9999s".to_string()
        };
        let padded = format!("{text:>width$}");
        if state.recording_state == RecordingState::Recording {
            format!(" {padded} ")
        } else {
            format!(" {}{}{} ", colors.dim, padded, colors.reset)
        }
    } else {
        let padded = format!("{MAIN_ROW_DURATION_PLACEHOLDER:>width$}");
        format!(" {}{}{} ", colors.dim, padded, colors.reset)
    }
}

fn dim_waveform_placeholder(width: usize, colors: &ThemeColors) -> String {
    // Keep idle ribbon placeholders theme-colored so the right panel still matches
    // the active palette instead of fading to neutral gray.
    let mut result = String::with_capacity(width + colors.success.len() + colors.reset.len());
    let bars = waveform_bars(colors.glyph_set);
    result.push_str(colors.success);
    for _ in 0..width {
        result.push(bars[0]);
    }
    result.push_str(colors.reset);
    result
}

/// Legacy bracket style for backwards compatibility.
#[allow(dead_code)]
fn format_panel_brackets(content: &str, colors: &ThemeColors) -> String {
    let mut result =
        String::with_capacity(content.len() + colors.dim.len() * 2 + colors.reset.len() * 2 + 2);
    result.push_str(colors.dim);
    result.push('[');
    result.push_str(colors.reset);
    result.push_str(content);
    result.push_str(colors.dim);
    result.push(']');
    result.push_str(colors.reset);
    result
}

fn format_meter_section(state: &StatusLineState, colors: &ThemeColors) -> String {
    let recording_active = state.recording_state == RecordingState::Recording;
    let db_value = state
        .meter_db
        .or_else(|| state.meter_levels.last().copied())
        .or(if recording_active {
            Some(METER_DB_FLOOR)
        } else {
            None
        });
    let raw_text = if let Some(db) = db_value {
        format!("{db:.0}dB")
    } else {
        "--dB".to_string()
    };
    let db_text = format!("{raw_text:>width$}", width = MAIN_ROW_METER_TEXT_WIDTH);
    let db_color = if recording_active {
        colors.info
    } else {
        colors.dim
    };
    format!(" {}{}{} ", db_color, db_text, colors.reset)
}

/// Format the main status row with mode, sensitivity, meter, and message.
fn format_main_row(
    state: &StatusLineState,
    colors: &ThemeColors,
    borders: &BorderSet,
    inner_width: usize,
    trailing_panel: Option<&str>,
) -> String {
    let render_width = inner_width.saturating_sub(MAIN_ROW_RIGHT_GUTTER);

    // Build content sections
    let mode_section = format_mode_indicator(state, colors);
    let duration_section = format_duration_section(state, colors);
    let meter_section = format_meter_section(state, colors);

    let message_section = format_full_hud_message(state, colors);

    // Combine all sections
    let sep = format!("{}│{}", colors.dim, colors.reset);
    let content = [mode_section, duration_section, meter_section].join(&sep);
    let message_lane = if message_section.is_empty() {
        String::new()
    } else {
        // Keep the final separator on the same column as the `[set]` shortcut start.
        format!(" {sep} {message_section}")
    };

    let content_width = display_width(&content);
    let panel_segment = trailing_panel
        .filter(|panel| !panel.is_empty())
        .and_then(|panel| {
            let segment = format!(" {panel}");
            if content_width + display_width(&segment) <= render_width {
                Some(segment)
            } else {
                None
            }
        })
        .unwrap_or_default();
    let panel_width = display_width(&panel_segment);
    let text_render_width = render_width.saturating_sub(panel_width);
    let message_available = text_render_width.saturating_sub(content_width);
    let truncated_message = truncate_display(&message_lane, message_available);
    let message_width = display_width(&truncated_message);
    let interior = format!("{content}{truncated_message}");

    // Padding to fill the row.
    let padding_needed = text_render_width.saturating_sub(content_width + message_width);
    let padding = " ".repeat(padding_needed);
    let right_gutter = " ".repeat(inner_width.saturating_sub(render_width));

    // No background colors - use transparent backgrounds for terminal compatibility
    format!(
        "{}{}{}{}{}{}{}{}{}{}",
        colors.border,
        borders.vertical,
        colors.reset,
        interior,
        padding,
        panel_segment,
        right_gutter,
        colors.border,
        borders.vertical,
        colors.reset,
    )
}

fn active_state_fallback_message(state: &StatusLineState, colors: &ThemeColors) -> String {
    match state.recording_state {
        RecordingState::Recording => format!("{}Recording{}", colors.recording, colors.reset),
        RecordingState::Processing => format!("{}Processing{}", colors.processing, colors.reset),
        RecordingState::Responding => format!("{}Responding{}", colors.info, colors.reset),
        RecordingState::Idle => String::new(),
    }
}

fn format_full_hud_message(state: &StatusLineState, colors: &ThemeColors) -> String {
    if state.recording_state != RecordingState::Idle {
        let fallback = active_state_fallback_message(state, colors);
        if state.message.is_empty() {
            return fallback;
        }
        let status_type = StatusType::from_message(&state.message);
        return match status_type {
            // While active, keep state lanes on the left but still surface explicit user toggles.
            StatusType::Warning => format!("{}{}{}", colors.warning, state.message, colors.reset),
            StatusType::Error => format!("{}{}{}", colors.error, state.message, colors.reset),
            StatusType::Info => format!("{}{}{}", colors.info, state.message, colors.reset),
            StatusType::Recording => {
                format!("{}{}{}", colors.recording, state.message, colors.reset)
            }
            StatusType::Processing => {
                format!("{}{}{}", colors.processing, state.message, colors.reset)
            }
            // Avoid stale "Transcript ready" while we're still in an active state.
            StatusType::Success => fallback,
        };
    }

    if state.queue_depth > 0 {
        // Queue is shown on the shortcuts row (`Q:n`); avoid duplicate text on main row.
        return String::new();
    }

    if state.message.is_empty() {
        return format!("{}Ready{}", colors.success, colors.reset);
    }

    let status_type = StatusType::from_message(&state.message);
    match status_type {
        // Keep idle success state concise beside the dB lane.
        StatusType::Success => format!("{}Ready{}", colors.success, colors.reset),
        // Show actionable/info toggles in the center message lane.
        StatusType::Info => format!("{}{}{}", colors.info, state.message, colors.reset),
        StatusType::Warning => format!("{}{}{}", colors.warning, state.message, colors.reset),
        StatusType::Error => format!("{}{}{}", colors.error, state.message, colors.reset),
        StatusType::Processing | StatusType::Recording => {
            format!(
                "{}{}{}",
                status_type.color(colors),
                state.message,
                colors.reset
            )
        }
    }
}

fn format_right_panel(
    state: &StatusLineState,
    colors: &ThemeColors,
    theme: Theme,
    max_width: usize,
) -> String {
    if max_width == 0 {
        return String::new();
    }

    let mode = state.hud_right_panel;
    if mode == HudRightPanel::Off {
        return String::new();
    }
    let recording_active = state.recording_state == RecordingState::Recording;
    let animate_panel = !state.hud_right_panel_recording_only || recording_active;

    let content_width = max_width.saturating_sub(1);
    if content_width < RIGHT_PANEL_MIN_CONTENT_WIDTH {
        return " ".repeat(max_width);
    }

    let show_live = animate_panel && !state.meter_levels.is_empty();
    let panel_width = content_width;

    let panel = match mode {
        HudRightPanel::Ribbon => {
            let reserved = 2; // brackets
            let available = panel_width.saturating_sub(reserved);
            let wave_width = available.min(RIGHT_PANEL_MAX_WAVEFORM_WIDTH);
            let waveform = if show_live {
                format_waveform(&state.meter_levels, wave_width, theme)
            } else {
                dim_waveform_placeholder(wave_width, colors)
            };
            format_panel_brackets(&waveform, colors)
        }
        HudRightPanel::Dots => {
            let active = if animate_panel {
                state.meter_db.unwrap_or(-60.0)
            } else {
                -60.0
            };
            truncate_display(&format_pulse_dots(active, colors), panel_width)
        }
        HudRightPanel::Heartbeat => {
            truncate_display(&format_heartbeat_panel(state, colors), panel_width)
        }
        HudRightPanel::Off => String::new(),
    };

    if panel.is_empty() {
        return String::new();
    }

    truncate_display(&panel, max_width)
}

#[inline]
fn format_pulse_dots(level_db: f32, colors: &ThemeColors) -> String {
    let normalized = ((level_db + 60.0) / 60.0).clamp(0.0, 1.0);
    let active = (normalized * 5.0).round() as usize;
    let color = meter_level_color(level_db, colors);
    // Pre-allocate for 5 dots with color codes
    let mut result = String::with_capacity(128);
    result.push_str(colors.dim);
    result.push('[');
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

#[inline]
fn should_animate_heartbeat(recording_only: bool, recording_active: bool) -> bool {
    !recording_only || recording_active
}

#[inline]
fn heartbeat_color(animate: bool, is_peak: bool, colors: &ThemeColors) -> &str {
    if animate && is_peak {
        colors.info
    } else {
        colors.dim
    }
}

fn format_heartbeat_panel(state: &StatusLineState, colors: &ThemeColors) -> String {
    let animate = should_animate_heartbeat(
        state.hud_right_panel_recording_only,
        state.recording_state == RecordingState::Recording,
    );
    let (glyph, is_peak) = heartbeat_glyph(animate);

    let mut content = String::with_capacity(16);
    let color = heartbeat_color(animate, is_peak, colors);
    content.push_str(color);
    content.push(glyph);
    content.push_str(colors.reset);

    format_panel_brackets(&content, colors)
}

/// Format the mode indicator with appropriate color and symbol.
/// Uses animated indicators for recording (pulsing) and processing (spinning).
#[inline]
fn format_mode_indicator(state: &StatusLineState, colors: &ThemeColors) -> String {
    let mut content = String::with_capacity(40);
    let mode_label = format!(
        "{:<width$}",
        full_mode_voice_label(state.voice_mode),
        width = MODE_LABEL_WIDTH
    );
    match state.recording_state {
        RecordingState::Recording => {
            content.push_str(&with_color(
                recording_mode_indicator(state.voice_mode, colors),
                recording_indicator_color(colors),
                colors,
            ));
            content.push(' ');
            content.push_str(&with_color(&mode_label, colors.recording, colors));
        }
        RecordingState::Processing => {
            content.push_str(&with_color(
                processing_mode_indicator(colors),
                colors.processing,
                colors,
            ));
            content.push(' ');
            content.push_str(&with_color(&mode_label, colors.processing, colors));
        }
        RecordingState::Responding => {
            content.push_str(&with_color(
                colors.indicator_responding,
                colors.info,
                colors,
            ));
            content.push(' ');
            content.push_str(&with_color(&mode_label, colors.info, colors));
        }
        RecordingState::Idle => {
            let (idle_indicator, idle_color) = idle_mode_indicator(state.voice_mode, colors);
            content.push_str(&with_color(idle_indicator, idle_color, colors));
            content.push(' ');
            content.push_str(&with_color(&mode_label, idle_color, colors));
        }
    }

    // Keep mode lane fixed; downstream duration spacing handles AUTO/PTT label delta.
    let lane_content_width = MAIN_ROW_MODE_LANE_WIDTH.saturating_sub(2);
    let clipped = truncate_display(&content, lane_content_width);
    let padding = " ".repeat(lane_content_width.saturating_sub(display_width(&clipped)));
    format!(" {}{} ", clipped, padding)
}

fn format_transition_suffix(state: &StatusLineState, colors: &ThemeColors) -> String {
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

/// Format the bottom border.
fn format_bottom_border(colors: &ThemeColors, borders: &BorderSet, width: usize) -> String {
    let inner: String = std::iter::repeat_n(borders.horizontal, width.saturating_sub(2)).collect();

    format!(
        "{}{}{}{}{}",
        colors.border, borders.bottom_left, inner, borders.bottom_right, colors.reset
    )
}

/// Format the enhanced status line with responsive layout.
#[must_use]
pub fn format_status_line(state: &StatusLineState, theme: Theme, width: usize) -> String {
    let colors = theme.colors();

    if width < breakpoints::MINIMAL {
        // Ultra-narrow: just the essential indicator and truncated message
        return format_minimal(state, &colors, width);
    }

    if width < breakpoints::COMPACT {
        // Compact: indicator + message only
        return format_compact(state, &colors, theme, width);
    }

    // Build sections based on available width
    let left = if width >= breakpoints::MEDIUM {
        format_left_section(state, &colors)
    } else {
        format_left_compact(state, &colors)
    };

    let right = format_right_shortcuts(&colors, width);

    let center = format_message(state, &colors, theme, width);

    // Calculate display widths (excluding ANSI codes)
    let left_width = display_width(&left);
    let right_width = display_width(&right);
    let center_width = display_width(&center);

    // Combine with proper spacing
    let total_content_width = left_width + center_width + right_width + 2;

    if total_content_width <= width {
        // Everything fits - add padding between center and right
        let padding = width.saturating_sub(total_content_width);
        if right.is_empty() {
            format!("{} {}", left, center)
        } else {
            format!(
                "{} {}{:padding$}{}",
                left,
                center,
                "",
                right,
                padding = padding
            )
        }
    } else if left_width + right_width + 4 <= width {
        // Truncate center message
        let available = width.saturating_sub(left_width + right_width + 3);
        let truncated_center = truncate_display(&center, available);
        if right.is_empty() {
            format!("{} {}", left, truncated_center)
        } else {
            format!("{} {} {}", left, truncated_center, right)
        }
    } else {
        // Very narrow - just show left + truncated message
        let available = width.saturating_sub(left_width + 1);
        let truncated_center = truncate_display(&center, available);
        format!("{} {}", left, truncated_center)
    }
}

#[inline]
fn format_right_shortcuts(colors: &ThemeColors, width: usize) -> String {
    if width >= breakpoints::FULL {
        format_shortcuts(colors)
    } else if width >= breakpoints::MEDIUM {
        format_shortcuts_compact(colors)
    } else {
        String::new()
    }
}

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
fn format_minimal(state: &StatusLineState, colors: &ThemeColors, width: usize) -> String {
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

    let available = width.saturating_sub(2); // indicator + space
    format!("{} {}", indicator, truncate_display(&msg, available))
}

/// Format compact status for narrow terminals.
fn format_compact(
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
        recording_duration_secs: state.recording_duration.unwrap_or(0.0),
        audio_level_db: state.meter_db.unwrap_or(-60.0),
        audio_levels: state.meter_levels.clone(),
        queue_depth: state.queue_depth,
        last_latency_ms: state.last_latency_ms,
        latency_history_ms: state.latency_history_ms.clone(),
        backend_name: String::new(),
        glyph_set: colors.glyph_set,
    };
    let modules = registry.render_all(&hud_state, module_budget, " · ");
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

fn compact_hud_registry(state: &StatusLineState, module_budget: usize) -> &'static HudRegistry {
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
fn format_left_compact(state: &StatusLineState, colors: &ThemeColors) -> String {
    let parts = compact_mode_parts(state, colors);
    let mode_indicator = format_compact_indicator(&parts, colors);
    let mode_label = parts.label;
    let transition = format_transition_suffix(state, colors);

    if mode_label.is_empty() {
        format!(
            "{}{} │ {:.0}dB",
            mode_indicator, transition, state.sensitivity_db
        )
    } else {
        format!(
            "{}{mode_label}{} │ {:.0}dB",
            mode_indicator, transition, state.sensitivity_db
        )
    }
}

/// Format compact shortcuts with modern separator.
fn format_shortcuts_compact(colors: &ThemeColors) -> String {
    // Compact style: dot separator
    let sep = format!(" {}·{} ", colors.dim, colors.reset);
    format_shortcuts_list(colors, SHORTCUTS_COMPACT, &sep)
}

fn format_left_section(state: &StatusLineState, colors: &ThemeColors) -> String {
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

    // Add recording duration if active
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

fn format_message(
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

fn format_shortcuts(colors: &ThemeColors) -> String {
    // Modern style: dimmed separator between shortcuts
    let sep = format!(" {}│{} ", colors.dim, colors.reset);
    format_shortcuts_list(colors, SHORTCUTS, &sep)
}

fn format_shortcuts_list(
    colors: &ThemeColors,
    shortcuts: &[(&str, &str)],
    separator: &str,
) -> String {
    let mut parts = Vec::with_capacity(shortcuts.len());
    for (key, action) in shortcuts {
        // Modern style: dim key, normal label
        parts.push(format!("{}{}{} {}", colors.dim, key, colors.reset, action));
    }
    parts.join(separator)
}
#[cfg(test)]
mod tests;
