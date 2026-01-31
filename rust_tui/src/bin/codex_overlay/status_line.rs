//! Enhanced status line layout with sections.
//!
//! Provides a structured status line with mode indicator, pipeline info,
//! sensitivity level, status message, and keyboard shortcuts.

use crate::audio_meter::format_waveform;
use crate::status_style::StatusType;
use crate::theme::{Theme, ThemeColors};

/// Current voice mode.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum VoiceMode {
    /// Auto-voice mode (hands-free)
    Auto,
    /// Manual voice mode (push-to-talk)
    Manual,
    /// Voice disabled/idle
    #[default]
    Idle,
}

impl VoiceMode {
    pub fn label(&self) -> &'static str {
        match self {
            Self::Auto => "AUTO",
            Self::Manual => "MANUAL",
            Self::Idle => "IDLE",
        }
    }

    pub fn indicator(&self) -> &'static str {
        match self {
            Self::Auto => "◉",
            Self::Manual => "●",
            Self::Idle => "○",
        }
    }
}

/// Current recording state.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum RecordingState {
    /// Not recording
    #[default]
    Idle,
    /// Recording in progress
    Recording,
    /// Processing recorded audio
    Processing,
}

/// Pipeline being used for voice capture.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum Pipeline {
    /// Native Rust pipeline
    #[default]
    Rust,
    /// Python fallback pipeline
    Python,
}

impl Pipeline {
    pub fn label(&self) -> &'static str {
        match self {
            Self::Rust => "Rust",
            Self::Python => "Python",
        }
    }
}

/// State for the enhanced status line.
#[derive(Debug, Clone, Default)]
pub struct StatusLineState {
    /// Current voice mode (auto/manual/idle)
    pub voice_mode: VoiceMode,
    /// Current recording state
    pub recording_state: RecordingState,
    /// Pipeline in use
    pub pipeline: Pipeline,
    /// Microphone sensitivity in dB
    pub sensitivity_db: f32,
    /// Main status message
    pub message: String,
    /// Recording duration in seconds (if recording)
    pub recording_duration: Option<f32>,
    /// Whether auto-voice is enabled
    pub auto_voice_enabled: bool,
    /// Recent audio meter samples in dBFS for waveform display
    pub meter_levels: Vec<f32>,
    /// Latest audio meter level in dBFS
    pub meter_db: Option<f32>,
    /// Optional transcript preview snippet
    pub transcript_preview: Option<String>,
}

impl StatusLineState {
    pub fn new() -> Self {
        Self {
            sensitivity_db: -35.0,
            ..Default::default()
        }
    }
}

/// Keyboard shortcuts to display.
const SHORTCUTS: &[(&str, &str)] = &[
    ("Ctrl+R", "rec"),
    ("Ctrl+V", "auto"),
    ("Ctrl+T", "send"),
    ("?", "help"),
    ("Ctrl+Y", "theme"),
];

/// Compact shortcuts for narrow terminals.
const SHORTCUTS_COMPACT: &[(&str, &str)] = &[
    ("^R", "rec"),
    ("^V", "auto"),
    ("^T", "send"),
    ("?", "help"),
    ("^Y", "theme"),
];

/// Terminal width breakpoints for responsive layout.
mod breakpoints {
    /// Full layout with all sections
    pub const FULL: usize = 80;
    /// Medium layout - shorter shortcuts
    pub const MEDIUM: usize = 60;
    /// Compact layout - minimal left section
    pub const COMPACT: usize = 40;
    /// Minimal layout - message only
    pub const MINIMAL: usize = 25;
}

/// Format the enhanced status line with responsive layout.
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

    let right = if width >= breakpoints::FULL {
        format_shortcuts(&colors)
    } else if width >= breakpoints::MEDIUM {
        format_shortcuts_compact(&colors)
    } else {
        String::new()
    };

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

/// Format minimal status for very narrow terminals.
fn format_minimal(state: &StatusLineState, colors: &ThemeColors, width: usize) -> String {
    let indicator = match state.recording_state {
        RecordingState::Recording => format!("{}●{}", colors.recording, colors.reset),
        RecordingState::Processing => format!("{}◐{}", colors.processing, colors.reset),
        RecordingState::Idle => {
            if state.voice_mode == VoiceMode::Auto {
                format!(
                    "{}{}{}",
                    colors.info,
                    state.voice_mode.indicator(),
                    colors.reset
                )
            } else {
                state.voice_mode.indicator().to_string()
            }
        }
    };

    let msg = if state.message.is_empty() {
        if state.voice_mode == VoiceMode::Auto {
            "auto"
        } else {
            "ready"
        }
        .to_string()
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
    let mode = match state.recording_state {
        RecordingState::Recording => format!("{}● R{}", colors.recording, colors.reset),
        RecordingState::Processing => format!("{}◐ ..{}", colors.processing, colors.reset),
        RecordingState::Idle => {
            let label = match state.voice_mode {
                VoiceMode::Auto => "A",
                VoiceMode::Manual => "M",
                VoiceMode::Idle => "",
            };
            if state.voice_mode == VoiceMode::Auto {
                format!(
                    "{}{} {}{}",
                    colors.info,
                    state.voice_mode.indicator(),
                    label,
                    colors.reset
                )
            } else if state.voice_mode == VoiceMode::Manual {
                format!("{} {}", state.voice_mode.indicator(), label)
            } else {
                state.voice_mode.indicator().to_string()
            }
        }
    };

    let msg = format_message(state, colors, theme, width);
    let mode_width = display_width(&mode);
    let available = width.saturating_sub(mode_width + 1);
    format!("{} {}", mode, truncate_display(&msg, available))
}

/// Format compact left section for medium terminals.
fn format_left_compact(state: &StatusLineState, colors: &ThemeColors) -> String {
    let mode_indicator = match state.recording_state {
        RecordingState::Recording => format!("{}●{}", colors.recording, colors.reset),
        RecordingState::Processing => format!("{}◐{}", colors.processing, colors.reset),
        RecordingState::Idle => {
            if state.voice_mode == VoiceMode::Auto {
                format!(
                    "{}{}{}",
                    colors.info,
                    state.voice_mode.indicator(),
                    colors.reset
                )
            } else {
                state.voice_mode.indicator().to_string()
            }
        }
    };

    let mode_label = match state.recording_state {
        RecordingState::Recording => "R",
        RecordingState::Processing => "..",
        RecordingState::Idle => match state.voice_mode {
            VoiceMode::Auto => "A",
            VoiceMode::Manual => "M",
            VoiceMode::Idle => "",
        },
    };

    if mode_label.is_empty() {
        format!("{} │ {:.0}dB", mode_indicator, state.sensitivity_db)
    } else {
        format!(
            "{}{} │ {:.0}dB",
            mode_indicator, mode_label, state.sensitivity_db
        )
    }
}

/// Format compact shortcuts.
fn format_shortcuts_compact(colors: &ThemeColors) -> String {
    let mut parts = Vec::new();
    for (key, action) in SHORTCUTS_COMPACT {
        parts.push(format!("{}{}{} {}", colors.info, key, colors.reset, action));
    }
    parts.join(" ")
}

fn format_left_section(state: &StatusLineState, colors: &ThemeColors) -> String {
    let mode_color = match state.recording_state {
        RecordingState::Recording => colors.recording,
        RecordingState::Processing => colors.processing,
        RecordingState::Idle => {
            if state.voice_mode == VoiceMode::Auto {
                colors.info
            } else {
                ""
            }
        }
    };

    let mode_indicator = match state.recording_state {
        RecordingState::Recording => "●",
        RecordingState::Processing => "◐",
        RecordingState::Idle => state.voice_mode.indicator(),
    };

    let mode_label = match state.recording_state {
        RecordingState::Recording => "REC",
        RecordingState::Processing => "...",
        RecordingState::Idle => state.voice_mode.label(),
    };

    let pipeline = state.pipeline.label();
    let sensitivity = format!("{:.0}dB", state.sensitivity_db);

    // Add recording duration if active
    let duration_part = if let Some(dur) = state.recording_duration {
        format!(" {:.1}s", dur)
    } else {
        String::new()
    };

    if mode_color.is_empty() {
        format!(
            "{} {} │ {} │ {}{}",
            mode_indicator, mode_label, pipeline, sensitivity, duration_part
        )
    } else {
        format!(
            "{}{} {}{} │ {} │ {}{}",
            mode_color,
            mode_indicator,
            mode_label,
            colors.reset,
            pipeline,
            sensitivity,
            duration_part
        )
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
    let mut parts = Vec::new();
    for (key, action) in SHORTCUTS {
        parts.push(format!("{}{}{} {}", colors.info, key, colors.reset, action));
    }
    parts.join("  ")
}

/// Calculate display width excluding ANSI escape codes.
fn display_width(s: &str) -> usize {
    let mut width = 0;
    let mut in_escape = false;

    for ch in s.chars() {
        if ch == '\x1b' {
            in_escape = true;
        } else if in_escape {
            if ch == 'm' {
                in_escape = false;
            }
        } else {
            // Most unicode chars are width 1, but some CJK are width 2
            // For simplicity, treat all as width 1
            width += 1;
        }
    }

    width
}

/// Truncate a string to a maximum display width.
fn truncate_display(s: &str, max_width: usize) -> String {
    if max_width == 0 {
        return String::new();
    }

    let mut result = String::new();
    let mut width = 0;
    let mut in_escape = false;
    let mut escape_seq = String::new();

    for ch in s.chars() {
        if ch == '\x1b' {
            in_escape = true;
            escape_seq.push(ch);
        } else if in_escape {
            escape_seq.push(ch);
            if ch == 'm' {
                result.push_str(&escape_seq);
                escape_seq.clear();
                in_escape = false;
            }
        } else {
            if width >= max_width {
                break;
            }
            result.push(ch);
            width += 1;
        }
    }

    // Ensure we close any open escape sequences
    if !result.is_empty() && result.contains("\x1b[") && !result.ends_with("\x1b[0m") {
        result.push_str("\x1b[0m");
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn voice_mode_labels() {
        assert_eq!(VoiceMode::Auto.label(), "AUTO");
        assert_eq!(VoiceMode::Manual.label(), "MANUAL");
        assert_eq!(VoiceMode::Idle.label(), "IDLE");
    }

    #[test]
    fn pipeline_labels() {
        assert_eq!(Pipeline::Rust.label(), "Rust");
        assert_eq!(Pipeline::Python.label(), "Python");
    }

    #[test]
    fn display_width_excludes_ansi() {
        assert_eq!(display_width("hello"), 5);
        assert_eq!(display_width("\x1b[91mhello\x1b[0m"), 5);
        assert_eq!(display_width("\x1b[38;2;255;0;0mred\x1b[0m"), 3);
    }

    #[test]
    fn truncate_display_respects_width() {
        assert_eq!(truncate_display("hello", 3), "hel");
        assert_eq!(truncate_display("hello", 10), "hello");
        assert_eq!(truncate_display("hello", 0), "");
    }

    #[test]
    fn truncate_display_preserves_ansi() {
        let colored = "\x1b[91mhello\x1b[0m";
        let truncated = truncate_display(colored, 3);
        assert!(truncated.contains("\x1b[91m"));
        assert!(truncated.contains("hel"));
    }

    #[test]
    fn format_status_line_basic() {
        let state = StatusLineState {
            auto_voice_enabled: true,
            voice_mode: VoiceMode::Auto,
            pipeline: Pipeline::Rust,
            sensitivity_db: -35.0,
            message: "Ready".to_string(),
            ..Default::default()
        };
        let line = format_status_line(&state, Theme::Coral, 80);
        assert!(line.contains("AUTO"));
        assert!(line.contains("Rust"));
        assert!(line.contains("-35dB"));
        assert!(line.contains("Ready"));
    }

    #[test]
    fn format_status_line_with_duration() {
        let state = StatusLineState {
            recording_state: RecordingState::Recording,
            recording_duration: Some(2.5),
            message: "Recording...".to_string(),
            ..Default::default()
        };
        let line = format_status_line(&state, Theme::Coral, 80);
        assert!(line.contains("2.5s"));
        assert!(line.contains("REC"));
    }

    #[test]
    fn status_line_state_default() {
        let state = StatusLineState::new();
        assert_eq!(state.sensitivity_db, -35.0);
        assert!(!state.auto_voice_enabled);
        assert!(state.message.is_empty());
    }

    #[test]
    fn format_status_line_narrow_terminal() {
        let state = StatusLineState {
            auto_voice_enabled: true,
            voice_mode: VoiceMode::Auto,
            message: "Ready".to_string(),
            ..Default::default()
        };
        // Narrow terminal should still produce output
        let line = format_status_line(&state, Theme::Coral, 40);
        assert!(!line.is_empty());
        // Should have some content
        assert!(line.len() > 5);
    }

    #[test]
    fn format_status_line_very_narrow() {
        let state = StatusLineState {
            auto_voice_enabled: true,
            voice_mode: VoiceMode::Auto,
            message: "Ready".to_string(),
            ..Default::default()
        };
        // Very narrow terminal
        let line = format_status_line(&state, Theme::Coral, 20);
        assert!(!line.is_empty());
    }

    #[test]
    fn format_status_line_minimal() {
        let state = StatusLineState {
            auto_voice_enabled: true,
            voice_mode: VoiceMode::Auto,
            message: "Ready".to_string(),
            ..Default::default()
        };
        // Minimal width
        let line = format_status_line(&state, Theme::None, 15);
        assert!(!line.is_empty());
        // Should contain indicator
        assert!(line.contains("◉") || line.contains("auto") || line.contains("Ready"));
    }

    #[test]
    fn format_status_line_medium_shows_compact_shortcuts() {
        let state = StatusLineState {
            auto_voice_enabled: true,
            voice_mode: VoiceMode::Auto,
            message: "Ready".to_string(),
            ..Default::default()
        };
        // Medium terminal - should show compact shortcuts
        let line = format_status_line(&state, Theme::None, 65);
        // Should have some shortcut hint
        assert!(line.contains("R") || line.contains("V") || line.contains("rec"));
    }
}
