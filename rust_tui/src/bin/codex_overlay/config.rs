use clap::{Parser, ValueEnum};
use rust_tui::config::AppConfig;
use std::path::PathBuf;

use crate::color_mode::ColorMode;
use crate::theme::Theme;

#[derive(Debug, Clone, Copy, PartialEq, Eq, ValueEnum)]
pub(crate) enum VoiceSendMode {
    Auto,
    Insert,
}

#[derive(Debug, Parser, Clone)]
#[command(about = "Codex Voice", author, version)]
pub(crate) struct OverlayConfig {
    #[command(flatten)]
    pub(crate) app: AppConfig,

    /// Regex used to detect the Codex prompt line (overrides auto-detection)
    #[arg(long = "prompt-regex")]
    pub(crate) prompt_regex: Option<String>,

    /// Log file path for prompt detection diagnostics
    #[arg(long = "prompt-log")]
    pub(crate) prompt_log: Option<PathBuf>,

    /// Start in auto-voice mode
    #[arg(long = "auto-voice", default_value_t = false)]
    pub(crate) auto_voice: bool,

    /// Idle time before auto-voice triggers when prompt detection is unknown (ms)
    #[arg(long = "auto-voice-idle-ms", default_value_t = 1200)]
    pub(crate) auto_voice_idle_ms: u64,

    /// Idle time before transcripts auto-send when a prompt has not been detected (ms)
    #[arg(long = "transcript-idle-ms", default_value_t = 250)]
    pub(crate) transcript_idle_ms: u64,

    /// Voice transcript handling (auto = send newline, insert = leave for editing)
    #[arg(long = "voice-send-mode", value_enum, default_value_t = VoiceSendMode::Auto)]
    pub(crate) voice_send_mode: VoiceSendMode,

    /// Color theme for status line (coral, catppuccin, dracula, nord, ansi, none)
    #[arg(long = "theme", default_value = "coral")]
    pub(crate) theme_name: Option<String>,

    /// Disable colors in status line output
    #[arg(long = "no-color", default_value_t = false)]
    pub(crate) no_color: bool,
}

impl OverlayConfig {
    /// Get the resolved theme, respecting --no-color and NO_COLOR env var.
    pub(crate) fn theme(&self) -> Theme {
        if self.no_color || std::env::var("NO_COLOR").is_ok() {
            return Theme::None;
        }
        let requested = self
            .theme_name
            .as_deref()
            .and_then(Theme::from_name)
            .unwrap_or_default();
        let mode = self.color_mode();
        if !mode.supports_color() {
            Theme::None
        } else if !mode.supports_truecolor() {
            requested.fallback_for_ansi()
        } else {
            requested
        }
    }

    /// Get the detected color mode for the terminal.
    pub(crate) fn color_mode(&self) -> ColorMode {
        if self.no_color {
            ColorMode::None
        } else {
            ColorMode::detect()
        }
    }
}
