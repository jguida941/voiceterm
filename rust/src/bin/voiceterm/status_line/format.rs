//! Status-line formatter so full/minimal HUD modes share consistent semantics.

use crate::config::{HudBorderStyle, HudStyle};
use crate::status_style::StatusType;
use crate::theme::{
    inline_separator, overlay_separator, resolved_hud_border_set, BorderSet, Theme, ThemeColors,
    BORDER_DOUBLE, BORDER_HEAVY, BORDER_NONE, BORDER_ROUNDED, BORDER_SINGLE,
};

use super::animation::transition_marker;
use super::buttons::{
    format_full_controls_with_positions, format_hidden_launcher_with_buttons,
    format_minimal_strip_with_button, format_shortcuts_row_with_positions, hidden_muted_color,
};
use super::layout::{breakpoints, effective_hud_style_for_state};
use super::mode_indicator::{
    full_mode_voice_label, idle_mode_indicator, processing_mode_indicator,
    recording_indicator_color, recording_mode_indicator,
};
use super::right_panel::format_right_panel;
#[cfg(test)]
use super::right_panel::{
    format_heartbeat_panel, format_pulse_dots, heartbeat_color, meter_level_color,
    scene_should_animate,
};
#[cfg(test)]
use super::state::Pipeline;
use super::state::{RecordingState, StatusBanner, StatusLineState, VoiceMode};
use super::text::{display_width, truncate_display, with_color};
#[cfg(test)]
use crate::config::HudRightPanel;
#[cfg(test)]
use crate::theme::VoiceSceneStyle;
#[cfg(test)]
use compact::compact_hud_registry;
use compact::{format_compact, format_left_compact, format_minimal, format_shortcuts_compact};
use single_line::{format_left_section, format_message, format_right_shortcuts};
#[cfg(test)]
use single_line::{format_shortcuts, format_transition_suffix};

mod compact;
mod single_line;

const MAIN_ROW_DURATION_PLACEHOLDER: &str = "--.-s";
const MAIN_ROW_DURATION_TEXT_WIDTH: usize = MAIN_ROW_DURATION_PLACEHOLDER.len();
const MAIN_ROW_DURATION_TEXT_WIDTH_AUTO: usize = MAIN_ROW_DURATION_TEXT_WIDTH + 1;
const MAIN_ROW_RIGHT_GUTTER: usize = 1;
const MAIN_ROW_METER_TEXT_WIDTH: usize = 5;
// Keep main-row separators anchored to stable columns so they do not jitter
// across recording/processing state transitions.
const MAIN_ROW_MODE_LANE_WIDTH: usize = 9;
const MODE_LABEL_WIDTH: usize = 8;
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
    ("Ctrl+Y", "studio"),
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
    ("^Y", "std"),
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

#[inline]
fn colored_inline_separator(colors: &ThemeColors) -> String {
    format!(
        "{}{}{}",
        colors.dim,
        inline_separator(colors.glyph_set),
        colors.reset
    )
}

#[inline]
fn colored_overlay_separator(colors: &ThemeColors) -> String {
    format!(
        " {}{}{} ",
        colors.dim,
        overlay_separator(colors.glyph_set),
        colors.reset
    )
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
    if state.prompt_suppressed {
        return StatusBanner::new(Vec::new());
    }

    let mut colors = theme.colors();
    colors.borders = resolved_hud_border_set(theme);
    let effective_hud_style = effective_hud_style_for_state(state);
    let borders = resolve_hud_border_set(state, &colors.borders);
    let borderless =
        effective_hud_style == HudStyle::Full && state.hud_border_style == HudBorderStyle::None;

    // Handle HUD style
    match effective_hud_style {
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
            if state.full_hud_single_line {
                return format_full_single_line_banner(state, &colors, theme, width);
            }
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

fn format_full_single_line_banner(
    state: &StatusLineState,
    colors: &ThemeColors,
    theme: Theme,
    width: usize,
) -> StatusBanner {
    if width == 0 {
        return StatusBanner::new(vec![String::new()]);
    }

    let mode_section = format_mode_indicator(state, colors);
    let duration_section = format_duration_section(state, colors);
    let meter_section = format_meter_section(state, colors);
    let message_section = format_full_hud_message(state, colors);
    let sep = colored_inline_separator(colors);
    let mut status = [mode_section, duration_section, meter_section].join(&sep);
    if !message_section.is_empty() {
        status.push_str(&format!(" {sep} {message_section}"));
    }

    let (controls_row, base_buttons) =
        format_full_controls_with_positions(state, colors, width, 1, 1);
    let controls_width = display_width(&controls_row);
    let status_controls_sep = colored_overlay_separator(colors);
    let status_controls_sep_width = display_width(&status_controls_sep);

    let right_panel = format_right_panel(state, colors, theme, width.saturating_sub(12));
    let panel_width = display_width(&right_panel);
    let include_panel = !right_panel.is_empty() && width > controls_width + panel_width + 1;
    let panel_reserve = if include_panel { panel_width + 1 } else { 0 };

    let include_status_controls_sep = !status.is_empty() && !controls_row.is_empty();
    let status_budget = width.saturating_sub(
        controls_width
            + panel_reserve
            + if include_status_controls_sep {
                status_controls_sep_width
            } else {
                0
            },
    );
    let status_prefix = truncate_display(&status, status_budget);

    let (mut line, controls_start_col) = if controls_row.is_empty() {
        (status_prefix, None)
    } else if status_prefix.is_empty() {
        (controls_row, Some(1usize))
    } else {
        (
            format!("{status_prefix}{status_controls_sep}{controls_row}"),
            Some(display_width(&status_prefix) + status_controls_sep_width + 1),
        )
    };

    if include_panel {
        let core_width = display_width(&line);
        if core_width + panel_width <= width {
            let gap = width.saturating_sub(core_width + panel_width);
            line.push_str(&" ".repeat(gap));
            line.push_str(&right_panel);
        } else {
            line = truncate_display(&line, width);
        }
    } else {
        line = truncate_display(&line, width);
    }

    let mut buttons = if let Some(start_col) = controls_start_col {
        let offset = start_col.saturating_sub(1) as u16;
        base_buttons
            .into_iter()
            .map(|mut button| {
                button.start_x = button.start_x.saturating_add(offset);
                button.end_x = button.end_x.saturating_add(offset);
                button
            })
            .collect::<Vec<_>>()
    } else {
        Vec::new()
    };
    let line_width = display_width(&line);
    buttons.retain(|button| button.end_x as usize <= line_width);

    StatusBanner::with_buttons(vec![line], buttons)
}

/// Format the top border with VoiceTerm badge.
fn format_top_border(colors: &ThemeColors, borders: &BorderSet, width: usize) -> String {
    let brand_label = format_brand_label(colors);
    let label_width = display_width(&brand_label);

    // Calculate border segments
    // Total: top_left(1) + left_segment + label + right_segment + top_right(1) = width
    let left_border_len = 2;
    let right_border_len = width.saturating_sub(left_border_len + label_width + 2); // +2 for corners

    let left_segment = horizontal_segment(borders.horizontal, left_border_len);
    let right_segment = horizontal_segment(borders.horizontal, right_border_len);

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

#[inline]
fn horizontal_segment(horizontal: char, len: usize) -> String {
    std::iter::repeat_n(horizontal, len).collect()
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
    let sep = colored_inline_separator(colors);
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

/// Format the bottom border.
fn format_bottom_border(colors: &ThemeColors, borders: &BorderSet, width: usize) -> String {
    let inner = horizontal_segment(borders.horizontal, width.saturating_sub(2));

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

#[cfg(test)]
mod tests;
